import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

from models import db
from models.hospital import Hospital
from models.medical_record import MedicalRecord
from models.request import AccessRequest
from services.encryption import encrypt_data


# =====================================================
# Hospital Helper Functions
# =====================================================

def get_hospital_by_user(user_id):
    """
    Fetch hospital linked to a logged-in hospital user
    """
    return Hospital.query.filter_by(user_id=user_id).first()


# =====================================================
# Upload Medical Record (DYNAMIC & SAFE)
# =====================================================

def upload_medical_record(hospital_id, patient_id, title, file):
    """
    Dynamically creates upload folders if they do not exist,
    encrypts the file, and stores metadata in DB.
    """

    # 1️⃣ Get base upload path from config
    base_path = current_app.config.get("UPLOAD_FOLDER")
    if not base_path:
        raise RuntimeError("UPLOAD_FOLDER is not configured")

    # 2️⃣ Ensure base upload directory exists
    os.makedirs(base_path, exist_ok=True)

    # 3️⃣ Create hospital and patient folders dynamically
    hospital_folder = os.path.join(base_path, f"hospital_{hospital_id}")
    patient_folder = os.path.join(hospital_folder, f"patient_{patient_id}")
    os.makedirs(patient_folder, exist_ok=True)

    # 4️⃣ Secure filename
    filename = secure_filename(file.filename)
    if not filename:
        raise ValueError("Invalid file name")

    file_path = os.path.join(patient_folder, filename)

    # 5️⃣ Encrypt file content
    encrypted_data = encrypt_data(file.read())

    # 6️⃣ Write encrypted data to file
    with open(file_path, "wb") as f:
        f.write(encrypted_data)

    # 7️⃣ Save record metadata
    record = MedicalRecord(
        patient_id=patient_id,
        hospital_id=hospital_id,
        title=title,
        record_label=title,  # auto-filled
        file_path=file_path,
        uploaded_at=datetime.utcnow()
    )

    db.session.add(record)
    db.session.commit()

    return record


# =====================================================
# Fetch Hospital Records
# =====================================================

def get_records_for_hospital(hospital_id):
    """
    Get all medical records uploaded by a hospital
    """
    return MedicalRecord.query.filter_by(hospital_id=hospital_id).all()


# =====================================================
# Fetch Access Requests for Hospital
# =====================================================

def get_requests_for_hospital(hospital_id):
    """
    Get all access requests for a hospital
    """
    return AccessRequest.query.filter_by(hospital_id=hospital_id).all()


# =====================================================
# Approve Access Request (CORRECT LOGIC)
# =====================================================

def approve_access_request(request_id, hospital_id):
    """
    Hospital approves a medical record access request.
    Patient verification must already be completed.
    """

    req = AccessRequest.query.filter_by(
        id=request_id,
        hospital_id=hospital_id
    ).first()

    if not req:
        return False, "Access request not found"

    # Ensure patient already verified ownership
    if not req.verified_by_patient:
        return False, "Patient verification incomplete"

    # Prevent duplicate processing
    if req.status != "PENDING":
        return False, "Request already processed"

    req.status = "APPROVED"
    req.verified_by_hospital = True
    req.verified_at = datetime.utcnow()

    db.session.commit()

    return True, "Access request approved successfully"


# =====================================================
# Reject Access Request
# =====================================================

def reject_access_request(request_id, hospital_id):
    """
    Hospital rejects a medical record access request
    """

    req = AccessRequest.query.filter_by(
        id=request_id,
        hospital_id=hospital_id
    ).first()

    if not req:
        return False, "Access request not found"

    if req.status != "PENDING":
        return False, "Request already processed"

    req.status = "REJECTED"
    req.verified_by_hospital = False
    req.verified_at = datetime.utcnow()

    db.session.commit()

    return True, "Access request rejected"

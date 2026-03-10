from models import db
from models.patient import Patient
from models.medical_record import MedicalRecord
from models.request import AccessRequest

from services.encryption import decrypt_data

def get_patient_by_user(user_id):
    """
    Fetch patient linked to logged-in user
    """
    return Patient.query.filter_by(user_id=user_id).first()

def get_records_for_patient(patient_id):
    """
    Fetch all medical records belonging to patient
    (metadata only, encrypted files remain protected)
    """
    return MedicalRecord.query.filter_by(
        patient_id=patient_id
    ).order_by(MedicalRecord.uploaded_at.desc()).all()

def get_requests_for_patient(patient_id):
    """
    Fetch all access requests made by patient
    """
    return AccessRequest.query.filter_by(
        patient_id=patient_id
    ).order_by(AccessRequest.requested_at.desc()).all()

def create_access_request(patient_id, record_id):
    """
    Create a new access request if not already requested
    """

    existing = AccessRequest.query.filter_by(
        patient_id=patient_id,
        record_id=record_id
    ).first()

    if existing:
        return False, "Access request already exists"

    record = MedicalRecord.query.get(record_id)
    if not record:
        return False, "Medical record not found"

    req = AccessRequest(
        patient_id=patient_id,
        record_id=record_id,
        hospital_id=record.hospital_id,
        status="PENDING"
    )

    db.session.add(req)
    db.session.commit()

    return True, "Access request submitted"

def is_request_approved(patient_id, record_id):
    """
    Check if access request is approved
    """

    return AccessRequest.query.filter_by(
        patient_id=patient_id,
        record_id=record_id,
        status="APPROVED"
    ).first()


def decrypt_medical_record(record):
    """
    Decrypt and return medical record file bytes
    (called ONLY after approval)
    """

    with open(record.file_path, "rb") as f:
        encrypted_data = f.read()

    return decrypt_data(encrypted_data)


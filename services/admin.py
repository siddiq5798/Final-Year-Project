import hashlib
from datetime import datetime

from models import db
from models.user import User
from models.hospital import Hospital
from models.patient import Patient

from services.code_generator import generate_code, hash_code


# ==============================
# Admin: Create Hospital
# ==============================
def create_hospital(
    name: str,
    email: str,
    password: str,
    hospital_identity_name: str
):
    """
    Creates a hospital with:
    - unique identity name
    - verification code (hashed)
    - linked user account
    """

    # 1. Create user account
    user = User(
        email=email,
        password=hashlib.sha256(password.encode()).hexdigest(),
        role="hospital"
    )
    db.session.add(user)
    db.session.commit()

    # 2. Generate hospital verification code
    hospital_code = generate_code()
    hospital_code_hash = hash_code(hospital_code)

    # 3. Create hospital record
    hospital = Hospital(
        name=name,
        hospital_identity_name=hospital_identity_name,
        hospital_code_hash=hospital_code_hash,
        code_created_at=datetime.utcnow(),
        user_id=user.id
    )

    db.session.add(hospital)
    db.session.commit()

    # 4. Return hospital + plain code (for email sending later)
    return hospital, hospital_code


# ==============================
# Admin: Create Patient
# ==============================
def create_patient(
    name: str,
    email: str,
    password: str
):
    """
    Creates a patient with:
    - verification code (hashed)
    - linked user account
    """

    # 1. Create user account
    user = User(
        email=email,
        password=hashlib.sha256(password.encode()).hexdigest(),
        role="patient"
    )
    db.session.add(user)
    db.session.commit()

    # 2. Generate patient verification code
    patient_code = generate_code()
    patient_code_hash = hash_code(patient_code)

    # 3. Create patient record
    patient = Patient(
        name=name,
        patient_code_hash=patient_code_hash,
        code_created_at=datetime.utcnow(),
        user_id=user.id
    )

    db.session.add(patient)
    db.session.commit()

    # 4. Return patient + plain code (for email sending later)
    return patient, patient_code


# ==============================
# Admin: Delete User (Optional CRUD)
# ==============================
def delete_user(user_id: int):
    """
    Deletes a user and cascades logically.
    """
    user = User.query.get(user_id)
    if not user:
        return False

    db.session.delete(user)
    db.session.commit()
    return True

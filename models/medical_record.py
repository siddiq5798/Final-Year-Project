from models import db
from datetime import datetime

class MedicalRecord(db.Model):
    __tablename__ = "medical_records"

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    hospital_id = db.Column(
        db.Integer,
        db.ForeignKey("hospitals.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    # NEW: Helps patients identify records easily
    record_label = db.Column(
        db.String(100),
        nullable=False
    )

    # Encrypted file path
    file_path = db.Column(
        db.String(300),
        nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

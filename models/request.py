from datetime import datetime
from models import db


class AccessRequest(db.Model):
    __tablename__ = "access_requests"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign keys
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    record_id = db.Column(db.Integer, db.ForeignKey("medical_records.id"), nullable=False)

    # Request status
    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    # Verification flags
    verified_by_patient = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    verified_by_hospital = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    # Timestamps
    requested_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    verified_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # -------------------------------
    # Relationships (optional but clean)
    # -------------------------------
    patient = db.relationship("Patient", backref="access_requests")
    hospital = db.relationship("Hospital", backref="access_requests")
    record = db.relationship("MedicalRecord", backref="access_requests")

    def __repr__(self):
        return f"<AccessRequest patient={self.patient_id} record={self.record_id} status={self.status}>"

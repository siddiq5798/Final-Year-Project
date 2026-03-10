from models import db
from datetime import datetime

class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    # Unique hospital identifier shown to patients
    hospital_identity_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    # Hashed 6-character hospital verification code
    hospital_code_hash = db.Column(
        db.String(256),
        nullable=False
    )

    code_created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

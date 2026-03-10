from models import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # SHA-256 hash
    role = db.Column(db.String(20), nullable=False)
    # roles: admin, hospital, patient

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Force model registration for Alembic
from models.user import User
from models.hospital import Hospital
from models.patient import Patient
from models.medical_record import MedicalRecord
from models.request import AccessRequest

import os

class Config:
    # ===============================
    # Flask Core Configuration
    # ===============================
    SECRET_KEY = "secure-medical-records-secret-key"
    DEBUG = True

    # ===============================
    # PostgreSQL Database Configuration
    # ===============================
    DB_HOST = "localhost"
    DB_NAME = "secure_medical_records"
    DB_USER = "postgres"
    DB_PASSWORD = "1976"
    DB_PORT = "5432"

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===============================
    # File Upload Configuration
    # ===============================
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR, "..", "static", "uploads", "hospitals"
    )

    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # ===============================
    # AES Encryption Configuration
    # ===============================
    # 32 bytes key for AES-256
    AES_SECRET_KEY = b"0123456789abcdef0123456789abcdef"



    # ===============================
    # EmailJS Configuration
    # ===============================
    EMAILJS_SERVICE_ID = "service_khorpfp"   # Hospital template service
    EMAILJS_HOSPITAL_TEMPLATE_ID = "template_n2z1olj"  # Hospital template ID
    EMAILJS_PATIENT_TEMPLATE_ID = "template_lofsja4"
    EMAILJS_PUBLIC_KEY = "XXLBq8d6zZgv4zMei"  # Public key for EmailJS

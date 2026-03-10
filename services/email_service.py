"""
email_service.py

NOTE:
EmailJS is a browser-only service.
Backend (Flask / Python) API calls are BLOCKED by EmailJS (403).

For academic / development mode:
- We safely SKIP email sending
- We LOG the email content instead
- Application NEVER crashes

This file can later be replaced with SMTP / SendGrid.
"""

from flask import current_app
import logging

# =====================================================
# Logger Setup
# =====================================================
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# =====================================================
# Internal Helper (SAFE NO-OP)
# =====================================================
def _send_emailjs_request(payload: dict):
    """
    EmailJS backend calls are NOT allowed.
    This function safely skips sending email
    and logs the intent instead.
    """

    logger.warning("EmailJS skipped (backend execution not allowed)")
    logger.info("Email payload (logged for demo): %s", payload)
    return True


# =====================================================
# Hospital Registration Email
# =====================================================
def send_hospital_created_email(
    to_email: str,
    hospital_name: str,
    hospital_identity: str,
    hospital_code: str
):
    """
    Hospital registration email (SAFE MODE)

    In production:
    - Replace this with SMTP / SendGrid
    """

    payload = {
        "to_email": to_email,
        "hospital_name": hospital_name,
        "hospital_identity": hospital_identity,
        "hospital_code": hospital_code,
    }

    _send_emailjs_request(payload)


# =====================================================
# Patient Registration Email
# =====================================================
def send_patient_created_email(
    to_email: str,
    patient_name: str,
    patient_code: str
):
    """
    Patient registration email (SAFE MODE)
    """

    payload = {
        "to_email": to_email,
        "patient_name": patient_name,
        "patient_code": patient_code,
    }

    _send_emailjs_request(payload)

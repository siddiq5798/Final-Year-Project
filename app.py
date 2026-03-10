from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, send_file
)
from flask_migrate import Migrate
from functools import wraps
import hashlib
from datetime import datetime
import os
from werkzeug.security import generate_password_hash
import os
from mimetypes import guess_type


from models import db
from models.user import User
from models.hospital import Hospital
from models.patient import Patient
from models.medical_record import MedicalRecord
from models.request import AccessRequest

from services.admin import create_hospital, create_patient
from services.code_generator import verify_code
from services.encryption import decrypt_data
from services.email_service import (
    send_hospital_created_email,
    send_patient_created_email
)

from services.hospital import (
    get_hospital_by_user,
    upload_medical_record,
    get_records_for_hospital,
    get_requests_for_hospital,
    approve_access_request,
    reject_access_request
)

from flask import render_template, redirect, url_for, flash, session, send_file
from io import BytesIO

from services.patient import (
    get_patient_by_user,
    get_records_for_patient,
    get_requests_for_patient,
    create_access_request,
    is_request_approved,
    decrypt_medical_record
)


# =============================
# App Initialization
# =============================
app = Flask(__name__)
app.config.from_object("config.config.Config")

db.init_app(app)
migrate = Migrate(app, db)

# =============================
# RBAC Helpers
# =============================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(role):
    def wrapper(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if session.get("role") != role:
                flash("Unauthorized access", "danger")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return inner
    return wrapper


def get_record_hospital_id(record_id):
    from models.medical_record import MedicalRecord
    record = MedicalRecord.query.get(record_id)
    return record.hospital_id if record else None


# =============================
# Public Routes
# =============================
@app.route("/")
def home():
    return render_template("base.html")

# =============================
# Authentication
# =============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        user = User.query.filter_by(email=email).first()

        if not user or user.password != hashed_password:
            flash("Invalid email or password", "danger")
            return redirect(url_for("login"))

        # Successful login
        session["user_id"] = user.id
        session["role"] = user.role
        flash("Successfully logged in", "success")

        # Safer role-based redirect
        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        elif user.role == "hospital":
            return redirect(url_for("hospital_dashboard"))
        elif user.role == "patient":
            return redirect(url_for("patient_dashboard"))
        else:
            flash("Unauthorized role", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully logged out", "info")
    return redirect(url_for("login"))


# =============================
# Admin Routes
# =============================
@app.route("/admin/dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    hospitals = Hospital.query.all()
    patients = Patient.query.all()
    return render_template(
        "admin/dashboard.html",
        hospitals=hospitals,
        patients=patients
    )


@app.route("/admin/create_users")
@login_required
@role_required("admin")
def admin_create_users_page():
    return render_template(
        "admin/create_users.html",
        send_email=False,
        emailjs_service_id=app.config["EMAILJS_SERVICE_ID"],
        emailjs_public_key=app.config["EMAILJS_PUBLIC_KEY"],
        emailjs_hospital_template=app.config["EMAILJS_HOSPITAL_TEMPLATE_ID"],
        emailjs_patient_template=app.config["EMAILJS_PATIENT_TEMPLATE_ID"],
    )


@app.route("/admin/hospitals")
@login_required
@role_required("admin")
def admin_hospitals():
    hospitals = Hospital.query.all()
    return render_template("admin/hospitals.html", hospitals=hospitals)


@app.route("/admin/patients")
@login_required
@role_required("admin")
def admin_patients():
    patients = Patient.query.all()
    return render_template("admin/patients.html", patients=patients)


@app.route("/admin/create_hospital", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_hospital():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    hospital_identity_name = request.form.get("hospital_identity_name")

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("User already exists with this email", "danger")
        return redirect(url_for("admin_create_users_page"))

    hospital, hospital_code = create_hospital(
        name=name,
        email=email,
        password=password,
        hospital_identity_name=hospital_identity_name
    )

    return render_template(
        "admin/create_users.html",
        send_email=True,
        user_type="hospital",
        email=email,
        name=name,
        hospital_identity=hospital_identity_name,
        verification_code=hospital_code,

        # 🔑 EmailJS config from config.py
        emailjs_service_id=app.config["EMAILJS_SERVICE_ID"],
        emailjs_public_key=app.config["EMAILJS_PUBLIC_KEY"],
        emailjs_hospital_template=app.config["EMAILJS_HOSPITAL_TEMPLATE_ID"],
        emailjs_patient_template=app.config["EMAILJS_PATIENT_TEMPLATE_ID"],
    )


@app.route("/admin/create_patient", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_patient():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash("User already exists with this email", "danger")
        return redirect(url_for("admin_create_users_page"))

    patient, patient_code = create_patient(
        name=name,
        email=email,
        password=password
    )

    return render_template(
        "admin/create_users.html",
        send_email=True,
        user_type="patient",
        email=email,
        name=name,
        verification_code=patient_code,

        # 🔑 EmailJS config from config.py
        emailjs_service_id=app.config["EMAILJS_SERVICE_ID"],
        emailjs_public_key=app.config["EMAILJS_PUBLIC_KEY"],
        emailjs_hospital_template=app.config["EMAILJS_HOSPITAL_TEMPLATE_ID"],
        emailjs_patient_template=app.config["EMAILJS_PATIENT_TEMPLATE_ID"],
    )


@app.route("/admin/edit/user/<int:user_id>")
@login_required
@role_required("admin")
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)

    hospital = None
    patient = None

    if user.role == "hospital":
        hospital = Hospital.query.filter_by(user_id=user.id).first()

    elif user.role == "patient":
        patient = Patient.query.filter_by(user_id=user.id).first()

    return render_template(
        "admin/edit_user.html",
        user=user,
        hospital=hospital,
        patient=patient
    )

@app.route("/admin/update/user/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def admin_update_user(user_id):
    user = User.query.get_or_404(user_id)

    # Common fields
    email = request.form.get("email")
    new_password = request.form.get("password")

    # Update email
    if email:
        user.email = email.strip()

    # Update password ONLY if provided
    if new_password and new_password.strip():
        user.password = hashlib.sha256(
            new_password.encode()
        ).hexdigest()

    # Role-specific updates
    if user.role == "hospital":
        hospital = Hospital.query.filter_by(user_id=user.id).first()
        if hospital:
            hospital.name = request.form.get("name", hospital.name)
            hospital.hospital_identity_name = request.form.get(
                "hospital_identity_name",
                hospital.hospital_identity_name
            )

    elif user.role == "patient":
        patient = Patient.query.filter_by(user_id=user.id).first()
        if patient:
            patient.name = request.form.get("name", patient.name)

    db.session.commit()

    flash("User details updated successfully", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/delete/user/<int:user_id>")
@login_required
@role_required("admin")
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # 🔴 Delete role-specific record FIRST
    if user.role == "hospital":
        hospital = Hospital.query.filter_by(user_id=user.id).first()
        if hospital:
            db.session.delete(hospital)

    elif user.role == "patient":
        patient = Patient.query.filter_by(user_id=user.id).first()
        if patient:
            db.session.delete(patient)

    # 🔴 Now delete the user
    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully", "success")
    return redirect(url_for("admin_dashboard"))


# =============================
# Hospital Routes
# =============================
@app.route("/hospital/dashboard")
@login_required
@role_required("hospital")
def hospital_dashboard():
    hospital = get_hospital_by_user(session["user_id"])
    if not hospital:
        flash("Hospital profile not found", "danger")
        return redirect(url_for("logout"))

    records = get_records_for_hospital(hospital.id)
    requests = get_requests_for_hospital(hospital.id)

    return render_template(
        "hospital/dashboard.html",
        records=records,
        requests=requests
    )

@app.route("/hospital/upload", methods=["GET", "POST"])
@login_required
@role_required("hospital")
def hospital_upload_record():
    # 1️⃣ Get hospital linked to logged-in user
    hospital = get_hospital_by_user(session["user_id"])
    if not hospital:
        flash("Hospital profile not found", "danger")
        return redirect(url_for("logout"))

    # =================================================
    # POST: Handle file upload
    # =================================================
    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        title = request.form.get("title")
        file = request.files.get("file")

        # Basic validation
        if not patient_id or not title or not file:
            flash("All fields are required", "warning")
            return redirect(url_for("hospital_upload_record"))

        try:
            upload_medical_record(
                hospital_id=hospital.id,
                patient_id=int(patient_id),
                title=title,
                file=file
            )
            flash("Medical record uploaded & encrypted successfully", "success")
            return redirect(url_for("hospital_dashboard"))

        except Exception as e:
            print("UPLOAD ERROR:", e)
            flash("Failed to upload medical record", "danger")
            return redirect(url_for("hospital_upload_record"))

    # =================================================
    # GET: Send patient data for dropdown + autofill
    # =================================================
    patients = Patient.query.all()

    patient_data = []
    for patient in patients:
        user = User.query.get(patient.user_id)
        if user:
            patient_data.append({
                "id": patient.id,
                "email": user.email,
                "name": patient.name
            })

    return render_template(
        "hospital/upload.html",
        patients=patient_data
    )


@app.route("/hospital/records")
@login_required
@role_required("hospital")
def hospital_records():
    hospital = get_hospital_by_user(session["user_id"])
    if not hospital:
        flash("Hospital profile not found", "danger")
        return redirect(url_for("logout"))

    records = get_records_for_hospital(hospital.id)

    return render_template(
        "hospital/records.html",
        records=records
    )

@app.route("/hospital/requests")
@login_required
@role_required("hospital")
def hospital_requests():
    hospital = get_hospital_by_user(session["user_id"])
    if not hospital:
        flash("Hospital profile not found", "danger")
        return redirect(url_for("logout"))

    requests = get_requests_for_hospital(hospital.id)

    return render_template(
        "hospital/requests.html",
        requests=requests
    )



@app.route("/hospital/request/<int:req_id>/approve", methods=["POST"])
@login_required
@role_required("hospital")
def hospital_approve_request(req_id):
    hospital = get_hospital_by_user(session["user_id"])
    if not hospital:
        flash("Hospital profile not found", "danger")
        return redirect(url_for("logout"))

    success, message = approve_access_request(req_id, hospital.id)

    flash(message, "success" if success else "danger")
    return redirect(url_for("hospital_requests"))




@app.route("/hospital/request/<int:req_id>/reject", methods=["POST"])
@login_required
@role_required("hospital")
def hospital_reject_request(req_id):
    hospital = get_hospital_by_user(session["user_id"])
    if not hospital:
        flash("Hospital profile not found", "danger")
        return redirect(url_for("logout"))

    success, message = reject_access_request(req_id, hospital.id)

    flash(message, "info" if success else "danger")
    return redirect(url_for("hospital_requests"))



# =============================
# Patient Routes
# =============================
@app.route("/patient/dashboard")
@login_required
@role_required("patient")
def patient_dashboard():
    patient = get_patient_by_user(session["user_id"])
    if not patient:
        flash("Patient profile not found", "danger")
        return redirect(url_for("logout"))

    records = get_records_for_patient(patient.id)
    requests = get_requests_for_patient(patient.id)

    return render_template(
        "patient/dashboard.html",
        records=records,
        requests=requests
    )

@app.route("/patient/records")
@login_required
@role_required("patient")
def patient_records():
    patient = get_patient_by_user(session["user_id"])
    if not patient:
        flash("Patient profile not found", "danger")
        return redirect(url_for("logout"))

    records = get_records_for_patient(patient.id)
    requests = get_requests_for_patient(patient.id)

    return render_template(
        "patient/records.html",
        records=records,
        requests=requests
    )


# @app.route("/patient/request/<int:record_id>")
# @login_required
# @role_required("patient")
# def request_record(record_id):
#     patient = Patient.query.filter_by(user_id=session["user_id"]).first()
#     record = MedicalRecord.query.get_or_404(record_id)

#     req = AccessRequest(
#         record_id=record.id,
#         patient_id=patient.id,
#         hospital_id=record.hospital_id
#     )

#     db.session.add(req)
#     db.session.commit()

#     flash("Record request sent", "info")
#     return redirect(url_for("patient_dashboard"))

@app.route("/patient/requests")
@login_required
@role_required("patient")
def patient_requests():
    patient = get_patient_by_user(session["user_id"])
    if not patient:
        flash("Patient profile not found", "danger")
        return redirect(url_for("logout"))

    requests = get_requests_for_patient(patient.id)

    return render_template(
        "patient/requests.html",
        requests=requests
    )

@app.route("/patient/request", methods=["POST"])
@login_required
@role_required("patient")
def patient_request_access():
    # 1️⃣ Get logged-in patient
    patient = get_patient_by_user(session["user_id"])
    if not patient:
        flash("Patient profile not found", "danger")
        return redirect(url_for("patient_records"))

    # 2️⃣ Get form data
    record_id = request.form.get("record_id")
    verification_code = request.form.get("verification_code")

    if not record_id or not verification_code:
        flash("Please verify your identity using the verification code", "warning")
        return redirect(url_for("patient_records"))

    # 3️⃣ Verify patient identity (MANDATORY)
    if not verify_code(verification_code, patient.patient_code_hash):
        flash("Invalid verification code. Please verify your identity.", "danger")
        return redirect(url_for("patient_records"))

    # 4️⃣ Prevent duplicate requests
    existing_request = AccessRequest.query.filter_by(
        patient_id=patient.id,
        record_id=record_id
    ).first()

    if existing_request:
        flash("Access request already submitted for this record", "info")
        return redirect(url_for("patient_records"))

    # 5️⃣ Create VERIFIED access request
    access_request = AccessRequest(
        patient_id=patient.id,
        record_id=record_id,
        hospital_id=get_record_hospital_id(record_id),
        status="PENDING",
        verified_by_patient=True
    )

    db.session.add(access_request)
    db.session.commit()

    flash("Access request submitted successfully", "success")
    return redirect(url_for("patient_requests"))



# @app.route("/patient/request/<int:record_id>")
# @login_required
# @role_required("patient")
# def patient_request_record(record_id):
#     patient = get_patient_by_user(session["user_id"])
#     if not patient:
#         flash("Patient profile not found", "danger")
#         return redirect(url_for("logout"))

#     success, message = create_access_request(patient.id, record_id)

#     if success:
#         flash(message, "success")
#     else:
#         flash(message, "warning")

#     return redirect(url_for("patient_records"))


@app.route("/patient/download/<int:record_id>")
@login_required
@role_required("patient")
def patient_download_record(record_id):
    patient = get_patient_by_user(session["user_id"])
    if not patient:
        flash("Patient profile not found", "danger")
        return redirect(url_for("logout"))

    approval = is_request_approved(patient.id, record_id)
    if not approval:
        flash("Access not approved for this record", "danger")
        return redirect(url_for("patient_requests"))

    record = approval.record

    try:
        decrypted_data = decrypt_medical_record(record)

        # ✅ Extract original filename & extension
        original_filename = os.path.basename(record.file_path)

        # ✅ Guess MIME type (pdf, image, etc.)
        mime_type, _ = guess_type(original_filename)

        return send_file(
            BytesIO(decrypted_data),
            as_attachment=True,
            download_name=original_filename,
            mimetype=mime_type or "application/octet-stream"
        )

    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        flash("Failed to download medical record", "danger")
        return redirect(url_for("patient_requests"))

# @app.route("/patient/download/<int:record_id>")
# @login_required
# @role_required("patient")
# def download_record(record_id):
#     patient = Patient.query.filter_by(user_id=session["user_id"]).first()

#     req = AccessRequest.query.filter_by(
#         record_id=record_id,
#         patient_id=patient.id,
#         status="APPROVED"
#     ).first()

#     if not req:
#         flash("Unauthorized access", "danger")
#         return redirect(url_for("patient_dashboard"))

#     record = MedicalRecord.query.get_or_404(record_id)

#     with open(record.file_path, "rb") as f:
#         decrypted = decrypt_data(f.read())

#     temp_path = record.file_path + "_tmp"
#     with open(temp_path, "wb") as f:
#         f.write(decrypted)

#     return send_file(temp_path, as_attachment=True)

# =============================
# Run
# =============================
if __name__ == "__main__":
    app.run(debug=True)

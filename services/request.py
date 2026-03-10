from models.request import AccessRequest

def get_requests_for_hospital(hospital_id):
    return AccessRequest.query.filter_by(hospital_id=hospital_id).all()


def get_requests_for_patient(patient_id):
    return AccessRequest.query.filter_by(patient_id=patient_id).all()

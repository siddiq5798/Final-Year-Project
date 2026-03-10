import hashlib
from models.user import User

def authenticate_user(email, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return User.query.filter_by(email=email, password=hashed_password).first()

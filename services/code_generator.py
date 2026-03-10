import random
import string
import hashlib


def generate_code(length=6):
    """
    Generates a random alphanumeric code.
    Example: A9K3P7
    """
    characters = string.ascii_uppercase + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def hash_code(code: str) -> str:
    """
    Hashes the code using SHA-256 before storing in DB.
    """
    return hashlib.sha256(code.encode()).hexdigest()


def verify_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verifies a plain code against stored hash.
    """
    return hashlib.sha256(plain_code.encode()).hexdigest() == hashed_code

from Crypto.Cipher import AES
from flask import current_app

def encrypt_data(data: bytes) -> bytes:
    key = current_app.config["AES_SECRET_KEY"]
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return cipher.nonce + tag + ciphertext


def decrypt_data(encrypted_data: bytes) -> bytes:
    key = current_app.config["AES_SECRET_KEY"]
    nonce = encrypted_data[:16]
    tag = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)

import bcrypt
import hashlib

def hash_password(plain_text):
    return bcrypt.hashpw(plain_text.encode(), bcrypt.gensalt()).decode()

def verificar_password(plain_text, hashed):
    return bcrypt.checkpw(plain_text.encode(), hashed.encode())

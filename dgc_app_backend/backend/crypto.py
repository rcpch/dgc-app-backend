import os
import base64
import hashlib

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key(password: str, salt: str, iterations: int) -> Fernet:
  kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt.encode('utf-8'),
    iterations=iterations,
  )

  key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))

  return Fernet(key)


def encrypt_bytes(f: Fernet, data: bytes) -> str:
  encrypted_data = f.encrypt(data)
  return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')


def encrypt_str(f: Fernet, data: str) -> str:
  return encrypt_bytes(f, data.encode('utf-8'))


def decrypt_bytes(f: Fernet, data: str) -> bytes:
  encrypted_data = base64.urlsafe_b64decode(data.encode('utf-8'))
  return f.decrypt(encrypted_data)


def decrypt_str(f: Fernet, data: str) -> str:
  return decrypt_bytes(f, data).decode('utf-8')


def sha_256(data: str) -> str:
  m = hashlib.sha256()
  m.update(data.encode('utf-8'))
  return m.hexdigest()


def salt() -> str:
  return os.urandom(32).hex()
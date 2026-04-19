import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import secrets
import base64

# For AES-256, use 32-byte key
def get_key() -> bytes:
    """
    Get encryption key from environment variable.
    For AES-256, ensure key is 32 bytes.
    """
    key_hex = os.getenv('ENCRYPTION_KEY')
    if not key_hex:
        raise ValueError("ENCRYPTION_KEY not set")
    try:
        key = bytes.fromhex(key_hex)
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes (64 hex chars)")
        return key
    except ValueError:
        raise ValueError("Invalid ENCRYPTION_KEY")

def encrypt_pan(pan: str) -> str:
    """
    Encrypt the PAN using AES-256-GCM.
    Returns nonce + tag + ciphertext as base64.
    """
    key = get_key()
    nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(pan.encode()) + encryptor.finalize()
    # Combine nonce + tag + ciphertext
    encrypted = nonce + encryptor.tag + ciphertext
    return base64.b64encode(encrypted).decode()

def decrypt_pan(encrypted_pan: str) -> str:
    """
    Decrypt the PAN using AES-256-GCM.
    """
    key = get_key()
    encrypted = base64.b64decode(encrypted_pan)
    nonce = encrypted[:12]
    tag = encrypted[12:28]
    ciphertext = encrypted[28:]
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode()

# Validate key on startup
get_key()
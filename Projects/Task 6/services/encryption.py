import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class EncryptionService:
    """AES-256 encryption service for PAN data.

    Uses AES-GCM for authenticated encryption plus random nonce per request.
    The raw PAN is only used in memory during request processing and is never stored.
    """
    def __init__(self, key: bytes):
        self._key = key
        self._aead = AESGCM(key)

    def encrypt_pan(self, pan: str) -> str:
        nonce = secrets.token_bytes(12)
        ciphertext = self._aead.encrypt(nonce, pan.encode("utf-8"), associated_data=None)
        payload = nonce + ciphertext
        return base64.urlsafe_b64encode(payload).decode("ascii")

    def decrypt_pan(self, encrypted_data: str) -> str:
        payload = base64.urlsafe_b64decode(encrypted_data.encode("ascii"))
        nonce = payload[:12]
        ciphertext = payload[12:]
        plaintext = self._aead.decrypt(nonce, ciphertext, associated_data=None)
        return plaintext.decode("utf-8")

    def simulate_fpe(self, pan: str) -> str:
        """Demonstrate a numeric-preserving transformation for PAN values.

        This is provided only as a conceptual FPE simulation. The actual stored
        PAN mapping uses authenticated AES-GCM encryption because strong data
        protection and integrity are needed for production use.
        """
        digits = [int(char) for char in pan]
        cipher = Cipher(algorithms.AES(self._key), modes.ECB())
        encryptor = cipher.encryptor()
        transformed = []
        counter = 0
        while len(transformed) < len(digits):
            block = counter.to_bytes(16, "big")
            stream_block = encryptor.update(block)
            for byte in stream_block:
                if len(transformed) >= len(digits):
                    break
                transformed.append((digits[len(transformed)] + (byte % 10)) % 10)
            counter += 1
        return "".join(str(digit) for digit in transformed)

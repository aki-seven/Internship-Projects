import secrets
import uuid
from typing import Optional
from storage.database import TokenStorage


class TokenizationService:
    def __init__(self, storage: TokenStorage):
        self.storage = storage

    def generate_token(self) -> str:
        return uuid.uuid4().hex

    def tokenize(self, encrypted_pan: str) -> str:
        token = self.generate_token()
        self.storage.save_token(token, encrypted_pan)
        return token

    def detokenize(self, token: str) -> Optional[str]:
        return self.storage.get_encrypted_pan(token)

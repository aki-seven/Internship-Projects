from functools import lru_cache
from fastapi import Depends
from config.settings import settings
from services.encryption import EncryptionService
from services.tokenization import TokenizationService
from storage.database import TokenStorage


@lru_cache()
def get_token_storage() -> TokenStorage:
    """Single shared SQLite storage instance for the application."""
    return TokenStorage(settings.sqlite_db_path)


@lru_cache()
def get_encryption_service() -> EncryptionService:
    """Provides the AES-256 encryption service loaded from the environment key."""
    return EncryptionService(settings.encryption_key)


def get_tokenization_service(
    storage: TokenStorage = Depends(get_token_storage),
) -> TokenizationService:
    """Provides the tokenization service using the shared storage backend."""
    return TokenizationService(storage)

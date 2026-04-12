import os
import tempfile
import secrets
from services.encryption import EncryptionService
from services.tokenization import TokenizationService
from storage.database import TokenStorage


def test_tokenize_and_detokenize_round_trip():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_store.db")
        with TokenStorage(db_path) as storage:
            token_service = TokenizationService(storage)
            key = secrets.token_bytes(32)
            encryptor = EncryptionService(key)

            pan = "4242424242424242"
            encrypted_pan = encryptor.encrypt_pan(pan)
            token = token_service.tokenize(encrypted_pan)

            stored_encrypted = token_service.detokenize(token)
            assert stored_encrypted == encrypted_pan
            assert encryptor.decrypt_pan(stored_encrypted) == pan


def test_detokenize_invalid_token_returns_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_store.db")
        with TokenStorage(db_path) as storage:
            token_service = TokenizationService(storage)

            assert token_service.detokenize("missingtoken") is None

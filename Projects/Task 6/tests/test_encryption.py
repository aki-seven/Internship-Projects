import secrets
from services.encryption import EncryptionService


def test_encrypt_and_decrypt_returns_original_pan():
    key = secrets.token_bytes(32)
    service = EncryptionService(key)
    pan = "4242424242424242"

    encrypted = service.encrypt_pan(pan)
    assert encrypted != pan

    decrypted = service.decrypt_pan(encrypted)
    assert decrypted == pan


def test_simulate_fpe_keeps_length_and_numeric():
    key = secrets.token_bytes(32)
    service = EncryptionService(key)
    pan = "4000123412341234"

    fpe_value = service.simulate_fpe(pan)
    assert len(fpe_value) == len(pan)
    assert fpe_value.isdigit()

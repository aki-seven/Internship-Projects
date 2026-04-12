import base64
import binascii
from pathlib import Path
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    # AES-256 key loaded from environment. The value can be hex or base64 encoded.
    encryption_key: bytes = Field(..., env="ENCRYPTION_KEY")
    detokenize_api_key: str = Field(..., env="DETOKENIZE_API_KEY")
    sqlite_db_path: str = Field(default="data/token_store.db", env="SQLITE_DB_PATH")
    rate_limit_requests: int = Field(default=20, env="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")

    @validator("encryption_key", pre=True)
    def parse_encryption_key(cls, value):
        if isinstance(value, bytes):
            key_bytes = value
        elif isinstance(value, str):
            key_bytes = None
            if len(value) == 64:
                try:
                    key_bytes = bytes.fromhex(value)
                except ValueError:
                    pass
            if key_bytes is None:
                try:
                    key_bytes = base64.b64decode(value, validate=True)
                except (binascii.Error, ValueError):
                    pass
        else:
            raise ValueError("ENCRYPTION_KEY must be a string or bytes")

        if not key_bytes or len(key_bytes) != 32:
            raise ValueError("ENCRYPTION_KEY must decode to 32 bytes (AES-256 key)")
        return key_bytes

    @validator("sqlite_db_path", pre=True, always=True)
    def normalize_db_path(cls, value):
        if value:
            return str(Path(value).expanduser())
        return value

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

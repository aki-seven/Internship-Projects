# app/core/config.py
from pydantic import field_validator
from pydantic_settings import BaseSettings  # pip install pydantic-settings if needed
import secrets


class Settings(BaseSettings):
    # JWT
    JWT_SECRET: str = secrets.token_hex(32)
    JWT_REFRESH_SECRET: str = secrets.token_hex(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    APP_NAME: str = "SecureSense Auth API"
    DEBUG: bool = True
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8001"]

    # Password reset token TTL
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15

    # Brute-force protection
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_MINUTES: int = 15

    class Config:
        env_file = ".env"


settings = Settings()

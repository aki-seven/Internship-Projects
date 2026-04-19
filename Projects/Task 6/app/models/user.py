# app/models/user.py
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class Role(str, Enum):
    admin     = "admin"
    moderator = "moderator"
    user      = "user"


# ── DB model (never sent to client) ───────────────────────────

class UserInDB(BaseModel):
    id: str
    username: str
    email: str
    hashed_password: str
    role: Role = Role.user
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()

    model_config = {"frozen": False}


# ── Public user shape (returned to clients) ────────────────────

class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    role: Role
    mfa_enabled: bool
    created_at: datetime


# ── Request schemas ────────────────────────────────────────────

def _validate_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[0-9]", v):
        raise ValueError("Password must contain at least one digit")
    return v


class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[Role] = None  # only respected for first-user bootstrap

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return _validate_password(v)

    @field_validator("username")
    @classmethod
    def valid_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError("Username must be 3-30 alphanumeric/underscore characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_token: Optional[str] = None  # TOTP code if MFA enabled


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return _validate_password(v)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return _validate_password(v)


class MFAVerifyRequest(BaseModel):
    token: str  # 6-digit TOTP code


class MFADisableRequest(BaseModel):
    password: str


class UpdateRoleRequest(BaseModel):
    role: Role


# ── Response schemas ───────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic


class MessageResponse(BaseModel):
    message: str


class MFASetupResponse(BaseModel):
    message: str
    secret: str
    qr_code: str  # base64 data URI

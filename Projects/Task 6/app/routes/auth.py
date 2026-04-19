# app/routes/auth.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.core import database as db
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_reset_token,
    generate_mfa_secret,
    generate_mfa_qr,
    verify_totp,
)
from app.middleware.auth import (
    get_current_user,
    check_account_lock,
    record_failed_login,
    clear_login_attempts,
)
from app.models.user import (
    Role,
    UserInDB,
    UserPublic,
    SignupRequest,
    LoginRequest,
    RefreshRequest,
    LogoutRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    MFAVerifyRequest,
    MFADisableRequest,
    MessageResponse,
    MFASetupResponse,
    TokenResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── POST /auth/signup ──────────────────────────────────────────
@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest):
    if db.email_exists(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    if db.username_exists(body.username):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

    # First user ever → admin bootstrap
    role = Role.admin if db.count_users() == 0 else Role.user
    # Explicit role request only honoured during bootstrap
    if body.role and db.count_users() == 0:
        role = body.role

    hashed = hash_password(body.password)
    user = db.create_user(body.username, body.email, hashed, role)
    logger.info("New user registered: %s (%s)", user.email, user.role)
    return UserPublic(**user.model_dump())


# ── POST /auth/login ───────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = db.get_user_by_email(body.email)

    # Generic error to prevent user enumeration
    _bad_creds = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    if not user:
        raise _bad_creds

    check_account_lock(user)

    if not verify_password(body.password, user.hashed_password):
        record_failed_login(user, settings.MAX_LOGIN_ATTEMPTS, settings.LOCKOUT_MINUTES)
        raise _bad_creds

    # MFA gate
    if user.mfa_enabled:
        if not body.mfa_token:
            raise HTTPException(
                status.HTTP_200_OK,
                detail={"mfa_required": True, "message": "Provide your 6-digit TOTP code"},
            )
        if not verify_totp(user.mfa_secret, body.mfa_token):
            record_failed_login(user, settings.MAX_LOGIN_ATTEMPTS, settings.LOCKOUT_MINUTES)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid MFA token")

    clear_login_attempts(user.id)

    access  = create_access_token(user.id, user.role.value)
    refresh = create_refresh_token(user.id, user.role.value)
    db.store_refresh_token(refresh)

    logger.info("Login: %s", user.email)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserPublic(**user.model_dump()),
    )


# ── POST /auth/refresh ─────────────────────────────────────────
@router.post("/refresh")
async def refresh_token(body: RefreshRequest):
    if not db.has_refresh_token(body.refresh_token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token revoked or invalid")
    try:
        payload = decode_refresh_token(body.refresh_token)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    db.revoke_refresh_token(body.refresh_token)

    new_access  = create_access_token(payload["sub"], payload["role"])
    new_refresh = create_refresh_token(payload["sub"], payload["role"])
    db.store_refresh_token(new_refresh)

    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}


# ── POST /auth/logout ──────────────────────────────────────────
@router.post("/logout", response_model=MessageResponse)
async def logout(body: LogoutRequest, current_user: UserInDB = Depends(get_current_user)):
    if body.refresh_token:
        db.revoke_refresh_token(body.refresh_token)
    logger.info("Logout: %s", current_user.email)
    return MessageResponse(message="Logged out successfully")


# ── POST /auth/forgot-password ─────────────────────────────────
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest):
    user = db.get_user_by_email(body.email)
    _generic = MessageResponse(message="If that email exists, a reset link has been sent.")

    if not user:
        return _generic  # prevent enumeration

    token = generate_reset_token()
    db.store_reset_token(token, user.id, settings.PASSWORD_RESET_EXPIRE_MINUTES)

    # In production → send via SMTP/SendGrid/etc.
    logger.warning("[DEV] Password reset token for %s: %s", body.email, token)
    print(f"\n{'='*60}\n[PASSWORD RESET] Token for {body.email}:\n{token}\n{'='*60}\n")

    return _generic


# ── POST /auth/reset-password ──────────────────────────────────
@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest):
    user_id = db.consume_reset_token(body.token)
    if not user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired reset token")

    hashed = hash_password(body.new_password)
    db.update_user(user_id, hashed_password=hashed)
    # Revoke all refresh tokens on password change
    db.revoke_all_refresh_tokens()

    return MessageResponse(message="Password reset successfully. Please log in again.")


# ── POST /auth/mfa/setup ───────────────────────────────────────
@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(current_user: UserInDB = Depends(get_current_user)):
    if current_user.mfa_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "MFA is already enabled")

    secret = generate_mfa_secret()
    qr     = generate_mfa_qr(secret, current_user.email)
    db.update_user(current_user.id, mfa_secret=secret)

    return MFASetupResponse(
        message="Scan the QR code with your authenticator app, then call /auth/mfa/verify to activate.",
        secret=secret,
        qr_code=qr,
    )


# ── POST /auth/mfa/verify ──────────────────────────────────────
@router.post("/mfa/verify", response_model=MessageResponse)
async def mfa_verify(body: MFAVerifyRequest, current_user: UserInDB = Depends(get_current_user)):
    user = db.get_user_by_id(current_user.id)
    if not user.mfa_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Call /auth/mfa/setup first")
    if not verify_totp(user.mfa_secret, body.token):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid TOTP token")

    db.update_user(user.id, mfa_enabled=True)
    return MessageResponse(message="MFA enabled successfully")


# ── POST /auth/mfa/disable ─────────────────────────────────────
@router.post("/mfa/disable", response_model=MessageResponse)
async def mfa_disable(body: MFADisableRequest, current_user: UserInDB = Depends(get_current_user)):
    user = db.get_user_by_id(current_user.id)
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    db.update_user(user.id, mfa_enabled=False, mfa_secret=None)
    return MessageResponse(message="MFA disabled")

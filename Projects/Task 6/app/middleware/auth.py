# app/middleware/auth.py
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError

from app.core import database as db
from app.core.security import decode_access_token
from app.models.user import Role, UserInDB

bearer_scheme = HTTPBearer(auto_error=True)


# ── Current user dependency ────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserInDB:
    token = credentials.credentials
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exc
    except JWTError as e:
        msg = "Token has expired" if "expired" in str(e).lower() else "Invalid token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


# ── Role-based access control ──────────────────────────────────

def require_role(*roles: Role):
    """
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(Role.admin))])
        async def admin_only(): ...

    Or as a parameter:
        async def endpoint(user: UserInDB = Depends(require_role(Role.admin, Role.moderator))):
    """
    async def checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(r.value for r in roles)}",
            )
        return current_user
    return checker


# ── Account lock helpers ───────────────────────────────────────

def check_account_lock(user: UserInDB) -> None:
    if user.locked_until and datetime.now(timezone.utc) < user.locked_until.replace(tzinfo=timezone.utc):
        remaining = int((user.locked_until.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked due to too many failed attempts. Try again in {remaining}s.",
        )


def record_failed_login(user: UserInDB, max_attempts: int, lockout_minutes: int) -> None:
    from datetime import timedelta
    attempts = user.login_attempts + 1
    update: dict = {"login_attempts": attempts}
    if attempts >= max_attempts:
        update["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
        update["login_attempts"] = 0
    db.update_user(user.id, **update)


def clear_login_attempts(user_id: str) -> None:
    db.update_user(user_id, login_attempts=0, locked_until=None)

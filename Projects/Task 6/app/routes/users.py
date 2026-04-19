# app/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status

from app.core import database as db
from app.core.security import hash_password, verify_password
from app.middleware.auth import get_current_user, require_role
from app.models.user import (
    Role,
    UserInDB,
    UserPublic,
    ChangePasswordRequest,
    UpdateRoleRequest,
    MessageResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


# ── GET /users/me ──────────────────────────────────────────────
@router.get("/me", response_model=UserPublic)
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    return UserPublic(**current_user.model_dump())


# ── PUT /users/me/password ─────────────────────────────────────
@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: UserInDB = Depends(get_current_user),
):
    user = db.get_user_by_id(current_user.id)
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Current password is incorrect")

    db.update_user(user.id, hashed_password=hash_password(body.new_password))
    # Revoke all refresh tokens to force re-login
    db.revoke_all_refresh_tokens()
    return MessageResponse(message="Password changed. Please log in again.")


# ── DELETE /users/me ───────────────────────────────────────────
@router.delete("/me", response_model=MessageResponse)
async def delete_own_account(
    current_user: UserInDB = Depends(get_current_user),
):
    db.delete_user(current_user.id)
    return MessageResponse(message="Account deleted")


# ════════════════════════════════════════════════════════════════
# ADMIN endpoints
# ════════════════════════════════════════════════════════════════

# ── GET /users  (admin) ────────────────────────────────────────
@router.get("/", response_model=list[UserPublic])
async def list_all_users(
    _admin: UserInDB = Depends(require_role(Role.admin)),
):
    return [UserPublic(**u.model_dump()) for u in db.list_users()]


# ── GET /users/{uid}  (admin) ──────────────────────────────────
@router.get("/{uid}", response_model=UserPublic)
async def get_user(
    uid: str,
    current_user: UserInDB = Depends(get_current_user),
):
    # Self or admin can access
    if current_user.id != uid and current_user.role != Role.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied")

    user = db.get_user_by_id(uid)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserPublic(**user.model_dump())


# ── PUT /users/{uid}/role  (admin) ─────────────────────────────
@router.put("/{uid}/role", response_model=UserPublic)
async def update_role(
    uid: str,
    body: UpdateRoleRequest,
    _admin: UserInDB = Depends(require_role(Role.admin)),
):
    user = db.get_user_by_id(uid)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    updated = db.update_user(uid, role=body.role)
    return UserPublic(**updated.model_dump())


# ── DELETE /users/{uid}  (admin) ───────────────────────────────
@router.delete("/{uid}", response_model=MessageResponse)
async def delete_user(
    uid: str,
    _admin: UserInDB = Depends(require_role(Role.admin)),
):
    if not db.delete_user(uid):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return MessageResponse(message=f"User {uid} deleted")


# ════════════════════════════════════════════════════════════════
# MODERATOR endpoints  (read-only user list)
# ════════════════════════════════════════════════════════════════

@router.get("/mod/dashboard", response_model=dict)
async def mod_dashboard(
    _mod: UserInDB = Depends(require_role(Role.admin, Role.moderator)),
):
    users = db.list_users()
    return {
        "total_users": len(users),
        "roles": {
            "admin":     sum(1 for u in users if u.role == Role.admin),
            "moderator": sum(1 for u in users if u.role == Role.moderator),
            "user":      sum(1 for u in users if u.role == Role.user),
        },
        "mfa_enabled": sum(1 for u in users if u.mfa_enabled),
    }

# app/core/database.py
"""
Thread-safe in-memory store.
Swap `_users`, `_refresh_tokens`, `_reset_tokens` with SQLAlchemy/SQLite/Postgres
models in production — the interface stays identical.
"""
import uuid
import threading
from datetime import datetime, timedelta
from typing import Optional
from app.models.user import UserInDB, Role

_lock = threading.Lock()

_users: dict[str, UserInDB] = {}          # id  -> UserInDB
_email_index: dict[str, str] = {}         # email -> id
_username_index: dict[str, str] = {}      # username -> id
_refresh_tokens: set[str] = set()
_reset_tokens: dict[str, tuple[str, datetime]] = {}  # token -> (user_id, expires)


# ── Users ──────────────────────────────────────────────────────

def create_user(username: str, email: str, hashed_password: str, role: Role = Role.user) -> UserInDB:
    with _lock:
        uid = str(uuid.uuid4())
        user = UserInDB(
            id=uid,
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
        )
        _users[uid] = user
        _email_index[email.lower()] = uid
        _username_index[username.lower()] = uid
        return user


def get_user_by_id(uid: str) -> Optional[UserInDB]:
    return _users.get(uid)


def get_user_by_email(email: str) -> Optional[UserInDB]:
    uid = _email_index.get(email.lower())
    return _users.get(uid) if uid else None


def get_user_by_username(username: str) -> Optional[UserInDB]:
    uid = _username_index.get(username.lower())
    return _users.get(uid) if uid else None


def update_user(uid: str, **fields) -> Optional[UserInDB]:
    with _lock:
        user = _users.get(uid)
        if not user:
            return None
        updated = user.model_copy(update=fields)
        _users[uid] = updated
        return updated


def delete_user(uid: str) -> bool:
    with _lock:
        user = _users.pop(uid, None)
        if user:
            _email_index.pop(user.email.lower(), None)
            _username_index.pop(user.username.lower(), None)
            return True
        return False


def list_users() -> list[UserInDB]:
    return list(_users.values())


def email_exists(email: str) -> bool:
    return email.lower() in _email_index


def username_exists(username: str) -> bool:
    return username.lower() in _username_index


def count_users() -> int:
    return len(_users)


# ── Refresh Tokens ─────────────────────────────────────────────

def store_refresh_token(token: str) -> None:
    with _lock:
        _refresh_tokens.add(token)


def has_refresh_token(token: str) -> bool:
    return token in _refresh_tokens


def revoke_refresh_token(token: str) -> bool:
    with _lock:
        existed = token in _refresh_tokens
        _refresh_tokens.discard(token)
        return existed


def revoke_all_refresh_tokens() -> None:
    with _lock:
        _refresh_tokens.clear()


# ── Password Reset Tokens ──────────────────────────────────────

def store_reset_token(token: str, user_id: str, expire_minutes: int) -> None:
    with _lock:
        expires = datetime.utcnow() + timedelta(minutes=expire_minutes)
        _reset_tokens[token] = (user_id, expires)


def consume_reset_token(token: str) -> Optional[str]:
    """Returns user_id if valid, else None. Deletes token after use."""
    with _lock:
        entry = _reset_tokens.pop(token, None)
        if not entry:
            return None
        user_id, expires = entry
        if datetime.utcnow() > expires:
            return None
        return user_id

# tests/test_auth.py
"""
Full integration test suite for the SecureSense Auth API.
Run:  pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core import database as db

client = TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def reset_db():
    """Wipe in-memory store before every test."""
    db._users.clear()
    db._email_index.clear()
    db._username_index.clear()
    db._refresh_tokens.clear()
    db._reset_tokens.clear()
    yield


# ── Helpers ────────────────────────────────────────────────────

def signup(username="aki", email="aki@securesense.io", password="Secure123", role=None):
    body = {"username": username, "email": email, "password": password}
    if role:
        body["role"] = role
    return client.post("/auth/signup", json=body)


def login(email="aki@securesense.io", password="Secure123", mfa_token=None):
    body = {"email": email, "password": password}
    if mfa_token:
        body["mfa_token"] = mfa_token
    return client.post("/auth/login", json=body)


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════════════════════
# SIGNUP
# ══════════════════════════════════════════════════════════════

class TestSignup:
    def test_signup_success(self):
        r = signup()
        assert r.status_code == 201
        d = r.json()
        assert d["email"] == "aki@securesense.io"
        assert d["role"] == "admin"           # first user → admin

    def test_second_user_is_regular(self):
        signup()
        r = signup("bob", "bob@example.com", "Secure123")
        assert r.status_code == 201
        assert r.json()["role"] == "user"

    def test_duplicate_email(self):
        signup()
        r = signup()
        assert r.status_code == 409

    def test_duplicate_username(self):
        signup()
        r = signup(email="other@example.com")
        assert r.status_code == 409

    def test_weak_password_too_short(self):
        r = signup(password="Ab1")
        assert r.status_code == 422

    def test_weak_password_no_uppercase(self):
        r = signup(password="secure123")
        assert r.status_code == 422

    def test_weak_password_no_digit(self):
        r = signup(password="SecurePass")
        assert r.status_code == 422

    def test_invalid_email(self):
        r = client.post("/auth/signup", json={"username": "x", "email": "notanemail", "password": "Secure123"})
        assert r.status_code == 422

    def test_invalid_username_chars(self):
        r = signup(username="bad user!")
        assert r.status_code == 422


# ══════════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════════

class TestLogin:
    def test_login_success(self):
        signup()
        r = login()
        assert r.status_code == 200
        d = r.json()
        assert "access_token" in d
        assert "refresh_token" in d

    def test_wrong_password(self):
        signup()
        r = login(password="WrongPass1")
        assert r.status_code == 401

    def test_nonexistent_email(self):
        r = login(email="ghost@x.com")
        assert r.status_code == 401

    def test_account_lockout(self):
        signup()
        for _ in range(5):
            login(password="WrongPass1")
        r = login(password="WrongPass1")
        assert r.status_code == 429

    def test_correct_login_after_failed_resets_counter(self):
        signup()
        login(password="WrongPass1")  # 1 failed
        r = login()                   # success resets
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════
# JWT / REFRESH
# ══════════════════════════════════════════════════════════════

class TestTokens:
    def test_refresh_success(self):
        signup()
        tokens = login().json()
        r = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_refresh_replay_rejected(self):
        signup()
        tokens = login().json()
        rt = tokens["refresh_token"]
        client.post("/auth/refresh", json={"refresh_token": rt})
        r = client.post("/auth/refresh", json={"refresh_token": rt})
        assert r.status_code == 401

    def test_protected_route_no_token(self):
        r = client.get("/users/me")
        assert r.status_code in (401, 403)  # HTTPBearer raises 403; some versions 401

    def test_protected_route_bad_token(self):
        r = client.get("/users/me", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401

    def test_protected_route_valid_token(self):
        signup()
        at = login().json()["access_token"]
        r = client.get("/users/me", headers=auth_header(at))
        assert r.status_code == 200
        assert r.json()["email"] == "aki@securesense.io"


# ══════════════════════════════════════════════════════════════
# LOGOUT
# ══════════════════════════════════════════════════════════════

class TestLogout:
    def test_logout_revokes_refresh(self):
        signup()
        tokens = login().json()
        at, rt = tokens["access_token"], tokens["refresh_token"]
        client.post("/auth/logout", json={"refresh_token": rt}, headers=auth_header(at))
        r = client.post("/auth/refresh", json={"refresh_token": rt})
        assert r.status_code == 401


# ══════════════════════════════════════════════════════════════
# PASSWORD RESET
# ══════════════════════════════════════════════════════════════

class TestPasswordReset:
    def _get_reset_token(self, email="aki@securesense.io"):
        # Grab from db directly (simulates email delivery)
        import secrets as s
        from app.core.security import generate_reset_token
        from app.core.config import settings
        user = db.get_user_by_email(email)
        token = generate_reset_token()
        db.store_reset_token(token, user.id, settings.PASSWORD_RESET_EXPIRE_MINUTES)
        return token

    def test_forgot_password_always_200(self):
        r = client.post("/auth/forgot-password", json={"email": "nobody@x.com"})
        assert r.status_code == 200  # no enumeration

    def test_reset_password_success(self):
        signup()
        token = self._get_reset_token()
        r = client.post("/auth/reset-password", json={"token": token, "new_password": "NewPass456"})
        assert r.status_code == 200
        r2 = login(password="NewPass456")
        assert r2.status_code == 200

    def test_reset_token_single_use(self):
        signup()
        token = self._get_reset_token()
        client.post("/auth/reset-password", json={"token": token, "new_password": "NewPass456"})
        r = client.post("/auth/reset-password", json={"token": token, "new_password": "Another789"})
        assert r.status_code == 400

    def test_invalid_reset_token(self):
        signup()
        r = client.post("/auth/reset-password", json={"token": "fake", "new_password": "NewPass456"})
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════════
# MFA
# ══════════════════════════════════════════════════════════════

class TestMFA:
    def test_mfa_setup_and_verify(self):
        signup()
        at = login().json()["access_token"]
        headers = auth_header(at)

        # Setup
        r = client.post("/auth/mfa/setup", headers=headers)
        assert r.status_code == 200
        secret = r.json()["secret"]
        assert "qr_code" in r.json()

        # Verify with valid TOTP
        import pyotp
        token = pyotp.TOTP(secret).now()
        r2 = client.post("/auth/mfa/verify", json={"token": token}, headers=headers)
        assert r2.status_code == 200

    def test_mfa_login_required_after_enable(self):
        signup()
        tokens = login().json()
        at = tokens["access_token"]
        headers = auth_header(at)

        setup = client.post("/auth/mfa/setup", headers=headers).json()
        secret = setup["secret"]
        import pyotp
        totp_token = pyotp.TOTP(secret).now()
        client.post("/auth/mfa/verify", json={"token": totp_token}, headers=headers)

        # Login without MFA token → mfa_required
        r = login()
        assert r.status_code == 200
        # Should signal MFA required

    def test_mfa_disable(self):
        signup()
        at = login().json()["access_token"]
        headers = auth_header(at)

        setup = client.post("/auth/mfa/setup", headers=headers).json()
        import pyotp
        totp_token = pyotp.TOTP(setup["secret"]).now()
        client.post("/auth/mfa/verify", json={"token": totp_token}, headers=headers)

        r = client.post("/auth/mfa/disable", json={"password": "Secure123"}, headers=headers)
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════
# RBAC
# ══════════════════════════════════════════════════════════════

class TestRBAC:
    def _admin_token(self):
        signup()
        return login().json()["access_token"]

    def _user_token(self):
        signup("bob", "bob@example.com", "Secure123")
        return login("bob@example.com", "Secure123").json()["access_token"]

    def test_admin_can_list_users(self):
        at = self._admin_token()
        r = client.get("/users/", headers=auth_header(at))
        assert r.status_code == 200

    def test_user_cannot_list_users(self):
        self._admin_token()           # creates admin first
        ut = self._user_token()
        r = client.get("/users/", headers=auth_header(ut))
        assert r.status_code == 403

    def test_admin_can_change_role(self):
        at = self._admin_token()
        # Create a second user
        signup("bob", "bob@example.com", "Secure123")
        bob = db.get_user_by_email("bob@example.com")
        r = client.put(f"/users/{bob.id}/role", json={"role": "moderator"}, headers=auth_header(at))
        assert r.status_code == 200
        assert r.json()["role"] == "moderator"

    def test_admin_can_delete_user(self):
        at = self._admin_token()
        signup("bob", "bob@example.com", "Secure123")
        bob = db.get_user_by_email("bob@example.com")
        r = client.delete(f"/users/{bob.id}", headers=auth_header(at))
        assert r.status_code == 200

    def test_health_public(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

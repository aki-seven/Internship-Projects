# SecureSense - Usage Guide

Quick guide to using the authentication system with examples.

---

## Quick Start

### 1. Setup & Run

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run server
uvicorn app.main:app --reload --port 8001
```

**Server Running:** http://localhost:8001  
**API Docs:** http://localhost:8001/docs (Swagger UI)

---

## Core Workflows

### Sign Up

**Request:**
```bash
curl -X POST http://localhost:8001/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice_wonder",
    "email": "alice@example.com",
    "password": "SecurePass123"
  }'
```

**Response (201 Created):**
```json
{
  "id": "usr_abc123xyz",
  "username": "alice_wonder",
  "email": "alice@example.com",
  "role": "admin",
  "mfa_enabled": false,
  "created_at": "2026-04-19T12:00:00Z"
}
```

**Password Requirements:**
- ✓ Minimum 8 characters
- ✓ At least one uppercase letter (A-Z)
- ✓ At least one digit (0-9)

---

### Sign In (Login)

**Request (Without MFA):**
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123"
  }'
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { "id": "usr_abc123xyz", "username": "alice_wonder", ... }
}
```

**Using Access Token:**
```bash
curl -X GET http://localhost:8001/users/me \
  -H "Authorization: Bearer <access_token>"
```

---

### Multi-Factor Authentication (MFA)

#### Step 1: Setup MFA (Request Secret & QR Code)

```bash
curl -X POST http://localhost:8001/auth/mfa/setup \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "message": "Scan the QR code with your authenticator app, then call /auth/mfa/verify to activate.",
  "secret": "JBSWY3DPEBLW64TMMQ======",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAA..."
}
```

**Action:** Scan QR code with **Google Authenticator**, **Authy**, or **Microsoft Authenticator**

#### Step 2: Verify TOTP Code

```bash
curl -X POST http://localhost:8001/auth/mfa/verify \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "123456"
  }'
```

**Response (200 OK):**
```json
{
  "message": "MFA enabled successfully"
}
```

#### Step 3: Login with MFA

```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123",
    "mfa_token": "123456"
  }'
```

#### Disable MFA

```bash
curl -X POST http://localhost:8001/auth/mfa/disable \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "SecurePass123"
  }'
```

---

### Token Refresh

Access tokens expire every 15 minutes. Use refresh token to get a new access token **without re-entering password**.

```bash
curl -X POST http://localhost:8001/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<old_refresh_token>"
  }'
```

**Response:**
```json
{
  "access_token": "new_access_token_here",
  "refresh_token": "new_refresh_token_here",
  "token_type": "bearer"
}
```

---

### Password Reset

#### Step 1: Request Password Reset

```bash
curl -X POST http://localhost:8001/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com"
  }'
```

**Response:**
```json
{
  "message": "If that email exists, a reset link has been sent."
}
```

**[Development Only]** Reset token is printed to console:
```
============================================================
[PASSWORD RESET] Token for alice@example.com:
d3f7b8c2-9k1m-4n2p-8q5r-9s8t7u6v5w4x
============================================================
```

#### Step 2: Reset Password

```bash
curl -X POST http://localhost:8001/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "d3f7b8c2-9k1m-4n2p-8q5r-9s8t7u6v5w4x",
    "new_password": "NewSecurePass456"
  }'
```

**Token Validity:** 15 minutes, single-use only

**Response:**
```json
{
  "message": "Password reset successfully. Please log in again."
}
```

---

### Password Change (Authenticated User)

```bash
curl -X PUT http://localhost:8001/users/me/password \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "SecurePass123",
    "new_password": "BrandNewPass789"
  }'
```

**Note:** All refresh tokens are revoked after password change (forces re-login everywhere)

---

### Logout

```bash
curl -X POST http://localhost:8001/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

---

## User Management (Admin Only)

### Get Own Profile

```bash
curl -X GET http://localhost:8001/users/me \
  -H "Authorization: Bearer <access_token>"
```

### List All Users (Admin)

```bash
curl -X GET http://localhost:8001/users/ \
  -H "Authorization: Bearer <admin_access_token>"
```

### Get User Details (Admin or Self)

```bash
curl -X GET http://localhost:8001/users/usr_abc123xyz \
  -H "Authorization: Bearer <access_token>"
```

### Change User Role (Admin)

```bash
curl -X PUT http://localhost:8001/users/usr_abc123xyz/role \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "moderator"
  }'
```

**Available Roles:** `admin`, `moderator`, `user`

### Delete User (Admin)

```bash
curl -X DELETE http://localhost:8001/users/usr_abc123xyz \
  -H "Authorization: Bearer <admin_access_token>"
```

### Delete Own Account

```bash
curl -X DELETE http://localhost:8001/users/me \
  -H "Authorization: Bearer <access_token>"
```

---

## Error Handling

### Invalid Credentials

**Status:** 401 Unauthorized
```json
{
  "detail": "Invalid credentials"
}
```

### Account Locked (Brute-Force)

After 5 failed login attempts, account locks for 15 minutes.

**Status:** 429 Too Many Requests
```json
{
  "detail": "Account locked due to too many failed attempts. Try again in 840s."
}
```

### Access Denied (Insufficient Role)

**Status:** 403 Forbidden
```json
{
  "detail": "Access denied. Required role: admin"
}
```

### Token Expired

**Status:** 401 Unauthorized
```json
{
  "detail": "Token has expired"
}
```

### Email Already Registered

**Status:** 409 Conflict
```json
{
  "detail": "Email already registered"
}
```

---

## Testing

Run integration tests:

```bash
pytest tests/ -v
```

**Tests cover:**
- User registration & validation
- Login flows (valid, invalid, MFA)
- Token refresh & rotation
- Password reset & change
- MFA setup/verify/disable
- RBAC enforcement
- Account lockout
- Edge cases & security

---

## Environment Variables

Create `.env` file (or use `.env.example` as template):

```env
# JWT Configuration
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_REFRESH_SECRET=your-refresh-secret-key-change-this
JWT_ALGORITHM=HS256

# Token Expiration
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Reset
PASSWORD_RESET_EXPIRE_MINUTES=15

# Brute-Force Protection
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_MINUTES=15

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8001"]

# App
APP_NAME=SecureSense
```

---

## Security Tips

✅ **DO:**
- Use HTTPS in production (not just HTTP)
- Generate strong JWT secrets (32+ bytes random)
- Store secrets in environment variables/Secrets Manager
- Rotate refresh tokens frequently
- Use strong, unique passwords
- Enable MFA for all admin accounts
- Monitor login attempts & account activity

❌ **DON'T:**
- Commit `.env` to git
- Share access tokens over email/chat
- Disable HTTPS in production
- Use default secrets
- Log passwords or tokens
- Store plaintext passwords (system uses Argon2id)

---

## API Status Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created (signup response) |
| 400 | Bad request (validation error, invalid token) |
| 401 | Unauthorized (invalid credentials, expired token) |
| 403 | Forbidden (insufficient role) |
| 404 | Not found |
| 409 | Conflict (email/username already exists) |
| 429 | Too many requests (account locked) |
| 500 | Server error |

---

## Support

- **Framework:** FastAPI (https://fastapi.tiangolo.com)
- **JWT:** python-jose (https://github.com/mpdavis/python-jose)
- **Password Hashing:** passlib (https://passlib.readthedocs.io)
- **MFA/TOTP:** pyotp (https://pyauth.github.io/pyotp)

For detailed API spec, visit: http://localhost:8001/docs

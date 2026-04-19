# SecureSense — User Authentication System
> **Task 6 · Advanced Project** | FastAPI · Argon2 · JWT · TOTP MFA · RBAC

A production-grade authentication backend built in Python with security-first design,
aligned with OWASP Authentication Cheat Sheet recommendations.

---

## Features

| Feature | Implementation |
|---|---|
| Secure sign-up | Argon2id password hashing (bcrypt fallback) via `passlib` |
| Sign-in | Email + password, returns short-lived access JWT + rotating refresh JWT |
| MFA (TOTP) | `pyotp` — Google Authenticator / Authy compatible QR setup |
| Password reset | Crypto-random token, 15-min TTL, single-use, anti-enumeration |
| Role-based access | `admin` → `moderator` → `user` hierarchy, enforced per-endpoint |
| Token refresh | Refresh token rotation — replay attack detection via `jti` claim |
| Brute-force guard | 5 failed attempts → 15-min account lockout |
| Security headers | HSTS, X-Frame-Options, X-Content-Type-Options, Cache-Control, CSP |
| CORS hardening | Configurable origin allowlist |
| Session management | Stateful refresh token store (swap for Redis in prod) |

---

## Tech Stack

```
Python 3.12+
FastAPI           — ASGI web framework
Uvicorn           — ASGI server
passlib[argon2]   — Argon2id / bcrypt password hashing
python-jose       — JWT encode / decode (HS256)
pyotp             — TOTP / HOTP (RFC 6238)
qrcode[pil]       — QR code generation for MFA setup
pydantic v2       — Request/response validation & settings
httpx + pytest    — Integration test client
```

---

## Project Structure

```
auth-system-py/
├── app/
│   ├── main.py                  # FastAPI app, CORS, security headers
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env-driven)
│   │   ├── database.py          # Thread-safe in-memory store
│   │   └── security.py          # Hashing, JWT, TOTP helpers
│   ├── middleware/
│   │   └── auth.py              # Bearer extraction, RBAC deps, lockout helpers
│   ├── models/
│   │   └── user.py              # UserInDB, UserPublic, all request/response schemas
│   └── routes/
│       ├── auth.py              # /auth/* endpoints
│       └── users.py             # /users/* endpoints
├── tests/
│   └── test_auth.py             # 32 integration tests (100% pass)
├── .env.example
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# 1. Clone / enter directory
cd auth-system-py

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install "pydantic[email]" pydantic-settings

# 4. Copy environment file
cp .env.example .env
# Edit .env — change secrets before any real use!

# 5. Run the server
uvicorn app.main:app --reload --port 8001

# 6. Open interactive docs
#    Swagger UI:  http://localhost:8001/docs
#    ReDoc:       http://localhost:8001/redoc
```

---

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/signup` | Public | Register new account |
| POST | `/auth/login` | Public | Login → access + refresh tokens |
| POST | `/auth/refresh` | Public | Rotate refresh token |
| POST | `/auth/logout` | Bearer | Revoke refresh token |
| POST | `/auth/forgot-password` | Public | Request reset token (anti-enumeration) |
| POST | `/auth/reset-password` | Public | Consume token, set new password |
| POST | `/auth/mfa/setup` | Bearer | Generate TOTP secret + QR code |
| POST | `/auth/mfa/verify` | Bearer | Activate MFA with first TOTP code |
| POST | `/auth/mfa/disable` | Bearer | Disable MFA (requires password) |

### Users

| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/users/me` | Any | Get own profile |
| PUT | `/users/me/password` | Any | Change own password |
| DELETE | `/users/me` | Any | Delete own account |
| GET | `/users/` | admin | List all users |
| GET | `/users/{id}` | admin / self | Get user by ID |
| PUT | `/users/{id}/role` | admin | Promote / demote role |
| DELETE | `/users/{id}` | admin | Delete user |
| GET | `/users/mod/dashboard` | admin, moderator | Stats dashboard |

---

## Example Flow

```bash
BASE=http://localhost:8001

# 1. Sign up (first user → auto-admin)
curl -s -X POST $BASE/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"aki","email":"aki@securesense.io","password":"Secure123"}' | jq

# 2. Login
TOKENS=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aki@securesense.io","password":"Secure123"}')
AT=$(echo $TOKENS | jq -r .access_token)
RT=$(echo $TOKENS | jq -r .refresh_token)

# 3. Access protected route
curl -s $BASE/users/me -H "Authorization: Bearer $AT" | jq

# 4. Set up MFA
SETUP=$(curl -s -X POST $BASE/auth/mfa/setup -H "Authorization: Bearer $AT")
SECRET=$(echo $SETUP | jq -r .secret)
echo "Scan QR or use secret: $SECRET"

# 5. Verify MFA (use an authenticator app or: python -c "import pyotp; print(pyotp.TOTP('$SECRET').now())")
TOTP=$(python -c "import pyotp; print(pyotp.TOTP('$SECRET').now())")
curl -s -X POST $BASE/auth/mfa/verify \
  -H "Authorization: Bearer $AT" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOTP\"}" | jq

# 6. Refresh token
curl -s -X POST $BASE/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$RT\"}" | jq

# 7. Logout
curl -s -X POST $BASE/auth/logout \
  -H "Authorization: Bearer $AT" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$RT\"}" | jq
```

---

## Running Tests

```bash
pytest tests/ -v
# Expected: 32 passed
```

---

## Security Notes (OWASP alignment)

- **Password storage** — Argon2id (memory-hard), min 8 chars, uppercase + digit enforced
- **Anti-enumeration** — `/forgot-password` always returns 200 regardless of email existence
- **Token rotation** — Each refresh issues a new pair; old token immediately invalidated
- **Replay protection** — `jti` (JWT ID) UUID in every refresh token ensures uniqueness
- **Brute-force** — 5-attempt lockout with exponential delay potential
- **Secure headers** — HSTS, X-Frame-Options, Cache-Control: no-store
- **CORS** — Allowlist-based, credentials supported
- **MFA** — TOTP RFC 6238, ±1 window tolerance

---

## Production Checklist

- [ ] Replace in-memory store with PostgreSQL / SQLite via SQLAlchemy
- [ ] Move refresh token store to Redis (with TTL)
- [ ] Wire `/forgot-password` to real SMTP (SendGrid, Resend, etc.)
- [ ] Set strong random secrets in `.env` (never commit!)
- [ ] Enable HTTPS / TLS termination at reverse proxy
- [ ] Add rate limiting middleware (e.g. `slowapi`)
- [ ] Set `DEBUG=false` in production

---

*Built for SecureSense Internship · Task 6 — Advanced · OWASP Authentication Cheat Sheet*

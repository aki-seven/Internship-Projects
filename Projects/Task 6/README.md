# Credit Card Encryption & Tokenization Service

Secure FastAPI service for encrypting PANs, generating non-predictable tokens, and detokenizing with authorization.

## Features

- PAN validation with length and Luhn check
- AES-256 authenticated encryption for PAN storage
- Conceptual numeric-preserving FPE simulation available in the encryption module
- Token generation using UUID4-based tokens
- SQLite-backed token-to-encrypted-PAN mapping
- Masked PAN responses
- Basic rate limiting middleware
- Authentication guard for `/detokenize`
- Docker support and unit tests

## File structure

- `main.py` - FastAPI application entrypoint
- `config/` - environment settings
- `routes/` - API route definitions
- `services/` - encryption and tokenization logic
- `storage/` - SQLite persistence layer
- `utils/` - PAN masking, validation, rate limiting
- `tests/` - unit tests

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create environment variables or an `.env` file with:

```env
ENCRYPTION_KEY=your-64-char-hex-or-base64-32-byte-key
DETOKENIZE_API_KEY=supersecretkey
SQLITE_DB_PATH=data/token_store.db
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=60
```

You can generate a secure AES-256 key with Python:

```python
import secrets
print(secrets.token_hex(32))
```

3. Run the service:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Example requests

### Tokenize a PAN

```bash
curl -X POST http://127.0.0.1:8000/tokenize \
  -H "Content-Type: application/json" \
  -d '{"pan": "4242424242424242"}'
```

Response:

```json
{
  "token": "...",
  "masked_pan": "**** **** **** 4242"
}
```

### Detokenize a token

```bash
curl -X POST http://127.0.0.1:8000/detokenize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer supersecretkey" \
  -d '{"token": "yourtoken"}'
```

Response:

```json
{
  "pan": "4242424242424242"
}
```

### Health check

```bash
curl http://127.0.0.1:8000/health
```

## Docker

Build and run:

```bash
docker build -t pan-tokenization-service .
docker run --rm -p 8000:8000 \
  -e ENCRYPTION_KEY=your-64-char-hex-or-base64-32-byte-key \
  -e DETOKENIZE_API_KEY=supersecretkey \
  pan-tokenization-service
```

## Tests

```bash
pytest
```

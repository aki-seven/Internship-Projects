# Credit Card Tokenization Service

A secure backend service for encrypting and tokenizing credit card PANs using AES-256 encryption.

## Features

- Encrypt PANs with AES-256-GCM
- Tokenize PANs for secure storage
- Mask PANs in responses
- Input validation (length, numeric, Luhn check)
- No plaintext PAN storage beyond processing
- Environment-based encryption keys
- Basic PCI-DSS compliance (minimal exposure, no full storage)

## File Structure

```
.
├── app.py              # FastAPI application with endpoints
├── encryption.py       # AES-256 encryption/decryption logic
├── tokenization.py     # Token generation and SQLite storage
├── utils.py            # Validation, masking, and utility functions
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (encryption key)
├── tokens.db           # SQLite database for tokens (created automatically)
└── README.md           # This file
```

## Installation

1. Install Python 3.8+ if not already installed.

2. Clone or download the project files.

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Edit `.env` file with a secure 32-byte hex key for encryption and an API key for authorization.
   - To generate a new encryption key: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Set API_KEY to a secure string for decrypt endpoint authorization.

## Running the Service

1. Run the FastAPI server:
   ```
   uvicorn app:app --reload
   ```

2. The service will be available at `http://127.0.0.1:8000`

3. API documentation at `http://127.0.0.1:8000/docs`

## API Endpoints

### POST /encrypt
Encrypt and tokenize a PAN.

**Request:**
```json
{
  "pan": "4111111111111111"
}
```

**Response:**
```json
{
  "token": "550e8400-e29b-41d4-a716-446655440000",
  "masked_pan": "**** **** **** 1111"
}
```

### POST /decrypt
Decrypt a PAN using its token. Requires API key authorization.

**Request Headers:**
```
X-API-Key: your_api_key_here
```

**Request Body:**
```json
{
  "token": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "pan": "4111111111111111"
}
```

### GET /health
Health check.

**Response:**
```json
{
  "status": "ok"
}
```

## Security Notes

- Encryption uses AES-256-GCM for authenticated encryption.
- Keys are loaded from environment variables.
- PANs are never logged in plaintext.
- Raw PANs are not stored; only encrypted versions with tokens.
- Input validation prevents invalid PANs.
- SQLite database stores only tokens and encrypted PANs.

## Testing

You can test with curl:

```bash
# Encrypt
curl -X POST "http://127.0.0.1:8000/encrypt" -H "Content-Type: application/json" -d '{"pan": "4111111111111111"}'

# Decrypt (use the token from encrypt response, and include API key)
curl -X POST "http://127.0.0.1:8000/decrypt" -H "Content-Type: application/json" -H "X-API-Key: your_api_key_here" -d '{"token": "your-token-here"}'
```

## Notes

- This is a simple implementation for demonstration.
- For production, add authentication, rate limiting, and more robust error handling.
- Ensure the `.env` file is not committed to version control.
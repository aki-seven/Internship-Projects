# Credit Card Tokenization Service - Usage Guide

## Main Uses

### 1. **Encrypt (Store Credit Cards Securely)**
**Purpose:** Convert raw credit card numbers into encrypted, tokenized form for secure storage.

**When to use:**
- User enters their credit card on checkout page
- Need to store card for future transactions
- PCI-DSS compliance required
- Card data must not be stored in plaintext

**Request Example:**
```json
POST /encrypt
Header: X-API-Key: secure_api_key_here
{
  "pan": "4532015112830366"
}
```

**Response:**
```json
{
  "token": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "masked_pan": "**** **** **** 0366"
}
```

**What happens:**
- Raw card number (PAN) is encrypted with AES-256-GCM
- Encrypted data stored in database with unique token
- Only token and masked number returned to client
- Raw card number discarded immediately (never persisted)

---

### 2. **Decrypt (Retrieve Credit Card)**
**Purpose:** Retrieve the original credit card number using a token (requires API key authorization).

**When to use:**
- Process payment using stored token
- Refund a previous transaction
- Only for authorized backend operations
- Never expose decrypt endpoint to frontend

**Request Example:**
```json
POST /decrypt
Header: X-API-Key: secure_api_key_here
{
  "token": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
}
```

**Response:**
```json
{
  "pan": "4532015112830366"
}
```

**Security:**
- Requires API key authentication
- Logged with token ID only (not PAN)
- Should only be called from secure backend servers
- Never expose to frontend or untrusted clients

---

## Other Main Uses

### 3. **Masking (Display Card Info Safely)**
**Purpose:** Show users their card without exposing full number.

**Use Cases:**
- Display in user dashboard: "Card ending in 3366"
- Confirmation screens: "Charged to **** **** **** 3366"
- Receipt generation
- Payment history

**Example Output:**
- Input: `4532015112830366`
- Output: `**** **** **** 0366`

---

### 4. **Validation (Check Card Format)**
**Purpose:** Validate PAN before processing.

**Checks Performed:**
- ✓ Must be 13-19 digits (Visa, Mastercard, Amex standards)
- ✓ Must be numeric only
- ✓ Must pass Luhn algorithm (checksum validation)

**Use Cases:**
- Reject invalid card entries immediately
- Reduce bad data in database
- Prevent processing errors

---

### 5. **Health Check (Monitor Service)**
**Purpose:** Verify service is running and responsive.

**Request:**
```
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

**Use Cases:**
- Monitoring and alerting
- Load balancer health checks
- CI/CD pipeline verification
- Uptime monitoring

---

## Workflow Example: E-Commerce Checkout

```
1. Customer enters card: 4532015112830366
2. Frontend → /encrypt endpoint
3. Backend returns token: a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d
4. Token stored in orders database (NOT the card number)
5. Masked card displayed: **** **** **** 0366
6. For payment processing:
   - Backend calls /decrypt with token (using API key)
   - Gets original PAN
   - Sends to payment processor (Stripe, Square, etc.)
   - Discards PAN immediately after
```

---

## Security Best Practices

| Best Practice | Why |
|--------------|-----|
| **Never store tokens in frontend** | Tokens = access to cards if exposed |
| **Always use API key for decrypt** | Only authorized servers can retrieve card data |
| **Use HTTPS only** | Encrypt data in transit |
| **Rotate encryption keys regularly** | Reduces exposure if key is compromised |
| **Never log raw PANs** | Service automatically masks sensitive data |
| **Limit API key access** | Use separate keys for different services |

---

## Summary

| Function | Main Use | Security Level |
|----------|----------|-----------------|
| **Encrypt** | Store card securely with token | High (requires API key) |
| **Decrypt** | Retrieve card for payments | Critical (requires API key auth) |
| **Mask** | Display safe card reference | Low (shows only last 4 digits) |
| **Validate** | Check card format | Low (public-facing) |
| **Health** | Monitor service | Low (public check endpoint) |

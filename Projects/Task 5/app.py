from dotenv import load_dotenv
import logging
import os

# Load environment variables FIRST, before any imports that use them
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel

from encryption import encrypt_pan, decrypt_pan
from tokenization import store_token, get_encrypted_pan
from utils import validate_pan, mask_pan, sanitize_log

# Configure logging to not log sensitive data
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Credit Card Tokenization Service", version="1.0.0")

@app.on_event("startup")
async def startup_message():
    """Print server access information on startup."""
    print("\n" + "="*60)
    print("✓ Credit Card Tokenization Service is running!")
    print("="*60)
    print("📍 Access the server at: http://127.0.0.1:8000")
    print("📚 API Documentation: http://127.0.0.1:8000/docs")
    print("🔍 ReDoc: http://127.0.0.1:8000/redoc")
    print("="*60 + "\n")

class EncryptRequest(BaseModel):
    pan: str

class DecryptRequest(BaseModel):
    token: str

def verify_api_key(x_api_key: str = Header(...)):
    """
    Verify API key for restricted endpoints.
    """
    expected_key = os.getenv('API_KEY')
    if not expected_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/")
async def root():
    """
    Welcome endpoint.
    """
    return {
        "message": "Credit Card Tokenization Service",
        "version": "1.0.0",
        "docs": "http://127.0.0.1:8000/docs",
        "endpoints": {
            "health": "/health",
            "encrypt": "/encrypt",
            "decrypt": "/decrypt"
        }
    }

@app.post("/encrypt")
async def encrypt_endpoint(request: EncryptRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    """
    Encrypt and tokenize the PAN.
    Input: {"pan": "1234567890123456"}
    Output: {"token": "uuid", "masked_pan": "**** **** **** 3456"}
    """
    pan = request.pan
    if not validate_pan(pan):
        raise HTTPException(status_code=400, detail="Invalid PAN")
    
    # Encrypt
    try:
        encrypted = encrypt_pan(pan)
    except Exception:
        logger.error("Encryption failed")
        raise HTTPException(status_code=500, detail="Encryption failed")
    
    # Store and get token
    token = store_token(encrypted)
    
    # Mask for response
    masked = mask_pan(pan)
    
    # Log sanitized
    logger.info(f"Encrypted PAN, token: {token}")
    
    return {"token": token, "masked_pan": masked}

@app.post("/decrypt")
async def decrypt_endpoint(request: DecryptRequest, x_api_key: str = Header(...)):
    """
    Decrypt the PAN using token.
    Requires API key authorization for security.
    Input: {"token": "uuid"}
    Output: {"pan": "1234567890123456"}
    """
    verify_api_key(x_api_key)
    
    token = request.token
    encrypted = get_encrypted_pan(token)
    if not encrypted:
        raise HTTPException(status_code=404, detail="Token not found")
    
    try:
        pan = decrypt_pan(encrypted)
        # Log sanitized
        logger.info(f"Decrypted token: {token}")
        return {"pan": pan}
    except Exception as e:
        logger.error(f"Decryption failed for token: {token}")
        raise HTTPException(status_code=500, detail="Decryption failed")

@app.get("/health")
async def health():
    """
    Health check.
    """
    return {"status": "ok"}

# Middleware to sanitize logs
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    return response
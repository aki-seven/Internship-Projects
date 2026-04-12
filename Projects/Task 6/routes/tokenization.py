import logging
from fastapi import APIRouter, Depends, Header, HTTPException, status
from config.settings import settings
from services.dependencies import get_encryption_service, get_tokenization_service
from services.encryption import EncryptionService
from services.tokenization import TokenizationService
from models.schemas import (
    DetokenizeRequest,
    DetokenizeResponse,
    TokenizeRequest,
    TokenizeResponse,
)
from utils.security import mask_pan, validate_pan

logger = logging.getLogger(__name__)
router = APIRouter()


def get_api_key(authorization: str | None = Header(default=None), x_api_key: str | None = Header(default=None)) -> str:
    api_key = None
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization.split("Bearer ", 1)[1].strip()
    elif x_api_key:
        api_key = x_api_key.strip()

    if api_key != settings.detokenize_api_key:
        logger.warning("Unauthorized detokenization attempt")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return api_key


@router.post("/tokenize", response_model=TokenizeResponse, tags=["tokenization"])
async def tokenize(
    request: TokenizeRequest,
    encryptor: EncryptionService = Depends(get_encryption_service),
    token_service: TokenizationService = Depends(get_tokenization_service),
):
    normalized_pan = validate_pan(request.pan)
    if not normalized_pan:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid PAN format")

    encrypted_pan = encryptor.encrypt_pan(normalized_pan)
    token = token_service.tokenize(encrypted_pan)
    masked = mask_pan(normalized_pan)
    logger.info("PAN tokenized, token=%s", token)
    return TokenizeResponse(token=token, masked_pan=masked)


@router.post("/detokenize", response_model=DetokenizeResponse, tags=["tokenization"])
async def detokenize(
    request: DetokenizeRequest,
    _: str = Depends(get_api_key),
    encryptor: EncryptionService = Depends(get_encryption_service),
    token_service: TokenizationService = Depends(get_tokenization_service),
):
    encrypted_pan = token_service.detokenize(request.token)
    if not encrypted_pan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")

    try:
        pan = encryptor.decrypt_pan(encrypted_pan)
    except Exception as exc:
        logger.error("Failed to decrypt PAN for token=%s: %s", request.token, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to decrypt PAN")

    logger.info("Token successfully detokenized, token=%s", request.token)
    return DetokenizeResponse(pan=pan)

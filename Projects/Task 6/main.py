import logging
from fastapi import FastAPI
from config.settings import settings
from routes.health import router as health_router
from routes.tokenization import router as token_router
from utils.rate_limiter import RateLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("creditcard-service")

app = FastAPI(
    title="Credit Card Encryption & Tokenization Service",
    description="Secure PAN encryption, tokenization, and restricted detokenization.",
    version="1.0.0",
)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.include_router(health_router)
app.include_router(token_router)


@app.on_event("startup")
def startup_event():
    logger.info("Service startup complete")

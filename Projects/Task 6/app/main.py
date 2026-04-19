# app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🦊 %s starting up…", settings.APP_NAME)
    print("\n" + "="*70)
    print(f"  🦊 {settings.APP_NAME} is running!")
    print("="*70)
    print(f"  📍 Server:       http://localhost:8001")
    print(f"  📚 Swagger UI:   http://localhost:8001/docs")
    print(f"  📖 ReDoc:        http://localhost:8001/redoc")
    print(f"  🎉 Health:       http://localhost:8001/health")
    print("="*70 + "\n")
    yield
    logger.info("🦊 %s shutting down.", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Secure User Authentication System — "
        "Argon2 hashing · JWT access/refresh · TOTP MFA · RBAC · "
        "Password reset · Brute-force protection · CORS/CSRF hardening"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
    expose_headers=["X-Request-ID"],
)

# ── Security headers middleware ────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"]             = "no-store"
    return response


# ── Global exception handler ───────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


# ── Routers ────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)


# ── Health check ───────────────────────────────────────────────
@app.get("/health", tags=["Meta"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/", tags=["Meta"])
async def root():
    return {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }

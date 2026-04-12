from fastapi import APIRouter
from models.schemas import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", details="Service is running")

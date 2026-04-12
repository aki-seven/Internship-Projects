from pydantic import BaseModel, Field


class TokenizeRequest(BaseModel):
    pan: str = Field(..., description="Primary Account Number in numeric form")


class TokenizeResponse(BaseModel):
    token: str
    masked_pan: str


class DetokenizeRequest(BaseModel):
    token: str = Field(..., description="Non-predictable token returned from /tokenize")


class DetokenizeResponse(BaseModel):
    pan: str


class HealthResponse(BaseModel):
    status: str
    details: str

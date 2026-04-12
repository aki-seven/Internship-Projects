import time
from collections import deque
from typing import Deque, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import HTTPException


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter based on client IP.

    This helps reject excessive requests before they reach the tokenization logic.
    """

    def __init__(self, app, max_requests: int = 20, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, Deque[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        if request.url.path.startswith("/health"):
            return await call_next(request)

        now = time.time()
        history = self.clients.setdefault(client_ip, deque())
        while history and history[0] + self.window_seconds <= now:
            history.popleft()

        if len(history) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests, slow down.",
            )

        history.append(now)
        return await call_next(request)

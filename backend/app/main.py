"""FastAPI application entrypoint.

Wiring: CORS → rate limiter → exception handlers → routers.
"""

import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.auth import AuthenticatedUser, require_user
from app.routes import health, trips
from app.settings import get_settings

settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)

app = FastAPI(
    title="PromptWars Travel Planning API",
    version="0.1.0",
    description="Plan trips dynamically with preferences, constraints, and real-time updates.",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    safe_errors = [
        {"type": e.get("type"), "loc": list(e.get("loc", [])), "msg": e.get("msg")}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request", "errors": safe_errors},
    )


app.include_router(health.router)
app.include_router(trips.router)


@app.get("/me", tags=["auth"])
async def me(user: AuthenticatedUser = Depends(require_user)) -> dict[str, str | None]:
    """Returns the authenticated user — used by the frontend to confirm login."""
    return {"uid": user.uid, "email": user.email, "name": user.name}

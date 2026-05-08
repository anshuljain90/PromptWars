"""Firebase ID token verification dependency for protected routes."""

import logging
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials, initialize_app
from firebase_admin.exceptions import FirebaseError

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)
_bearer_scheme = HTTPBearer(auto_error=False)
_firebase_initialized = False


@dataclass(frozen=True)
class AuthenticatedUser:
    uid: str
    email: str | None
    name: str | None


def _ensure_firebase_initialized(settings: Settings) -> None:
    """Initialize firebase-admin once per process."""
    global _firebase_initialized
    if _firebase_initialized:
        return

    if settings.google_application_credentials:
        cred = credentials.Certificate(settings.google_application_credentials)
        initialize_app(cred, {"projectId": settings.firebase_project_id})
    else:
        initialize_app(options={"projectId": settings.firebase_project_id})
    _firebase_initialized = True


async def require_user(
    request: Request,
    credentials_: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    """Verify the Firebase ID token from the Authorization header.

    Returns the authenticated user or raises 401.
    """
    if credentials_ is None or credentials_.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _ensure_firebase_initialized(settings)

    try:
        decoded = firebase_auth.verify_id_token(credentials_.credentials, check_revoked=False)
    except FirebaseError as exc:
        logger.warning("Firebase token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = AuthenticatedUser(
        uid=decoded["uid"],
        email=decoded.get("email"),
        name=decoded.get("name"),
    )
    request.state.user = user
    return user

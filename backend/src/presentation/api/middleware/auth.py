"""Authentication middleware for Google SSO and JWT."""

import os
import sys
from dataclasses import dataclass
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jwt.exceptions import ExpiredSignatureError

from src.infrastructure.auth.jwt import verify_access_token

# Load .env file explicitly
load_dotenv()

# Security scheme
security = HTTPBearer(auto_error=False)

# Google OAuth Configuration
# Note: Terraform sets GOOGLE_OAUTH_CLIENT_ID/SECRET, support both for compatibility
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET") or os.getenv(
    "GOOGLE_CLIENT_SECRET", ""
)

# Development mode: disable authentication (ONLY for local development)
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false").lower() == "true"
APP_ENV = os.getenv("APP_ENV", "development")

# Debug logging
print(f"[AUTH] DISABLE_AUTH={DISABLE_AUTH}, APP_ENV={APP_ENV}", file=sys.stderr)


@dataclass
class CurrentUser:
    """Current authenticated user."""

    id: str
    email: str
    name: str | None
    picture_url: str | None
    google_id: str


# Create a default development user when auth is disabled
DEV_USER = CurrentUser(
    id="00000000-0000-0000-0000-000000000001",
    email="dev@localhost",
    name="Development User",
    picture_url=None,
    google_id="dev-google-id",
)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser | None:
    """Get current user from JWT token (optional - returns None if not authenticated)."""
    # Development mode: skip authentication
    if DISABLE_AUTH and APP_ENV != "production":
        return DEV_USER

    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = verify_access_token(token)
        if payload is None:
            return None

        return CurrentUser(
            id=payload.sub,
            email=payload.email,
            name=payload.name,
            picture_url=payload.picture_url,
            google_id=payload.google_id,
        )
    except ExpiredSignatureError:
        return None
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    """Get current user from JWT token (required - raises 401 if not authenticated)."""
    # Development mode: skip authentication
    if DISABLE_AUTH and APP_ENV != "production":
        return DEV_USER

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = verify_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return CurrentUser(
            id=payload.sub,
            email=payload.email,
            name=payload.name,
            picture_url=payload.picture_url,
            google_id=payload.google_id,
        )
    except ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def verify_google_id_token(token: str) -> dict:
    """Verify Google ID token and return user info.

    Args:
        token: Google ID token from OAuth flow

    Returns:
        Dictionary with user info from Google

    Raises:
        HTTPException: If token is invalid
    """
    try:
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )

        # Verify issuer
        if id_info["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Invalid issuer")

        return {
            "google_id": id_info["sub"],
            "email": id_info["email"],
            "name": id_info.get("name"),
            "picture_url": id_info.get("picture"),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate Google credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# Type alias for dependency injection
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
CurrentUserOptionalDep = Annotated[CurrentUser | None, Depends(get_current_user_optional)]

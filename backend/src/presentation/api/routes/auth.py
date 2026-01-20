"""Authentication routes for Google SSO."""

import os
import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from src.infrastructure.auth.domain_validator import (
    DomainValidationError,
    get_allowed_domains,
    is_domain_restriction_enabled,
    validate_email_domain,
)
from src.infrastructure.auth.jwt import create_access_token
from src.presentation.api.middleware.auth import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    CurrentUserDep,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# OAuth configuration
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_SCOPES = ["openid", "profile", "email"]

# Get base URL from environment
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


class UserResponse(BaseModel):
    """User information response."""

    id: str
    email: str
    name: str | None
    picture_url: str | None
    google_id: str


class TokenResponse(BaseModel):
    """Token response for login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.get("/google")
async def google_auth_start(
    redirect_uri: str | None = Query(None, description="URL to redirect after successful login"),
) -> RedirectResponse:
    """Initiate Google OAuth 2.0 login flow.

    Redirects to Google's authorization page.
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured",
        )

    callback_url = f"{BASE_URL}/api/v1/auth/google/callback"

    # Build state with redirect URI
    state = redirect_uri or FRONTEND_URL

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "state": state,
        "prompt": "consent",
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_auth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query("", description="State parameter with redirect URI"),
) -> RedirectResponse:
    """Handle Google OAuth callback.

    Exchanges authorization code for tokens and creates JWT.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured",
        )

    callback_url = f"{BASE_URL}/api/v1/auth/google/callback"

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": callback_url,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange authorization code",
            )

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        tokens.get("id_token")

        # Get user info from Google
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user info from Google",
            )

        user_info = userinfo_response.json()

    # Validate email domain
    email = user_info.get("email", "")
    try:
        validate_email_domain(email)
    except DomainValidationError:
        # Redirect to frontend with error
        redirect_url = state or FRONTEND_URL
        separator = "&" if "?" in redirect_url else "?"
        error_msg = f"domain_not_allowed:{email.split('@')[1] if '@' in email else 'unknown'}"
        return RedirectResponse(url=f"{redirect_url}{separator}error={error_msg}")

    # Create or update user in database (simplified - should use repository)
    user_id = str(uuid.uuid4())  # In production, lookup or create user in DB

    # Create JWT token
    jwt_token = create_access_token(
        user_id=user_id,
        email=user_info["email"],
        google_id=user_info["id"],
        name=user_info.get("name"),
        picture_url=user_info.get("picture"),
    )

    # Redirect to frontend with token
    redirect_url = state or FRONTEND_URL
    separator = "&" if "?" in redirect_url else "?"
    return RedirectResponse(url=f"{redirect_url}{separator}token={jwt_token}")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUserDep) -> UserResponse:
    """Get current authenticated user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture_url=current_user.picture_url,
        google_id=current_user.google_id,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(_current_user: CurrentUserDep, response: Response) -> None:
    """Logout current user.

    Note: JWT tokens are stateless, so we can't truly invalidate them.
    Client should discard the token. For enhanced security, implement
    a token blacklist in Redis.
    """
    # Clear any cookies if used
    response.delete_cookie("access_token")
    return None


class DomainRestrictionInfo(BaseModel):
    """Domain restriction configuration info."""

    enabled: bool
    allowed_domains: list[str]


@router.get("/domain-restriction", response_model=DomainRestrictionInfo)
async def get_domain_restriction_info() -> DomainRestrictionInfo:
    """Get domain restriction configuration.

    Returns information about which email domains are allowed for login.
    This is a public endpoint for frontend to show appropriate UI.
    """
    return DomainRestrictionInfo(
        enabled=is_domain_restriction_enabled(),
        allowed_domains=get_allowed_domains(),
    )

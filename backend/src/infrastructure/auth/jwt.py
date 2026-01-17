"""JWT token generation and validation utilities."""

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours


@dataclass
class JWTPayload:
    """JWT payload structure."""

    sub: str  # Subject (user ID)
    email: str
    name: str | None
    picture_url: str | None
    google_id: str
    exp: datetime
    iat: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary."""
        return {
            "sub": self.sub,
            "email": self.email,
            "name": self.name,
            "picture_url": self.picture_url,
            "google_id": self.google_id,
            "exp": self.exp,
            "iat": self.iat,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JWTPayload":
        """Create payload from dictionary."""
        return cls(
            sub=data["sub"],
            email=data["email"],
            name=data.get("name"),
            picture_url=data.get("picture_url"),
            google_id=data["google_id"],
            exp=data["exp"] if isinstance(data["exp"], datetime) else datetime.fromtimestamp(data["exp"], tz=UTC),
            iat=data["iat"] if isinstance(data["iat"], datetime) else datetime.fromtimestamp(data["iat"], tz=UTC),
        )


def create_access_token(
    user_id: str,
    email: str,
    google_id: str,
    name: str | None = None,
    picture_url: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID (UUID as string)
        email: User email
        google_id: Google OAuth ID
        name: User display name
        picture_url: User profile picture URL
        expires_delta: Token expiration time delta

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = JWTPayload(
        sub=user_id,
        email=email,
        name=name,
        picture_url=picture_url,
        google_id=google_id,
        exp=expire,
        iat=now,
    )

    encoded_jwt = jwt.encode(
        payload.to_dict(),
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return encoded_jwt


def verify_access_token(token: str) -> JWTPayload | None:
    """Verify and decode a JWT access token.

    Args:
        token: JWT token string

    Returns:
        JWTPayload if valid, None if invalid

    Raises:
        ExpiredSignatureError: If token has expired
        InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        return JWTPayload.from_dict(payload)
    except ExpiredSignatureError:
        raise
    except InvalidTokenError:
        return None

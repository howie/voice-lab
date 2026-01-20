"""Authentication infrastructure."""

from src.infrastructure.auth.domain_validator import (
    DomainValidationError,
    get_allowed_domains,
    is_domain_restriction_enabled,
    validate_email_domain,
)
from src.infrastructure.auth.jwt import (
    JWTPayload,
    create_access_token,
    verify_access_token,
)

__all__ = [
    "create_access_token",
    "verify_access_token",
    "JWTPayload",
    "DomainValidationError",
    "validate_email_domain",
    "get_allowed_domains",
    "is_domain_restriction_enabled",
]

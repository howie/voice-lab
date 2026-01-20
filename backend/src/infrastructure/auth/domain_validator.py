"""Domain validation for OAuth login restriction."""

from src.config import get_settings


class DomainValidationError(Exception):
    """Exception raised when email domain is not allowed."""

    def __init__(self, email: str, allowed_domains: list[str]):
        self.email = email
        self.allowed_domains = allowed_domains
        domain = email.split("@")[1] if "@" in email else "unknown"
        super().__init__(
            f"Email domain '{domain}' is not allowed. Allowed domains: {', '.join(allowed_domains)}"
        )


def validate_email_domain(email: str) -> bool:
    """Validate that the email domain is in the allowed list.

    Args:
        email: User's email address

    Returns:
        True if domain is allowed, raises DomainValidationError otherwise

    Raises:
        DomainValidationError: If the email domain is not in the allowed list
    """
    settings = get_settings()

    # If no domains are configured, allow all
    if not settings.allowed_domains:
        return True

    # Extract domain from email
    if "@" not in email:
        raise DomainValidationError(email, settings.allowed_domains)

    domain = email.split("@")[1].lower()

    # Check if domain is in the allowed list
    if domain not in settings.allowed_domains:
        raise DomainValidationError(email, settings.allowed_domains)

    return True


def get_allowed_domains() -> list[str]:
    """Get the list of allowed email domains.

    Returns:
        List of allowed domains, empty list means all domains allowed
    """
    settings = get_settings()
    return settings.allowed_domains


def is_domain_restriction_enabled() -> bool:
    """Check if domain restriction is enabled.

    Returns:
        True if domain restriction is enabled (at least one domain configured)
    """
    settings = get_settings()
    return len(settings.allowed_domains) > 0

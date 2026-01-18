"""API key masking utilities."""


def mask_api_key(key: str, visible_chars: int = 4) -> str:
    """Mask an API key, showing only the last N characters.

    Args:
        key: The API key to mask
        visible_chars: Number of characters to show at the end (default: 4)

    Returns:
        Masked API key (e.g., "****abc1")

    Examples:
        >>> mask_api_key("sk-1234567890abcdef")
        '****cdef'
        >>> mask_api_key("abc")
        '****'
        >>> mask_api_key("")
        '****'
    """
    if not key or len(key) <= visible_chars:
        return "****"
    return f"****{key[-visible_chars:]}"


def is_key_masked(key: str) -> bool:
    """Check if a key appears to be masked.

    Args:
        key: The key to check

    Returns:
        True if the key appears to be masked
    """
    return key.startswith("****")

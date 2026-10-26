"""Utility helpers used by pkg.core."""

DEFAULT_RETRIES = 3


def slugify(text: str) -> str:
    """Lowercase and replace whitespace runs with single dashes."""
    return "-".join(text.lower().split())


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    """Clamp value into [low, high]."""
    return max(low, min(high, value))

"""String sanitization and redaction helpers."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_TOKEN_LIKE_RE = re.compile(
    r"(?i)\b(?:[0-9a-f]{32}|[0-9a-f]{64}|"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b"
)


def strip_nul(value: str) -> str:
    """Remove NUL characters from an input string.

    Args:
        value: The input string to sanitize.

    Returns:
        The input string with all NUL (``\\x00``) characters removed.
    """
    return value.replace("\x00", "")


def clean_env(value: str | None) -> str:
    """Normalize optional environment text to a stripped string.

    Args:
        value: An optional environment variable value to normalize.

    Returns:
        An empty string when *value* is ``None``; otherwise *value* stripped
        of leading and trailing whitespace.
    """
    return ("" if value is None else value).strip()


def redact_pii_and_secrets(value: str) -> str:
    """Redact emails and token-like substrings from free-form text.

    Args:
        value: The free-form text to sanitize.

    Returns:
        The sanitized text with email addresses replaced by
        ``[REDACTED_EMAIL]`` and token-like substrings replaced by
        ``[REDACTED_TOKEN]``.
    """
    text = strip_nul(str(value or ""))
    if not text:
        return ""
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    return _TOKEN_LIKE_RE.sub("[REDACTED_TOKEN]", text)

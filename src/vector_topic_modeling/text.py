"""Text shaping helpers for standalone topic modeling."""

from __future__ import annotations

from vector_topic_modeling._sanitize import redact_pii_and_secrets


def build_qa_pair_text(
    user_question: str | None,
    assistant_response: str | None,
    *,
    max_chars: int = 4000,
) -> str:
    """Build a redacted ``User/Assistant`` text block with length capping.

    Args:
        user_question: Raw user question text; ``None`` is treated as empty.
        assistant_response: Raw assistant response text; ``None`` is treated
            as empty.
        max_chars: Maximum character length of the resulting string.

    Returns:
        A ``"User: …\\nAssistant: …"`` block with PII/secrets redacted and
        truncated to *max_chars* characters, appending ``"…"`` when truncated.
    """
    uq = redact_pii_and_secrets(str(user_question or "")).strip()
    ar = redact_pii_and_secrets(str(assistant_response or "")).strip()
    out = f"User: {uq}\nAssistant: {ar}".strip()
    limit = max(1, int(max_chars))
    if len(out) <= limit:
        return out
    suffix = "…"
    if limit <= len(suffix):
        return suffix[:limit]
    return out[: limit - len(suffix)] + suffix


def normalize_text(value: str | None, *, max_chars: int = 4000) -> str:
    """Redact and trim text to the requested maximum character length.

    Args:
        value: Raw text to normalize; ``None`` is treated as empty.
        max_chars: Maximum number of characters to retain.

    Returns:
        Sanitized text with PII/secrets redacted, stripped of surrounding
        whitespace, and truncated to *max_chars* characters.
    """
    text = redact_pii_and_secrets(str(value or "")).strip()
    return text[:max_chars].rstrip() if len(text) > max_chars else text

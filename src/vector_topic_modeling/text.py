"""Text shaping helpers for standalone topic modeling."""

from __future__ import annotations

from vector_topic_modeling._sanitize import redact_pii_and_secrets


def build_qa_pair_text(
    user_question: str | None,
    assistant_response: str | None,
    *,
    max_chars: int = 4000,
) -> str:
    """Build a redacted ``User/Assistant`` text block with length capping."""
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
    """Redact and trim text to the requested maximum character length."""
    text = redact_pii_and_secrets(str(value or "")).strip()
    return text[:max_chars].rstrip() if len(text) > max_chars else text

"""Pure service helpers for topic statistics."""

from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json

from vector_topic_modeling._sanitize import strip_nul


def _norm_value(value: str | None) -> str:
    """Normalize filter values into stable non-empty tokens.

    Args:
        value: Raw filter value string, or ``None``.

    Returns:
        Stripped non-empty string, or ``"all"`` when *value* is ``None`` or
        blank after sanitization.
    """
    normalized = strip_nul(str(value or "")).strip()
    return normalized if normalized else "all"


def filter_signature_sha256_hex(filters: dict[str, str]) -> str:
    """Build a deterministic SHA-256 signature for filter dictionaries.

    Args:
        filters: Mapping from filter name to filter value.

    Returns:
        Lowercase hexadecimal SHA-256 digest of the canonicalized filter
        payload.
    """
    normalized = {str(key): _norm_value(value) for key, value in filters.items()}
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def previous_period(date_from: str, date_to: str) -> tuple[str, str]:
    """Return the immediately preceding date range with equal inclusive length.

    Args:
        date_from: ISO 8601 date string for the start of the current period.
        date_to: ISO 8601 date string for the end of the current period.

    Returns:
        ``(prev_start, prev_end)`` ISO 8601 date strings for the preceding
        period of the same length immediately before *date_from*.
    """
    start = date.fromisoformat(date_from)
    end = date.fromisoformat(date_to)
    if end < start:
        start, end = end, start
    days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return prev_start.isoformat(), prev_end.isoformat()


def format_trend(*, cur_count: int, prev_count: int) -> tuple[float | None, str]:
    """Format percentage trend from previous to current count.

    Args:
        cur_count: Document count for the current period.
        prev_count: Document count for the preceding period.

    Returns:
        ``(pct, label)`` tuple where *pct* is the rounded percentage change
        and *label* is a human-readable sign-prefixed string such as
        ``"+12%"`` or ``"-5%"``.
    """
    current = int(cur_count)
    previous = int(prev_count)
    if previous <= 0:
        if current <= 0:
            return 0.0, "+0%"
        return 100.0, "+100%"
    pct = ((current - previous) / previous) * 100.0
    rounded = float(round(pct))
    sign = "+" if rounded >= 0 else ""
    return rounded, f"{sign}{int(rounded)}%"

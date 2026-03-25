"""Pure service helpers for topic statistics."""

from __future__ import annotations

from datetime import date, timedelta
import hashlib
import json

from vector_topic_modeling._sanitize import strip_nul


def _norm_value(value: str | None) -> str:
    normalized = strip_nul(str(value or "")).strip()
    return "all" if not normalized else normalized


def filter_signature_sha256_hex(filters: dict[str, str]) -> str:
    normalized = {str(key): _norm_value(value) for key, value in filters.items()}
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def previous_period(date_from: str, date_to: str) -> tuple[str, str]:
    start = date.fromisoformat(date_from)
    end = date.fromisoformat(date_to)
    if end < start:
        start, end = end, start
    days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return prev_start.isoformat(), prev_end.isoformat()


def format_trend(*, cur_count: int, prev_count: int) -> tuple[float | None, str]:
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

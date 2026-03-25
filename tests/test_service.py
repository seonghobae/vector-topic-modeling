from __future__ import annotations

from vector_topic_modeling.service import (
    filter_signature_sha256_hex,
    format_trend,
    previous_period,
)


def test_filter_signature_is_order_independent() -> None:
    a = filter_signature_sha256_hex(
        {"model": "gpt-4o", "api_key": "all", "team_alias": "TEAM_ALPHA"}
    )
    b = filter_signature_sha256_hex(
        {"team_alias": "TEAM_ALPHA", "api_key": "all", "model": "gpt-4o"}
    )
    assert a == b
    assert len(a) == 64


def test_previous_period_has_same_length() -> None:
    assert previous_period("2026-02-01", "2026-02-07") == ("2026-01-25", "2026-01-31")


def test_format_trend_handles_zero_previous() -> None:
    assert format_trend(cur_count=0, prev_count=0)[1] == "+0%"
    assert format_trend(cur_count=10, prev_count=0)[1] == "+100%"
    assert format_trend(cur_count=10, prev_count=10)[1] == "+0%"
    assert format_trend(cur_count=5, prev_count=10)[1] == "-50%"

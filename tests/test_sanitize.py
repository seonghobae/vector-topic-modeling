from __future__ import annotations

from vector_topic_modeling._sanitize import clean_env, redact_pii_and_secrets, strip_nul


def test_strip_nul_removes_nul_bytes() -> None:
    assert strip_nul("a\x00b") == "ab"


def test_clean_env_trims_whitespace() -> None:
    assert clean_env("  value  ") == "value"
    assert clean_env(None) == ""


def test_redact_pii_and_secrets_masks_email_and_token() -> None:
    text = redact_pii_and_secrets("mail a@b.com token 0123456789abcdef0123456789abcdef")
    assert "a@b.com" not in text
    assert "0123456789abcdef0123456789abcdef" not in text
    assert "[REDACTED_EMAIL]" in text
    assert "[REDACTED_TOKEN]" in text

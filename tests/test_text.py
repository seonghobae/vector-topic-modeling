from __future__ import annotations

from vector_topic_modeling.text import build_qa_pair_text


def test_build_qa_pair_text_includes_user_and_assistant() -> None:
    out = build_qa_pair_text(
        user_question="사용자 질문",
        assistant_response="어시스턴트 응답",
        max_chars=10_000,
    )
    assert "User:" in out
    assert "Assistant:" in out
    assert "사용자 질문" in out
    assert "어시스턴트 응답" in out


def test_build_qa_pair_text_redacts_email_and_tokens() -> None:
    out = build_qa_pair_text(
        user_question="email user@corp.example",
        assistant_response="payload=0123456789abcdef0123456789abcdef",
        max_chars=10_000,
    )
    assert "user@corp.example" not in out
    assert "0123456789abcdef" not in out
    assert "[REDACTED_EMAIL]" in out
    assert "[REDACTED_TOKEN]" in out


def test_build_qa_pair_text_truncates_long_inputs() -> None:
    long = "x" * 10_000
    out = build_qa_pair_text(long, long, max_chars=200)
    assert len(out) <= 200

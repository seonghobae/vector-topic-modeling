from __future__ import annotations

from vector_topic_modeling.sessioning import (
    aggregate_session_topic_counts,
    build_digest_counts_all_pairs,
    build_digest_counts_session_main_pair,
    pick_sample_sessions_for_topics,
    pick_session_main_digest,
)


def test_aggregate_session_topic_counts_sums_by_session_and_topic() -> None:
    rows = [
        {"session_id": "A", "digest_hex": "d1", "count": 2},
        {"session_id": "A", "digest_hex": "d2", "count": 1},
        {"session_id": "B", "digest_hex": "d2", "count": 3},
    ]
    digest_to_topic = {"d1": "T1", "d2": "T2"}
    out = aggregate_session_topic_counts(rows, digest_to_topic)
    assert out[("A", "T1")] == 2
    assert out[("A", "T2")] == 1
    assert out[("B", "T2")] == 3


def test_pick_sample_sessions_is_deterministic_and_bounded() -> None:
    topic_sessions = {"T1": [("A", 5), ("B", 3)], "T2": [("B", 10), ("C", 1)]}
    picks = pick_sample_sessions_for_topics(
        topic_sessions, max_per_topic=1, max_total=2
    )
    assert picks["T1"] == ["A"]
    assert picks["T2"] == ["B"]


def test_session_main_pair_selection_avoids_trivial_dominance() -> None:
    greeting_digest = "g" * 64
    rows: list[dict[str, object]] = []
    for i in range(20):
        sess = f"sess-{i:02d}"
        rows.append(
            {
                "session_id": sess,
                "question": "안녕?",
                "response": "안녕하세요! 무엇을 도와드릴까요?",
                "digest_hex": greeting_digest,
                "count": 50,
            }
        )
        rows.append(
            {
                "session_id": sess,
                "question": f"2026년 2월 법인세 신고 절차를 단계별로 설명해줘 ({i})",
                "response": "전제 조건을 확인한 뒤 신고 대상/서류/기한을 정리하고 홈택스에서 신고서를 작성합니다.",
                "digest_hex": (f"sub-{i:02d}".encode("utf-8").hex() * 4)[:64],
                "count": 1,
            }
        )
    assert (
        max(
            build_digest_counts_all_pairs(rows).items(), key=lambda x: (int(x[1]), x[0])
        )[0]
        == greeting_digest
    )
    assert build_digest_counts_session_main_pair(rows).get(greeting_digest, 0) == 0


def test_pick_session_main_digest_edge_cases() -> None:
    assert pick_session_main_digest([]) is None
    assert pick_session_main_digest([{"session_id": "s1", "question": "x"}]) is None


def test_pick_session_main_digest_prefers_substantive_candidate() -> None:
    greeting_digest = "g" * 64
    substantive_digest = "a" * 64
    rows: list[dict[str, object]] = [
        {
            "session_id": "s1",
            "question": "안녕?",
            "response": "안녕하세요!",
            "digest_hex": greeting_digest,
        },
        {
            "session_id": "s1",
            "question": "2026년 2월 법인세 신고 절차를 단계별로 설명해줘",
            "response": "전제 조건/서류/기한을 정리하고 홈택스에서 신고서를 작성합니다.",
            "digest_hex": substantive_digest,
        },
    ]
    assert pick_session_main_digest(rows) == substantive_digest


def test_pick_session_main_digest_tiebreaks_by_digest_hex() -> None:
    rows: list[dict[str, object]] = [
        {
            "session_id": "s1",
            "question": "same",
            "response": "same",
            "digest_hex": "b" * 64,
        },
        {
            "session_id": "s1",
            "question": "same",
            "response": "same",
            "digest_hex": "a" * 64,
        },
    ]
    assert pick_session_main_digest(rows) == ("a" * 64)


def test_build_digest_counts_all_pairs_coerces_count_types_and_clamps() -> None:
    rows: list[dict[str, object]] = [
        {"digest_hex": "a" * 64, "count": 1},
        {"digest_hex": "a" * 64, "count": True},
        {"digest_hex": "a" * 64, "count": 2.9},
        {"digest_hex": "a" * 64, "count": "3"},
        {"digest_hex": "a" * 64, "count": "bad"},
        {"digest_hex": "a" * 64, "count": -5},
        {"digest_hex": "", "count": 123},
    ]
    assert build_digest_counts_all_pairs(rows) == {"a" * 64: 7}


def test_build_digest_counts_session_main_pair_skips_empty_choice_and_keeps_best() -> (
    None
):
    s1_rows = [
        {
            "session_id": "s1",
            "digest_hex": "d-best",
            "question": "long unique tax filing question",
            "response": "detailed answer",
        },
        {
            "session_id": "s1",
            "digest_hex": "d-low",
            "question": "hi",
            "response": "ok",
        },
    ]

    assert pick_session_main_digest(s1_rows) == "d-best"

    all_rows = [
        {"session_id": "s0", "digest_hex": "", "question": "x", "response": "y"},
        *s1_rows,
    ]
    assert build_digest_counts_session_main_pair(all_rows) == {"d-best": 1}


def test_pick_sample_sessions_for_topics_ignores_duplicate_session_ids() -> None:
    out = pick_sample_sessions_for_topics(
        {"T1": [("sess-a", 5), ("sess-a", 4), ("sess-b", 3)]},
        max_per_topic=10,
        max_total=10,
    )

    assert out["T1"] == ["sess-a", "sess-b"]

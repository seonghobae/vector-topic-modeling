import pytest
import json
from pathlib import Path
from vector_topic_modeling.ingestion import (
    _coerce_count, _stringify, _to_field_tuple, _opt_text, _first_non_empty, _materialize_column_value_fields,
    TopicDocumentIngestionConfig, load_jsonl_topic_documents, _resolve_session_id
)

def test_coerce_count():
    assert _coerce_count(True, default=1) == 1
    assert _coerce_count(5, default=1) == 5
    assert _coerce_count(5.5, default=1) == 5
    assert _coerce_count("7", default=1) == 7
    assert _coerce_count("abc", default=1) == 1
    assert _coerce_count(None, default=1) == 1

def test_stringify():
    assert _stringify(None) == ""
    assert _stringify("test") == "test"
    assert _stringify(5) == "5"
    assert _stringify(5.5) == "5.5"
    assert _stringify(True) == "True"
    assert _stringify(["a", "b"]) == '["a", "b"]'
    assert _stringify({"a": 1}) == '{"a": 1}'

def test_to_field_tuple():
    assert _to_field_tuple(None, fallback=("a",)) == ("a",)
    assert _to_field_tuple(" b ", fallback=("a",)) == ("b",)
    assert _to_field_tuple("   ", fallback=("a",)) == ("a",)
    assert _to_field_tuple([" b ", "  ", "c"], fallback=("a",)) == ("b", "c")
    assert _to_field_tuple(["   "], fallback=("a",)) == ("a",)
    assert _to_field_tuple(123, fallback=("a",)) == ("a",)

def test_opt_text():
    assert _opt_text(None) is None
    assert _opt_text("  ") is None
    assert _opt_text(" a ") == "a"
    assert _opt_text(123) == "123"

def test_first_non_empty():
    assert _first_non_empty({"a": " "}, ("a", "b")) == ""
    assert _first_non_empty({"a": " "}, ("b",)) == ""

def test_materialize_edge_cases():
    config = TopicDocumentIngestionConfig(column_value_path="cols")
    
    assert _materialize_column_value_fields(row={"cols": None}, config=config) == {"cols": None}
    
    assert _materialize_column_value_fields(row={"cols": ["bad"]}, config=config) == {"cols": ["bad"]}
    
    assert _materialize_column_value_fields(row={"cols": [{"column": " "}]}, config=config) == {"cols": [{"column": " "}]}

def test_load_jsonl_empty_lines(tmp_path: Path):
    input_path = tmp_path / "input.jsonl"
    input_path.write_text("\n\n{\"id\":\"1\"}\n\n", encoding="utf-8")
    docs = load_jsonl_topic_documents(input_path)
    assert len(docs) == 1

def test_resolve_session_id_missing_keys():
    config = TopicDocumentIngestionConfig(session_key_fields=("a", "b"))
    assert _resolve_session_id({"a": "1"}, config=config) is None

def test_resolve_text_qa_pair():
    from vector_topic_modeling.ingestion import _resolve_text
    config = TopicDocumentIngestionConfig()
    text = _resolve_text(row={}, question="Q?", response="A!", config=config)
    assert "Q?" in text
    assert "A!" in text

from vector_topic_modeling.sessioning import (
    pick_session_main_digest,
    build_digest_counts_all_pairs,
    aggregate_session_topic_counts,
    pick_sample_sessions_for_topics,
    build_digest_counts_session_main_pair
)

def test_pick_session_main_digest_selector_exception():
    def bad_selector(sid, rows):
        raise ValueError("bad")
    rows = [{"session_id": "s1", "digest_hex": "d1"}]
    assert pick_session_main_digest(rows, selector=bad_selector) == "d1"

def test_pick_session_main_digest_selector_success():
    def good_selector(sid, rows):
        return "d2"
    rows = [{"session_id": "s1", "digest_hex": "d1"}, {"session_id": "s1", "digest_hex": "d2"}]
    assert pick_session_main_digest(rows, selector=good_selector) == "d2"

def test_build_digest_counts_all_pairs_bad_types():
    rows = [
        {"digest_hex": "d1", "count": object()},
        {"digest_hex": "d2", "count": True},
        {"digest_hex": "d3", "count": 2.5},
        {"digest_hex": "d4", "count": "bad"},
        {"digest_hex": "d5", "count": "10"},
        {"digest_hex": "d6"},
    ]
    res = build_digest_counts_all_pairs(rows)
    assert res == {"d1": 0, "d2": 1, "d3": 2, "d4": 0, "d5": 10, "d6": 0}

def test_build_digest_counts_session_main_pair_edge_cases():
    rows = [
        {"session_id": "", "digest_hex": "d1"}, # ignored session
        {"session_id": "s1", "digest_hex": "d1"}, 
    ]
    res = build_digest_counts_session_main_pair(rows)
    assert res == {"d1": 1}

def test_aggregate_session_topic_counts_edge_cases():
    digest_to_topic = {"d1": "t1", "d2": "t2", "d3": "t3"}
    rows = [
        {"session_id": "", "digest_hex": "d1"}, # missing session
        {"session_id": "s1", "digest_hex": "unknown"}, # missing topic
        {"session_id": "s2", "digest_hex": "d2", "count": True}, # count 0 because of bool handling in this func
        {"session_id": "s2", "digest_hex": "d2", "count": 2.5},
        {"session_id": "s2", "digest_hex": "d2", "count": "bad"},
        {"session_id": "s3", "digest_hex": "d3", "count": object()},
        {"session_id": "s3", "digest_hex": "d3", "count": -1}, # <= 0
        {"session_id": "s4", "digest_hex": "d2", "count": "3"},
    ]
    res = aggregate_session_topic_counts(rows, digest_to_topic)
    assert res == {("s2", "t2"): 2, ("s4", "t2"): 3}

def test_pick_sample_sessions_for_topics_edge_cases():
    topic_sessions = {
        "t1": [(None, 5), ("", 4)], # session not stripped / empty
        "t2": [("s1", 5), ("s2", 4), ("s1", 3)], # duplicate session
    }
    # Test `total_cap` limit reached early
    res = pick_sample_sessions_for_topics(topic_sessions, max_per_topic=5, max_total=1)
    assert res["t1"] == []
    assert res["t2"] == ["s1"] # reached cap

def test_pick_session_main_digest_missed_lines():
    assert pick_session_main_digest([]) is None
    # row without digest
    assert pick_session_main_digest([{"session_id": "s1"}]) is None
    # testing int count, ValueError on string, and per_topic break
    
def test_build_digest_counts_all_pairs_missed_lines():
    rows = [
        {"digest_hex": "d1", "count": 10}, # int type
        {"digest_hex": "d2", "count": "bad"}, # string ValueError
    ]
    res = build_digest_counts_all_pairs(rows)
    assert res == {"d1": 10, "d2": 0}

def test_pick_sample_sessions_for_topics_missed_lines():
    topic_sessions = {
        "t1": [("s1", 5), ("s2", 4), ("s3", 3)],
    }
    # Test per_topic limit reached
    res = pick_sample_sessions_for_topics(topic_sessions, max_per_topic=2, max_total=10)
    assert res["t1"] == ["s1", "s2"]


def test_build_digest_counts_all_pairs_missing_digest():
    rows = [{"digest_hex": ""}]
    res = build_digest_counts_all_pairs(rows)
    assert res == {}

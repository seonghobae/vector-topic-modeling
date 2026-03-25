from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from vector_topic_modeling.ingestion import (
    TopicDocumentIngestionConfig,
    load_ingestion_config,
    load_jsonl_topic_documents,
    topic_document_from_row,
)


def test_topic_document_from_row_preserves_legacy_defaults() -> None:
    row = {
        "id": "doc-1",
        "text": "refund duplicate billing",
        "session_id": "session-1",
        "question": "q",
        "response": "r",
        "count": 3,
    }

    doc = topic_document_from_row(row, row_index=0)

    assert doc.id == "doc-1"
    assert doc.text == "refund duplicate billing"
    assert doc.session_id == "session-1"
    assert doc.question == "q"
    assert doc.response == "r"
    assert doc.count == 3


def test_topic_document_from_row_uses_payload_when_text_missing() -> None:
    row = {
        "id": "doc-2",
        "payload": {"ticket": {"intent": "billing_refund", "locale": "ko-KR"}},
    }

    doc = topic_document_from_row(row, row_index=0)

    assert "billing_refund" in doc.text
    assert "ticket" in doc.text


def test_topic_document_from_row_supports_db_column_value_input() -> None:
    config = TopicDocumentIngestionConfig(
        content_fields=("query", "answer"),
        column_value_path="columns",
    )
    row = {
        "id": "doc-3",
        "columns": [
            {"column": "query", "value": "왜 이중 결제가 되었나요?"},
            {"column": "answer", "value": "영수증을 확인한 뒤 환불을 도와드릴게요."},
        ],
    }

    doc = topic_document_from_row(row, row_index=0, config=config)

    assert "query:" in doc.text
    assert "answer:" in doc.text


def test_topic_document_from_row_builds_session_id_from_primary_key_bundle() -> None:
    config = TopicDocumentIngestionConfig(session_key_fields=("tenant_id", "thread_id"))
    row = {
        "id": "doc-4",
        "tenant_id": "t-1",
        "thread_id": "th-9",
        "text": "session key bundle example",
    }

    doc = topic_document_from_row(row, row_index=0, config=config)

    expected_session_id = 'pk:{"tenant_id":"t-1","thread_id":"th-9"}'
    assert doc.session_id == expected_session_id


def test_load_jsonl_topic_documents_accepts_config_file(tmp_path: Path) -> None:
    input_path = tmp_path / "input.jsonl"
    config_path = tmp_path / "ingestion.json"

    input_path.write_text(
        json.dumps(
            {
                "pk_a": "A",
                "pk_b": "B",
                "payload": {"message": "db payload text"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config_path.write_text(
        json.dumps(
            {
                "session_key_fields": ["pk_a", "pk_b"],
                "payload_fields": ["payload"],
                "id_fields": ["pk_a"],
            }
        ),
        encoding="utf-8",
    )

    config = load_ingestion_config(config_path)
    docs = load_jsonl_topic_documents(input_path, config=config)

    assert len(docs) == 1
    assert docs[0].id == "A"
    assert docs[0].session_id is not None
    assert "db payload text" in docs[0].text


def test_load_ingestion_config_rejects_non_object_json(tmp_path: Path) -> None:
    config_path = tmp_path / "ingestion.json"
    config_path.write_text(json.dumps(["bad"]), encoding="utf-8")

    with pytest.raises(TypeError, match="JSON object"):
        load_ingestion_config(config_path)


def test_load_jsonl_topic_documents_rejects_non_object_rows(tmp_path: Path) -> None:
    input_path = tmp_path / "input.jsonl"
    input_path.write_text(json.dumps(["bad"]) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load_jsonl_topic_documents(input_path)


def test_topic_document_from_row_accepts_non_json_serializable_payload_values() -> None:
    row = {
        "id": "doc-x",
        "payload": {"ts": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)},
    }

    doc = topic_document_from_row(row, row_index=0)

    assert "2026-01-01" in doc.text

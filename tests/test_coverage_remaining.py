import pytest
from pathlib import Path
import json
import argparse
from unittest.mock import patch

from vector_topic_modeling._sanitize import redact_pii_and_secrets
from vector_topic_modeling.cli import main
from vector_topic_modeling.pipeline import TopicModeler
from vector_topic_modeling.service import previous_period
from vector_topic_modeling.text import build_qa_pair_text


def test_sanitize_empty():
    assert redact_pii_and_secrets("") == ""
    assert redact_pii_and_secrets(None) == ""


def test_cli_errors():
    with pytest.raises(SystemExit):
        main(["--help"])

    # To test line 42, we bypass argparse
    with patch("vector_topic_modeling.cli.build_parser") as mock_parser:
        mock_args = argparse.Namespace(
            command="invalid", base_url="test", api_key="test"
        )
        mock_parser.return_value.parse_args.return_value = mock_args
        with pytest.raises(ValueError, match="Unsupported command: invalid"):
            main(["cluster"])

    # To test line 44, we missing base-url and api-key
    with patch("vector_topic_modeling.cli.build_parser") as mock_parser:
        mock_args = argparse.Namespace(command="cluster", base_url="", api_key="")
        mock_parser.return_value.parse_args.return_value = mock_args
        with pytest.raises(
            ValueError, match="cluster requires --base-url and --api-key"
        ):
            main(["cluster"])


def test_pipeline_unassigned():
    pipeline = TopicModeler(config=None, embedding_provider=None)
    # mock rows
    rows = [
        {
            "session_id": "sess_1",
            "digest_hex": "digest_1",
            "count": 1,
            "representative_text": "text_1",
        },
        {
            "session_id": "sess_unassigned",
            "digest_hex": "digest_unknown",
            "count": 1,
            "representative_text": "text_unassigned",
        },
    ]
    digest_to_topic = {"digest_1": "topic_A"}
    session_representatives = {"sess_1": "digest_1"}

    # testing _resolve_assignment_topic_id directly for "unassigned"
    assert (
        pipeline._resolve_assignment_topic_id(
            row=rows[1],
            digest_to_topic=digest_to_topic,
            session_representatives=session_representatives,
        )
        == "unassigned"
    )

    # testing _build_session_topic_counts
    counts = pipeline._build_session_topic_counts(
        rows=rows,
        digest_to_topic=digest_to_topic,
        session_representatives=session_representatives,
    )
    assert ("sess_1", "topic_A") in counts
    assert ("sess_unassigned", "unassigned") not in counts


def test_service_previous_period():
    assert previous_period("2024-01-05", "2024-01-01") == ("2023-12-27", "2023-12-31")


def test_text_build_qa_pair_text_edge_cases():
    assert build_qa_pair_text("test", "test", max_chars=1) == "…"

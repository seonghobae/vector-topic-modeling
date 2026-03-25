from __future__ import annotations

import json
from pathlib import Path

from vector_topic_modeling.cli import build_parser


def test_build_parser_supports_cluster_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["cluster", "input.jsonl", "--output", "topics.json"])
    assert args.command == "cluster"
    assert args.input_path == "input.jsonl"
    assert args.output_path == "topics.json"
    assert args.ingestion_config is None


def test_cli_cluster_writes_output(monkeypatch, tmp_path: Path) -> None:
    from vector_topic_modeling import cli

    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "topics.json"
    input_path.write_text(
        json.dumps({"id": "1", "text": "refund duplicate billing"}) + "\n",
        encoding="utf-8",
    )

    class FakeProvider:
        def __init__(self, config) -> None:
            self.config = config

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(cli, "OpenAICompatEmbeddingProvider", FakeProvider)

    rc = cli.main(
        [
            "cluster",
            str(input_path),
            "--output",
            str(output_path),
            "--base-url",
            "https://example.com",
            "--api-key",
            "key",
        ]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["topics"]
    assert payload["assignments"][0]["document_id"] == "1"


def test_cli_cluster_supports_generic_ingestion_config(
    monkeypatch, tmp_path: Path
) -> None:
    from vector_topic_modeling import cli

    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "topics.json"
    config_path = tmp_path / "ingestion.json"

    input_path.write_text(
        json.dumps(
            {
                "pk_a": "account-1",
                "pk_b": "thread-2",
                "payload": {"text": "generic payload topic text"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config_path.write_text(
        json.dumps(
            {
                "id_fields": ["pk_a"],
                "payload_fields": ["payload"],
                "session_key_fields": ["pk_a", "pk_b"],
            }
        ),
        encoding="utf-8",
    )

    class FakeProvider:
        def __init__(self, config) -> None:
            self.config = config

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(cli, "OpenAICompatEmbeddingProvider", FakeProvider)

    rc = cli.main(
        [
            "cluster",
            str(input_path),
            "--output",
            str(output_path),
            "--ingestion-config",
            str(config_path),
            "--base-url",
            "https://example.com",
            "--api-key",
            "key",
        ]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert payload["topics"]
    assert payload["assignments"][0]["document_id"] == "account-1"
    assert payload["session_topic_counts"]
    assert payload["session_topic_counts"][0]["session_id"]
    assert "account-1" in payload["session_topic_counts"][0]["session_id"]
    assert "thread-2" in payload["session_topic_counts"][0]["session_id"]

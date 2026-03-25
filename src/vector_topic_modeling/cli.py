"""Command-line interface for standalone topic modeling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vector_topic_modeling.pipeline import TopicDocument, TopicModelConfig, TopicModeler
from vector_topic_modeling.providers.openai_compat import (
    OpenAICompatConfig,
    OpenAICompatEmbeddingProvider,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vector-topic-modeling",
        description="Standalone embedding-based topic modeling",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    cluster = subparsers.add_parser(
        "cluster", help="Cluster JSONL documents into topics"
    )
    cluster.add_argument("input_path")
    cluster.add_argument("--output", dest="output_path", required=True)
    cluster.add_argument("--base-url")
    cluster.add_argument("--api-key")
    cluster.add_argument("--model", default="text-embedding-3-large")
    cluster.add_argument("--similarity-threshold", type=float, default=0.85)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "cluster":
        raise ValueError(f"Unsupported command: {args.command}")
    if not args.base_url or not args.api_key:
        raise ValueError("cluster requires --base-url and --api-key")
    docs = _load_jsonl(Path(args.input_path))
    provider = OpenAICompatEmbeddingProvider(
        OpenAICompatConfig(
            base_url=args.base_url, api_key=args.api_key, model=args.model
        )
    )
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(
            similarity_threshold=float(args.similarity_threshold),
            embedding_model_name=args.model,
        ),
    )
    result = modeler.fit_predict(docs)
    payload = {
        "topics": [topic.__dict__ for topic in result.topics],
        "assignments": [assignment.__dict__ for assignment in result.assignments],
        "session_topic_counts": [
            {"session_id": session_id, "topic_id": topic_id, "count": count}
            for (session_id, topic_id), count in sorted(
                result.session_topic_counts.items()
            )
        ],
    }
    Path(args.output_path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


def _load_jsonl(path: Path) -> list[TopicDocument]:
    documents: list[TopicDocument] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        documents.append(
            TopicDocument(
                id=str(row.get("id") or row.get("document_id") or len(documents)),
                text=str(row.get("text") or ""),
                session_id=row.get("session_id"),
                question=row.get("question"),
                response=row.get("response"),
                count=int(row.get("count") or 1),
            )
        )
    return documents

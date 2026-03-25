"""Command-line interface for standalone topic modeling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from vector_topic_modeling.ingestion import (
    load_ingestion_config,
    load_jsonl_topic_documents,
)
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
    cluster.add_argument("--min-topics", type=int, default=2)
    cluster.add_argument("--max-topics", type=int, default=30)
    cluster.add_argument("--max-top-share", type=float, default=0.35)
    cluster.add_argument("--display-limit", type=int, default=30)
    cluster.add_argument("--use-session-representatives", action="store_true")
    cluster.add_argument("--ingestion-config")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "cluster":
        raise ValueError(f"Unsupported command: {args.command}")
    if not args.base_url or not args.api_key:
        raise ValueError("cluster requires --base-url and --api-key")
    docs = _load_jsonl(
        Path(args.input_path),
        ingestion_config_path=args.ingestion_config,
    )
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
            min_topics=args.min_topics,
            max_topics=args.max_topics,
            max_top_share=args.max_top_share,
            use_session_representatives=args.use_session_representatives,
            display_limit=args.display_limit,
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


def _load_jsonl(
    path: Path,
    *,
    ingestion_config_path: str | None = None,
) -> list[TopicDocument]:
    config = load_ingestion_config(ingestion_config_path)
    return load_jsonl_topic_documents(path, config=config)

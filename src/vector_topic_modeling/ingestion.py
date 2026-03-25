"""Generic row ingestion helpers for topic modeling inputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from vector_topic_modeling.pipeline import TopicDocument
from vector_topic_modeling.text import build_qa_pair_text, normalize_text


@dataclass(frozen=True)
class TopicDocumentIngestionConfig:
    id_fields: tuple[str, ...] = ("id", "document_id")
    text_fields: tuple[str, ...] = ("text",)
    payload_fields: tuple[str, ...] = ("payload", "json_payload", "body")
    content_fields: tuple[str, ...] = ()
    question_fields: tuple[str, ...] = ("question",)
    response_fields: tuple[str, ...] = ("response",)
    session_id_fields: tuple[str, ...] = ("session_id",)
    session_key_fields: tuple[str, ...] = ()
    count_field: str = "count"
    column_value_path: str | None = None
    column_name_field: str = "column"
    column_value_field: str = "value"
    max_text_chars: int = 4000


def load_ingestion_config(path: str | Path | None) -> TopicDocumentIngestionConfig:
    if path is None:
        return TopicDocumentIngestionConfig()
    parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise TypeError("ingestion config must be a JSON object")
    return TopicDocumentIngestionConfig(
        id_fields=_to_field_tuple(
            parsed.get("id_fields"), fallback=("id", "document_id")
        ),
        text_fields=_to_field_tuple(parsed.get("text_fields"), fallback=("text",)),
        payload_fields=_to_field_tuple(
            parsed.get("payload_fields"),
            fallback=("payload", "json_payload", "body"),
        ),
        content_fields=_to_field_tuple(parsed.get("content_fields"), fallback=()),
        question_fields=_to_field_tuple(
            parsed.get("question_fields"), fallback=("question",)
        ),
        response_fields=_to_field_tuple(
            parsed.get("response_fields"), fallback=("response",)
        ),
        session_id_fields=_to_field_tuple(
            parsed.get("session_id_fields"), fallback=("session_id",)
        ),
        session_key_fields=_to_field_tuple(
            parsed.get("session_key_fields"), fallback=()
        ),
        count_field=str(parsed.get("count_field") or "count"),
        column_value_path=_opt_text(parsed.get("column_value_path")),
        column_name_field=str(parsed.get("column_name_field") or "column"),
        column_value_field=str(parsed.get("column_value_field") or "value"),
        max_text_chars=max(1, int(parsed.get("max_text_chars") or 4000)),
    )


def load_jsonl_topic_documents(
    path: Path,
    *,
    config: TopicDocumentIngestionConfig | None = None,
) -> list[TopicDocument]:
    effective = config or TopicDocumentIngestionConfig()
    documents: list[TopicDocument] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError("each JSONL line must be a JSON object")
        documents.append(
            topic_document_from_row(row, row_index=len(documents), config=effective)
        )
    return documents


def topic_document_from_row(
    row: Mapping[str, object],
    *,
    row_index: int,
    config: TopicDocumentIngestionConfig | None = None,
) -> TopicDocument:
    effective = config or TopicDocumentIngestionConfig()
    materialized = _materialize_column_value_fields(row=row, config=effective)
    question = _first_non_empty(materialized, effective.question_fields)
    response = _first_non_empty(materialized, effective.response_fields)
    text = _resolve_text(
        row=materialized,
        question=question,
        response=response,
        config=effective,
    )
    session_id = _resolve_session_id(materialized, config=effective)
    document_id = _resolve_document_id(
        row=materialized,
        row_index=row_index,
        config=effective,
    )
    return TopicDocument(
        id=document_id,
        text=text,
        session_id=session_id,
        question=question or None,
        response=response or None,
        count=_coerce_count(materialized.get(effective.count_field), default=1),
    )


def _resolve_document_id(
    *,
    row: Mapping[str, object],
    row_index: int,
    config: TopicDocumentIngestionConfig,
) -> str:
    explicit = _first_non_empty(row, config.id_fields)
    return explicit if explicit else str(row_index)


def _resolve_session_id(
    row: Mapping[str, object],
    *,
    config: TopicDocumentIngestionConfig,
) -> str | None:
    explicit = _first_non_empty(row, config.session_id_fields)
    if explicit:
        return explicit
    if not config.session_key_fields:
        return None
    bundle: dict[str, str] = {}
    for field in config.session_key_fields:
        value = _stringify(row.get(field)).strip()
        if not value:
            return None
        bundle[field] = value
    return "pk:" + json.dumps(
        bundle,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _resolve_text(
    *,
    row: Mapping[str, object],
    question: str,
    response: str,
    config: TopicDocumentIngestionConfig,
) -> str:
    direct_text = _first_non_empty(row, config.text_fields)
    if direct_text:
        return normalize_text(direct_text, max_chars=config.max_text_chars)
    if config.content_fields:
        pieces = []
        for field in config.content_fields:
            raw = row.get(field)
            rendered = _stringify(raw).strip()
            if rendered:
                pieces.append(f"{field}: {rendered}")
        if pieces:
            return normalize_text("\n".join(pieces), max_chars=config.max_text_chars)
    payload_text = _first_non_empty(row, config.payload_fields)
    if payload_text:
        return normalize_text(payload_text, max_chars=config.max_text_chars)
    if question or response:
        return build_qa_pair_text(
            question,
            response,
            max_chars=config.max_text_chars,
        )
    return normalize_text(
        json.dumps(row, ensure_ascii=False, sort_keys=True, default=str),
        max_chars=config.max_text_chars,
    )


def _materialize_column_value_fields(
    *,
    row: Mapping[str, object],
    config: TopicDocumentIngestionConfig,
) -> dict[str, object]:
    out = dict(row)
    source_key = config.column_value_path
    if not source_key:
        return out
    raw = out.get(source_key)
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        column_name = _stringify(item.get(config.column_name_field)).strip()
        if not column_name:
            continue
        out[column_name] = item.get(config.column_value_field)
    return out


def _first_non_empty(row: Mapping[str, object], fields: tuple[str, ...]) -> str:
    for field in fields:
        rendered = _stringify(row.get(field)).strip()
        if rendered:
            return rendered
    return ""


def _coerce_count(value: Any, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def _to_field_tuple(value: object, *, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return fallback
    if isinstance(value, str):
        stripped = value.strip()
        return (stripped,) if stripped else fallback
    if isinstance(value, list):
        fields = tuple(str(item).strip() for item in value if str(item).strip())
        return fields if fields else fallback
    return fallback


def _opt_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None

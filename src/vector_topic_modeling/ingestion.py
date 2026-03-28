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
    """Configurable field mapping rules for converting source rows to documents.

    Attributes:
        id_fields: Candidate field names used to resolve a document identifier.
        text_fields: Candidate field names for the primary text body.
        payload_fields: Candidate field names for structured payload text.
        content_fields: Optional field names whose values are concatenated as
            labelled content blocks.
        question_fields: Candidate field names for the user question text.
        response_fields: Candidate field names for the assistant response text.
        session_id_fields: Candidate field names for the session identifier.
        session_key_fields: Ordered field names used to synthesize a composite
            session identifier when no direct session-id field is present.
        count_field: Name of the field holding the document occurrence count.
        column_value_path: Optional key of a list of column/value records to
            promote into top-level row fields.
        column_name_field: Name of the column-name sub-field in column/value
            records.
        column_value_field: Name of the value sub-field in column/value
            records.
        max_text_chars: Maximum character length to which text is trimmed.
    """

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
    """Load ingestion mapping config from JSON, or defaults when omitted.

    Args:
        path: Filesystem path to a JSON ingestion-config file, or ``None``
            to use built-in defaults.

    Returns:
        A :class:`TopicDocumentIngestionConfig` with values from the file or
        all-default field mappings when *path* is ``None``.

    Raises:
        TypeError: When the JSON file root is not an object.
    """
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
    """Parse a JSONL file and map each object row into a topic document.

    Args:
        path: Filesystem path to the ``.jsonl`` source file.
        config: Optional ingestion config overriding field-mapping defaults.

    Returns:
        Ordered list of :class:`TopicDocument` instances, one per non-blank
        line in the file.

    Raises:
        ValueError: When a JSONL line is not a JSON object.
    """
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
    """Convert one generic mapping row into a normalized ``TopicDocument``.

    Args:
        row: Source data row as a key-to-value mapping.
        row_index: Zero-based position of the row in the source file, used as
            a fallback document identifier.
        config: Optional ingestion config controlling field resolution.

    Returns:
        A :class:`TopicDocument` with text, session, and count fields resolved
        from *row* according to *config*.
    """
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
    """Resolve document id from configured fields or fallback to row index.

    Args:
        row: Source data row to inspect.
        row_index: Fallback index used when no id field is populated.
        config: Ingestion config specifying candidate id field names.

    Returns:
        String document identifier from the first populated id field, or the
        string representation of *row_index* when no such field exists.
    """
    explicit = _first_non_empty(row, config.id_fields)
    return explicit if explicit else str(row_index)


def _resolve_session_id(
    row: Mapping[str, object],
    *,
    config: TopicDocumentIngestionConfig,
) -> str | None:
    """Resolve a session id directly or synthesize one from key fields.

    Args:
        row: Source data row to inspect.
        config: Ingestion config specifying session-id and session-key fields.

    Returns:
        String session identifier, a synthesized ``pk:…`` composite when key
        fields are configured, or ``None`` when no session identity can be
        determined.
    """
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
    """Resolve model text using direct text, field bundles, payload, or QA fallback.

    Args:
        row: Source data row to inspect.
        question: Pre-resolved question string (may be empty).
        response: Pre-resolved response string (may be empty).
        config: Ingestion config controlling text-resolution priority.

    Returns:
        Normalized, length-capped text string derived from the most specific
        available source in the row.
    """
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
    """Promote nested column/value records into top-level row fields.

    Args:
        row: Source data row to transform.
        config: Ingestion config with ``column_value_path``,
            ``column_name_field``, and ``column_value_field`` settings.

    Returns:
        A new dict with the original row fields plus any column/value entries
        promoted from the nested list, if present.
    """
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
    """Return first non-empty rendered value from candidate fields.

    Args:
        row: Source data row to search.
        fields: Ordered tuple of candidate field names.

    Returns:
        Stripped string value of the first field that is non-empty after
        rendering, or an empty string when no such field exists.
    """
    for field in fields:
        rendered = _stringify(row.get(field)).strip()
        if rendered:
            return rendered
    return ""


def _coerce_count(value: Any, *, default: int) -> int:
    """Coerce a count-like input to ``int`` with safe fallback.

    Args:
        value: Raw value to interpret as a count (may be ``bool``, ``int``,
            ``float``, ``str``, or any other type).
        default: Fallback count used for booleans, unparseable strings, and
            unrecognised types.

    Returns:
        Integer count, or *default* when coercion is not possible.
    """
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
    """Render structured values into deterministic string form.

    Args:
        value: Arbitrary Python object to convert.

    Returns:
        String representation of *value*.  ``None`` maps to ``""``, numerics
        are stringified directly, and lists/dicts are serialized as compact
        JSON with sorted keys.
    """
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
    """Normalize configured field names into a non-empty tuple.

    Args:
        value: Raw config value that may be a string, list of strings, or
            ``None``.
        fallback: Tuple to return when *value* is ``None`` or produces no
            non-empty fields.

    Returns:
        Tuple of stripped, non-empty field name strings, or *fallback* when
        the result would otherwise be empty.
    """
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
    """Normalize optional config text and return ``None`` when blank.

    Args:
        value: Raw config value to normalize.

    Returns:
        Stripped non-empty string, or ``None`` when *value* is ``None`` or
        produces an empty string after stripping.
    """
    if value is None:
        return None
    text = str(value).strip()
    return text or None

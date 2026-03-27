"""Session-aware representative selection and aggregation helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
import re

_TOKEN_RE = re.compile(r"[A-Za-z0-9가-힣]{2,}")


def _tokenize(text: str) -> list[str]:
    """Extract lower-cased alphanumeric tokens used for heuristic scoring."""
    return [token.lower() for token in _TOKEN_RE.findall(text or "") if token]


def _candidate_score(*, question: str, response: str) -> tuple[int, int, int]:
    """Score QA content by token diversity, max token length, and text length."""
    q = (question or "").strip()
    r = (response or "").strip()
    tokens = _tokenize(f"{q} {r}")
    return (
        len(set(tokens)),
        max((len(token) for token in tokens), default=0),
        len(q) + len(r),
    )


def pick_session_main_digest(
    session_rows: Sequence[Mapping[str, object]],
    *,
    selector: Callable[[str, Sequence[Mapping[str, object]]], str | None] | None = None,
) -> str | None:
    """Select a representative digest for one session's rows."""
    if not session_rows:
        return None
    session_id = str(session_rows[0].get("session_id") or "").strip()
    if selector is not None and session_id:
        try:
            chosen = str(selector(session_id, list(session_rows)) or "").strip()
        except Exception:
            chosen = ""
        if chosen and any(
            str(row.get("digest_hex") or "").strip() == chosen for row in session_rows
        ):
            return chosen
    best_digest = ""
    best_score: tuple[int, int, int] | None = None
    for row in session_rows:
        digest = str(row.get("digest_hex") or "").strip()
        if not digest:
            continue
        score = _candidate_score(
            question=str(row.get("question") or ""),
            response=str(row.get("response") or ""),
        )
        if (
            best_score is None
            or score > best_score
            or (score == best_score and digest < best_digest)
        ):
            best_score = score
            best_digest = digest
    return best_digest or None


def build_digest_counts_all_pairs(
    rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    """Aggregate non-negative counts per digest across all rows."""
    out: dict[str, int] = {}
    for row in rows:
        digest = str(row.get("digest_hex") or "").strip()
        if not digest:
            continue
        raw = row.get("count")
        if isinstance(raw, bool):
            # Design decision: Treat boolean True as a count of 1 for digest occurrences
            # (used in test_build_digest_counts_all_pairs expectations).
            count = int(raw)
        elif isinstance(raw, int):
            count = raw
        elif isinstance(raw, float):
            count = int(raw)
        elif isinstance(raw, str):
            try:
                count = int(raw)
            except ValueError:
                count = 0
        else:
            count = 0
        out[digest] = out.get(digest, 0) + max(count, 0)
    return out


def build_digest_counts_session_main_pair(
    rows: Sequence[Mapping[str, object]],
    *,
    selector: Callable[[str, Sequence[Mapping[str, object]]], str | None] | None = None,
) -> dict[str, int]:
    """Count one selected representative digest per non-empty session."""
    by_session: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        session_id = str(row.get("session_id") or "").strip()
        if session_id:
            by_session[session_id].append(row)
    out: dict[str, int] = {}
    for session_id in sorted(by_session.keys()):
        chosen = pick_session_main_digest(by_session[session_id], selector=selector)
        if chosen:
            out[chosen] = out.get(chosen, 0) + 1
    return out


def aggregate_session_topic_counts(
    rows: Iterable[dict[str, object]],
    digest_to_topic: dict[str, str],
) -> dict[tuple[str, str], int]:
    """Aggregate positive counts by ``(session_id, topic_id)``."""
    out: dict[tuple[str, str], int] = {}
    for row in rows:
        session_id = str(row.get("session_id") or "").strip()
        digest_hex = str(row.get("digest_hex") or "").strip()
        if not session_id or not digest_hex:
            continue
        topic_id = digest_to_topic.get(digest_hex)
        if not topic_id:
            continue
        raw = row.get("count")
        if isinstance(raw, bool):
            # Design decision: Unlike build_digest_counts_all_pairs, boolean values
            # are explicitly coerced to 0 here to prevent invalid aggregations.
            count = 0
        elif isinstance(raw, int):
            count = raw
        elif isinstance(raw, float):
            count = int(raw)
        elif isinstance(raw, str):
            try:
                count = int(raw)
            except ValueError:
                count = 0
        else:
            count = 0
        if count <= 0:
            continue
        key = (session_id, str(topic_id))
        out[key] = out.get(key, 0) + count
    return out


def pick_sample_sessions_for_topics(
    topic_sessions: dict[str, list[tuple[str, int]]],
    *,
    max_per_topic: int,
    max_total: int,
) -> dict[str, list[str]]:
    """Pick deterministic sample session ids per topic under global caps."""
    per_topic = max(0, int(max_per_topic))
    total_cap = max(0, int(max_total))
    remaining = total_cap
    selected: dict[str, list[str]] = {}
    for topic_id in sorted(topic_sessions.keys()):
        items = sorted(
            topic_sessions.get(topic_id) or [],
            key=lambda item: (-int(item[1] or 0), str(item[0] or "")),
        )
        picks: list[str] = []
        for session_id, _count in items:
            session = str(session_id or "").strip()
            if not session:
                continue
            if per_topic and len(picks) >= per_topic:
                break
            if total_cap and remaining <= 0:
                break
            if session not in picks:
                picks.append(session)
                remaining = remaining - 1 if total_cap else remaining
        selected[topic_id] = picks
    return selected

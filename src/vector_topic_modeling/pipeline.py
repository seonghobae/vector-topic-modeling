"""Standalone topic-modeling orchestration layer."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import TypedDict

from vector_topic_modeling.clustering import (
    Cluster,
    adaptive_greedy_cluster,
    rescue_display_dominance,
    stable_topic_id,
)
from vector_topic_modeling.providers.base import EmbeddingProvider
from vector_topic_modeling.sessioning import (
    build_digest_counts_all_pairs,
    build_digest_counts_session_main_pair,
    pick_session_main_digest,
)
from vector_topic_modeling.text import normalize_text


class PreparedRow(TypedDict):
    """Normalized row payload consumed by clustering and aggregation helpers.

    Attributes:
        document_id: Resolved string identifier for the source document.
        session_id: Session identifier string, or empty string when absent.
        question: User question text, or empty string when absent.
        response: Assistant response text, or empty string when absent.
        text: Normalized, redacted, length-capped model input text.
        digest_hex: SHA-256 hex digest of *text*.
        count: Positive occurrence count for this row.
    """

    document_id: str
    session_id: str
    question: str
    response: str
    text: str
    digest_hex: str
    count: int


@dataclass(frozen=True)
class TopicDocument:
    """Input document record for topic-model inference.

    Attributes:
        id: Unique string identifier for this document.
        text: Raw text body to be embedded and clustered.
        session_id: Optional identifier grouping related documents.
        question: Optional user question associated with the document.
        response: Optional assistant response associated with the document.
        count: Number of times this document was observed; defaults to ``1``.
        metadata: Arbitrary key-value metadata for downstream use.
    """

    id: str
    text: str
    session_id: str | None = None
    question: str | None = None
    response: str | None = None
    count: int = 1
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TopicModelConfig:
    """Runtime configuration knobs for topic modeling behavior.

    Attributes:
        similarity_threshold: Initial cosine-similarity threshold for greedy
            clustering.
        min_topics: Minimum number of topics to produce.
        max_topics: Maximum number of topics to produce.
        max_top_share: Maximum allowed fractional share for the largest topic.
        use_session_representatives: When ``True``, count only one digest per
            session for clustering input.
        display_limit: Number of topics included in the display-dominance
            evaluation prefix.
        embedding_model_name: Human-readable model name used to derive stable
            topic identifiers.
    """

    similarity_threshold: float = 0.85
    min_topics: int = 2
    max_topics: int = 30
    max_top_share: float = 0.35
    use_session_representatives: bool = False
    display_limit: int = 30
    embedding_model_name: str = "embedding-provider"


@dataclass(frozen=True)
class TopicAssignment:
    """Per-document mapping from digest to resolved topic id.

    Attributes:
        document_id: Source document identifier.
        topic_id: Resolved topic identifier for this document.
        digest_hex: SHA-256 hex digest of the document's normalized text.
    """

    document_id: str
    topic_id: str
    digest_hex: str


@dataclass(frozen=True)
class Topic:
    """Aggregated topic output for one discovered cluster.

    Attributes:
        topic_id: Stable deterministic identifier for this topic.
        total_count: Sum of document counts across all member texts.
        texts: Deduplicated text strings that belong to this topic.
    """

    topic_id: str
    total_count: int
    texts: list[str]


@dataclass(frozen=True)
class TopicModelResult:
    """Complete topic-model output including topics, assignments, and lookups.

    Attributes:
        topics: Ordered list of discovered topics.
        assignments: Per-document topic assignment records.
        session_topic_counts: Counts keyed by ``(session_id, topic_id)`` pairs.
        topic_lookup: Mapping from topic identifier to :class:`Topic` object.
    """

    topics: list[Topic]
    assignments: list[TopicAssignment]
    session_topic_counts: dict[tuple[str, str], int]
    topic_lookup: dict[str, Topic]


class TopicModeler:
    """Coordinate embedding, clustering, and assignment for topic modeling."""

    def __init__(
        self,
        *,
        embedding_provider: EmbeddingProvider,
        config: TopicModelConfig | None = None,
    ) -> None:
        """Initialize the modeler with an embedding provider and config.

        Args:
            embedding_provider: Provider that converts text lists to embedding
                vectors.
            config: Optional configuration overrides; uses
                :class:`TopicModelConfig` defaults when ``None``.
        """
        self.embedding_provider = embedding_provider
        self.config = config or TopicModelConfig()

    def fit_predict(self, documents: list[TopicDocument]) -> TopicModelResult:
        """Fit topics over input documents and return topic-level outputs.

        Args:
            documents: List of input documents to cluster into topics.

        Returns:
            A :class:`TopicModelResult` with topics, per-document assignments,
            and session-level topic counts.
        """
        prepared_rows = [self._prepare_row(document) for document in documents]
        digest_counts = self._build_digest_counts(prepared_rows)
        session_representatives = self._build_session_representatives(prepared_rows)
        unique_texts = {row["digest_hex"]: str(row["text"]) for row in prepared_rows}
        digests = list(unique_texts.keys())
        vectors = self.embedding_provider.embed(
            [unique_texts[digest] for digest in digests]
        )
        items = [
            (unique_texts[digest], vectors[index], digest_counts.get(digest, 0))
            for index, digest in enumerate(digests)
            if digest_counts.get(digest, 0) > 0
        ]
        clustering_result = adaptive_greedy_cluster(
            items,
            initial_threshold=self.config.similarity_threshold,
            max_top_share=self.config.max_top_share,
            min_clusters=self.config.min_topics,
            max_clusters=self.config.max_topics,
        )
        clusters = list(clustering_result["clusters"])
        items_by_text = {
            unique_texts[digest]: (vectors[index], digest_counts.get(digest, 0))
            for index, digest in enumerate(digests)
            if digest_counts.get(digest, 0) > 0
        }
        rescue = rescue_display_dominance(
            clusters,
            items_by_text=items_by_text,
            initial_threshold=float(clustering_result["chosen_threshold"]),
            max_display_share=self.config.max_top_share,
            display_limit=self.config.display_limit,
        )
        clusters = list(rescue["clusters"])
        digest_to_topic: dict[str, str] = {}
        topics: list[Topic] = []
        for cluster in clusters:
            topic_id = self._topic_id_for_cluster(cluster, prepared_rows)
            topic = Topic(
                topic_id=topic_id,
                total_count=int(cluster.total_count),
                texts=list(cluster.texts),
            )
            topics.append(topic)
            for text in cluster.texts:
                for digest, candidate_text in unique_texts.items():
                    if candidate_text == text:
                        digest_to_topic[digest] = topic_id
        assignments = [
            TopicAssignment(
                document_id=str(row["document_id"]),
                topic_id=self._resolve_assignment_topic_id(
                    row=row,
                    digest_to_topic=digest_to_topic,
                    session_representatives=session_representatives,
                ),
                digest_hex=str(row["digest_hex"]),
            )
            for row in prepared_rows
        ]
        session_topic_counts = self._build_session_topic_counts(
            rows=prepared_rows,
            digest_to_topic=digest_to_topic,
            session_representatives=session_representatives,
        )
        topic_lookup = {topic.topic_id: topic for topic in topics}
        return TopicModelResult(
            topics=topics,
            assignments=assignments,
            session_topic_counts=session_topic_counts,
            topic_lookup=topic_lookup,
        )

    def _prepare_row(self, document: TopicDocument) -> PreparedRow:
        """Normalize one document into a digest-addressed prepared row.

        Args:
            document: Source :class:`TopicDocument` to normalize.

        Returns:
            A :class:`PreparedRow` dict with normalized text and SHA-256
            digest.
        """
        text = normalize_text(document.text)
        digest_hex = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return {
            "document_id": document.id,
            "session_id": (document.session_id or "").strip(),
            "question": document.question or "",
            "response": document.response or "",
            "text": text,
            "digest_hex": digest_hex,
            "count": max(int(document.count), 1),
        }

    def _build_digest_counts(self, rows: list[PreparedRow]) -> dict[str, int]:
        """Build digest frequency counts using configured session strategy.

        Args:
            rows: Prepared rows produced by :meth:`_prepare_row`.

        Returns:
            Mapping from SHA-256 digest hex to aggregate document count.
        """
        if self.config.use_session_representatives:
            with_session = [row for row in rows if row["session_id"]]
            without_session = [row for row in rows if not row["session_id"]]
            counts = build_digest_counts_session_main_pair(with_session)
            for digest_hex, count in build_digest_counts_all_pairs(
                without_session
            ).items():
                counts[digest_hex] = counts.get(digest_hex, 0) + count
            return counts
        return build_digest_counts_all_pairs(rows)

    def _build_session_representatives(self, rows: list[PreparedRow]) -> dict[str, str]:
        """Pick one representative digest per session when enabled.

        Args:
            rows: Prepared rows to group by session identifier.

        Returns:
            Mapping from session identifier to its representative digest hex,
            or an empty dict when session representatives are disabled.
        """
        if not self.config.use_session_representatives:
            return {}
        by_session: dict[str, list[PreparedRow]] = {}
        for row in rows:
            session_id = row["session_id"]
            if session_id:
                by_session.setdefault(session_id, []).append(row)
        representatives: dict[str, str] = {}
        for session_id, session_rows in by_session.items():
            chosen = pick_session_main_digest(session_rows)
            if chosen:
                representatives[session_id] = chosen
        return representatives

    def _resolve_assignment_topic_id(
        self,
        *,
        row: PreparedRow,
        digest_to_topic: dict[str, str],
        session_representatives: dict[str, str],
    ) -> str:
        """Resolve a row topic by digest, then by session representative fallback.

        Args:
            row: Prepared row whose topic assignment is needed.
            digest_to_topic: Mapping from digest hex to topic identifier.
            session_representatives: Mapping from session id to representative
                digest.

        Returns:
            Topic identifier string, or ``"unassigned"`` when no match is
            found.
        """
        digest_hex = str(row["digest_hex"])
        topic_id = digest_to_topic.get(digest_hex)
        if topic_id:
            return topic_id
        session_id = row["session_id"]
        representative = session_representatives.get(session_id)
        if representative:
            return digest_to_topic.get(representative, "unassigned")
        return "unassigned"

    def _build_session_topic_counts(
        self,
        *,
        rows: list[PreparedRow],
        digest_to_topic: dict[str, str],
        session_representatives: dict[str, str],
    ) -> dict[tuple[str, str], int]:
        """Aggregate per-session counts keyed by resolved topic id.

        Args:
            rows: All prepared rows for the current run.
            digest_to_topic: Mapping from digest hex to topic identifier.
            session_representatives: Mapping from session id to representative
                digest.

        Returns:
            Dict keyed by ``(session_id, topic_id)`` tuples with summed
            document counts.
        """
        out: dict[tuple[str, str], int] = {}
        for row in rows:
            session_id = row["session_id"]
            if not session_id:
                continue
            topic_id = self._resolve_assignment_topic_id(
                row=row,
                digest_to_topic=digest_to_topic,
                session_representatives=session_representatives,
            )
            if topic_id == "unassigned":
                continue
            count = max(row["count"], 0)
            key = (session_id, topic_id)
            out[key] = out.get(key, 0) + count
        return out

    def _topic_id_for_cluster(self, cluster: Cluster, rows: list[PreparedRow]) -> str:
        """Derive a stable topic id for a cluster from sampled row digests.

        Args:
            cluster: Cluster whose stable identifier should be computed.
            rows: Full prepared-row list used to sample matching digests.

        Returns:
            A 12-character stable topic identifier derived from sorted member
            digests, the embedding model name, and the similarity threshold.
        """
        sample_sha = [
            str(row["digest_hex"])
            for row in rows
            if str(row["text"]) in set(cluster.texts)
        ]
        sample_sha.sort()
        return stable_topic_id(
            sample_sha256_hex=sample_sha,
            embedding_model=self.config.embedding_model_name,
            similarity_threshold=self.config.similarity_threshold,
        )

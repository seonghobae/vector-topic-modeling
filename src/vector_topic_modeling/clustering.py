"""Dependency-light embedding clustering helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
import json
from typing import TypedDict


def _top_share_in_prefix(clusters: list[Cluster], *, limit: int) -> tuple[int, float]:
    """Return total count and dominant-share among the first ``limit`` clusters.

    Args:
        clusters: Ordered list of clusters to evaluate.
        limit: Maximum number of clusters from the front of the list to consider.

    Returns:
        A ``(total, share)`` tuple where *total* is the combined document count
        of the prefix and *share* is the fraction held by the largest cluster.
    """
    n = max(int(limit), 0)
    prefix = clusters[:n] if n else []
    counts = [max(int(cluster.total_count), 0) for cluster in prefix]
    total = sum(counts)
    if total <= 0:
        return 0, 0.0
    return total, float(max(counts) / total)


def _stable_cluster_sort_key(cluster: Cluster) -> tuple[int, str]:
    """Build a deterministic sort key by size then lexical tie-break.

    Args:
        cluster: The cluster whose sort key should be derived.

    Returns:
        A ``(negated_total_count, lexically_smallest_text)`` tuple that
        produces a stable descending-by-size ordering when used with
        :func:`list.sort`.
    """
    tie = min((str(text) for text in cluster.texts), default="")
    return (-int(cluster.total_count), tie)


def _cluster_stats(clusters: list[Cluster]) -> tuple[int, float]:
    """Compute cluster count and global share of the largest cluster.

    Args:
        clusters: List of clusters to evaluate.

    Returns:
        A ``(count, top_share)`` tuple where *count* is the number of clusters
        and *top_share* is the fraction of total documents in the largest cluster.
    """
    if not clusters:
        return 0, 0.0
    counts = [max(int(cluster.total_count), 0) for cluster in clusters]
    total = sum(counts)
    if total <= 0:
        return len(clusters), 0.0
    return len(clusters), float(max(counts) / total)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity for two equal-length vectors.

    Args:
        a: First dense embedding vector.
        b: Second dense embedding vector; must be the same length as *a*.

    Returns:
        Cosine similarity in ``[-1.0, 1.0]``, or ``0.0`` when either input is
        empty, the lengths differ, or a vector has zero norm.
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b, strict=True):
        dot += float(x) * float(y)
        norm_a += float(x) * float(x)
        norm_b += float(y) * float(y)
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / ((norm_a**0.5) * (norm_b**0.5))


@dataclass(frozen=True)
class Cluster:
    """A clustered group of texts with centroid and aggregate count.

    Attributes:
        centroid: Averaged embedding vector representing this cluster.
        texts: Deduplicated text strings assigned to this cluster.
        total_count: Aggregate document count across all member texts.
    """

    centroid: list[float]
    texts: list[str]
    total_count: int


class AdaptiveGreedyClusterResult(TypedDict):
    """Result payload for adaptive greedy clustering.

    Attributes:
        clusters: Final cluster list produced by the search.
        chosen_threshold: Similarity threshold that was selected.
        cluster_count: Number of clusters in the result.
        top_cluster_share: Share held by the largest cluster.
        ok: ``True`` when all constraints were fully satisfied.
    """

    clusters: list[Cluster]
    chosen_threshold: float
    cluster_count: int
    top_cluster_share: float
    ok: bool


class RescueDisplayDominanceResult(TypedDict):
    """Result payload for dominance-rescue post-processing.

    Attributes:
        clusters: Cluster list after the rescue pass.
        rescued: ``True`` when the display share was reduced.
        attempts: Number of threshold candidates evaluated.
        rescue_threshold: Threshold that produced the best improvement, or
            ``None`` when no improvement was found.
        cluster_count_before: Cluster count before the rescue pass.
        cluster_count_after: Cluster count after the rescue pass.
        top_cluster_share_before: Top-cluster share across all clusters before.
        top_cluster_share_after: Top-cluster share across all clusters after.
        display_top_share_before: Top-cluster share in the display prefix before.
        display_top_share_after: Top-cluster share in the display prefix after.
    """

    clusters: list[Cluster]
    rescued: bool
    attempts: int
    rescue_threshold: float | None
    cluster_count_before: int
    cluster_count_after: int
    top_cluster_share_before: float
    top_cluster_share_after: float
    display_top_share_before: float
    display_top_share_after: float


def _avg_vectors(
    *, prev_centroid: list[float], new_vector: list[float], prev_weight: float
) -> list[float]:
    """Update a centroid with one additional vector using weighted averaging.

    Args:
        prev_centroid: Current centroid vector.
        new_vector: New member vector to incorporate.
        prev_weight: Weight to assign to *prev_centroid* relative to
            *new_vector* (weight 1.0).

    Returns:
        Updated centroid vector.  Returns *prev_centroid* unchanged when the
        two vectors have different lengths, and returns a copy of *new_vector*
        when *prev_centroid* is empty.
    """
    if not prev_centroid:
        return list(new_vector)
    if len(prev_centroid) != len(new_vector):
        return list(prev_centroid)
    weight_prev = max(prev_weight, 0.0)
    weight_sum = weight_prev + 1.0
    return [
        (p * weight_prev + v) / weight_sum
        for p, v in zip(prev_centroid, new_vector, strict=True)
    ]


def greedy_cluster(
    items: Iterable[tuple[str, list[float], int]],
    *,
    similarity_threshold: float,
    max_clusters: int | None = None,
) -> list[Cluster]:
    """Cluster texts greedily by first centroid crossing the similarity threshold.

    Args:
        items: Iterable of ``(text, vector, count)`` triples to cluster.
        similarity_threshold: Minimum cosine similarity to merge into an
            existing cluster.  Clamped to ``[0.0, 1.0]``.
        max_clusters: Optional hard cap on the number of clusters.  When the
            cap is reached, new items are assigned to their closest centroid.

    Returns:
        List of :class:`Cluster` objects in insertion order.
    """
    threshold = min(max(float(similarity_threshold), 0.0), 1.0)
    centroids: list[list[float]] = []
    members: list[list[str]] = []
    counts: list[int] = []
    max_k = None if max_clusters is None else max(int(max_clusters), 1)

    for text, vector, count in items:
        assigned: int | None = None
        best_idx: int | None = None
        best_similarity = -1.0
        for idx, centroid in enumerate(centroids):
            similarity = cosine_similarity(centroid, vector)
            if similarity > best_similarity:
                best_similarity = similarity
                best_idx = idx
            if similarity >= threshold:
                assigned = idx
                break
        if (
            assigned is None
            and centroids
            and max_k is not None
            and len(centroids) >= max_k
        ):
            assigned = best_idx if best_idx is not None else 0
        if assigned is None:
            centroids.append(list(vector))
            members.append([text])
            counts.append(int(count))
        else:
            members[assigned].append(text)
            counts[assigned] += int(count)
            centroids[assigned] = _avg_vectors(
                prev_centroid=centroids[assigned],
                new_vector=vector,
                prev_weight=float(max(len(members[assigned]) - 1, 1)),
            )

    return [
        Cluster(centroid=centroid, texts=texts, total_count=int(total_count))
        for centroid, texts, total_count in zip(centroids, members, counts, strict=True)
    ]


def adaptive_greedy_cluster(
    items: Iterable[tuple[str, list[float], int]],
    *,
    initial_threshold: float,
    max_top_share: float,
    min_clusters: int,
    max_clusters: int,
    step: float = 0.02,
    tries: int = 6,
) -> AdaptiveGreedyClusterResult:
    """Search thresholds to satisfy topic-count and top-share constraints.

    Args:
        items: Iterable of ``(text, vector, count)`` triples to cluster.
        initial_threshold: Starting cosine-similarity threshold.
        max_top_share: Maximum allowed fractional share for the largest cluster.
        min_clusters: Minimum acceptable cluster count.
        max_clusters: Maximum acceptable cluster count.
        step: Threshold increment applied on each iteration.
        tries: Maximum number of threshold candidates to evaluate.

    Returns:
        An :class:`AdaptiveGreedyClusterResult` dict.  The ``ok`` field is
        ``True`` when a threshold satisfying all constraints was found.
    """
    threshold = float(initial_threshold)
    max_share = float(max_top_share)
    min_k = max(int(min_clusters), 1)
    max_k = max(int(max_clusters), min_k)
    step_value = abs(float(step)) if float(step) else 0.02
    attempts = max(int(tries), 1)
    items_list = list(items)
    best: AdaptiveGreedyClusterResult | None = None
    best_penalty: float | None = None

    for i in range(attempts):
        candidate_threshold = min(max(threshold + (step_value * i), 0.0), 1.0)
        clusters = greedy_cluster(
            items_list,
            similarity_threshold=candidate_threshold,
            max_clusters=max_k,
        )
        cluster_count, top_share = _cluster_stats(clusters)
        if min_k <= cluster_count <= max_k and top_share <= max_share:
            return {
                "clusters": clusters,
                "chosen_threshold": candidate_threshold,
                "cluster_count": cluster_count,
                "top_cluster_share": top_share,
                "ok": True,
            }
        penalty = 0.0
        if top_share > max_share:
            penalty += (top_share - max_share) * 10.0
        if cluster_count < min_k:
            penalty += (min_k - cluster_count) / float(min_k)
        if best_penalty is None or penalty < best_penalty:
            best_penalty = penalty
            best = {
                "clusters": clusters,
                "chosen_threshold": candidate_threshold,
                "cluster_count": cluster_count,
                "top_cluster_share": top_share,
                "ok": False,
            }

    return best or {
        "clusters": [],
        "chosen_threshold": threshold,
        "cluster_count": 0,
        "top_cluster_share": 0.0,
        "ok": False,
    }


def rescue_display_dominance(
    clusters: list[Cluster],
    *,
    items_by_text: dict[str, tuple[list[float], int]],
    initial_threshold: float,
    max_display_share: float = 0.35,
    display_limit: int = 30,
    step: float = 0.02,
    tries: int = 6,
) -> RescueDisplayDominanceResult:
    """Split a dominant first cluster to reduce top-share in display prefix.

    Args:
        clusters: Input cluster list sorted by descending size.
        items_by_text: Mapping from text to ``(vector, count)`` for
            re-clustering.
        initial_threshold: Baseline cosine-similarity threshold.
        max_display_share: Target maximum share for the leading cluster in the
            display prefix.
        display_limit: Number of clusters in the display prefix to evaluate.
        step: Threshold increment applied on each rescue attempt.
        tries: Maximum number of rescue attempts.

    Returns:
        A :class:`RescueDisplayDominanceResult` dict describing before/after
        cluster statistics and whether the rescue reduced display dominance.
    """
    in_clusters = list(clusters or [])
    in_clusters.sort(key=_stable_cluster_sort_key)
    cluster_count_before, top_share_before = _cluster_stats(in_clusters)
    _, display_share_before = _top_share_in_prefix(in_clusters, limit=display_limit)
    max_share = min(max(float(max_display_share), 0.01), 1.0)
    if not in_clusters or display_share_before <= max_share:
        return {
            "clusters": in_clusters,
            "rescued": False,
            "attempts": 0,
            "rescue_threshold": None,
            "cluster_count_before": cluster_count_before,
            "cluster_count_after": cluster_count_before,
            "top_cluster_share_before": top_share_before,
            "top_cluster_share_after": top_share_before,
            "display_top_share_before": display_share_before,
            "display_top_share_after": display_share_before,
        }

    threshold = min(max(float(initial_threshold), 0.0), 1.0)
    step_value = abs(float(step)) if float(step) else 0.02
    attempts = max(int(tries), 1)
    best_clusters = list(in_clusters)
    best_display_share = float(display_share_before)
    rescue_threshold: float | None = None

    for i in range(attempts):
        candidate_threshold = min(max(threshold + (step_value * (i + 1)), 0.0), 1.0)
        dominant = best_clusters[0]
        members: list[tuple[str, list[float], int]] = []
        for raw_text in dominant.texts:
            vector_count = items_by_text.get(str(raw_text))
            if vector_count is None:
                continue
            vector, count = vector_count
            members.append((str(raw_text), vector, int(count)))
        if len(members) < 2:
            continue
        members.sort(key=lambda item: (-int(item[2] or 0), item[0]))
        subclusters = greedy_cluster(members, similarity_threshold=candidate_threshold)
        if len(subclusters) <= 1:
            continue
        candidate = [*subclusters, *best_clusters[1:]]
        candidate.sort(key=_stable_cluster_sort_key)
        _, candidate_display_share = _top_share_in_prefix(
            candidate, limit=display_limit
        )
        if candidate_display_share <= best_display_share:
            best_clusters = candidate
            best_display_share = float(candidate_display_share)
            rescue_threshold = candidate_threshold
        if best_display_share <= max_share:
            break

    cluster_count_after, top_share_after = _cluster_stats(best_clusters)
    return {
        "clusters": best_clusters,
        "rescued": best_display_share < float(display_share_before),
        "attempts": attempts,
        "rescue_threshold": rescue_threshold,
        "cluster_count_before": cluster_count_before,
        "cluster_count_after": cluster_count_after,
        "top_cluster_share_before": top_share_before,
        "top_cluster_share_after": top_share_after,
        "display_top_share_before": display_share_before,
        "display_top_share_after": best_display_share,
    }


def stable_topic_id(
    *, sample_sha256_hex: list[str], embedding_model: str, similarity_threshold: float
) -> str:
    """Derive a deterministic short topic identifier from stable cluster metadata.

    Args:
        sample_sha256_hex: Sorted list of SHA-256 digest hex strings sampled
            from cluster member documents.
        embedding_model: Name of the embedding model used to produce the
            vectors.
        similarity_threshold: Cosine-similarity threshold used during
            clustering.

    Returns:
        A 12-character hexadecimal prefix of the SHA-256 hash over the
        serialized metadata payload.
    """
    payload = {
        "v": 1,
        "sample_sha256": list(sample_sha256_hex),
        "embedding_model": str(embedding_model),
        "threshold": float(similarity_threshold),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:12]


def match_clusters_by_centroid(
    *,
    current_clusters: list[Cluster],
    previous_clusters: list[Cluster],
    match_threshold: float,
) -> dict[int, int]:
    """Greedily match current clusters to previous clusters by centroid similarity.

    Args:
        current_clusters: Clusters from the current run (indexed as keys).
        previous_clusters: Clusters from a prior run (indexed as values).
        match_threshold: Minimum cosine similarity for a valid match.

    Returns:
        Mapping from current-cluster index to previous-cluster index.  An
        index of ``-1`` means no sufficiently similar previous cluster was
        found.
    """
    threshold = min(max(float(match_threshold), 0.0), 1.0)
    pairs: list[tuple[float, int, int]] = []
    for i, current in enumerate(current_clusters):
        for j, previous in enumerate(previous_clusters):
            pairs.append((cosine_similarity(current.centroid, previous.centroid), i, j))
    pairs.sort(reverse=True)
    used_current: set[int] = set()
    used_previous: set[int] = set()
    mapping: dict[int, int] = dict.fromkeys(range(len(current_clusters)), -1)
    for similarity, i, j in pairs:
        if similarity < threshold:
            break
        if i in used_current or j in used_previous:
            continue
        mapping[i] = j
        used_current.add(i)
        used_previous.add(j)
    return mapping

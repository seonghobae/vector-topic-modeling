"""Mathematical evaluation metrics for clustering without heavy dependencies."""

from __future__ import annotations


from typing import TypedDict
from vector_topic_modeling.clustering import cosine_similarity


class ClusteringMetrics(TypedDict):
    """Comprehensive result payload for mathematical evaluation metrics."""

    silhouette_score: float
    calinski_harabasz_score: float
    davies_bouldin_score: float
    topic_coherence: dict[str, float]


class SilhouetteResult(TypedDict):
    """Result payload for silhouette score evaluation."""

    overall_score: float
    cluster_scores: dict[str, float]


LARGE_DB_PENALTY = 1_000_000.0


def calculate_silhouette_score(
    clusters: list[tuple[str, list[str]]],
    vectors_by_text: dict[str, list[float]],
) -> SilhouetteResult:
    """Calculate the Silhouette Score for the given clusters using cosine distance.

    Args:
        clusters: A list of tuples containing (cluster_id, list_of_texts).
        vectors_by_text: A mapping from text to its embedding vector.

    Returns:
        The overall average silhouette score and per-cluster scores.
        Cosine distance is calculated as (1.0 - cosine_similarity).
    """
    if len(clusters) < 2:
        return {"overall_score": 0.0, "cluster_scores": {}}

    cluster_vectors: list[list[list[float]]] = []
    cluster_ids: list[str] = []

    for cid, texts in clusters:
        vecs = []
        for text in texts:
            if text in vectors_by_text:
                vecs.append(vectors_by_text[text])
        cluster_vectors.append(vecs)
        cluster_ids.append(cid)

    if sum(1 for vecs in cluster_vectors if vecs) < 2:
        return {"overall_score": 0.0, "cluster_scores": {}}

    overall_scores: list[float] = []
    cluster_score_map: dict[str, float] = {}

    for i, vecs_i in enumerate(cluster_vectors):
        if not vecs_i:
            continue

        cluster_total_score = 0.0
        valid_points = 0

        for v_idx, v in enumerate(vecs_i):
            if len(vecs_i) == 1:
                s_i = 0.0
                cluster_total_score += s_i
                overall_scores.append(s_i)
                valid_points += 1
                continue

            a_i = sum(
                (1.0 - cosine_similarity(v, other_v))
                for other_idx, other_v in enumerate(vecs_i)
                if other_idx != v_idx
            ) / (len(vecs_i) - 1)

            b_i = float("inf")
            for j, vecs_j in enumerate(cluster_vectors):
                if i == j or not vecs_j:
                    continue
                mean_dist = sum(
                    (1.0 - cosine_similarity(v, other_v)) for other_v in vecs_j
                ) / len(vecs_j)
                if mean_dist < b_i:
                    b_i = mean_dist

            max_ab = max(a_i, b_i)
            s_i = (b_i - a_i) / max_ab if max_ab > 0 else 0.0

            cluster_total_score += s_i
            overall_scores.append(s_i)
            valid_points += 1

        cluster_score_map[cluster_ids[i]] = cluster_total_score / valid_points

    overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
    return {"overall_score": overall, "cluster_scores": cluster_score_map}


def compute_centroid(vectors: list[list[float]]) -> list[float]:
    """Calculate the centroid of a list of vectors."""
    if not vectors:
        return []
    dims = len(vectors[0])
    centroid = [0.0] * dims
    for v in vectors:
        for i in range(dims):
            centroid[i] += v[i]
    count = len(vectors)
    return [x / count for x in centroid]


def calculate_extended_metrics(
    clusters: list[tuple[str, list[str]]],
    vectors_by_text: dict[str, list[float]],
    precomputed_silhouette: float | None = None,
) -> ClusteringMetrics:
    """Calculate Silhouette, Calinski-Harabasz, Davies-Bouldin, and Coherence metrics."""
    if len(clusters) < 2:
        return {
            "silhouette_score": 0.0,
            "calinski_harabasz_score": 0.0,
            "davies_bouldin_score": 0.0,
            "topic_coherence": {},
        }

    cluster_vectors: list[list[list[float]]] = []
    cluster_ids: list[str] = []
    all_vectors: list[list[float]] = []

    for cid, texts in clusters:
        vecs = []
        for text in texts:
            if text in vectors_by_text:
                v = vectors_by_text[text]
                vecs.append(v)
                all_vectors.append(v)
        cluster_vectors.append(vecs)
        cluster_ids.append(cid)

    if not all_vectors:
        return {
            "silhouette_score": 0.0,
            "calinski_harabasz_score": 0.0,
            "davies_bouldin_score": 0.0,
            "topic_coherence": {},
        }

    global_centroid = compute_centroid(all_vectors)
    centroids = [compute_centroid(cv) for cv in cluster_vectors]

    # 1. Silhouette Score
    if precomputed_silhouette is None:
        silhouette_score = calculate_silhouette_score(clusters, vectors_by_text)[
            "overall_score"
        ]
    else:
        silhouette_score = precomputed_silhouette

    # 2. Topic Coherence (Intra-cluster Similarity) & Scatter for DB
    topic_coherence: dict[str, float] = {}
    scatter: list[float] = []
    within_cluster_variance = 0.0

    for i, vecs in enumerate(cluster_vectors):
        if not vecs:
            topic_coherence[cluster_ids[i]] = 0.0
            scatter.append(0.0)
            continue

        coherence_sum = 0.0
        variance_sum = 0.0
        for v in vecs:
            sim = cosine_similarity(v, centroids[i])
            dist = max(0.0, 1.0 - sim)  # Ensure non-negative distance
            coherence_sum += sim
            variance_sum += dist

        topic_coherence[cluster_ids[i]] = coherence_sum / len(vecs)
        scatter.append(variance_sum / len(vecs))
        within_cluster_variance += variance_sum

    # 3. Calinski-Harabasz Index
    between_cluster_variance = 0.0
    for i, vecs in enumerate(cluster_vectors):
        if not vecs:
            continue
        dist_to_global = max(
            0.0, 1.0 - cosine_similarity(centroids[i], global_centroid)
        )
        between_cluster_variance += len(vecs) * dist_to_global

    n_samples = len(all_vectors)
    k_clusters = sum(1 for v in cluster_vectors if v)

    if within_cluster_variance == 0.0 or k_clusters < 2 or n_samples <= k_clusters:
        ch_score = 0.0
    else:
        ch_score = (between_cluster_variance / (k_clusters - 1)) / (
            within_cluster_variance / (n_samples - k_clusters)
        )

    # 4. Davies-Bouldin Index
    db_ratios: list[float] = []
    for i in range(len(cluster_vectors)):
        if not cluster_vectors[i]:
            continue
        max_r = 0.0
        found_other = False
        for j in range(len(cluster_vectors)):
            if i == j or not cluster_vectors[j]:
                continue
            dist_ij = max(0.0, 1.0 - cosine_similarity(centroids[i], centroids[j]))
            if dist_ij == 0.0:
                # Strong finite penalty for overlapping centroids.
                r_ij = LARGE_DB_PENALTY
            else:
                r_ij = (scatter[i] + scatter[j]) / dist_ij
            max_r = max(max_r, r_ij)
            found_other = True

        if found_other:
            db_ratios.append(max_r)

    db_score = sum(db_ratios) / len(db_ratios) if db_ratios else 0.0

    return {
        "silhouette_score": silhouette_score,
        "calinski_harabasz_score": ch_score,
        "davies_bouldin_score": db_score,
        "topic_coherence": topic_coherence,
    }

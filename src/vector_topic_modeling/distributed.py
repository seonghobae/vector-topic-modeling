"""Distributed computation using Valkey for evaluation metrics."""

from __future__ import annotations

import json
import importlib
import uuid
import threading
from typing import Any

from vector_topic_modeling.evaluation import (
    ClusteringMetrics,
    calculate_extended_metrics,
)
from vector_topic_modeling.clustering import cosine_similarity

_valkey: Any
try:
    _valkey = importlib.import_module("valkey")
    VALKEY_AVAILABLE = True
except ImportError:
    _valkey = None
    VALKEY_AVAILABLE = False

valkey: Any = _valkey


def calculate_distributed_metrics(
    clusters: list[tuple[str, list[str]]],
    vectors_by_text: dict[str, list[float]],
    valkey_url: str = "redis://localhost:6379",
    num_workers: int = 4,
    precomputed_silhouette: float | None = None,
) -> ClusteringMetrics:
    """Calculate extended metrics using Valkey for distributed distance calculation."""
    if not VALKEY_AVAILABLE:
        raise ImportError(
            "Valkey is not installed. Install with `pip install .[distributed]`."
        )

    # Extended metrics (CH, DB, Coherence) are O(K*N) or O(K^2), so we do them locally
    # The silhouette score is O(N^2), so we distribute it.
    base_metrics = calculate_extended_metrics(
        clusters,
        vectors_by_text,
        precomputed_silhouette=precomputed_silhouette,
    )

    if len(clusters) < 2:
        return base_metrics

    # Check if we have valid vectors to compute silhouette
    has_vectors = False
    for _, texts in clusters:
        for text in texts:
            if text in vectors_by_text:
                has_vectors = True
                break
        if has_vectors:
            break

    if not has_vectors:
        return base_metrics

    # If silhouette was already computed by the pipeline, avoid duplicating
    # distributed O(N^2) work and reuse the precomputed value.
    if precomputed_silhouette is not None:
        return base_metrics

    client = valkey.Valkey.from_url(valkey_url, decode_responses=True)
    job_id = str(uuid.uuid4())

    # Flatten vectors and create cluster index mapping
    flat_vectors: list[list[float]] = []
    cluster_indices: list[list[int]] = []
    cluster_ids: list[str] = []

    for cid, texts in clusters:
        c_idx = []
        for text in texts:
            if text in vectors_by_text:
                c_idx.append(len(flat_vectors))
                flat_vectors.append(vectors_by_text[text])
        cluster_indices.append(c_idx)
        cluster_ids.append(cid)

    non_empty_clusters = sum(1 for indices in cluster_indices if indices)
    if non_empty_clusters < 2:
        base_metrics["silhouette_score"] = 0.0
        return base_metrics

    # Store data in Valkey
    vectors_key = f"{job_id}:vectors"
    clusters_key = f"{job_id}:clusters"
    tasks_key = f"{job_id}:tasks"
    results_key = f"{job_id}:results"

    results: dict[str, str] = {}
    try:
        client.set(vectors_key, json.dumps(flat_vectors))
        client.set(clusters_key, json.dumps(cluster_indices))

        tasks = list(range(len(flat_vectors)))
        client.rpush(tasks_key, *tasks)

        # Start workers
        threads = []
        for _ in range(num_workers):
            t = threading.Thread(target=_worker_loop, args=(valkey_url, job_id))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # Read results
        results = client.hgetall(results_key)
    finally:
        # Clean up
        client.delete(vectors_key)
        client.delete(clusters_key)
        client.delete(tasks_key)
        client.delete(results_key)

    if not results or len(results) != len(flat_vectors):
        # Fallback if workers failed
        return base_metrics

    # Aggregate results into overall silhouette score
    s_scores = []
    for s_val in results.values():
        s_scores.append(float(s_val))

    base_metrics["silhouette_score"] = sum(s_scores) / len(s_scores)

    return base_metrics


def _worker_loop(valkey_url: str, job_id: str) -> None:
    """Run a worker loop to process distance computations.

    Args:
        valkey_url: The Valkey instance URL.
        job_id: The job ID to process.
    """
    client = valkey.Valkey.from_url(valkey_url, decode_responses=True)
    vectors_key = f"{job_id}:vectors"
    clusters_key = f"{job_id}:clusters"
    tasks_key = f"{job_id}:tasks"
    results_key = f"{job_id}:results"

    vectors_json = client.get(vectors_key)
    clusters_json = client.get(clusters_key)

    if not vectors_json or not clusters_json:
        return

    vectors: list[list[float]] = json.loads(vectors_json)
    cluster_indices: list[list[int]] = json.loads(clusters_json)

    # Map index to its cluster index
    idx_to_cluster = {}
    for c_idx, indices in enumerate(cluster_indices):
        for idx in indices:
            idx_to_cluster[idx] = c_idx

    while True:
        task = client.lpop(tasks_key)
        if task is None:
            break

        i = int(task)
        v_i = vectors[i]
        c_i = idx_to_cluster[i]

        # Calculate a_i
        same_cluster_indices = cluster_indices[c_i]
        if len(same_cluster_indices) == 1:
            client.hset(results_key, str(i), "0.0")
            continue

        a_i = sum(
            1.0 - cosine_similarity(v_i, vectors[j])
            for j in same_cluster_indices
            if j != i
        ) / (len(same_cluster_indices) - 1)

        # Calculate b_i
        b_i = float("inf")
        for c_j, other_cluster_indices in enumerate(cluster_indices):
            if c_i == c_j or not other_cluster_indices:
                continue
            mean_dist = sum(
                1.0 - cosine_similarity(v_i, vectors[j]) for j in other_cluster_indices
            ) / len(other_cluster_indices)
            if mean_dist < b_i:
                b_i = mean_dist

        if b_i == float("inf"):
            b_i = 0.0

        max_ab = max(a_i, b_i)
        s_i = (b_i - a_i) / max_ab if max_ab > 0 else 0.0

        client.hset(results_key, str(i), str(s_i))

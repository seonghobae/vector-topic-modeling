from __future__ import annotations

from collections.abc import Sequence

from vector_topic_modeling.clustering import (
    Cluster,
    adaptive_greedy_cluster,
    cosine_similarity,
    greedy_cluster,
    match_clusters_by_centroid,
    rescue_display_dominance,
    stable_topic_id,
)


def _top_share_within_prefix(clusters: Sequence[object], *, limit: int) -> float:
    top_n = max(int(limit), 0)
    prefix = list(clusters)[:top_n] if top_n else []
    counts = [int(getattr(c, "total_count", 0) or 0) for c in prefix]
    total = sum(max(c, 0) for c in counts)
    if total <= 0:
        return 0.0
    return max(counts) / float(total)


def _one_hot(*, dim: int, idx: int) -> list[float]:
    return [1.0 if j == idx else 0.0 for j in range(int(dim))]


def test_cosine_similarity_basic() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_greedy_cluster_groups_similar_vectors() -> None:
    items = [
        ("a", [1.0, 0.0], 10),
        ("b", [0.9, 0.1], 3),
        ("c", [0.0, 1.0], 5),
    ]
    clusters = greedy_cluster(items, similarity_threshold=0.8)
    clusters_sorted = sorted(clusters, key=lambda c: c.total_count, reverse=True)
    assert clusters_sorted[0].total_count == 13
    assert set(clusters_sorted[0].texts) == {"a", "b"}
    assert clusters_sorted[1].texts == ["c"]


def test_stable_topic_id_is_deterministic() -> None:
    t1 = stable_topic_id(
        sample_sha256_hex=["aa" * 32, "bb" * 32],
        embedding_model="text-embedding-3-large",
        similarity_threshold=0.85,
    )
    t2 = stable_topic_id(
        sample_sha256_hex=["aa" * 32, "bb" * 32],
        embedding_model="text-embedding-3-large",
        similarity_threshold=0.85,
    )
    assert t1 == t2
    assert len(t1) == 12


def test_match_clusters_by_centroid_picks_best_match() -> None:
    current = greedy_cluster(
        [("x", [1.0, 0.0], 10), ("y", [0.0, 1.0], 7)],
        similarity_threshold=0.8,
    )
    prev = greedy_cluster(
        [("p", [0.95, 0.05], 4), ("q", [0.05, 0.95], 20)],
        similarity_threshold=0.8,
    )
    mapping = match_clusters_by_centroid(
        current_clusters=current,
        previous_clusters=prev,
        match_threshold=0.7,
    )
    assert mapping[0] == 0
    assert mapping[1] == 1


def test_adaptive_greedy_cluster_can_avoid_single_cluster_collapse() -> None:
    items = [
        ("a", [1.0, 0.0], 10),
        ("b", [0.829, 0.559], 10),
        ("c", [0.829, -0.559], 10),
    ]
    res = adaptive_greedy_cluster(
        items,
        initial_threshold=0.80,
        max_top_share=0.60,
        min_clusters=2,
        max_clusters=100,
        step=0.02,
        tries=6,
    )
    assert isinstance(res.get("chosen_threshold"), float)
    assert res["chosen_threshold"] >= 0.84
    assert res["cluster_count"] >= 2
    assert res["top_cluster_share"] <= 0.60


def test_rescue_display_dominance_splits_dominant_cluster_in_display_prefix() -> None:
    from vector_topic_modeling import clustering as qtm

    a_vec = [1.0, 0.0]
    b_vec = [0.86, 0.510296]
    big_texts: list[str] = []
    items_by_text: dict[str, tuple[list[float], int]] = {}
    for i in range(25):
        text = f"big_a_{i:02d}"
        big_texts.append(text)
        items_by_text[text] = (a_vec, 1)
    for i in range(24):
        text = f"big_b_{i:02d}"
        big_texts.append(text)
        items_by_text[text] = (b_vec, 1)

    big_cluster = qtm.Cluster(centroid=[0.0, 0.0], texts=big_texts, total_count=49)
    tail_clusters: list[qtm.Cluster] = []
    for i in range(60):
        text = f"tail_{i:02d}"
        items_by_text[text] = ([0.0, 1.0], 1)
        tail_clusters.append(
            qtm.Cluster(centroid=[0.0, 1.0], texts=[text], total_count=1)
        )

    clusters = [big_cluster, *tail_clusters]
    clusters.sort(key=lambda c: c.total_count, reverse=True)
    assert _top_share_within_prefix(clusters, limit=30) > 0.35

    rescued = qtm.rescue_display_dominance(
        clusters,
        items_by_text=items_by_text,
        initial_threshold=0.85,
        max_display_share=0.35,
        display_limit=30,
        step=0.02,
        tries=6,
    )
    rescued_clusters = list(rescued["clusters"])
    assert _top_share_within_prefix(rescued_clusters, limit=30) <= 0.35


def test_greedy_cluster_with_max_clusters_caps_k_for_orthogonal_items() -> None:
    items = [(f"t{i}", _one_hot(dim=12, idx=i), 1) for i in range(10)]
    assert len(greedy_cluster(items, similarity_threshold=0.75, max_clusters=3)) == 3


def test_greedy_cluster_with_max_clusters_preserves_total_count() -> None:
    items = [(f"t{i}", _one_hot(dim=12, idx=i), i + 1) for i in range(10)]
    total_in = sum(cnt for _text, _vector, cnt in items)
    total_out = sum(
        c.total_count
        for c in greedy_cluster(items, similarity_threshold=0.75, max_clusters=3)
    )
    assert total_out == total_in


def test_adaptive_greedy_cluster_respects_max_clusters_and_is_deterministic() -> None:
    items = [(f"t{i}", _one_hot(dim=12, idx=i), 1) for i in range(10)]
    res1 = adaptive_greedy_cluster(
        items,
        initial_threshold=0.90,
        max_top_share=1.0,
        min_clusters=2,
        max_clusters=3,
        step=0.02,
        tries=3,
    )
    res2 = adaptive_greedy_cluster(
        items,
        initial_threshold=0.90,
        max_top_share=1.0,
        min_clusters=2,
        max_clusters=3,
        step=0.02,
        tries=3,
    )
    assert len(list(res1["clusters"])) <= 3
    assert list(res1["clusters"]) == list(res2["clusters"])


def test_adaptive_greedy_cluster_penalizes_cluster_count_when_top_share_is_within_limit() -> (
    None
):
    res = adaptive_greedy_cluster(
        [("only", [1.0, 0.0], 3)],
        initial_threshold=0.9,
        max_top_share=1.0,
        min_clusters=2,
        max_clusters=3,
        step=0.1,
        tries=1,
    )

    assert res["ok"] is False
    assert res["cluster_count"] == 1
    assert res["top_cluster_share"] == 1.0


def test_rescue_display_dominance_keeps_previous_best_when_split_candidate_is_worse() -> (
    None
):
    dominant_texts = [f"a{i}" for i in range(5)] + [f"b{i}" for i in range(5)]
    clusters = [
        Cluster(centroid=[0.0, 0.0], texts=dominant_texts, total_count=10),
        Cluster(centroid=[0.0, 1.0], texts=["runner"], total_count=9),
    ]
    items_by_text = {
        **{f"a{i}": ([1.0, 0.0], 1) for i in range(5)},
        **{f"b{i}": ([0.0, 1.0], 1) for i in range(5)},
        "runner": ([0.0, 1.0], 9),
    }

    res = rescue_display_dominance(
        clusters,
        items_by_text=items_by_text,
        initial_threshold=0.0,
        max_display_share=0.4,
        display_limit=2,
        step=0.5,
        tries=2,
    )

    assert res["rescued"] is False
    assert res["rescue_threshold"] is None
    assert res["display_top_share_after"] == res["display_top_share_before"]
    assert [cluster.total_count for cluster in res["clusters"]] == [10, 9]

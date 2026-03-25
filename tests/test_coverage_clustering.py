from vector_topic_modeling.clustering import (
    _top_share_in_prefix,
    _cluster_stats,
    cosine_similarity,
    _avg_vectors,
    adaptive_greedy_cluster,
    rescue_display_dominance,
    match_clusters_by_centroid,
    Cluster,
)


def test_top_share_in_prefix_edge_cases():
    assert _top_share_in_prefix([], limit=5) == (0, 0.0)
    assert _top_share_in_prefix(
        [Cluster(texts=[], total_count=-1, centroid=[])], limit=5
    ) == (0, 0.0)


def test_cluster_stats_edge_cases():
    assert _cluster_stats([]) == (0, 0.0)
    assert _cluster_stats([Cluster(texts=[], total_count=-1, centroid=[])]) == (1, 0.0)


def test_cosine_similarity_edge_cases():
    assert cosine_similarity([], []) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert cosine_similarity([0.0], [0.0]) == 0.0


def test_avg_vectors_edge_cases():
    assert _avg_vectors(prev_centroid=[], new_vector=[1.0, 2.0], prev_weight=1.0) == [
        1.0,
        2.0,
    ]
    assert _avg_vectors(
        prev_centroid=[1.0], new_vector=[1.0, 2.0], prev_weight=1.0
    ) == [1.0]
    assert _avg_vectors(prev_centroid=[1.0], new_vector=[2.0], prev_weight=-1.0) == [
        2.0
    ]


def test_adaptive_greedy_cluster_max_k():
    items = [
        ("a", [1.0, 0.0], 1),
        ("b", [0.0, 1.0], 1),
    ]
    # cluster_count > max_clusters
    res = adaptive_greedy_cluster(
        items,
        initial_threshold=0.9,
        min_clusters=1,
        max_clusters=1,
        max_top_share=1.0,
        step=0.1,
        tries=1,
    )
    assert len(res["clusters"]) == 1  # forced to group together


def test_rescue_display_dominance_edge_cases():
    res1 = rescue_display_dominance(
        [], items_by_text={}, initial_threshold=0.9, max_display_share=0.5
    )
    assert res1["rescued"] is False

    # Text not in items_by_text
    clusters = [
        Cluster(texts=["missing", "also_missing"], total_count=100, centroid=[1.0]),
        Cluster(texts=["ok"], total_count=1, centroid=[0.0]),
    ]
    items_by_text = {"ok": ([0.0], 1)}
    res2 = rescue_display_dominance(
        clusters,
        items_by_text=items_by_text,
        initial_threshold=0.5,
        max_display_share=0.5,
        step=0.1,
        tries=1,
    )
    assert res2["cluster_count_before"] == 2


def test_match_clusters_by_centroid_used():
    current = [
        Cluster(texts=["a"], total_count=1, centroid=[1.0]),
        Cluster(texts=["a"], total_count=1, centroid=[1.0]),
    ]
    previous = [
        Cluster(texts=["a"], total_count=1, centroid=[1.0]),
        Cluster(texts=["a"], total_count=1, centroid=[1.0]),
    ]
    mapping = match_clusters_by_centroid(
        current_clusters=current, previous_clusters=previous, match_threshold=0.0
    )
    # The first pair matches, the second current/previous pair might have similarity >= 0.0
    # and they will test `if i in used_current or j in used_previous:`
    assert len(mapping) <= 2

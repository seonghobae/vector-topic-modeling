from __future__ import annotations

from vector_topic_modeling.evaluation import (
    calculate_extended_metrics,
    calculate_silhouette_score,
    compute_centroid,
)


def test_silhouette_score_calculation():
    clusters = [
        ("c1", ["a", "b"]),
        ("c2", ["c", "d"]),
        ("c3", ["e"]),
    ]

    vectors_by_text = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],
        "c": [0.0, 1.0],
        "d": [0.1, 0.9],
        "e": [0.5, 0.5],
    }

    result = calculate_silhouette_score(clusters, vectors_by_text)

    assert result["overall_score"] > 0.0
    assert "c1" in result["cluster_scores"]
    assert "c2" in result["cluster_scores"]
    assert "c3" in result["cluster_scores"]


def test_silhouette_score_single_cluster():
    clusters = [("c1", ["a", "b"])]
    vectors_by_text = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],
    }
    result = calculate_silhouette_score(clusters, vectors_by_text)
    assert result["overall_score"] == 0.0
    assert result["cluster_scores"] == {}


def test_silhouette_score_empty_or_missing_vectors():
    # Empty cluster
    clusters = [
        ("c1", []),
        ("c2", ["a"]),
    ]

    vectors_by_text = {
        "a": [0.0, 1.0],
    }

    result = calculate_silhouette_score(clusters, vectors_by_text)
    assert result["overall_score"] == 0.0
    assert result["cluster_scores"] == {}

    # Text not in vectors_by_text
    clusters_missing = [
        ("c3", ["b", "c"]),
        ("c4", ["a"]),
    ]
    result2 = calculate_silhouette_score(clusters_missing, vectors_by_text)
    assert result2["overall_score"] == 0.0


def test_compute_centroid_empty() -> None:
    assert compute_centroid([]) == []


def test_compute_centroid_single() -> None:
    assert compute_centroid([[1.0, 2.0]]) == [1.0, 2.0]


def test_compute_centroid_multiple() -> None:
    assert compute_centroid([[1.0, 2.0], [3.0, 4.0]]) == [2.0, 3.0]


def test_calculate_extended_metrics_fewer_than_2_clusters() -> None:
    clusters = [("c1", ["a", "b"])]
    vectors = {"a": [1.0, 0.0], "b": [1.0, 0.0]}
    res = calculate_extended_metrics(clusters, vectors)
    assert res["silhouette_score"] == 0.0
    assert res["calinski_harabasz_score"] == 0.0
    assert res["davies_bouldin_score"] == 0.0


def test_calculate_extended_metrics_empty_all_vectors() -> None:
    clusters = [("c1", ["x"]), ("c2", ["y"])]
    vectors = {"a": [1.0, 0.0]}
    res = calculate_extended_metrics(clusters, vectors)
    assert res["silhouette_score"] == 0.0


def test_calculate_extended_metrics_valid() -> None:
    clusters = [("c1", ["a", "b"]), ("c2", ["c", "d"])]
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],
        "c": [0.0, 1.0],
        "d": [0.1, 0.9],
    }
    res = calculate_extended_metrics(clusters, vectors)
    assert res["silhouette_score"] > 0.0
    assert res["calinski_harabasz_score"] > 0.0
    assert res["davies_bouldin_score"] >= 0.0
    assert res["topic_coherence"]["c1"] > 0.9
    assert res["topic_coherence"]["c2"] > 0.9


def test_calculate_extended_metrics_empty_cluster() -> None:
    clusters = [("c1", ["a"]), ("c2", ["x"]), ("c3", ["b"])]  # no vector
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.0, 1.0],
    }
    res = calculate_extended_metrics(clusters, vectors)
    assert res["silhouette_score"] > 0.0
    assert "c2" in res["topic_coherence"]
    assert res["topic_coherence"]["c2"] == 0.0


def test_calculate_extended_metrics_identical_centroids() -> None:
    clusters = [("c1", ["a", "b"]), ("c2", ["c", "d"])]
    # Make vectors identical to force division by zero scenarios
    vectors = {
        "a": [1.0, 0.0],
        "b": [1.0, 0.0],
        "c": [1.0, 0.0],
        "d": [1.0, 0.0],
    }
    res = calculate_extended_metrics(clusters, vectors)
    assert res["calinski_harabasz_score"] == 0.0
    # DB score might be 0.0 or 0.0 depending on max_r accumulation
    assert res["davies_bouldin_score"] == 0.0


def test_calculate_extended_metrics_db_infinity() -> None:
    clusters = [("c1", ["a", "b"]), ("c2", ["c", "d"]), ("c3", ["e"])]
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],  # slightly spread
        "c": [1.0, 0.0],
        "d": [0.9, 0.1],  # identical centroid to c1
        "e": [0.0, 1.0],
    }
    res = calculate_extended_metrics(clusters, vectors)
    assert res["davies_bouldin_score"] >= 0.0


def test_calculate_silhouette_score_fewer_than_2_clusters():
    res = calculate_silhouette_score([("c1", ["a", "b"])], {"a": [1.0], "b": [0.9]})
    assert res["overall_score"] == 0.0


def test_calculate_extended_metrics_db_dist_zero():
    # dist_ij == 0.0 path should avoid division by zero in DB computation.
    clusters = [("c1", ["a"]), ("c2", ["b"])]
    vectors = {
        "a": [1.0, 0.0],
        "b": [1.0, 0.0],  # Identical to 'a' to make dist_ij == 0.0
    }
    res = calculate_extended_metrics(clusters, vectors)
    assert res["davies_bouldin_score"] == 0.0


def test_calculate_extended_metrics_db_smaller_r_ij():
    # Exercise branch where later candidate does not exceed current max_r.
    clusters = [("c1", ["a"]), ("c2", ["b"]), ("c3", ["c"])]
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],  # Close to 'a', so high r_ij
        "c": [0.0, 1.0],  # Far from 'a', so low r_ij
    }
    res = calculate_extended_metrics(clusters, vectors)
    assert res["davies_bouldin_score"] > 0.0


def test_silhouette_mean_dist_not_less():
    # Exercise branch where a later cluster does not replace current b_i.
    clusters = [
        ("c1", ["a"]),
        ("c2", ["b"]),  # closer to a
        ("c3", ["c"]),  # further from a
    ]
    vectors = {"a": [1.0, 0.0], "b": [0.9, 0.1], "c": [0.0, 1.0]}
    res = calculate_silhouette_score(clusters, vectors)
    assert -1.0 <= res["overall_score"] <= 1.0
    assert set(res["cluster_scores"].keys()) == {"c1", "c2", "c3"}

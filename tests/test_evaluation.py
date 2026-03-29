from __future__ import annotations

from vector_topic_modeling.evaluation import calculate_silhouette_score


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
    assert "c2" in result["cluster_scores"]

    # Text not in vectors_by_text
    clusters_missing = [
        ("c3", ["b", "c"]),
        ("c4", ["a"]),
    ]
    result2 = calculate_silhouette_score(clusters_missing, vectors_by_text)
    assert result2["overall_score"] == 0.0

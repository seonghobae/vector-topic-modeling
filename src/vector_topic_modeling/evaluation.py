"""Mathematical evaluation metrics for clustering without heavy dependencies."""

from __future__ import annotations

from typing import TypedDict
from vector_topic_modeling.clustering import cosine_similarity

class SilhouetteResult(TypedDict):
    """Result payload for silhouette score evaluation."""
    overall_score: float
    cluster_scores: dict[str, float]

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

    overall_scores: list[float] = []
    cluster_score_map: dict[str, float] = {}

    for i, vecs_i in enumerate(cluster_vectors):
        if not vecs_i:
            continue
            
        cluster_total_score = 0.0
        valid_points = 0
        
        for v_idx, v in enumerate(vecs_i):
            if len(vecs_i) > 1:
                a_i = sum((1.0 - cosine_similarity(v, other_v)) 
                         for other_idx, other_v in enumerate(vecs_i) 
                         if other_idx != v_idx) / (len(vecs_i) - 1)
            else:
                a_i = 0.0
            
            b_i = float('inf')
            for j, vecs_j in enumerate(cluster_vectors):
                if i == j or not vecs_j:
                    continue
                mean_dist = sum((1.0 - cosine_similarity(v, other_v)) 
                              for other_v in vecs_j) / len(vecs_j)
                if mean_dist < b_i:
                    b_i = mean_dist
            
            if b_i == float('inf'):
                b_i = 0.0
                
            max_ab = max(a_i, b_i)
            s_i = (b_i - a_i) / max_ab if max_ab > 0 else 0.0
            
            cluster_total_score += s_i
            overall_scores.append(s_i)
            valid_points += 1
            
        cluster_score_map[cluster_ids[i]] = cluster_total_score / valid_points

    overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
    return {"overall_score": overall, "cluster_scores": cluster_score_map}

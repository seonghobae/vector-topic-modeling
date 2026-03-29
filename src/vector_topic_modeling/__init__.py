"""Standalone vector-based topic modeling package."""

from vector_topic_modeling.evaluation import (
    ClusteringMetrics,
    SilhouetteResult,
    calculate_extended_metrics,
    calculate_silhouette_score,
)
from vector_topic_modeling.pipeline import (
    Topic,
    TopicAssignment,
    TopicDocument,
    TopicModelConfig,
    TopicModelResult,
    TopicModeler,
)
from vector_topic_modeling.ingestion import (
    TopicDocumentIngestionConfig,
    load_ingestion_config,
    load_jsonl_topic_documents,
    topic_document_from_row,
)
from vector_topic_modeling.providers.openai_compat import (
    OpenAICompatConfig,
    OpenAICompatEmbeddingProvider,
)

__all__ = [
    "SilhouetteResult",
    "ClusteringMetrics",
    "calculate_silhouette_score",
    "calculate_extended_metrics",
    "OpenAICompatConfig",
    "OpenAICompatEmbeddingProvider",
    "TopicDocumentIngestionConfig",
    "Topic",
    "TopicAssignment",
    "TopicDocument",
    "TopicModelConfig",
    "TopicModelResult",
    "TopicModeler",
    "load_ingestion_config",
    "load_jsonl_topic_documents",
    "topic_document_from_row",
]

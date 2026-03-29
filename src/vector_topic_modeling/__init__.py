"""Standalone vector-based topic modeling package."""

from vector_topic_modeling.evaluation import (
    SilhouetteResult,
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
    "calculate_silhouette_score",
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

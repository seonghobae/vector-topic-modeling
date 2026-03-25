"""Standalone vector-based topic modeling package."""

from vector_topic_modeling.pipeline import (
    Topic,
    TopicAssignment,
    TopicDocument,
    TopicModelConfig,
    TopicModelResult,
    TopicModeler,
)
from vector_topic_modeling.providers.openai_compat import (
    OpenAICompatConfig,
    OpenAICompatEmbeddingProvider,
)

__all__ = [
    "OpenAICompatConfig",
    "OpenAICompatEmbeddingProvider",
    "Topic",
    "TopicAssignment",
    "TopicDocument",
    "TopicModelConfig",
    "TopicModelResult",
    "TopicModeler",
]

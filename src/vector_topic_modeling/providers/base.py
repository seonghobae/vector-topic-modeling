"""Provider protocols for embeddings and labels."""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol for components that map text inputs to embedding vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return an embedding vector per input text.

        Args:
            texts: Ordered list of text strings to embed.

        Returns:
            List of embedding vectors in the same order as *texts*, each a
            list of floats.
        """

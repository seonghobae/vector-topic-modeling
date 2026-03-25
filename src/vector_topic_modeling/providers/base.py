"""Provider protocols for embeddings and labels."""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return an embedding vector per input text."""

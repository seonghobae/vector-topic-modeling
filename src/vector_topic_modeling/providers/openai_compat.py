"""OpenAI-compatible embedding provider implemented with urllib."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.parse import urlparse
import urllib.error
import urllib.request

from vector_topic_modeling._sanitize import clean_env, strip_nul


@dataclass(frozen=True)
class OpenAICompatConfig:
    """Connection settings for an OpenAI-compatible embeddings endpoint."""

    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 20.0


def parse_embedding_response_data(
    *, data: list[dict[str, Any]], expected_count: int
) -> list[list[float]]:
    """Validate and reorder embedding response items by their index field."""
    indexed: dict[int, list[float]] = {}
    expected_dim: int | None = None
    for item in data:
        idx = item.get("index")
        if not isinstance(idx, int):
            raise ValueError("Embedding response item missing integer 'index'")
        if idx < 0 or idx >= expected_count:
            raise ValueError("Embedding response index out of range")
        embedding = item.get("embedding")
        if not isinstance(embedding, list):
            raise ValueError("Embedding response item missing 'embedding'")
        if expected_dim is None:
            expected_dim = len(embedding)
        if len(embedding) != expected_dim:
            raise ValueError("Embedding response dimensionality mismatch")
        converted: list[float] = []
        for value in embedding:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("Embedding response item has non-numeric values")
            converted.append(float(value))
        indexed[idx] = converted
    if expected_dim is None or len(indexed) != expected_count:
        raise ValueError("Embedding response missing embeddings")
    return [indexed[i] for i in range(expected_count)]


class OpenAICompatEmbeddingProvider:
    """Embedding provider that calls an OpenAI-compatible HTTP API."""

    def __init__(self, config: OpenAICompatConfig) -> None:
        """Validate and normalize provider configuration."""
        parsed = urlparse(clean_env(config.base_url))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be a valid http(s) URL")
        self.config = OpenAICompatConfig(
            base_url=clean_env(config.base_url).rstrip("/"),
            api_key=clean_env(config.api_key),
            model=clean_env(config.model),
            timeout_seconds=float(config.timeout_seconds),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Fetch embeddings for input texts using the configured endpoint."""
        if not texts:
            return []
        payload = json.dumps(
            {"model": self.config.model, "input": [strip_nul(text) for text in texts]},
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.config.base_url}/v1/embeddings",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout_seconds
            ) as response:  # nosec B310
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise ValueError(f"Embedding request failed: HTTP {exc.code}") from exc
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            raise ValueError(f"Embedding request failed: {type(exc).__name__}") from exc
        parsed = json.loads(raw.decode("utf-8", "replace"))
        if not isinstance(parsed, dict) or not isinstance(parsed.get("data"), list):
            raise ValueError("Embedding response missing 'data'")
        items = [item for item in parsed["data"] if isinstance(item, dict)]
        return parse_embedding_response_data(data=items, expected_count=len(texts))

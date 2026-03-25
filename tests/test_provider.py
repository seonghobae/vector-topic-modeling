from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest

from vector_topic_modeling.providers.openai_compat import (
    OpenAICompatConfig,
    OpenAICompatEmbeddingProvider,
    parse_embedding_response_data,
)


def test_parse_embedding_response_data_orders_by_index() -> None:
    data = [
        {"index": 1, "embedding": [0.0, 1.0]},
        {"index": 0, "embedding": [1.0, 0.0]},
    ]
    assert parse_embedding_response_data(data=data, expected_count=2) == [
        [1.0, 0.0],
        [0.0, 1.0],
    ]


def test_openai_compat_provider_rejects_invalid_base_url() -> None:
    with pytest.raises(ValueError):
        OpenAICompatEmbeddingProvider(
            OpenAICompatConfig(base_url="ftp://bad", api_key="k", model="m")
        )


def test_parse_embedding_response_data_rejects_non_numeric_values() -> None:
    with pytest.raises(ValueError, match="non-numeric"):
        parse_embedding_response_data(
            data=[{"index": 0, "embedding": [1.0, "bad"]}],
            expected_count=1,
        )


def test_parse_embedding_response_data_rejects_boolean_values() -> None:
    with pytest.raises(ValueError, match="non-numeric"):
        parse_embedding_response_data(
            data=[{"index": 0, "embedding": [1.0, True]}],
            expected_count=1,
        )


def test_openai_compat_provider_parses_embedding_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatEmbeddingProvider(
        OpenAICompatConfig(base_url="https://example.com", api_key="k", model="m")
    )

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"data": [{"index": 0, "embedding": [1, 2, 3]}]}).encode(
                "utf-8"
            )

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout=0: FakeResponse(),
    )

    assert provider.embed(["hello"]) == [[1.0, 2.0, 3.0]]


def test_openai_compat_provider_wraps_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAICompatEmbeddingProvider(
        OpenAICompatConfig(base_url="https://example.com", api_key="k", model="m")
    )

    def _raise(request, timeout=0):
        raise HTTPError(
            url="https://example.com/v1/embeddings",
            code=500,
            msg="boom",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("urllib.request.urlopen", _raise)

    with pytest.raises(ValueError, match="HTTP 500"):
        provider.embed(["hello"])

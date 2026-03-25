import pytest
from vector_topic_modeling.providers.openai_compat import (
    parse_embedding_response_data,
    OpenAICompatEmbeddingProvider,
    OpenAICompatConfig,
)
import urllib.error

def test_parse_embedding_response_data_edge_cases():
    with pytest.raises(ValueError, match="missing integer 'index'"):
        parse_embedding_response_data(data=[{}], expected_count=1)
        
    with pytest.raises(ValueError, match="index out of range"):
        parse_embedding_response_data(data=[{"index": 1}], expected_count=1)
        
    with pytest.raises(ValueError, match="missing 'embedding'"):
        parse_embedding_response_data(data=[{"index": 0}], expected_count=1)
        
    with pytest.raises(ValueError, match="dimensionality mismatch"):
        parse_embedding_response_data(data=[
            {"index": 0, "embedding": [1.0]},
            {"index": 1, "embedding": [1.0, 2.0]}
        ], expected_count=2)
        
    with pytest.raises(ValueError, match="missing embeddings"):
        parse_embedding_response_data(data=[{"index": 0, "embedding": [1.0]}], expected_count=2)
        
    with pytest.raises(ValueError, match="non-numeric values"):
        parse_embedding_response_data(data=[{"index": 0, "embedding": [True]}], expected_count=1)

def get_test_config():
    return OpenAICompatConfig(base_url="http://test.com", api_key="test", model="test")

def test_embed_empty():
    provider = OpenAICompatEmbeddingProvider(get_test_config())
    assert provider.embed([]) == []

def test_embed_exceptions(monkeypatch):
    provider = OpenAICompatEmbeddingProvider(get_test_config())
    
    def mock_urlopen_url_err(*args, **kwargs):
        raise urllib.error.URLError("test")
        
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_url_err)
    with pytest.raises(ValueError, match="Embedding request failed: URLError"):
        provider.embed(["test"])
        
    def mock_urlopen_bad_json(*args, **kwargs):
        class MockResponse:
            def read(self):
                return b'{"not_data": []}'
            def __enter__(self): return self
            def __exit__(self, exc_type, exc_val, exc_tb): pass
        return MockResponse()
        
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_bad_json)
    with pytest.raises(ValueError, match="missing 'data'"):
        provider.embed(["test"])

    def mock_urlopen_http_err(*args, **kwargs):
        raise urllib.error.HTTPError("http://test.com", 500, "Server Error", {}, None)
        
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_http_err)
    with pytest.raises(ValueError, match="Embedding request failed: HTTP 500"):
        provider.embed(["test"])


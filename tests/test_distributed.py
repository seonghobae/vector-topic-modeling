from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import vector_topic_modeling.distributed as distributed


@pytest.fixture
def mock_valkey_client(mocker: Any) -> MagicMock:
    # Mock the Valkey module and client
    mock_valkey = mocker.patch("vector_topic_modeling.distributed.valkey")
    mock_client = MagicMock()
    mock_valkey.Valkey.from_url.return_value = mock_client

    # Simple in-memory storage for the mock
    storage: dict[str, Any] = {}
    hashes: dict[str, dict[str, str]] = {}
    lists: dict[str, list[str]] = {}

    def mock_set(key, value):
        storage[key] = value

    def mock_get(key):
        return storage.get(key)

    def mock_rpush(key, *values):
        if key not in lists:
            lists[key] = []
        lists[key].extend([str(v) for v in values])

    def mock_lpop(key):
        if key in lists and lists[key]:
            return lists[key].pop(0)
        return None

    def mock_hset(key, field, value):
        if key not in hashes:
            hashes[key] = {}
        hashes[key][str(field)] = str(value)

    def mock_hgetall(key):
        return hashes.get(key, {})

    def mock_delete(*keys):
        for k in keys:
            storage.pop(k, None)
            hashes.pop(k, None)
            lists.pop(k, None)

    mock_client.set.side_effect = mock_set
    mock_client.get.side_effect = mock_get
    mock_client.rpush.side_effect = mock_rpush
    mock_client.lpop.side_effect = mock_lpop
    mock_client.hset.side_effect = mock_hset
    mock_client.hgetall.side_effect = mock_hgetall
    mock_client.delete.side_effect = mock_delete

    return mock_client


def test_calculate_distributed_metrics_no_valkey(mocker):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", False)
    with pytest.raises(ImportError):
        distributed.calculate_distributed_metrics([], {})


def test_calculate_distributed_metrics_fewer_than_2_clusters(
    mock_valkey_client, mocker
):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    clusters = [("c1", ["a", "b"])]
    vectors = {"a": [1.0, 0.0], "b": [1.0, 0.0]}

    res = distributed.calculate_distributed_metrics(clusters, vectors)
    assert res["silhouette_score"] == 0.0
    mock_valkey_client.set.assert_not_called()


def test_calculate_distributed_metrics_no_valid_vectors(mock_valkey_client, mocker):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    clusters = [("c1", ["x"]), ("c2", ["y"])]
    vectors = {"a": [1.0, 0.0]}

    res = distributed.calculate_distributed_metrics(clusters, vectors)
    assert res["silhouette_score"] == 0.0
    mock_valkey_client.set.assert_not_called()


def test_calculate_distributed_metrics_valid(mock_valkey_client, mocker):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    clusters = [("c1", ["a", "b"]), ("c2", ["c", "d"])]
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],
        "c": [0.0, 1.0],
        "d": [0.1, 0.9],
    }

    res = distributed.calculate_distributed_metrics(clusters, vectors, num_workers=2)
    assert res["silhouette_score"] > 0.0
    assert res["calinski_harabasz_score"] > 0.0
    assert res["davies_bouldin_score"] >= 0.0
    assert res["topic_coherence"]["c1"] > 0.9

    # Check that cleanup was called
    assert mock_valkey_client.delete.called


def test_worker_loop_missing_data(mock_valkey_client):
    # Setup worker loop where vectors_key is missing
    distributed._worker_loop("redis://localhost:6379", "test_job")
    mock_valkey_client.get.assert_called()


def test_worker_loop_single_element_cluster(mock_valkey_client, mocker):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    clusters = [("c1", ["a"]), ("c2", ["b", "c"])]
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.0, 1.0],
        "c": [0.1, 0.9],
    }
    res = distributed.calculate_distributed_metrics(clusters, vectors, num_workers=1)
    assert res["silhouette_score"] > 0.0


def test_worker_loop_empty_cluster(mock_valkey_client, mocker):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    clusters = [("c1", ["a", "b"]), ("c2", []), ("c3", ["c", "d"])]
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],
        "c": [0.0, 1.0],
        "d": [0.1, 0.9],
    }
    res = distributed.calculate_distributed_metrics(clusters, vectors, num_workers=1)
    assert res["silhouette_score"] > 0.0


def test_calculate_distributed_metrics_worker_fallback(mock_valkey_client, mocker):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    clusters = [("c1", ["a", "b"]), ("c2", ["c", "d"])]
    vectors = {"a": [1.0, 0.0], "b": [0.9, 0.1], "c": [0.0, 1.0], "d": [0.1, 0.9]}

    # Override fixture side effect so hgetall deterministically returns empty data.
    mock_valkey_client.hgetall.side_effect = lambda _key: {}

    res = distributed.calculate_distributed_metrics(clusters, vectors, num_workers=0)

    # It should fallback to base metrics which has silhouette_score calculated locally
    assert res["silhouette_score"] > 0.0


def test_calculate_distributed_metrics_partial_results_fallback(
    mock_valkey_client, mocker
):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    base_metrics = {
        "silhouette_score": 0.42,
        "calinski_harabasz_score": 1.23,
        "davies_bouldin_score": 0.98,
        "topic_coherence": {"c1": 0.9, "c2": 0.8},
    }
    mocker.patch(
        "vector_topic_modeling.distributed.calculate_extended_metrics",
        return_value=base_metrics,
    )

    clusters = [("c1", ["a", "b"]), ("c2", ["c", "d"])]
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],
        "c": [0.0, 1.0],
        "d": [0.1, 0.9],
    }

    mock_valkey_client.hgetall.side_effect = lambda _key: {"0": "0.5"}

    res = distributed.calculate_distributed_metrics(clusters, vectors, num_workers=0)

    assert res == base_metrics


def test_valkey_import_error_exposes_patchable_symbol():
    import builtins
    import importlib
    import sys

    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "valkey":
            raise ImportError("No module named valkey")
        return original_import(name, *args, **kwargs)

    try:
        with patch("builtins.__import__", side_effect=mock_import):
            sys.modules.pop("valkey", None)
            importlib.reload(distributed)
            assert not distributed.VALKEY_AVAILABLE
            assert hasattr(distributed, "valkey")
            assert distributed.valkey is None

            patched_valkey = MagicMock()
            with patch("vector_topic_modeling.distributed.valkey", patched_valkey):
                assert distributed.valkey is patched_valkey
    finally:
        importlib.reload(distributed)


def test_valkey_import_success_sets_availability_true() -> None:
    import importlib
    import sys

    fake_valkey = MagicMock()

    try:
        with patch.dict(sys.modules, {"valkey": fake_valkey}):
            importlib.reload(distributed)
            assert distributed.VALKEY_AVAILABLE
            assert distributed.valkey is fake_valkey
    finally:
        importlib.reload(distributed)


def test_distributed_missing_vector(mock_valkey_client, mocker):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    clusters = [("c1", ["a", "missing_vector"]), ("c2", ["c", "d"])]
    vectors = {
        "a": [1.0, 0.0],
        "c": [0.0, 1.0],
        "d": [0.1, 0.9],
    }
    res = distributed.calculate_distributed_metrics(clusters, vectors, num_workers=1)
    assert res["silhouette_score"] > 0.0


def test_worker_loop_no_other_clusters(mock_valkey_client, mocker):
    mocker.patch("vector_topic_modeling.distributed.VALKEY_AVAILABLE", True)
    # This hits line 164, where b_i stays infinity
    clusters = [
        ("c1", ["a", "b"]),
        ("c2", []),  # other cluster empty
    ]
    vectors = {
        "a": [1.0, 0.0],
        "b": [0.9, 0.1],
    }
    # Distributed path now short-circuits when fewer than 2 populated clusters remain.
    distributed.calculate_distributed_metrics(clusters, vectors, num_workers=1)
    # We still call _worker_loop directly to exercise the worker branch.

    mock_valkey_client.set("test_job2:vectors", json.dumps([[1.0, 0.0], [0.9, 0.1]]))
    mock_valkey_client.set("test_job2:clusters", json.dumps([[0, 1], []]))
    mock_valkey_client.rpush("test_job2:tasks", 0, 1)

    distributed._worker_loop("redis://localhost:6379", "test_job2")
    # This should hit b_i = 0.0
    res = mock_valkey_client.hgetall("test_job2:results")
    assert "0" in res


def test_worker_loop_multiple_clusters_mean_dist_not_less(mock_valkey_client):
    # First run: later cluster can replace b_i.
    mock_valkey_client.set(
        "test_job3:vectors",
        json.dumps(
            [
                [1.0, 0.0],
                [0.0, 1.0],
                [0.5, 0.5],
            ]
        ),
    )
    mock_valkey_client.set("test_job3:clusters", json.dumps([[0], [1], [2]]))
    mock_valkey_client.rpush("test_job3:tasks", 0)

    distributed._worker_loop("redis://localhost:6379", "test_job3")
    first_res = mock_valkey_client.hgetall("test_job3:results")
    assert "0" in first_res
    assert -1.0 <= float(first_res["0"]) <= 1.0

    # Second run: exercise branch where a later cluster does not replace b_i.
    mock_valkey_client.delete("test_job3:results")
    mock_valkey_client.set(
        "test_job3:vectors",
        json.dumps(
            [
                [1.0, 0.0],
                [0.5, 0.5],
                [0.0, 1.0],
            ]
        ),
    )
    mock_valkey_client.rpush("test_job3:tasks", 0)
    distributed._worker_loop("redis://localhost:6379", "test_job3")
    second_res = mock_valkey_client.hgetall("test_job3:results")
    assert second_res["0"] == "1.0"

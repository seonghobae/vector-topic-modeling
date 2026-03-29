from __future__ import annotations

from vector_topic_modeling.pipeline import (
    TopicDocument,
    TopicModelConfig,
    TopicModeler,
)


class FakeEmbeddingProvider:
    def __init__(self, vectors: dict[str, list[float]]) -> None:
        self.vectors = vectors

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self.vectors[text] for text in texts]


def test_topic_modeler_clusters_documents_and_builds_assignments() -> None:
    docs = [
        TopicDocument(id="1", text="refund duplicate billing"),
        TopicDocument(id="2", text="cancel subscription refund"),
        TopicDocument(id="3", text="vpn connection timeout"),
    ]
    provider = FakeEmbeddingProvider(
        {
            "refund duplicate billing": [1.0, 0.0],
            "cancel subscription refund": [0.95, 0.05],
            "vpn connection timeout": [0.0, 1.0],
        }
    )
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(similarity_threshold=0.8, min_topics=2, max_topics=10),
    )

    result = modeler.fit_predict(docs)

    assert len(result.topics) == 2
    assert len(result.assignments) == 3
    assert result.assignments[0].topic_id == result.assignments[1].topic_id
    assert result.assignments[2].topic_id != result.assignments[0].topic_id


def test_topic_modeler_session_aware_mode_avoids_trivial_pair_dominance() -> None:
    docs = [
        TopicDocument(
            id="greeting-1",
            text="안녕? 안녕하세요!",
            session_id="s1",
            question="안녕?",
            response="안녕하세요!",
            count=50,
        ),
        TopicDocument(
            id="substantive-1",
            text="2026년 2월 법인세 신고 절차 설명",
            session_id="s1",
            question="2026년 2월 법인세 신고 절차를 단계별로 설명해줘",
            response="전제 조건/서류/기한을 정리하고 홈택스에서 신고서를 작성합니다.",
            count=1,
        ),
        TopicDocument(
            id="substantive-2",
            text="2026년 3월 부가세 신고 절차 설명",
            session_id="s2",
            question="2026년 3월 부가세 신고 절차를 단계별로 설명해줘",
            response="서류와 신고 기한을 검토한 다음 홈택스에서 신고합니다.",
            count=1,
        ),
    ]
    provider = FakeEmbeddingProvider(
        {
            "안녕? 안녕하세요!": [1.0, 0.0],
            "2026년 2월 법인세 신고 절차 설명": [0.0, 1.0],
            "2026년 3월 부가세 신고 절차 설명": [0.05, 0.95],
        }
    )
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(use_session_representatives=True),
    )

    result = modeler.fit_predict(docs)

    greeting_assignment = next(
        item for item in result.assignments if item.document_id == "greeting-1"
    )
    substantive_assignment = next(
        item for item in result.assignments if item.document_id == "substantive-1"
    )
    assert greeting_assignment.topic_id == substantive_assignment.topic_id
    assert result.topic_lookup[substantive_assignment.topic_id].total_count == 2
    assert result.session_topic_counts[("s1", substantive_assignment.topic_id)] == 51


def test_topic_modeler_session_aware_mode_keeps_sessionless_documents() -> None:
    docs = [TopicDocument(id="1", text="refund request")]
    provider = FakeEmbeddingProvider({"refund request": [1.0, 0.0]})
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(use_session_representatives=True, min_topics=1),
    )

    result = modeler.fit_predict(docs)

    assert len(result.topics) == 1
    assert result.assignments[0].topic_id != "unassigned"


def test_fit_predict_uses_session_representative_for_topic_assignment() -> None:
    docs = [
        TopicDocument(
            id="greeting",
            text="안녕? 안녕하세요!",
            session_id="s-valid",
            question="안녕?",
            response="안녕하세요!",
            count=1,
        ),
        TopicDocument(
            id="substantive",
            text="2026년 2월 법인세 신고 절차 설명",
            session_id="s-valid",
            question="2026년 2월 법인세 신고 절차를 단계별로 설명해줘",
            response="전제 조건과 신고 절차를 단계별로 설명합니다.",
            count=1,
        ),
    ]
    provider = FakeEmbeddingProvider(
        {
            "안녕? 안녕하세요!": [1.0, 0.0],
            "2026년 2월 법인세 신고 절차 설명": [0.0, 1.0],
        }
    )
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(use_session_representatives=True, min_topics=1),
    )

    result = modeler.fit_predict(docs)

    assert len(result.topics) == 1
    assert result.topics[0].texts == ["2026년 2월 법인세 신고 절차 설명"]
    assignment_by_document = {
        item.document_id: item.topic_id for item in result.assignments
    }
    assert assignment_by_document["greeting"] == assignment_by_document["substantive"]


def test_fit_predict_allows_sessions_without_selected_representative(
    monkeypatch,
) -> None:
    docs = [
        TopicDocument(
            id="s-empty-doc",
            text="simple greeting",
            session_id="s-empty",
            question="hi",
            response="ok",
            count=1,
        ),
        TopicDocument(
            id="s-valid-doc",
            text="tax filing process 2026 details",
            session_id="s-valid",
            question="tell me tax filing process in detail",
            response="step-by-step explanation",
            count=1,
        ),
    ]
    provider = FakeEmbeddingProvider(
        {
            "simple greeting": [1.0, 0.0],
            "tax filing process 2026 details": [0.0, 1.0],
        }
    )

    def _pick_or_none(
        session_rows: list[dict[str, object]], *, selector: object | None = None
    ) -> str | None:
        _ = selector
        session_id = str(session_rows[0]["session_id"])
        if session_id == "s-empty":
            return None
        return str(session_rows[0]["digest_hex"])

    monkeypatch.setattr(
        "vector_topic_modeling.pipeline.pick_session_main_digest", _pick_or_none
    )

    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(use_session_representatives=True, min_topics=1),
    )

    result = modeler.fit_predict(docs)

    assert len(result.assignments) == 2


def test_pipeline_silhouette_score() -> None:
    """Test that pipeline correctly calculates silhouette score when enabled."""
    provider = FakeEmbeddingProvider(
        {
            "apple orange": [1.0, 0.0],
            "cat dog": [0.0, 1.0],
        }
    )
    docs = [
        TopicDocument(id="1", text="apple orange"),
        TopicDocument(id="2", text="apple orange"),
        TopicDocument(id="3", text="cat dog"),
        TopicDocument(id="4", text="cat dog"),
    ]
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(min_topics=2, max_topics=2, calculate_silhouette=True),
    )
    result = modeler.fit_predict(docs)
    assert result.silhouette_score is not None
    assert "overall_score" in result.silhouette_score
    assert isinstance(result.silhouette_score["overall_score"], float)


def test_pipeline_extended_metrics_local() -> None:
    """Test that pipeline correctly calculates extended metrics locally when enabled."""
    provider = FakeEmbeddingProvider(
        {
            "apple orange": [1.0, 0.0],
            "cat dog": [0.0, 1.0],
        }
    )
    docs = [
        TopicDocument(id="1", text="apple orange"),
        TopicDocument(id="2", text="apple orange"),
        TopicDocument(id="3", text="cat dog"),
        TopicDocument(id="4", text="cat dog"),
    ]
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(
            min_topics=2,
            max_topics=2,
            calculate_extended_metrics=True,
            use_distributed_evaluation=False,
        ),
    )
    result = modeler.fit_predict(docs)
    assert result.extended_metrics is not None
    assert "calinski_harabasz_score" in result.extended_metrics


def test_pipeline_extended_metrics_distributed(mocker) -> None:
    """Test that pipeline correctly calculates extended metrics distributed when enabled."""
    provider = FakeEmbeddingProvider(
        {
            "apple orange": [1.0, 0.0],
            "cat dog": [0.0, 1.0],
        }
    )
    docs = [
        TopicDocument(id="1", text="apple orange"),
        TopicDocument(id="2", text="apple orange"),
        TopicDocument(id="3", text="cat dog"),
        TopicDocument(id="4", text="cat dog"),
    ]
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(
            min_topics=2,
            max_topics=2,
            calculate_extended_metrics=True,
            use_distributed_evaluation=True,
        ),
    )

    mock_calc = mocker.patch(
        "vector_topic_modeling.pipeline.calculate_distributed_metrics"
    )
    mock_calc.return_value = {
        "silhouette_score": 1.0,
        "calinski_harabasz_score": 2.0,
        "davies_bouldin_score": 3.0,
        "topic_coherence": {},
    }

    result = modeler.fit_predict(docs)

    mock_calc.assert_called_once()
    assert result.extended_metrics is not None
    assert result.extended_metrics["silhouette_score"] == 1.0


def test_pipeline_reuses_precomputed_silhouette_for_local_extended_metrics(
    mocker,
) -> None:
    provider = FakeEmbeddingProvider(
        {
            "apple orange": [1.0, 0.0],
            "cat dog": [0.0, 1.0],
        }
    )
    docs = [
        TopicDocument(id="1", text="apple orange"),
        TopicDocument(id="2", text="apple orange"),
        TopicDocument(id="3", text="cat dog"),
        TopicDocument(id="4", text="cat dog"),
    ]
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(
            min_topics=2,
            max_topics=2,
            calculate_silhouette=True,
            calculate_extended_metrics=True,
            use_distributed_evaluation=False,
        ),
    )

    mocker.patch(
        "vector_topic_modeling.pipeline.calculate_silhouette_score",
        return_value={"overall_score": 0.4, "cluster_scores": {"t1": 0.4}},
    )
    extended_mock = mocker.patch(
        "vector_topic_modeling.evaluation.calculate_extended_metrics",
        return_value={
            "silhouette_score": 0.4,
            "calinski_harabasz_score": 1.0,
            "davies_bouldin_score": 0.3,
            "topic_coherence": {},
        },
    )

    modeler.fit_predict(docs)

    assert extended_mock.call_args.kwargs["precomputed_silhouette"] == 0.4


def test_pipeline_reuses_precomputed_silhouette_for_distributed_metrics(
    mocker,
) -> None:
    provider = FakeEmbeddingProvider(
        {
            "apple orange": [1.0, 0.0],
            "cat dog": [0.0, 1.0],
        }
    )
    docs = [
        TopicDocument(id="1", text="apple orange"),
        TopicDocument(id="2", text="apple orange"),
        TopicDocument(id="3", text="cat dog"),
        TopicDocument(id="4", text="cat dog"),
    ]
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(
            min_topics=2,
            max_topics=2,
            calculate_silhouette=True,
            calculate_extended_metrics=True,
            use_distributed_evaluation=True,
        ),
    )

    mocker.patch(
        "vector_topic_modeling.pipeline.calculate_silhouette_score",
        return_value={"overall_score": 0.55, "cluster_scores": {"t1": 0.55}},
    )
    distributed_mock = mocker.patch(
        "vector_topic_modeling.pipeline.calculate_distributed_metrics",
        return_value={
            "silhouette_score": 0.55,
            "calinski_harabasz_score": 1.2,
            "davies_bouldin_score": 0.2,
            "topic_coherence": {},
        },
    )

    modeler.fit_predict(docs)

    assert distributed_mock.call_args.kwargs["precomputed_silhouette"] == 0.55


def test_pipeline_extended_metrics_without_silhouette_passes_none_precomputed(
    mocker,
) -> None:
    provider = FakeEmbeddingProvider(
        {
            "apple orange": [1.0, 0.0],
            "cat dog": [0.0, 1.0],
        }
    )
    docs = [
        TopicDocument(id="1", text="apple orange"),
        TopicDocument(id="2", text="apple orange"),
        TopicDocument(id="3", text="cat dog"),
        TopicDocument(id="4", text="cat dog"),
    ]
    modeler = TopicModeler(
        embedding_provider=provider,
        config=TopicModelConfig(
            min_topics=2,
            max_topics=2,
            calculate_silhouette=False,
            calculate_extended_metrics=True,
            use_distributed_evaluation=False,
        ),
    )

    extended_mock = mocker.patch(
        "vector_topic_modeling.evaluation.calculate_extended_metrics",
        return_value={
            "silhouette_score": 0.1,
            "calinski_harabasz_score": 1.0,
            "davies_bouldin_score": 0.2,
            "topic_coherence": {},
        },
    )

    modeler.fit_predict(docs)

    assert extended_mock.call_args.kwargs["precomputed_silhouette"] is None

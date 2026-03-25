from __future__ import annotations

from vector_topic_modeling import TopicDocument, TopicModelConfig, TopicModeler


class DemoEmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        lookup = {
            "refund duplicate billing": [1.0, 0.0],
            "cancel subscription refund": [0.95, 0.05],
            "vpn connection timeout": [0.0, 1.0],
        }
        return [lookup[text] for text in texts]


def main() -> None:
    docs = [
        TopicDocument(id="1", text="refund duplicate billing"),
        TopicDocument(id="2", text="cancel subscription refund"),
        TopicDocument(id="3", text="vpn connection timeout"),
    ]
    result = TopicModeler(
        embedding_provider=DemoEmbeddingProvider(),
        config=TopicModelConfig(similarity_threshold=0.8, min_topics=2),
    ).fit_predict(docs)
    for topic in result.topics:
        print(topic.topic_id, topic.total_count, topic.texts)


if __name__ == "__main__":
    main()

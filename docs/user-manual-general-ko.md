# 일반 문서 주제 분류(Topic Modeling) 사용자 매뉴얼

<!-- markdownlint-disable MD013 -->

이 매뉴얼은 채팅 기록이나 세션 기반의 데이터가 아닌, **일반 문서(뉴스 기사, 보고서, 블로그 포스트, 논문 요약 등)**를 대상으로 `vector-topic-modeling` 패키지를 활용하는 방법에 초점을 맞춥니다.

## 1. 일반 문서 처리에 대한 이해

일반 문서를 클러스터링할 때는 대화형 데이터에서 요구되는 `session_id`, `question`, `response` 등의 메타데이터가 필요하지 않습니다. 오직 **문서의 고유 식별자(`id`)**와 **문서 본문(`text`)**만으로 모든 파이프라인(임베딩, 코사인 유사도 비교, 적응형 군집화)이 동작합니다.

## 2. 데이터 준비 (JSONL 형태)

문서 한 건당 한 줄의 JSON 객체를 포함하는 `.jsonl` 파일을 준비합니다.

### 2.1 기본 형태

가장 직관적인 방법은 `id`와 `text` 필드만을 포함하는 것입니다.

```json
{"id": "news_001", "text": "한국은행이 기준금리를 동결함에 따라 시장이 안정세를 보이고 있습니다."}
{"id": "news_002", "text": "최근 AI 기술의 발전으로 자율주행 자동차의 상용화가 앞당겨지고 있습니다."}
{"id": "news_003", "text": "미국 연준의 금리 인하 기대감에 기술주 중심으로 상승 마감했습니다."}
```

### 2.2 기존 데이터베이스 형태 변환 없이 사용 (`--ingestion-config`)

이미 가지고 있는 문서 데이터에 `text` 대신 `content`, `body`, `article` 등의 필드명이 사용되고 있다면 데이터 자체를 수정할 필요 없이 `ingestion-config`를 설정하여 맵핑할 수 있습니다.

**config.json:**

```json
{
  "id_fields": ["article_id", "url"],
  "text_fields": ["body", "content", "summary"]
}
```

## 3. CLI 기반 토픽 도출 실행

준비된 문서를 기반으로 터미널에서 다음 명령어를 실행하여 토픽을 추출합니다. 세션 병합 옵션(`--use-session-representatives`)은 일반 문서에서는 사용하지 않습니다.

```bash
vector-topic-modeling cluster my_documents.jsonl \
  --output topics_output.json \
  --base-url "https://api.openai.com" \
  --api-key "sk-..." \
  --model text-embedding-3-large \
  --similarity-threshold 0.80 \
  --min-topics 3 \
  --max-topics 20
```

## 4. Python API를 이용한 일반 문서 처리

파이썬 코드 내에서 직접 문서를 주입하고 결과를 확인할 수 있습니다.

```python
from vector_topic_modeling import TopicDocument, TopicModelConfig, TopicModeler
from vector_topic_modeling.providers.openai_compat import (
    OpenAICompatConfig,
    OpenAICompatEmbeddingProvider,
)

# 1. 일반 문서 리스트 생성 (session_id 배제)
docs = [
    TopicDocument(id="doc1", text="금리 동결로 인한 금융 시장 안정세"),
    TopicDocument(id="doc2", text="AI 기술 도입으로 인한 자율주행 상용화 기대"),
    TopicDocument(id="doc3", text="미국 연준의 금리 인하와 글로벌 증시 상승"),
]

# 2. 임베딩 프로바이더 설정
provider = OpenAICompatEmbeddingProvider(
    OpenAICompatConfig(
        base_url="https://api.openai.com",
        api_key="sk-...",
        model="text-embedding-3-large",
    )
)

# 3. 모델러 초기화 및 클러스터링 실행
modeler = TopicModeler(
    embedding_provider=provider,
    config=TopicModelConfig(
        similarity_threshold=0.82,
        min_topics=2,
        max_topics=10
    ),
)

# 4. 결과 분석
result = modeler.fit_predict(docs)

print(f"발견된 토픽 수: {len(result.topics)}")
for topic in result.topics:
    print(f"Topic ID: {topic.topic_id} (문서 수: {topic.total_count})")
    print(f"대표 문서: {topic.texts[0]}")
```

## 5. 자주 묻는 질문 (FAQ)

- **Q. 일반 문서의 길이가 너무 깁니다. 다 들어가나요?**
  - A. `ingestion-config`를 통해 `max_text_chars` (기본값: 4000) 옵션으로 텍스트 길이를 조정할 수 있습니다. 임베딩 모델의 최대 토큰 한도를 초과하지 않도록 적절히 잘라내는 것을 권장합니다.
- **Q. 세션 관련 정보가 없으면 토픽 클러스터링 품질에 영향을 미치나요?**
  - A. 아닙니다. 세션 정보는 동일 사용자의 여러 대화를 묶기 위한 부가 기능일 뿐입니다. 일반 문서는 순수하게 텍스트 간 코사인 유사도(Cosine Similarity)를 통해 정확한 의미 기반 클러스터링을 수행합니다.

- **Q. 시작할 때는 어떤 토픽(topic_id)이 있는지 전혀 모르는 상태인데 어떻게 하나요?**
  - A. 정확합니다. 이 패키지는 사전에 정의된 카테고리를 맞추는 분류(Classification)가 아니라, 데이터 스스로 뭉치게 만드는 **비지도 학습 군집화(Unsupervised Clustering)** 도구입니다.
    사용자는 `topic_id`를 전혀 제공할 필요가 없으며 오직 `id`와 `text`만 입력합니다. 시스템이 의미가 비슷한 문서들을 묶은 뒤, 해당 군집(Cluster)을 대표하는 **고유한 `topic_id`를 자동으로 생성**하여 결과물에 할당(`assignments`)해 줍니다.

- **Q. 최적의 토픽 개수(k)를 찾는 수학적인 해(Mathematical Solution)는 무엇인가요?**
  - A. 이 패키지는 실무적인 편의를 위해 '탐욕적 휴리스틱 알고리즘(Greedy Heuristic Algorithm)'을 기본으로 사용하고 있습니다.
    그러나 엄밀한 수학적/통계적 관점에서 최적의 군집 수(k)를 평가하기 위해 패키지 내부에 **실루엣 점수(Silhouette Score)** 및 **Calinski-Harabasz, Davies-Bouldin** 지표 계산 기능이 내장되어 있습니다. CLI에서 `--calculate-silhouette`나 `--calculate-extended-metrics` 옵션을 사용하거나 파이썬 API에서 설정하면 외부 라이브러리(Scikit-Learn 등) 없이도 군집 품질을 확인할 수 있습니다. 데이터가 클 경우 Valkey를 통한 분산 처리(`--use-distributed-evaluation`)도 지원합니다.
    - **실루엣 점수**: 각 데이터 포인트가 같은 군집 내의 데이터와 얼마나 가깝고, 다른 군집의 데이터와 얼마나 먼지를 계산하여 -1에서 1 사이의 값으로 평가합니다. 1에 가까울수록 군집화가 잘 되었다고 판단할 수 있습니다.

<!-- markdownlint-enable MD013 -->

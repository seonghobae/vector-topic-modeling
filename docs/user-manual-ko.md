# Vector Topic Modeling 사용자 매뉴얼

패키지: `vector-topic-modeling`  
Python: `>=3.11`  
CLI: `vector-topic-modeling`

## 1) 설치 방법

### 1.1 사전 요구 사항

- Python 3.11 이상
- `uv` (개발 및 검증 환경 구축 시 권장)

### 1.2 소스 코드에서 설치

```bash
git clone https://github.com/seonghobae/vector-topic-modeling.git
cd vector-topic-modeling
uv sync
```

### 1.3 Wheel 파일로 설치

```bash
python3.11 -m pip install dist/vector_topic_modeling-<version>-py3-none-any.whl
```

### 1.4 설치 확인

```bash
vector-topic-modeling --help
vector-topic-modeling cluster --help
```

## 2) 빠른 시작 (Quick Start)

### 2.1 Python API 사용

```python
from vector_topic_modeling import TopicDocument, TopicModelConfig, TopicModeler

class FakeEmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

modeler = TopicModeler(
    embedding_provider=FakeEmbeddingProvider(),
    config=TopicModelConfig(similarity_threshold=0.85),
)

result = modeler.fit_predict(
    [
        TopicDocument(id="1", text="중복 결제 환불 요청"),
        TopicDocument(id="2", text="구독 취소 및 환불"),
    ]
)

print(len(result.topics), len(result.assignments))
```

### 2.2 CLI 사용

```bash
vector-topic-modeling cluster examples/sample_queries.jsonl \
  --output topics.json \
  --base-url "$LITELLM_API_BASE" \
  --api-key "$LITELLM_API_KEY" \
  --model text-embedding-3-large
```

일반적인 DB 데이터나 JSON 페이로드 주입(Ingestion) 예시:

```bash
vector-topic-modeling cluster examples/sample_db_rows.jsonl \
  --output topics.json \
  --ingestion-config examples/ingestion_config_db_columns.json \
  --base-url "$LITELLM_API_BASE" \
  --api-key "$LITELLM_API_KEY" \
  --model text-embedding-3-large
```

## 3) JSONL 입력 / 출력

### 3.1 입력 형태

각 줄마다 하나의 JSON 객체를 포함해야 합니다:

```json
{"id":"1","text":"중복 결제 환불 요청","session_id":"s1","question":"...","response":"...","count":1}
```

`--ingestion-config` 옵션을 사용하면 DB 스타일의 열(column)/값(value) 배열이나 중첩된 JSON 형태의 데이터도 처리할 수 있습니다.

### 3.2 입력 필드 매핑 규칙

- `id`: 고유 식별자로 우선 사용되며, 없을 경우 `document_id` 또는 행 인덱스로 대체됩니다.
- `text`: 다음 순서로 텍스트를 추출합니다: `text_fields` → `content_fields` → `payload_fields` → `question_fields`/`response_fields` (QA 쌍) → 원본 JSON 직렬화.
- `session_id`, `question`, `response`: 선택 사항입니다.
- `count`: 기본값은 `1`입니다.

`--ingestion-config`에서 `session_key_fields`가 설정된 경우, 명시적인 `session_id`가 없더라도 지정된 기본 키 컬럼을 조합하여(`pk:{...}`) 결정론적인 `session_id`를 생성합니다.

### 3.3 출력 형태 (`--output`)

생성된 JSON 파일은 다음의 최상위 키를 포함합니다:

- `topics`: 클러스터링된 토픽 목록 및 대표 예시
- `assignments`: 각 문서의 토픽 할당 결과
- `session_topic_counts`: 세션별 토픽 빈도수

## 4) CLI 옵션 상세 안내

실행 패턴:

```bash
vector-topic-modeling cluster INPUT_JSONL --output OUTPUT_JSON
```

| 옵션 | 필수 여부 | 기본값 | 설명 |
| --- | --- | --- | --- |
| `input_path` | 필수 | - | 입력 JSONL 파일 경로 |
| `--output` | 필수 | - | 결과 저장 JSON 파일 경로 |
| `--base-url` | 실행 시 필수 | - | OpenAI 호환 임베딩 API URL |
| `--api-key` | 실행 시 필수 | - | 임베딩 API 인증 키 |
| `--model` | 선택 | `text-embedding-3-large` | 임베딩에 사용할 모델 이름 |
| `--similarity-threshold` | 선택 | `0.85` | 클러스터링 유사도 임계값 (Threshold) |
| `--min-topics` | 선택 | `2` | 최소 생성 토픽 수 (`>= 1`) |
| `--max-topics` | 선택 | `30` | 최대 생성 토픽 수 (`>= --min-topics`) |
| `--max-top-share` | 선택 | `0.35` | 적응형 클러스터링 최상위 토픽 쏠림 제한 (`0 < x <= 1`) |
| `--display-limit` | 선택 | `30` | 토픽당 표시할 최대 대표 예시 개수 (`>= 0`) |
| `--use-session-representatives` | 선택 | `false` | 세션별로 하나의 대표 예시만 추출하여 카운트 및 할당 폴백에 적용 |
| `--ingestion-config` | 선택 | - | 커스텀 형태의 입력 처리를 위한 JSON 설정 파일 경로 |

### 4.1 Ingestion 설정 형태 (`--ingestion-config`)

설정 가능한 키:

- `id_fields`: `TopicDocument.id`로 사용할 필드 후보 (우선순위 순)
- `text_fields`: 텍스트로 직접 추출할 필드 후보 (우선순위 순)
- `payload_fields`: JSON 페이로드 내에서 폴백(fallback)으로 사용할 필드 후보
- `content_fields`: 연결하여 텍스트로 사용할 DB 열 이름 명시 (`field: value` 형식으로 연결됨)
- `question_fields`: 질문 텍스트 후보
- `response_fields`: 답변 텍스트 후보
- `session_id_fields`: `session_id` 후보
- `session_key_fields`: `session_id`를 조합하기 위해 사용할 기본 키 열 목록
- `count_field`: 빈도수를 나타내는 필드 이름 (기본값: `count`)
- `column_value_path`: 컬럼/값 쌍의 목록이 들어있는 데이터 내부 경로
- `column_name_field`, `column_value_field`: 컬럼/값 항목 내부에서 키와 값을 나타내는 필드 이름
- `max_text_chars`: 추출된 텍스트의 최대 길이 제한 (기본값: `4000`)

설정 예시:

```json
{
  "id_fields": ["account_id"],
  "payload_fields": ["payload"],
  "content_fields": ["query", "answer"],
  "session_key_fields": ["account_id", "thread_id"],
  "column_value_path": "columns",
  "column_name_field": "column",
  "column_value_field": "value"
}
```

## 5) 문제 해결 (Troubleshooting)

### 5.1 `cluster requires --base-url and --api-key` 오류

명령어 실행 시 두 인자를 모두 제공해야 합니다:

```bash
--base-url https://... --api-key ...
```

### 5.2 `base_url must be a valid http(s) URL` 오류

`http://` 또는 `https://`로 시작하는 유효한 엔드포인트 URL을 사용하세요.

### 5.3 임베딩 요청 실패 (Embedding request failures)

- 엔드포인트 네트워크 연결 상태 확인
- API 키 유효성 검증
- 최소 1줄의 입력 데이터로 단일 테스트 재시도

### 5.4 Smoke 테스트에서 Wheel을 찾을 수 없는 경우

스크립트에서 `Expected exactly one wheel` 오류 발생 시 아래 순서대로 빌드 환경을 초기화하세요:

```bash
rm -rf dist .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli
```

# Vector Topic Modeling User Manual

Package: `vector-topic-modeling`  
Python: `>=3.11`  
CLI: `vector-topic-modeling`

## 1) Installation

### 1.1 Prerequisites

- Python 3.11+
- `uv` (recommended for development and verification)

### 1.2 Install from source

```bash
git clone https://github.com/seonghobae/vector-topic-modeling.git
cd vector-topic-modeling
uv sync
```

### 1.3 Install from wheel

```bash
python3.11 -m pip install dist/vector_topic_modeling-<version>-py3-none-any.whl
```

### 1.4 Verify installation

```bash
vector-topic-modeling --help
vector-topic-modeling cluster --help
```

## 2) Quick Start

### 2.1 Python API

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
        TopicDocument(id="1", text="refund duplicate billing"),
        TopicDocument(id="2", text="cancel subscription refund"),
    ]
)

print(len(result.topics), len(result.assignments))
```

### 2.2 CLI

```bash
vector-topic-modeling cluster examples/sample_queries.jsonl \
  --output topics.json \
  --base-url "$LITELLM_API_BASE" \
  --api-key "$LITELLM_API_KEY" \
  --model text-embedding-3-large
```

Generic DB/JSON payload ingestion example:

```bash
vector-topic-modeling cluster examples/sample_db_rows.jsonl \
  --output topics.json \
  --ingestion-config examples/ingestion_config_db_columns.json \
  --base-url "$LITELLM_API_BASE" \
  --api-key "$LITELLM_API_KEY" \
  --model text-embedding-3-large
```

## 3) JSONL Input / Output

### 3.1 Input shape

One JSON object per line:

```json
{"id":"1","text":"refund duplicate billing","session_id":"s1","question":"...","response":"...","count":1}
```

Alternative rows can be DB-style column/value arrays or nested JSON payloads when
used with `--ingestion-config`.

### 3.2 Input field behavior

- `id`: preferred identifier; falls back to `document_id`, then row index
- `text`: defaults to `""` when absent
- `session_id`, `question`, `response`: optional
- `count`: defaults to `1`

When `--ingestion-config` sets `session_key_fields`, `session_id` is composed as
a deterministic primary-key bundle (`pk:{...}`) when no explicit
`session_id` field is present.

### 3.3 Output shape (`--output`)

Top-level keys:

- `topics`
- `assignments`
- `session_topic_counts`

## 4) CLI Options Explained

Command pattern:

```bash
vector-topic-modeling cluster INPUT_JSONL --output OUTPUT_JSON
```

| Option | Required | Default | Description |
| --- | --- | --- | --- |
| `input_path` | yes | - | Input JSONL file path |
| `--output` | yes | - | Output JSON path |
| `--base-url` | runtime-required | - | OpenAI-compatible embedding URL |
| `--api-key` | runtime-required | - | API key used for embedding requests |
| `--model` | no | `text-embedding-3-large` | Embedding model |
| `--similarity-threshold` | no | `0.85` | Clustering similarity threshold |
| `--ingestion-config` | no | - | JSON config for generic row ingestion |

Example with stricter threshold:

```bash
vector-topic-modeling cluster input.jsonl \
  --output topics.json \
  --base-url "$LITELLM_API_BASE" \
  --api-key "$LITELLM_API_KEY" \
  --model text-embedding-3-large \
  --similarity-threshold 0.90
```

### 4.1 Ingestion config shape (`--ingestion-config`)

Config keys:

- `id_fields`: ordered candidates for `TopicDocument.id`
- `text_fields`: ordered candidates for direct text extraction
- `payload_fields`: ordered candidates for JSON payload fallback
- `content_fields`: explicit DB column names to concatenate (`field: value`)
- `session_id_fields`: ordered candidates for explicit `session_id`
- `session_key_fields`: ordered primary-key columns used to compose `session_id`
- `column_value_path`: row key containing list-style column/value pairs
- `column_name_field`, `column_value_field`: keys used inside column/value entries

Example:

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

## 5) Troubleshooting

### 5.1 `cluster requires --base-url and --api-key`

Provide both arguments:

```bash
--base-url https://... --api-key ...
```

### 5.2 `base_url must be a valid http(s) URL`

Use an endpoint starting with `http://` or `https://`.

### 5.3 Embedding request failures

- Verify endpoint reachability
- Verify API key
- Retry with a minimal single-row input

### 5.4 Smoke test cannot find wheel

If the script reports `Expected exactly one wheel`:

```bash
rm -rf dist .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli
```

## 6) Release Operations (Maintainers)

### 6.1 Local release verification

```bash
uv sync --extra dev
uv run pytest -q
uv run python scripts/docstring_coverage.py --min-percent 100
rm -rf dist .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli
```

### 6.2 Automated release flow

1. Push a SemVer tag prefixed with `v`:

   ```bash
   git checkout main
   git pull --ff-only
   git tag v0.1.1
   git push origin v0.1.1
   ```

2. `.github/workflows/release.yml` verifies tests/build/smoke and creates a
   GitHub Release with built artifacts.
3. `.github/workflows/publish.yml` then runs on `release.published` and uploads
   to PyPI using PyPI Trusted Publishing (OIDC).

### 6.3 Manual release trigger

You can also run `release.yml` via **workflow_dispatch** with an existing tag.

## 7) Sequence Diagrams

### 7.1 CLI clustering runtime flow

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant C as CLI (vector-topic-modeling)
    participant M as TopicModeler
    participant P as OpenAICompatEmbeddingProvider
    participant E as Embedding API (/v1/embeddings)
    participant G as Clustering (adaptive + rescue)
    participant O as Output JSON file

    U->>C: vector-topic-modeling cluster INPUT_JSONL --output OUTPUT_JSON ...
    C->>C: Parse args + validate --base-url/--api-key
    C->>C: Load JSONL -> TopicDocument[]
    C->>M: fit_predict(documents)

    M->>M: Normalize text, build digests/counts, unique_texts
    M->>P: embed(unique_texts)
    P->>E: POST /v1/embeddings {model, input[]}
    E-->>P: 200 {data:[{index, embedding}, ...]}
    P-->>M: vectors[] (index-aligned)

    M->>G: adaptive_greedy_cluster(items, threshold, bounds)
    G-->>M: clusters + chosen_threshold
    M->>G: rescue_display_dominance(...)
    G-->>M: final clusters

    M->>M: stable_topic_id + assignments + session_topic_counts
    M-->>C: TopicModelResult
    C->>O: Write topics/assignments/session_topic_counts as JSON
    O-->>U: OUTPUT_JSON ready
```

### 7.2 Release automation flow

```mermaid
sequenceDiagram
    autonumber
    participant M as Maintainer
    participant GH as GitHub
    participant R as release.yml
    participant REL as GitHub Release
    participant P as publish.yml
    participant PY as PyPI

    M->>GH: git push origin vX.Y.Z
    GH->>R: Trigger on push.tags (v*)
    R->>R: Checkout tagged commit + validate SemVer tag
    R->>R: uv sync --extra dev
    R->>R: pytest + build + smoke_installed_cli
    R->>R: Generate SHA256SUMS for dist/*
    R->>REL: Create/update release and upload dist artifacts

    REL-->>GH: release.published event
    GH->>P: Trigger publish workflow
    P->>P: uv sync --extra dev
    P->>P: Re-run pytest + build + smoke gate
    P->>PY: pypa/gh-action-pypi-publish (dist/*)
    PY-->>M: New package version available
```

# Vector Topic Modeling

[![CI](https://github.com/seonghobae/vector-topic-modeling/actions/workflows/ci.yml/badge.svg)](https://github.com/seonghobae/vector-topic-modeling/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

Standalone embedding-based topic modeling software for vector workflows.

## What it provides

- dependency-light clustering kernel
- session-aware representative selection
- safe text shaping/redaction for embedding input
- generic ingestion for DB column-value rows and JSON payloads
- provider-driven `TopicModeler` API
- JSONL-oriented CLI for standalone runs

## Install

Install from a local checkout today:

```bash
git clone https://github.com/seonghobae/vector-topic-modeling.git
cd vector-topic-modeling
uv sync
```

For local wheel installation during development or release validation:

```bash
python3.11 -m pip install dist/vector_topic_modeling-0.1.0-py3-none-any.whl
```

The package requires Python 3.11 or newer.

## Development install

```bash
uv sync --extra dev
```

## Verify locally

```bash
uv run pytest -q
uv run python scripts/docstring_coverage.py --min-percent 100
# Delete any previous build artifacts and smoke-test virtual environment.
# On POSIX shells: rm -rf dist .venv-smoke-cli
# On Windows PowerShell: Remove-Item -Recurse -Force dist, .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli
```

The repository release gate also smoke-tests the installed
`vector-topic-modeling` console script with:

```bash
uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli
```

## Quick start

```python
from vector_topic_modeling import TopicDocument, TopicModelConfig, TopicModeler

class FakeEmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]

modeler = TopicModeler(
    embedding_provider=FakeEmbeddingProvider(),
    config=TopicModelConfig(similarity_threshold=0.85),
)

result = modeler.fit_predict([
    TopicDocument(id="1", text="refund duplicate billing"),
])
```

See [`examples/`](./examples/) for end-to-end local usage samples.

Detailed usage and troubleshooting guidance is in
[`docs/user-manual.md`](./docs/user-manual.md).

## JSONL CLI input shapes

### Legacy flat shape

Each line can contain:

```json
{"id":"1","text":"refund duplicate billing","session_id":"s1","question":"...","response":"...","count":1}
```

### Generic DB / JSON payload shape

You can also pass arbitrary rows (DB-export style columns or nested JSON payloads)
and map them with `--ingestion-config`.

Example config: [`examples/ingestion_config_db_columns.json`](./examples/ingestion_config_db_columns.json)

Example rows: [`examples/sample_db_rows.jsonl`](./examples/sample_db_rows.jsonl)

Run the CLI with an OpenAI-compatible embedding endpoint:

```bash
vector-topic-modeling cluster input.jsonl \
  --output topics.json \
  --base-url https://your-gateway.example.com \
  --api-key "$LITELLM_API_KEY" \
  --model text-embedding-3-large
```

With generic ingestion mapping:

```bash
vector-topic-modeling cluster examples/sample_db_rows.jsonl \
  --output topics.json \
  --ingestion-config examples/ingestion_config_db_columns.json \
  --base-url https://your-gateway.example.com \
  --api-key "$LITELLM_API_KEY" \
  --model text-embedding-3-large
```

Sample files:

- [`examples/sample_queries.jsonl`](./examples/sample_queries.jsonl)
- [`examples/sample_db_rows.jsonl`](./examples/sample_db_rows.jsonl)
- [`examples/ingestion_config_db_columns.json`](./examples/ingestion_config_db_columns.json)
- [`examples/cli_openai_compat.sh`](./examples/cli_openai_compat.sh)
- [`examples/basic_in_memory_provider.py`](./examples/basic_in_memory_provider.py)

## Scope

- This package intentionally excludes web framework routes, persistence,
  background jobs, export pipelines, and email delivery concerns.

## Repository guides

- [Contributing](./CONTRIBUTING.md)
- [User manual](./docs/user-manual.md)
- [Security policy](./SECURITY.md)
- [Support](./SUPPORT.md)
- [Changelog](./CHANGELOG.md)
- [Maintainer release guide](./docs/maintainers/releasing.md)

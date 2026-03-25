# Deploy / Release Runbook

This repository publishes package artifacts from GitHub and treats built
wheels/sdists as the deployable output.

## Local release verification

```bash
uv sync --extra dev
uv run pytest -q
# Delete any previous build artifacts and smoke-test virtual environment.
# On POSIX shells: rm -rf dist .venv-smoke-cli
# On Windows PowerShell: Remove-Item -Recurse -Force dist, .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist \
  --venv-dir .venv-smoke-cli
```

## Artifacts

- Wheel: `dist/vector_topic_modeling-<version>-py3-none-any.whl`
- Source distribution: `dist/vector_topic_modeling-<version>.tar.gz`

## Smoke install

```bash
uv run python scripts/smoke_installed_cli.py --dist-dir dist \
  --venv-dir .venv-smoke-cli
```

The smoke gate validates both the installed wheel import surface and the
shipped `vector-topic-modeling` console script help paths.

## Publishing status

- GitHub is the canonical remote and release surface.
- `.github/workflows/publish.yml` publishes on GitHub Release events
  when `PYPI_API_TOKEN` is configured.
- `main` branch protection must require `workflow-lint`,
  `test-and-build (3.11)`, and `test-and-build (3.12)` before merge.
- No long-running deploy queue or runtime service exists; package build
  artifacts are the deployable output.

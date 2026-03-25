# AGENTS.md

## Project overview

- This repository contains a standalone vector topic-modeling package.
- Keep the package dependency-light and runtime-independent.

## Build / test

- `uv run pytest -q`
- `uv run python -m build`
- `uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli`

## Code style

- Prefer small pure functions and explicit dataclasses.
- Keep the public API exported from `src/vector_topic_modeling/__init__.py`.

## Documentation

- Update `ARCHITECTURE.md` when structure or runtime behavior changes.
- Keep canonical docs under `docs/` in sync with implementation.
- Keep release/CI guidance aligned with the actual `uv` workflow and
  required GitHub checks.

## Security governance

- Keep `.github/dependabot.yml` aligned with repository dependency update
  policy for `pip` and `github-actions`.
- If a Dependabot alert is dismissed without an upstream patch, update
  `docs/security/dependency-vulnerability-exceptions.md` in the same
  change set.

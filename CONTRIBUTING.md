# Contributing

Thanks for contributing to `vector-topic-modeling`.

## Development setup

```bash
git clone https://github.com/seonghobae/vector-topic-modeling.git
cd vector-topic-modeling
uv sync --extra dev
```

## Verification

Run these before opening a pull request:

```bash
uv run pytest -q
uv run python scripts/docstring_coverage.py --min-percent 100
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli
```

If you change examples, CLI behavior, or packaging metadata, verify those
manually as well.

## Branching and pull requests

- Create a branch from `dev`.
- Follow the default merge path: feature branches merge into `dev`, then
  `dev` merges into `main`.
- Keep pull requests small and focused.
- Update docs when changing behavior, workflows, or release expectations.
- Link relevant issues when they exist.

## Commit style

This repository prefers concise conventional-style commit messages such as:

- `feat: add x`
- `fix: correct y`
- `docs: clarify z`

## Scope guardrails

- Keep this package runtime-independent from external systems.
- Do not reintroduce webapp, database, scheduler, or email/export coupling.
- Favor small pure functions and deterministic tests.

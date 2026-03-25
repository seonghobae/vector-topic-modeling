# Public Wording Sanitization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task.

## Goal

Remove explicit identity traces from public repository text while
preserving technical scope boundaries.

## Architecture

Normalize user-visible wording, sanitize package metadata
links/descriptions, and add a regression guard that fails if blocked
identity phrases reappear.

## Tech Stack

- Markdown/TOML/Python text edits
- pytest governance regression test

---

## Task 1: Sanitize public-facing wording

### Task 1 files

- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/engineering/acceptance-criteria.md`
- Modify: `src/vector_topic_modeling/__init__.py`

### Task 1 steps

1. Replace explicit identity strings with neutral wording.
1. Keep boundary meaning and exclusion guardrails intact.

## Task 2: Sanitize package metadata

### Task 2 files

- Modify: `pyproject.toml`

### Task 2 steps

1. Replace description text that references explicit identity.
1. Remove explicit external identity URL keys and keep local notes only.

## Task 3: Sanitize historical design wording

### Task 3 files

- Modify: `docs/plans/2026-03-24-repository-polish-design.md`
- Modify: historical topic-modeling plan file
- Modify: `docs/plans/2026-03-25-public-wording-sanitization-design.md`

### Task 3 steps

1. Replace remaining explicit identity identifiers in plan docs.
1. Preserve design intent while removing direct identity mentions.

## Task 4: Add phrase-regression guard

### Task 4 files

- Create: `tests/test_public_wording_sanitization.py`
- Modify: `tests/test_service.py`

### Task 4 steps

1. Add deterministic scan assertions for blocked phrases across key text
   file types.
1. Remove company-identifying literal test fixtures where not functionally
   required.

## Task 5: End-to-end verification

### Task 5 steps

1. Run full tests:

```bash
uv run pytest -q
```

1. Build and smoke test the packaged CLI:

```bash
rm -rf dist .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist \
  --venv-dir .venv-smoke-cli
```

1. Run mypy baseline:

```bash
uvx mypy --config-file pyproject.toml \
  --exclude '(^|[\\/])(research_repos)([\\/]|$)' .
```

# Canonical Verification Alignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task.

## Goal

Keep canonical engineering docs, CI release gates, and local maintainer
verification commands aligned so release checks cannot drift silently.

## Architecture

Treat canonical docs as release-governance inputs, align them with the
current CI and publish workflows, and add a deterministic pytest guard
for command-fragment drift.

## Tech Stack

- Python 3.11+
- uv
- pytest
- Markdown docs
- GitHub Actions

---

## Task 1: Align canonical engineering docs

### Task 1 files

- Modify: `docs/engineering/acceptance-criteria.md`
- Modify: `docs/engineering/harness-engineering.md`

### Task 1 steps

1. Define required fragments:
   - `uv run pytest -q`
   - `uv run python -m build`
   - `scripts/smoke_installed_cli.py` with `--dist-dir` and `--venv-dir`
1. Define forbidden stale snippets in harness docs:
   - `python3 -m pytest -q`
   - `python3 -m build`
1. Update docs to satisfy required fragments and remove forbidden snippets.

## Task 2: Add regression test for docs drift

### Task 2 files

- Create: `tests/test_docs_release_gate_alignment.py`

### Task 2 steps

1. Add deterministic string-fragment assertions for required and
   forbidden command snippets.
1. Run targeted test:

```bash
uv run pytest tests/test_docs_release_gate_alignment.py -q
```

1. Confirm green after Task 1 updates.

## Task 3: Improve worktree hygiene

### Task 3 files

- Modify: `.gitignore`

### Task 3 steps

1. Add ignore entries for local cache and automation artifacts:
   - `.mypy_cache/`
   - `.ruff_cache/`
   - `registered_agents.json`
   - `task_agent_mapping.json`
1. Verify status no longer reports those artifacts as untracked noise.

## Task 4: End-to-end verification

### Task 4 steps

1. Run full test suite:

```bash
uv run pytest -q
```

1. Run build and installed-wheel smoke verification:

```bash
rm -rf dist .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist \
  --venv-dir .venv-smoke-cli
```

1. Run mypy baseline check:

```bash
uvx mypy --config-file pyproject.toml \
  --exclude '(^|[\\/])(research_repos)([\\/]|$)' .
```

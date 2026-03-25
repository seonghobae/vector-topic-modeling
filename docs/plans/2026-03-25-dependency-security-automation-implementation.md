# Dependency Security Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task.

## Goal

Codify dependency-security automation and unpatchable-advisory governance so
the repository does not rely on ad-hoc manual dismissals.

## Architecture

Add in-repo Dependabot automation for dependency update cadence, record a
canonical vulnerability exception register under `docs/security/`, and add
pytest drift guards for both config and docs.

## Tech Stack

- GitHub Dependabot config (`.github/dependabot.yml`)
- Markdown canonical docs
- pytest string-fragment governance checks

---

## Task 1: Add Dependabot baseline automation

### Task 1 files

- Create: `.github/dependabot.yml`

### Task 1 steps

1. Add Dependabot version 2 config.
1. Add weekly `pip` update block for repo root (`directory: "/"`).
1. Add weekly `github-actions` update block.
1. Set bounded `open-pull-requests-limit` per ecosystem.

## Task 2: Add canonical vulnerability exception governance

### Task 2 files

- Modify: `docs/security/api-security-checklist.md`
- Create: `docs/security/dependency-vulnerability-exceptions.md`
- Modify: `ARCHITECTURE.md`
- Modify: `AGENTS.md`

### Task 2 steps

1. Extend API security checklist with dependency supply-chain controls and
   exception-governance requirements.
1. Add canonical exception register doc and record alert #1
   (`GHSA-5239-wwwm-4pmq`) with:
   - reason for temporary dismissal,
   - required re-evaluation triggers,
   - owner/last-reviewed metadata.
1. Update architecture operations state to include Dependabot automation
   and exception-register workflow.
1. Update AGENTS guidance to keep security exception register in sync when
   dismissing advisories.

## Task 3: Add regression tests for automation/docs drift

### Task 3 files

- Create: `tests/test_dependency_security_governance.py`

### Task 3 steps

1. Add tests that assert `.github/dependabot.yml` includes required
   ecosystems/fragments.
1. Add tests that assert security docs include required governance fragments
   and the current advisory id.
1. Run targeted tests:

```bash
uv run pytest tests/test_dependency_security_governance.py -q
```

## Task 4: End-to-end verification

### Task 4 steps

1. Run full test suite:

```bash
uv run pytest -q
```

1. Run build and installed-wheel smoke:

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

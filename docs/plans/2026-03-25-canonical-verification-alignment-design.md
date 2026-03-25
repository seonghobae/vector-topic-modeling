# Canonical Verification Alignment Design

Date: 2026-03-25

## Context

The repository's hosted gates (`ci.yml`, `publish.yml`) enforce three release
signals: tests, package build, and installed-wheel CLI smoke verification.
However, two canonical engineering docs still drift from that enforced path:

- `docs/engineering/acceptance-criteria.md` omits the installed-wheel CLI smoke step.
- `docs/engineering/harness-engineering.md` still presents `python3 -m ...` commands
  while the repository standard is `uv run ...`.

The worktree also accumulates local automation artifacts (`registered_agents.json`,
`task_agent_mapping.json`) that are not ignored.

## Constraints

- Keep runtime behavior unchanged; this is a verification-governance hardening pass.
- Canonical docs under `docs/` must remain the authoritative source.
- Keep guidance cross-platform where cleanup commands differ.
- Preserve CI/publish parity: local maintainer commands should map 1:1
  to workflow checks.

## Approaches considered

### Approach 1: Update docs only

Edit canonical docs so command sequences match workflows.

**Pros:** minimal diff, very low risk.
**Cons:** no regression guard; drift can silently reappear.

### Approach 2: Update docs + add docs-consistency regression test (recommended)

Align canonical docs and add a small deterministic pytest that checks required
verification fragments and rejects stale `python3 -m ...` snippets in
`harness-engineering.md`.

**Pros:** closes current gap and prevents relapse with CI evidence.
**Cons:** introduces one documentation-focused test to maintain.

### Approach 3: Move command source to generated docs

Generate docs from a single machine-readable command manifest.

**Pros:** strongest centralization.
**Cons:** disproportionate complexity for this repository size.

## Recommended design

Implement Approach 2 with three workstreams:

1. **Canonical docs alignment**
   - Update acceptance criteria to include installed-wheel CLI smoke
     verification.
   - Rewrite harness guidance to uv-first commands with explicit
     POSIX/PowerShell cleanup.

2. **Regression guard in tests**
   - Add a pytest check that asserts required command fragments exist in
     canonical docs.
   - Explicitly block stale `python3 -m pytest` / `python3 -m build`
     snippets in harness docs.

3. **Worktree hygiene**
   - Extend `.gitignore` for local automation artifacts and common local caches.

## Decisions recorded

- Chosen approach: **docs + regression test + ignore hygiene**.
- No workflow YAML changes are needed because workflows already enforce
  the target gate.
- The canonical engineering docs are treated as release-governance code
  and covered by tests.

## Verification plan

- `uv run pytest -q`
- `uv run python -m build`
- `uv run python scripts/smoke_installed_cli.py`
  with `--dist-dir dist` and `--venv-dir .venv-smoke-cli`

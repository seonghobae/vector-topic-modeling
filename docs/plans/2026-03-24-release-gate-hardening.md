# Release Gate Hardening Implementation Plan

## Goal

Close the highest-priority release risk by hardening CI/release
verification around the shipped CLI and enforcing merge protection on
`main`.

## Architecture

Extend the existing GitHub Actions workflow so the installed wheel smoke
test also exercises the published console script, then align repository
docs with the actual `uv`-based verification path and release gates.
After the repo changes are pushed, configure GitHub branch protection so
the CI workflow must pass before merge.

## Tech Stack

Python 3.11+, uv, pytest, GitHub Actions, GitHub branch protection.

---

## Task 1: Add failing installed-CLI smoke tests

**Files:**

- Create: `tests/test_smoke_installed_cli.py`
- Modify: `scripts/smoke_installed_cli.py`

### Task 1 / Step 1: Write the failing test

Add tests that define the console-script help behavior expected from
the packaged CLI surface.

### Task 1 / Step 2: Run test to verify it fails

Run: `uv run pytest tests/test_smoke_installed_cli.py -q`
Expected: FAIL because the new CLI help expectations are not covered
yet.

### Task 1 / Step 3: Write minimal implementation

Adjust CLI behavior only if the new tests reveal a real gap.

### Task 1 / Step 4: Run test to verify it passes

Run: `uv run pytest tests/test_smoke_installed_cli.py -q`
Expected: PASS.

## Task 2: Extend CI/release smoke verification

**Files:**

- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/publish.yml`

### Task 2 / Step 1: Write the failing test/check

Define installed-wheel smoke checks that must run
`vector-topic-modeling --help` and `vector-topic-modeling cluster --help`
in CI/release verification.

### Task 2 / Step 2: Run verification to verify current gap

Run: `uv run python -m build` and inspect workflow definitions.
Expected: current workflows smoke-test only importability, not the
installed CLI entrypoint.

### Task 2 / Step 3: Write minimal implementation

Update workflows to build once and smoke-test the installed wheel
console script.

### Task 2 / Step 4: Run verification to verify it passes

Run: `uv run pytest -q && uv run python -m build`
Expected: PASS locally, with workflow definitions still valid.

## Task 3: Align canonical docs and repo agent guidance

**Files:**

- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `docs/maintainers/releasing.md`
- Modify: `docs/operations/deploy-runbook.md`
- Modify: `ARCHITECTURE.md`

### Task 3 / Step 1: Write the failing doc expectation

Record the actual supported verification commands and release gate
expectations.

### Task 3 / Step 2: Verify current mismatch

Run: `python3 -m build`
Expected: FAIL in the current environment, proving `AGENTS.md` is stale.

### Task 3 / Step 3: Write minimal implementation

Update canonical docs to use `uv run ...` verification and document
installed-CLI smoke testing plus required CI protection.

### Task 3 / Step 4: Run verification to verify it passes

Run: `uv run pytest -q && uv run python -m build`
Expected: PASS, docs aligned with actual behavior.

## Task 4: Enforce GitHub merge gates on main

**Files:**

- Remote config only: branch protection / required status checks

### Task 4 / Step 1: Verify current gap

Run: `gh api repos/seonghobae/vector-topic-modeling/branches/main/protection/required_status_checks`
Expected: 404 / missing required status checks.

### Task 4 / Step 2: Apply minimal implementation

Configure `main` branch protection to require pull requests,
conversation resolution, and the `workflow-lint` /
`test-and-build (3.11)` / `test-and-build (3.12)` status checks.

### Task 4 / Step 3: Verify it passes

Run:
`gh api repos/seonghobae/vector-topic-modeling/branches/main/protection`
and
`gh api repos/seonghobae/vector-topic-modeling/branches/main/protection/required_status_checks`
Expected: required checks are present.

## Notes for maintainers

- This document records the implementation work that landed in the
  repository so future maintainers can see why the smoke script, docs,
  and branch protection changed together.
- The canonical day-to-day guidance now lives in `AGENTS.md`,
  `docs/operations/deploy-runbook.md`,
  `docs/maintainers/releasing.md`, and
  `docs/workflow/one-day-delivery-plan.md`.

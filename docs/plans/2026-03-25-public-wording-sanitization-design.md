# Public Wording Sanitization Design

Date: 2026-03-25

## Context

Public-facing repository text currently contains explicit upstream repository
identity references (organization/repository names) that are more specific
than needed for package users.

Goal: keep scope boundaries clear while reducing unnecessary identity
exposure in public docs and metadata.

## Constraints

- Preserve technical meaning: this package is standalone and excludes webapp/
  database/worker/export concerns.
- Keep runtime behavior unchanged (wording-only changes).
- Keep canonical docs and metadata consistent after wording changes.
- Add a regression guard against reintroducing explicit identity text.

## Approaches considered

### Approach 1: README-only adjustment

Change only the top README tagline.

**Pros:** smallest diff.
**Cons:** explicit references remain in metadata/docs/tests and continue to
surface publicly.

### Approach 2: Comprehensive wording normalization + regression test (recommended)

Update all current user-visible surfaces and add a test that blocks explicit
identity phrases from reappearing.

**Pros:** closes the issue holistically and prevents recurrence.
**Cons:** broader doc churn.

### Approach 3: Remove context text entirely

Delete historical context sections.

**Pros:** maximal concealment.
**Cons:** loses useful architectural context and boundary rationale.

## Recommended design

Implement Approach 2 with three workstreams:

1. **Normalize wording across public surfaces**
   - Replace explicit upstream identity phrases with neutral wording.
   - Keep scope/exclusion statements technically equivalent.

2. **Metadata sanitization**
   - Update `pyproject.toml` description and remove explicit external
     identity URLs.
   - Keep homepage/repository/issues/changelog links to this repository.

3. **Regression guard**
   - Add a deterministic pytest that asserts blocked phrases are absent from
     key public-facing files.

## Decisions recorded

- Use neutral wording instead of removing context entirely.
- Remove explicit identity links from package metadata.
- Add CI-backed phrase guard tests for key surfaces.

## Verification plan

- `uv run pytest -q`
- `uv run python -m build`
- `uv run python scripts/smoke_installed_cli.py --dist-dir dist`
  `--venv-dir .venv-smoke-cli`
- `uvx mypy --config-file pyproject.toml`
  `--exclude '(^|[\\/])(research_repos)([\\/]|$)' .`

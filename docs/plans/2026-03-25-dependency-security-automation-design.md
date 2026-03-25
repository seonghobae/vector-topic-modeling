# Dependency Security Automation Design

Date: 2026-03-25

## Context

Repository delivery gates (tests/build/smoke) are green, and open issues/PRs
are currently zero. Security state still depends on one manually dismissed
Dependabot advisory for `Pygments` (`GHSA-5239-wwwm-4pmq`) with no patched
upstream version yet.

Current gap:

- `.github/dependabot.yml` is missing, so dependency update cadence is not
  codified in-repo.
- Canonical security docs do not define how dismissed/unpatchable advisories
  must be tracked and re-evaluated.

## Constraints

- Keep package runtime behavior unchanged.
- Use repository-local, automatable controls first.
- Avoid introducing new runtime dependencies for governance checks.
- Keep canonical docs (`docs/security/**`) authoritative and testable.

## Approaches considered

### Approach 1: Documentation-only policy

Add security policy text without automation changes.

**Pros:** lowest implementation effort.
**Cons:** policy drift risk remains high without update automation.

### Approach 2: Dependabot automation + canonical exception register + tests (recommended)

Add Dependabot config for `pip` and `github-actions`, document exception
handling in canonical docs, and add lightweight regression tests for config
and docs fragments.

**Pros:** closes immediate governance gap and adds CI evidence for drift.
**Cons:** modest increase in doc/test maintenance.

### Approach 3: External security scanner pipeline only

Rely on separate SCA toolchain and dashboards without in-repo controls.

**Pros:** potentially richer scanning.
**Cons:** weaker local repo ownership and higher operational complexity.

## Recommended design

Implement Approach 2 with three workstreams:

1. **Security automation baseline**
   - Add `.github/dependabot.yml` updates for:
     - `pip` ecosystem at repo root
     - `github-actions` ecosystem
   - Use weekly schedule and bounded open PR limits.

2. **Canonical vulnerability exception policy**
   - Extend `docs/security/api-security-checklist.md` with dependency
     supply-chain and exception-governance requirements.
   - Add `docs/security/dependency-vulnerability-exceptions.md` as the
     canonical register for dismissed advisories, with required fields and
     re-evaluation triggers.

3. **Regression guardrails**
   - Add tests that assert:
     - Dependabot config exists and includes required ecosystems.
     - Security docs include exception-governance fragments and the current
       advisory register entry.

## Decisions recorded

- Chosen approach: **Dependabot automation + canonical exception register + tests**.
- Keep advisory #1 dismissed as `tolerable_risk` until upstream fix exists,
  but make re-evaluation criteria explicit in-repo.
- Treat security-governance docs as CI-verified assets.

## Verification plan

- `uv run pytest -q`
- `uv run python -m build`
- `uv run python scripts/smoke_installed_cli.py --dist-dir dist`
  `--venv-dir .venv-smoke-cli`
- `uvx mypy --config-file pyproject.toml`
  `--exclude '(^|[\\/])(research_repos)([\\/]|$)' .`

# Repository Polish Design

<!-- markdownlint-disable MD013 MD022 -->

Date: 2026-03-24

## Context

`vector-topic-modeling` is now a real GitHub repository with a protected `main` branch, a single initial release-baseline commit, package/test/build automation, and no open issues or PRs. The code itself is in reasonable shape, but the repository still feels closer to an initial code drop than a polished public Python package.

## Constraints

- Keep the package source and runtime behavior stable; this pass is primarily repository and maintainer ergonomics.
- Prefer changes that improve trust, discoverability, and contributor readiness without adding heavy new infrastructure.
- Use safe defaults: local build/test remains authoritative; publish automation may exist even if PyPI secrets are not yet configured.
- Preserve runtime boundary clarity while shifting canonical package
  metadata to this repository.

## Approaches considered

### Approach 1: Community-health baseline only
Add `CONTRIBUTING.md`, `SECURITY.md`, issue templates, PR template, and governance docs.

**Pros:** strongest contributor-facing signal, low risk.
**Cons:** still leaves the repo without a clear release story, changelog, or maintainers' operating model.

### Approach 2: Release-ready package polish only
Focus on `CHANGELOG.md`, release workflow, badges, package URLs, and maintainer release docs.

**Pros:** strongest package-consumer signal, aligns with Python packaging expectations.
**Cons:** still leaves repo interaction patterns underdefined for contributors and issue triage.

### Approach 3: Repository completeness baseline (recommended)
Combine the highest-value pieces of community health and release polish in one coherent pass.

**Pros:** best overall repository completeness; turns the repo into a credible OSS package with contributor, maintainer, and consumer guidance.
**Cons:** touches more files, so doc consistency must be verified carefully.

## Recommended design

Implement a repository completeness baseline with four workstreams:

1. **Repository metadata and docs**
   - Refresh `README.md` so it reflects the real GitHub repo state.
   - Add `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, and `CODE_OF_CONDUCT.md`.
   - Update `pyproject.toml` URLs to point at this repository's homepage/issues/changelog.

2. **GitHub collaboration scaffolding**
   - Add issue forms, a PR template, and `CODEOWNERS`.
   - Keep the templates lightweight and aligned with the current single-maintainer reality.

3. **Release and publish path**
   - Add a `publish.yml` workflow that builds and publishes on GitHub release events using trusted publishing or API-token-based PyPI upload.
   - Add a maintainer-facing release runbook under `docs/maintainers/`.

4. **Examples and onboarding**
   - Add a minimal `examples/` directory with one Python in-memory example, one sample JSONL input, and one CLI shell example.
   - Link examples from the README so users can validate the package quickly.

## Decisions recorded

- Keep the package version at `0.1.0`; this pass improves repository completeness, not package semantics.
- Use Keep a Changelog format for future maintainability.
- Add release automation now even though publishing secrets may not yet be configured; the workflow documents the expected path and fails safely if credentials are missing.
- Prefer short, concrete docs over comprehensive policy sprawl.

## Testing and verification plan

- `uv run pytest -q`
- `uv run python -m build`
- Smoke-install the wheel in a Python 3.11 venv
- Re-check `git status` and current branch before commit/push

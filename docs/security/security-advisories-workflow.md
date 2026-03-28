# GitHub Security Advisories Workflow

This document is the canonical process for private vulnerability intake,
triage, remediation, release coordination, and disclosure for this repository.

## Scope

- Runtime/library vulnerabilities in this repository
- Dependency vulnerabilities that materially affect shipped artifacts
- CI/release workflow vulnerabilities that could compromise artifacts

## Roles and ownership

- **Reporter**: submits a private report via GitHub Security Advisories.
- **Triage owner**: validates impact/severity and owns advisory state.
- **Fix owner**: prepares patch and regression tests.
- **Release owner**: coordinates fixed artifact publication and advisory publish.

Unless delegated, the repository maintainer is all four roles.

## Intake and private reporting

- Preferred channel: GitHub Security Advisories report form
  (<https://github.com/seonghobae/vector-topic-modeling/security/advisories/new>).
- Never request public issue creation for vulnerability details.
- Required report details:
  - affected version/commit range,
  - reproduction details or proof-of-concept,
  - impact assessment,
  - mitigation ideas (if available).

## Triage and severity

- Create or update a Draft advisory in `Security > Advisories` for valid reports.
- Record severity (`critical`, `high`, `moderate`, `low`) with
  repository-specific rationale.
- Record affected ranges and intended fixed version.
- Response targets:
  - initial acknowledgement within 3 business days,
  - triage decision within 5 business days.

## Private fix workflow

- Use private coordination while the fix is not released.
- Add or update regression tests that fail pre-fix and pass post-fix.
- Verify with canonical release gates:
  - `uv run pytest -q`
  - `uv run python scripts/docstring_coverage.py --min-percent 100`
  - `uv run python -m build`
  - `uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli`

## Publishing workflow

Publish in this order:

1. Publish fixed artifacts (tag/release).
2. Publish the GitHub Security Advisory.
3. Validate advisory metadata includes:
   - advisory ID (GHSA/CVE when available),
   - affected versions,
   - first fixed version,
   - remediation notes and release/commit references.
4. Ensure release notes / `CHANGELOG.md` include a security-fix summary and
   advisory reference (GHSA/CVE when available).

## Dependency advisory handling

- If an advisory is temporarily unpatchable and dismissed as tolerable risk,
  track it in `docs/security/dependency-vulnerability-exceptions.md`.
- When a patched dependency becomes available and adopted, move it from Active
  to Resolved in the same change set.

## Dry-run rehearsal log

Record periodic tabletop rehearsal evidence in this format:

- Date (UTC): 2026-03-25
- Elapsed time: 1h 10m (tabletop intake-to-publish simulation)
- Scenario: simulated provider-side vulnerability intake and
  coordinated release/disclosure sequence
- Outcome: completed from intake checklist to publish-order verification
- Follow-up improvements: added canonical workflow and CI governance tests

## References

- `SECURITY.md`
- `docs/security/api-security-checklist.md`
- `docs/security/dependency-vulnerability-exceptions.md`
- `docs/maintainers/releasing.md`
- `docs/operations/deploy-runbook.md`

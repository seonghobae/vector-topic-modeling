# API Security Checklist

This repository does not expose an inbound HTTP API. Its only
network-facing component is the outbound OpenAI-compatible embedding
client in `src/vector_topic_modeling/providers/openai_compat.py`.

## Applicable checks

- Require explicit `base_url` and `api_key` from the caller.
- Restrict provider URLs to `http` or `https` schemes.
- Never log API keys or request bodies containing credentials.
- Strip NUL bytes and redact sensitive text before outbound embedding requests.
- Keep provider tests network-free and validate parsing/error paths locally.

## Dependency supply-chain checks

- Keep `.github/dependabot.yml` present and configured for `pip` and
  `github-actions` ecosystems.
- `dependency-review.yml` runs on every PR and fails on moderate-severity
  (or above) known vulnerabilities in added or changed dependencies.
- `dependency-submission.yml` submits dependency snapshots for `pip` and
  `uv.lock` so Dependency Review can evaluate PR-head dependency metadata.
- `dependency-review.yml` enables `retry-on-snapshot-warnings: true` to
  reduce non-actionable snapshot warning noise while preserving vulnerability
  gate enforcement.
- `dependency-review.yml` posts PR summary comments only on failures
  (`comment-summary-in-pr: on-failure`) so transient non-blocking warnings do
  not drown out actionable review failures.
- Review dependency-update PRs promptly and keep the lock file current via
  the normal `uv` workflow.
- If a vulnerability has no patched upstream version, do not leave it as
  implicit knowledge: record and maintain it in
  `docs/security/dependency-vulnerability-exceptions.md`.
- Re-evaluate each recorded exception whenever one of the following occurs:
  - upstream advisory metadata changes (patched version, severity, scope),
  - dependency graph changes (`uv.lock` refresh or dependency additions),
  - before each tagged release cut.
- If a previously dismissed advisory becomes patchable and the repository
  upgrades to the patched version, close the exception in the same change set:
  - remove it from active entries in
    `docs/security/dependency-vulnerability-exceptions.md`,
  - add it under resolved entries with fixed version (`uv.lock`), PR/commit
    link, date, and owner,
  - verify the advisory is no longer tracked as a tolerated dismissal.

## Security advisory governance linkage

- Repository-wide vulnerability intake, triage, and disclosure sequencing is
  governed by `docs/security/security-advisories-workflow.md`.
- If an API-adjacent vulnerability is found in provider adapters or outbound
  request shaping logic, create/update a Draft GitHub Security Advisory and
  follow the private fix workflow before public disclosure.

## Automated security scanning

- `trivy.yml` runs Trivy filesystem scanning on every push, PR, and weekly
  schedule, reporting CRITICAL and HIGH severity findings as SARIF to GitHub
  Security.
- `codeql.yml` performs CodeQL static analysis for Python on every push, PR,
  and weekly schedule, surfacing security and quality findings in GitHub
  Security.

## Not currently applicable

- Authentication/authorization middleware
- Session cookies
- Public REST/GraphQL endpoint hardening
- Webhook signature validation

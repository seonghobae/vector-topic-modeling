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

## Not currently applicable

- Authentication/authorization middleware
- Session cookies
- Public REST/GraphQL endpoint hardening
- Webhook signature validation

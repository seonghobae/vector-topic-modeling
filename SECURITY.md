# Security Policy

## Reporting a vulnerability

Please do not open a public GitHub issue for suspected security vulnerabilities.

Instead, report them privately via GitHub Security Advisories:

- Report form: <https://github.com/seonghobae/vector-topic-modeling/security/advisories/new>
- Canonical workflow: `docs/security/security-advisories-workflow.md`

If GitHub Security Advisories is temporarily unavailable, contact the
maintainer directly via one of the following channels:

- Maintainer GitHub handle: <https://github.com/seonghobae>
- Maintainer security email: `me@seonghobae.me`

Include:

- affected version
- reproduction details
- impact assessment
- any suggested mitigation

Maintainer response targets:

- initial acknowledgement within 3 business days
- severity/impact triage within 5 business days
- coordinated fix/disclosure timeline shared after triage

Do not include exploit details in public issues, pull requests, or commit
messages before coordinated disclosure and fixed release availability.

## Scope

The main security-sensitive area in this repository is the outbound
OpenAI-compatible provider adapter and any text sent to it for embedding
generation.

Current guardrails include:

- explicit API key injection by the caller
- URL scheme validation (`http`/`https` only)
- redaction of some sensitive text patterns before outbound requests
- no runtime dependency on external application databases or auth stacks
- dependency-vulnerability dismissals are temporary, tracked in
  `docs/security/dependency-vulnerability-exceptions.md`, and must move from
  Active to Resolved when a patched version is adopted

## Supported versions

Only the latest version on `main` is currently supported.

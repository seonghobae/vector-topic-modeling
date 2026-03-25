# Security Policy

## Reporting a vulnerability

Please do not open a public GitHub issue for suspected security vulnerabilities.

Instead, report them privately via GitHub Security Advisories if enabled for this repository, or contact the maintainer directly with:

- affected version
- reproduction details
- impact assessment
- any suggested mitigation

## Scope

The main security-sensitive area in this repository is the outbound OpenAI-compatible provider adapter and any text sent to it for embedding generation.

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

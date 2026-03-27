# Architecture Overview

Last updated: 2026-03-27

## Project structure

```text
.
├── .github/                    # CI, release workflows, issue/PR templates,
│                              # and code ownership
├── src/vector_topic_modeling/
│   ├── clustering.py
│   ├── sessioning.py
│   ├── text.py
│   ├── service.py
│   ├── pipeline.py
│   ├── ingestion.py
│   ├── cli.py
│   └── providers/
├── examples/                  # Runnable local examples and sample JSONL
│                              # inputs
├── tests/
├── docs/
└── pyproject.toml
```

## Runtime model

1. Caller provides documents or JSONL rows.
2. `ingestion.py` maps raw rows (flat rows, DB column-value rows, or JSON payloads)
   into `TopicDocument` records and can compose `session_id` from primary-key bundles.
3. `TopicModeler` normalizes text and computes digest keys.
4. Embeddings are fetched through an injected provider.
5. Clustering is performed with a dependency-light greedy/adaptive
   kernel.
6. Optional session-aware digest selection prevents repeated boilerplate
   from dominating.

## Explicit exclusions

This standalone project intentionally excludes web framework routes,
database storage, background jobs, XLSX export, and email delivery.

## Current repository operations state

- GitHub is the canonical collaboration surface for issues, PRs,
  branch protection, CI, and releases.
- `main` is protected with pull-request-only merges, a minimum of one
  approving review, and required checks.
- `ci.yml` validates tests/builds, smoke-tests the installed wheel and
  CLI entrypoint, and `publish.yml` repeats that verification before the
  release-to-PyPI path when credentials are configured.
- `trivy.yml` runs Trivy filesystem scanning on every push and PR
  (plus a weekly schedule) and uploads SARIF results to GitHub Security.
- `codeql.yml` performs CodeQL static analysis for Python on every push
  and PR (plus a weekly schedule) and uploads findings to GitHub Security.
- `dependency-review.yml` reviews dependency changes in each PR and
  fails on moderate-severity (or above) known vulnerabilities.
- `dependency-submission.yml` submits dependency snapshots for `pip` and
  `uv.lock` inputs so Dependency Review can consume PR-head dependency
  metadata consistently.
- `.github/dependabot.yml` is the canonical dependency-update automation
  baseline for `pip` and `github-actions` ecosystems.
- `main` branch protection requires `workflow-lint`,
  `test-and-build (3.11)`, `test-and-build (3.12)`, and
  `dependency-review` so releases cannot bypass CI evidence.
- `pytest` is configured with `--cov=vector_topic_modeling --cov-branch`
  and `--cov-fail-under=100`, enforcing 100% line+branch coverage for
  product code in `src/vector_topic_modeling`.
- `scripts/docstring_coverage.py` reports and enforces 100% AST-level
  docstring coverage for module/class/function symbols in
  `src/vector_topic_modeling`.
- Vulnerability dismissals that lack an upstream patch must be recorded in
  `docs/security/dependency-vulnerability-exceptions.md`, re-evaluated on
  advisory/dependency/release changes, and moved from Active to Resolved when
  patched versions are adopted.
- GitHub Security Advisories is the canonical private vulnerability intake and
  disclosure workflow surface, documented in
  `docs/security/security-advisories-workflow.md`.
- Local verification remains the fastest pre-PR evidence path.

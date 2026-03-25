# Architecture Overview

Last updated: 2026-03-25

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
2. `TopicModeler` normalizes text and computes digest keys.
3. Embeddings are fetched through an injected provider.
4. Clustering is performed with a dependency-light greedy/adaptive
   kernel.
5. Optional session-aware digest selection prevents repeated boilerplate
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
- `.github/dependabot.yml` is the canonical dependency-update automation
  baseline for `pip` and `github-actions` ecosystems.
- `main` branch protection requires `workflow-lint`,
  `test-and-build (3.11)`, and `test-and-build (3.12)` so releases
  cannot bypass CI evidence.
- Vulnerability dismissals that lack an upstream patch must be recorded in
  `docs/security/dependency-vulnerability-exceptions.md`, re-evaluated on
  advisory/dependency/release changes, and moved from Active to Resolved when
  patched versions are adopted.
- Local verification remains the fastest pre-PR evidence path.

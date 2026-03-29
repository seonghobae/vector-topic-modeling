# Architecture Overview

Last updated: 2026-03-28

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
│   ├── evaluation.py
│   ├── distributed.py
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
7. Optional extended metrics (Silhouette, Calinski-Harabasz, Davies-Bouldin)
   can be calculated via `evaluation.py`, and can be parallelized using Valkey
   (`distributed.py`) to reduce heavy pairwise distance computation time.

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
  release-to-PyPI path via PyPI Trusted Publishing (OIDC) in the `pypi`
  environment.
- `ci-stability.yml` extends CI/CD stability coverage to Python 3.13 and 3.14
  on `main` pushes, PRs into `main`, and a weekly schedule.
- `pr-branch-guard.yml` enforces the dev→main merge discipline by requiring
  head branch `dev` for PRs into `main`, with emergency exceptions limited to
  `hotfix/*`, `release/*`, or label `override:branch-guard`.
- `trivy.yml` runs Trivy filesystem scanning on every push and PR
  (plus a weekly schedule) and uploads SARIF results to GitHub Security.
- `codeql.yml` performs CodeQL static analysis for Python on every push
  and PR (plus a weekly schedule) and uploads findings to GitHub Security.
- `cflite_pr.yml` runs ClusterFuzzLite `code-change` fuzzing for PRs to
  `main`, filtered to code-relevant paths (`src/**`, `tests/**`,
  `.clusterfuzzlite/**`, and the workflow file) to avoid docs-only PR churn.
- `cflite_batch.yml` runs scheduled/manual ClusterFuzzLite `batch` fuzzing
  for deeper continuous coverage outside the PR critical path.
- `dependency-review.yml` reviews dependency changes in PRs targeting `main` and
  fails on moderate-severity (or above) known vulnerabilities.
- `dependency-submission.yml` submits dependency snapshots for `pip` and
  `uv.lock` inputs so Dependency Review can consume PR-head dependency
  metadata consistently.
- `dependency-review-runtime-monitor.yml` runs weekly (and on manual dispatch)
  to inspect `actions/dependency-review-action` upstream runtime metadata and
  track the Node24 migration readiness path documented in Issue #45; summary
  guidance classifies `fetch-error` as retry/availability and keeps
  `parse-error`/`unexpected-error` on repair-focused paths.
- `.github/dependabot.yml` is the canonical dependency-update automation
  baseline for `pip` and `github-actions` ecosystems.
- `main` branch protection requires `workflow-lint`,
  `test-and-build (3.11)`, `test-and-build (3.12)`, `dependency-review`,
  `stability (py3.13)`, and `Enforce head branch policy` so releases cannot
  bypass CI evidence; branch protection also requires conversation resolution
  before merge.
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

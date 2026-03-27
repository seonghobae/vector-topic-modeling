# PR Continuity

- Keep the standalone package scoped to reusable topic-modeling concerns.
- Avoid bundling webapp, DB, or scheduler changes into this repository.
- Prefer small PRs that separately cover core logic, provider work, and docs refinements.
- Treat the branch-linked open PR as canonical for the current task; avoid
  duplicate PRs for the same head branch.
- Keep PR checks green (`workflow-lint`, `test-and-build (3.11)`,
  `test-and-build (3.12)`, `dependency-review`) before requesting merge.
- Keep local pre-PR verification green with:
  - `uv run pytest -q` (100% line+branch coverage gate),
  - `uv run python scripts/docstring_coverage.py --min-percent 100`,
  - build/smoke verification commands documented in
    `docs/engineering/harness-engineering.md`.
- Keep CodeRabbit review commands in PR comments only (`@coderabbitai
  review`, `@coderabbitai pause`, `@coderabbitai resume`) and synchronize
  follow-up commits to the same canonical PR whenever possible.

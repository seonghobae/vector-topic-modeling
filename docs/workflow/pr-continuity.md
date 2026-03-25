# PR Continuity

- Keep the standalone package scoped to reusable topic-modeling concerns.
- Avoid bundling webapp, DB, or scheduler changes into this repository.
- Prefer small PRs that separately cover core logic, provider work, and docs refinements.
- Treat the branch-linked open PR as canonical for the current task; avoid
  duplicate PRs for the same head branch.
- Keep PR checks green (`workflow-lint`, `test-and-build (3.11)`,
  `test-and-build (3.12)`) before requesting merge.
- Keep CodeRabbit review commands in PR comments only (`@coderabbitai
  review`, `@coderabbitai pause`, `@coderabbitai resume`) and synchronize
  follow-up commits to the same canonical PR whenever possible.

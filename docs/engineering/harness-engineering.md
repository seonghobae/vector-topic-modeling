# Harness Engineering

- Use `uv run pytest -q` for verification.
  - `pyproject.toml` enforces `--cov=vector_topic_modeling --cov-branch`
    and `--cov-fail-under=100`.
- Use `uv run python scripts/docstring_coverage.py --min-percent 100`
  to verify product docstring coverage is 100%.
- Before build/smoke checks, remove previous artifacts:
  - POSIX shell: `rm -rf dist .venv-smoke-cli`
  - PowerShell: `Remove-Item -Recurse -Force dist, .venv-smoke-cli`
- Use `uv run python -m build` to verify distributable artifacts.
- Use `uv run python scripts/smoke_installed_cli.py` with
  `--dist-dir dist` and `--venv-dir .venv-smoke-cli` to verify
  installed-wheel import and console-script paths.
- Keep tests deterministic and network-free unless explicitly testing the
  provider adapter.
- Coverage policy: 100% line + 100% branch for `src/vector_topic_modeling`.
- Docstring policy: 100% AST-level module/class/function docstring coverage
  for `src/vector_topic_modeling`.
- `.github/workflows/ci.yml` is the canonical pre-merge verification path
  for pull requests.
- `.github/workflows/ci-stability.yml` is the compatibility verification path
  for Python 3.13 and 3.14 (PR-to-main, push-to-main, weekly schedule).
- `.github/workflows/pr-branch-guard.yml` enforces head-branch policy for PRs
  into `main` (`dev` default; emergency exceptions via `hotfix/*`,
  `release/*`, or label `override:branch-guard`).
- `.github/workflows/release.yml` is the canonical tag/manual release
  verification path for GitHub Release artifact creation.
- `.github/workflows/publish.yml` is the canonical release-to-PyPI path
  triggered by `release.published`.
- Use `uv run python scripts/review_checks/dependency_review_warning_gate.py`
  for pull-request dependency-warning triage and issue closure verification.
  - Required args: `--owner`, `--repo`, `--pr`
  - Policy args: `--max-unknown-licenses` and optional
    `--allow-snapshot-warning`
- Use `uv run python scripts/review_checks/pr_check_gate_classifier.py`
  to classify PR check contexts into required blockers vs optional external
  status noise (for example stale CodeRabbit contexts).
  - Input: JSON array from `gh pr checks <pr> --json name,state,completedAt`
  - Output: `gate=PASS|FAIL` summary with required/optional buckets
- Use `uv run python scripts/review_checks/dependency_review_action_runtime_check.py`
  to monitor upstream `actions/dependency-review-action` runtime metadata and
  detect when mutable upstream ref `actions/dependency-review-action@v4`
  transitions to a Node24-native runtime.
  - Exit code `0`: still monitoring (runtime mismatch; current expected state)
  - Exit code `1`: upstream runtime now matches expected Node24 (migration work
    should proceed per Issue #45)
  - Exit code `2`: monitor execution error; classify by payload `status`:
    - `fetch-error`: retry first (manual `workflow_dispatch` or next schedule)
      and verify upstream/raw-host availability before code changes.
    - `parse-error` or `unexpected-error`: repair-focused path (monitor
      parser/logic/workflow needs correction).
- `.github/workflows/dependency-review-runtime-monitor.yml` is the canonical
  scheduled/dispatch path for automated Issue #45 runtime-monitor evidence.
- Branch protection on `main` requires pull-request-only merges, one
  approving review, conversation resolution, and all required checks passing
  before merge.

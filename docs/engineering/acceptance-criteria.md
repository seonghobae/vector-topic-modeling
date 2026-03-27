# Acceptance Criteria

- The project builds as a standalone Python package.
- Pure clustering, sessioning, text shaping, and service helpers are covered by pytest.
- The package does not import from external systems at runtime.
- The CLI exposes a topic-clustering entrypoint for JSONL inputs.
- Session-aware mode preserves session-less documents and keeps
  assignments consistent with session topic aggregates.
- The repository includes a LICENSE file and the built sdist contains it.
- Local verification consists of:
  - `uv run pytest -q`
    - enforces `--cov=vector_topic_modeling --cov-branch --cov-fail-under=100`
      through `pyproject.toml`
  - `uv run python scripts/docstring_coverage.py --min-percent 100`
  - `uv run python -m build`
  - `uv run python scripts/smoke_installed_cli.py`
    with `--dist-dir dist` and `--venv-dir .venv-smoke-cli`
- Coverage gates require 100% line coverage and 100% branch coverage for
  `src/vector_topic_modeling`.
- Docstring gates require 100% AST-level coverage across module/class/function
  symbols in `src/vector_topic_modeling`.
- Dependency governance includes `.github/dependabot.yml` coverage for
  `pip` and `github-actions`, and documented handling for unpatchable
  dismissed advisories under `docs/security/`.
- Security governance documents private vulnerability intake/disclosure flow via
  GitHub Security Advisories in `SECURITY.md` and
  `docs/security/security-advisories-workflow.md`.
- Repository polish changes keep contributor/release/community docs aligned
  with actual GitHub workflow and protected-branch policy.
- Dependency review policy gates pull requests on moderate-severity (or above)
  vulnerabilities.

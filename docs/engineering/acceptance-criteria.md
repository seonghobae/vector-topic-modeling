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
  - `uv run python -m build`
  - `uv run python scripts/smoke_installed_cli.py`
    with `--dist-dir dist` and `--venv-dir .venv-smoke-cli`
- Dependency governance includes `.github/dependabot.yml` coverage for
  `pip` and `github-actions`, and documented handling for unpatchable
  dismissed advisories under `docs/security/`.
- Repository polish changes keep contributor/release/community docs aligned
  with actual GitHub workflow and protected-branch policy.

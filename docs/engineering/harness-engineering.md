# Harness Engineering

- Use `uv run pytest -q` for verification.
- Before build/smoke checks, remove previous artifacts:
  - POSIX shell: `rm -rf dist .venv-smoke-cli`
  - PowerShell: `Remove-Item -Recurse -Force dist, .venv-smoke-cli`
- Use `uv run python -m build` to verify distributable artifacts.
- Use `uv run python scripts/smoke_installed_cli.py` with
  `--dist-dir dist` and `--venv-dir .venv-smoke-cli` to verify
  installed-wheel import and console-script paths.
- Keep tests deterministic and network-free unless explicitly testing the
  provider adapter.
- `.github/workflows/ci.yml` and `.github/workflows/publish.yml` are the
  canonical hosted verification paths and must remain aligned with these
  local commands.

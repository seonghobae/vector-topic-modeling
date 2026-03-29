# Pull Request

## Summary

-

## Verification

- [ ] `uv run pytest -q`
- [ ] `uv run python scripts/docstring_coverage.py --min-percent 100`
- [ ] `rm -rf dist .venv-smoke-cli`
- [ ] `uv run python -m build`
- [ ] `uv run python scripts/smoke_installed_cli.py --dist-dir dist --venv-dir .venv-smoke-cli`

## Checklist

- [ ] docs updated if behavior, packaging, or workflows changed
- [ ] runtime boundaries preserved
- [ ] no external system runtime coupling reintroduced

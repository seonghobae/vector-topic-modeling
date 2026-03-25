# Releasing `vector-topic-modeling`

## Preconditions

- `main` is green in CI.
- README, changelog, and version metadata are up to date.
- The release commit is already merged into `main`.

## Local verification

```bash
uv sync --extra dev
uv run pytest -q
# Delete any previous build artifacts and smoke-test virtual environment.
# On POSIX shells: rm -rf dist .venv-smoke-cli
# On Windows PowerShell: Remove-Item -Recurse -Force dist, .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist \
  --venv-dir .venv-smoke-cli
```

`main` must keep the required GitHub checks green before tagging a release:

- `workflow-lint`
- `test-and-build (3.11)`
- `test-and-build (3.12)`

## Versioning

- Follow Semantic Versioning.
- Update `pyproject.toml` version.
- Move relevant `CHANGELOG.md` items from `Unreleased` into the new version section.

## Create a release

1. Create and push a tag:

   ```bash
   git checkout main
   git pull --ff-only
   git tag 0.1.1
   git push origin 0.1.1
   ```

2. Create a GitHub Release from that tag.
3. The publish workflow will build the package, rerun the installed-CLI
   smoke check, and publish it when `PYPI_API_TOKEN` is configured in
   the repository secrets.
4. Confirm the GitHub branch protection for `main` still requires the
   CI checks above before merging any last-minute fixes.

## Fallback manual publish

If automation is unavailable, publish from a trusted local environment:

```bash
uv sync --extra dev
# Delete any previous build artifacts and smoke-test virtual environment.
# On POSIX shells: rm -rf dist .venv-smoke-cli
# On Windows PowerShell: Remove-Item -Recurse -Force dist, .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist \
  --venv-dir .venv-smoke-cli
uv run python -m pip install twine
uv run twine upload dist/*
```

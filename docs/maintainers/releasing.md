# Releasing `vector-topic-modeling`

## Preconditions

- `main` is green in CI.
- README, changelog, and version metadata are up to date.
- The release commit is already merged into `main`.
- Dependency exception governance is clean:
  - each active entry in
    `docs/security/dependency-vulnerability-exceptions.md` is still
    unpatchable upstream,
  - any advisory resolved via dependency upgrade has been moved to
    `Resolved exception entries` in the same change set as the upgrade.
- Security advisory governance is clean:
  - if the release includes a security fix, a Draft advisory exists with
    affected/fixed version intent,
  - disclosure sequencing follows
    `docs/security/security-advisories-workflow.md`.

## Local verification

```bash
uv sync --extra dev
uv run pytest -q
uv run python scripts/docstring_coverage.py --min-percent 100
# Delete any previous build artifacts and smoke-test virtual environment.
# On POSIX shells: rm -rf dist .venv-smoke-cli
# On Windows PowerShell: Remove-Item -Recurse -Force dist, .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist \
  --venv-dir .venv-smoke-cli
```

`main` must keep the required GitHub checks green before tagging a release.

Required CI status checks:

- `workflow-lint`
- `test-and-build (3.11)`
- `test-and-build (3.12)`
- `dependency-review`

Branch protection / merge policy:

- pull-request-only merges (no direct push to `main`)
- at least one approving PR review before merge

## Versioning

- Follow Semantic Versioning.
- Update `pyproject.toml` version.
- Move relevant `CHANGELOG.md` items from `Unreleased` into the new version section.

## Dependency-exception release gate

Before tagging:

- Review `docs/security/dependency-vulnerability-exceptions.md`.
- Confirm no advisory remains in `Active exception entries` if `uv.lock`
  already contains a patched version for that advisory path.
- If such an advisory exists, stop release prep and update the dependency and
  exception register first.

## Security advisory release gate

Before tagging:

- Review GitHub `Security > Advisories` state.
- If this release includes a security fix:
  - verify Draft advisory metadata includes affected/fixed versions,
  - prepare release references (tag, PR/commit) for advisory publication.
- After release publication, publish the advisory and verify the fixed version
  metadata matches the released artifact version.
- Update release notes / `CHANGELOG.md` with a security-fix entry that
  references advisory ID (GHSA/CVE when available) and fixed version.

## Create a release

**Prerequisite for PyPI Trusted Publishing:**
Before your first automated release, configure a Trusted Publisher in PyPI:
1. Log in to PyPI and go to your project's **Publishing** settings.
2. Add a new publisher using GitHub.
3. Set the owner (`seonghobae`), repository (`vector-topic-modeling`), and workflow name (`publish.yml`).
4. Set the environment name to `pypi` to match the environment used in the workflow.

1. Create and push a `v`-prefixed tag:

   ```bash
   git checkout main
   git pull --ff-only
    git tag v0.1.1
    git push origin v0.1.1
    ```

2. The `release.yml` workflow verifies tests/build/smoke and creates a
   GitHub Release with artifacts from that tag.
3. The `publish.yml` workflow then runs on `release.published` and
   publishes to PyPI using PyPI Trusted Publishing (OIDC).
4. Confirm the GitHub branch protection for `main` still requires the
   CI checks above and at least one approving PR review before merging
   any last-minute fixes.

You can also run `release.yml` manually with `workflow_dispatch` by
passing an existing tag (for example, `v0.1.1`).

## Fallback manual publish

If automation is unavailable, publish from a trusted local environment:

```bash
uv sync --extra dev
uv run pytest -q
uv run python scripts/docstring_coverage.py --min-percent 100
# Delete any previous build artifacts and smoke-test virtual environment.
# On POSIX shells: rm -rf dist .venv-smoke-cli
# On Windows PowerShell: Remove-Item -Recurse -Force dist, .venv-smoke-cli
uv run python -m build
uv run python scripts/smoke_installed_cli.py --dist-dir dist \
  --venv-dir .venv-smoke-cli
uv run python -m pip install twine
uv run twine upload dist/*
```

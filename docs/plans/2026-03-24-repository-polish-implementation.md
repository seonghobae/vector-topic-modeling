# Repository Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `vector-topic-modeling` feel like a complete open-source Python package repository with contributor guidance, release metadata, collaboration templates, and runnable examples.

**Architecture:** This plan leaves package runtime behavior intact and focuses on repository surface area: docs, metadata, GitHub templates, release workflow, and examples. The implementation should improve package discoverability and contributor confidence without introducing unnecessary operational complexity.

**Tech Stack:** Markdown, YAML, Python packaging metadata, GitHub Actions.

---

### Task 1: Refresh package-facing metadata and changelog

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`
- Create: `CHANGELOG.md`

**Step 1: Write the failing test**

Use a doc/metadata checklist instead of code tests:
- README must not claim there is no GitHub remote.
- `pyproject.toml` must contain canonical URLs for homepage/issues/changelog.
- `CHANGELOG.md` must exist in Keep a Changelog format.

**Step 2: Run verification to confirm failure**

Run: `grep -n "no GitHub remote configured yet\|project.urls\|CHANGELOG" README.md pyproject.toml CHANGELOG.md`
Expected: missing or stale metadata.

**Step 3: Write minimal implementation**

Update the README, package URLs, and add a changelog.

**Step 4: Run verification to confirm pass**

Run: `grep -n "Homepage\|Issues\|Changelog\|## \[Unreleased\]" README.md pyproject.toml CHANGELOG.md`
Expected: all canonical metadata present.

### Task 2: Add contributor and maintainer guidance

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `SUPPORT.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `docs/maintainers/releasing.md`

**Step 1: Write the failing test**

Checklist:
- contributor setup and verification commands documented
- security disclosure route documented
- maintainer release workflow documented

**Step 2: Run verification to confirm failure**

Run: `ls CONTRIBUTING.md SECURITY.md SUPPORT.md CODE_OF_CONDUCT.md docs/maintainers/releasing.md`
Expected: files missing.

**Step 3: Write minimal implementation**

Add concise contributor, support, security, conduct, and maintainer docs.

**Step 4: Run verification to confirm pass**

Run: `ls CONTRIBUTING.md SECURITY.md SUPPORT.md CODE_OF_CONDUCT.md docs/maintainers/releasing.md`
Expected: all files exist.

### Task 3: Add GitHub collaboration scaffolding

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/CODEOWNERS`

**Step 1: Write the failing test**

Checklist:
- bug and feature issue intake exist
- PR checklist exists
- repository owner routing exists

**Step 2: Run verification to confirm failure**

Run: `ls .github/ISSUE_TEMPLATE .github/PULL_REQUEST_TEMPLATE.md .github/CODEOWNERS`
Expected: files/directories missing.

**Step 3: Write minimal implementation**

Create lightweight GitHub templates for the current repository state.

**Step 4: Run verification to confirm pass**

Run: `ls .github/ISSUE_TEMPLATE .github/PULL_REQUEST_TEMPLATE.md .github/CODEOWNERS`
Expected: all scaffolding exists.

### Task 4: Add release automation and onboarding examples

**Files:**
- Create: `.github/workflows/publish.yml`
- Create: `.github/release.yml`
- Create: `examples/basic_in_memory_provider.py`
- Create: `examples/sample_queries.jsonl`
- Create: `examples/cli_openai_compat.sh`
- Modify: `README.md`

**Step 1: Write the failing test**

Checklist:
- release workflow exists
- release note categories exist
- examples directory contains runnable/reference assets
- README links to examples and release path

**Step 2: Run verification to confirm failure**

Run: `ls .github/workflows/publish.yml .github/release.yml examples`
Expected: missing files.

**Step 3: Write minimal implementation**

Add release workflow, release config, and examples, then link them from the README.

**Step 4: Run verification to confirm pass**

Run: `ls .github/workflows/publish.yml .github/release.yml examples && uv run pytest -q && uv run python -m build`
Expected: scaffolding exists and package verification still passes.

# Topic Modeling Extraction Implementation Plan

<!-- markdownlint-disable MD001 MD013 MD029 MD032 MD036 -->

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract the reusable topic-modeling logic from the source
application into a standalone Python library and CLI without modifying or
removing the source implementation.

**Architecture:** Port the pure clustering, session-selection, and text-shaping helpers into a new `src/` package, then add a small provider-driven orchestration layer that accepts prebuilt documents and embedding providers. Keep the package dependency-light and avoid DB, FastAPI, scheduler, XLSX, and email couplings.

**Tech Stack:** Python 3.11+, hatchling packaging, pytest.

---

### Task 1: Port the pure topic-modeling kernel

**Files:**
- Create: `src/vector_topic_modeling/clustering.py`
- Create: `src/vector_topic_modeling/sessioning.py`
- Create: `src/vector_topic_modeling/text.py`
- Test: `tests/test_clustering.py`
- Test: `tests/test_sessioning.py`
- Test: `tests/test_text.py`

**Step 1: Write the failing tests**

Create the clustering, sessioning, and text tests based on the proven baseline behavior.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_clustering.py tests/test_sessioning.py tests/test_text.py -q`
Expected: FAIL with import errors or missing symbols.

**Step 3: Write minimal implementation**

Port the pure helper logic with repo-independent imports.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_clustering.py tests/test_sessioning.py tests/test_text.py -q`
Expected: PASS.

### Task 2: Add standalone orchestration and CLI

**Files:**
- Create: `src/vector_topic_modeling/pipeline.py`
- Create: `src/vector_topic_modeling/providers/base.py`
- Create: `src/vector_topic_modeling/providers/openai_compat.py`
- Create: `src/vector_topic_modeling/cli.py`
- Create: `src/vector_topic_modeling/__init__.py`
- Test: `tests/test_pipeline.py`
- Test: `tests/test_cli.py`

**Step 1: Write the failing tests**

Add tests for document clustering, session-aware topic modeling, and CLI parsing.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_pipeline.py tests/test_cli.py -q`
Expected: FAIL with missing module/class errors.

**Step 3: Write minimal implementation**

Create a provider-driven `TopicModeler`, typed result objects, and a JSONL-oriented CLI.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_pipeline.py tests/test_cli.py -q`
Expected: PASS.

### Task 3: Package and document the standalone project

**Files:**
- Create: `README.md`
- Create: `ARCHITECTURE.md`
- Create: `AGENTS.md`
- Create: `docs/engineering/acceptance-criteria.md`
- Create: `docs/workflow/one-day-delivery-plan.md`
- Create: `docs/engineering/harness-engineering.md`
- Create: `docs/agents/README.md`
- Create: `docs/coderabbit/review-commands.md`
- Create: `docs/workflow/pr-continuity.md`
- Create: `tests/test_service.py`
- Create: `src/vector_topic_modeling/service.py`

**Step 1: Write the failing test**

Add service-helper tests for filter signatures, previous-period ranges, and trend formatting.

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_service.py -q`
Expected: FAIL with missing import errors.

**Step 3: Write minimal implementation**

Add the helper module and repository documentation required for standalone reuse.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_service.py -q`
Expected: PASS.

### Task 4: Verify package build and repo readiness

**Files:**
- Modify: `pyproject.toml`
- Verify: `src/vector_topic_modeling/**`
- Verify: `tests/**`

**Step 1: Run the full test suite**

Run: `python3 -m pytest -q`
Expected: PASS.

**Step 2: Build the package**

Run: `python3 -m build`
Expected: wheel and source distribution created under `dist/`.

**Step 3: Commit**

```bash
git add .
git commit -m "feat: extract standalone query topic modeling package"
```

# One-Day Delivery Plan

1. Port the pure topic-modeling helpers.
2. Add standalone orchestration and CLI.
3. Fix release blockers discovered by review
   (session-aware consistency, licensing, CI, docs).
4. Validate with pytest (100% line+branch coverage),
   docstring coverage (100% via
   `uv run python scripts/docstring_coverage.py --min-percent 100`),
   package build, and wheel/sdist smoke checks.
5. Keep runtime boundaries documented without expanding external coupling.

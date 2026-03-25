# Agent Usage

- Prefer pure-function decoupling over runtime coupling.
- Use subagents for architecture review when changing boundaries.
- Keep ingestion adaptation logic in `src/vector_topic_modeling/ingestion.py` so
  topic-model orchestration stays isolated in `pipeline.py`.
- Keep runtime adapters isolated under `src/vector_topic_modeling/providers/`.
- Route vulnerability handling through canonical docs:
  - `SECURITY.md`
  - `docs/security/security-advisories-workflow.md`
- Never direct security reporters to public issues for vulnerability details.

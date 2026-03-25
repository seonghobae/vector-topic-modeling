#!/usr/bin/env bash
set -euo pipefail

vector-topic-modeling cluster examples/sample_queries.jsonl \
	--output topics.json \
	--base-url "${LITELLM_API_BASE:?set LITELLM_API_BASE}" \
	--api-key "${LITELLM_API_KEY:?set LITELLM_API_KEY}" \
	--model text-embedding-3-large

# Session — railway_logs.py: retry/backoff on transient 5xx

> **Status:** `in-progress`

## What I'm about to do

A live log-triage run (`railway_logs.py -n 20`) failed with `Railway API HTTP 503: upstream connect
error … reset reason: connection timeout` on the `deployments` query — a transient Railway-side
gateway 5xx. A plain retry seconds later succeeded, confirming it was a blip. But the script has a
30s timeout and **no retry**, so a single transient 5xx fails the whole `superbot-log-triage` Hermes
skill.

Harden the shared GraphQL `post()` in `scripts/hermes/railway_logs.py` with bounded
retry-with-backoff on retryable statuses (429/500/502/503/504) and connection-level errors
(URLError/timeout), honoring `Retry-After` on 429. Non-retryable 4xx and GraphQL-error bodies still
raise immediately (no masking of auth/bad-request failures). Injectable `sleep` + `max_retries` keep
the unit tests hermetic and fast.

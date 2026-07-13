# 2026-07-13 — mineverse FLAG 2: HMAC mining write endpoint

> **Status:** `in-progress`

About to build the mineverse FLAG 2 WRITE endpoint: an HMAC-signed
`POST /relay/mining/action` on the existing healthserver aiohttp app
(dormant unless `MINING_WRITE_SHARED_SECRET` is set), validating against
`schemas/mining_action.v1.schema.json`, executing exclusively through
`disbot/services/mining_workflow.py`, with action_id idempotency (≥24h),
per-(suid,guild) rate limits, a hard test-guild allowlist, and an
`emit_audit_action` row for every web-originated action.

📊 Model: fable-5

# 2026-07-09 — telemetry-gate-guard

> **Status:** `in-progress` — extending the session merge-gate with a telemetry-append requirement.

**Intent:** Owner-directed (fleet-review coordinator, 2026-07-09, finding #3 of the superbot kit-handling assessment): the telemetry-append rule (`telemetry/README.md`) is exhortative and already leaking — 3 rows in `telemetry/model-usage.jsonl` vs ≥4 sessions carded since the lane shipped (#1884). Per Q-0194 (friction → guard, "enforce, don't exhort" Q-0132), extend `scripts/check_session_gate.py` so a PR that **adds** a `.sessions/` card dated ≥ 2026-07-09 must also append ≥1 row to `telemetry/model-usage.jsonl` in the same PR. Engage-only-on-card-adding shape, so routine/workflow PRs never deadlock; date floor avoids retroactive redness on older cards.

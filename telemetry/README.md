# telemetry/ — superbot's model-allocation feed (hand-authored)

> **Status:** `living-ledger`

`model-usage.jsonl` carries superbot's per-session **PL-004 / Q-0248 record**
(`{session, date, model, effort, task_class, tokens_out, outcome}`, one JSON
object per line, append-only). The **canonical schema + field rules live in
the kit repo** — `substrate-kit/telemetry/README.md` and the founding plan
§5.2; superbot is *not* an adopted kit install, so rows here are
**hand-authored by the session** (kit-lab plan §4.2) until superbot truly
adopts and the kit's `session-close` harvest takes over. Append your session's
row at close; `task_class` uses the 8 Q-0248 classes verbatim; `tokens_out`
is null until a real meter exists (KF-9 — estimates must be labeled).
**Enforced since 2026-07-09 (Q-0194 guard in `scripts/check_session_gate.py`):**
a PR that *adds* a `.sessions/` card dated ≥ 2026-07-09 is held red in Code
Quality until the same PR appends ≥1 row here.
`scripts/export_dashboard_data.py` renders the feed onto the program console's
"Model & spend telemetry" lane (field-whitelisted; capped to the newest 200).
The `outcome` object's PR fields are backfilled by the kit-lab's telemetry
sweep once 👤 P13 read scopes exist.

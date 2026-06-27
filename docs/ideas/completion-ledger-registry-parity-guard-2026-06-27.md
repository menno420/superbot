# Completion-ledger ↔ registry parity guard

> **Status:** `ideas`. Not approved for implementation. Source + binding contracts win.
> **Subsystem:** none (S4/S3 tooling).

**Session idea (2026-06-27, Q-0089, from building the feature-completion framework PR #1513):** the
new [completion ledger](../planning/feature-completion/README.md) lists every S1 game / server-function
unit by hand, seeded from `subsystem_registry.py`. Nothing keeps the two in sync — a **new game or
server function added to the registry would silently miss a completion unit** (and never get
assessed/certified), exactly the drift class the `subsystem-inventory-homed-guard` idea flags for the
navigation/ownership tables.

**The guard (lightest that works):** a stdlib `scripts/check_completion_ledger_parity.py` that reads
the user-facing `SUBSYSTEMS` keys (games + server functions, minus the documented out-of-scope set —
knowledge domains, routing-only hubs, dev-internal) and asserts each appears as a row in the
completion ledger, and vice-versa (no ledger row for a key the registry dropped). Warn-first,
`--strict` for the reconciliation cadence; **disposable (Q-0105)** — delete if it proves noisy. The
*completeness-axis* sibling of `check_subsystem_inventory_homed` (which homes cogs in the
nav/ownership tables) and `readiness_scoreboard` (the risk axis).

**Why it matters:** the whole point of the completion ledger is "finish everything that exists" — a
unit the ledger never knew about is a hole in that guarantee. Cheap to build once the
`completion_scoreboard.py` parser exists (reuse its table reader).

→ relates `scripts/completion_scoreboard.py` · `docs/planning/feature-completion/README.md` ·
`disbot/utils/subsystem_registry.py` · the `subsystem-inventory-homed-guard` idea.

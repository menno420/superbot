# 2026-06-23 — Consolidation audit: record three code-verified findings into the brief

> **Status:** `in-progress` — routine dispatch run, second slice. De-risks the owner-directed
> consolidation/discoverability audit (#1366) by resolving three of its "verify before trusting" /
> open-question TODOs against source, so the audit session starts ahead.

> **Run type:** `routine · dispatch`

## What I'm about to do

While scoping a slice of the just-staged consolidation audit
(`docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md`), I verified three of its open
questions against source. None is a buildable code fix (the audit's real targets need live Discord
repro / owner decisions), but the findings are durable and remove research the audit session would
otherwise repeat. Recording them in the brief is first-class orientation work.

1. **§3.1 / §6 / §8 — the help-reachability guard is located, and it is subsystem-level only.** The
   brief said "a grep did not locate a standalone `check_help_reachability.py`; verify before
   trusting." It lives as **`tests/unit/invariants/test_help_reachability.py`** (→
   `tools/sim/help_menu_grouping_sim.py::check_reachability`) + **`test_discoverability.py`**. Both
   check **subsystem**-level homing (no orphan, ≤3 clicks, no dropdown overflow / a discovery path per
   subsystem). **Per-command reachability (rubric item 2) is NOT machine-checked** — resolving the §8
   "#1297 scope" open question: subsystem-homing only.
2. **§3.2 — the General cog menu IS already buttonized + homed (static).** `GeneralMenuView` has a
   per-command button for each of the 8 commands (`fact_btn`/`joke_btn`/…); `general` is a Utility
   `primary_child` with a `build_help_menu_view` hook. So the owner's "unfindable" complaint is **not**
   a static buttonization gap — it genuinely needs the live repro the brief calls for (path/listing,
   not buttons).
3. **§3.4 — both settings-orphan signals are already empty.** `build_catalogue(None).findings` reports
   `settings_without_panel == ()` and `panels_without_settings == ()` — that sub-goal is already at
   zero in the static build (the audit need only re-confirm the bot-dependent help-hook signal live).

## What shipped

_(filled at close)_

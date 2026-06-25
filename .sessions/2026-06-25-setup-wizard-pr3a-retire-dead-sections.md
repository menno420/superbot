# Session — 2026-06-25 · setup-wizard PR 3a — retire dead/legacy sections

> **Status:** `in-progress` — born-red card (Q-0133). Run type: routine · dispatch.

## What this run is

Empty-fire dispatch → advance the S1 ▶ next slice: **setup-wizard PR 3** (the prior session's
named handoff). PR 3 has two halves; I'm shipping the contained, offline-verifiable half as **PR 3a**
and handing off the rest as PR 3b.

**PR 3a (this PR) — retire the dead/legacy sections from the (now-Advanced) wizard.** Per the plan
§3/§7 disposition (owner-greenlit): the old section-list wizard (now `!setupadvanced`) still shows
read-only / metadata / announcement / link-only steps whose function moved into the Essential Setup
spine (step 0 + "Check my setup", PR 1/2). Retire them so the Advanced wizard only contains steps
that do real config:
- **Delete** (fully orphaned, no non-test importer): `purpose`, `identity`, `btd6`, `ai_setup`,
  `readiness`, `diagnostics` (section view; the `setup_diagnostics` *service* stays), `suggestions`.
- **Unregister only** (keep module — `channels` imports `server_scan.get_cached_snapshot`):
  `server_scan`.
- **Demote** `cleanup` to advanced-only depth (`cog_routing` already advanced-only).

**Deferred to PR 3b** (needs live bot verification): the Q-E Advanced draft→Final-Review editor
rework ("currently most of it does not do anything") + deleting any now-dead service code.

## Verification
`check_quality.py --full` (pytest is the import-breakage net) + `check_architecture --mode strict`
+ `check_docs --strict` + the setup-wizard sim.

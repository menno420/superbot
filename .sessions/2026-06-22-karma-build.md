# Session — 2026-06-22 · Karma (thanks/upvote reputation) — build

> **Status:** `in-progress` — born-red HOLD card; flip to `complete` as the final step.

**Run type:** owner-directed. **Branch:** `claude/peaceful-franklin-klgw3f`.
**Trigger:** the owner explicitly authorized building the Karma plan ("you can execute this plan",
2026-06-22) and went offline. Executing with the plan's **recommended defaults** (both surfaces with
reaction off by default · positive-only · pure reputation · karma-roles deferred · 1h cooldown /
10-per-day cap), since the 5 design questions were not individually answered.

## What I'm about to do

Implement the Karma subsystem per
[`docs/planning/karma-reputation-plan-2026-06-22.md`](../docs/planning/karma-reputation-plan-2026-06-22.md),
delivering the plan's **PR 1 (foundation + audited seam) + PR 2 (cog + leaderboard)** as one cohesive
PR — Karma is a net-new isolated subsystem (nothing else imports it), so the risk is contained and a
single PR avoids inter-PR merge coordination while the owner is offline. **PR 3 (reaction-grant +
karma-roles) is deferred** per the recommended defaults.

Files: migration `092_karma.sql` (karma + karma_audit_log) · `utils/db/karma.py` (+ `__init__`
re-export) · `services/karma_service.py` + `services/karma_config.py` · `core/events_catalogue.py`
(`karma.granted`) · `utils/settings_keys/karma.py` (+ re-export) · `cogs/karma/schemas.py` +
`cogs/karma_cog.py` · `KarmaProvider` in `rank_providers.py` · `config.py` extension · subsystem
registry entry · INV-K invariant test + service tests · `docs/ownership.md` rows + `docs/subsystems/karma.md`.

## What changed

_(filled at close)_

## 💡 Session idea (Q-0089)

_(filled at close)_

## ⟲ Previous-session review (Q-0102)

_(filled at close)_

## 📋 Doc audit (Q-0104)

_(filled at close)_

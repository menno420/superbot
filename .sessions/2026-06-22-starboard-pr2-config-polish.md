# 2026-06-22 — Starboard PR 2: self-star exclusion + ignore-channels + config panel

> **Status:** `in-progress` — born-red HOLD. Dispatch routine (no work order); advancing the
> band-#1260 next-band queue slice **B1 — Starboard PR 2 (config panel + polish)**, building on the
> freshly-merged PR 1 (#1259). Flip to `complete` as the deliberate final step.

> **Run type:** `routine · dispatch`

## What I'm about to do

Starboard PR 1 (#1259) shipped a working v1 — raw-reaction listener + `!starboard` config command +
the audited `starboard_service` seam. PR 2 (§6 of [the plan](../planning/starboard-plan-2026-06-21.md))
is the polish layer. This session ships the **config/correctness/UX** subset:

1. **`self_star` exclusion** (correctness) — migration 084 adds `self_star BOOLEAN DEFAULT FALSE`; the
   listener subtracts the author's own ⭐ from the count unless enabled. The plan named this column in §2
   but PR 1 deferred it.
2. **Ignore-channels** (feature) — a per-guild list of channels whose messages never enter the board
   (e.g. spam/bot channels). New `starboard_ignore_channels` table + service/db support + listener gate.
3. **`BaseView` admin-hub config panel** (UX) — a panel matching the role-hub style so config isn't
   command-only.

**Deferred (with reason):** the optional **XP bonus** to the starred author (§6) — it couples the
starboard to the economy and invites star-farming; the reward economics want owner input. Scoped as a
clearly-named follow-up, not built unilaterally.

## Files (planned)

- `disbot/migrations/084_starboard_pr2.sql` — `self_star` column + `starboard_ignore_channels` table
- `disbot/utils/db/starboard.py` — self_star in settings CRUD + ignore-channel CRUD + teardown
- `disbot/services/starboard_service.py` — self_star plumbing + ignore-channel ops (audited) + listener gate
- `disbot/cogs/starboard_cog.py` — self-star subtraction + ignore-channel filter + panel mount
- `disbot/views/…` — the BaseView config panel
- tests mirroring `tests/unit/services/test_starboard_service*.py`

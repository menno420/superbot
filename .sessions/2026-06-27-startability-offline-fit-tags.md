# 2026-06-27 — Per-sector offline-fit startability tags (workflow improvement)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is about to do

Empty-fire dispatch. Acting on the **twice-flagged** self-audit observation (Q-0102 notes in the
2026-06-25 and 2026-06-26 session logs): only the **S2** per-sector live-state file tags its ▶ Next
startable items with an offline-fit phrase (`(offline, self-mergeable)`), and that tag worked as a
fast dispatch signal — but S1/S3/S5 don't carry it, so every autonomous dispatch run (this one
included) burns orient-time discovering which ▶ startables are offline-verifiable vs. needs-live-bot
vs. owner-gated. The previous run's review reached the "route it if it recurs once more" bar.

**Plan (offline, self-mergeable):**
1. Standardize a small per-item offline-fit tag vocabulary on the per-sector live-state files'
   `▶ Next` startable items — `[offline]` / `[needs-live-bot]` / `[owner]` — matching S2's proven
   inline-phrase model, and apply it to S1/S3/S5 (S2 already carries the prose; S4 is the
   docs/reconciliation sector with a cadence-gated ▶ Next).
2. Add a disposable, NOT-CI-wired checker (`scripts/check_startability_tags.py`, Q-0105 header +
   kill-switch) that asserts every sector live-state file's `▶ Next` block carries at least one
   recognized offline-fit tag — so the convention can't silently drift back out.
3. Tests for the checker in `tests/unit/scripts/`.
4. Document the convention in `docs/repo-sector-map.md` next to the existing unattended-fit tag.
5. Record the rule-level proposal as a router DISCUSS block (owner review) — not a unilateral
   CLAUDE.md/router rule edit in an unattended run.

⚑ Self-initiated (Q-0172): yes — promoting the self-audit observation to a built improvement.

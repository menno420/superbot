# 2026-06-16 — PR mergeability keepers: auto-update behind + red-on-conflict

> **Status:** `complete` — shipped; PR #965 auto-merges on green CI.

## Arc

Follow-up to PR #959 (same session). The #959 stall (it sat `behind` main, green-but-unmergeable,
while 12 PRs merged) made the owner ask: wasn't a problematic branch supposed to go **red so an
agent acts**, not rot quietly? I verified the real behavior — a conflict/behind state is a git
property, not a test result, so GitHub never reddens a check for it; native auto-merge won't
auto-update a behind branch (no merge queue); born-red (Q-0133) only covers *incomplete* cards; the
Q-0125 sweep is only every ~30 PRs. Owner chose **build both** (Q-0154).

## Shipped (PR #965)

- **`.github/workflows/pr-auto-update.yml`** — `push: main` → bring open non-draft `claude/*` PRs
  that are `BEHIND` up to date so they re-test + auto-merge; carve-outs left alone; real conflicts
  fall through to the guard. (behind = handled silently)
- **`.github/workflows/pr-conflict-guard.yml`** — `push: main` + `pull_request` + schedule → red
  `conflict-guard` status on any `DIRTY` PR, cleared on resolution (skips `UNKNOWN`). Non-required
  (visibility, not a gate). (conflict = loud red)
- Docs: router **Q-0154**; `autonomous-routines.md` § "PR mergeability keepers".

YAML validated; jq/bash sweep + auto-update filter unit-checked against sample data locally.

## Context delta

- **Discovered by hand:** GitHub's mergeability model — `mergeStateStatus` (`BEHIND` vs `DIRTY` vs
  `UNKNOWN`), that native auto-merge doesn't auto-update behind branches, and that conflicts surface
  as a banner + auto-merge-disable, never a red check. Now captured in Q-0154 + the routines doc so
  the next agent doesn't have to re-derive it from a live stall.
- **Decisions made alone (in Q-0154):** `conflict-guard` is a **non-required** status (visibility,
  no branch-protection change) rather than a hard gate; `push: main` as the primary trigger (cron is
  a laggy backstop); applied to all open PRs (conflict-guard) but only `claude/*` (auto-update).
- **Flagged for maintainer / known limits:** both workflows are UNVERIFIED until the first real
  behind/conflict case exercises them (Q-0105 headers say so). `mergeStateStatus` is computed async,
  so a freshly-pushed PR can read `UNKNOWN` briefly — handled by skipping (the `push:main`/schedule
  re-runs settle it). This PR can still fall behind before it merges (the fix only helps *after* it's
  on main) — I'll merge main in if so.

## 📤 Run report

- **Did:** shipped the two PR-mergeability-keeper workflows (auto-update behind + red-on-conflict) so
  PRs stop sitting silently stuck · **Outcome:** shipped (PR #965, auto-merges on green)
- **Shipped:** #965 — `pr-auto-update.yml` + `pr-conflict-guard.yml` + Q-0154 + routines doc
- **⚑ Owner decisions needed:** `none` (chosen live via AskUserQuestion → Q-0154)
- **⚑ Owner manual steps:** `none` required — `ROUTINE_PAT` already has the Pull-requests + Contents
  write scope these need (same as `auto-merge-enabler.yml`). *Optional:* make `conflict-guard` a
  required check if you want a conflict to hard-block (not necessary — a DIRTY PR can't merge anyway).
- **↪ Next:** watch the first real behind/conflict case to confirm both fire (auto-update brings a
  behind PR forward; a DIRTY PR shows the red `conflict-guard` status).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#959 earlier; this follow-up #965 auto-merges on green) |
| CI-red rounds | 0 real (intentional born-red hold only) |
| Repo-rule trips | 0 (no `disbot/` touched; YAML validated) |
| New ideas contributed | 0 this follow-up (1 already this session — the verdict loop) |
| Ideas groomed | 0 this follow-up (1 already this session) |

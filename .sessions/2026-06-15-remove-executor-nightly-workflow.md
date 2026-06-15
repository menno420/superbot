# Session: Remove the legacy executor-nightly.yml workflow

> **Status:** `complete` — born-red card flipped (Q-0133).

**Branch:** `claude/remove-executor-nightly-workflow-2026-06-15` · **Date:** 2026-06-15 · **Type:** infra/docs (S5/S3) · **Trigger:** owner-directed in-session

## What shipped

Owner deleted the night-executor **console routine** and asked if more disabling was needed — and
it was: `.github/workflows/executor-nightly.yml` was **still on `main`**, so its cron kept opening
scheduled `continue` issues that now reach no routine (orphans). Per Q-0146 (dispatch's cadence is
the console Schedule, `0 */2 * * *`) this workflow is fully superseded, so:

- **Deleted** `.github/workflows/executor-nightly.yml` (the last legacy trigger).
- De-staled the references that called it current / "should be disabled" → **removed 2026-06-15**:
  `autonomous-routines.md` (trigger note · timing caveat · See-also), router Q-0146 (+ "owner action
  DONE"), `current-state.md` stamp-line, `repo-sector-map.md` operations-sector list.
- `scripts/check_loop_health.py` — comment-only: the reconcile issue is now the live ROUTINE_PAT
  canary (the executor prefix kept as a legacy match for any old issues in history); no logic change,
  so the checker still works via `reconciliation-trigger.yml`.

Left genuine historical records intact (the ✅ setup-checklist row, the ROUTINE_PAT A/B-test
explanation, roadmap/idea/planning-pass mentions). `check_docs --strict` ✓; lint ✓.

## 💡 Session idea (Q-0089)

Covered by the standing `check_routine_prompts.py` / loop-consistency idea logged earlier today — a
guard that cross-checks "declared triggers" (console Schedule + reconcile workflow) against the
workflows actually present would have flagged this dangling workflow automatically. No new idea forced.

## ⟲ Previous-run review (Q-0102)

The #908 de-stale correctly said "owner action: disable executor-nightly.yml" but *assumed* deleting
the console routine would handle it — it didn't (routine ≠ workflow file; they're separate surfaces).
The lesson: a "retire X" task isn't done until you've checked **every surface X lives on** — here a
console routine AND a repo workflow file. This PR closes the file half; verifying live `origin/main`
(not the local branch) is what caught it.

## Handoff

The legacy trigger is fully gone now: dispatch fires only on the console Schedule (`0 */2 * * *`).
No remaining owner action on the trigger side. If a Hermes VPS crontab entry still calls
`routine_fire.py` on a schedule, remove it too — otherwise it would double-fire alongside the
console Schedule (owner-side, can't verify from the repo).

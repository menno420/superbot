# Session: De-stale the docs/prompts to the console-Schedule trigger

> **Status:** `complete` — born-red card flipped (Q-0133).

## Shipped

De-staled every **active** trigger description to the console-Schedule reality (`0 */2 * * *`, every
2h), recorded as **Q-0146**: the dispatch prompt intro + step 8 + Maintainer-setup (`hermes-dispatch-bridge.md`);
the fleet table · Stage-1 note · merged-section trigger note · operating cost line · label table ·
timing-caveat resolution (`autonomous-routines.md`); the current-state stamp-line; the Q-0145 trigger
note (marked superseded) + new Q-0146. Left genuine historical records intact (the #865 `routine_fire.py`
ledger entry, Q-0141, the A/B PAT test, and the "what it replaced" mentions). `check_docs --strict` ✓.

## 💡 Session idea (Q-0089)

The `check_routine_prompts.py` guard idea (logged earlier this session) would extend cleanly here:
also assert the **trigger description** in the prompt/fleet-table matches a single declared source
(the console cron), so a future trigger change can't leave a "Hermes cron"-style stale claim that an
autonomous run reads about itself.

## ⟲ Previous-run review (Q-0102)

#900/#904 (the consolidation + trim) were right to flag the trigger as "owner-managed, not in this PR"
rather than guess the final wiring — which is exactly why this clean-up was a quick, low-risk de-stale
once the owner settled on the console Schedule. Lesson kept: when a control-plane decision is still in
flux, document the *current* state and defer the wiring claim, rather than over-committing the doc to a
mechanism that's about to change (Hermes-cron → console Schedule changed twice in one day).

**Branch:** `claude/docs-console-schedule-trigger-2026-06-15` · **Date:** 2026-06-15 · **Type:** docs (S3) · **Trigger:** owner-directed in-session

## What I'm about to do (intentions — born-red)

Owner found a reliable way to set the console **Schedule** trigger and enabled it (`0 */2 * * *`,
every 2h), retiring the Hermes-VPS-cron plan (Hermes proved unreliable for the cadence). Owner fixed
the console prompts; my task = make the in-repo docs/prompt mirrors match. Record as **Q-0146**.

Update the **active** trigger descriptions (the ones an autonomous run reads) from "Hermes VPS cron"
→ "console Schedule (every 2h)":
- `hermes-dispatch-bridge.md` dispatch prompt intro + step 8 + the maintainer-setup/runbook prose.
- `autonomous-routines.md` fleet table · Stage-1 note · the merged-section trigger note · operating
  section · the control-plane caveat (mark the GitHub-schedule-lag observation historical) · See-also
  (mark `executor-nightly.yml` legacy).
- `docs/current-state.md` Q-0145 stamp-line trigger note.
- Router: update the Q-0145 trigger-consequence note + add **Q-0146**.

Leave genuine historical records (the #865 routine_fire.py ledger entry, Q-0141, the A/B PAT test).
Docs only; self-merge on green `check_docs`.

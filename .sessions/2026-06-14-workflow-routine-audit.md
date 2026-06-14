# Session: workflow-routine audit — tools, Hermes, routines, loop health

> **Status:** `complete`

**Branch:** `claude/modest-ptolemy-2xipoh` · **PR:** #853 · **Date:** 2026-06-14 · **Type:** owner-directed review (manual)

## What this session did

Owner-requested workflow-health review. Verified the four pillars of the autonomous system, then
acted on three owner decisions taken live.

### Findings (verified by direct test + live GitHub)
1. **Navigation tools — all 4 active & working:** `context_map.py` (Grimp import graph),
   `wiring_map.py` (EventBus), `check_architecture.py`, CodeGraph MCP `where`/`query`. CodeGraph
   `semantic_search` is non-functional (embeddings never built) but **honestly documented** as
   needing an `embed` pre-run — not drift. Trust tiers held (`dead-unresolved` false-positive on
   `apply_operations` confirmed).
2. **Routines DO fire — the docs were wrong.** The control-plane table claimed `ROUTINE_PAT` was
   unverified and the loop had never self-fired; live GitHub proved both false (the 06-14
   scheduled-executor #819 and reconcile #822/#841 were auto-opened yet authored by `menno420`,
   the PAT owner → ROUTINE_PAT is set; #819→#821→merged #825 ran unattended). Corrected the table.
3. **Timing complaint = GitHub Actions cron lag, not timezone/config.** Same cron fired 01:20 UTC
   one day, 06:04 the next (~4¾ h late); backups ~4 h late both days. Documented the caveat.
4. **One routine genuinely broken:** `backup-db.yml` runs but fails daily — `DATABASE_PUBLIC_URL`
   unset (daily backup-failure issues #823/#773). No working DB backups. Maintainer-side.
5. **Hermes:** wired (VPS, 10 skills, dispatch tested) but `review-merge` still advisory; the
   "sensitive information" dispatch balk diagnosed (see Q-0136).

### Changes shipped (PR #853)
- **Q-0134:** reconciliation cadence widened 20→30 (`STEP=30`; CLAUDE.md + current-state + routines
  doc; next pass now #870). Workflow reads the script, so it propagates with no workflow edit.
- **Q-0135:** `scripts/check_loop_health.py` — live-GitHub probe of the control-plane table
  (ROUTINE_PAT author / open backup-failure / loop-self-fired), folded into the reconciliation
  routine STEP 2 so the table can't silently drift again. +9 unit tests on the pure `classify` core.
- **Q-0136:** Hermes dispatch prompt gained an AUTHORIZED clause (using the named secret env var in
  the `/fire` curl is sanctioned, not a leak) + a diagnosis note. **Owner: re-paste into Hermes.**
- Control-plane table rows 1+6 ticked with evidence; cron-lag caveat; misleading "03:00/05:00
  local" cron references corrected to UTC.

## My opinion on the loop (the owner asked)
The core continue→executor→reconcile chain genuinely works and self-fires. The 20-PR cadence was
too tight at burst velocity (widened to 30). Biggest real gap is **observability of the control
plane** — its state was only a hand-ticked table that drifted; `check_loop_health.py` + the
reconciliation-pass re-verification closes that. The cron lag is GitHub's, not ours; accept
"overnight" or move to an external `workflow_dispatch` trigger (captured idea).

## Still-open / handed to owner
- DATABASE_PUBLIC_URL secret (backups inert), Railway `CLAUDE_ROUTINE_*` deploy, routine
  model/prompt confirmation (control-plane table rows 2–5).
- Re-paste the updated `dispatch.md` into Hermes; deeper Hermes sensitive-info dig deferred.

## 💡 Session idea (Q-0089)
`docs/ideas/external-cron-trigger-for-routines-2026-06-14.md` — drive the overnight cadence from an
external scheduler hitting `workflow_dispatch` (VPS cron) instead of GitHub's best-effort
`schedule:`, which fired ~4¾ h late this session. Keep `schedule:` as a backstop. Genuinely
surfaced by the timing investigation.

## ⟲ Previous-session review (Q-0102)
Reviewing **#849 (born-red session merge-gate, Q-0133):** strong work — it fixed a real race and
dogfooded the gate on its own PR. **What it missed / could improve:** the gate is
*engage-when-present* — it only fires when a PR **adds** a session card. The autonomous routines
(executor/reconciliation) don't reliably add a `.sessions/` card, so a **routine-authored PR can
still merge a partial PR** — the exact #843 race the gate was built to stop, just on the path most
likely to run unattended. **System improvement:** require the routine prompts to create a born-red
session card as their first commit too (or tighten the gate so routine-authored PRs without a card
are held). Captured here as the concrete next hardening of Q-0133; worth a follow-up before
trusting the loop to merge big steps on its own.

## Doc audit (Q-0104)
`check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓ · `check_architecture` 0 errors ·
`check_quality --check-only` ✓ · loop-health + context_map tests ✓. New owner decisions Q-0134/0135/
0136 recorded in the router; new docs reachable (ideas README updated).

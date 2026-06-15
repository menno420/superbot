# Session: Merge dispatch + night-executor into one routine prompt (2 total)

> **Status:** `complete` — born-red card flipped as the final step (Q-0133).

**Branch:** `claude/merge-routine-prompts-2026-06-15` · **Date:** 2026-06-15 · **Type:** workflow/docs (S3 mechanism) · **Trigger:** owner-directed in-session

## What shipped

Owner directive (Q-0145), immediately after Q-0144: the **dispatch** routine takes over all
execution — it and the night-executor always did the same job (dispatch is just the steerable one;
the night agent had a fixed prompt). Consolidated to **one execution routine for everything except
reconciliation** → **2 routine prompts total**.

- **Merged** the dispatch + night-executor prompts (already on the identical Q-0144 12-step
  lifecycle) into the single **dispatch** prompt (canonical home `hermes-dispatch-bridge.md`), which
  absorbed the executor's three distinct bits: the "single execution routine" framing,
  `docs/health/bug-book.md` in the orient list, and the bounded-continuation handoff (step 8).
- **Retired the night-executor** in `autonomous-routines.md`: fleet table → 2 routines; the
  night-executor section → a pointer; label table + prose de-staled (executor/caretaker → dispatch).
- Recorded **Q-0145**; current-state stamp-line updated.

Trigger consequence (flagged, owner-managed, NOT changed here): dispatch is fired by Hermes' VPS cron
→ `routine_fire.py` (reliable), replacing the GitHub `schedule:` cron (proven ~1 run/night, hours
late); the legacy `executor-nightly.yml` should be disabled/repointed. Docs only; `check_docs` ✓.

## 💡 Session idea (Q-0089)

**A `check_routine_prompts.py` consistency guard** — now that there are exactly 2 canonical routine
prompts, a tiny stdlib checker could assert each prompt block contains the load-bearing invariants
(sync-first · never-stop · work-order-is-a-hint · scope-vs-safety-brake · the standing enders) so a
future edit can't silently drop one, and that the fleet table lists exactly the prompts that exist.
Pairs with the Q-0144 paste-ready-files idea (single source → generate the console text + the check).

## ⟲ Previous-run review (Q-0102)

#899 (the Q-0144 canon, this session's slice 1) did the right thing rewriting *both* prompts onto one
lifecycle — which is precisely what made *this* merge a 20-minute job instead of a reconciliation:
the two prompts were already byte-near-identical, so consolidating was deletion + three small folds,
not a rewrite. The lesson worth keeping: when you can see a consolidation coming (two things
converging), **make them converge first, merge second** — the intermediate "identical but separate"
state is cheap insurance that the merge is mechanical. One miss in #899: it left the night-executor
prompt as a full second copy in `autonomous-routines.md`, so for ~one PR the canon lived in two
places; this PR closes that by making dispatch the single home.

## Handoff

**Owner action:** re-paste the merged **dispatch** prompt into the dispatch routine console; **delete
the separate night-executor routine**; disable or repoint `.github/workflows/executor-nightly.yml`
(its `continue`-issue cron now fires a retired routine). Natural next slices: the Q-0089
paste-ready-files + consistency guard (makes the re-paste foolproof and the 2-prompt invariant
enforced). Ledger: the #898/#899/#900-band entries fold in at the imminent #900 reconciliation.

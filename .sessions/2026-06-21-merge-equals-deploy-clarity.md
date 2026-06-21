# 2026-06-21 — "Merge = deploy" clarity (kill the "restart is yours" misinformation)

> **Status:** `in-progress` — born-red HOLD (Q-0133). Flip to `complete` as the final step.

> **Run type:** `manual` (owner-directed, in-chat)

## Arc

Owner caught a real error: at the end of the role-presets session (#1245) I told him "the production
restart is still yours" — but **Railway auto-deploys `main` on every merge**, so a merged change is
live on its own. The owner's point was two-fold: (1) the factual claim is wrong, and (2) the fact that
I parroted it means the deploy reality is buried / the docs are too crowded.

This is a docs-only correction at the **roots** so the next agent stops repeating it — not more text:

1. **`docs/operations/production-deployment.md`** — a single unmissable "Merge = deploy" lead on
   *How code reaches production* (it already said this correctly, just not loudly), and drop the
   misleading "restarts … stay the maintainer's" shorthand from the consequence bullet.
2. **`.claude/CLAUDE.md`** — fix the binding shorthand "**Merge ≠ deploy** — production
   restart/prod-checks stay the maintainer's" (the line agents internalize and copy) to the accurate
   "**Merging IS deploying** … never tell the maintainer to restart/deploy a merge; only live
   verification / rollback stay his." Owner-directed in-session → applied directly under the Q-0106
   live-owner exception, citing **Q-0193**.
3. **`docs/owner/maintainer-question-router.md`** — **Q-0193** provenance.
4. **`.session-journal.md`** — one prevention line next to the already-accurate auto-deploy fact.

## Status: building. (close-out notes on flip-to-complete.)

## 📤 Run report

- **Did:** (in progress)
- **Run type:** `manual`

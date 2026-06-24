# Session — 2026-06-24 · Essential Setup survives restart (revive in place)

> **Status:** `complete` — the new setup wizard now survives a bot restart.
> Full `check_quality --full` green (12516 passed); arch 0 new errors; PR #1440.

**Trigger:** Owner — "the setup wizard seems to not survive restart, can you fix this?" Follow-on to
the logging-step fix (#1439, merged). Owner chose (AskUserQuestion) the **revive-in-place** option:
after a restart the in-channel wizard message itself shows a **Resume** button and continues from the
exact step.

## Why it died

`EssentialFlow` held all state in memory; the step views are non-persistent `BaseView`s, so on restart
the wizard message's buttons "interaction failed". (The setup **launcher** already survives — a
persistent view re-bound on `on_ready`; the in-channel Essential Setup flow never adopted that
pattern.) Essential Setup is **direct-apply**, so no *configuration* is lost on restart — only the
wizard's position + live buttons.

## What changed (revive-in-place — mirrors the launcher's `_resume_launchers`)

- **Migration 099** — `setup_session.essential_message_id` + `essential_step` (nullable; the wizard
  message snowflake + step). Channel reuses `setup_channel_id`. Forward-only + idempotent.
- **DB + service** — primitives (`set_essential_anchor` / `set_essential_step` / `clear_essential_anchor`)
  + `SetupSession` fields + service wrappers (UI-position bookkeeping, not audited config mutations).
- **`EssentialSetupResumeView`** (`PersistentView`, static custom_id, `STANDARD_NAV=False`,
  setup-admin-gated) — rebuilds the flow at the saved step and edits the message back to the live wizard.
- **Persistence** — anchor recorded on post (+ `mark_in_progress`); step persisted on every move;
  anchor cleared + `mark_complete` when the flow reaches the summary.
- **`SetupCog`** — registers the resume view at `cog_load`; `on_ready` calls
  `revive_essential_flows(bot)` (the sweep lives in the view module so the cog stays ≤799 LOC, under
  the 800 ceiling — the size guard caught this and I extracted accordingly).
- **Tests** — DB/service/view/cog coverage incl. resume-at-step, anchor lifecycle, message-gone
  clears anchor. 186 in the four files; full suite green.

## 💡 Session idea (Q-0089)

**Extract a shared `revive_anchored_message` helper.** This session's `revive_one_essential_flow` and
the launcher's existing `_resume_one_launcher` are near-identical: resume session → fetch the anchored
message by id → re-edit it with a fresh persistent view (clear the anchor if it 404s). A small generic
helper — `revive_anchored_message(guild, channel_id, message_id, build_view, on_missing)` — would DRY
the two and make "survives restart" a one-liner for the *next* anchored flow (e.g. a future ticket
panel or giveaway message), instead of each surface hand-rolling the same fetch/edit/clear dance.
Buildable, contained, and it turns a copied pattern into a reusable seam. (Dedup-checked `docs/ideas/`:
no existing anchored-flow-revive idea — grep empty.)

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` log: the **logging-step defer fix** (#1439, this same chat). Did well: tight
root-cause diagnosis and it used the codebase's own `safe_defer` remedy + a regression test. What it
*structurally* missed — and what became THIS session — is that the **same module** (`essential_setup.py`)
carried a *second* re-introduced gap: it skipped the advanced wizard's restart-persistence just as it
had skipped its deferral. Both are the same root pattern: **the Essential Setup "v2" spine was built
without the v1 advanced wizard's hard-won robustness (defer slow work · persist position · register
persistent views).** **System improvement (acted on as the Q-0089 idea + noted for future v2 work):**
when fixing a bug in a freshly-built replacement surface, run a quick *"what did the v1 already solve
that this v2 might have dropped?"* diff — it would have surfaced the restart gap *alongside* the defer
gap in one pass instead of two sessions. The defer-lint idea from #1439 and the revive-helper idea here
are the two concrete halves of that checklist.

## 📋 Doc audit (Q-0104)

`check_docs --strict` ✓, `check_current_state_ledger --strict` in sync, arch 0 new errors. Migration
099 is self-documented (header: purpose · column semantics · rollback). The AskUserQuestion answer
("revive in place") is a UX-depth pick recorded here + in the PR, not a binding rule, so no router Q.
No `current-state.md` entry yet — the ledger keys off **merged** PRs; #1440 is picked up by the next
reconciliation pass (note: #1440 is also a Q-0107 cadence boundary — that docs pass is the routine's,
not this owner-directed session's, per Q-0124). Claim file deleted at close.

## Context delta

- **Surprise (carried from #1439):** twice now the Essential Setup spine re-introduced a problem the
  older advanced wizard had already solved. The infrastructure existed both times (`safe_defer`;
  `PersistentView` + the launcher's resume sweep) — only adoption was skipped. Strongest argument yet
  for a "v2 inherits v1's lessons" checklist/guard.
- **For next session:** the lighter follow-ups, if wanted — (a) the shared revive helper (Q-0089
  idea); (b) extend restart-revive to the inline-fallback flow (no `#superbot-setup` channel), which
  this PR intentionally leaves un-revived (degraded path); (c) the #1439 defer-lint.

## ⚑ Self-initiated: NO — owner-directed feature; the owner picked the revive-in-place depth via
AskUserQuestion. The cog-size extraction (sweep → view module) was a guard-driven refactor, not new scope.

# 2026-06-24 — Essential Setup step 0: server-type starter preset (direct-apply)

> **Status:** `complete` — PR #1437; auto-merge armed (MCP-created, so armed
> manually per Q-0127); merges on green. Full CI mirror green (12,488 passed, 48
> skipped, 2 xfailed; mypy + lint + arch 0 errors). The one CI red before this flip
> was the **born-red session gate** doing its job (Q-0133) — not a real failure.

> **Run type:** `routine · dispatch`

## What I'm about to do
Scheduled dispatch fire, no work order. Open bugs are blocked/data-gated for an
unattended run (BUG-0009 remaining slices need BTD6 release-order data + plan-level
work; BUG-0011 needs a VPS repro; BUG-0019 #1 is an owner design fork). So I take the
**owner-directed ▶ next** for the Essential Setup spine: **step 0 — "What kind of
server is this?"** (the server-type starter preset), the explicit remaining item in
[`planning/setup-wizard-restructure-plan-2026-06-24.md`](../docs/planning/setup-wizard-restructure-plan-2026-06-24.md)
§5 / §7 (PR 1 tail).

**The design decision the plan flagged ("presets are draft-only today; needs a
direct-apply path"):** step-0 starter sets are **pure settings bundles** applied
through the same audited `SettingsMutationPipeline` (`_StepView._set`) every other
spine step uses — *not* the draft-only `automation_templates.SERVER_PRESETS` (those
bind channels / create roles+rules → need operator picks + Final Review, the wrong
shape for Q-C's "fastest, nothing irreversible"). Every value is a channel-independent
boolean/scalar, so picking a type never creates or binds anything and is fully
reversible from each feature's own panel later.

Five server types (Community · Gaming · Support · Creator · Just exploring), each a
curated bundle of automod toggles + `moderation.dm_on_action` + an XP rate (reusing
`_XP_RATES`). Inserted as the new first step; tests updated for the index shift +
new step coverage.

## Shipped (PR #1437)
- `disbot/views/setup/essential_setup.py` — **`ServerTypeStep`** (the new first
  step), `_ServerTypePreset` (frozen dataclass), `_SERVER_TYPES` (the five starter
  sets), `_server_type` lookup, `_ServerTypeSelect` + `_ServerTypeSaveButton`.
  Inserted first in `EssentialFlow._steps` (flow now **7 steps**). Each starter set
  is a curated bundle of **channel-independent** settings — automod toggles (the same
  `enabled`/`spam_enabled`/`invites_enabled`/`caps_enabled`/`mentions_enabled` names
  the block-spam step writes) + `moderation.dm_on_action` + an XP rate (reusing
  `_XP_RATES`) — applied verbatim through the inherited audited `_set`
  (`SettingsMutationPipeline`). Community/Creator caps-allowed; Gaming invites-allowed;
  Support strict; Just-exploring = basic spam only (XP untouched).
- `tests/unit/views/setup/test_essential_setup.py` — +4 step-0 tests (requires a
  pick · community bundle + the resolved `_XP_RATES` triplet · exploring minimal +
  skips XP · gaming allows invites) + a **known-settings invariant** pinning every
  starter set to channel-independent keys + a resolvable `xp_rate`. Existing step
  tests shifted for the new index ordering (ServerType=0 … HelpDesk=6).
- Docs de-staled: plan §Build-progress + §5 + §7, and `current-state/S1-bot.md`.

### The design decision the plan flagged
The plan left open: *"presets are draft-only today; needs a direct-apply path;
design decision before building."* Resolved by **not** reusing
`automation_templates.SERVER_PRESETS` — those bind channels and create roles/rules,
so they need operator picks + a Final Review (the wrong shape for Q-C's one-tap,
instant, fully-reversible starter). The starter sets are pure settings bundles on the
direct lane, so picking a type creates/binds nothing and is reversible from each
feature's own panel. No named resource → Q-0205 optional-typing satisfied trivially.

## 💡 Session idea (Q-0089)
**Show the active starter set on the "All done" summary as an at-a-glance baseline
card.** Step 0 now establishes a server-type baseline, but the closing
`EssentialSummaryView` only lists the per-step `applied` lines — it doesn't surface
*which server type* shaped the run or which later steps refined vs. inherited that
baseline. Idea: have the summary lead with "Starter set: 🎮 Gaming" and mark each
following line as *(from starter set)* vs *(you customised)*, so an operator who
clicked through fast sees exactly what their one pick turned on. Cheap (the data is
already in `flow.applied`); makes the fast-path's value legible. Dedup-checked — not
in `docs/ideas/`; smaller than a plan, flagged for grooming.

## ⟲ Previous-session review (Q-0102)
Reviewed **2026-06-24-xpmenu-rank-card-h3** (#1413). **Did well:** tight, single-
surface H3 migration with a clean shared `_decorate()` extraction (killed real
duplication) and a focused 6-test pin including the help-nav-stays-embed contract —
exactly the "complete a function, don't pad" discipline. **Could improve / system
note:** it (and the two H3 runs before it) each shipped one small card surface, and
the running S1 ▶ Remaining note has grown into a dense multi-clause paragraph
tracking "H1 ✅ / H2 🟡 / H3 incremental" inline. That inline progress-ledger is
drifting toward the same restate-everywhere pattern the one-fact-one-home rule warns
about. **Improvement:** the visual-card-engine rollout now has enough moving parts
(H1/H2/H3 × per-surface adoption) to deserve a tiny `planning/` rollout-tracker with
a checkbox table, so the S1 sector line can shrink to a one-line pointer instead of
absorbing a new clause every dispatch run. (Flagged here, not built — out of this
PR's scope; a grooming candidate.)

## ✅ Doc audit (Q-0104)
- `check_docs --strict` green in CI (this run); `check_quality --full` green locally.
- New owner decisions: **none** (executed existing plan + Q-C/Q-0205, no new ones).
- Plan + S1 sector updated in lock-step with the merge; no chat-only facts left
  un-homed. `check_current_state_ledger` not run for #1437 (not merged yet — the next
  reconciliation pass folds it; benign newest-merge lag, Q-0166).

## 📤 Run report
- **Run type:** `routine · dispatch`
- **PR:** #1437 (Essential Setup step 0 — server-type starter preset).
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none (merge auto-deploys; no off-repo action)
- **⚑ Self-initiated:** none (executed the documented owner-directed ▶ next plan
  slice — setup-wizard restructure plan §5/§7 step 0)

## Handoff — next dispatch
- **DONE:** Essential Setup **PR 1 spine is now fully complete** (all 7 steps incl.
  step 0). Step 0 ships the direct-apply starter-set pattern; `_SERVER_TYPES` is the
  extension point (add a type = one tuple).
- **▶ NEXT (setup lane):** **PR 2 — extras menu + "Check my setup"**
  (`planning/setup-wizard-restructure-plan-2026-06-24.md` §7). Each existing config
  surface (starboard, counters, security, image-mod, karma, AI, reaction roles,
  giveaways) as a one-action extra reachable from "All done" / `/setup`, plus a single
  read-only "Check my setup" health button folding in scan/readiness/diagnostics. Then
  **PR 3** retires the dead/legacy sections + reworks the Advanced editor (Q-E).
- **Other startable S1 lanes** (unchanged): Project Moon runtime PR 1 · botsite React
  PR 2 · the visual-card-engine H3 incremental adoption (thin remaining surface — see
  the previous-session note above; consider the rollout-tracker idea first).
- **Bugs:** still blocked/gated for an unattended run — BUG-0009 (BTD6 release-order
  data + plan-level), BUG-0011 (VPS repro), BUG-0019 #1 (owner design fork).
- **Env:** CodeGraph up (v3.11.2); Grimp available; no arch warnings I introduced.

# 2026-06-25 — Project Moon (Limbus) knowledge domain — runtime PR 1

> **Status:** `complete`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-adgv45` · **PR:** #1453

## What I did

Scheduled dispatch fire, no work order → advanced the next on-plan slice. Picked the
owner-directed **Project Moon knowledge domain** program (Q-0192, "full parity, all
games"; [plan](../docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md)), a
▶-startable item in S1. Built **Slice A PR 1** as a safe, fully-offline vertical:

- **Committed Limbus structural/lore data** — `disbot/data/projmoon/limbus/` (12 Sinners ·
  7 Sins · 3 damage types · 5 E.G.O grades · status keywords), each provenance-tagged + a
  README. Deliberately the *patch-stable* facts only — **not** the fragile exact-number
  StaticData dump (which feeds AI grounding; wrong-unattended it poisons the domain).
- **`services/projmoon_data_service.py`** — typed loader + validation (canonical/alias
  collision checks) + a longest-match resolver. Mirrors the BTD6 data-service shape, small.
- **`utils/projmoon/keywords.py`** — the curated `has_limbus_context()` detector (reserved
  for PR 2's routing; bare Sin/ambiguous status words deliberately excluded to avoid
  over-routing).
- **`!pm` / `/pm` browse surface** — `views/projmoon/` `LimbusBrowseView` (one button per
  category + per-entry detail) + per-category lookup subcommands. Its **own top-level
  Project Moon Help hub** (like BTD6 — a knowledge domain, not a Games activity, so it
  isn't subjected to the Games actionability contract).
- Full subsystem registration via the `new_subsystem.py` checklist (registry, panel
  command, extension role, INITIAL_EXTENSIONS, surface/command/navigation-map rows,
  crosswalk + dashboard/site/env artifacts regenerated).
- **66 new tests** (data service · keywords · cog/view). Deliberate hub-count pin updates
  (7→8) for the new top-level hub.

**No AI hot-path change, no BTD6 change, no DB, no writes** — read-only reference, like
`btd6_reference`. PR 2 (the `AITask.PROJMOON_ANSWER` grounding wiring into
`natural_language_stage.py`) is the next slice and **wants a Q-0086 runtime walk**.

## Verification

- `python3.10 scripts/check_quality.py --full` → **all checks passed** (12,487 passed,
  48 skipped, 2 xfailed).
- `check_architecture.py --mode strict` → 0 (no new violations).
- `check_command_reachability.py --mode strict` → 0 gaps (`!pm` reachable).
- `check_current_state_ledger.py --strict` → exit 0 (only benign newest-merge lag).

## Handoff (the continuation is current-state ▶ Next action)

**Project Moon PR 2** — wire the grounding path: add `AITask.PROJMOON_ANSWER`
(`core/runtime/ai/contracts.py`), a thin `projmoon_context_service` reusing the BTD6
tag/cap/provenance render + the answer-faithfulness guard, and the 3 wiring points in
`core/runtime/ai/natural_language_stage.py` (route on `has_limbus_context`, floor, guard
haystack). **Touches the gated AI stage → flag for a runtime walk.** Then Slice B = extract
the shared `KnowledgeDomain` seam from BTD6 + Limbus + the exact StaticData numbers.

## 💡 Session idea (Q-0089)

**A `has_<domain>_context` over-route harness.** As the second knowledge domain lands, the
real risk is two curated keyword sets fighting (a Limbus "sink" vs a BTD6/economy "sink").
Idea: a tiny offline test fixture that runs every domain's `has_*_context` over a shared
corpus of cross-domain phrasings and asserts **at most one** domain claims each — a
cheap guard against the multi-domain over-routing class *before* PR 2 wires routing.
(Genuinely believe in it — it's the cross-domain version of the BTD6 keyword-curation
discipline, and it gets valuable exactly when the seam generalizes in Slice B.)

## ⟲ Previous-session review (Q-0102)

The prior dispatch runs (#1449 PR 2 extras-menu, #1451 PR 3a) executed the setup-wizard
tail cleanly and left a *sharp* S1 ▶ Next — which is exactly why this run could orient and
pick a fresh, non-conflicting lane in minutes. One improvement they surface: the S1 "▶ Next
startable" list mixes *shipped-with-tail* items and *fresh* items in one bullet stream, so
an empty-fire run has to read several bullets to find a clean, ungated, offline-buildable
slice. **System improvement:** tag each ▶-startable item with the same startability glyphs
the roadmap uses (▶ offline-buildable / ⛔ needs-live-verify / 👤 owner-gated) so a dispatch
run can pick a safe lane at a glance — the per-sector mirror of the roadmap convention
`check_sector_map.py` already enforces. (Captured as a candidate; not applied this run to
stay in scope.)

## 📤 Run report

- **Did:** shipped a standalone Limbus (Project Moon) knowledge domain — data + service +
  resolver + `!pm`/`/pm` browse surface (own top-level Help hub) · **Outcome:** shipped
- **Shipped:** #1453 — Project Moon (Limbus) knowledge domain, runtime PR 1 (browse/lookup; no AI hot-path)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none` (PR 2's open design Qs — lore depth, unified vs per-game surface — are non-blocking and already routed in the plan §7)
- **⚑ Owner manual steps:** `none` (read-only committed data; a merge auto-deploys)
- **⚑ Self-initiated:** Project Moon PR 1 — chosen on an *empty* dispatch fire. Executes an
  already-owner-approved plan (Q-0192) + a ▶-startable S1 queue item, not a fresh idea→plan
  promotion; flagged here for visibility since no work order named it.
- **↪ Next:** Project Moon **PR 2** — `AITask.PROJMOON_ANSWER` + grounding into
  `natural_language_stage.py` (reuse tag/cap/provenance + faithfulness guard); **flag for a
  Q-0086 runtime walk** (gated AI stage). Then Slice B = `KnowledgeDomain` seam + StaticData numbers.

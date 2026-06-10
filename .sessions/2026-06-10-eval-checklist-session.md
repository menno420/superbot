# 2026-06-10 — Production eval checklist (eval-session support)

**PR:** #673 (draft at first push per Q-0052). **Prompt:** "continue with the
plan / what previous agents suggested; meanwhile, what do I manually need to
test in the server?"

## Arc

The two halves of the prompt converged: the EOD audit §6 + the #671/#672
session log both name the **maintainer's production walk** as the single
highest-value next action (it gates AI §7.5 and mining structures §7.5), and
the maintainer's "what do I test?" is that walk asking for its working doc.
So the eval checklist *is* the plan continuation, not a side errand.

## Shipped

**`docs/audits/production-eval-checklist-2026-06-10.md`** — every
user-visible surface from the #606–#672 burst, tiered by who can verify:

1. **Tier 1 — AI model loops** (sandbox has no provider key; sign-off
   un-gates §7.5): the $19,840 inclusive round-cash anchor (Q-0043) ·
   profile setup via `!aimenu` → Tools + the #634 workflow + dry-run
   analyzer · the three #639 self-awareness questions with audience-tier
   checks · the Navarch/carryover/minion/diacritic grounding class
   (#662/#668), phrased in the deliberately-sloppy forms that broke live.
2. **Tier 2 — mining economy** (balance verdict gates structures §7.5):
   panel walk (new 🧰 Gear / 📖 Recipes), atomic-purchase rejection check,
   the diamond-lantern→MAGMA run, duels wear, game-XP boards, PIL cards.
3. **Tier 3 — BTD6 spot-check** — closes decode-status **item 4**; every
   expected answer re-probed against source via `scripts/btd6_probe.py`
   this session (Orca · Wall Street $4,000/round · Navarch $3,200
   end-of-round · Mini Sun Avatar → Sun Temple · Pouākai sans diacritic).
4. **Tier 4/5** — Settings hub (12 groups incl. new proof_channel),
   `!prizemenu` unbound-identical check, staff-hub Access Map / Help
   Preview, chain modals (the #671 "service-verified, never human-clicked"
   debt), Help paths, regression sweep (dropped `!hub`/`!server` aliases).

Linked from EOD audit §6 (its companion) + current-state Last-updated.

## Context delta

- **Needed but not pointed to:** the #634 workflow's *activation condition*
  (`workflow="analyze_execute_verify"` only on `btd6_grounded`/`_strict`
  presets — the default profile never runs it) lives only in
  `ai_orchestration_presets.py` source. Every "awaits prod check" banner
  says *that* it needs checking, none says *how to arm it*. The checklist
  now carries it; if a future doc wants it, the orchestration plan's Phase 4
  section is the home.
- **Pointed to but didn't need:** nothing significant; audit §6 + the
  session-log "flagged for maintainer" lines were exactly the right trail.
- **Discovered by hand:** `!mineinv` is a thin alias for `!inventory` (the
  PIL card renders from the panel's 📦 button path); leaderboard category
  spellings (`gamexp`/`crafting` + aliases) come from `rank_providers`.
- **Decisions made alone:** checklist lives in `docs/audits/` with badge
  `audit` (it's the walk's result ledger, companion to the EOD audit, not a
  plan); tiered by *who can verify* rather than by subsystem — the
  maintainer's scarce capability (model loops, clicks, feel) goes first.
- **Weak point of what shipped:** expected values are source/probe-verified,
  but panel *click* flows are described from code reading — a button label
  drift would only surface during the walk itself (acceptable: that's what
  the walk is for).
- **One change that would have helped:** nothing structural — this was the
  fastest orientation yet (≈15 min to full picture); the per-lane bullets +
  audit §6 + session-log flag lines composed perfectly.

## Open after this session

Unchanged queue (Batch 9 RS05/RS10 · Help overlay editor UI plan-first ·
setup PR4 planning · AI §7.5 post-prod-check) — plus the eval itself, now
armed. This session stays live as the ride-along fixer for eval findings.

---

## Continuation (same session): Help overlay editor UI plan — PR #674

#673 merged within minutes; while the maintainer walks the checklist, the
session took the queue's next non-colliding item — the **Help overlay
editor UI (plan-first)** — and produced
`docs/planning/help-overlay-editor-ui-plan-2026-06-10.md`.

**Why this item:** all owner decisions answered (Q-0055/56/58/59), zero
overlap with the surfaces under eval (the editor *writes* through the
#659-verified seam; the eval walks *read* paths), and the EOD audit lists
it among "most ready for further work". RS05/RS10 still want their own
focused session; setup PR4 planning needs the wizard plan re-read first.

**Plan shape:** 2 PRs. **A** (low risk, no migration): `views/help/editor.py`
on BaseView; entry points = staff-hub `✏️ Help editor` button +
`cogs/help/schemas.py` `DomainPanelSpec` ("Help appearance", capability
`help.settings.configure`, Settings taxonomy 12 → 13); every action = one
`set_overlay_fields` call. **B** (medium): migration widening the 064
`entity_kind` CHECK with `'home'` (exactly as 064's header pre-plans) +
bounded home-only columns; `set_home_message`; Home render consumption
(absence byte-identical, pinned); `HomeMessageBuilderView` with
**Save-disabled-until-previewed** enforcement of Q-0059's mandatory preview.

**Context delta (continuation):**

- **Needed but not pointed to:** nothing — migration 064's header comment
  literally pre-planned the Q-0059 widening, and `DomainPanelSpec`'s
  docstring + the cleanup example made the Settings integration turn-key.
  The substrate docs from #654/#657/#659 are exemplary; this plan mostly
  *collects* decisions rather than making them.
- **Decisions made alone:** (1) setup/final-review integration **deferred**
  (audit marks it optional; direct-lane is the right lane for a focused,
  reversible single-domain edit per `ownership.md` — revisit on ask);
  (2) named colors only in the v1 color picker (no hex parsing);
  (3) staff-hub button beside 👁 Help Preview so edit + verify sit together.
- **Flagged for maintainer:** none blocking — the plan executes on existing
  authority once an implementation session picks it up.

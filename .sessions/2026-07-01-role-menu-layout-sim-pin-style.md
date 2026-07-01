# 2026-07-01 — Layout sim: pin Style first-screen (owner correction)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13576 passed**; lint clean; arch 0 new). PR #1613.

**Branch:** `claude/reaction-roles-counter-bgxnyd` (restarted from `main` @ #1612 — the sim merged).

## What I'm about to do (intentions)

Owner corrected the layout sim's recommendation: **"the style button should definitely be visible on
the first screen."** My model had treated Style (dropdown-vs-buttons) as a rarely-tapped knob (because
the RSVP template sets it) and folded it behind Advanced — but Style is a **primary, up-front choice**
about the menu's whole shape, so it belongs first-screen. Encode that in the sim:

1. A `PINNED_FIRST_SCREEN = {"style"}` set — pinned buttons are never folded (the fold-builder skips
   them) and get a row-0 pull via a new `pin_penalty` (LAMBDA_PIN).
2. Surface Style as a real up-front choice in the colour + game journeys (dropdown-vs-buttons is a
   genuine early decision there).
3. Re-run + update the docstring FINDINGS + tests.

## What shipped

Encoded the owner's "Style stays first-screen" directive in the layout sim + re-optimised:

1. **`tools/sim/role_menu_layout_sim.py`** — `PINNED_FIRST_SCREEN = {"style"}` (never folded, `LAMBDA_PIN`
   row-0 pull via `pin_penalty`); the fold-builder now skips pinned members, so `lean_advanced` folds
   five knobs (Theme/Card/Counts/Mode/Limit) and **keeps Style visible**. Style added to the colour +
   game journeys (a real up-front choice there). Docstring FINDINGS refreshed.
2. **`tests/unit/tools/test_role_menu_layout_sim.py`** — updated the fold test (Style no longer folded)
   + a new guard that **every** optimised variant places Style on row 0.

**Corrected result (stable across seeds 1/2/7):** current ≈ 40. **lean_advanced (~ −52%)** —
`row0: Template Packs Roles Style Text · row1: Back Colours Channel Advanced Post` (Advanced hides the
five knobs; Style stays row 0). **Low-risk re-order (~ −42%)** keeps all 14, Style on row 0. Advisory —
still doesn't change the builder.

## Context delta

- **Discovered:** the owner's correction is exactly the "verify the model against real knowledge" loop —
  my journey weights treated Style as template-set/rarely-tapped, but dropdown-vs-buttons is a *primary*
  choice. The `PINNED_FIRST_SCREEN` mechanism is deliberately general (extensible to Counts/others if the
  owner wants more pinned) rather than a one-off Style hack.
- **Decisions made alone (reversible):** pinned Style to **row 0** (not just "not folded") since "first
  screen" means visible up-front; added it to two journeys to reflect genuine usage.
- **🛠 Friction → guard:** the new "Style on row 0 in every variant" test locks the directive in — the
  sim can't silently re-fold Style on a future weight tweak.

## 💡 Session idea (Q-0089)

Contributed in the parent sim session (instrument builder button-presses → data-driven weights). Per
Q-0089 (one genuine idea per session, not per follow-up commit), no forced second idea here — the
data-driven-weights idea is the direct answer to "is Style really first-screen-worthy?" and stands.

## ⟲ Previous-session review (Q-0102)

Predecessor is the parent **layout-sim PR (#1612)**. **Did well:** transparent, tunable model with a
documented cost function + stability check across seeds. **What this correction proves it missed:** it
shipped a recommendation (fold Style) that contradicted the owner's real UX intent — because the journey
weights were my estimates, unverified against how the owner actually thinks about the builder. **System
note:** advisory sims should ideally surface their most load-bearing assumptions for a quick owner
gut-check *before* the recommendation is presented as "optimal" — the Q-0089 instrumentation idea is the
durable fix, but even a one-line "key assumptions" callout in the report would have flagged the Style
weight for correction sooner.

## 📤 Run report

- **Did:** encoded the owner's Style-first-screen correction into the layout sim (pin + re-weight) and
  re-optimised. · **Outcome:** shipped (advisory tool; no UI change)
- **Shipped:** PR (this) — sim(roles): pin Style first-screen + re-optimise
- **Run type:** `manual · owner-directed`
- **Class:** tooling / analysis (read-only, disposable, test-guarded)
- **⚑ Owner decisions needed:** still the adopt choice — lean (−52%, Style visible) vs safe re-order
  (−42%) vs hold.
- **⚑ Owner manual steps:** none (no runtime change).
- **⚑ Self-initiated:** no — owner-directed correction.
- **↪ Next:** adopt the chosen layout in `role_menu_builder.py`; the Q-0089 press-instrumentation for
  data-driven weights.

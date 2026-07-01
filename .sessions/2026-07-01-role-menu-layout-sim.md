# 2026-07-01 — Role-menu builder button-layout simulation

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13550 passed**, 48 skipped; lint/mypy clean; arch strict 0 new). PR #1612.

**Branch:** `claude/reaction-roles-counter-bgxnyd` (restarted from `main` @ #1608 — prior PR merged).

## What I'm about to do (intentions)

Owner asked (after the builder preview-fix): "create a simulation to find out the most optimal button
placements and functions." Build a real optimizer (in the `tools/sim/` precedent) that models the
builder's buttons + weighted operator journeys + a transparent UX cost model, and searches for the
best layout + function set. Deliver the tool + findings; adopting a layout is an owner-gated follow-up.

## What shipped

1. **`tools/sim/role_menu_layout_sim.py`** — a seeded (deterministic) simulated-annealing optimizer over
   the builder's button layout AND function-set variants. Models: the **14 live buttons** (drift-guarded
   against `role_menu_builder.py`), **8 weighted operator journeys** (RSVP / colour / game / notification
   / verify / custom / edit — RSVP-led, templates short-circuiting config), and a **transparent cost
   model** (prominence by top-left reading index; travel with row jumps costlier than column steps;
   submenu-open penalty for folded functions; layout terms for group contiguity + Post/Back submit/back
   corners). Ranks variants, prints the winning grid + per-journey tap cost vs. the current layout.
   Findings are baked into the module docstring.
2. **`tests/unit/tools/test_role_menu_layout_sim.py`** — +7 guards: inventory drift-guard (every sim
   button still exists in the live builder), current-layout integrity, weights-sum-to-1, determinism
   (same seed → same cost), optimiser-beats-current, cost-model-orientation sanity (hot button top-left
   < bottom-right), and the lean_advanced fold shape.

**Findings (stable across seeds 1/2/7):** current 14-button/3-row builder ≈ 34.1 cost (it leads with
rarely-tapped knobs). Two improvements: **low-risk re-order** (all 14, content on row 0, Post
bottom-right) ≈ **−45%**; **best = "lean_advanced"** — fold the six rarely-tapped knobs
(Theme/Card/Counts/Style/Mode/Limit) behind one **⚙️ Advanced** button → a 9-button/2-row builder ≈
**−55%** (`row0: Template Packs Roles Text Colours · row1: Back Channel Advanced Post`).

**Recommendation is advisory — this PR does not touch the builder.** The lean fold is a product call
(hides six functions behind Advanced; the RSVP template already sets Style/Counts/Mode, so the common
path never needs them); the re-order is a safe mechanical win. Adoption is the owner's pick, done next.

## Why this is contained / safe

Read-only, stdlib-only, disposable advisory tool in `tools/sim/` (established precedent —
`help_menu_grouping_sim`, `setup_wizard_sim`). No runtime code, no migration, no builder change. The
drift-guard keeps the sim honest against the live builder.

## Context delta

- **Discovered:** my first cost model put **Post on the top row** — because it charged
  find-from-scratch prominence to Post even though Post is a colour-coded anchor (green = submit) users
  learn once. Fixed the model (action buttons pay no prominence; the convention penalty places them),
  and the winner became sensible (Post bottom-right). A good reminder that a sim's output is only as
  trustworthy as its cost model — so the model is fully documented + the weights tunable, and I checked
  the winner is stable across seeds before trusting it (the Q-0120 "verify the tool" instinct).
- **Decisions made alone (reversible):** modeled the journey weights from the owner's RSVP-first
  priority + general self-role usage (documented as judgment); scoped the deliverable to the **tool +
  findings** and left **adopting** a layout as an owner pick (the lean fold changes the feature surface
  — a product call, not a mechanical edit).
- **🛠 Friction → guard:** ruff's `S101` (no-assert) fired on the sim's asserts (the `tools/**/*.py`
  ignore covers S603/S607 but not S101) — converted them to explicit `raise`s rather than widen the
  lint ignore. The inventory drift-guard test is itself the friction→guard for "the sim silently
  drifting from the real builder."

## 💡 Session idea (Q-0089)

**Instrument the builder's button presses → feed the sim real weights.** The sim's journey weights are
my best-judgment guesses; the honest next step is to close the model→measure loop: log an **aggregate**
per-button press counter for the builder (the exact privacy-safe pattern `role_menu_pickup_stats`
already uses — counts only, no per-user history), then add a `--weights <file>` input so the sim
re-optimises against *real* usage instead of assumptions. That turns "optimal per my model" into
"optimal per what operators actually do", and would either confirm or correct the −55% recommendation
before anyone commits to a UI change.

## ⟲ Previous-session review (Q-0102)

Predecessor is **#1608 (the builder preview-fix)**. **Did well:** root-caused a real bug straight from
the owner's screen recording (ephemeral `Message.edit()` no-op), fixed the whole class (builder +
manager, not just the one symptom), and added routing tests that pin the fix. **Missed / system note:**
it knowingly **scoped out `ReactionRolesPanel._rerender`** (the emoji panel — same latent bug) to keep
the PR verifiable. That's a reasonable call, but a "same bug, deferred" instance can rot silently; it's
tracked only in the ↪ Next line. The Q-0089 static guard I proposed last session (flag `self.message
.edit(` in `views/`) is exactly what would keep such deferrals honest — worth actually building it as a
small checker so "deferred = tracked by CI", not "deferred = hope someone remembers".

## 📤 Run report

- **Did:** built + ran a deterministic optimizer for the reaction-role builder's button layout +
  function set; produced a stable, documented recommendation (−45% re-order / −55% lean fold).
  · **Outcome:** shipped (advisory tool; no UI change)
- **Shipped:** PR #1612 — sim(roles): optimizer for the menu-builder button layout
- **Run type:** `manual · owner-directed`
- **Class:** tooling / analysis (read-only, disposable, test-guarded)
- **⚑ Owner decisions needed:** **which layout to adopt** — (a) low-risk re-order (−45%), (b) lean
  Advanced-fold (−55%, hides six knobs behind ⚙️ Advanced), or (c) leave as-is / tune the weights.
- **⚑ Owner manual steps:** none (no runtime change; merge just adds the tool).
- **⚑ Self-initiated:** no — owner-directed ("create a simulation to find…").
- **↪ Next:** adopt the chosen layout in `role_menu_builder.py` (guarded by the existing row-cap test);
  the Q-0089 builder-press instrumentation → data-driven weights; the deferred `ReactionRolesPanel`
  re-render fix + the `self.message.edit` static guard.

# Session — 2026-06-24 · Card-engine consistency guard (Rule 5)

> **Status:** `in-progress` — born-red card; flips to `complete` as the final step.

**Run type:** `routine · dispatch`. **Branch:** `claude/card-engine-guard`.
**Trigger:** continuation of this dispatch fire — second slice. The first slice (PR #1396) shipped
the card-engine **H2** renderer migration and surfaced its own Q-0089 idea: *institutionalize the
dedup as a CI guard so a renderer can't re-grow the triplication.* Building that idea now
(idea→build is open, Q-0172).

## What I'm about to do

Add **Rule 5** (`card_engine_helper_duplication`) to `scripts/check_consistency.py`: an image-render
module under `utils/` (one importing Pillow or `card_render`) that re-declares a private
`_fonts`/`_fit`/`_mix`/`_initials`/`_initials_disc` — the exact helpers the shared engine provides —
is flagged. `card_render.py` itself is exempt; warn-first (Q-0105). It runs clean on the post-#1396
tree (0 findings, verified), so it codifies the just-shipped dedup as a standing invariant — the same
friction→guard reflex behind #1280 / #1297 / BUG-0017.

Also folds in a **docs de-stale**: the vision doc's `mining_render` "remaining H2" note, corrected with
the 2026-06-24 finding that `mining_render` uses *no fonts* + a specialized rarity palette, so rebasing
it is a **visual redesign for the owner**, not a clean dedup.

⚑ **Self-initiated:** yes — building slice-1's own Q-0089 idea with no dispatch/owner ask (Q-0172).

## What changed

Tooling + tests + one docs note (no `disbot/` runtime change):

- **`scripts/check_consistency.py`** — new **Rule 5** `card_engine_helper_duplication` (warn-first,
  `roots=("utils/",)`): flags an image-render module (one importing Pillow or `card_render`) that
  defines a private `_fonts`/`_fit`/`_mix`/`_initials`/`_initials_disc` — the helpers the engine
  already provides. `card_render.py` exempt; `_imports_pillow_or_engine` guard keeps an unrelated
  `utils/` `_fit`/`_mix` math helper out of scope; allowlistable via `consistency_exceptions.yml`.
  Registered in `RULES` with a comment recording its #1396 provenance + graduation path.
- **`tests/unit/scripts/test_check_consistency.py`** — +6 tests (flags a dup; clean migrated renderer;
  non-render out-of-scope; engine exempt; allowlist suppresses; registry/scope/severity). 54 pass.
- **`docs/ideas/visual-card-engine-vision-2026-06-23.md`** — corrected the `mining_render` "remaining
  H2" note: it uses no fonts + a specialized rarity palette, so its rebase is a **visual redesign for
  the owner**, not a clean dedup; and noted the dedup is now CI-guarded by this rule.

**Verification:** Rule 5 runs **clean on the post-#1396 tree** (0 findings; `--graduation` shows it
warn-only, `findings=0`); `check_consistency --mode strict` exits 0; `check_quality.py --check-only`
(CI scope) green; the full mirror confirmed green before flip. The bare-`ruff` "104 errors" seen mid-run
were default-ruleset `S101` asserts in the test file + `COM812` that CI's scope/config excludes — the
canonical `check_quality` is the authority and is green.

## 💡 Session idea (Q-0089)

**A `--graduation`-driven nudge in the dispatch close-out: surface consistency rules that are
`ELIGIBLE` (clean across N sessions) so an empty-fire run graduates one warn→error instead of letting
proven rules sit warn-only forever.** This session *added* a warn-only rule; the symmetric value is a
cheap standing task that *graduates* the ones that have earned it (the soak is the only gate left for
`back_button`-class rules). A one-line `check_consistency.py --graduation --eligible-only` in the
session-close skill would make "which guard is ready to bite?" a single hop. Dedup-grepped
`docs/ideas/` — the `--graduation` tracker exists (#1060) but auto-graduation nudging isn't captured.

## ⟲ Previous-session review (Q-0102)

Reviewing **slice 1 of this same fire (#1396)**: it shipped a clean, well-verified migration *and*
booked its follow-through as a Q-0089 idea rather than letting it evaporate — which is exactly why this
slice existed to build. The one thing slice 1 got *right* that's worth naming: it **declined** the
riskier H2 remainder (`mining_render`) instead of forcing a second slice to hit "2–3 slices", then this
slice investigated `mining_render` concretely and *proved* the deferral correct (no fonts + specialized
palette → visual redesign, not dedup). That's the completion-bias and the safety-brake resolving the
right way — ship the contained guard, route the redesign to the owner. **System note:** the pattern
"slice N generates the idea, slice N+1 builds it, within one fire" is the self-improvement loop working
at sub-session granularity — worth keeping as an explicit dispatch habit (build your own surfaced idea
when it's contained and the budget's there).

## 📤 Run report footer

- **Run type:** `routine · dispatch`
- **PR:** #1397 (born-red → flipped complete; auto-merge armed, merges on green CI).
- **⚑ Self-initiated:** the `card_engine_helper_duplication` consistency rule — built slice-1's own
  Q-0089 idea with no dispatch/owner ask (Q-0172). Warn-first, contained, reversible, tested.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none.
- **Bug-book:** no entries fixed/opened this run.

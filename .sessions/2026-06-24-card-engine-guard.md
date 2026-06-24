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

# 2026-06-24 — Provider `card_theme` conformance guard

> **Status:** `complete` — the invariant test runs clean over all 10 providers; full CI mirror green
> (12289 passed, 48 skipped; black/isort/ruff/mypy clean).

> **Run type:** `routine · dispatch`

**Branch:** `claude/card-theme-conformance-guard`. **Trigger:** continuation of this dispatch fire —
second slice. The first slice (PR #1401) brought `!rank` onto the card engine and surfaced its own
Q-0089 idea: *a skin typo in a `RankProvider.card_theme` renders the wrong (default) skin silently.*
Building that guard now (idea→build is open, Q-0172). Independent of #1401 — touches only
`rank_providers` + `card_render.THEMES`, both already on main (themes shipped #1399, registry #1349).

## What I'm about to do

Add a one-shot invariant test `tests/unit/invariants/test_provider_card_theme_registered.py`:
every `RankProvider.card_theme` must be a registered key in `utils.card_render.THEMES`. Today
`get_theme` falls back to the default skin on an unknown key with **no error** — so `"abyss "` /
`"emberr"` would quietly render midnight instead of the intended skin, a silent visual bug with no
red signal. The guard makes a skin typo a failing test (the friction→guard reflex: #1280 / #1297 /
BUG-0017).

⚑ **Self-initiated:** yes — building slice-1's own Q-0089 idea, no dispatch/owner ask (Q-0172).
Tests-only, no runtime change, fully reversible.

CI mirror green before flipping to `complete`.

## What shipped (PR #1403)

`tests/unit/invariants/test_provider_card_theme_registered.py` — parametrized over every registered
`RankProvider`; asserts each `card_theme` is a key in `card_render.THEMES`, plus a meta-test pinning
that a bogus key is genuinely absent (so the assertion is real, not vacuous). A skin typo is now a
red build, not a silent default-skin render. Tests-only; no runtime change.

## 📤 Run report footer

- **Run type:** `routine · dispatch`
- **PR:** #1403 (provider `card_theme` conformance guard) — slice 2 of this dispatch fire (slice 1 =
  #1401, `!rank` image card). Full session enders (the Q-0089 new idea, the Q-0102 previous-session
  review, the Q-0104 doc audit) are in the slice-1 card `2026-06-24-rank-card-image.md`; this slice
  builds *that* card's Q-0089 idea.
- **⚑ Self-initiated:** yes — built slice-1's own captured Q-0089 idea (Q-0172). Tests-only, reversible.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **Bug-book:** no new bugs; none fixed.

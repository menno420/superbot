# 2026-06-24 — Provider `card_theme` conformance guard

> **Status:** `in-progress`

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

## What shipped

_(filled at close)_

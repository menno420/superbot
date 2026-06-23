# 2026-06-23 — Render-structure ("golden") tests for the card engine

> **Status:** `in-progress` — born-red card (Q-0133). Flip to `complete` as the final step.
> Owner-directed (chat: "continue from where you left off" → the highest-value captured follow-up
> idea, #1 golden-image card tests, from `session-followups-visual-ai-setup-2026-06-23.md`).
> PR auto-merges on green (Q-0123).

## Arc

The card engine (#1349) and its renderers were only asserted on "returns PNG bytes / doesn't crash"
— a layout regression (panel shift, bar overflow, theme colour swap) passed silently. The idea
backlog flagged golden-image tests as the highest-value follow-up, "load-bearing at engine roadmap
H2" (when the existing renderers migrate onto `CardCanvas`). This ships that protection.

**Design decision:** committing reference PNGs is fragile (font/Pillow versions, anti-aliasing). The
robust form samples **solid-fill regions** at coordinates away from text and asserts the pixel
equals the theme's declared colour — environment-independent, but still catches a moved panel /
swapped colour / shifted layout. Same goal, durable delivery.

## Plan (this PR)

- `tests/unit/utils/test_card_render_structure.py` — 10 tests: `CardCanvas` primitives (bg per
  theme · header band · panel fill · progress-bar fill-vs-track split · clamp to full/empty) and the
  profile hero card (fixed 900×400 · header/accent/background pixels · progress-bar position ·
  every theme paints its palette · no-progress has no bar).
- Groom idea #1 → ✅ implemented in `docs/ideas/session-followups-visual-ai-setup-2026-06-23.md`
  (with the "as built" note on the robust form).

## Status

In progress — born-red. Close-out written as the final step before flipping to `complete`.

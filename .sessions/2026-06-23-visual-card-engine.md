# 2026-06-23 — Themeable card-render engine + profile card (out-visual Dank Memer, PR 1)

> **Status:** `in-progress` — born-red card (Q-0133). Flip to `complete` as the final step.
> Owner-directed (chat task: "find Dank Memer's commands/visuals, plan how to out-visual them";
> owner picked *vision doc + themeable card-engine + profile card* via AskUserQuestion).
> PR auto-merges on green (Q-0123).

## Arc

The owner shared a Dank Memer fishing season-card screenshot and asked: enumerate DM's
commands/functions, dissect its **visual** approach, and plan how our bot can **beat** it
visually. Two research agents ran (DM feature/visual report; our visual-layer audit). Finding:
DM's moat is **server-rendered PNG/GIF cards, not embeds** ("image is the screen, buttons are the
controls"), skinned per season from **one templated engine**. Our bot already has the *pipeline*
(Pillow, graceful `bytes | None` fallback, 6 renderers, a manifest sprite system, 65+ persistent
views) but every renderer **re-declares its own `_fonts()` + palette** (`welcome_render`,
`character_render`, `image_builders`) — there is no shared, *themeable* engine, and almost
everything still ships as plain embeds.

Owner picked: capture the strategy as a **vision doc**, and build the **themeable card engine +
a polished profile card** as the foundation PR.

## Plan (this PR)

- `disbot/utils/card_render.py` — the themeable engine: a `Theme` value object + named `THEMES`
  registry (so a new skin is config, not code), cached font loader, and pure-ish draw primitives
  (panel, rounded panel, progress bar, initials disc, header band, footer, text-fit/truncate).
  Lazy-PIL, `bytes | None` discipline.
- `disbot/utils/profile_render.py` — `render_profile_card(...)` on the engine: a real hero card
  (avatar disc + name/level, stat panels, XP progress bar, themed frame).
- Wire into `views/profile/profile_view.py` — attach the rendered card as the embed's hero image
  with graceful fallback to today's text embed (image-as-screen + fallback).
- Dedupe: migrate `welcome_render` + `ux_patterns/image_builders` font loading onto the engine
  (behaviour-identical) so the engine is the one seam, not a fourth copy.
- Tests for the engine + profile render; `docs/ideas/` vision doc + README index entry.

## Status

In progress — born-red. Close-out (Shipped / Verification / session enders) written as the final
step before flipping to `complete`.

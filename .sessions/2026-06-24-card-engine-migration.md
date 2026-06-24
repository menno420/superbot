# Session — 2026-06-24 · Visual card-engine migration (H2)

> **Status:** `in-progress` — born-red card; flips to `complete` as the final step.

**Run type:** `routine · dispatch`. **Branch:** `claude/funny-franklin-cm5vdw`.
**Trigger:** scheduled dispatch fire, **no work order** → advance the next S1 plan slice. The S1
queue lists the **visual card-engine migration (§3.6 — rank/profile/leaderboard onto `card_render`,
still plain embeds)** as a remaining polish-tail item, and the
[card-engine vision](../ideas/visual-card-engine-vision-2026-06-23.md) **H2** is exactly "migrate
existing renderers onto the engine … so all cards share one look and one code path."

## What I'm about to do

The engine (`utils/card_render.py`, `CardCanvas` + `THEMES`) shipped in #1349 (H1) and its own
docstring names the renderers that still re-declare their own palette + font loader: `welcome_render`,
`ux_patterns.image_builders`, `role_menu_render`. Rebase those three onto `CardCanvas` so the
triplicated dark-blurple palette, the duplicated `_fit` (×3) / `_fonts` (×2) / `_mix` / `_initials*`
helpers collapse to the one engine code path (the exact Dank-Memer "one templated engine" property).

Plan (one cohesive low-risk pure-`utils/` PR):
1. Add a pure `mix(a, b, t)` RGB-blend helper to `card_render` (engine home for the gradient math
   `role_menu_render` needs) + export it.
2. Rebase `welcome_render.render_welcome_card` onto `CardCanvas`/theme `midnight` (drop `_BG…`,
   `_initials_disc`, `_initials`, `_fit`, `_fonts`).
3. Rebase `image_builders.render_leaderboard_image` + `render_event_poster` onto `CardCanvas`.
4. Rebase `role_menu_render.render_role_menu_card` onto `CardCanvas` + `mix` (drop its private
   palette/`_fonts`/`_fit`/`_mix`); per-call `accent` stays an override.
5. Repoint the two `test_fit_truncates_to_width` tests (welcome + role_menu) that reach private
   `_fonts`/`_fit` onto the engine, add a `mix` test, keep every public-behaviour test green.

Contract preserved throughout: lazy PIL, `bytes | None` graceful fallback, same output format
(welcome/leaderboard/poster = JPEG; role-menu = PNG), no-network, identical signatures (so the
UX-lab views + welcome service + role-menu callers are untouched).

⚑ **Self-initiated:** yes — promoted the listed card-engine H2 polish item to a build with no
dispatch/owner ask (Q-0172 idea→build is open; flagged here for owner review).

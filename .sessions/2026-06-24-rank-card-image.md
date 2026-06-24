# 2026-06-24 — Rank card as a themed image (card-engine H3, first feature card)

> **Status:** `in-progress`

> **Run type:** `routine · dispatch`

**Branch:** `claude/funny-franklin-n8lnux`. **Trigger:** scheduled dispatch fire, **no work order**
→ advance the next S1 plan slice. The S1 queue lists the visual card-engine **H3** *embed-feature →
image-card move (rank/profile)* as the remaining card-engine tail; `/myprofile` already renders an
image (H1), the leaderboard ships an image card (H2), so the flagship single-user **`!rank`** XP card
is the obvious next "image-as-screen" feature.

## What I'm about to do

Render `!rank` (the XP/coins rank card) as a designed image on the shared card engine, with a clean
embed fallback — the exact vision grammar: *the image is the screen; the stat-toggle dropdown is the
control; each toggle re-renders the card.*

Plan (one cohesive low-risk PR):
1. New pure `utils/rank_render.py` → `render_rank_card(*, display_name, subtitle, stats, progress,
   theme, footer)` — a header band (initials disc + name/subtitle) + a 3-column stat-panel **grid**
   (up to 6 panels, so the "both" card's XP-rank/level/total-XP/messages/coin-rank/coins all show) +
   the level progress bar. Pure `utils/` on `CardCanvas`; `bytes | None` graceful fallback.
2. `services/xp_helpers.py`: a `RankCardData` value object + `build_rank_card_data(member, guild,
   stat)` so the rank stats are fetched **once**; `_build_rank_embed` consumes it (byte-identical
   embed output); `build_rank_response(...) -> (Embed, File | None)` returns the embed + optional
   image card (sets `attachment://rank.png`, embed-only when Pillow is unavailable).
3. Wire it: `xp_cog.rank` sends the card with the file; `_RankSelect.callback` re-renders the image
   and replaces the attachment on each stat toggle (the "re-render on interaction" grammar).
4. Tests: the renderer (theme/grid/fallback), the single-fetch data builder, the embed parity, and
   the toggle re-render.

⚑ **Self-initiated:** yes — advances the card-engine vision's H3 with no dispatch/owner ask
(idea→build is open, Q-0172). Contained, reversible, test-covered, additive (embed fallback intact).

CI mirror green + arch strict before flipping to `complete`.

## What shipped

_(filled at close)_

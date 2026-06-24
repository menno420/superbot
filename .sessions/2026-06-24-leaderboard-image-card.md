# 2026-06-24 — Leaderboard image card: ship the H2 card-engine tail as a real feature

> **Status:** `in-progress` — born-red gate holds the merge until this card flips to `complete`.

> **Run type:** `routine · dispatch`

## What I'm about to do

No work order this fire → take the next real plan slice. S1 ▶ remaining (visual card-engine H2 tail):
the renderer-dedup half is shipped, and the explicit remaining turn-key item is **shipping the
leaderboard card as a real feature** — wiring `utils/ux_patterns/image_builders.render_leaderboard_image`
into `leaderboard_cog` as an optional image attachment with embed fallback. (`mining_render` is
explicitly *not* a clean rebase — owner visual decision — so it's out of scope.)

Plan:
1. Extend `services.rank_providers.RankEntry` with optional `name` / `score` / `value_text` so a
   provider can expose structured rows for the image card (defaults `None` → fully backward-compatible;
   embeds keep using `label`).
2. Populate the new fields in every provider (each already computes the name + a numeric primary stat).
3. Generalize `render_leaderboard_image` to accept a `title` + per-row value text (keep the UX-lab
   sample-data default so the gallery preview + existing test stay green).
4. Wire the cog: when the top rows carry numeric scores, attach the rendered card (embed
   `set_image(attachment://…)`); when Pillow is unavailable or scores are missing, post the embed
   unchanged. Pure graceful-fallback, same discipline as the welcome card.
5. Tests for the new fields, the titled renderer, and the cog attach/fallback paths.

Also cleaned a stale claim file (`claude-card-engine-guard.md` — its PR #1397 is already merged HEAD).

CI mirror green + arch strict before flipping this card to `complete`.

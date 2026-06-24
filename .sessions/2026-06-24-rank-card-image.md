# 2026-06-24 — Rank card as a themed image (card-engine H3, first feature card)

> **Status:** `complete` — `!rank` (XP/coins **and** every category) now renders a themed image card;
> full CI mirror green (12296 passed, 48 skipped; black/isort/ruff/mypy clean) + arch 0.

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

## What shipped (PR #1401)

The flagship single-user `!rank` card is now a themed image on the shared card engine — `/myprofile`
(H1) and the leaderboard (H2) already render images, this brings `!rank` onto the same path.

- **`utils/rank_render.py`** (new, pure) — `render_rank_card(...)`: header band (initials disc +
  name/subtitle) + a 3-column stat-panel **grid** (up to 6 panels, so the "both" view shows
  XP-rank / level / total-XP / messages / coin-rank / coins) + the level progress bar, all on
  `CardCanvas`. `bytes | None` graceful fallback. The sibling of `profile_render`.
- **`services/xp_helpers.py`** — a frozen `RankCardData` value object + `build_rank_card_data()`
  (single DB+registry fetch), `_build_rank_embed` refactored to consume it (embed output unchanged),
  and `build_rank_response() -> (embed, File | None)` that builds both faces from the one fetch and
  points the embed image at `attachment://rank.png` when the card renders.
- **`cogs/xp_cog.py`** — `!rank` (XP/coins) sends the card; **`!rank <category>`** (mining /
  deathmatch / crafting / creatures / …) now also renders an image **on the provider's own
  `card_theme`** (abyss / ember / verdant / …) — the same per-category skinning the leaderboard uses;
  unranked / Pillow-less → the plain embed.
- **`views/xp/rank_view.py`** — the stat-toggle dropdown re-renders the image and swaps the
  attachment on each switch (the "image is the screen, the control re-runs the renderer" grammar).
- **Tests** — `tests/unit/utils/test_rank_render.py` (render/grid/theme/fallback),
  `tests/unit/services/test_xp_helpers_rank.py` (single-fetch, embed parity, fallback),
  `tests/unit/cogs/test_xp_cog_rank_provider.py` (themed provider card + empty-state/Pillow fallback).

**Deliberately out of scope (clean boundary):** the `!xpmenu` **hub panel** (`_XpHubView`) stays
embed-only — it's an admin control panel with a different `build_embed()` shape; threading an
attachment through `send_panel`/`edit_message` there is a separate follow-up. `_build_rank_embed`
is kept intact for it (and `main_panel`).

## Handoff / next

The card-engine **H3** thread continues: (1) the **`!xpmenu` hub panel** + other showpiece embeds
onto image cards (the rank/profile *hub* surfaces); (2) the genuine **season/world skin packs** the
vision's H3 names (a fishing/collection season card). Both are turn-key on the now-proven
`render_rank_card` / `render_profile_card` + `THEMES` pattern. Remaining H2 is only the `mining_render`
rebase (an owner *visual* decision — it uses no fonts + a specialized rarity palette).

## 💡 Session idea

**A `card_theme` provider-conformance test.** Each `RankProvider.card_theme` is a free string resolved
by `card_render.get_theme` with a silent default-on-unknown fallback — so a typo (`"abyss "` /
`"emberr"`) would *silently* render the wrong (default) skin with no error, exactly the class the
`dead-binding self-heal` and tool-pin guards exist to catch elsewhere. A one-line invariant test
(`test_every_provider_card_theme_is_registered`) asserting every provider's `card_theme` is a key in
`card_render.THEMES` would make a skin typo a red test instead of a quiet visual bug. Cheap, high-signal,
fits the friction→guard reflex (#1280 / #1297 / BUG-0017). Worth having — not built this run (kept the
PR to the feature); flagged for the next dispatch.

## ⟲ Previous-session review

The previous run (`2026-06-24-leaderboard-card-themes`, PR #1399) did the per-category leaderboard
themes well — it correctly *dogfooded* the multi-theme registry (`RankProvider.card_theme`), which is
exactly what made **this** session's provider rank cards a two-line change (the themes were already
declared). One thing it could have done better: it shipped `card_theme` as a plain string with no guard
that the value is a registered theme — the silent-fallback footgun my Session idea above proposes
closing. **System improvement surfaced:** the card-engine now has *three* consumers
(`profile_render`, leaderboard `image_builders`, `rank_render`) each re-composing the same
header-band + initials-disc + panel-grid layout. The `card_engine_helper_duplication` consistency rule
(Rule 5, #1396) guards the *helper* layer (`_fonts`/`_fit`/…) but not the *composition* layer — if a
fourth card re-types the header-band geometry, nothing flags it. Worth considering a shared
`hero_header(canvas, name, subtitle, theme)` composition primitive on `CardCanvas` before the H3 hub
cards add a fourth re-implementation.

## 📤 Run report footer

- **Run type:** `routine · dispatch`
- **PR:** #1401 (card-engine H3 — `!rank` as a themed image)
- **⚑ Self-initiated:** yes — advanced the card-engine vision's H3 with no dispatch/owner ask
  (idea→build is open, Q-0172). Contained, reversible, test-covered, additive (embed fallback intact).
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none (a merge auto-deploys; no data/seed step — pure rendering, no schema
  change)
- **Bug-book:** no new bugs; none fixed this run.
- **Doc audit:** S1-bot.md + the card-engine vision doc de-staled to reflect H3 underway; claim file
  added at open and removed at close; ledger unaffected (PR will be reconciled by the next pass).

# Vision: out-visual Dank Memer with a themeable card engine

> **Status:** `ideas` (north-star) — but **the foundation is now built** (this PR): the themeable
> card engine (`utils/card_render.py`) + the first feature card (`utils/profile_render.py`, wired
> into `/myprofile`). The rest of this doc is the *strategy + roadmap*, not approval. Binding
> contracts and owner decisions win over anything here.

**Captured:** 2026-06-23 (owner-directed: the maintainer shared a Dank Memer fishing season-card
screenshot and asked us to enumerate DM's commands/functions, dissect its *visual* approach, and
plan how to **beat** it visually). **Owning area:** the bot's presentation layer (image cards) +
the agent-workflow value of having one templated render engine.

## The finding (why this matters)

Dank Memer is ~100 slash commands of economy game — but its **competitive moat is not the
commands, it's the visuals**. The flagship cards (fishing "Fishstanbul" season cards, profile
cards, pet/hunt cards) are **server-rendered PNG/GIF images uploaded as Discord attachments, not
embeds**. Discord embeds physically cannot draw custom fonts, framed art, or progress bars, so DM
doesn't use them for showpieces. The grammar is:

> **The image is the screen; native Discord buttons / select-menus / pagination are the controls.**
> Each click re-runs the renderer with new state and edits the message with a fresh image.

And crucially: **every fishing season is a re-skin of one templated card engine** — a new season
is an *art drop* (frame, palette, motifs swapped by config), not an engineering project. That
templating is their efficiency secret. Their legacy meme pipeline (`imgen`, open-source) confirms
the topology: a **separate image service** (Python Flask + Pillow + Wand/ImageMagick + moviepy)
behind a proxy. The modern game-card renderer is closed-source (inferred Skia-backed Node canvas).

Full research (commands by category + visual dissection + sources) was produced by two research
agents this session; the actionable distillation is this doc.

## Where we already stand (audit)

Good news — we are closer than expected. We already have the **pipeline**, just not the **engine**:

- Pillow is pinned; **6 working renderers** (mining inventory/stat cards, character paper-doll
  compositor, welcome card, BTD6 CT hex map) all follow a disciplined `bytes | None` graceful
  fallback so a broken render never takes a panel down.
- A **manifest-driven sprite system** (`disbot/assets/gear/` + `manifest.json`) — a hot-swappable
  art pipeline where the owner's real art replaces placeholders file-for-file.
- A deep **component layer**: `BaseView/HubView/PersistentView`, 65+ persistent panels, paginated
  selects, modals, buttons across 50+ cogs. The "controls" half of the grammar is already strong.

The gaps were: (1) **no shared, themeable engine** — `welcome_render`, `character_render`, and
`ux_patterns/image_builders` each re-declared their own `_fonts()` + palette (the exact
duplication DM avoids); (2) almost everything still ships as **plain text embeds**; (3) **no real
art assets** (emoji + procedural tier colours stand in); (4) **no animation**.

## Strategy — match, then exceed

We do **not** copy DM's Node/Skia stack. We already have Pillow working with a fallback discipline
they'd envy. The four moves:

1. **One themeable card-template engine** (not per-feature renderers). A `Theme` value object +
   named registry so a new world/season skin is config. ← **built this PR.**
2. **Real art set + custom fonts.** This is the maintainer's domain (he designs/visualizes); the
   pipeline absorbs it file-for-file. Biggest visual jump per unit effort.
3. **Convert showpiece features to "image-as-screen"** — render state into the PNG, keep buttons
   as controls, re-render on interaction. Profile/economy and fishing/mining cards first.
4. **Out-polish where DM is weak: animation + per-user themes.** Animated cards (APNG/WebP/GIF
   frame sequences) and user-selectable themes are the differentiator — and the lowest-friction
   way to monetize **cosmetics, not power** (custom backgrounds, embed colours, premium skins),
   exactly DM's model.

## Roadmap horizons

- **H1 — Engine + first card (this PR).** `utils/card_render.py` (Theme + `THEMES` registry +
  `CardCanvas` primitives: themed text/fit, panels, progress bars, initials disc, header band,
  PNG/JPEG export) and `utils/profile_render.py` (the profile hero card) wired into `/myprofile`
  with graceful fallback. Dedupes the triplicated font loader onto the engine.
- **H2 — Migrate existing renderers onto the engine.** Re-base `mining_render` /
  `welcome_render` / the UX-lab leaderboard + event-poster prototypes on `CardCanvas` so all cards
  share one look and one code path; ship the leaderboard card as a real feature.
  **🟡 Partially shipped (2026-06-24, dispatch run):** `welcome_render`, the UX-lab
  `render_leaderboard_image` / `render_event_poster`, **and** `role_menu_render` are now rebased onto
  `CardCanvas` (the triplicated dark-blurple palette + the duplicated `_fit`/`_fonts`/`_mix`/`_initials*`
  helpers collapsed onto one engine path; a pure `card_render.mix()` blend helper added for gradients).
  **The leaderboard card is now a real feature (2026-06-24, dispatch run):** `render_leaderboard_image`
  gained a `title` + per-row `value_texts`, `RankEntry` exposes a structured `(name, score, value_text)`
  projection populated by every provider, and `leaderboard_cog` attaches the rendered card to the board
  (embed `set_image(attachment://…)`) with a clean embed-only fallback when Pillow is unavailable, the
  board is empty, or a category hasn't opted in. **Each category also renders in its own skin**
  (`RankProvider.card_theme`: combat/forge → `ember`, nature → `verdant`, underground → `abyss`,
  economy → `midnight`) — the first real consumer of the multi-theme registry, dogfooding "a new look =
  a few RGB tuples". **Remaining H2 work:** only `mining_render`.
  **Note on `mining_render` (2026-06-24 finding):** it is **not** a clean dedup rebase — it
  uses **no fonts at all** (every `draw.text` uses Pillow's default bitmap font, with hardcoded
  `8 * len(text)` width math) and a deliberately *specialized* rarity palette (`_KIND_COLOR`), so
  moving it onto `CardCanvas` would *change the card's look* (loaded DejaVu fonts, new metrics) and
  require re-tuning the layout — a **visual redesign decision for the owner**, not a mechanical rebase.
  The dedup invariant is now CI-guarded by the `card_engine_helper_duplication` consistency rule (PR
  after #1396) so no renderer can re-grow the triplication.
- **H3 — Skinnable feature cards.** A fishing/collection **season card** (the FOOTONCLASH analogue)
  and a cross-game **world identity card** on themed skin packs; "new season = new `Theme` + asset
  pack", no layout code.
  **🟢 Started (2026-06-24, dispatch run):** the flagship single-user **`!rank`** card now renders as
  a themed image (`utils/card_render.py` engine → `utils/profile_render.py` for `/myprofile` (H1) and
  the new `utils/rank_render.py` for `!rank`) — a header band + a 3-column stat-panel **grid** (up to
  six panels, so the "both" view shows XP-rank/level/total-XP/messages/coin-rank/coins) + the level
  progress bar. The `_RankView` stat-toggle re-renders the card and swaps the attachment on each
  switch — the literal *"image is the screen; the dropdown is the control; each click re-runs the
  renderer"* grammar. `services.xp_helpers.build_rank_response` fetches the rank data **once** (a
  `RankCardData` value object) and builds both the embed and the image from it, with a clean
  embed-only fallback when Pillow is unavailable. **Remaining H3:** the rank/profile **hub panels**
  (`!xpmenu`) + the genuine season/world skin packs.
  **🟢 Readability + real-avatar polish (2026-07-01, owner-directed — Arcane/MEE6 screenshot compare):**
  the first pass that judged the *shipped* cards against the incumbents (`!rank`, `!leaderboard`) and
  closed the visible gaps. Engine: `CardCanvas.avatar_disc` (composite a real, circular-cropped avatar
  from fetched bytes — the caller's one network seam is `services.xp_helpers.fetch_avatar_png`; graceful
  fall-back to `initials_disc`) + `card_render.image_safe` (strip the emoji the bundled DejaVu font draws
  as a tofu □ box, applied at the `CardCanvas.text` seam so *no* card can tofu again — the 🏆/🪙 titles
  and values in the screenshots). Rank card: the live avatar replaces the "ME" initials, and the level
  bar gained a visible track + right-aligned `%` readout (was a near-invisible dot). Leaderboard:
  **outlier-safe bar scaling** (`_bar_fraction` — a runaway #1 no longer squashes the field into
  invisible stubs), a **reserved right value column** (the #1 value no longer clips off-canvas),
  **podium colours** for the top three, and `_clean_name` so a departed member's raw `<@id>` never bakes
  into the image. **Next obvious adopter:** `/myprofile` (`utils.profile_render`) still uses the "ME"
  disc — the `avatar_disc` primitive is now ready for it.
- **H4 — Real art + fonts.** Owner art pack lands file-for-file; brand fonts named per theme.
  (When a colour-emoji font lands here, gate `card_render.image_safe` on glyph coverage so intentional
  emoji can render instead of being stripped.)
- **H5 — Animation + per-user themes (the exceed move).** Frame-sequence animated cards and a
  cosmetic theme picker (premium-gated), the visual differentiator over DM.

## What this is NOT

Not approval for H2–H5, not a commitment to a specific art style (the maintainer owns art
direction), and not a rewrite of the component layer (it's already strong). It is the captured
strategy + the foundation that makes every later horizon a small, contained PR.

## Related

- `utils/card_render.py` · `utils/profile_render.py` (built this PR) · `.sessions/2026-06-23-visual-card-engine.md`
- Existing renderers it generalizes: `utils/mining_render.py`, `utils/welcome_render.py`,
  `utils/character_render.py`, `utils/ux_patterns/image_builders.py`
- `docs/ideas/superbot-vision-2026-06-10.md` (product vision) · `docs/architecture.md` (layering:
  the engine is pure `utils/`, no Discord/services/cogs imports)

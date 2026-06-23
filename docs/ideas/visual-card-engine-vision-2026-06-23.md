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
- **H3 — Skinnable feature cards.** A fishing/collection **season card** (the FOOTONCLASH analogue)
  and a cross-game **world identity card** on themed skin packs; "new season = new `Theme` + asset
  pack", no layout code.
- **H4 — Real art + fonts.** Owner art pack lands file-for-file; brand fonts named per theme.
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

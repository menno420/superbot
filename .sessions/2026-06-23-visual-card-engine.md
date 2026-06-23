# 2026-06-23 — Themeable card-render engine + profile card (out-visual Dank Memer, PR 1)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Owner-directed (chat task: "find Dank Memer's commands/visuals, plan how to out-visual them";
> owner picked *vision doc + themeable card-engine + profile card* via AskUserQuestion).
> PR #1349 → auto-merges on green (Q-0123).

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

## Shipped (PR #1349)

- **`utils/card_render.py`** (new) — the themeable engine. `Theme` (frozen palette + font
  candidates) + a named `THEMES` registry (`midnight`/`ember`/`verdant`/`abyss`) so a new skin is
  config, not code; `get_theme` resolves with a safe default (unknown name never raises).
  `CardCanvas` wraps a lazy-PIL surface with the primitives every card needs — themed `text` with
  width-fit truncation, `panel`, `progress_bar` (clamped, cap-guarded), `initials_disc`,
  `header_band`, PNG/JPEG export. `new_canvas()` is the single lazy-PIL gate → `None` when Pillow
  is absent. `dejavu_fonts()` + `initials()` are the de-duplicated shared helpers.
- **`utils/profile_render.py`** (new) — `render_profile_card(...)`: a 900×400 hero card (initials
  disc + name/subtitle, up to 4 stat panels, an optional engagement progress bar, themed frame).
  Pure presentation inputs → `bytes | None`, no Discord/DB/network.
- **`views/profile/profile_view.py`** — `_gather_profile()` now builds the embed **and** an
  engagement `ProfileSummary` in one DB pass (`_subsystem_section` returns its participation state);
  `build_profile_embed` keeps its embed-only signature (tests/callers unchanged); new
  `build_profile_card()` returns `(embed, discord.File | None)` with the card as the embed's hero
  image and a graceful embed-only fallback. `ProfileHomeView.refresh` re-renders the card.
- **`views/base.py`** — `send_panel` gained an optional `file=` kwarg (backward-compatible across
  its 145 importers; omitted = byte-identical).
- **`cogs/utility_cog.py`** — `!myprofile` + `/myprofile` now render the hero card (file attached;
  fallback when render unavailable).
- **Dedup** — `welcome_render._fonts` and `ux_patterns/image_builders._fonts` now delegate to
  `card_render.dejavu_fonts` (was triplicated). The engine is the one seam, not a fourth copy.
- **Vision doc** — `docs/ideas/visual-card-engine-vision-2026-06-23.md` (DM-vs-us finding +
  strategy + H1–H5 roadmap) + README index entry.
- **Tests** — `tests/unit/utils/test_card_render.py` (15) + `test_profile_render.py` (11): pure
  helpers, per-theme renders, fraction clamp, overlong/symbolic names, Pillow-absent → `None`.

## Verification

- `python3.10 scripts/check_quality.py --full` → **11986 passed**, 47 skipped, 2 xfailed; lint
  green after fixing two ruff nits (`S112` noqa on the font-fallback loop; `D209` docstring).
- `check_architecture --mode strict` → **0 errors** (49 pre-existing warnings; none from new files).
- `mypy` clean on the three core modules. Ledger (`--strict`) + `check_docs --strict` both green.
- Rendered all four themes to PNG and sent the owner samples (the skinnability proof).

## Session enders

- **♻ Grooming (Q-0015):** captured + advanced one idea down its lifecycle — the new
  `visual-card-engine-vision` idea, promoted *idea → partly-built (H1 shipped)* in the same
  session with the as-built note (H2–H5 remain live).
- **💡 Session idea (Q-0089):** *Golden-image snapshot tests for cards.* Card renderers are only
  asserted on "returns PNG bytes / doesn't crash" — a layout regression (a panel shifting, a bar
  overflowing) passes silently. A small golden harness (hash or pixel-diff a rendered card against
  a committed reference per theme, tolerance for font-AA) would catch visual regressions the byte
  check can't, and becomes load-bearing as H2 migrates the existing renderers onto the engine.
  Contained, dev-only (Pillow already present). Dedup-checked `docs/ideas/` — not yet captured.
- **⟲ Previous-session review (Q-0102):** the prior session (`fishing-bait-crafting`, #1338) was
  clean — closed the catch→craft→bait loop with good test depth and an honest "process note"
  documenting the bare-`black tests/` trap it hit. *Did well:* the self-flagged trap is exactly the
  guidebook-grows-itself behavior the workflow wants. *Workflow improvement it surfaces:* that trap
  recurs across sessions (CLAUDE.md §"Match CI" warns about it explicitly), yet agents keep
  re-discovering it — a guard (`check_quality.py` could refuse / warn when invoked with an explicit
  broad path arg that includes `tests/`, since CI never formats `tests/`) would convert a
  repeated-by-hand lesson into an enforced rail. Captured as a candidate, not built (out of this
  PR's scope).
- **📋 Doc audit (Q-0104):** ledger + `check_docs` strict green; the vision doc is reachable from
  the ideas README; no chat-only conclusions left undocumented (the DM research distillation lives
  in the vision doc).

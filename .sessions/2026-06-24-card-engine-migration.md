# Session — 2026-06-24 · Visual card-engine migration (H2)

> **Status:** `complete` — three image renderers rebased onto the shared card engine; full CI mirror
> green (12256 passed, 48 skipped; black/isort/ruff/mypy clean) + arch 0 errors.

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

## What changed

Pure `utils/` refactor (no `services`/`core`/`cogs`/DB change; identical public signatures, so the
welcome service + UX-lab views + role-menu view callers are untouched):

- **`utils/card_render.py`** — added a pure `mix(a, b, t)` RGB-blend helper (engine home for gradient
  math, `[0,1]`-clamped) + exported it. The engine the renderers now share.
- **`utils/welcome_render.py`** — rebased `render_welcome_card` onto `CardCanvas` (theme `midnight`).
  Dropped its private palette, `_initials_disc`, `_initials`, `_fit`, `_fonts`. Now uses
  `canvas.initials_disc` / `canvas.text(max_width=…)` / `canvas.to_jpeg`.
- **`utils/ux_patterns/image_builders.py`** — rebased `render_leaderboard_image` + `render_event_poster`
  onto `CardCanvas`. Dropped its private palette + `_fonts`.
- **`utils/role_menu_render.py`** — rebased `render_role_menu_card` (+ `_draw_background`) onto
  `CardCanvas` + `mix`. Dropped its private palette, `_fonts`, `_fit`, `_mix`. The four preset styles
  (banner/gradient/minimal/spotlight) + the per-call `accent` override are preserved.
- **Tests** — repointed the two `test_fit_truncates_to_width` tests (welcome + role_menu) that reached
  private `_fonts`/`_fit` onto the engine's `CardCanvas.fit`; added `test_mix_blends_and_clamps` to
  `test_card_render.py`. All public-behaviour render tests (format markers, overflow, no-Pillow → None)
  unchanged and green.

**Net dedup:** 3 copies of the dark-blurple palette → 1 theme; `_fit` ×3 → `CardCanvas.fit`; `_fonts`
×2 → the engine; `_mix` → `card_render.mix`; `_initials*` → `card_render.initials` + `initials_disc`.
Exactly the Dank-Memer "one templated engine" property (#1352 north-star).

**Contract preserved:** lazy PIL, `bytes | None` graceful fallback, same output format (welcome /
leaderboard / poster = JPEG; role-menu = PNG), no-network.

**Verification:** `python3.10 scripts/check_quality.py --full` → green (12256 passed, 48 skipped, 2
xfailed; black/isort/ruff/mypy clean — one COM812/black whitespace fix on `role_menu_render`); arch
`--mode strict` → 0 errors. Targeted: `test_card_render` / `test_welcome_render` /
`test_role_menu_render` / `test_ux_lab_*` all pass.

## Handoff — ▶ Next action (remaining H2)

The renderer-dedup half of card-engine **H2** is partially shipped. Clearly-scoped remainder for a
later dispatch (both contained, both `utils/`):
1. **`mining_render` rebase** — deferred this run: it uses a pure-spec `build_card_spec` pattern + a
   distinct (non-blurple) palette and per-kind row colours, so the rebase is larger/riskier than the
   three flat renderers done here. Keep `CardSpec` pure; migrate only the pixel-push onto `CardCanvas`.
2. **Ship the leaderboard card as a real feature** — wire `render_leaderboard_image` into
   `leaderboard_cog` as an optional image attachment with the embed fallback (H2's "ship as a feature"
   tail). This is light feature-wiring + likely a display toggle — confirm the surface with the owner.
Then H3 (embed features → image cards) is the next horizon. State home: the
[vision doc](../ideas/visual-card-engine-vision-2026-06-23.md) H2/H3.

## 💡 Session idea (Q-0089)

**A `check_consistency` rule (or AST test) banning a re-declared card palette / font loader outside
`utils/card_render.py`.** This PR removed the *third* private copy of the dark-blurple palette + the
*third* `_fit`; the engine exists precisely so there's one home, but nothing stops the next renderer
from pasting its own `_BG = (24, 25, 31)` / `_fonts()` again (the same drift class the consistency
linter already guards for views/select-truncation). A tiny rule — *a module under `utils/*render*` or
`ux_patterns` that defines an RGB-tuple palette constant or a private `_fonts`/`_fit` and is **not**
`card_render` is a finding* — would make the dedup a standing invariant, not a per-session cleanup.
Dedup-grepped `docs/ideas/` — not already captured.

## ⟲ Previous-session review (Q-0102)

The previous dispatch chain (the 2026-06-23 burst: new economy/game subsystems #1328–#1344, fishing
polish #1329–#1356, the card engine **H1** #1349) executed prolifically and, notably, **#1349 left H2/H3
as a clean, well-documented vision doc with named targets** — which is exactly why this session could
pick up H2 cold in minutes. That's the workflow working as designed. **One miss it surfaced:** #1349
shipped the engine and immediately had `welcome_render`/`image_builders` *delegate* their `_fonts` to it
(`dejavu_fonts`) but stopped there — leaving the palette + `_fit` + the raw-PIL draw paths duplicated. A
half-migration reads as "done" in a grep for `_fonts` but isn't; the cheap follow-through (this PR) sat
unbooked for a day. **System improvement:** the Q-0089 idea above (a linter rule banning re-declared
palettes/font-loaders outside the engine) would have *flagged* that half-migration the moment #1349
merged, converting "remembered polish" into an enforced invariant — the same friction→guard reflex the
repo already institutionalized for CI strands (#1280) and select-truncation (BUG-0017).

## 📤 Run report footer

- **Run type:** `routine · dispatch`
- **PR:** #1396 (born-red → flipped complete; auto-merge armed, merges on green CI).
- **⚑ Self-initiated:** card-engine **H2** renderer-dedup (welcome / UX-lab leaderboard+poster /
  role-menu rebased onto `CardCanvas` + the `mix` engine helper). Promoted a listed S1 polish-tail item
  → build with no dispatch/owner ask (Q-0172). Contained, reversible, pure `utils/`, fully tested.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (pure refactor; a merge auto-deploys, no data step).
- **Bug-book:** no entries fixed/opened this run.

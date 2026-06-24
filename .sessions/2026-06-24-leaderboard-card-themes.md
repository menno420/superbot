# 2026-06-24 — Per-category leaderboard card themes (card-engine H2 polish)

> **Status:** `complete`

> **Run type:** `routine · dispatch`

## What I'm about to do

Second slice this fire (first was PR #1398 — the leaderboard image card, merged). Promote the
Q-0089 idea I captured in #1398: the board always renders the `midnight` skin, but the engine
already ships 4 themes (`midnight`/`ember`/`verdant`/`abyss`). Let each provider name a card
theme so boards are visually distinct at a glance — the engine's whole reason to exist ("a new
look = a few RGB tuples, not layout code").

Plan:
1. `RankProvider.card_theme: str = "midnight"` (safe default; `get_theme` already falls back on an
   unknown key so a bad value never breaks a render).
2. Per-provider overrides by category flavour (combat/forge → `ember`, nature → `verdant`,
   underground → `abyss`, economy/progression → `midnight`).
3. `render_leaderboard_image` gains a `theme` param (defaults to the module skin so the UX-lab
   preview is unchanged); `leaderboard_cog._render_card` forwards `provider.card_theme`.
4. Tests: every provider declares a registered theme; the cog forwards it; the renderer honours it.

⚑ Self-initiated: yes — promotes my own captured idea (not dispatched, adjacent polish to a
roadmap item). Contained, reversible, test-covered.

CI mirror green + arch strict before flipping to `complete`.

## What shipped (PR #1399)

- `RankProvider.card_theme: str = "midnight"`; overrides mining→`abyss`, creatures→`verdant`,
  crafting+deathmatch→`ember`; economy/progression keep `midnight`. `get_theme` falls back on an
  unknown key, so an override can never break a render.
- `render_leaderboard_image` gained a `theme` param (defaults to the wing skin → UX-lab preview
  byte-unchanged); `leaderboard_cog._render_card` forwards `provider.card_theme`.
- Tests: every provider declares a *registered* theme + the set is differentiated; the cog forwards
  the theme; the renderer renders in all four skins. Full mirror green; arch 0; mypy clean.

## Handoff — ▶ next

Card-engine **H2** is now done except `mining_render` (owner-gated visual redesign — do not
auto-rebase). The next horizon is **H3** (embed-feature → image-card for `!rank` /
`views/xp/rank_view.py` and `/myprofile`), which the vision doc says needs its own plan. Other
S1-startable lanes unchanged: Project Moon runtime PR 1, botsite React-SPA PR 2, fishing open-world
Phase 2 (shore-cap rebalance is an owner balance call).

## 💡 Session idea (Q-0089)

**A per-user cosmetic card theme.** The engine + the per-category theming now prove the registry works;
the natural H5 "exceed move" is letting a *member* pick their own card skin (stored on their profile,
applied to their profile/rank cards). It's the lowest-friction cosmetic-not-power surface the vision
calls out (and the mission doc permits — cosmetics never gate features). A small slice would add a
`user_card_theme` setting + a picker; the render path already takes a theme name. → relates
`card_render.THEMES` · `profile_render` · `free-for-everyone-mission`.

## ⟲ Previous-session review (Q-0102)

The previous slice (PR #1398, this same fire) was solid and shipped clean, and it did the right thing by
*capturing* this theming idea in its Q-0089 line rather than scope-creeping it into the feature PR — which
is exactly why this slice was a clean, unambiguous pickup. The one thing both slices share as a watch-item:
the card title forwards `display_title` verbatim, so leading emoji render as missing-glyph boxes under
DejaVu — still cosmetic and pre-existing, but now it shows on *four* skins; a later art pass should strip
or font-swap the emoji. **System improvement:** the two-slices-one-fire pattern worked well here because
slice 1 merged before slice 2 opened (no shared-file conflict) — worth noting in the dispatch runbook that
when two slices touch the same files, sequencing them through merge (not parallel branches) is the safe
default.

## 📋 Doc audit (Q-0104)

Durable home updated: the vision doc's H2 bullet records the per-category theming. `check_docs --strict`
✓, arch 0, mypy clean. No new owner decision → no router entry. No merged-PR ledger edit owed (PR not yet
merged). Reconciliation marker untouched.

## 📤 Run report

- **Run type:** `routine · dispatch`
- **What shipped (this fire, 2 slices):** PR #1398 (leaderboard image card, merged) + PR #1399
  (per-category card themes).
- **⚑ Self-initiated:** PR #1399 — promotes my own Q-0089 idea (cosmetic polish adjacent to a roadmap
  item, not dispatched). Contained, reversible, fully test-covered. (PR #1398 was the next item on the
  approved roadmap — not self-initiated.)
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (merge auto-deploys; no data file changed).

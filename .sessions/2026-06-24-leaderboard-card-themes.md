# 2026-06-24 — Per-category leaderboard card themes (card-engine H2 polish)

> **Status:** `in-progress` — born-red gate holds the merge until this card flips to `complete`.

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

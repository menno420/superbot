# 2026-06-24 — Leaderboard image card: ship the H2 card-engine tail as a real feature

> **Status:** `complete`

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

## What shipped (PR #1398)

- **`services.rank_providers.RankEntry`** gained optional `name` / `score` / `value_text` (defaults
  `None` → embeds, which render from `label`, are byte-unchanged). All **10** providers populate the
  projection.
- **`render_leaderboard_image`** now takes a `title` + per-row `value_texts` and guards empty rows
  (`None`); the UX-lab sample-data default is preserved (gallery preview + its test stay green).
- **`leaderboard_cog`** fetches the rows once (`_build_provider_response`) and attaches the rendered
  card via embed `set_image(attachment://leaderboard.jpg)` when the top rows are structured; otherwise
  posts the embed unchanged (Pillow-less host, empty board, card-less category). The category select
  passes `attachments=[card]` / `[]` so a switch replaces or clears the prior image. The old
  `_build_provider_embed(provider, guild)` is kept (now delegating) so the existing tests are unbroken.
- Removed the stale claim `claude-card-engine-guard.md` (its PR #1397 is merged HEAD — drift-on-sight).
- Tests: `tests/unit/cogs/test_leaderboard_card.py` (attach/fallback + titled/empty renderer) +
  a structured-projection pin in `test_rank_providers.py`. Full mirror green (12271 passed); arch 0.

## Handoff — ▶ next

The card-engine **H2** tail is now essentially done. Remaining:
- **`mining_render` rebase** — explicitly **owner-gated** (a visual redesign decision, not a mechanical
  dedup: it uses no loaded fonts + a specialized rarity palette). Do **not** auto-rebase it.
- **H3 (embed-feature → image-card)** — `!rank` (`views/xp/rank_view.py`) and `/myprofile` rank/profile
  are still plain embeds; converting them to image cards on `CardCanvas` is the next horizon (its own
  plan, per the vision doc — "not approval for H2–H5").
- Optional polish on this feature: the card title forwards `provider.display_title` verbatim, so its
  leading emoji renders as a missing-glyph box under DejaVu (same as the pre-existing sample title) —
  strip/replace the emoji if a later art pass wants clean glyphs.

## 💡 Session idea (Q-0089)

**A `theme` knob on the leaderboard card keyed to the category.** The engine already ships 4 skins
(`midnight`/`ember`/`verdant`/`abyss`); the board always renders `midnight`. Letting each provider name
a theme (combat categories → `ember`, nature/creatures → `verdant`, economy → `midnight`) would make the
boards visually distinct at a glance for ~one line per provider and zero new art — a cheap step toward
the H3/H5 "per-world identity" the vision wants, and it dogfoods the Theme-registry's whole reason to
exist (a new look = a few RGB tuples, not layout code). → relates `card_render.THEMES` ·
`rank_providers` · the visual-card-engine vision.

## ⟲ Previous-session review (Q-0102)

The previous run (#1397 — card-engine consistency guard) did exactly the right *durable* thing: it
shipped a `check_consistency.py` rule that **prevents the triplication from re-growing** before moving on,
so the dedup it protects can't quietly rot — a strong "ship the guard with the cleanup" instinct. Its one
gap (the thing that left this run a job to do) was stopping at the *guard* and not taking the small,
turn-key *feature* the same vision doc flagged one bullet away (the leaderboard card) — understandable
scope discipline, but the feature was contained enough to fold in. **System improvement:** the vision
doc's H-horizon bullets carry an inline `🟡 partially shipped / remaining:` status that made this run's
pickup unambiguous — that "status-tagged horizon bullet" convention is worth making standard in every
`docs/ideas/*-vision-*.md` roadmap so a dispatch run can resolve "what's the next turn-key slice here?"
in one read (it worked perfectly here).

## 📋 Doc audit (Q-0104)

Durable homes updated: the vision doc's H2 bullet + `current-state/S1-bot.md` ▶-next both record the
card as shipped. `check_current_state_ledger --strict` ✓ (no merged-PR ledger edit owed — PR not yet
merged; the listed newer PRs are benign newest-merge lag), `check_docs --strict` ✓, arch 0, mypy clean.
No new owner decision → no router entry owed. Reconciliation marker untouched.

## 📤 Run report

- **Run type:** `routine · dispatch`
- **What shipped:** PR #1398 — leaderboard top-N image card as a real feature (card-engine H2 tail) +
  stale-claim cleanup.
- **⚑ Self-initiated:** none — the slice is the next item on an existing approved roadmap (vision doc
  H2 "remaining"), not an invented feature. (The Q-0089 idea above is captured, not built.)
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none (a merge auto-deploys; no data step — no `*.json` changed).

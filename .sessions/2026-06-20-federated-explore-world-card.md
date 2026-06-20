# 2026-06-20 — Federated Explore-hub PR 3: cross-game world card

> **Status:** `complete` — read-only/additive slice → self-merge on green (Q-0113).

> **Run type:** routine · dispatch

## What I did
Scheduled dispatch fire, no work order → advanced the next plan slice. The live ▶ Next action
named federated Explore-hub PR 2/PR 3. Investigation reframed the work:
- **The "global vs per-game XP" data layer already exists** (verified against source): `game_xp`
  is already keyed per `game` (`db.add_game_xp(user, guild, game, …)`, with
  `GAME_MINING`/`GAME_CRAFTING`/`GAME_FISHING`), and the **level is already global** (`db.get_total_xp`
  = `SUM(xp)`). So PR 2's *visibility* half is effectively the read surface — i.e. PR 3.
- **PR 2's remaining work is the heavy, design-laden part** — a per-game *skill-tree* discriminator
  needing a **`player_skills` PK migration on a live progression table** + a new per-game-tree /
  global-trickle *earning model* (a progression-balance decision for the owner-designer). The prior
  run rightly deferred its live-schema part; I left it owner/runtime-gated and **built PR 3** instead
  (explicitly ungated, read-only, Q-0080 stranger-grade).

## What shipped
- **`disbot/services/game_xp_service.py`** — `world_identity(guild_id, user_id)` read aggregator
  (`WorldIdentity` + `GameStanding`: global level from the summed total, each game's own level from
  its own XP, deterministic highest-XP-first ordering) + `GAME_LABELS`/`game_display()` display
  metadata. Pure read over the existing `game_xp` table — no schema, no write, no event.
- **`disbot/views/explore/world_card.py`** (NEW) — `build_world_card_embed(user, guild_id)`: global
  world level + progress bar + per-game standings, honest empty-state and DM (no-guild) handling.
- **`disbot/views/explore/world_hub.py`** — a `🪪 World Card` button on `ExploreWorldHubView`
  (in-place edit keeping the hub view, mirroring PR 1's openers).
- **`disbot/cogs/games_cog.py`** — `!worldcard`/`!mystats` command (the typed read surface, like
  fishing's `!fishlog`).
- Tests: `tests/unit/views/test_world_card.py` (NEW — render / empty / DM / **read-only AST guard**),
  `world_identity` cases in `test_game_xp_service.py`, the hub-button test in `test_explore_world_hub.py`.
- Regenerated the committed generated artifacts (`dashboard.json` / `botsite/data/site.json`) — the new
  `!worldcard` command changed the catalogue (the BUG-0018 class; the hard freshness test caught it).
- Docs: plan §-banner reframed (PR 3 done + the PR 2 data-layer correction); current-state ▶ Next action.

## Verification
- `python3.10 scripts/check_quality.py --full` → **All checks passed ✓** (10940 passed, 44 skipped).
- `python3.10 scripts/check_architecture.py --mode strict` → exit 0 (only pre-existing `[known]` warns;
  none in the new files).

## Handoff
**Explore-hub PR 2** (per-game skill-tree discriminator + the earning-model decision) is the only
remaining spine slice — it's **owner/runtime-gated**: it needs a `player_skills` PK migration on a
live progression table and a progression-balance design call. Do it in a runtime-verified session with
owner design input, NOT an autonomous empty fire. After PR 2 the spine stops (Q-0182 gates gear/survival/
biome layers). Reusable seam now in place: `game_xp_service.world_identity()` + `GAME_LABELS`.

Next ungated empty-fire lanes (current-state ▶ Next action): consistency-linter rule-1 AI-nav redesign
(needs a runtime live-walk, `needs-hermes-review`), procedures→skills Batch 1 (edits CLAUDE.md — read-only
to an autonomous run), or the small stdlib guards.

## 💡 Session idea
**A "world card on `/myprofile`" cross-link.** The new `world_identity()` read aggregator is a clean
cross-game identity seam, and the existing `views/profile/` card is schema-driven per-subsystem. A
genuinely small future slice: surface a compact "world level + top game" line on the profile card (or a
button bridging the two), so a player's federated standing shows up in the one place they already check
their per-server identity. Distinct from PR 3 (which lives in the Explore spine); this is the *profile*
side of the same identity. Worth having because it unifies the two identity surfaces without duplicating
the read logic (both call `world_identity`).

## ⟲ Previous-session review
The previous run (`world-registry-parity-invariant`) did the right *kind* of thing — it hardened the
merged PR 1 seam with a parity invariant + folio docs rather than barrelling into PR 2 unverified, and
it was honest that PR 2 needed runtime verification. **What it missed:** it stated PR 2 "needs a
`player_skills` game-discriminator migration" as if that were the *whole* of PR 2, without noticing that
the **`game_xp` per-game/global split already exists in source** — which means PR 3 (the read surface)
was buildable *now* on existing data and didn't need PR 2 first. A 10-minute source read of
`game_xp_service` + `db/games/game_xp.py` would have surfaced that and unblocked a full slice that run.
**System improvement it surfaces:** when a plan says "add a discriminator if missing — verify the live
schema first," the verify-first step should be treated as *mandatory reconnaissance before deferring*,
not just before building — a deferral based on an unverified schema assumption can hide a shippable
slice. (Folded into how I approached this run: verify the data layer before accepting the plan's framing.)

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** Federated Explore-hub PR 3 — the read-only cross-game world card
  (`world_identity()` + `views/explore/world_card.py` + `🪪 World Card` button + `!worldcard`/`!mystats`),
  tests, regenerated generated artifacts, and the plan/current-state reframe of PR 2 to owner-gated.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** none — PR 3 is an on-plan slice of the owner-promoted Explore-hub spine
  (dispatched lane), not an invented feature.

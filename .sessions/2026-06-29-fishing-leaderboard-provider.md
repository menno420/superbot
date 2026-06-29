# 2026-06-29 — Fishing leaderboard provider (S1 deepening win)

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.
> Full CI mirror green (**12982 passed**, arch 0); committed `site.json`/`data.js`/`dashboard.json`
> regenerated for the new `fishlb` alias (BUG-0018/0022 class); PR #1540.

**Branch:** `claude/funny-franklin-hyw1yp` (re-synced to `main` @ #1539, `2dea872c`).

## What I'm about to do (intentions)

Empty-fire scheduled dispatch — no work order. Advancing the S1 ▶ Next startable, offline
**deepening win** flagged twice in `current-state/S1-bot.md`: *"Leaderboards is missing providers for
several existing games — notably Fishing... each is one `RankProvider` class + a `utils/db` top-N read
(the headline turn-key deepening win now)."*

Fishing already has the data (`db.top_fishers(guild, known_species)` → `(user_id, caught, species)`,
used by `!fishtop`) and its own `!trophies` board, but **no provider in the unified `!leaderboard` hub /
select menu** — so it's absent from the central leaderboard surface every other game appears in. This
slice closes that gap, mirroring `CreaturesProvider` exactly.

Planned:
1. `utils/fishing/fish.py` — add `fish_names()` catalog helper (mirror `creature_names()`); export it.
   Refactor the two duplicated `[s.name for s in SPECIES]` call sites in `fishing_cog.py` onto it.
2. `services/rank_providers.py` — new `FishingProvider` (top by total caught, member_rank on/off board),
   registered + `fishlb`/`fishingleaderboard`/`anglerlb` aliases.
3. `cogs/leaderboard_cog.py` — add `fishlb` to the command alias list + the help category list.
4. `utils/card_render.py` — add a `tidal` ocean skin (the engine's "a new look = a few RGB tuples"
   property); `FishingProvider.card_theme = "tidal"` for at-a-glance visual distinction.
5. Tests: extend the canonical-category set, add FishingProvider coverage + a `fish_names()` test.

Offline, self-mergeable on green (contained, reversible, test-covered). After this, if budget remains:
the Economy `give`/`pay` deepening win or another game provider (Blackjack/Word-Chain/Farm).

## What shipped

1. **`services/rank_providers.py`** — `FishingProvider` (top anglers by total fish caught via
   `db.top_fishers`, `member_rank` on/off board reading a deep `limit=500` list), registered in
   `_PROVIDERS` between Creatures and GameXp, + `fishlb`/`fishingleaderboard`/`anglerlb` aliases, +
   `__all__`. Mirrors `CreaturesProvider` (same `top_collectors`-shaped `(uid, caught, species)` rows).
2. **`cogs/leaderboard_cog.py`** — `fishlb` added to the `!leaderboard` command alias list + the help
   usage string (the select-menu option auto-generates from the registry, no further edit).
3. **`utils/fishing/fish.py`** (+ `__init__.py` export) — new `fish_names()` catalog helper mirroring
   `creature_names()`; the two duplicated `[s.name for s in SPECIES]` call sites in `fishing_cog.py`
   (`!fishtop`, `!trophies`) refactored onto it.
4. **`utils/card_render.py`** — new `tidal` ocean skin (teal/aqua); `FishingProvider.card_theme="tidal"`
   for at-a-glance board distinction (the engine's "a new look = a few RGB tuples" property).
5. **Tests** — extended `test_registry_exposes_canonical_categories` to include `fishing`; +5
   `FishingProvider` tests (top render, 10-cap, member_rank on/off, deep-list `limit=500`, alias
   resolution) + a `fish_names()` catalog test. The existing card-theme invariant covers `tidal`.
6. **Generated artifacts** — regenerated `botsite/data/site.json`, `botsite/site/data.js`,
   `dashboard/data/dashboard.json` for the new `fishlb` alias (the BUG-0018/0022 static-scan regen).

## Context delta

- **Discovered:** the fishing data + the unified-leaderboard registry already existed and aligned
  perfectly — `top_fishers` returns the exact `(uid, caught, species)` shape `CreaturesProvider` uses, so
  this was a near-mechanical mirror. The only friction was the expected `site.json` regen (the new alias
  is statically scanned into the command surface).
- **Decisions made alone:** added a *new* `tidal` theme rather than reusing `abyss` (mining's) — a clean,
  on-philosophy, reversible touch that gives the board its own look; added `fish_names()` rather than
  inlining `[s.name for s in SPECIES]` a third time (a small dedup the helper-policy favours). Both
  reversible.
- **🛠 Friction → guard:** none new — the regen drift was already a known, guarded class (the
  `test_committed_site_json_matches_a_fresh_build` test *is* the guard; it caught my stale artifact).

## 💡 Session idea (Q-0089)

**A registry-completeness guard for leaderboard providers** — the completion assessment found
Fishing/Blackjack/Casino/Word-Chain/Farm all missing from the unified `!leaderboard` hub one at a time,
by hand. A cheap test could assert that every game subsystem declaring a top-N `utils/db` read (or every
`product_subsystem` cog tagged `game`) has a corresponding `RankProvider` registered — turning "which
games are missing a board?" from a manual per-assessment sweep into a CI readout (warn-first, with an
allowlist for games that genuinely have no ranking). Captured as a candidate; not built this run (would
need a reliable "is this a rankable game?" signal to avoid false positives).

## ⟲ Previous-session review (Q-0102)

The previous run (#1505, EffectiveStats knob-coverage guard) did the right thing leaving BUG-0026 OPEN
for an owner wire-or-remove call — but BUG-0026 was in fact *already wired* (#1512, Q-0208) before this
run, so the "OPEN, owner-gated" framing it left in the bug book lagged the resolution by a few PRs. The
lesson for the system: a guard that allowlists a known gap (`_UNWIRED_STATS`) should ideally fail when
the gap is *closed elsewhere* (it does — the honesty check), but the **bug-book entry** has no such
self-correction, so a fixed-elsewhere bug can sit stale. Improvement surfaced: the bug-book root-fix
backlog checker (`check_bug_book_rootfix_backlog.py`) could also flag entries whose `_UNWIRED`/allowlist
guard has since gone green — but that's a cross-reference few bugs need; noting it, not building it.

## 📤 Run report

- **Did:** shipped the Fishing leaderboard provider (S1 completion-first deepening win) into the unified
  `!leaderboard` hub. · **Outcome:** shipped
- **Shipped:** #1540 — feat(leaderboard): Fishing leaderboard provider (self-merge on green, Q-0113)
- **Run type:** `routine · dispatch`
- **Class:** feature/deepening (contained, reversible, test-covered) — an existing-feature completion win,
  not an invented new unit
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (a merge auto-deploys; no data step — no migration/data file changed)
- **⚑ Self-initiated:** **yes** — empty-fire scheduled dispatch with no work order; I picked the S1 ▶
  Next flagged deepening win (idea→ship open, Q-0172). Grounded in `current-state/S1-bot.md`'s own
  finding, not invented.
- **↪ Next:** the remaining leaderboard-provider deepening wins (**Blackjack/Casino/Word-Chain/Farm** —
  this Fishing provider is the worked example, BUT each needs a `utils/db` top-N read built first: none
  of those four has one yet, unlike fishing's pre-existing `top_fishers`); or Economy `give`/`pay`; or
  continue the feature-completion server-fn assessments (Counters · Spotlight · Channels · …).

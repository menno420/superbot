# 2026-07-01 — Fishing Boathouse (third coral structure — energy-regen payoff)

> **Status:** `complete`

**Run type:** `routine · dispatch`

## What I'm about to do

Empty-fire scheduled dispatch → advance S1's standing offline ▶ Next: **a third fishing structure**
(the explicit "next offline successor" after Tide Pool #1598 / Dock #1599 / Structures sub-hub #1603).

**The Boathouse** 🛖 — a coral + **wood** structure whose payoff is **faster fishing energy regen**, a
genuinely distinct third axis:

| Structure | Payoff | Axis |
|---|---|---|
| 🪸 Tide Pool | rarity-pull (rarer fish) | *quality* |
| ⚓ Dock | bite-speed (faster bites) | *throughput per cast* |
| 🛖 **Boathouse** | energy regen (shorter "line rest" wait) | *endurance / less waiting* |

Reuses the proven pattern end-to-end: a registry entry in `utils/mining/structures.py`
(`_BOATHOUSE_BUILD_LADDER` + `boathouse_regen_mult`), the audited `mining_workflow.build_structure`
seam (no new mutation path), the generic `mining_structures` table (**no migration**), a
`views/fishing/boathouse.py` panel + a Boathouse button in the 🏗 Structures sub-hub, and a `!boathouse`
command. **Additive-safety:** unbuilt (level 0) ⇒ `boathouse_regen_mult == 1.0` ⇒ the effective regen
interval is exactly `REGEN_SECONDS` ⇒ **byte-identical** energy behaviour.

**BUG-0030 lesson applied:** command name `!boathouse` (aliases `moorings`, `boat`) grep-verified
collision-free bot-wide (`sail`/`setsail` are the only nearby tokens; `boat`/`boathouse`/`moor` all clean).

## What shipped (PR #1605)

The **Boathouse** 🛖 — the third fishing structure (energy-regen payoff), byte-identical energy when
unbuilt:

- **`disbot/utils/mining/structures.py`** — `BOATHOUSE` registry entry (`_BOATHOUSE_BUILD_LADDER`
  coral+wood 3/20/2k → 6/40/5k, `_BOATHOUSE_LEVEL_NAMES`), `boathouse_regen_mult(level)` (1.0 −
  0.12·level, ≤1.0 lower=faster), `MAX_BOATHOUSE_LEVEL`, `__all__` exports.
- **`disbot/utils/fishing/energy.py`** — `regen_seconds_for(regen_mult)` = `max(1, round(base·mult))`
  (never ÷0; unbuilt ⇒ exactly `REGEN_SECONDS`).
- **`disbot/services/fishing_workflow.py`** — `begin_cast` reads structures **once** at the top (was a
  duplicate read lower down) and threads the Boathouse-adjusted `regen_seconds` into `settle` /
  `seconds_until` / `spend`; `get_energy` does the same so the gauge matches.
- **`disbot/views/fishing/boathouse.py`** (new, twin of `dock.py`) + a 🛖 button/field/footer in
  `structures_hub.py` + `!boathouse` (aliases `moorings`, `boat`) in `fishing_cog.py`; `views/fishing`
  package exports.
- **Tests (+18):** `test_mining_structures.py` (registry/ladder/mult/no-forge-gate),
  `test_fishing_energy.py` (`regen_seconds_for` + faster-settle), `test_fishing_workflow.py`
  (`get_energy`/`begin_cast` regen threading + updated the two existing energy tests for the new
  structures read), `test_fishing_structures_hub.py` (Boathouse field/button/back-nav).
- **Docs/artifacts:** `docs/planning/fishing-boathouse-numbers-2026-07-01.md` (pinned numbers), S1-bot.md
  Recently-shipped + advanced ▶ Next successor, regenerated dashboard/site/data.js for `!boathouse`.

## 📤 Run report

- **Did:** shipped the third fishing structure (Boathouse — coral+wood, faster energy regen) as the
  standing S1 offline ▶ Next successor · **Outcome:** shipped (CI green, auto-merge armed).
- **Shipped:** #1605.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none (no migration, no data step; live on next auto-deploy).
- **⚑ Self-initiated:** the whole slice is the plan's explicitly-named "next offline successor" (a third
  fishing structure, the Boathouse was the suggested example) — dispatched-plan work, not unprompted;
  the *payoff choice* (energy regen over other axes) + numbers were my judgment (Q-0172).
- **↪ Next:** a *fourth* fishing structure would need a fresh lever (quality/throughput/endurance are
  taken — e.g. a coin-yield "Fish Market" or shore-cook energy refill), or the fishing open-world
  expansion Phase 2. See S1-bot.md ▶ Next successor.

## 💡 Session idea (Q-0089)

**Extract the shared energy `settle`/`spend`/`seconds_until` core into one `utils` home now that a
*structure* modifies fishing regen.** `energy.py`'s own docstring already flags the "rule of three":
mining and fishing each keep a copy of the regen math, and the Boathouse is the first thing that
*parameterizes* one of them (regen_seconds). A third energy system, or a mining structure wanting the
same treatment, would be the trigger to unify — capturing it as an idea so the duplication is retired
deliberately, not copied a third time. Genuine (the file itself predicts this), not filler.

## ⟲ Previous-session review (Q-0102)

The previous 2026-07-01 dispatch chain (Tide Pool #1598 → Dock #1599 → sub-hub #1603) built the coral
structure line cleanly and left an unusually good handoff — the ▶ Next successor named the Boathouse by
example, which is exactly why this session was near-turn-key. **But that same chain caused BUG-0030**:
the Dock run picked the command name `dock`, colliding with `!sail`'s `dock` alias → a prod boot
crash-loop. The lesson it should have applied — and which #1601 then enforced — is *grep the command
token bot-wide before naming a command*. **System improvement (applied this session, worth making
standing):** the born-red card / PR body now records the collision-grep as an explicit build step, and
#1601's boot-smoke test is the safety net. The durable habit: **every new command name gets a bot-wide
`git grep name="…"|aliases` check recorded in the PR before it's chosen** — cheap, and it closes the
exact class that took the bot offline hours earlier.

## Doc audit (Q-0104)

No owner *decision* to route (dispatched plan work under the existing structure pattern; the numbers are
a tunable-constants doc, not an ADR). S1-bot.md Recently-shipped + ▶ Next updated; the new numbers doc
is linked from S1-bot.md (reachable). `check_docs` / `check_consistency` / `check_artifacts_fresh` green
via the mirror. No prior-merge ledger drift spotted this session (recon marker #1590, latest merge
#1604 — benign newest-merge lag, next pass at #1620).

## 🛠 Friction → guard (Q-0194)

- **Friction:** I ran bare `python3.10 -m black disbot/ tests/` to auto-fix formatting and it
  reformatted **603 unrelated files** (CI *excludes* `tests/` from black/isort/ruff, and a broad run
  reformats files CI never checks) — the exact CLAUDE.md "don't hand-run bare formatters" trap. Had to
  revert 607 files by hand. **Guard (habit):** use `python3.10 scripts/check_quality.py --check-only`
  to *find* what's unclean, then format only the specific offending file(s) — never a broad
  `black <dir>`. The mirror is the one true scope; a directory-wide format is always wrong here.

## Context delta

- **Needed and well-pointed:** the ▶ Next successor line named the Boathouse and the exact pattern
  (registry + audited build_structure + panel + sub-hub button); the Dock (#1599) was a perfect
  copy-from template. Turn-key as intended.
- **Pointed to but didn't need:** the `CastStart` bonus-flag plumbing (Tide Pool/Dock use it) — the
  Boathouse payoff is regen, not per-cast, so no `CastStart`/cast_view change (smaller blast radius).
- **Decisions made alone:** energy-regen as the third axis (over max-energy or other levers), the
  numbers, and threading `regen_seconds` (vs. `max_energy`) — regen directly shortens the felt "line
  rest" wait and was the suggested payoff.

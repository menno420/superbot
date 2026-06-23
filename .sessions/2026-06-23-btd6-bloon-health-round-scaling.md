# 2026-06-23 — BTD6 late-game/freeplay bloon health scaling (round-scaled HP)

> **Status:** `complete` — owner-directed (Discord screenshot → "find it on the web"
> → "continue"). The bot answered "BAD on r100" with a flat **20,000** and asserted
> "round 100 doesn't change the BAD's base health." Wrong: a BAD first spawns on
> round 100 already at **28,000 HP**. This session adds the missing round-relative
> MOAB-class health scaling. PR #1384; auto-merge armed on green (Q-0127);
> owner-directed → merges immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## The bug (from the channel)

`@SuperBot how much health does a BAD have … And on r100?` → bot: "20,000 … round
100 keeps its 20,000 HP base." A community member (kthxbye) corrected it: *28k — 20k
base × 1.4 by r100.* kthxbye was right.

## Root cause

BTD6 applies a **runtime late-game/freeplay health ramp to MOAB-class bloons** that
is **not in the game-data dump**: round files store only composition + spawn timing,
and `BloonModel` stores only base `maxHealth`. Our `bloons.json` therefore had the
20,000 base and nothing round-relative, so the model "knew" only the base and
confidently flattened the nuance. Same shape as per-round XP/cash, already curated.

## Verified mechanic (web research, this session)

MOAB-class bloons (MOAB/BFB/ZOMG/DDT/BAD) gain **+2% of base HP per round from round
81**, piecewise-linear with step-ups at 101/151/201/252:

```
v(r) = 1.0                    r ≤ 80
v(r) = 1.0 + (r−80)·0.02      81 ≤ r ≤ 100   → v(100) = 1.40
v(r) = 1.6 + (r−101)·0.02     101 ≤ r ≤ 150
v(r) = 3.0 + (r−151)·0.02     151 ≤ r ≤ 200
v(r) = 4.5 + (r−201)·0.02     201 ≤ r ≤ 251
v(r) = 6.0 + (r−252)·0.02     r ≥ 252
```

`BAD @ r100 = 20,000 × 1.40 = 28,000` (67,200 RBE) — cross-verified by three sources
(Late Game and Freeplay / BAD wiki / topper64 "+2% health/round after round 80").
The **r ≤ 100 bracket is cross-verified**; the > 100 brackets are the wiki's
documented continuation (flagged in the data file's source note). The Fandom/Blooncyclopedia
pages 403 to fetchers (Cloudflare); the formula was pulled via WebSearch summaries + the
topper64 cross-check, not a direct page fetch.

## Shipped (PR #1384)

- **`disbot/data/btd6/bloon_scaling.json`** — the curve as curated data with a
  `scaling_source` note stating it is NOT in the dump (sibling of `round_xp.json`).
- **`btd6_data_service`** — `HealthScalingBracket`, dataset fields
  `moab_health_scaling` / `moab_health_start_round`, and
  `moab_class_health_multiplier(round)` + `bloon_health_at_round(id, round, *, fortified=)`.
- **`btd6_context_service`** — `deterministic_bloon_health_reply` floor (owns "HP of
  <bloon> at round N" so the model can't re-flatten it) + a MOAB-class grounding note
  in `_render_fixture_bloon` for conversational follow-ups ("and on r100?").
- **Tests** — `test_btd6_bloon_scaling.py` (18) pins the loader, multiplier math,
  per-bloon scaled HP (BAD 28k / fortified 56k, non-MOAB unchanged), and the reply;
  plus the floor-builder exclusivity corpus entry.
- **`btd6-gamedata-dictionary.md`** — a "Runtime-formula facts the dump does NOT
  store" section so the next agent doesn't re-investigate "where's the round HP modifier."
- Full CI mirror green (`check_quality.py --full`: 12,172 passed); arch strict clean.

## 💡 Session idea (Q-0089)

**Round-scaled RBE, not just HP.** The same ramp means a BAD's *RBE* at r100 is
**67,200**, but `rounds.json` still lists the unscaled **55,760** (and the
round-economy reply repeats it). Extend `bloon_scaling` consumption to recompute
MOAB-class RBE at a round (RBE = HP-of-this-layer + Σ children, with the multiplier
applied per MOAB-class layer) and surface it in `deterministic_round_economy_reply`
and the round grounding — so "RBE of round 100" matches the in-game 67,200. Scoped,
verifiable (same three-source anchor), and closes the other half of this bug class.
*(Dedup-checked docs/ideas/ + roadmap: no existing round-scaled-RBE entry.)*

## ⟲ Previous-session review (Q-0102)

Reviewed **2026-06-23-panel-back-nav-fix** (#1383, universal panel Help/Back nav).
**Did well:** fixed the *root cause* — leaf panels lost externally-attached nav on
`edit_in_place` redraw onto a fresh instance — with a registry-driven `attach_standard_nav`
self-attach, instead of patching each of ~8 panels (one mechanism vs. N patches; the
right altitude). **Could improve / system note:** its `_self_navigates` guard is a
**heuristic on the codebase's stable button copy** (string-matching label text) — a
later copy tweak silently breaks the guard and either double-attaches or skips nav.
A *structural* marker (a `SELF_NAVIGATES` class attribute or a mixin) would be
robust to wording changes. **Workflow improvement it surfaces:** when a guard keys on
human-facing strings, add a test that asserts the guard's verdict for each live panel
class (so a copy change that flips the verdict fails CI) — the same "executable contract
over the live tuple" discipline this repo already uses for the floor-builder exclusivity
corpus (which is exactly what caught my new builder this session).

## Doc audit (Q-0104)

`check_current_state_ledger --strict` exit 0 (24 PRs newer than marker #1352 = benign
lag, not drift, Q-0166); `check_docs --strict` passed. New mechanic has a durable home
(the data file's `scaling_source` + the gamedata-dictionary section + this log). No
owner decision to route. Ledger entry for #1384 lands via the next reconciliation pass
(no placeholder — Q-0052).

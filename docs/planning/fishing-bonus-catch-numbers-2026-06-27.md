# Fishing lucky-double-catch numbers (S1 fishing acquisition-depth, with PR #1515)

> **Status:** `reference` — the balance rationale for the lucky-double-catch bonus.
> Source of truth is the code (`utils/fishing/rewards.py` `BONUS_CATCH_CHANCE` /
> `roll_bonus_catch`); this doc records *why* the number is what it is and is pinned
> by `tests/unit/utils/test_fishing_rewards.py`.

## What this is

The named S1 `▶ Next offline successor` after the fish→rod craft path: **a small chance
a cast yields craft materials directly.** Realized as a **lucky double catch** — on a
successful reel there is a `BONUS_CATCH_CHANCE` chance the line lands a *second* copy of
the same fish, dropping extra fodder straight into the catch→bait/charm/rod craft loops
(`services/fishing_workflow.craft_bait` / `craft_charm` / `craft_rod`).

Rolled at **commit** time (`fishing_workflow.commit_catch`), only on a landed catch, via
the pure `roll_bonus_catch(rng)` — separate from the species roll so the bonus is a clean,
independently-tunable knob.

## The number

| Knob | Value | Why |
|---|---|---|
| `BONUS_CATCH_CHANCE` | **0.10** (1 in 10 casts) | Frequent enough to *feel* lucky and visibly accelerate the craft loops, rare enough that it stays a treat — not a baseline doubling of fishing output. |

## Why this is safe / not arbitrage

- **Byte-identical when it doesn't fire.** The grant is `2 if bonus else 1`; the 90% path
  is the exact pre-change behaviour. The pure test pins that `BONUS_CATCH_CHANCE` keeps it
  a treat, not the norm.
- **No dex/trophy distortion.** The bonus only bumps the *inventory* grant. The catch-log
  row (`db.record_catch`) — the dex tally and the heaviest-weight trophy record — is
  written exactly once per cast, so a double catch never logs a second species row or a
  phantom trophy.
- **Not a coin mint.** The extra fish is the same low-value common catch the player already
  reeled; it feeds the *slow* craft paths (whose recipes already cost far more fish than
  the gear is worth sold — see the rod/charm craft numbers docs). It speeds the grind
  modestly; it does not break the coin economy.
- **Energy-gated like every cast.** The bonus can only fire on a cast the player paid
  energy for, so it can't be farmed faster than normal fishing.

## Where the loop closes

`catch (!fish) → 🍀 lucky double → more craft fodder → craft (!craftbait / !craftcharm /
!craftrod) faster`. The bonus is surfaced inline on the catch result
(`views/fishing/cast_view.py` — "🍀 **Lucky double catch!**").

# 2026-06-22 — Fishing PR4: separate energy bar (pacing) + generous sell rebalance

> **Status:** `in-progress` — born-red card. Owner-directed implementation (Q-0175 fishing minigame,
> continuing after #1298/#1299/#1301/#1303). The "soft energy/cooldown" pacing decision, now built.

## Arc (what I'm about to do)

Fishing has been **unpaced** — you can cast endlessly, which is why fish sell for a deliberately-low
1–7 coins (#1289). The owner's pacing decisions (AskUserQuestion, 2026-06-22):
1. **Separate fishing energy** — fishing gets its OWN energy bar (own cap + regen), decoupled from
   mining (you can fish when mined-out and vice-versa).
2. **Generous sell values** — once paced, raise fish to ≈ `size_rank` (1–21 coins) so a trophy pays
   off and selling is worth doing.

This PR:
1. **`utils/fishing/energy.py`** — pure energy math (settle/spend/can-cast/regen/bar) + fishing
   constants (own `MAX`/`REGEN`/`CAST_COST`). Self-contained per the "separate" decision (the regen
   math mirrors `utils/mining/energy.py`; rule-of-three note to extract a shared core if a third
   energy system ever appears — not now, to keep mining untouched & this PR low-risk).
2. **Persistence** — migration `088_fishing_energy.sql` (`fishing_energy(user, guild, energy,
   energy_updated_at)`, defaults full) + `utils/db/games/fishing_energy.py` + re-export.
3. **`fishing_workflow.begin_cast`** — settle → if out of energy return a "ready in Ns" message; else
   spend energy (direct game-state write, like mining) + roll the cast. `prepare_cast` calls it.
4. **Sell rebalance** — `utils/mining/items.py` `_fish_value` → `max(1, size_rank)` (1–21).
5. **Energy surfaced** — the menu embed + the cast show the ⚡ bar; out-of-energy casts say when
   you'll be ready.
6. **Tests** — energy math, the db CRUD, begin_cast (has-energy / out-of-energy), the new sell value.

**Deferred to PR5:** the boat / deepwater venue (exclusive species, gated by a decent rod).

## Shipped

_(filled in at close)_

# 2026-06-22 — Fishing PR4: separate energy bar (pacing) + generous sell rebalance

> **Status:** `complete` — separate fishing energy + generous sell rebalance shipped & verified
> (full CI mirror green, 11,642 tests). Owner-directed. PR #1304 → auto-merges on green (Q-0191).

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

## Shipped (PR #1304)

- **`utils/fishing/energy.py`** — pure pacing math (settle/spend/can_cast/seconds_until/bar) + own
  tunables (MAX 20, CAST_COST 1, REGEN 30s = ~120/hr). Self-contained (separate bar); regen math
  mirrors mining's with a rule-of-three note (don't extract a shared core until a 3rd consumer).
- **Persistence** — migration `088_fishing_energy.sql` (`fishing_energy`, defaults to a full bar so
  every existing/new player starts full) + `utils/db/games/fishing_energy.py` + re-export.
- **`fishing_workflow.begin_cast`** — settle → out-of-energy returns a "ready in Ns" message → else
  spend 1 (direct game-state write, like mining; no audit) → roll. Energy spent only after a catch
  is rolled (a broken catalog never charges). `get_energy` for the gauge. `prepare_cast` routes
  through it, so `!fish` and the menu Cast button are both gated identically.
- **Sell rebalance** — `utils/mining/items.py` `_fish_value` → `max(1, size_rank)` (1–21, up from
  1–7); comment rewritten (pacing, not a low price, is the faucet brake now).
- **Energy surfaced** — the ⚡ gauge shows on the cast embed footer and the fishing menu; the
  out-of-energy cast message says when you'll be ready.
- **Tests** — energy math (6), energy db CRUD (3), begin_cast charged/out-of-energy/empty-catalog +
  get_energy (4), the sell-value rebalance (1); updated the prior `roll_catch`-patch + prepare_cast
  tests for the new `begin_cast` seam. Dashboard regenerated. Full CI mirror green.

## Session enders

- **💡 Session idea (Q-0089):** *Energy-aware menu Cast button.* When the player is out of energy, the
  menu's 🎣 Cast button could render **disabled with a "ready in Ns" label** (read settled energy at
  menu-open, like the Rod button's at-max disable) instead of only failing on click — a clearer,
  friendlier signal. Cheap (energy is already read for the gauge). Logged for the next fishing PR.
- **♻ Grooming (Q-0015):** advanced the fishing minigame down its lifecycle — the owner's
  "soft energy/cooldown" decision is now built, which unlocked the long-deferred fish-sell-value
  rebalance (#1289's low value was *explicitly* a placeholder "until paced"). Games folio updated;
  only the boat/deepwater slice remains.
- **⟲ Previous-session review:** PR #1303 (menu buttons) was the right fix and its session log even
  flagged the lesson ("a feature isn't done until it's reachable from the menu"). This PR benefited:
  because the menu existed, surfacing the new ⚡ gauge had an obvious home. **What this PR navigated:**
  the energy-math duplication tension — mining's `energy.py` is fully generic, so the "pure" instinct
  was to share it, but the owner's *separate-bar* decision + the risk of refactoring live mining made
  a self-contained copy the right call. **System note:** "one source of truth" (helper-policy) and
  "small low-risk PRs" can conflict; the rule-of-three (copy twice, extract on the third) is the
  honest tiebreaker — recorded in the module so a future agent extracts it deliberately, not by reflex.
- **🧾 Doc audit (Q-0104):** games folio updated; `check_docs --strict` ✓; dashboard regenerated;
  migration `088` follows the numbering contract. Ledger auto-updates on merge. Nothing left in chat.

## ⚑ Self-initiated: none — owner-directed (the planned PR4, with the pacing model + sell values
   chosen by the owner via AskUserQuestion this session).

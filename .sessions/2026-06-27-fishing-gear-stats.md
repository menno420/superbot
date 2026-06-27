# 2026-06-27 — Fishing-specific gear stats (loadout presets become a real optimisation)

> **Status:** `in-progress` — born-red card; opening the PR before the build (Q-0133/Q-0189).

> **Run type:** `routine · dispatch` — empty-fire schedule fire, no work order. Took the next real
> plan slice: the offline-tagged S1 ▶ Next item **Fishing-specific gear stats**
> ([idea](../docs/ideas/fishing-gear-stats-2026-06-27.md)), the offline successor to the gear loadout
> presets (#1499).

**Branch:** `claude/funny-franklin-iv2rzi` (off `main` @ #1503 merge, `a7c11f53`).

## What I'm about to do (intentions)

Complete the Q-0175 / V-14 "matching gear → better fishing" half. The loadout-*swap* shipped (#1499),
but a "fishing loadout" only changes *which* mining/combat gear is equipped — nothing biases fishing,
because `utils/equipment.EffectiveStats` models only mining + combat stats. So a fishing loadout is
currently cosmetic convenience, not an optimisation.

Plan (pure, sim-pinned, offline-self-mergeable — reuses the cross-game `EffectiveStats` seam, no
parallel fishing-stat store, no migration):

1. `utils/equipment.py` — add `fishing_power` + `bite_luck` to `EffectiveStats` (additive, default 0,
   so every existing stat read is byte-identical), wire `__add__`/`STAT_LABELS`/`STAT_GLYPHS`. Add a
   small **fishing-charm ladder** in the existing CHARM slot (kept off the combat SET_SLOTS so the
   duel-balance sim is untouched) to `_GEAR` + `MAX_DURABILITY` + `GEAR_SHOP` (buyable = reacquirable).
2. `utils/fishing/gear.py` (new, pure) — convert `EffectiveStats` → the two cast knobs (a bounded
   rarity-pull multiplier from `fishing_power`, a bounded faster-bite multiplier from `bite_luck`).
3. `services/fishing_workflow.begin_cast` — read equipped gear + skills → `character_stats` → fold the
   gear knobs into `effective_pull` / `effective_bite_speed` as the **4th** how-well knob
   (rod × bait × weather × **gear**). Default-preserving: no fishing gear ⇒ ×1.0 ⇒ byte-identical.
4. Surface a small cast-panel note when fishing gear is contributing; the gear panel + shop pick up the
   new items automatically (slot-grouped).
5. Sim-pin the numbers (mirror `docs/planning/gear-set-numbers-2026-06-11.md`) + tests.

## 📤 Run report

*(filled at close)*

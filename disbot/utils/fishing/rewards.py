"""Fishing catch roll — level-gated, pure (owner design Q-0175).

The catch mechanic is the owner's first-listed, deferrable v1 option — a
**deterministic roll** within the player's unlocked size band (analogous to the
``explore`` resolve seam). A future minigame is an explicitly OPEN owner question
(Q-0175) and layers on top without changing this contract.

State-in (an explicit ``random.Random`` for seed-determinism in tests),
return-out; no Discord, no DB.
"""

from __future__ import annotations

import random

from utils.fishing.fish import Catch, FishSpecies, unlocked_species


def roll_catch(fishing_level: int, rng: random.Random | None = None) -> Catch | None:
    """Roll one catch from the fish unlocked at *fishing_level*.

    Bigger fish are rarer: within the unlocked band the pick is weighted by the
    inverse of size rank, so the common small fish dominate and a freshly
    unlocked big fish is a treat — without ever being unreachable. Returns
    ``None`` only if the catalog failed to load (no fish unlocked).
    """
    pool = unlocked_species(fishing_level)
    if not pool:
        return None
    r = rng or random.Random()
    weights = [1.0 / s.size_rank for s in pool]
    species: FishSpecies = r.choices(pool, weights=weights, k=1)[0]
    return Catch(species=species)

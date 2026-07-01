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

from utils.fishing.fish import SHORE_VENUE, Catch, FishSpecies, unlocked_species
from utils.fishing.venue import DEEPWATER, normalize
from utils.fishing.weight import roll_weight


def roll_catch(
    fishing_level: int,
    rng: random.Random | None = None,
    *,
    rarity_pull: float = 1.0,
    venue: str = SHORE_VENUE,
) -> Catch | None:
    """Roll one catch from the fish unlocked at *fishing_level* in *venue*.

    Bigger fish are rarer: within the unlocked band the pick is weighted by the
    inverse of size rank, so the common small fish dominate and a freshly
    unlocked big fish is a treat — without ever being unreachable. Returns
    ``None`` only if the catalog failed to load (no fish unlocked).

    ``rarity_pull`` (≥ 1, the rod knob) flattens that size penalty toward the big
    end of the band: at 1.0 it is the base inverse-size weighting; above 1.0 the
    big fish get relatively likelier (``→ ∞`` approaches a uniform pick), so a
    better rod catches *better* fish within the same unlocked band — never new
    bands (that is the fishing-level axis).
    """
    pool = unlocked_species(fishing_level, venue)
    if not pool:
        return None
    r = rng or random.Random()
    pull = max(1.0, rarity_pull)
    weights = [1.0 / (s.size_rank ** (1.0 / pull)) for s in pool]
    species: FishSpecies = r.choices(pool, weights=weights, k=1)[0]
    return Catch(species=species, weight=roll_weight(species, r))


#: Base chance a successful reel also lands a **second** copy of the same fish — a
#: "lucky double catch" that drops extra craft fodder straight into the
#: catch→bait/charm/rod loops (``services/fishing_workflow.craft_*``). A pure
#: bonus on top of the normal catch: byte-identical economics when it doesn't
#: fire, and it never touches the dex/trophy record (that stays the single
#: heaviest-weight row). Sim-pinned in
#: ``docs/planning/fishing-bonus-catch-numbers-2026-06-27.md``.
BONUS_CATCH_CHANCE = 0.10


def roll_bonus_catch(
    rng: random.Random | None = None,
    *,
    chance: float | None = None,
) -> bool:
    """Roll the lucky-double-catch bonus — ``True`` ≈ *chance*.

    Rolled at commit time (only a *landed* catch can double), separate from the
    species roll so the bonus is a clean, independently-tunable knob. State-in
    (an explicit ``random.Random`` for seed-determinism in tests), return-out.

    *chance* defaults to :data:`BONUS_CATCH_CHANCE` (so every existing caller is
    byte-identical). A built **Fishery** structure raises it — see
    ``services.fishing_workflow.commit_catch`` — and it is clamped to ``[0, 1]`` so
    an over-large bonus can never exceed certainty.
    """
    effective = BONUS_CATCH_CHANCE if chance is None else chance
    effective = min(1.0, max(0.0, effective))
    r = rng or random.Random()
    return r.random() < effective


#: The dedicated **rare crafting material** a successful reel can also yield — a
#: "pearl".  Unlike the lucky double-catch (which drops a second *fish*), a pearl
#: is its own inventory item: it is **never** a catch-log / dex / trophy row,
#: just a tangible material stored in the shared ``mining_inventory``.  Its sole
#: sink is the pearl-only craft path for the premium **Royal Feast** bait (the one
#: bait deliberately left with no fish recipe — a pure coin sink today), so pearls
#: have a *repeatable* home: a lucky fisher can earn the top bait by fishing while
#: coins stay the fast alternative.  Byte-identical economics when no pearl drops.
#: Numbers sim-pinned in ``docs/planning/fishing-pearl-numbers-2026-06-28.md``.
PEARL_ITEM = "pearl"

#: Per-reel pearl-drop chance for the *smallest* fish (size_rank 1).
PEARL_DROP_BASE_CHANCE = 0.02
#: Additive per-size-rank bonus, so a trophy haul is markedly likelier to yield a
#: pearl than a minnow (bigger fish, better odds — the design's framing).
PEARL_DROP_PER_SIZE_RANK = 0.004
#: Hard ceiling so even the largest fish can never make pearls common.
PEARL_DROP_MAX_CHANCE = 0.15


def pearl_drop_chance(size_rank: int) -> float:
    """The pearl-drop probability for a fish of *size_rank* (clamped, bounded).

    Rises ``PEARL_DROP_PER_SIZE_RANK`` per rank above the smallest, from
    :data:`PEARL_DROP_BASE_CHANCE` up to :data:`PEARL_DROP_MAX_CHANCE`.
    """
    rank = max(1, size_rank)
    chance = PEARL_DROP_BASE_CHANCE + PEARL_DROP_PER_SIZE_RANK * (rank - 1)
    return min(chance, PEARL_DROP_MAX_CHANCE)


def roll_pearl_drop(size_rank: int, rng: random.Random | None = None) -> bool:
    """Roll a pearl drop for a landed fish of *size_rank* — ``True`` ≈ its chance.

    Rolled at commit time (only a *landed* catch can drop a pearl), separate from
    both the species roll and the bonus-catch roll so the material is a clean,
    independently-tunable knob.  State-in (an explicit ``random.Random`` for
    seed-determinism in tests), return-out.
    """
    r = rng or random.Random()
    return r.random() < pearl_drop_chance(size_rank)


#: A **second** dedicated rare crafting material — "coral" — a reel byproduct like
#: the pearl, but **deepwater-only**: coral is a reef find, so only a cast made in
#: the boat/deepwater venue (``utils.fishing.venue.DEEPWATER``) can yield it.  This
#: gives the deepwater venue (the boat, #1340) a *unique* reward the shore can't
#: earn — a reason to sail beyond the tougher minigame.  Coral's sole sink is the
#: cosmetic **curio** collection (``utils.fishing.curios``): a completionist set of
#: carvings you craft from coral, never a bait (that is the pearl's lane).  Stored
#: in the shared ``mining_inventory``; never a catch-log / dex / trophy row.
#: Byte-identical economics when no coral drops.  Numbers sim-pinned in
#: ``docs/planning/fishing-coral-numbers-2026-07-01.md``.
CORAL_ITEM = "coral"

#: Per-reel coral-drop chance in the **deepwater** venue (flat — coral is a reef
#: find, not size-scaled like the pearl).  A shore cast never drops coral.
CORAL_DROP_CHANCE = 0.06


def coral_drop_chance(venue: str) -> float:
    """The coral-drop probability for a landed catch made in *venue*.

    :data:`CORAL_DROP_CHANCE` in the deepwater venue, ``0.0`` everywhere else —
    coral is a reef find, exclusive to the boat/deepwater venue.
    """
    return CORAL_DROP_CHANCE if normalize(venue) == DEEPWATER else 0.0


def roll_coral_drop(venue: str, rng: random.Random | None = None) -> bool:
    """Roll a coral drop for a landed catch made in *venue* — ``True`` ≈ its chance.

    Rolled at commit time (only a *landed* catch can drop coral), separate from
    the species / bonus-catch / pearl rolls so the material is a clean,
    independently-tunable knob.  Always ``False`` outside the deepwater venue.
    State-in (an explicit ``random.Random`` for seed-determinism in tests),
    return-out.
    """
    chance = coral_drop_chance(venue)
    if chance <= 0.0:
        return False
    r = rng or random.Random()
    return r.random() < chance

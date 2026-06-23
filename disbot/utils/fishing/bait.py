"""Fishing bait — the optional *second* pre-cast economy knob (Q-0175 §4).

The fishing design's named follow-up layer
(``docs/planning/fishing-minigame-design-2026-06-22.md`` §4, "Bait as the second
economy knob"): bait is an **optional, coin-bought consumable** that biases the
catch toward rarer / bigger fish for a bounded number of casts. Fish became
sellable + cookable in #1289, so bait gives those coins somewhere to go *and* a
pre-cast decision ("load a lure before this trip?") sitting beside the rod ladder.

The two-knob model stays clean:

* **Fishing level** (``game_xp``) gates *what* you can catch — the size bands.
* **The rod** (:mod:`utils.fishing.rods`) is the permanent *how-well* axis.
* **Bait** is the *consumable* how-well axis with **two** knobs, each compounding
  onto the matching rod knob while you hold charges (one charge spent per cast):

  - ``rarity_pull`` (≥ 1) multiplies the rod's pull, so a loaded lure pulls the
    catch toward the big end of your unlocked band — *never* a new band (that
    stays the fishing-level axis).
  - ``bite_speed`` (≤ 1 = faster, mirroring ``rod.bite_speed``) multiplies the
    rod's bite-wait, so a loaded lure makes fish bite sooner — more casts within
    the same energy bar. Owner decision 4 (design §4) named this the clean
    second knob on the same ``CastStart``/cast-view seam the rarity knob uses.

  The starter setup still catches fine without bait (bait only improves, never
  gates), and the two knobs are *orthogonal*: the shelf has dedicated rarity
  baits, dedicated speed baits, and one premium combo that turns both.

Pure + stdlib-only (no Discord, no DB): :mod:`services.fishing_workflow` owns the
purchase write + the per-cast consume; the bait shop view reads this catalog.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bait:
    """One bait type — a stable key, presentation, its two knobs, charges, price."""

    key: str  # stable lookup key (stored in the fishing_bait row)
    name: str
    emoji: str
    rarity_pull: float  # ≥ 1 multiplier applied ON TOP of the equipped rod's pull
    charges: int  # casts one bought pack lasts
    price: int  # coin cost of one pack
    bite_speed: float = 1.0  # ≤ 1 multiplier ON TOP of the rod's bite-wait (faster)


#: The bait shelf, grouped by knob family. ``rarity_pull`` multiplies the rod's
#: own pull (so a Gold Rod at 1.45 with a Shimmer Lure at 2.0 fishes at 2.9) and
#: ``bite_speed`` multiplies the rod's bite-wait (so a Gold Rod at 0.80 with a
#: Flash Spinner at 0.60 waits 0.48× as long). Charges bound the boost so it's a
#: *consumable* sink; prices are tunable constants. The two families are kept
#: orthogonal — rarity baits leave speed neutral and vice-versa — so the pre-cast
#: choice is legible; one premium combo turns both for the top coin sink.
BAIT_CATALOG: tuple[Bait, ...] = (
    # Rarity family — bias the catch toward bigger fish (speed neutral).
    Bait("worm", "Worm Bait", "🪱", rarity_pull=1.25, charges=10, price=150),
    Bait("grub", "Glow Grub", "🐛", rarity_pull=1.50, charges=10, price=400),
    Bait("lure", "Shimmer Lure", "✨", rarity_pull=2.00, charges=10, price=1000),
    # Speed family — fish bite sooner (rarity neutral); more casts per energy bar.
    Bait(
        "minnow",
        "Live Minnow",
        "🐟",
        rarity_pull=1.00,
        charges=10,
        price=200,
        bite_speed=0.80,
    ),
    Bait(
        "spinner",
        "Flash Spinner",
        "🌀",
        rarity_pull=1.00,
        charges=10,
        price=600,
        bite_speed=0.60,
    ),
    # Combo — the premium pack: pulls hard AND bites fast (the top coin sink).
    Bait(
        "feast",
        "Royal Feast",
        "👑",
        rarity_pull=1.75,
        charges=10,
        price=1800,
        bite_speed=0.70,
    ),
)

_BY_KEY: dict[str, Bait] = {b.key: b for b in BAIT_CATALOG}

#: The stable keys, in shelf order (for selects / validation).
BAIT_KEYS: tuple[str, ...] = tuple(b.key for b in BAIT_CATALOG)


def bait_by_key(key: str | None) -> Bait | None:
    """The :class:`Bait` for *key*, or ``None`` for an unknown / empty key."""
    if not key:
        return None
    return _BY_KEY.get(key)


def effect_text(bait: Bait) -> str:
    """A short human label of a bait's knobs, e.g. ``×1.5 rarity · −35% wait``.

    Shared by the shop view (shelf / select) and the purchase message (workflow)
    so a speed bait never mislabels itself as "×1 rarity" — only the knobs it
    actually turns are shown (rarity pull above 1, bite-wait reduction below 1).
    """
    parts: list[str] = []
    if bait.rarity_pull > 1.0:
        parts.append(f"×{bait.rarity_pull:g} rarity")
    if bait.bite_speed < 1.0:
        parts.append(f"−{round((1.0 - bait.bite_speed) * 100)}% wait")
    return " · ".join(parts) or "no effect"


# ---------------------------------------------------------------------------
# Bait crafting — turn caught fish into bait, the gameplay-native second source
# ---------------------------------------------------------------------------
#
# The fishing economy loops back on itself (idea ``fishing-bait-crafting-2026-06-22``):
# the cook/campfire loop (#1289) made fish a tangible inventory item; crafting lets
# the *small, common* catches (which otherwise just sell cheap) become the lure that
# lands the trophy — ``catch → craft → bait → bigger catch``. A recipe consumes
# ``fish_count`` fish whose ``size_rank`` is ``≤ max_size_rank`` (smallest-first, so
# the player keeps their bigger fish) and yields one pack (``Bait.charges`` casts).
#
# Only the cheaper / mid baits are craftable — the premium combo ("feast") stays a
# pure coin sink, so spending coins keeps a top-end reason to exist beside fishing.


@dataclass(frozen=True)
class BaitRecipe:
    """A fish → bait recipe: consume *fish_count* small fish, yield one pack.

    Only fish whose ``size_rank`` is ``≤ max_size_rank`` count as ingredients
    (so crafting drains the low-rank catches first); the produced pack carries
    the bait's own :attr:`Bait.charges`.
    """

    bait_key: str
    fish_count: int  # number of eligible fish consumed per craft
    max_size_rank: int  # only fish with size_rank ≤ this are eligible ingredients


#: The craft shelf, keyed by bait key. Cheaper baits cost a few of the smallest
#: fish; better baits want more / larger fish. The premium combo ("feast") is
#: deliberately ABSENT — it stays a pure coin sink (the top-end spend reason).
CRAFT_RECIPES: dict[str, BaitRecipe] = {
    "worm": BaitRecipe("worm", fish_count=3, max_size_rank=3),
    "minnow": BaitRecipe("minnow", fish_count=3, max_size_rank=3),
    "grub": BaitRecipe("grub", fish_count=5, max_size_rank=6),
    "spinner": BaitRecipe("spinner", fish_count=5, max_size_rank=6),
    "lure": BaitRecipe("lure", fish_count=6, max_size_rank=9),
}

#: Craftable bait keys, in shelf order (skips any without a recipe).
CRAFTABLE_KEYS: tuple[str, ...] = tuple(
    b.key for b in BAIT_CATALOG if b.key in CRAFT_RECIPES
)


def craft_recipe(key: str | None) -> BaitRecipe | None:
    """The :class:`BaitRecipe` for *key*, or ``None`` if that bait isn't craftable."""
    if not key:
        return None
    return CRAFT_RECIPES.get(key)


def recipe_text(recipe: BaitRecipe) -> str:
    """A short human label of a recipe's cost, e.g. ``3 fish (size ≤ 3)``."""
    return f"{recipe.fish_count} fish (size ≤ {recipe.max_size_rank})"


def craftable_key_for(text: str | None) -> str | None:
    """Resolve typed *text* (a key or a bait name) to a **craftable** bait key.

    Case-insensitive; matches either the stable key (``worm``) or the display
    name (``Worm Bait``). Returns ``None`` for empty input or a bait that has no
    recipe — so ``!craftbait worm`` and ``!craftbait "worm bait"`` both work but
    a non-craftable bait (the premium combo) does not resolve.
    """
    if not text:
        return None
    needle = text.strip().lower()
    for key in CRAFTABLE_KEYS:
        bait = _BY_KEY.get(key)
        if bait is None:
            continue
        if needle in (key.lower(), bait.name.lower()):
            return key
    return None

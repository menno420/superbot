"""Exploration engine — pure, loadout-aware outcome catalog (foundation).

This module is the structured successor to the flat five-entry
``EXPLORE_OUTCOMES`` table in :mod:`cogs.mining.rewards`.  It models
exploration as *depth-banded* (a :class:`Biome`) and *loadout-aware* (the
tools a player has equipped change which outcomes are reachable and how
generous they are), while staying a **pure** domain module: no Discord,
no DB, no I/O.  Randomness is injected so every roll is deterministic
under test.

Design intent (see ``docs/mining_exploration_brainstorm.md``):

* The engine owns the *catalog* of possible outcomes and the math that
  selects and scales one.  A future exploration **service** would own
  state/mutations, and a registered **renderer** (or the read-only AI
  layer) would turn a :class:`ExploreResult` into buttons / an embed /
  an image.  Keeping selection pure here is what lets the AI "narrate
  and theme" an outcome it is *given* without ever writing state.
* Tool-gating (`requires`) is how a loadout meaningfully drives results:
  a torch unlocks deep finds, dynamite unlocks high-payoff blasted
  veins, a lucky charm scales amounts.  This replaces the current binary
  "owns pickaxe → double".

Nothing in this module is wired into a command yet — it is additive
foundation.  ``resolve_to_legacy_tuple`` returns the exact
``(text, item, amount)`` shape the existing ``!explore`` handler already
consumes, so adoption later is a drop-in, not a rewrite.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum


class Biome(Enum):
    """Depth bands.  Deeper biomes carry richer (and riskier) outcomes."""

    SURFACE = "surface"
    CAVERN = "cavern"
    DEEP = "deep"
    MAGMA = "magma"


# Depth ordering for "this outcome is available at this biome or deeper".
_BIOME_DEPTH: dict[Biome, int] = {
    Biome.SURFACE: 0,
    Biome.CAVERN: 1,
    Biome.DEEP: 2,
    Biome.MAGMA: 3,
}


class Rarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"


# Tool names recognised by the gating / scaling logic.  Kept as plain
# strings so a loadout is just "the set of tool item-names the player
# owns" — no coupling to a separate enum the inventory would have to map.
PICKAXE = "pickaxe"
TORCH = "torch"
LANTERN = "lantern"
DYNAMITE = "dynamite"
LUCKY_CHARM = "lucky charm"
MAP = "map"


@dataclass(frozen=True)
class Loadout:
    """The tools a player has available for an exploration roll.

    Built from an inventory elsewhere (``Loadout.from_inventory``) so this
    module never touches the DB.  ``consumes`` on an outcome can later tell
    the caller which tools to decrement — the engine itself mutates
    nothing.
    """

    tools: frozenset[str] = frozenset()

    @classmethod
    def from_inventory(cls, inventory: dict[str, int]) -> Loadout:
        """Derive a loadout from an ``{item_name: qty}`` inventory map.

        A tool counts as equipped when its quantity is positive.  Item
        names are lower-cased to match the inventory's storage convention.
        """
        owned = {
            name.lower()
            for name, qty in inventory.items()
            if qty > 0 and name.lower() in _KNOWN_TOOLS
        }
        return cls(tools=frozenset(owned))

    def has(self, tool: str) -> bool:
        return tool.lower() in self.tools


_KNOWN_TOOLS: frozenset[str] = frozenset(
    {PICKAXE, TORCH, LANTERN, DYNAMITE, LUCKY_CHARM, MAP},
)


@dataclass(frozen=True)
class ExploreOutcome:
    """One catalog entry.  ``narration`` is a flavour template; the engine
    fills ``{amount}`` / ``{item}`` when a roll resolves it.
    """

    key: str
    narration: str
    item: str | None
    amount: int
    rarity: Rarity = Rarity.COMMON
    min_biome: Biome = Biome.SURFACE
    weight: float = 1.0
    # Tools required for this outcome to even be reachable.
    requires: frozenset[str] = field(default_factory=frozenset)
    # Tools this outcome would consume if applied (advisory; engine is pure).
    consumes: frozenset[str] = field(default_factory=frozenset)
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class ExploreResult:
    """The resolved result of one exploration roll."""

    outcome: ExploreOutcome
    biome: Biome
    final_amount: int
    narration: str

    def to_legacy_tuple(self) -> tuple[str, str | None, int]:
        """Return ``(text, item_or_None, delta)`` — the shape the existing
        ``!explore`` handler already consumes.
        """
        return self.narration, self.outcome.item, self.final_amount


# ---------------------------------------------------------------------------
# The catalog.  Deliberately data, not code: extend by appending entries.
# ---------------------------------------------------------------------------
CATALOG: tuple[ExploreOutcome, ...] = (
    # --- surface ---------------------------------------------------------
    ExploreOutcome(
        key="abandoned_camp",
        narration="found {amount} gold in an abandoned camp!",
        item="gold",
        amount=1,
        rarity=Rarity.UNCOMMON,
        min_biome=Biome.SURFACE,
        weight=2.0,
    ),
    ExploreOutcome(
        key="secret_chest",
        narration="found a secret chest with {amount} wood!",
        item="wood",
        amount=3,
        rarity=Rarity.COMMON,
        min_biome=Biome.SURFACE,
        weight=3.0,
    ),
    ExploreOutcome(
        key="got_lost",
        narration="got lost and found nothing...",
        item=None,
        amount=0,
        rarity=Rarity.COMMON,
        min_biome=Biome.SURFACE,
        weight=3.0,
    ),
    ExploreOutcome(
        key="monster_ambush",
        narration="was attacked by monsters and lost {amount} stone...",
        item="stone",
        amount=-2,
        rarity=Rarity.COMMON,
        min_biome=Biome.SURFACE,
        weight=2.0,
        tags=frozenset({"hazard"}),
    ),
    # --- cavern / deep (often torch-gated) -------------------------------
    ExploreOutcome(
        key="hidden_diamond_vein",
        narration="stumbled upon a hidden diamond vein and got {amount} diamond!",
        item="diamond",
        amount=1,
        rarity=Rarity.RARE,
        min_biome=Biome.CAVERN,
        weight=1.0,
        requires=frozenset({TORCH}),
        tags=frozenset({"torch_only"}),
    ),
    ExploreOutcome(
        key="iron_pocket",
        narration="chipped {amount} iron out of a glittering pocket!",
        item="iron",
        amount=2,
        rarity=Rarity.UNCOMMON,
        min_biome=Biome.CAVERN,
        weight=2.0,
    ),
    # --- deep / magma (dynamite-gated high payoff) -----------------------
    ExploreOutcome(
        key="blasted_vein",
        narration="blew open a sealed vein and hauled out {amount} gold!",
        item="gold",
        amount=5,
        rarity=Rarity.RARE,
        min_biome=Biome.DEEP,
        weight=1.0,
        requires=frozenset({DYNAMITE}),
        consumes=frozenset({DYNAMITE}),
        tags=frozenset({"dynamite_only"}),
    ),
    ExploreOutcome(
        key="molten_geode",
        narration="cracked a molten geode and recovered {amount} diamond!",
        item="diamond",
        amount=2,
        rarity=Rarity.LEGENDARY,
        min_biome=Biome.MAGMA,
        weight=0.5,
        requires=frozenset({TORCH}),
    ),
)


def eligible_outcomes(biome: Biome, loadout: Loadout) -> list[ExploreOutcome]:
    """Outcomes reachable at *biome* (or shallower) with *loadout*.

    An outcome is eligible when the current biome is at least as deep as
    its ``min_biome`` and the loadout contains every tool in ``requires``.
    """
    depth = _BIOME_DEPTH[biome]
    return [
        o
        for o in CATALOG
        if _BIOME_DEPTH[o.min_biome] <= depth and o.requires <= loadout.tools
    ]


def _scale_amount(outcome: ExploreOutcome, loadout: Loadout) -> int:
    """Apply loadout-driven scaling to a positive payout.

    A pickaxe doubles ore gains (mirrors the existing !mine bonus); a
    lucky charm adds +1 on top.  Penalties (negative amounts) are never
    scaled — gear protects gains, it does not amplify losses.
    """
    amount = outcome.amount
    if amount <= 0:
        return amount
    if loadout.has(PICKAXE) and outcome.item in {"stone", "iron", "gold", "diamond"}:
        amount *= 2
    if loadout.has(LUCKY_CHARM):
        amount += 1
    return amount


def resolve(
    biome: Biome,
    loadout: Loadout,
    *,
    rng: random.Random | None = None,
) -> ExploreResult:
    """Pick and resolve one weighted exploration outcome.

    *rng* is injected for deterministic tests; defaults to the module
    :mod:`random`.  Always returns a result — if nothing is eligible
    (should not happen given the surface fallbacks), a benign "nothing"
    result is produced.
    """
    chooser = rng or random
    candidates = eligible_outcomes(biome, loadout)
    if not candidates:
        empty = ExploreOutcome(
            key="empty",
            narration="found nothing of note...",
            item=None,
            amount=0,
        )
        return ExploreResult(empty, biome, 0, empty.narration)

    outcome = chooser.choices(candidates, weights=[o.weight for o in candidates], k=1)[
        0
    ]
    final_amount = _scale_amount(outcome, loadout)
    narration = outcome.narration.format(
        amount=abs(final_amount),
        item=outcome.item or "",
    )
    return ExploreResult(outcome, biome, final_amount, narration)


def resolve_to_legacy_tuple(
    biome: Biome = Biome.SURFACE,
    loadout: Loadout | None = None,
    *,
    rng: random.Random | None = None,
) -> tuple[str, str | None, int]:
    """Drop-in replacement for ``rewards.roll_explore_outcome``.

    Returns ``(text, item_or_None, delta)`` so a future wiring step can
    swap the call site with no change to the cog's downstream code.
    """
    return resolve(biome, loadout or Loadout(), rng=rng).to_legacy_tuple()


# Mutation-application is intentionally NOT here: applying ``final_amount``
# and ``outcome.consumes`` to an inventory is a write, which must flow
# through the DB/mutation layer the cog already uses.  This module only
# decides *what* happened, never *commits* it.
__all__ = [
    "Biome",
    "Rarity",
    "Loadout",
    "ExploreOutcome",
    "ExploreResult",
    "CATALOG",
    "eligible_outcomes",
    "resolve",
    "resolve_to_legacy_tuple",
    "PICKAXE",
    "TORCH",
    "LANTERN",
    "DYNAMITE",
    "LUCKY_CHARM",
    "MAP",
]

"""Mining storage caps — pure capacity math for the pack soft-cap and the
upgradeable vault (brainstorm §7.5 "inventory cap + safe stash" → a real sink).

Slice A of ``docs/planning/mining-structures-skill-tree-plan-2026-06-14.md``.

Caps are measured in **distinct item-types**, not total quantity, so a player
who stacks 9 999 stone into one slot is never punished for hoarding a single
resource — only for spreading across many *kinds* (the design intent).

Enforcement is **gentle and additive** (owner directive on the work order:
*"warn at cap, do not hard-block mining; no hard cap approved"*): every function
here is pure and the callers only ever **warn** — mining, deposits, and
withdrawals are never blocked.  The vault upgrade is a coin sink that raises the
comfortable capacity and clears the over-capacity nudge.

This is a ``utils`` module: it imports stdlib only (no services / db), so the
service, view, and cog layers can all share one source of truth for the math.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

#: Soft cap on the active pack, in distinct item-types.  A nudge only — mining
#: never stops at the cap (owner: no hard cap approved).
PACK_SOFT_CAP = 40

#: Vault capacity ladder (distinct item-types), upgradeable for coins.
BASE_VAULT_CAP = 30
VAULT_SLOTS_PER_LEVEL = 15
MAX_VAULT_LEVEL = 6

#: Vault upgrade cost ladder (coins): the cost to go level → level + 1 rises
#: per level so each slot block is a meaningful sink.
_VAULT_UPGRADE_BASE_COST = 2_000
_VAULT_UPGRADE_COST_STEP = 1_500


def distinct_types(store: Mapping[str, int]) -> int:
    """Number of distinct item-types actually held (quantity > 0)."""
    return sum(1 for qty in store.values() if qty > 0)


def projected_distinct_types(store: Mapping[str, int], new_item: str | None) -> int:
    """Distinct-type count *after* granting ``new_item`` (``None`` grants nothing).

    Adding more of an item already held does not consume a new slot, so the
    count only grows when ``new_item`` is a genuinely new type.
    """
    count = distinct_types(store)
    if new_item and store.get(new_item, 0) <= 0:
        count += 1
    return count


def vault_capacity(level: int) -> int:
    """Distinct-type capacity of a vault at ``level`` (clamped to the ladder)."""
    level = max(0, min(level, MAX_VAULT_LEVEL))
    return BASE_VAULT_CAP + level * VAULT_SLOTS_PER_LEVEL


def vault_upgrade_cost(level: int) -> int | None:
    """Coin cost to upgrade **from** ``level`` to ``level`` + 1, or ``None`` if maxed."""
    if level >= MAX_VAULT_LEVEL:
        return None
    return _VAULT_UPGRADE_BASE_COST + max(0, level) * _VAULT_UPGRADE_COST_STEP


@dataclass(frozen=True)
class CapStatus:
    """A store's fill against its (soft) capacity, in distinct item-types."""

    used: int
    cap: int

    @property
    def remaining(self) -> int:
        """Slots left before the cap (never negative)."""
        return max(0, self.cap - self.used)

    @property
    def at_cap(self) -> bool:
        """True once the store has reached (or passed) its cap."""
        return self.used >= self.cap

    @property
    def over_cap(self) -> bool:
        """True only when the store has *passed* its cap."""
        return self.used > self.cap


def pack_status(inventory: Mapping[str, int]) -> CapStatus:
    """The active pack's fill against the soft cap."""
    return CapStatus(used=distinct_types(inventory), cap=PACK_SOFT_CAP)


def vault_status(vault: Mapping[str, int], level: int) -> CapStatus:
    """The vault's fill against its (level-dependent) capacity."""
    return CapStatus(used=distinct_types(vault), cap=vault_capacity(level))


def pack_warning(status: CapStatus) -> str | None:
    """The hub/action nudge when the pack is at/over its soft cap (else ``None``)."""
    if not status.at_cap:
        return None
    return (
        f"⚠️ Your pack is full (**{status.used}/{status.cap}** item types) — "
        "stash spare loot at the 🏦 Vault to keep mining tidy."
    )


def vault_warning(status: CapStatus) -> str | None:
    """The over-capacity nudge for the vault (else ``None``)."""
    if not status.over_cap:
        return None
    return (
        f"⚠️ Your vault is over capacity (**{status.used}/{status.cap}** item "
        "types) — `!vaultupgrade` adds more room."
    )


__all__ = [
    "PACK_SOFT_CAP",
    "BASE_VAULT_CAP",
    "VAULT_SLOTS_PER_LEVEL",
    "MAX_VAULT_LEVEL",
    "CapStatus",
    "distinct_types",
    "projected_distinct_types",
    "vault_capacity",
    "vault_upgrade_cost",
    "pack_status",
    "vault_status",
    "pack_warning",
    "vault_warning",
]

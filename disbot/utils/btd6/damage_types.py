"""Decode a BTD6 projectile's ``immuneBloonProperties`` into a damage type.

bloonswiki stores each projectile's damage type as an ``immuneBloonProperties``
bitmask integer; the ``Template:BTD6 dt`` switch maps it to the named damage
type and the set of bloon properties that type *cannot* pop. This is a verbatim
port of that switch, so "what can this pop?" answers stay authoritative rather
than guessed.

Pure / stdlib-only, so services, views, and the AI grounding layer can all use
it without crossing a layer boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

# immuneBloonProperties bitmask -> (damage type name, what it cannot pop).
# Ported verbatim from Template:BTD6 dt. ``9`` (Energy) is documented there as
# legacy/unused, replaced by ``73``; kept here so stale data still resolves.
_DAMAGE_TYPES: dict[int, tuple[str, str]] = {
    0: ("Normal", "Can damage any Bloon type"),
    1: ("Shatter", "Cannot damage Lead"),
    2: ("Explosion", "Cannot damage Black"),
    4: ("Glacier", "Cannot damage White"),
    5: ("Cold", "Cannot damage Lead or White"),
    8: ("Fire", "Cannot damage Purple"),
    9: ("Energy", "Cannot damage Lead, Purple, or Glass"),
    12: ("Frigid", "Cannot damage White or Purple"),
    17: ("Sharp", "Cannot damage Lead or frozen"),
    64: ("Acid", "Cannot damage Glass"),
    72: ("Plasma", "Cannot damage Purple or Glass"),
    73: ("Energy", "Cannot damage Lead, Purple, or Glass"),
}

_UNKNOWN = ("Unknown", "Unknown immunities")


@dataclass(frozen=True)
class DamageType:
    """A decoded damage type and the bloon properties it cannot pop."""

    name: str
    cannot_pop: str

    @property
    def is_known(self) -> bool:
        return self.name != "Unknown"

    @property
    def pops_everything(self) -> bool:
        return self.name == "Normal"


def decode_damage_type(immune_bloon_properties: int) -> DamageType:
    """Map an ``immuneBloonProperties`` value to its :class:`DamageType`."""
    name, cannot_pop = _DAMAGE_TYPES.get(immune_bloon_properties, _UNKNOWN)
    return DamageType(name=name, cannot_pop=cannot_pop)


__all__ = ["DamageType", "decode_damage_type"]

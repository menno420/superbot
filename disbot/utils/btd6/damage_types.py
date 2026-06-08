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

# Additive damage-modifier field -> short label (the bloon class the bonus
# applies to). The single source of truth shared by the stats embed (Discord
# UI, ``utils.btd6.stats_embed``) and the AI grounding renderer
# (``services.btd6_upgrade_detail_service``) so both surface the same set —
# the bonus values live in the curated stats as ``damageModifierFor*`` (the
# additive read from the dump's misspelled ``damageAddative``).
DAMAGE_MODIFIER_LABELS: tuple[tuple[str, str], ...] = (
    ("damageModifierForLead", "Lead"),
    ("damageModifierForCeramic", "Ceramic"),
    ("damageModifierForFortified", "Fortified"),
    ("damageModifierForMoab", "MOABs"),
    ("damageModifierForMoabs", "MOAB-Class"),
    ("damageModifierForBoss", "Bosses"),
    ("damageModifierForBad", "BADs"),
    ("damageModifierForCamo", "Camo"),
    ("damageModifierForStunned", "stunned"),
)


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


def immunities_for_bloon_properties(bloon_properties: int) -> tuple[str, ...]:
    """Damage-type names a bloon with ``bloon_properties`` is immune to.

    The inverse of :data:`_DAMAGE_TYPES`: a bloon carrying property bit ``p`` is
    immune to a damage type whose ``immuneBloonProperties`` mask shares that bit
    (the projectile-side filter excludes any bloon sharing a property bit). So a
    Lead bloon (bit ``1``) is immune to every damage type whose mask has bit
    ``1`` set — Shatter / Cold / Energy / Sharp. Deterministic (ascending mask
    order), de-duplicated by name, and ``Normal``/``Unknown`` are never emitted.

    This reproduces the curated bloonswiki ``immune_to`` lists **exactly** from
    the game-data dump's ``bloonProperties`` flag (verified 23/23 on v55), so
    bloon immunity can be sourced from the dump instead of the wiki.
    """
    seen: set[str] = set()
    out: list[str] = []
    for mask, (name, _) in _DAMAGE_TYPES.items():
        if (
            mask
            and (mask & bloon_properties)
            and name != "Unknown"
            and name not in seen
        ):
            seen.add(name)
            out.append(name)
    return tuple(out)


__all__ = ["DamageType", "decode_damage_type", "immunities_for_bloon_properties"]

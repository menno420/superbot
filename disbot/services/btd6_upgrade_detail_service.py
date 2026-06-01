"""Targeted BTD6 *upgrade detail* read model — the deep, queryable layer.

:mod:`services.btd6_upgrade_service` resolves a query to an
:class:`~services.btd6_upgrade_service.UpgradeIdentity` (which tower / path /
tier). This module joins that identity to the per-tier combat data in
:mod:`services.btd6_stats_service` and exposes a structured
:class:`UpgradeDetail` — every named attack with its projectiles, spawned
subtowers ("minions"), activated abilities, buffs, and damage zones — plus a
grounding renderer for the AI.

Why a separate layer: the existing normal-stat view distils a tier to a single
"main projectile" (highest damage), which is why a question like *"Prince of
Darkness minion pierce?"* can't be answered from it — the answer (``1``) lives
on the **Reanimate** attack's projectile, not the main one. This model keeps
every attack/minion/buff addressable so those questions resolve.

Purely additive and read-only: it reads the two services above and changes
neither. Wiring :func:`grounding_for_query` into the AI grounding path is a
separate, behaviour-changing step left for review.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services import btd6_stats_service, btd6_upgrade_service
from services.btd6_stats_service import NormalStats
from services.btd6_upgrade_service import UpgradeIdentity

_MAX_LINE = 320
_PATH_LABEL = {"top": "top", "mid": "middle", "bot": "bottom"}


@dataclass(frozen=True)
class ProjectileSpec:
    """One projectile fired by an attack."""

    name: str
    pierce: int | None
    damage: int | None
    damage_type: str | None
    cannot_pop: str | None
    radius: float | None
    lifespan: float | None
    can_see_camo: bool
    moab_bonus: int | None


@dataclass(frozen=True)
class AttackSpec:
    """One named attack on a tier (``Attack``, ``Reanimate``, ``MOAB`` …)."""

    name: str
    cooldown: float | None  # the raw ``rate`` field, in seconds
    count: int | None
    can_see_camo: bool
    projectiles: tuple[ProjectileSpec, ...]


@dataclass(frozen=True)
class SubtowerSpec:
    """A spawned sub-tower / minion (alchemist's Transformed Monkey, etc.)."""

    name: str
    attacks: tuple[AttackSpec, ...]


@dataclass(frozen=True)
class AbilitySpec:
    """An activated ability on a tier."""

    name: str
    cooldown: float | None
    lifespan: float | None


@dataclass(frozen=True)
class UpgradeDetail:
    """The full, structured detail for one upgrade."""

    identity: UpgradeIdentity
    game_version: str
    normal: NormalStats | None
    attacks: tuple[AttackSpec, ...]
    subtowers: tuple[SubtowerSpec, ...]
    abilities: tuple[AbilitySpec, ...]
    buffs: tuple[str, ...]
    zones: tuple[str, ...]

    @property
    def has_combat_stats(self) -> bool:
        return bool(self.attacks or self.subtowers or self.abilities or self.zones)

    @property
    def coverage(self) -> tuple[str, ...]:
        """Which detail sections are populated — for missing-data signalling."""
        present = []
        if self.normal is not None:
            present.append("normal")
        for name in ("attacks", "subtowers", "abilities", "buffs", "zones"):
            if getattr(self, name):
                present.append(name)
        return tuple(present)


# ---------------------------------------------------------------------------
# Parsing (stats JSON node -> spec)
# ---------------------------------------------------------------------------


def _camo(node: dict[str, Any]) -> bool:
    """``filterInvisible`` means the attack/projectile cannot target Camo."""
    return not bool(node.get("filterInvisible"))


def _projectile(proj: dict[str, Any]) -> ProjectileSpec:
    return ProjectileSpec(
        name=str(proj.get("name") or "Projectile"),
        pierce=proj.get("pierce"),
        damage=proj.get("damage"),
        damage_type=proj.get("damage_type"),
        cannot_pop=proj.get("cannot_pop"),
        radius=proj.get("radius"),
        lifespan=proj.get("lifespan"),
        can_see_camo=_camo(proj),
        moab_bonus=proj.get("damageModifierForMoabs"),
    )


def _attack(attack: dict[str, Any]) -> AttackSpec:
    return AttackSpec(
        name=str(attack.get("name") or "Attack"),
        cooldown=attack.get("rate"),
        count=attack.get("count"),
        can_see_camo=_camo(attack),
        projectiles=tuple(_projectile(p) for p in attack.get("projectiles", [])),
    )


def _subtower(sub: dict[str, Any]) -> SubtowerSpec:
    return SubtowerSpec(
        name=str(sub.get("name") or "Minion"),
        attacks=tuple(_attack(a) for a in sub.get("attacks", [])),
    )


def _ability(ability: dict[str, Any]) -> AbilitySpec:
    return AbilitySpec(
        name=str(ability.get("name") or "Ability"),
        cooldown=ability.get("cooldown"),
        lifespan=ability.get("lifespan"),
    )


# Buff field -> readable formatter. Only the headline effect fields; structural
# fields (isGlobal, maxStackSize, filters) are intentionally omitted.
_BUFF_FIELDS: tuple[tuple[str, str], ...] = (
    ("damageAdditive", "+{} damage"),
    ("damageMultiplier", "x{} damage"),
    ("damageAdditiveForMoabs", "+{} damage vs MOAB-class"),
    ("damageAdditiveForCeramic", "+{} damage vs Ceramic"),
    ("damageAdditiveForBad", "+{} damage vs BAD"),
    ("pierceAdditive", "+{} pierce"),
    ("pierceMultiplier", "x{} pierce"),
    ("piercePercentage", "+{}% pierce"),
    ("rateMultiplier", "x{} attack cooldown"),
    ("ratePercentage", "{}% attack speed"),
    ("rangeAdditive", "+{} range"),
    ("rangeMultiplier", "x{} range"),
    ("rangePercentage", "+{}% range"),
    ("lifespanMultiplier", "x{} lifespan"),
    ("abilityCooldownMultiplier", "x{} ability cooldown"),
)


def _buff_text(buff: dict[str, Any]) -> str:
    parts = [
        tmpl.format(buff[field])
        for field, tmpl in _BUFF_FIELDS
        if buff.get(field) is not None
    ]
    name = str(buff.get("name") or "").strip()
    body = ", ".join(parts) if parts else "buff"
    return f"{name}: {body}" if name else body


def _zone_text(zone: dict[str, Any]) -> str:
    name = str(zone.get("name") or "Zone")
    dmg = zone.get("damage")
    dtype = zone.get("damage_type")
    interval = zone.get("interval")
    bits = []
    if dmg is not None:
        bits.append(f"{dmg} {dtype} dmg" if dtype else f"{dmg} dmg")
    if interval is not None:
        bits.append(f"every {interval}s")
    return f"{name} ({', '.join(bits)})" if bits else name


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_upgrade_detail(upgrade_id: str) -> UpgradeDetail | None:
    """Full structured detail for ``upgrade_id`` (``tower_id:code``), or None.

    None only when the id names no real upgrade. A real upgrade on a tower with
    no stats file (or an economy tower with no combat tiers) returns a detail
    with identity + ``normal=None`` / empty sections and ``has_combat_stats``
    False — callers can still surface the identity and signal missing data.
    """
    identity = btd6_upgrade_service.get_upgrade(upgrade_id)
    if identity is None:
        return None

    stats = btd6_stats_service.get_tower_stats(identity.tower_id)
    tier = stats.tier(identity.code) if stats is not None else None
    game_version = stats.game_version if stats is not None else ""

    if tier is None:
        return UpgradeDetail(
            identity=identity,
            game_version=game_version,
            normal=None,
            attacks=(),
            subtowers=(),
            abilities=(),
            buffs=(),
            zones=(),
        )

    return UpgradeDetail(
        identity=identity,
        game_version=game_version,
        normal=btd6_stats_service.normal_stats(tier),
        attacks=tuple(_attack(a) for a in tier.get("attacks", [])),
        subtowers=tuple(_subtower(s) for s in tier.get("subtowers", [])),
        abilities=tuple(_ability(a) for a in tier.get("abilities", [])),
        buffs=tuple(_buff_text(b) for b in tier.get("buffs", [])),
        zones=tuple(_zone_text(z) for z in tier.get("zones", [])),
    )


# ---------------------------------------------------------------------------
# Grounding renderer
# ---------------------------------------------------------------------------


def _cap(line: str) -> str:
    return line if len(line) <= _MAX_LINE else line[: _MAX_LINE - 1] + "…"


def _projectile_bits(proj: ProjectileSpec) -> str:
    bits: list[str] = []
    if proj.damage is not None:
        dmg = (
            f"{proj.damage:,} dmg"
            if isinstance(proj.damage, int)
            else f"{proj.damage} dmg"
        )
        if proj.damage_type and proj.damage_type != "Normal":
            note = f", {proj.cannot_pop}" if proj.cannot_pop else ""
            dmg += f" ({proj.damage_type}{note})"
        bits.append(dmg)
    if proj.pierce is not None:
        bits.append(
            (
                f"{proj.pierce:,} pierce"
                if isinstance(proj.pierce, int)
                else f"{proj.pierce} pierce"
            ),
        )
    if proj.moab_bonus:
        bits.append(f"+{proj.moab_bonus} vs MOAB-class")
    return ", ".join(bits)


def _attack_bits(attack: AttackSpec) -> str:
    projs = attack.projectiles
    if len(projs) == 1:
        body = _projectile_bits(projs[0])
    else:
        body = "; ".join(
            f"{p.name} ({pb})" for p in projs[:4] if (pb := _projectile_bits(p))
        )
    tail: list[str] = []
    if attack.cooldown is not None:
        tail.append(f"{attack.cooldown}s cooldown")
    tail.append("sees Camo" if attack.can_see_camo else "no Camo detection")
    return ", ".join([b for b in (body,) if b] + tail)


def render_upgrade_grounding(detail: UpgradeDetail) -> list[str]:
    """``[btd6_upgrade]`` grounding fact lines for one upgrade, AI-ready."""
    idy = detail.identity
    name = idy.canonical
    path = _PATH_LABEL.get(idy.path, idy.path)
    src = f" (source: bloonswiki{f' {detail.game_version}' if detail.game_version else ''})"
    cost = f", cost ${idy.cost:,}" if idy.cost else ""
    lines = [
        _cap(
            f"[btd6_upgrade] {name} = {idy.tower_name} {idy.crosspath} "
            f"(tier {idy.tier}, {path} path){cost}.{src}",
        ),
    ]

    if not detail.has_combat_stats:
        if detail.normal is None:
            lines.append(f"[btd6_upgrade] {name}: no per-tier combat stats on file.")
        return lines

    for attack in detail.attacks[:6]:
        bits = _attack_bits(attack)
        if bits:
            label = "main attack" if attack.name == "Attack" else attack.name
            lines.append(_cap(f"[btd6_upgrade] {name} — {label}: {bits}."))

    for sub in detail.subtowers[:3]:
        inner = "; ".join(b for a in sub.attacks[:2] if (b := _attack_bits(a)))
        if inner:
            lines.append(_cap(f"[btd6_upgrade] {name} — {sub.name} (minion): {inner}."))
        else:
            lines.append(f"[btd6_upgrade] {name} spawns {sub.name} (minion).")

    if detail.abilities:
        ability = detail.abilities[0]
        ability_bits: list[str] = []
        if ability.cooldown is not None:
            ability_bits.append(f"{ability.cooldown}s cooldown")
        if ability.lifespan is not None:
            ability_bits.append(f"{ability.lifespan}s duration")
        suffix = f": {', '.join(ability_bits)}" if ability_bits else ""
        lines.append(f"[btd6_upgrade] {name} — activated ability{suffix}.")

    for buff in detail.buffs[:4]:
        lines.append(_cap(f"[btd6_upgrade] {name} — buff: {buff}."))

    if detail.zones:
        joined = "; ".join(detail.zones[:4])
        lines.append(_cap(f"[btd6_upgrade] {name} — zones: {joined}."))

    return lines


def grounding_for_query(query: str) -> list[str]:
    """Resolve ``query`` to an upgrade and render its grounding (the wiring seam).

    Returns the fact lines for a confident match, a single clarification line
    for an ambiguous reference, or ``[]`` for no match — so a caller can splice
    the result straight into the grounding context.
    """
    res = btd6_upgrade_service.resolve_upgrade(query)
    if res.match_type == "ambiguous":
        names = ", ".join(c.canonical for c in res.candidates[:6])
        return [
            f"[btd6_upgrade] Ambiguous upgrade reference — did you mean: {names}?",
        ]
    if res.upgrade is None:
        return []
    detail = get_upgrade_detail(res.upgrade.upgrade_id)
    return render_upgrade_grounding(detail) if detail is not None else []


__all__ = [
    "AbilitySpec",
    "AttackSpec",
    "ProjectileSpec",
    "SubtowerSpec",
    "UpgradeDetail",
    "get_upgrade_detail",
    "grounding_for_query",
    "render_upgrade_grounding",
]

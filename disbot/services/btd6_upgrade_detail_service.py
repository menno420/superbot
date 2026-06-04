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
neither. :func:`grounding_for_query` is wired into the AI grounding path via
``btd6_context_service.build`` (its fixture-fallback pass), and the per-projectile
``modifiers`` surface the curated ``damageModifierFor*`` bonuses (e.g. *+3 vs
Ceramic*) the UI embed already shows, so the model can ground bonus-damage
answers instead of refusing them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services import btd6_stats_service, btd6_upgrade_service
from services.btd6_stats_service import NormalStats
from services.btd6_upgrade_service import UpgradeIdentity
from utils.btd6.damage_types import DAMAGE_MODIFIER_LABELS
from utils.btd6.grounding_format import is_infinite

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
    # Additive damage bonuses vs bloon classes, as ``(label, +bonus)`` in a
    # stable order (e.g. ``("Ceramic", 3)``). Surfaces the curated
    # ``damageModifierFor*`` numbers the UI embed already shows, so the AI can
    # ground "bonus damage vs Lead/Ceramic/Fortified" answers.
    modifiers: tuple[tuple[str, int], ...]


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
    # Game-authored "what this upgrade grants" prose (textTable, via the
    # upgrade's LocsKey). Empty when the dump localizes no description.
    description: str = ""

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


def _modifiers(proj: dict[str, Any]) -> tuple[tuple[str, int], ...]:
    """``(label, +bonus)`` for every non-zero ``damageModifierFor*`` on a
    projectile, in the shared canonical order (mirrors the stats embed).
    """
    out: list[tuple[str, int]] = []
    for field_name, label in DAMAGE_MODIFIER_LABELS:
        value = proj.get(field_name)
        if isinstance(value, (int, float)) and value:
            out.append((label, int(value)))
    return tuple(out)


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
        modifiers=_modifiers(proj),
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


# Buff field -> (readable formatter, scale). Only the headline effect fields;
# structural fields (isGlobal, maxStackSize, filters) are intentionally omitted.
# Percentage fields are stored as fractions in the data (0.15 = 15%), so they
# carry a x100 scale — without it the render read "+0.15% pierce" (wrong: it is
# +15%). The fraction is faithful to the dump (PoplustSupportModel
# ``ratePercentIncrease: 0.15``); the percent is a display concern.
_BUFF_FIELDS: tuple[tuple[str, str, int], ...] = (
    ("damageAdditive", "+{} damage", 1),
    ("damageMultiplier", "x{} damage", 1),
    ("damageAdditiveForMoabs", "+{} damage vs MOAB-class", 1),
    ("damageAdditiveForCeramic", "+{} damage vs Ceramic", 1),
    ("damageAdditiveForBad", "+{} damage vs BAD", 1),
    ("pierceAdditive", "+{} pierce", 1),
    ("pierceMultiplier", "x{} pierce", 1),
    ("piercePercentage", "+{}% pierce", 100),
    ("rateMultiplier", "x{} attack cooldown", 1),
    ("ratePercentage", "{}% attack speed", 100),
    ("rangeAdditive", "+{} range", 1),
    ("rangeMultiplier", "x{} range", 1),
    ("rangePercentage", "+{}% range", 100),
    ("lifespanMultiplier", "x{} lifespan", 1),
    ("abilityCooldownMultiplier", "x{} ability cooldown", 1),
    ("heroXpMultiplier", "x{} hero XP", 1),
    # Cash / economy buffs. These were decoded into committed data
    # (TradeEmpireBuffModel, Bucc 0-0-5) but had no render field here, so the
    # renderer surfaced only the damage bonus and silently dropped the income —
    # "what does Trade Empire do" lost its headline effect (extracted, but not
    # answerable). Labels match the wiki: +$10/round per Merchantman, +$20/round
    # per Favored Trades, +4% sellback value in range. The per-buff stack cap
    # (Merchantman x20, sellback x3) is rendered separately — see ``_stack_cap``.
    ("cashPerRoundPerMechantship", "+${}/round per Merchantman", 1),
    ("cashPerRoundPerFavouredTrades", "+${}/round per Favored Trades", 1),
    ("cashbackZoneMultiplier", "+{}% sellback value", 100),
)


def _fmt_buff_num(value: Any) -> str:
    """Whole floats as ints (``15.0`` -> ``15``), real fractions kept (``1.5``)."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (int, float)):
        return str(round(value, 4))
    return str(value)


def _stack_cap(buff: dict[str, Any]) -> int | None:
    """A buff's real, positive stack cap, or ``None``.

    Two field names encode the same concept — ``maxStacks`` on most towers,
    ``maxStackSize`` on Sniper. ``0`` is *not* an unlimited cap: it means the
    buff applies once and does not stack (a global aura like Pirate Lord's
    Flagship or Sergeant's attack-speed buff), so we surface "up to N" only for
    a genuine positive limit — Trade Empire (20 Merchantmen), sellback (3).
    """
    for field in ("maxStacks", "maxStackSize"):
        value = buff.get(field)
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value > 0
        ):
            return int(value)
    return None


def _buff_text(buff: dict[str, Any]) -> str:
    parts = [
        tmpl.format(_fmt_buff_num(buff[field] * scale))
        for field, tmpl, scale in _BUFF_FIELDS
        if isinstance(buff.get(field), (int, float))
        and not isinstance(buff.get(field), bool)
    ]
    name = str(buff.get("name") or "").strip()
    body = ", ".join(parts) if parts else "buff"
    cap = _stack_cap(buff)
    if cap is not None:
        body += f" (stacks up to {cap})"
    return f"{name}: {body}" if name else body


def _zone_num(zone: dict[str, Any], field: str) -> Any:
    """A zone's numeric field value, or None (rejecting bools)."""
    value = zone.get(field)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


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
    # Ice Monkey's Arctic Wind slow: 'multiplier' is the speed multiplier
    # (0.6 = bloons move at 60% speed); MOABs are slowed less. Verified
    # 'multiplier' only ever appears on Ice slow zones, so rendering it as a
    # speed multiplier can't mislabel a different zone type's number.
    slow = _zone_num(zone, "multiplier")
    if slow is not None:
        bits.append(f"slows bloons to x{_fmt_buff_num(slow)} speed")
    moab_slow = _zone_num(zone, "multiplierForMoabs")
    if moab_slow is not None:
        bits.append(f"MOABs to x{_fmt_buff_num(moab_slow)} speed")
    # Druid Thorn zone: flat bonus damage vs Ceramic/MOAB-class.
    cmoab = _zone_num(zone, "damageModifierForCeramicOrMoabs")
    if cmoab is not None:
        bits.append(f"+{_fmt_buff_num(cmoab)} damage vs Ceramic/MOAB")
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
    description = _upgrade_description(stats, identity)

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
            description=description,
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
        description=description,
    )


def _upgrade_description(
    stats: btd6_stats_service.TowerStats | None,
    identity: UpgradeIdentity,
) -> str:
    """The committed upgrade's game-authored ``description``, matched by
    ``(path, tier)`` in the tower's ``upgrades`` list. ``""`` when absent —
    the dump doesn't localize a description for every card (2 of 375).
    """
    if stats is None:
        return ""
    for up in stats.upgrades:
        if (
            isinstance(up, dict)
            and up.get("path") == identity.path_index
            and up.get("tier") == identity.tier
        ):
            desc = up.get("description")
            return desc if isinstance(desc, str) else ""
    return ""


# ---------------------------------------------------------------------------
# Grounding renderer
# ---------------------------------------------------------------------------


def _cap(line: str) -> str:
    return line if len(line) <= _MAX_LINE else line[: _MAX_LINE - 1] + "…"


def _projectile_bits(proj: ProjectileSpec) -> str:
    bits: list[str] = []
    if proj.damage is not None:
        if is_infinite(proj.damage):
            dmg = "∞ dmg"  # 9,999,999 instant-pop sentinel — not a real number
        elif isinstance(proj.damage, int):
            dmg = f"{proj.damage:,} dmg"
        else:
            dmg = f"{proj.damage} dmg"
        if proj.damage_type and proj.damage_type != "Normal":
            note = f", {proj.cannot_pop}" if proj.cannot_pop else ""
            dmg += f" ({proj.damage_type}{note})"
        bits.append(dmg)
    if proj.pierce is not None:
        if is_infinite(proj.pierce):
            bits.append("∞ pierce")
        elif isinstance(proj.pierce, int):
            bits.append(f"{proj.pierce:,} pierce")
        else:
            bits.append(f"{proj.pierce} pierce")
    for label, bonus in proj.modifiers:
        # Say "damage" explicitly: next to "210 pierce" a bare "+20 vs Lead" was
        # misread by the model as bonus pierce — these are additive damage.
        bits.append(f"+{bonus} damage vs {label}")
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

    # Game-authored "what this grants" prose — the most useful single line, so
    # it grounds before (and independent of) the decoded combat stats.
    if detail.description:
        lines.append(
            _cap(
                f"[btd6_upgrade] {name} — {detail.description} "
                "(source: BTD6 in-game description)",
            ),
        )

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

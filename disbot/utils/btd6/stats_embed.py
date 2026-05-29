"""Render BTD6 tower stats into Discord embeds / field text.

Lives in ``utils/btd6/`` so both ``cogs/btd6/`` and ``views/btd6/`` can render
the same shapes (utils may import discord, never services). Inputs are
duck-typed ``Any`` — the ``NormalStats`` / ``TowerStats`` shapes from
``services.btd6_stats_service`` — to preserve the utils → services boundary,
exactly as ``response_embed`` does.

Two surfaces, matching the agreed UX:

* :func:`format_normal_stats` — the glanceable headline field;
* :func:`build_pro_tier_embed` — the full per-tier breakdown behind Pro.
"""

from __future__ import annotations

from typing import Any

import discord

# Damage-modifier field -> short label (the bloon class the bonus applies to).
_DAMAGE_MODIFIERS: tuple[tuple[str, str], ...] = (
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

_PUSH_MULTIPLIERS: tuple[tuple[str, str], ...] = (
    ("pushMultiplierForMoab", "MOAB"),
    ("pushMultiplierForBfb", "BFB"),
    ("pushMultiplierForZomg", "ZOMG"),
    ("pushMultiplierForDdt", "DDT"),
)


# ---------------------------------------------------------------------------
# Normal view
# ---------------------------------------------------------------------------


def format_normal_stats(ns: Any) -> str:
    """Multi-line headline string for the tower-detail embed."""
    line1: list[str] = []
    if ns.damage is not None:
        dmg = f"**{_num(ns.damage)}** dmg"
        if ns.damage_type:
            note = "pops everything" if ns.damage_type == "Normal" else ns.cannot_pop
            dmg += f" · {ns.damage_type}" + (f" ({note})" if note else "")
        line1.append(dmg)
    if ns.pierce is not None:
        line1.append(f"**{_num(ns.pierce)}** pierce")

    line2: list[str] = []
    if ns.cooldown is not None:
        line2.append(f"{ns.cooldown}s cooldown")
    if ns.attack_range is not None:
        line2.append(f"{ns.attack_range} range")
    line2.append("sees Camo" if ns.can_see_camo else "can't see Camo")

    lines = [" · ".join(line1)] if line1 else []
    if line2:
        lines.append(" · ".join(line2))
    if ns.specials:
        lines.append("✦ " + " · ".join(ns.specials))
    return "\n".join(p for p in lines if p) or "No combat stats."


# ---------------------------------------------------------------------------
# Pro view
# ---------------------------------------------------------------------------


def tier_label(stats: Any, code: str) -> str:
    """e.g. ``"Bloon Crush (5-0-0)"`` / ``"Base (0-0-0)"``."""
    crosspath = "-".join(code)
    if code == "000":
        return f"Base ({crosspath})"
    digits = [int(c) for c in code]
    path, tier = next((i + 1, d) for i, d in enumerate(digits) if d)
    name = next(
        (
            u.get("name", "")
            for u in stats.upgrades
            if u.get("path") == path and u.get("tier") == tier
        ),
        "",
    )
    return f"{name} ({crosspath})" if name else crosspath


def _num(value: Any) -> str:
    if isinstance(value, (int, float)) and value >= 9_999_999:
        return "∞"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return f"{value:,}" if isinstance(value, int) else str(value)


def _format_projectile(proj: dict[str, Any]) -> str:
    parts: list[str] = []
    if proj.get("damage"):
        dmg = f"{proj['damage']} dmg"
        if proj.get("damage_type"):
            dmg += f" ({proj['damage_type']})"
        parts.append(dmg)
    if proj.get("pierce") is not None:
        pierce = _num(proj["pierce"])
        if proj.get("maxPierce"):
            pierce += f" (max {_num(proj['maxPierce'])})"
        parts.append(f"{pierce} pierce")
    for key, label in _DAMAGE_MODIFIERS:
        if proj.get(key):
            parts.append(f"+{proj[key]} vs {label}")
    if proj.get("radius"):
        parts.append(f"{_num(proj['radius'])} units radius")
    if proj.get("speed"):
        parts.append(f"{_num(proj['speed'])} units/sec")
    if proj.get("lifespan"):
        parts.append(f"{_num(proj['lifespan'])}s lifespan")
    if proj.get("pushAmount"):
        push = f"{proj['pushAmount']} units knockback"
        muls = [f"×{proj[k]} {lbl}" for k, lbl in _PUSH_MULTIPLIERS if k in proj]
        if muls:
            push += f" ({', '.join(muls)})"
        parts.append(push)
    for effect in proj.get("effects", []):
        if effect.get("lifespan"):
            parts.append(f"{effect.get('name', 'Effect')} {effect['lifespan']}s")
    if proj.get("filterInvisible"):
        parts.append("can't hit Camo")
    if proj.get("rounds"):
        parts.append("persists between rounds")
    body = ", ".join(parts) if parts else "—"
    return f"**{proj.get('name', 'Projectile')}**: {body}"


def _format_ability(ability: dict[str, Any]) -> str:
    parts: list[str] = []
    if ability.get("cooldown"):
        parts.append(f"{ability['cooldown']}s cooldown")
    if ability.get("damageToBad"):
        parts.append(f"{_num(ability['damageToBad'])} to BADs/Bosses")
    if ability.get("damageToNonBad"):
        parts.append(f"{_num(ability['damageToNonBad'])} to other Bloons")
    for proj in ability.get("projectiles", []):
        parts.append(_format_projectile(proj))
    return " · ".join(parts) if parts else "—"


def _stat_node_embed(
    title: str,
    node: dict[str, Any],
    game_version: str,
    *,
    empty_msg: str,
) -> discord.Embed:
    """Shared full-breakdown embed for a tier OR a hero-level stats node.

    Both shapes carry the same ``range`` / ``attacks`` → ``projectiles`` /
    ``abilities`` structure, so the tower Pro view and the hero Pro view render
    through one body.
    """
    embed = discord.Embed(title=title, color=discord.Color.dark_teal())
    head: list[str] = []
    if node.get("range") is not None:
        head.append(f"Range {node['range']} units")
    if node.get("footprintRadius") is not None:
        head.append(f"Footprint {node['footprintRadius']} units")
    if head:
        embed.description = " · ".join(head)

    for attack in node.get("attacks", []):
        lines: list[str] = []
        if attack.get("rate") is not None:
            lines.append(f"Cooldown {attack['rate']}s")
        if attack.get("range") is not None:
            lines.append(f"Range {attack['range']} units")
        lines.extend(_format_projectile(p) for p in attack.get("projectiles", []))
        value = "\n".join(lines) or "—"
        embed.add_field(
            name=f"⚔ {attack.get('name', 'Attack')}",
            value=value[:1024],
            inline=False,
        )

    for ability in node.get("abilities", []):
        embed.add_field(
            name=f"✨ Ability: {ability.get('name', 'Ability')}",
            value=_format_ability(ability)[:1024],
            inline=False,
        )

    if not embed.fields:
        embed.description = empty_msg
    embed.set_footer(text=f"BTD6 stats v{game_version}")
    return embed


def build_pro_tier_embed(stats: Any, code: str) -> discord.Embed:
    """Full per-tier stat breakdown for the tower Pro view."""
    return _stat_node_embed(
        f"🔬 {stats.canonical} — {tier_label(stats, code)}",
        stats.tier(code) or {},
        stats.game_version,
        empty_msg="This is an economy/support tower — no combat stats.",
    )


def hero_level_label(code: str) -> str:
    """e.g. ``"Level 5"`` — the hero analogue of :func:`tier_label`."""
    return f"Level {code}"


def build_pro_hero_level_embed(stats: Any, code: str) -> discord.Embed:
    """Full per-level stat breakdown for a hero's Pro view."""
    return _stat_node_embed(
        f"🔬 {stats.canonical} — {hero_level_label(code)}",
        stats.level(code) or {},
        stats.game_version,
        empty_msg="No combat stats at this level.",
    )


__all__ = [
    "build_pro_hero_level_embed",
    "build_pro_tier_embed",
    "format_normal_stats",
    "hero_level_label",
    "tier_label",
]

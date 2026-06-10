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

from utils.btd6 import tier_codes
from utils.btd6.damage_types import DAMAGE_MODIFIER_LABELS
from utils.btd6.effect_lines import tier_effect_lines

# Damage-modifier field -> short label (the bloon class the bonus applies to).
# Shared with the AI grounding renderer via the single source in damage_types.
_DAMAGE_MODIFIERS = DAMAGE_MODIFIER_LABELS

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
    """e.g. ``"Bloon Crush (5-0-0)"`` / ``"Crossbow (0-3-2)"`` / ``"Base (0-0-0)"``.

    The name comes from the *primary* (highest-tier) path — correct for
    crosspaths, unlike the old first-non-zero-digit shortcut that mislabelled
    e.g. ``2-0-2``. See :mod:`utils.btd6.tier_codes`.
    """
    label = tier_codes.format_code(code)
    if tier_codes.is_base(code):
        return f"Base ({label})"
    path = tier_codes.primary_path(code)
    if path is None:
        return label
    tier = tier_codes.digits(code)[path - 1]
    name = next(
        (
            u.get("name", "")
            for u in stats.upgrades
            if u.get("path") == path and u.get("tier") == tier
        ),
        "",
    )
    return f"{name} ({label})" if name else label


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
    # End-of-round income (Trade Empire $800, Navarch $3,200, Benjamin's
    # levels…) — same wording as the normal view's specials; without this the
    # Pro/paragon/hero views render an income tower as pure combat.
    if node.get("cashPerRound"):
        head.append(f"Income ${_num(node['cashPerRound'])}/round")
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

    # Buff/zone effects + spawned minions were menu-dark on every Pro view
    # (towers showed them only via upgrade cards; heroes and paragons not at
    # all — #655 answerability item 6d). Same shared wording the AI grounding
    # uses (utils.btd6.effect_lines).
    effect_lines = tier_effect_lines(node)
    if effect_lines:
        embed.add_field(
            name="🌀 Effects",
            value=_bullet_block(effect_lines),
            inline=False,
        )
    minion_lines = [
        _format_subtower(sub)
        for sub in node.get("subtowers", [])
        if isinstance(sub, dict)
    ]
    if minion_lines:
        embed.add_field(
            name="🤖 Minions",
            value=_bullet_block(minion_lines),
            inline=False,
        )

    if not embed.fields:
        embed.description = empty_msg
    embed.set_footer(text=f"BTD6 stats v{game_version}")
    return embed


def _bullet_block(lines: list[str], cap: int = 1024) -> str:
    """Bulleted field value bounded to Discord's per-field cap.

    Whole bullets only — a mid-line cut reads like data corruption; the
    drop count keeps the truncation honest.
    """
    out: list[str] = []
    used = 0
    for index, line in enumerate(lines):
        bullet = f"• {line}"
        # Reserve room for a potential "… (+N more)" tail.
        if used + len(bullet) + 1 > cap - 16:
            out.append(f"… (+{len(lines) - index} more)")
            break
        out.append(bullet)
        used += len(bullet) + 1
    return "\n".join(out) or "—"


def _format_subtower(sub: dict[str, Any]) -> str:
    """One spawned minion as ``name — headline (lifespan)``."""
    bits = [_headline(sub)]
    lifespan = sub.get("lifespan")
    if isinstance(lifespan, (int, float)) and lifespan:
        # The 9,999,999 sentinel means permanent (same convention _num
        # renders as ∞ elsewhere) — "∞s lifespan" reads like broken data.
        if lifespan >= 9_999_999:
            bits.append("permanent")
        else:
            bits.append(f"{_num(lifespan)}s lifespan")
    body = " · ".join(bit for bit in bits if bit and bit != "—")
    name = str(sub.get("name") or "Minion")
    return f"**{name}** — {body}" if body else f"**{name}**"


def build_pro_tier_embed(stats: Any, code: str) -> discord.Embed:
    """Full per-tier stat breakdown for the tower Pro view."""
    return _stat_node_embed(
        f"🔬 {stats.canonical} — {tier_label(stats, code)}",
        stats.tier(code) or {},
        stats.game_version,
        empty_msg="This is an economy/support tower — no combat stats.",
    )


def _headline(node: dict[str, Any]) -> str:
    """Compact damage / pierce / cooldown / range line for the compare view."""
    best: dict[str, Any] | None = None
    for attack in node.get("attacks", []):
        for proj in attack.get("projectiles", []):
            if (proj.get("damage") or 0) > (best.get("damage", 0) if best else 0):
                best = proj
    parts: list[str] = []
    if best:
        dmg = f"{_num(best['damage'])} dmg"
        if best.get("damage_type"):
            dmg += f" ({best['damage_type']})"
        parts.append(dmg)
        if best.get("pierce") is not None:
            parts.append(f"{_num(best['pierce'])} pierce")
    attacks = node.get("attacks", [])
    if attacks and attacks[0].get("rate") is not None:
        parts.append(f"{attacks[0]['rate']}s cooldown")
    if node.get("range") is not None:
        parts.append(f"{node['range']} range")
    return " · ".join(parts) or "—"


def build_crosspath_compare_embed(
    stats: Any,
    code_a: str,
    code_b: str,
) -> discord.Embed:
    """Side-by-side headline stats for two tiers / crosspaths of one tower."""
    embed = discord.Embed(
        title=(
            f"⚖ {stats.canonical} — "
            f"{tier_codes.format_code(code_a)} vs {tier_codes.format_code(code_b)}"
        ),
        color=discord.Color.dark_teal(),
    )
    for code in (code_a, code_b):
        embed.add_field(
            name=tier_label(stats, code)[:256],
            value=_headline(stats.tier(code) or {})[:1024],
            inline=True,
        )
    embed.set_footer(text=f"BTD6 stats v{stats.game_version}")
    return embed


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


# ---------------------------------------------------------------------------
# Paragon view (degree-independent base + a per-degree breakdown)
# ---------------------------------------------------------------------------


def build_paragon_base_embed(stats: Any) -> discord.Embed:
    """Degree-independent base stats for a paragon — the infobox view.

    Reuses the shared per-node body, so a paragon renders through the same code
    as a tower tier / hero level. The damage / pierce / cooldown shown are the
    degree-1 values; they scale up per degree (see
    :func:`build_paragon_degree_embed`), while count / speed / radius / lifespan /
    damage type / range hold at every degree.
    """
    embed = _stat_node_embed(
        f"👑 {stats.canonical} — Base stats",
        stats.base,
        stats.game_version,
        empty_msg="No combat stats.",
    )
    header = f"{stats.tower_canonical}'s Paragon (tier 6)"
    if stats.cost:
        header += f" · ${stats.cost:,} on Medium"
    header += "\n*Damage, pierce and cooldown scale with degree (1–100).*"
    if getattr(stats, "is_prose_sourced", False):
        header += (
            "\n*ℹ️ Transcribed from the wiki article (no data module yet) — "
            "primary attacks only.*"
        )
    overview = getattr(stats, "description", "")
    if overview:
        header = f"{overview}\n\n{header}"
    embed.description = (
        f"{header}\n{embed.description}" if embed.description else header
    )
    return embed


def paragon_degree_label(degree: int) -> str:
    """e.g. ``"Degree 50"`` — the paragon analogue of :func:`tier_label`."""
    return f"Degree {degree}"


def build_paragon_degree_embed(stats: Any, degree: int) -> discord.Embed:
    """Degree-dependent stats for one paragon degree (power, boss mult, scaled
    cells grouped by attack / projectile / effect / ability).
    """
    from utils.btd6.paragon_degrees import format_value

    row = stats.degree(degree)
    embed = discord.Embed(
        title=f"👑 {stats.canonical} — {paragon_degree_label(row.degree)}",
        color=discord.Color.gold(),
    )
    embed.description = (
        f"**Power required:** {row.power:,}\n"
        f"**Boss-damage multiplier:** ×{row.boss_multiplier}"
    )
    grouped: dict[str, list[Any]] = {}
    order: list[str] = []
    for cell in row.stats:
        if cell.group not in grouped:
            grouped[cell.group] = []
            order.append(cell.group)
        grouped[cell.group].append(cell)
    for group in order:
        parts: list[str] = []
        for cell in grouped[group]:
            value = format_value(cell.value)
            if cell.is_cooldown:
                value += "s"
            prefix = "+" if cell.is_modifier else ""
            parts.append(f"{cell.label} **{prefix}{value}**")
        embed.add_field(name=group, value=" · ".join(parts)[:1024], inline=False)
    if not row.stats:
        embed.add_field(
            name="—",
            value="No degree-dependent stats.",
            inline=False,
        )
    embed.set_footer(text=f"BTD6 stats v{stats.game_version}")
    return embed


__all__ = [
    "build_crosspath_compare_embed",
    "build_paragon_base_embed",
    "build_paragon_degree_embed",
    "build_pro_hero_level_embed",
    "build_pro_tier_embed",
    "format_normal_stats",
    "hero_level_label",
    "paragon_degree_label",
    "tier_label",
]

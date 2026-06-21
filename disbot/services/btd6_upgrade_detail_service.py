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

# The buff/zone effect renderers live in utils.btd6.effect_lines so the
# Pro-stats embeds (utils layer) share them with this grounding layer
# (helper-policy: needed by services AND utils -> lives in utils). The
# private aliases keep this module's internal callers and its tests stable.
from utils.btd6.effect_lines import buff_text as _buff_text
from utils.btd6.effect_lines import tier_effect_lines
from utils.btd6.effect_lines import zone_text as _zone_text
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
        # Structural zones with no decoded effect render as "" — drop them.
        zones=tuple(text for z in tier.get("zones", []) if (text := _zone_text(z))),
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
    # Per-tier stats are game-sourced since the v55.1 towers cutover; the label
    # carries the stats file's own game_version so a successful answer can
    # never contradict the refusal stamp (the old "bloonswiki 54.0 vs 55.0"
    # label trap from the decode-status provenance note).
    src = (
        " (source: BTD6 game data"
        f"{f' {detail.game_version}' if detail.game_version else ''})"
    )
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


# --- Power → tower-stat application -----------------------------------------
#
# Most Powers don't touch a tower's combat stat: Cash Drop / Thrive are economy,
# Camo & Glue Trap act on bloons, Road Spikes / MOAB Mine are placed damage. The
# one Power whose decoded ``effect`` modifies a *tower* stat is Monkey Boost
# (``rate_scale`` -> attack cooldown). ``_POWER_STAT_EFFECTS`` is the set of
# effect keys we know how to apply to a tier stat; a Power lacking all of them is
# reported honestly as "doesn't modify a tower's attack stat" rather than guessed.
_POWER_STAT_EFFECTS = ("rate_scale",)


def _tier_attack_cooldown(tower_id: str, code: str) -> float | None:
    """The base attack cooldown (seconds) of a tier's primary attack, or None.

    Reads the raw ``attacks[0].rate`` — the same field
    :func:`btd6_stats_service.normal_stats` surfaces as ``cooldown`` — so the
    number matches what every other stat surface reports. ``None`` when the tier
    has no stats file or no attack (economy/support towers, un-statted tiers).
    """
    stats = btd6_stats_service.get_tower_stats(tower_id)
    tier = stats.tier(code) if stats is not None else None
    if not tier:
        return None
    attacks = tier.get("attacks") or []
    if not attacks:
        return None
    rate = attacks[0].get("rate")
    return float(rate) if isinstance(rate, (int, float)) and rate > 0 else None


def _resolve_stat_target(tower: str) -> tuple[str, str, str] | None:
    """Resolve ``tower`` to ``(tower_id, tier_code, display_name)`` or None.

    Accepts an upgrade name / alias / path-notation ("Crossbow Master",
    "dart 0-4-0") via the deterministic upgrade resolver, or a bare tower name
    ("Dart Monkey") which maps to its base tier ``"000"``. Returns ``None`` for a
    miss; the special sentinel ``("", "ambiguous", query)`` flags an ambiguous
    upgrade reference so the caller can ask for clarification.
    """
    from services import btd6_data_service

    res = btd6_upgrade_service.resolve_upgrade(tower)
    if res.match_type == "ambiguous":
        return ("", "ambiguous", tower)
    if res.upgrade is not None:
        return (res.upgrade.tower_id, res.upgrade.code, res.upgrade.canonical)
    entry = btd6_data_service.find_tower(tower)
    if entry is not None:
        return (entry.id, "000", entry.canonical)
    return None


def power_effect(power: str, tower: str) -> dict[str, Any]:
    """Apply a BTD6 Power's decoded effect to a tower/upgrade's attack stat.

    The grounded compute behind the ``btd6_power_effect`` tool: e.g. *"Crossbow
    Master on a Monkey Boost"* -> base 4.19 attacks/sec, boosted 8.38 for 15s.
    Returns ``found=False`` with an honest note for an unknown power, a Power that
    doesn't modify a tower stat, an unresolved/ambiguous tower, or a tower with no
    attack stat — never a fabricated number.
    """
    from services import btd6_data_service

    entry = btd6_data_service.find_power(power)
    if entry is None:
        return {"found": False, "note": f"unknown power: {power!r}"}
    effect = entry.effect or {}
    rate_scale = effect.get("rate_scale")
    if not isinstance(rate_scale, (int, float)) or not any(
        k in effect for k in _POWER_STAT_EFFECTS
    ):
        return {
            "found": False,
            "power": entry.canonical,
            "note": (
                f"{entry.canonical} doesn't modify a tower's attack stat — use "
                "btd6_power_lookup for what it does (it's an economy / bloon / "
                "placed-damage Power, not an attack-speed buff)."
            ),
        }

    target = _resolve_stat_target(tower)
    if target is None:
        return {"found": False, "note": f"could not resolve tower/upgrade: {tower!r}"}
    tower_id, code, display = target
    if code == "ambiguous":
        return {
            "found": False,
            "note": f"ambiguous tower/upgrade reference: {tower!r} — name one upgrade.",
        }

    cooldown = _tier_attack_cooldown(tower_id, code)
    if cooldown is None:
        return {
            "found": False,
            "power": entry.canonical,
            "target": display,
            "note": (
                f"no attack-speed stat for {display} — it has no committed attack "
                "(economy/support tower or un-statted tier)."
            ),
        }

    boosted_cooldown = cooldown * float(rate_scale)
    duration = effect.get("duration_seconds")
    out: dict[str, Any] = {
        "found": True,
        "power": entry.canonical,
        "target": display,
        "tier_code": code,
        "stat": "attack_speed",
        "rate_scale": float(rate_scale),
        "base_cooldown_seconds": round(cooldown, 4),
        "boosted_cooldown_seconds": round(boosted_cooldown, 4),
        "base_attacks_per_second": round(1.0 / cooldown, 3),
        "boosted_attacks_per_second": round(1.0 / boosted_cooldown, 3),
        "note": (
            f"{entry.canonical} multiplies attack cooldown by {float(rate_scale)} "
            f"(lower = faster), so {display} attacks "
            f"{round(1.0 / boosted_cooldown, 3)}x/sec while active "
            f"(vs {round(1.0 / cooldown, 3)}x/sec normally)"
            + (f", for {duration} seconds." if duration is not None else ".")
        ),
    }
    if duration is not None:
        out["duration_seconds"] = duration
    return out


# --- Alchemist buff uptime ---------------------------------------------------
# An Alchemist buff (Berserker Brew / Stronger Stimulant, and the Acidic Mixture
# Dip lead-buff) is *dual-limited*: it ends at the earlier of a time window OR a
# number of the buffed tower's attacks. The throw cadence (re-buff interval) and
# the target's attack speed are committed game data; the time-duration +
# attack-cap are decoded onto the buff-applying attack node by parse_gamedata
# (``buff_duration`` / ``buff_attack_cap``). This compute joins them so the bot
# answers "what's the buff uptime on <tower>" instead of punting on the duration.
_BUFF_ATTACK_LABELS: dict[str, str] = {
    "BeserkerBrewAttack": "Berserker Brew",
    "AcidicMixture": "Acidic Mixture Dip",
}


def _alch_buff_attack(tower_id: str, code: str) -> dict[str, Any] | None:
    """The buff-applying attack node on an Alchemist tier, or ``None``.

    Prefers Berserker Brew (the headline damage/speed/range buff, 3-0-0+) over
    the Acidic Mixture Dip lead-buff (2-0-0+) when a tier carries both. Reads the
    same ``attacks`` list every other stat surface uses.
    """
    stats = btd6_stats_service.get_tower_stats(tower_id)
    tier = stats.tier(code) if stats is not None else None
    attacks = (tier or {}).get("attacks") or []
    brew = acidic = None
    for attack in attacks:
        name = str(attack.get("name") or "")
        if name == "BeserkerBrewAttack":
            brew = attack
        elif name == "AcidicMixture":
            acidic = attack
    return brew or acidic


def buff_uptime(buff_source: str, target: str, targets: int = 1) -> dict[str, Any]:
    """Compute an Alchemist buff's uptime on a target tower — the grounded
    compute behind the ``btd6_buff_uptime`` tool.

    Joins the buff's throw cadence + time-duration + attack-count cap (all game
    data) with the target's attack speed to report **which limiter binds** (time
    vs attacks) and the resulting uptime. e.g. a 4-0-0 (Stronger Stimulant: 12s
    or 40 attacks, thrown every 8s) on a 5-0-0 Ninja (0.217s) burns the 40-attack
    cap in ~8.7s, so it is attack-cap-limited.

    ``targets`` is how many towers in range the one Alchemist is buffing: it
    round-robins its throws, so a given tower is re-buffed every
    ``max(targets × throw_cadence, rebuff_block)`` seconds (``rebuff_block`` =
    the dump's per-target ``rebuffBlockTime`` floor). ``targets=1`` is the
    single-tower case. Returns ``found=False`` with an honest note when the buff
    isn't an Alchemist buff, the window isn't decoded, or the target has no
    attack stat — never a fabricated number.
    """
    targets = max(1, int(targets))
    src = _resolve_stat_target(buff_source)
    if src is None:
        return {
            "found": False,
            "note": f"could not resolve buff source: {buff_source!r}",
        }
    src_id, src_code, src_display = src
    if src_code == "ambiguous":
        return {
            "found": False,
            "note": f"ambiguous Alchemist tier: {buff_source!r} — name one upgrade.",
        }
    if src_id != "alchemist":
        return {
            "found": False,
            "note": (
                f"buff-uptime currently covers the Alchemist (Berserker Brew / "
                f"Acidic Mixture Dip); {src_display} isn't an Alchemist buff."
            ),
        }

    attack = _alch_buff_attack(src_id, src_code)
    if attack is None:
        return {
            "found": False,
            "note": (
                f"{src_display} has no buff throw — Acidic Mixture Dip starts at "
                "2-0-0, Berserker Brew at 3-0-0."
            ),
        }
    buff_label = _BUFF_ATTACK_LABELS.get(
        str(attack.get("name") or ""),
        "Alchemist buff",
    )
    # The buff's own name + the upgrade it comes from, deduped — "Berserker Brew
    # (Stronger Stimulant)", but just "Berserker Brew" when the upgrade IS the buff.
    source_label = (
        buff_label if src_display == buff_label else f"{buff_label} ({src_display})"
    )
    cadence = attack.get("rate")
    duration = attack.get("buff_duration")
    cap = attack.get("buff_attack_cap")
    permanent = bool(attack.get("buff_permanent"))
    rebuff_block = attack.get("buff_rebuff_block")

    tgt = _resolve_stat_target(target)
    if tgt is None:
        return {
            "found": False,
            "note": f"could not resolve target tower/upgrade: {target!r}",
        }
    tgt_id, tgt_code, tgt_display = tgt
    if tgt_code == "ambiguous":
        return {
            "found": False,
            "note": f"ambiguous target tower/upgrade: {target!r} — name one upgrade.",
        }
    tgt_cd = _tier_attack_cooldown(tgt_id, tgt_code)
    if tgt_cd is None:
        return {
            "found": False,
            "note": (
                f"no attack-speed stat for {tgt_display} — it has no committed "
                "attack (economy/support tower or un-statted tier)."
            ),
        }

    out: dict[str, Any] = {
        "found": True,
        "buff": buff_label,
        "buff_source": src_display,
        "buff_tier_code": src_code,
        "target": tgt_display,
        "target_tier_code": tgt_code,
        "target_cooldown_seconds": round(tgt_cd, 4),
        "target_attacks_per_second": round(1.0 / tgt_cd, 3),
        "targets": targets,
    }
    if isinstance(cadence, (int, float)) and cadence > 0:
        out["throw_cadence_seconds"] = float(cadence)
    if isinstance(rebuff_block, (int, float)) and rebuff_block > 0:
        out["rebuff_block_seconds"] = float(rebuff_block)

    # Permanent Brew (5-0-0): the buff never expires once applied.
    if permanent:
        out["limiter"] = "permanent"
        out["uptime"] = 1.0
        out["uptime_percent"] = 100.0
        out["note"] = (
            f"{source_label} is permanent — 100% uptime on "
            f"{tgt_display} once buffed (it never expires)."
        )
        return out

    has_time = isinstance(duration, (int, float)) and duration > 0
    has_cap = isinstance(cap, (int, float)) and cap > 0
    if not has_time and not has_cap:
        # The cadence + target speed ARE known; only the buff window is missing.
        # Say so honestly (better than the old "I don't have it" punt) and name
        # the one step that fills it.
        cadence_txt = (
            f" It is thrown every {float(cadence)}s"
            if isinstance(cadence, (int, float)) and cadence > 0
            else ""
        )
        return {
            "found": False,
            "buff": buff_label,
            "buff_source": src_display,
            "target": tgt_display,
            "note": (
                f"{buff_label}'s duration/attack-cap isn't decoded into the data "
                f"yet, so I can't ground the uptime.{cadence_txt} and {tgt_display} "
                f"attacks every {round(tgt_cd, 4)}s — re-run the game-data parse to "
                "populate the buff window."
            ),
        }

    # Window the buff actually lasts on THIS target = the earlier limiter.
    cap_time = cap * tgt_cd if has_cap else None
    candidates: list[tuple[str, float]] = []
    if has_time:
        candidates.append(("time", float(duration)))
        out["buff_duration_seconds"] = float(duration)
    if has_cap:
        candidates.append(("attacks", float(cap_time)))
        out["buff_attack_cap"] = int(cap)
        out["attack_cap_window_seconds"] = round(float(cap_time), 3)
    limiter, window = min(candidates, key=lambda c: c[1])
    out["limiter"] = limiter
    out["effective_window_seconds"] = round(window, 3)
    out["attacks_under_buff"] = int(min(filter(None, [cap, window / tgt_cd])))

    # Re-buff interval for one of the `targets` towers: the alch round-robins its
    # throws, so each tower's turn comes every `targets × throw_cadence` — but no
    # faster than the per-target `rebuff_block` floor.
    if isinstance(cadence, (int, float)) and cadence > 0:
        floor = float(rebuff_block) if isinstance(rebuff_block, (int, float)) else 0.0
        rebuff_interval = max(float(cadence) * targets, floor)
        out["rebuff_interval_seconds"] = round(rebuff_interval, 3)
        uptime = min(1.0, window / rebuff_interval)
        out["uptime"] = round(uptime, 3)
        out["uptime_percent"] = round(uptime * 100.0, 1)

    limiter_txt = (
        f"the {int(cap)}-attack cap (hit in {round(float(cap_time), 2)}s at "
        f"{round(1.0 / tgt_cd, 2)} attacks/sec)"
        if limiter == "attacks"
        else f"the {float(duration)}s time limit"
    )
    if "uptime_percent" in out:
        if targets > 1:
            uptime_txt = (
                f" Buffing {targets} towers, each gets re-thrown every "
                f"~{out['rebuff_interval_seconds']}s → {out['uptime_percent']}% "
                f"uptime per tower."
            )
        else:
            uptime_txt = (
                f" Re-thrown every {float(cadence)}s → {out['uptime_percent']}% "
                f"uptime{' (continuous)' if out.get('uptime', 0) >= 1.0 else ''} "
                f"on {tgt_display}."
            )
    else:
        uptime_txt = ""
    out["note"] = (
        f"{source_label} on {tgt_display}: limited by {limiter_txt}, "
        f"so it lasts ~{round(window, 2)}s per throw and buffs "
        f"{out['attacks_under_buff']} attacks.{uptime_txt}"
    )
    return out


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


def path_grounding_for_query(query: str) -> list[str]:
    """Ground a ``<tower> <top|middle|bottom> path`` reference's whole tier line.

    Layer A of the absence-claim guard (``docs/btd6/btd6-absence-claim-guard-design.md``
    §4.1): path/line phrasing like "bomb shooter middle path" resolves to no single
    upgrade, so without this it grounds nothing and the model confabulates a false
    "no". This surfaces a **header line naming all five tiers on the path** (so the
    model always sees the complete line — the direct absence-claim antidote) followed
    by each tier's full grounding. Tiers the user **named explicitly** are skipped —
    :func:`grounding_for_query` (Pass 3c) already grounds those. Returns ``[]`` for a
    non-path query so a caller can splice it straight in.
    """
    ref = btd6_upgrade_service.resolve_path_reference(query)
    if ref is None:
        return []
    path_label = _PATH_LABEL.get(ref.path, ref.path)
    roster = ", ".join(f"{u.tier}) {u.canonical}" for u in ref.tiers)
    lines: list[str] = [
        _cap(
            f"[btd6_path] {ref.tower_name} {path_label} path tiers: {roster} "
            "(source: BTD6 game data). These are every tier on that path; do not "
            "claim the path lacks a tier or effect that is listed here.",
        ),
    ]
    query_lc = (query or "").lower()
    for identity in ref.tiers:
        # Skip a tier the user named outright — Pass 3c grounds it in full already.
        if identity.canonical.lower() in query_lc:
            continue
        detail = get_upgrade_detail(identity.upgrade_id)
        if detail is not None:
            lines.extend(render_upgrade_grounding(detail))
    return lines


__all__ = [
    "AbilitySpec",
    "AttackSpec",
    "ProjectileSpec",
    "SubtowerSpec",
    "UpgradeDetail",
    "get_upgrade_detail",
    "grounding_for_query",
    "path_grounding_for_query",
    "power_effect",
    "render_upgrade_grounding",
    "tier_effect_lines",
]

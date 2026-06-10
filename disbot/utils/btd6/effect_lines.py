"""Readable effect lines for a committed tier/level node's buffs + zones.

Moved verbatim from ``services.btd6_upgrade_detail_service`` (2026-06-10,
#655 answerability item 6): the AI grounding layer (services) and the
Pro-stats embeds (``utils.btd6.stats_embed``) both need this rendering, and a
helper needed by services AND utils lives in utils (``docs/helper-policy.md``).
The phrasing is pinned by the upgrade-detail service's tests through its
back-compat aliases — one wording for every surface.

Pure / stdlib-only.
"""

from __future__ import annotations

from typing import Any

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
    # Projectile-size buffs. radiusMultiplier was committed (Striker Jones L7's
    # Mortar blast-radius aura, x1.1) but had no render field, so it surfaced
    # as a bare "buff" — the same extracted-but-not-answerable class as the
    # cash fields below. radiusPercentage (Mortar 0-4-0 ability buff, 0.15)
    # and the absolute projectileRadius (Super Monkey Fan Club) ride along.
    ("radiusMultiplier", "x{} projectile radius", 1),
    ("radiusPercentage", "+{}% projectile radius", 100),
    ("projectileRadius", "{} projectile radius", 1),
    # Benjamin's Bank Hack: banks earn +N% income (a fraction in data, like
    # the other *Percentage fields; L5 0.05, L9 0.12 — prose-confirmed).
    ("incomePercentage", "+{}% income", 100),
    # Projectile-speed aura (Village Primary Training, Ezili totem): fraction,
    # owner-confirmed +25% reading (Q-0069).
    ("projectileSpeedPercentage", "+{}% projectile speed", 100),
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
    # Farm/Village economy + aura tiers (the Q-0067 cutover lift). The income
    # auras are TRUE multipliers (Central Market x1.1 = +10%, Banana Central
    # x1.25, Monkey City x1.2), unlike the fraction-encoded *Percentage rows.
    ("incomeMultiplier", "x{} income", 1),
    ("cashPerPopMultiplier", "x{} cash per pop", 1),
    ("abilityCooldownSpeedScale", "x{} ability recharge rate", 1),
    ("freeUpgradeTiers", "free upgrades up to tier {}", 1),
)

# Presence-flag buff effects (no number — the model's presence is the effect):
# Village Radar Scanner camo grant, Monkey Intelligence Bureau's all-types pop.
_BUFF_FLAG_TEXT: tuple[tuple[str, str], ...] = (
    ("grantsCamoDetection", "grants Camo detection"),
    ("grantsAllDamageTypes", "attacks can pop all Bloon types"),
)


def _fmt_buff_num(value: Any) -> str:
    """Whole floats as ints (``15.0`` -> ``15``), real fractions kept (``1.5``)."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (int, float)):
        return str(round(value, 4))
    return str(value)


def _num_field(node: dict[str, Any], field: str) -> Any:
    """A node's numeric field value, or None (rejecting bools); buffs + zones."""
    value = node.get(field)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


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


# A triggered buff's activation condition, keyed by the ``trigger`` the decoder
# stamps on it (parser ``_BUFF_TRIGGER``). The trigger also fixes the duration
# unit: ``on_life_lost`` carries a seconds ``lifespan`` window + ``cooldown``;
# ``start_of_round`` re-applies every round, so we state the condition rather
# than a round-count duration that would read as "lasts 3s" and mislead.
_BUFF_TRIGGER_COND: dict[str, str] = {
    "on_life_lost": "when a life is lost",
    "start_of_round": "at the start of each round",
}


def _buff_trigger_clause(buff: dict[str, Any]) -> str:
    """Activation condition (+ the active/cooldown window for timed triggers)."""
    trigger = buff.get("trigger")
    if not isinstance(trigger, str):
        return ""
    cond = _BUFF_TRIGGER_COND.get(trigger)
    if cond is None:
        return ""
    if trigger == "on_life_lost":
        life = _num_field(buff, "lifespan")
        cooldown = _num_field(buff, "cooldown")
        window = f"for {_fmt_buff_num(life)}s " if life is not None else ""
        tail = f" ({_fmt_buff_num(cooldown)}s cooldown)" if cooldown is not None else ""
        return f"{window}{cond}{tail}"
    return cond


def buff_text(buff: dict[str, Any]) -> str:
    parts = [
        tmpl.format(_fmt_buff_num(buff[field] * scale))
        for field, tmpl, scale in _BUFF_FIELDS
        if isinstance(buff.get(field), (int, float))
        and not isinstance(buff.get(field), bool)
    ]
    parts += [text for field, text in _BUFF_FLAG_TEXT if buff.get(field) is True]
    name = str(buff.get("name") or "").strip()
    body = ", ".join(parts) if parts else "buff"
    # The cutover's structural split: a paragon can carry the same aura twice,
    # once global and once paragon-scoped (Navarch/Glaive/Shadow Flagship-style
    # buffs). Without this clause the two entries render identically and read
    # as a duplicate.
    if buff.get("onlyAffectParagon") is True:
        body += " (affects paragons only)"
    clause = _buff_trigger_clause(buff)
    if clause:
        body += f" {clause}"
    # Cash-on-leak is a permanent passive, not part of the timed window above, so
    # it gets its own clause. cashOnLeakMultiplier 2 = a leaked bloon grants 2x
    # its value as cash (Desperado Vigilante line; like Bloon Trap / Obyn trees).
    leak = _num_field(buff, "cashOnLeakMultiplier")
    if leak is not None:
        body += f"; leaked bloons give {_fmt_buff_num(leak)}x their value as cash"
    cap = _stack_cap(buff)
    if cap is not None:
        body += f" (stacks up to {cap})"
    return f"{name}: {body}" if name else body


def _slow_zone_subject(zone: dict[str, Any]) -> str:
    """Who a game-native slow zone affects, from its tag + ``inclusive`` flag.

    ``inclusive`` True = bloons WITH the tag, False = everything WITHOUT it
    (Obyn's totem pairs two same-tag zones; without the flag the exclusive one
    reads inverted — see the parser's ``_zones``). No tag = everything.
    """
    tag = str(zone.get("bloonTag") or "")
    inclusive = zone.get("inclusive")
    if tag in ("Moab", "Moabs"):
        return "MOABs" if inclusive is True else "non-MOAB bloons"
    return "bloons"


def zone_text(zone: dict[str, Any]) -> str:
    name = str(zone.get("name") or "").strip()
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
    slow = _num_field(zone, "multiplier")
    if slow is not None:
        bits.append(f"slows bloons to x{_fmt_buff_num(slow)} speed")
    moab_slow = _num_field(zone, "multiplierForMoabs")
    if moab_slow is not None:
        bits.append(f"MOABs to x{_fmt_buff_num(moab_slow)} speed")
    # Game-native slow zones (the cutover shape): ``speedScale`` + an optional
    # bloon tag whose ``inclusive`` flag picks the subject (Ice 0-5-0 carries
    # one zone per subject: non-MOABs x0.4 + MOABs x0.7).
    speed_scale = _num_field(zone, "speedScale")
    if speed_scale is not None:
        bits.append(
            f"slows {_slow_zone_subject(zone)} to x{_fmt_buff_num(speed_scale)} speed",
        )
    # Druid Thorn zone: flat bonus damage vs Ceramic/MOAB-class.
    cmoab = _num_field(zone, "damageModifierForCeramicOrMoabs")
    if cmoab is not None:
        bits.append(f"+{_fmt_buff_num(cmoab)} damage vs Ceramic/MOAB")
    # Village discount aura: a fraction (0.1 = 10% off) capped by upgrade tier
    # (Monkey Business: "10% discount … tier 3 or less" — prose-pinned).
    discount = _num_field(zone, "discountMultiplier")
    if discount is not None:
        cap = _num_field(zone, "tierCap")
        tail = f" on upgrades up to tier {_fmt_buff_num(cap)}" if cap else ""
        bits.append(f"{_fmt_buff_num(discount * 100)}% discount{tail}")
    bits.extend(_moab_shove_bits(zone))
    if not bits:
        # A structural zone with no decoded effect and no curated label is
        # nothing a user can read — suppress the line entirely (callers filter
        # empty strings) rather than surface a bare internal marker.
        return name
    label = name or "Zone"
    return f"{label} ({', '.join(bits)})"


# Heli Pilot "MOAB Shove" (0-0-3+) per-blimp speed caps, maintainer-confirmed
# sign semantics (2026-06-08): a NEGATIVE cap means the blimp is shoved
# *backward* (it moves in reverse, up to that fraction of its normal speed); a
# POSITIVE cap means it can only be slowed *forward* to that fraction (too heavy
# to reverse); 0 means it can be slowed to a halt. The dump's
# ``moab/bfb/zomgPushSpeedScaleCap`` are committed verbatim as these fields and
# verified exact vs the dump (e.g. Comanche Defense 0-0-4: MOAB -0.51, BFB -0.11,
# ZOMG 0.09). DDT has no field in the dump; the committed data mirrors ZOMG, so
# we render it only when present. ``multiplierForMoab`` (singular) is unique to
# this zone type — it never collides with Ice's ``multiplierForMoabs`` (plural).
_MOAB_SHOVE_CLASSES: tuple[tuple[str, str], ...] = (
    ("MOAB-class", "multiplierForMoab"),
    ("BFB", "multiplierForBfb"),
    ("ZOMG", "multiplierForZomg"),
    ("DDT", "multiplierForDdt"),
)


def _moab_shove_bits(zone: dict[str, Any]) -> list[str]:
    """Per-blimp shove/slow phrasing for a MOAB-Shove zone (empty for others)."""
    if _num_field(zone, "multiplierForMoab") is None:
        return []  # not a shove zone — the singular field is its unique marker
    bits: list[str] = []
    for label, field in _MOAB_SHOVE_CLASSES:
        cap = _num_field(zone, field)
        if cap is None:
            continue
        if cap < 0:
            bits.append(f"{label} shoved backward at x{_fmt_buff_num(cap)} speed")
        elif cap == 0:
            bits.append(f"{label} slowed to a halt")
        else:
            bits.append(f"{label} slowed to x{_fmt_buff_num(cap)} speed")
    return bits


def tier_effect_lines(tier: dict[str, Any]) -> list[str]:
    """Rendered buff + zone effect strings for a committed tier node.

    The default upgrade grounding resolves an upgrade *card* to its base-path
    tier, so a specifically-named crosspath's buff/zone effects (e.g. Heli Pilot
    0-1-4's stronger MOAB Shove, MOAB -0.51 vs the 0-0-4 base -0.4) are stored but
    never surfaced. This renders them off any tier dict so the crosspath grounding
    seam can reach them — reusing the exact ``_buff_text``/``_zone_text`` the
    upgrade path uses, so the phrasing stays identical.
    """
    out = [buff_text(b) for b in tier.get("buffs", []) if isinstance(b, dict)]
    out += [
        text
        for z in tier.get("zones", [])
        if isinstance(z, dict) and (text := zone_text(z))
    ]
    return out

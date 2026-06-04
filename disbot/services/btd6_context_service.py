"""BTD6 context owner for the central AI stage.

The BTD6 cog's intent-resolution / confidence-threshold logic lives
here so it can be invoked by the central natural-language stage when
the task router classifies a message as
:attr:`AITask.BTD6_ANSWER`.

PR3 wires real grounding: the resolver's typed entities become
:class:`BTD6FactQuery` rows, and :func:`btd6_fact_store.fetch_for_intent`
returns matching ``btd6_facts`` rows joined to the source registry.
Each row is sanitised (control chars stripped, capped at 240 chars)
and rendered with a provenance label before reaching the instruction
stack — which itself wraps the whole bundle as untrusted data, so
adversarial text inside body_json never reaches the system prompt
unwrapped.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from utils.btd6 import coverage as cov
from utils.btd6 import tier_codes
from utils.btd6.body_coerce import coerce_body
from utils.btd6.grounding_format import DEFAULT_CAP as _FACT_TEXT_CAP
from utils.btd6.grounding_format import is_infinite as _is_infinite
from utils.btd6.grounding_format import relative_time as _relative_time
from utils.btd6.grounding_format import sanitise as _sanitise_helper

logger = logging.getLogger("bot.services.btd6_context")

_DEFAULT_SOURCE_SUMMARY = "data.ninjakiwi.com (Tier 1)"
_FALLBACK_SOURCE_SUMMARY = "no btd6_facts rows for intent"

# Crosspath codes mentioned in a query, e.g. "0-2-5" or "025". Bounded by
# non-digit/hyphen edges so it won't fire inside longer numbers (versions etc.).
_CROSSPATH_RE = re.compile(r"(?<![\d-])([0-5])-?([0-5])-?([0-5])(?![\d-])")


def _crosspaths_in_text(text: str, *, limit: int = 3) -> list[str]:
    """Legal crosspath codes named in ``text`` (single-path tiers excluded).

    The 16 single-path tiers already ship in grounding, so this only surfaces
    the specific crosspath a user named — never all ~48 per tower.
    """
    out: list[str] = []
    for match in _CROSSPATH_RE.finditer(text or ""):
        code = "".join(match.groups())
        if (
            tier_codes.is_legal(code)
            and tier_codes.is_crosspath(code)
            and code not in out
        ):
            out.append(code)
        if len(out) >= limit:
            break
    return out


@dataclass(frozen=True)
class BTD6Context:
    """Retrieved facts ready for the instruction stack."""

    facts: tuple[str, ...]
    source_summary: str
    confidence: float


def _sanitise(value: object) -> str:
    """Strip control chars, collapse whitespace, cap at 240 chars.

    Thin wrapper around :func:`utils.btd6.grounding_format.sanitise`
    that locks the cap at :data:`_FACT_TEXT_CAP`, so existing callers
    that read this name continue to behave identically.
    """
    return _sanitise_helper(value, cap=_FACT_TEXT_CAP)


# Body keys (in priority order) we try as the human-readable headline.
_HEADLINE_KEYS = ("name", "display_name", "id", "tile_id")

# Body keys we surface as "k=v" extras when present and scalar.
_EXTRA_KEYS = (
    ("map", "map"),
    ("mode", "mode"),
    ("difficulty", "difficulty"),
    ("rank", "rank"),
    ("score", "score"),
    ("type", "type"),
    ("game_type", "game_type"),
)


def _render_fact(row: dict[str, Any]) -> str:
    """Turn one fact row into a single labeled context string.

    The rendered line begins with a ``[entity_kind]`` tag (e.g.
    ``[btd6_boss]``) so the LLM knows what category the name belongs
    to. Without this tag, asking "what was the previous boss?" can
    surface race / event names and the model has no signal to filter
    them — leading it to fall back to training-data names like
    "Vortex" instead of using the freshly-fetched grounding.

    URL fields (``creator_url``, ``profile_url``, ``metadata_url``,
    ``map_url``, ``boss_type_url``, ``leaderboard_*_url`` etc.) are
    intentionally NOT included; the parser preserves them in the
    body, but bare links in a context string can encourage the LLM
    to follow them.
    """
    body = coerce_body(row.get("body_json"))
    headline = ""
    for key in _HEADLINE_KEYS:
        value = body.get(key)
        if isinstance(value, str) and value and value != "n/a":
            headline = _sanitise(value)
            break
    extras: list[str] = []
    for body_key, label in _EXTRA_KEYS:
        value = body.get(body_key)
        if value is None or isinstance(value, (dict, list)):
            continue
        extras.append(f"{label}={_sanitise(str(value))}")
    parts: list[str] = []
    if headline:
        parts.append(headline)
    if extras:
        parts.append(", ".join(extras))
    summary = " — ".join(parts) if parts else "(no summary)"
    source_name = _sanitise(row.get("source_name") or "data.ninjakiwi.com")
    rel = _relative_time(row.get("fetched_at"))
    version = row.get("version")
    version_label = f", v{version}" if isinstance(version, int) and version > 1 else ""
    # Tag with the entity_kind so the model can disambiguate between
    # race / boss / odyssey / event / tower / hero names when the user
    # asks about a specific category. The kind is intentionally a
    # bracketed prefix the task contract teaches the model to read.
    kind = _sanitise(str(row.get("entity_kind") or ""))
    kind_tag = f"[{kind}] " if kind else ""
    full = f"{kind_tag}{summary} (source: {source_name}{version_label}, fetched {rel})"
    if len(full) > _FACT_TEXT_CAP:
        full = full[: _FACT_TEXT_CAP - 1] + "…"
    return full


def _intent_to_queries(intent: Any) -> list[Any]:
    """Map a :class:`ResolvedIntent` to grounding queries (static kinds).

    Each typed entity with a known key (tower / hero / map / mode)
    becomes one :class:`BTD6FactQuery` with ``fact_type=None`` so any
    registered fact about the entity surfaces. PR-E added live
    entities (race / boss / CT / odyssey / challenge / event /
    leaderboard) — those don't have a known key from the resolver
    and are handled by :func:`_fetch_live_entity_rows` instead.
    """
    from services.btd6_fact_store import BTD6FactQuery

    queries: list[BTD6FactQuery] = []
    for tower in getattr(intent, "towers", ()):
        if getattr(tower, "id", None):
            queries.append(BTD6FactQuery(None, "btd6_tower", str(tower.id)))
    for hero in getattr(intent, "heroes", ()):
        if getattr(hero, "id", None):
            queries.append(BTD6FactQuery(None, "btd6_hero", str(hero.id)))
    for game_map in getattr(intent, "maps", ()):
        if getattr(game_map, "id", None):
            queries.append(BTD6FactQuery(None, "btd6_map", str(game_map.id)))
    for mode in getattr(intent, "modes", ()):
        if getattr(mode, "id", None):
            queries.append(BTD6FactQuery(None, "btd6_mode", str(mode.id)))
    return queries


async def _fetch_live_entity_rows(
    intent: Any,
    *,
    per_kind_limit: int = 3,
) -> list[dict[str, Any]]:
    """Resolve PR-E live entities into the newest facts per kind.

    The resolver yields ``LiveEntityMatch`` records that only carry
    the parser-produced ``entity_kind``. The fact store's
    ``search_facts`` already returns the newest envelopes per kind,
    ordered by ``fetched_at DESC``. We cap each kind so one chatty
    leaderboard cannot drown out other kinds in the same context.
    """
    matches = getattr(intent, "live_entities", ()) or ()
    if not matches:
        return []
    from utils.db import btd6_sources as btd6_db

    seen_kinds: set[str] = set()
    rows: list[dict[str, Any]] = []
    for match in matches:
        kind = getattr(match, "entity_kind", None)
        if not kind or kind in seen_kinds:
            continue
        seen_kinds.add(kind)
        batch = await btd6_db.search_facts(
            entity_kind=kind,
            limit=per_kind_limit,
        )
        rows.extend(batch)
    return rows


def _render_restriction_for_grounding(entity_name: str, ctx: Any) -> str:
    """Render one tower/hero restriction context as a grounding line.

    Bounded by ``_FACT_TEXT_CAP``; provenance label always present.
    """
    name = _sanitise(entity_name) or "(unknown)"
    event_name = _sanitise(getattr(ctx, "event_name", "")) or "(unknown event)"
    kind = getattr(ctx, "event_kind", "")
    kind_label = {
        "btd6_race": "race",
        "btd6_boss_difficulty": "boss",
        "btd6_odyssey_difficulty": "odyssey",
        "btd6_challenge": "challenge",
    }.get(kind, kind or "event")
    stance = getattr(ctx, "stance", "allowed")
    if getattr(ctx, "sentinel_all_heroes_banned", False):
        body = f"All heroes are banned in {kind_label} '{event_name}'"
    elif stance == "banned":
        body = f"{name} is banned in {kind_label} '{event_name}'"
    elif stance == "limited":
        body = (
            f"{name} is limited (max {ctx.max_count}) in "
            f"{kind_label} '{event_name}'"
        )
    elif stance == "path_blocked":
        body = f"{name} has path tiers blocked in {kind_label} '{event_name}'"
    else:
        return ""
    rel = _relative_time(getattr(ctx, "fetched_at", None))
    full = f"{body} (source: data.ninjakiwi.com, fetched {rel})"
    if len(full) > _FACT_TEXT_CAP:
        full = full[: _FACT_TEXT_CAP - 1] + "…"
    return full


async def _restriction_lines_for_intent(intent: Any) -> list[str]:
    """Pull active-event restriction strings for towers/heroes in ``intent``.

    Returns an empty list when nothing matches; bounded at 8 lines so a
    chatty event can't drown the LLM context window.
    """
    from services import btd6_live_query_service as btd6_live

    out: list[str] = []
    for tower in getattr(intent, "towers", ()) or ():
        if not getattr(tower, "id", None):
            continue
        for ctx in await btd6_live.get_active_event_restrictions_for_tower(
            str(tower.id),
        ):
            line = _render_restriction_for_grounding(
                getattr(tower, "canonical", "") or str(tower.id),
                ctx,
            )
            if line:
                out.append(line)
    for hero in getattr(intent, "heroes", ()) or ():
        if not getattr(hero, "id", None):
            continue
        for ctx in await btd6_live.get_active_event_restrictions_for_hero(
            str(hero.id),
        ):
            line = _render_restriction_for_grounding(
                getattr(hero, "canonical", "") or str(hero.id),
                ctx,
            )
            if line:
                out.append(line)
    return out[:8]


def _render_fixture_tower(entry: Any) -> list[str]:
    """Render a TowerEntry as 1-4 grounding lines for the AI context.

    Returns multiple short strings (each within ``_FACT_TEXT_CAP``) so
    the LLM gets cost, category, and upgrade path names without any
    single line being truncated.
    """
    canonical = _sanitise(
        getattr(entry, "canonical", "") or str(getattr(entry, "id", "")),
    )
    cost = getattr(entry, "base_cost", None)
    category = _sanitise(str(getattr(entry, "category", "") or ""))
    description = _sanitise(getattr(entry, "description", "") or "")
    lines: list[str] = []

    # Line 1: identity + cost
    cost_str = f"base cost: {cost} (medium difficulty)" if cost else ""
    cat_str = f"category: {category}" if category else ""
    meta = " | ".join(p for p in [cost_str, cat_str] if p)
    lines.append(
        (
            _cap(f"[btd6_tower] {canonical} — {meta} (source: fixture/btd6_data)")
            if meta
            else _cap(f"[btd6_tower] {canonical} (source: fixture/btd6_data)")
        ),
    )

    # Lines 2-4: one per upgrade path, including costs when populated.
    upgrade_paths: dict[str, Any] = getattr(entry, "upgrade_paths", {}) or {}
    upgrade_costs: dict[str, Any] = getattr(entry, "upgrade_costs", {}) or {}
    for path_name, upgrades in upgrade_paths.items():
        if not upgrades:
            continue
        costs = upgrade_costs.get(path_name, ())
        has_costs = bool(costs) and any(c for c in costs)
        if has_costs:
            parts = [
                f"{u} (${c})" if c else u for u, c in zip(upgrades, costs, strict=False)
            ]
            upgrades_str = ", ".join(parts)
        else:
            upgrades_str = ", ".join(str(u) for u in upgrades if u)
        lines.append(
            _cap(
                f"[btd6_tower] {canonical} {path_name} upgrades: "
                f"{upgrades_str} (source: fixture/btd6_data)",
            ),
        )

    if description:
        lines.append(
            _cap(
                f"[btd6_tower] {canonical} — {description} (source: fixture/btd6_data)",
            ),
        )

    lines.extend(_render_paragon(getattr(entry, "id", ""), canonical))
    lines.extend(_render_upgrade_descriptions(getattr(entry, "id", ""), canonical))
    lines.extend(_render_tower_costs(getattr(entry, "id", ""), canonical))
    lines.extend(_render_tower_stats(getattr(entry, "id", ""), canonical))
    return lines


def _render_upgrade_descriptions(tower_id: str, canonical: str) -> list[str]:
    """Per-upgrade game-authored description prose as ``[btd6_upgrade]`` lines.

    A tower's 15 upgrade cards each carry a localized description (extracted from
    the dump). ``_render_tower`` lists upgrade NAMES + costs but not their prose,
    so "list the upgrades and descriptions of X" / "what does <upgrade> do" had no
    grounding and the model free-recalled it — which the faithfulness guard
    rejected (live ``grounding_failed``). Surfaces every described card, bounded
    by the 15-card max and emitted only for a specifically-named tower — the
    tower analogue of :func:`_render_hero_descriptions`.
    """
    from services import btd6_stats_service

    stats = btd6_stats_service.get_tower_stats(tower_id)
    if stats is None:
        return []
    suffix = " (source: BTD6 in-game description)"
    lines: list[str] = []
    for up in stats.upgrades:
        if not isinstance(up, dict):
            continue
        name = _sanitise(str(up.get("name", "") or ""))
        desc = _sanitise(str(up.get("description", "") or ""))
        if not name or not desc:
            continue
        # Budget the prose so the provenance suffix always survives (mirrors the
        # per-level hero descriptions); _cap would otherwise chop the source off.
        prefix = f"[btd6_upgrade] {canonical} {name}: "
        budget = _FACT_TEXT_CAP - len(prefix) - len(suffix)
        if budget < len(desc):
            desc = desc[: max(budget - 1, 0)].rstrip() + "…"
        lines.append(f"{prefix}{desc}{suffix}")
    return lines


def _render_tower_costs(tower_id: str, canonical: str) -> list[str]:
    """All-difficulty per-buy + cumulative upgrade costs as ``[btd6_cost]`` lines.

    ``_render_tower`` carries only the Medium per-buy price, so a "pricing across
    all difficulties" or "total cost to reach tier N" table emitted *derived*
    numbers (difficulty-scaled / summed) absent from grounding — the faithfulness
    guard rejected them (live ``grounding_failed``) on any turn where the model
    didn't route through the cost tools, which it does inconsistently. Surfacing
    every derived number as a grounded fact makes those tables answerable by
    construction, independent of tool invocation. Reuses the tested
    :func:`btd6_data_service.cumulative_upgrade_costs` (one pass per difficulty);
    emitted for any named tower that has cost data.
    """
    from services import btd6_data_service
    from utils.btd6 import difficulty_costs

    diffs = difficulty_costs.DIFFICULTIES  # easy, medium, hard, impoppable
    per = {
        d: btd6_data_service.cumulative_upgrade_costs(tower_id, difficulty=d)
        for d in diffs
    }
    if not per["medium"].get("found"):
        return []
    base = {d: per[d]["base_cost"] for d in diffs}
    lines = [
        _cap(
            f"[btd6_cost] {canonical} pricing — Medium from fixture/btd6_data; "
            "Easy/Hard/Impoppable = Medium ×0.85/1.08/1.20 rounded to $5; "
            "'to reach' = tower base + all earlier tiers on that path.",
        ),
        _cap(
            f"[btd6_cost] {canonical} base placement: Easy ${base['easy']:,}, "
            f"Medium ${base['medium']:,}, Hard ${base['hard']:,}, "
            f"Impoppable ${base['impoppable']:,}",
        ),
    ]
    for pkey, tiers in per["medium"]["paths"].items():
        by_tier = {d: {t["tier"]: t for t in per[d]["paths"][pkey]} for d in diffs}
        for t in tiers:
            tier = t["tier"]
            b = {d: by_tier[d][tier]["upgrade_cost"] for d in diffs}
            c = {d: by_tier[d][tier]["cumulative_cost"] for d in diffs}
            lines.append(
                _cap(
                    f"[btd6_cost] {canonical} {t['name']} ({pkey} tier {tier}) — "
                    f"buy E${b['easy']:,}/M${b['medium']:,}/H${b['hard']:,}/I${b['impoppable']:,}; "
                    f"to reach E${c['easy']:,}/M${c['medium']:,}/H${c['hard']:,}/I${c['impoppable']:,}",
                ),
            )
    return lines


def _render_paragon(tower_id: str, canonical: str) -> list[str]:
    """One grounding line naming this tower's Paragon (tier 6) + Medium cost.

    Returns nothing for the towers that have no paragon. Tagged
    ``[btd6_paragon]`` so the assistant uses the verified name instead of
    guessing one (or claiming a paragon for a tower that has none).
    """
    from services import btd6_stats_service

    stats = btd6_stats_service.get_tower_stats(tower_id)
    if stats is None or not stats.paragon_cost:
        return []
    name = stats.paragon_name or f"{canonical} Paragon"
    lines = [
        _cap(
            f"[btd6_paragon] {canonical}'s Paragon (tier 6) is {name}, costing "
            f"{stats.paragon_cost} on Medium (source: bloonswiki)",
        ),
    ]
    pstats = btd6_stats_service.get_paragon_stats_by_tower(tower_id)
    if pstats is not None and pstats.description:
        # Overview is paraphrased from bloonswiki; the [btd6_paragon] tag + the
        # cost line above already establish the source, so keep this line lean
        # (the per-fact cap would otherwise truncate a trailing attribution).
        lines.append(_cap(f"[btd6_paragon] {name} — {_sanitise(pstats.description)}"))
    if pstats is not None:
        lines.extend(_render_paragon_abilities(name, pstats))
    lines.extend(_render_paragon_stats(tower_id, name))
    return lines


def _render_paragon_abilities(name: str, pstats: Any) -> list[str]:
    """``[btd6_paragon]`` ability lines for a paragon (curated from bloonswiki).

    One line per named ability so the assistant can answer "what does <ability>
    do / what's its cooldown" without guessing. A paragon with no activated
    ability (e.g. Apex Plasma Master) gets a single explicit line so the model
    states that rather than inventing one.
    """
    abilities = getattr(pstats, "abilities", ()) or ()
    if not abilities:
        return [f"[btd6_paragon] {name} has no activated ability."]
    lines: list[str] = []
    for ability in abilities:
        if ability.kind == "passive":
            head = f"[btd6_paragon] {name} passive — {ability.name}"
        else:
            cd = f" ({ability.cooldown}s cooldown)" if ability.cooldown else ""
            head = f"[btd6_paragon] {name} ability — {ability.name}{cd}"
        lines.append(_cap(f"{head}: {_sanitise(ability.description)}"))
    return lines


def _paragon_main_bits(base: dict[str, Any], degree: int) -> list[str]:
    """Headline bits for a paragon's *primary* attack at ``degree``.

    Uses the first attack (the recognisable main weapon) rather than the highest
    single-hit projectile, so the headline isn't dominated by a situational nuke
    (e.g. Glaive Dominus's MOAB Press). Damage / pierce / cooldown are scaled by
    the wiki's degree formulas; the damage type + immunity note are folded in
    exactly as the tower headline does. Returns ``[]`` for an ability-led paragon
    with no primary attack.
    """
    from utils.btd6 import paragon_degrees

    attacks = base.get("attacks") or []
    if not attacks:
        return []
    attack = attacks[0]
    projectiles = attack.get("projectiles") or []
    main = max(projectiles, key=lambda p: p.get("damage") or 0, default=None)

    bits: list[str] = []
    if main is not None:
        damage = main.get("damage")
        if isinstance(damage, (int, float)) and damage > 0:
            dmg = f"{_big(round(paragon_degrees.scale_damage(damage, degree)))} dmg"
            dtype = main.get("damage_type")
            if dtype:
                note = (
                    "pops everything" if dtype == "Normal" else main.get("cannot_pop")
                )
                dmg += f" ({dtype}{f', {note}' if note else ''})"
            bits.append(dmg)
        pierce = main.get("pierce")
        if (
            isinstance(pierce, (int, float))
            and pierce < 99999
            and (main.get("maxPierce") or 0) < 1
        ):
            bits.append(
                f"{_big(round(paragon_degrees.scale_pierce(pierce, degree)))} pierce",
            )
    rate = attack.get("rate")
    if isinstance(rate, (int, float)) and rate < 9999:
        cd = paragon_degrees.format_value(paragon_degrees.scale_cooldown(rate, degree))
        bits.append(f"{cd}s cooldown")
    return bits


def _render_paragon_stats(tower_id: str, name: str) -> list[str]:
    """Headline paragon combat stats as ``[btd6_paragon_stats normal]`` lines.

    Bounded to two lines — Degree 1 (base) and Degree 100 (max) — so the model
    has the *range* a paragon's stats span without flooding the prompt with 100
    rows. Degree-dependent values are derived by ``utils.btd6.paragon_degrees``
    (the wiki's own scaling). The two prose-sourced paragons label their origin
    so the model can hedge appropriately.
    """
    from services import btd6_stats_service
    from utils.btd6 import paragon_degrees

    pstats = btd6_stats_service.get_paragon_stats_by_tower(tower_id)
    if pstats is None or not pstats.has_combat_stats:
        return []

    src = "bloonswiki article prose" if pstats.is_prose_sourced else "bloonswiki"
    lines: list[str] = []
    base_bits = _paragon_main_bits(pstats.base, 1) or _normal_stat_bits(
        btd6_stats_service.normal_stats(pstats.base),
    )
    if base_bits:
        lines.append(
            _cap(
                f"[btd6_paragon_stats normal] {name} primary attack at Degree 1 "
                f"(base): {_sanitise(', '.join(base_bits))} (source: {src})",
            ),
        )

    max_bits = _paragon_main_bits(pstats.base, 100)
    boss = paragon_degrees.boss_multiplier(100)
    lines.append(
        _cap(
            f"[btd6_paragon_stats normal] {name} at Degree 100 (max): "
            f"{_sanitise(', '.join(max_bits)) if max_bits else 'see base'}; "
            f"boss-damage multiplier ×{boss} "
            f"(stats scale per degree 1-100; source: {src})",
        ),
    )
    # The two anchors above are endpoints, not a line: spell out the real
    # (non-linear) curve so the model doesn't interpolate Degree 1<->100 linearly.
    lines.append(
        _cap(
            "[btd6_paragon_stats scaling] Paragon stats do NOT scale linearly "
            "with degree — never interpolate linearly between Degree 1 and 100. "
            "Damage and pierce rise about +1% of base per degree, then jump to "
            "~2x base (base*2+10) at Degree 100.",
        ),
    )
    lines.append(
        _cap(
            "[btd6_paragon_stats scaling] Attack speed is a square-root curve: "
            "cooldown = rate / (1 + 0.01*sqrt(50*(degree-1))), so early degrees "
            "gain most. Boss-damage steps every 20 degrees (1.0 to 2.0), 2.25 "
            "at Degree 100.",
        ),
    )
    return lines


def _render_tower_stats(tower_id: str, canonical: str) -> list[str]:
    """Per-tier headline stats as ``[btd6_tower_stats normal]`` grounding lines.

    Tagged ``normal`` so the assistant can distinguish the glanceable stats it
    has here from the deeper Pro breakdown surfaced in the tower UI. Returns
    nothing for economy towers (no combat stats) or towers without a stats file.
    """
    from services import btd6_stats_service

    stats = btd6_stats_service.get_tower_stats(tower_id)
    if stats is None or not stats.has_combat_stats:
        return []

    lines: list[str] = []
    for code in stats.tier_codes():
        # Grounding stays bounded to the 16 single-path tiers; crosspaths are a
        # UI / Pro-view concern and would bloat the prompt with ~64 lines.
        if not (tier_codes.is_base(code) or tier_codes.is_single_path(code)):
            continue
        tier = stats.tier(code)
        if tier is None:
            continue
        ns = btd6_stats_service.normal_stats(tier)
        bits = _normal_stat_bits(ns)
        if not bits:
            continue
        crosspath = "-".join(code)
        name = "Base" if code == "000" else _tier_name(stats, code)
        lines.append(
            _cap(
                f"[btd6_tower_stats normal] {canonical} {name} ({crosspath}): "
                f"{_sanitise(', '.join(bits))} (source: bloonswiki)",
            ),
        )
    return lines


def _normal_stat_bits(ns: Any) -> list[str]:
    """Shared 'normal view' bits for a tier or hero-level node.

    Damage (with the immunity note folded in, exactly as the tower UI does —
    this is what answers "can it pop Lead?"), pierce, cooldown, camo detection
    (previously extracted but dropped from grounding), and headline specials.
    """
    bits: list[str] = []
    if ns.damage is not None:
        dmg = f"{_big(ns.damage)} dmg"
        if ns.damage_type:
            note = "pops everything" if ns.damage_type == "Normal" else ns.cannot_pop
            dmg += f" ({ns.damage_type}{f', {note}' if note else ''})"
        bits.append(dmg)
    if ns.pierce is not None:
        bits.append(f"{_big(ns.pierce)} pierce")
    if ns.cooldown is not None:
        bits.append(f"{ns.cooldown}s cooldown")
    # Camo detection only matters for attacking tiers; surface it like the UI.
    if ns.damage is not None:
        bits.append("sees Camo" if ns.can_see_camo else "no Camo detection")
    if ns.specials:
        bits.append("; ".join(ns.specials))
    return bits


# Headline hero levels for AI grounding — start, the two usual ability tiers,
# and max. Keeps the (verbose) stat lines bounded rather than dumping all 20.
_HERO_GROUNDING_LEVELS: tuple[str, ...] = ("1", "3", "10", "20")
# All hero levels, in order — used for the short per-level *description* lines
# (which, unlike stats, are surfaced for every level a hero defines).
_HERO_LEVEL_CODES_ALL: tuple[str, ...] = tuple(str(n) for n in range(1, 21))


def _render_hero_stats(hero_id: str, canonical: str) -> list[str]:
    """Per-level headline stats as ``[btd6_hero_stats normal]`` grounding lines.

    Returns nothing for heroes without a stats module (the prose-only majority);
    only the ~6 heroes with a bloonswiki module produce lines here.
    """
    from services import btd6_stats_service

    stats = btd6_stats_service.get_hero_stats(hero_id)
    if stats is None or not stats.has_combat_stats:
        return []

    lines: list[str] = []
    for code in _HERO_GROUNDING_LEVELS:
        node = stats.level(code)
        if node is None:
            continue
        bits = _normal_stat_bits(btd6_stats_service.normal_stats(node))
        if not bits:
            continue
        lines.append(
            _cap(
                f"[btd6_hero_stats normal] {canonical} Level {code}: "
                f"{_sanitise(', '.join(bits))} (source: bloonswiki)",
            ),
        )
    return lines


def _render_hero_descriptions(hero_id: str, canonical: str) -> list[str]:
    """Per-level game-authored prose as ``[btd6_hero_level]`` grounding lines.

    Heroes have no upgrade cards — they level 1..20, and the game stores a
    description per level (e.g. *Ezili L11 → "+50% pierce to reanimated
    Bloons"*). Unlike the verbose stat lines (bounded to 4 headline levels),
    these are short, so every level a hero defines is surfaced — making
    "what does <hero> level N do?" answerable for any N — bounded by the
    20-level max and emitted only for a specifically-named hero.
    """
    from services import btd6_stats_service

    stats = btd6_stats_service.get_hero_stats(hero_id)
    if stats is None:
        return []
    suffix = " (source: BTD6 in-game description)"
    lines: list[str] = []
    for code in _HERO_LEVEL_CODES_ALL:
        node = stats.level(code)
        if not isinstance(node, dict):
            continue
        desc = _sanitise(node.get("description", "") or "")
        if not desc:
            continue
        # Budget the prose so the provenance suffix always survives — _cap would
        # otherwise chop the source label off a long description.
        prefix = f"[btd6_hero_level] {canonical} Level {code}: "
        budget = _FACT_TEXT_CAP - len(prefix) - len(suffix)
        if budget < len(desc):
            desc = desc[: max(budget - 1, 0)].rstrip() + "…"
        lines.append(f"{prefix}{desc}{suffix}")
    return lines


def _big(value: int) -> str:
    """Render BTD6's 9,999,999 'infinite' sentinel as ∞."""
    return "∞" if _is_infinite(value) else str(value)


def _tier_name(stats: Any, code: str) -> str:
    path = tier_codes.primary_path(code)
    if path is None:
        return code
    tier = tier_codes.digits(code)[path - 1]
    return next(
        (
            str(u.get("name", ""))
            for u in stats.upgrades
            if u.get("path") == path and u.get("tier") == tier
        ),
        code,
    )


def _render_tower_crosspath(tower_id: str, canonical: str, code: str) -> list[str]:
    """One ``[btd6_tower_stats normal]`` line for a specifically-named crosspath.

    Crosspaths are kept out of default grounding for size; when a user names one
    (e.g. "0-2-5 ninja") this surfaces just that tier's headline stats.
    """
    from services import btd6_stats_service

    stats = btd6_stats_service.get_tower_stats(tower_id)
    if stats is None:
        return []
    tier = stats.tier(code)
    if tier is None:
        return []
    bits = _normal_stat_bits(btd6_stats_service.normal_stats(tier))
    if not bits:
        return []
    name = _tier_name(stats, code)
    return [
        _cap(
            f"[btd6_tower_stats normal] {canonical} {name} "
            f"({tier_codes.format_code(code)}): {_sanitise(', '.join(bits))} "
            "(source: bloonswiki)",
        ),
    ]


def _render_fixture_hero(entry: Any) -> list[str]:
    """Render a HeroEntry as 1-3 grounding lines for the AI context."""
    canonical = _sanitise(
        getattr(entry, "canonical", "") or str(getattr(entry, "id", "")),
    )
    cost = getattr(entry, "base_cost", None)
    description = _sanitise(getattr(entry, "description", "") or "")
    abilities = getattr(entry, "abilities", ()) or ()
    lines: list[str] = []

    cost_str = f"base cost: {cost} (medium difficulty)" if cost else ""
    lines.append(
        (
            _cap(f"[btd6_hero] {canonical} — {cost_str} (source: fixture/btd6_data)")
            if cost_str
            else _cap(f"[btd6_hero] {canonical} (source: fixture/btd6_data)")
        ),
    )

    for ability in abilities:
        name = _sanitise(getattr(ability, "name", "") or "")
        summary = _sanitise(getattr(ability, "summary", "") or "")
        level = getattr(ability, "level", "?")
        if name:
            ab_str = f"ability@{level}: {name}"
            if summary:
                ab_str += f" — {summary}"
            lines.append(
                _cap(f"[btd6_hero] {canonical} {ab_str} (source: fixture/btd6_data)"),
            )

    if description:
        lines.append(
            _cap(
                f"[btd6_hero] {canonical} — {description} (source: fixture/btd6_data)",
            ),
        )

    hero_id = getattr(entry, "id", "")
    lines.extend(_render_hero_stats(hero_id, canonical))
    lines.extend(_render_hero_descriptions(hero_id, canonical))
    return lines


def _render_fixture_bloon(entry: Any) -> list[str]:
    """Render a BloonEntry as 1-3 ``[btd6_bloon]``-tagged grounding lines.

    Surfaces the facts BTD6 reliability questions hinge on: damage-type
    immunities, trait properties (camo / lead / fortified / MOAB-class),
    health, and what the bloon pops into.
    """
    canonical = _sanitise(
        getattr(entry, "canonical", "") or str(getattr(entry, "id", "")),
    )
    category = _sanitise(str(getattr(entry, "category", "") or ""))
    description = _sanitise(getattr(entry, "description", "") or "")
    immune_to = tuple(getattr(entry, "immune_to", ()) or ())
    properties = tuple(getattr(entry, "properties", ()) or ())
    popped_by = _sanitise(getattr(entry, "popped_by", "") or "")
    children = _sanitise(getattr(entry, "children", "") or "")
    health = getattr(entry, "health", None)
    health_fortified = getattr(entry, "health_fortified", None)
    rbe = getattr(entry, "rbe", None)
    rbe_fortified = getattr(entry, "rbe_fortified", None)
    speed = getattr(entry, "speed", None)

    lines: list[str] = []

    # Line 1: identity + category + immunities (the headline reliability fact).
    head_bits: list[str] = []
    if category:
        head_bits.append(f"category: {category}")
    if immune_to:
        head_bits.append(f"immune to {', '.join(_sanitise(d) for d in immune_to)}")
    elif category not in {"modifier", ""}:
        head_bits.append("no damage-type immunity")
    if popped_by:
        head_bits.append(f"popped by {popped_by}")
    meta = " | ".join(head_bits)
    lines.append(
        _cap(
            (
                f"[btd6_bloon] {canonical} — {meta} (source: fixture/btd6_data)"
                if meta
                else f"[btd6_bloon] {canonical} (source: fixture/btd6_data)"
            ),
        ),
    )

    # Line 2: stats — properties, health/RBE/speed, children.
    stat_bits: list[str] = []
    if properties:
        stat_bits.append(f"properties: {', '.join(_sanitise(p) for p in properties)}")
    if isinstance(health, int):
        hp = f"health: {health}"
        if isinstance(health_fortified, int):
            hp += f" ({health_fortified} fortified)"
        stat_bits.append(hp)
    if isinstance(rbe, int):
        rbe_bit = f"RBE (total hits incl. all spawned children): {rbe}"
        if isinstance(rbe_fortified, int):
            rbe_bit += f" ({rbe_fortified} fortified)"
        stat_bits.append(rbe_bit)
    if isinstance(speed, (int, float)):
        stat_bits.append(f"speed: {speed}")
    if children:
        stat_bits.append(f"pops into {children}")
    elif category not in {"modifier", ""}:
        stat_bits.append("pops into nothing (bottom of the spawn chain)")
    if stat_bits:
        lines.append(
            _cap(
                f"[btd6_bloon] {canonical} — {' | '.join(stat_bits)} "
                "(source: fixture/btd6_data)",
            ),
        )

    if description:
        lines.append(
            _cap(
                f"[btd6_bloon] {canonical} — {description} (source: fixture/btd6_data)",
            ),
        )

    return lines


def _render_fixture_round(entry: Any) -> list[str]:
    """Render a RoundEntry as 1-3 ``[btd6_round]`` grounding lines.

    Surfaces the facts round questions hinge on: danger, total (children-
    inclusive) RBE, the exact spawn composition, and any curated strategy note.
    Only resolver-matched round(s) are rendered, so grounding stays bounded.
    """
    from services import btd6_data_service

    number = getattr(entry, "round_number", None)
    if number is None:
        return []
    danger = _sanitise(str(getattr(entry, "danger", "") or ""))
    rbe = getattr(entry, "rbe", None)
    threats = tuple(getattr(entry, "common_threats", ()) or ())
    summary = _sanitise(getattr(entry, "summary", "") or "")
    groups = tuple(getattr(entry, "groups", ()) or ())

    head: list[str] = []
    if danger:
        head.append(f"danger: {danger}")
    if isinstance(rbe, int):
        head.append(f"total RBE {rbe:,} (hits to fully clear)")
    cash = getattr(entry, "cash", None)
    if isinstance(cash, (int, float)):
        cumulative = getattr(entry, "cumulative_cash", None)
        bit = f"cash this round ~${round(cash):,}"
        if isinstance(cumulative, (int, float)):
            bit += f", cumulative ~${round(cumulative):,}"
        # Standard/Medium base economy: ~$1 per bloon pop + end-of-round bonus,
        # before any income towers, and halved under Half Cash.
        head.append(bit + " (standard economy, no income towers)")
    if threats:
        head.append(f"threats: {', '.join(_sanitise(t) for t in threats)}")
    headline = " | ".join(head)
    lines = [
        _cap(
            (
                f"[btd6_round] Round {number} — {headline} (source: fixture/btd6_data)"
                if headline
                else f"[btd6_round] Round {number} (source: fixture/btd6_data)"
            ),
        ),
    ]

    # Exact composition: aggregate the ordered spawn groups by bloon + modifiers.
    aggregated: dict[tuple[str, tuple[str, ...]], int] = {}
    order: list[tuple[str, tuple[str, ...]]] = []
    for group in groups:
        key = (str(group.get("bloon_id", "")), tuple(group.get("modifiers", ()) or ()))
        if key not in aggregated:
            aggregated[key] = 0
            order.append(key)
        aggregated[key] += int(group.get("count", 0))
    if order:
        parts: list[str] = []
        for bloon_id, modifiers in order:
            record = btd6_data_service.get_bloon(bloon_id)
            name = record.canonical if record is not None else bloon_id.title()
            prefix = " ".join(m.capitalize() for m in modifiers)
            label = f"{prefix} {name}".strip()
            parts.append(f"{aggregated[(bloon_id, modifiers)]} {label}")
        lines.append(
            _cap(
                f"[btd6_round] Round {number} composition — "
                f"{_sanitise(', '.join(parts))} (source: fixture/btd6_data)",
            ),
        )

    # Curated strategy blurb (skip the auto-generated "N Lead, M Ceramic…" ones).
    if summary and not summary[0].isdigit():
        lines.append(
            _cap(
                f"[btd6_round] Round {number} — {summary} (source: fixture/btd6_data)",
            ),
        )
    return lines


def _cap(text: str) -> str:
    """Truncate ``text`` to ``_FACT_TEXT_CAP`` characters."""
    return text if len(text) <= _FACT_TEXT_CAP else text[: _FACT_TEXT_CAP - 1] + "…"


def _render_ct_relic(entry: Any) -> list[str]:
    """One ``[btd6_ct_relic]`` grounding line: relic name + paraphrased effect.

    The catalog is static knowledge (the Ninja Kiwi API stores relic
    names only), so this runs in the always-on fixture pass.
    """
    canonical = _sanitise(
        getattr(entry, "canonical", "") or str(getattr(entry, "id", "")),
    )
    if not canonical:
        return []
    abbrev = _sanitise(getattr(entry, "abbrev", "") or "")
    effect = _sanitise(getattr(entry, "effect", "") or "")
    name = f"{canonical} ({abbrev})" if abbrev else canonical
    if not effect:
        return []
    return [_cap(f"[btd6_ct_relic] {name} — {effect} (source: bloonswiki)")]


async def _ct_relic_location_lines(intent: Any) -> list[str]:
    """``[btd6_ct_tile]`` lines: where each named relic sits in active CTs.

    Bounded at 8 lines so a relic that appears on many tiles across many
    active events cannot flood the prompt.
    """
    relics = getattr(intent, "ct_relics", ()) or ()
    if not relics:
        return []
    from services import btd6_live_query_service as btd6_live

    out: list[str] = []
    for relic in relics:
        relic_id = str(getattr(relic, "id", "") or "")
        canonical = _sanitise(getattr(relic, "canonical", "") or relic_id)
        if not relic_id:
            continue
        for placement in (await btd6_live.find_relic_locations(relic_id))[:6]:
            pos = (
                placement.position.describe() if placement.position else "position n/a"
            )
            rel = _relative_time(placement.fetched_at)
            mode = (
                f", {_sanitise(placement.game_type)} battle"
                if placement.game_type
                else ""
            )
            out.append(
                _cap(
                    f"[btd6_ct_tile] {canonical} is on tile {placement.tile_id} "
                    f"({pos}{mode}) in CT event {placement.ct_id}; captured-tile "
                    f"relic bonus (source: data.ninjakiwi.com, fetched {rel})",
                ),
            )
            if len(out) >= 8:
                return out
    return out


# A general Contested-Territory topic — the user is asking about CT relics
# or tile layout without naming a specific relic ("what relics are in the
# current CT", "tiles and relics", …). Matched on the raw message so the
# listing fires even when no catalog relic alias appears in the text.
_CT_TOPIC_RE = re.compile(r"\b(relics?|tiles?|contested\s+territor)", re.IGNORECASE)


def _mentions_ct_topic(intent: Any) -> bool:
    if _CT_TOPIC_RE.search(getattr(intent, "raw_text", "") or ""):
        return True
    for entity in getattr(intent, "live_entities", ()) or ():
        kind = getattr(entity, "entity_kind", entity)
        if kind in ("btd6_ct", "btd6_ct_tile"):
            return True
    return False


# CT tile listing bounds. A CT map is 169 tiles, of which ~24 carry relics and
# the rest are plain battle / banner tiles. We list every relic tile in full
# (bounded generously above 24 so even two concurrently-active CT events are
# never truncated) but summarise the plain tiles as counts rather than 145
# individual lines, so a "list all tiles" answer stays readable.
_CT_TILE_LINE_CAP = 48
_CT_RELIC_EFFECT_CAP = 24
# A specific tile named by its code is a focused lookup; bound it so a message
# that happens to contain many tile-code-shaped tokens can't flood the prompt.
_CT_SPECIFIC_TILE_CAP = 8

# A 3-letter CT tile code (e.g. "DEC", "MRX", "FAH"). Deliberately liberal — a
# candidate is only grounded when it also equals a real tile id in the live
# event, so ordinary 3-letter words ("all", "you") drop out at that
# intersection rather than via a brittle structural rule that would also miss
# any Ninja Kiwi code quirk.
_TILE_CODE_RE = re.compile(r"\b[A-Za-z]{3}\b")


def _tile_codes_in_text(text: str) -> set[str]:
    """Upper-cased 3-letter tokens from ``text`` that might be tile codes."""
    return {m.group(0).upper() for m in _TILE_CODE_RE.finditer(text or "")}


def _humanize_label(value: str) -> str:
    """Split a CamelCase API token for display: ``LeastCash`` -> ``Least Cash``."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value).strip()


def _ct_tile_breakdown_lines(ct_id: str, tiles: Sequence[Any]) -> list[str]:
    """Two ``[btd6_ct_map]`` lines: total tile count, by type and by battle mode.

    A CT map is 169 tiles but only ~24 carry relics; the rest are plain
    battle / banner tiles. Grounding the real inventory lets the model answer
    "how many tiles" / "list all tiles" from the true total and stop implying
    the lookup is truncating once it has returned the complete relic set.
    """
    if not tiles:
        return []
    by_type: Counter[str] = Counter()
    by_mode: Counter[str] = Counter()
    fetched = None
    for tile in tiles:
        by_type[_humanize_label(str(getattr(tile, "tile_type", None) or "Other"))] += 1
        mode = getattr(tile, "game_type", None)
        if mode:
            by_mode[_humanize_label(str(mode))] += 1
        fetched = fetched or getattr(tile, "fetched_at", None)

    def _counts(counter: Counter[str]) -> str:
        return ", ".join(
            f"{n} {label}"
            for label, n in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
        )

    cid = _sanitise(ct_id)
    out = [
        _cap(
            f"[btd6_ct_map] CT {cid}: {sum(by_type.values())} tiles total — "
            f"{_counts(by_type)} (source: data.ninjakiwi.com, "
            f"fetched {_relative_time(fetched)})",
        ),
    ]
    if by_mode:
        out.append(
            _cap(
                f"[btd6_ct_map] CT {cid}: battle modes — {_counts(by_mode)} "
                f"(source: data.ninjakiwi.com)",
            ),
        )
    return out


def _render_ct_tile_full(ct_id: str, tile: Any) -> str:
    """A ``[btd6_ct_tile]`` line for one tile of *any* type (specific lookup)."""
    pos = (
        tile.position.describe() if getattr(tile, "position", None) else "position n/a"
    )
    ttype = _humanize_label(str(getattr(tile, "tile_type", None) or "tile"))
    relic = _sanitise(
        getattr(tile, "relic_canonical", None)
        or getattr(tile, "relic_name", None)
        or "",
    )
    carries = f" carrying {relic}" if relic else ""
    mode = getattr(tile, "game_type", None)
    mode_bit = f" — {_humanize_label(_sanitise(str(mode)))} battle" if mode else ""
    return _cap(
        f"[btd6_ct_tile] CT {_sanitise(ct_id)}: tile {_sanitise(tile.tile_id)} "
        f"({pos}) — {ttype}{carries}{mode_bit} (source: data.ninjakiwi.com)",
    )


def _specific_tile_lines(
    ct_id: str,
    tiles: Sequence[Any],
    wanted_codes: set[str],
) -> list[str]:
    """Detailed lines for tiles whose code the query named.

    Matches any tile type (relic or plain) but only when the code equals a
    real tile id, so a 3-letter word that isn't a tile grounds nothing.
    """
    if not wanted_codes:
        return []
    out: list[str] = []
    for tile in tiles:
        if str(getattr(tile, "tile_id", "")) in wanted_codes:
            out.append(_render_ct_tile_full(ct_id, tile))
            if len(out) >= _CT_SPECIFIC_TILE_CAP:
                break
    return out


def _relic_tile_lines(
    ct_id: str,
    tiles: Sequence[Any],
    seen_relics: list[str],
) -> list[str]:
    """One ``[btd6_ct_tile]`` line per relic tile; records distinct relic ids."""
    out: list[str] = []
    cid = _sanitise(ct_id)
    for tile in tiles:
        if getattr(tile, "relic_name", None) is None:
            continue
        canonical = _sanitise(tile.relic_canonical or tile.relic_name or "?")
        pos = tile.position.describe() if tile.position else "position n/a"
        mode = f" — {_sanitise(tile.game_type)} battle" if tile.game_type else ""
        out.append(
            _cap(
                f"[btd6_ct_tile] CT {cid}: {canonical} "
                f"on tile {_sanitise(tile.tile_id)} ({pos}){mode} "
                f"(source: data.ninjakiwi.com)",
            ),
        )
        if tile.relic_id and tile.relic_id not in seen_relics:
            seen_relics.append(tile.relic_id)
        if len(out) >= _CT_TILE_LINE_CAP:
            break
    return out


async def _ct_active_tile_lines(intent: Any) -> list[str]:
    """Active-CT tile inventory for a *general* CT relic/tile question.

    When a specific relic is named, :func:`_ct_relic_location_lines` gives the
    targeted answer, so this broad listing is skipped to avoid duplication.
    Otherwise it grounds, for the newest active CT event(s): the true tile
    inventory (total + per-type / per-mode counts), every relic tile in full,
    the effect of each distinct relic found, and a detailed line for any
    specific tile the query named by code. Each part is bounded so even a full
    169-tile map cannot flood the prompt.
    """
    if getattr(intent, "ct_relics", ()):  # specific relic handled elsewhere
        return []
    if not _mentions_ct_topic(intent):
        return []

    from services import btd6_data_service

    out: list[str] = []
    seen_relics: list[str] = []
    wanted_codes = _tile_codes_in_text(getattr(intent, "raw_text", "") or "")
    # Live tile placements — guarded so a DB outage falls through to the
    # static catalog below rather than aborting the whole CT answer.
    try:
        from services import btd6_live_query_service as btd6_live

        events = await btd6_live.get_active_events(("btd6_ct",))
        for evt in events[:2]:
            tiles = await btd6_live.get_ct_tiles(evt.entity_key)
            if not tiles:
                continue
            out.extend(_ct_tile_breakdown_lines(evt.entity_key, tiles))
            out.extend(_specific_tile_lines(evt.entity_key, tiles, wanted_codes))
            out.extend(_relic_tile_lines(evt.entity_key, tiles, seen_relics))
    except Exception as exc:  # noqa: BLE001 — degrade to the static catalog
        logger.debug("btd6_context_service: ct live tiles unavailable (%s)", exc)

    # The effect of each distinct relic actually on the map, so the model
    # can answer "what does it do" follow-ups without a second round-trip.
    for relic_id in seen_relics[:_CT_RELIC_EFFECT_CAP]:
        entry = btd6_data_service.get_ct_relic(relic_id)
        if entry is not None:
            out.extend(_render_ct_relic(entry))

    # No live tile data (DB not yet populated) — fall back to the static
    # relic catalog so a general "tell me about the relics" question still
    # gets the verified relic effects instead of an "I don't have it".
    if not out:
        for relic in btd6_data_service.list_ct_relics():
            out.extend(_render_ct_relic(relic))
    return out


_ROSTER_INTENT = (
    "all paragon",
    "list paragon",
    "which paragon",
    "every paragon",
    "how many paragon",
    "each paragon",
    "name the paragon",
    "name all paragon",
)


def _paragon_roster_facts(message_text: str) -> list[str]:
    """Ground the authoritative 13-paragon roster for roster-level questions.

    A general "which paragons …" / "list all paragons" question otherwise lets
    the model invent paragons — it has listed HEROES (which have no paragon) and
    fake names. Pin the real 13 and the rule that only towers have paragons.
    """
    from utils.btd6 import paragon_math

    text = (message_text or "").lower()
    if "paragon" not in text:
        return []
    if "paragons" not in text and not any(kw in text for kw in _ROSTER_INTENT):
        return []
    names = [p.name.split(" (")[0].strip() for p in paragon_math.PARAGONS]
    lines = [
        "[btd6_paragon_roster] BTD6 has exactly 13 paragons (tier-6 super-"
        "upgrades), one per tower. ONLY towers have paragons — a hero (Quincy, "
        "Gwendolin, Adora, Benjamin, …) is NEVER a paragon; never list heroes "
        "as paragons.",
    ]
    prefix = "[btd6_paragon_roster] The 13: "
    line = prefix
    for name in names:
        addition = name if line == prefix else f", {name}"
        if len(line) + len(addition) > 230:
            lines.append(line)
            line = prefix + name
        else:
            line += addition
    lines.append(line)
    return lines


# Roster-intent verbs for the hero/tower roster grounding. Heroes and towers
# have no ``_paragon_roster_facts`` equivalent, so a "list all heroes" / "which
# towers" question reached the model with ZERO grounding facts — and the
# answer-faithfulness guard then refused the model's (correct) roster as
# ungrounded. Gated on the entity word so ordinary entity questions
# ("dart monkey stats") never trip it.
_ENTITY_ROSTER_VERBS = (
    "list ",
    "all ",
    "which ",
    "every ",
    "how many",
    "name the",
    "name all",
    "name every",
    "what are the",
    "what heroes",
    "what towers",
    "each ",
)


def _roster_lines(kind: str, count: int, entries: list[str], note: str) -> list[str]:
    """Chunk a roster into <=230-char grounding lines tagged by ``kind``.

    Each entry carries its base cost (and, for towers, its category) so a roster
    answer that lists costs — as the model naturally does — grounds. Name-only
    facts left the cost numbers unsupported, which refused the whole roster.
    """
    if not entries:
        return []
    plural = "heroes" if kind == "hero" else f"{kind}s"
    head = (
        f"[btd6_{kind}_roster] BTD6 has {count} {plural} ({note}) — the complete "
        f"list (state these verbatim; never invent or omit one):"
    )
    lines = [head]
    prefix = f"[btd6_{kind}_roster] "
    line = prefix
    for entry in entries:
        addition = entry if line == prefix else f", {entry}"
        if len(line) + len(addition) > 230:
            lines.append(line)
            line = prefix + entry
        else:
            line += addition
    lines.append(line)
    return lines


def _entity_roster_facts(message_text: str) -> list[str]:
    """Ground the authoritative hero / tower roster for roster-level questions.

    Mirrors :func:`_paragon_roster_facts` for the two catalogs that lacked it.
    "which heroes are in the game" / "list all towers" otherwise produce no
    grounding facts at all, so the model's correct roster reads as ungrounded
    and is refused by the faithfulness guard. Pin the real roster, count, and
    each entry's base cost (+ tower category) so a cost-listing answer grounds —
    independent of ``AI_TOOLS_ENABLED`` and of whether the model calls
    ``btd6_list_roster``.
    """
    text = (message_text or "").lower()
    if not any(verb in text for verb in _ENTITY_ROSTER_VERBS):
        return []
    from services import btd6_data_service

    dataset = btd6_data_service.get_dataset()
    out: list[str] = []
    if "hero" in text:
        entries = [
            (
                f"{h.canonical} (${h.base_cost})"
                if getattr(h, "base_cost", None)
                else h.canonical
            )
            for h in dataset.heroes
        ]
        out.extend(
            _roster_lines(
                "hero",
                len(dataset.heroes),
                entries,
                "$ = base placement cost, medium difficulty",
            ),
        )
    if "tower" in text:
        entries = [
            (
                f"{t.canonical} (${t.base_cost}, {t.category})"
                if getattr(t, "base_cost", None)
                else t.canonical
            )
            for t in dataset.towers
        ]
        out.extend(
            _roster_lines(
                "tower",
                len(dataset.towers),
                entries,
                "$ = base placement cost (medium); category = "
                "primary/military/magic/support",
            ),
        )
    if "map" in text:
        # Counts are a single grounded summary (not 89 names): "how many maps",
        # "by difficulty", and "how many have water" all answer from it. Without
        # it the model recited stale training counts (25/28/22/14, "~73 water")
        # and even labelled them "verified" — the real figures are below.
        maps = dataset.maps
        water = sum(1 for m in maps if m.has_water)
        order = ("Beginner", "Intermediate", "Advanced", "Expert")
        diff_str = ", ".join(
            f"{c} {d}"
            for d in order
            if (c := sum(1 for m in maps if m.difficulty == d))
        )
        out.append(
            _cap(
                f"[btd6_map] BTD6 has {len(maps)} maps total: {diff_str}. "
                f"{water} have water (naval towers placeable), "
                f"{len(maps) - water} are land-only. (source: fixture/btd6_data)",
            ),
        )
    return out


# Strategy / opinion words → the user wants a recommendation, not an
# enumeration. The model handles those; the deterministic roster must NOT fire.
_ROSTER_STRATEGY_WORDS = (
    "best",
    "worst",
    "should",
    "good for",
    "recommend",
    "better",
    " vs ",
    "versus",
    "against",
    "counter",
    "strateg",
    "tier list",
    "for round",
)

# Phrases that clearly request a complete enumeration.
_ROSTER_LIST_INTENT = (
    "list",
    "how many",
    "name all",
    "name every",
    "name the",
    "are there",
    "in the game",
    "exist",
    "all of the",
    "what are all",
)


def deterministic_roster_reply(message_text: str) -> str | None:
    """A clean, code-built roster for a clear LIST request, or ``None``.

    Heroes / towers / paragons enumerated deterministically from the dataset,
    so the answer is always correct and never tripped by the faithfulness guard
    (it *is* the source). The natural-language stage sends this as the floor for
    a roster-list question — the model cannot reliably restate 17+ costs
    verbatim, so a single mismatched cost refused the whole list. Returns
    ``None`` for strategy/opinion questions ("which hero is best") so those
    still reach the model, and for anything that is not a clear enumeration.
    """
    text = (message_text or "").lower()
    if any(word in text for word in _ROSTER_STRATEGY_WORDS):
        return None
    is_list = any(phrase in text for phrase in _ROSTER_LIST_INTENT) or (
        "all " in text or "every " in text
    )
    if not is_list:
        return None

    from services import btd6_data_service

    dataset = btd6_data_service.get_dataset()

    if "paragon" in text:
        from utils.btd6 import paragon_math

        lines = [
            f"• **{paragon.name}** — {paragon.tower} "
            f"(${paragon.base_price_medium:,})"
            for paragon in paragon_math.PARAGONS
        ]
        return (
            f"**BTD6 Paragons ({len(lines)})** — one per eligible tower, "
            "base price on medium:\n" + "\n".join(lines)
        )

    if "hero" in text:
        lines = [
            (
                f"• **{hero.canonical}** — ${hero.base_cost}"
                if getattr(hero, "base_cost", None)
                else f"• **{hero.canonical}**"
            )
            for hero in dataset.heroes
        ]
        return (
            f"**BTD6 Heroes ({len(lines)})** — base placement cost (medium):"
            "\n" + "\n".join(lines)
        )

    if "tower" in text:
        cats = [c for c in ("primary", "military", "magic", "support") if c in text]
        towers = [t for t in dataset.towers if not cats or t.category in cats]
        if not towers:
            return None
        if cats:
            label = "/".join(c.capitalize() for c in cats)
            body = "\n".join(f"• **{t.canonical}** — ${t.base_cost}" for t in towers)
            return (
                f"**BTD6 {label} Towers ({len(towers)})** — base cost "
                "(medium):\n" + body
            )
        out: list[str] = [f"**BTD6 Towers ({len(towers)})** — base cost (medium):"]
        for cat in ("primary", "military", "magic", "support"):
            group = [t for t in towers if t.category == cat]
            if not group:
                continue
            out.append(f"__{cat.capitalize()}__")
            out.extend(f"• **{t.canonical}** — ${t.base_cost}" for t in group)
        return "\n".join(out)

    return None


def _paragon_name_facts(message_text: str, resolved_tower_ids: set[str]) -> list[str]:
    """Ground a paragon named directly (e.g. "what are Glaive Dominus's stats?").

    The resolver keys on towers/heroes, not paragon names, so a question naming
    only the paragon would otherwise get no paragon grounding. Match on the full
    paragon name (distinctive enough to avoid tower-name false positives) and emit
    the same name + cost + stats lines, skipping any tower already grounded via
    the resolved intent so nothing is duplicated.
    """
    from services import btd6_stats_service
    from utils.btd6 import paragon_math

    text = (message_text or "").lower()
    out: list[str] = []
    grounded: set[str] = set(resolved_tower_ids)
    for paragon in paragon_math.PARAGONS:
        # Strip a parenthetical (e.g. "… (B.O.M.B.)") and match the bare name.
        name = paragon.name.split(" (")[0].strip().lower()
        if not name or name not in text:
            continue
        pstats = btd6_stats_service.get_paragon_stats(paragon.paragon_id)
        if pstats is None or pstats.tower_id in grounded:
            continue
        grounded.add(pstats.tower_id)
        out.extend(_render_paragon(pstats.tower_id, pstats.tower_canonical))

    # A paragon ABILITY named directly (e.g. "Spikeageddon cooldown", "what does
    # Final Strike do") — the names are distinctive, so a full-name substring
    # match grounds the owning paragon (and its ability lines) without false hits.
    for paragon_id in btd6_stats_service.list_paragon_ids():
        pstats = btd6_stats_service.get_paragon_stats(paragon_id)
        if pstats is None or pstats.tower_id in grounded:
            continue
        if any(ab.name and ab.name.lower() in text for ab in pstats.abilities):
            grounded.add(pstats.tower_id)
            out.extend(_render_paragon(pstats.tower_id, pstats.tower_canonical))
    return out


def _fixture_facts_for_intent(intent: Any) -> list[str]:
    """Return fixture-sourced grounding lines for any tower/hero/bloon in ``intent``.

    Called when the DB returns no rows for a matched entity so the AI
    still gets cost, category, upgrade/ability, and bloon-immunity data
    from the JSON fixture files.
    """
    try:
        from services import btd6_data_service
    except Exception:  # noqa: BLE001
        return []

    lines: list[str] = []
    crosspaths = _crosspaths_in_text(str(getattr(intent, "raw_text", "") or ""))
    for tower in getattr(intent, "towers", ()) or ():
        tower_id = str(getattr(tower, "id", "") or "")
        if not tower_id:
            continue
        record = btd6_data_service.get_tower(tower_id)
        if record is not None:
            lines.extend(_render_fixture_tower(record))
            for code in crosspaths:
                lines.extend(_render_tower_crosspath(tower_id, record.canonical, code))
    for hero in getattr(intent, "heroes", ()) or ():
        hero_id = str(getattr(hero, "id", "") or "")
        if not hero_id:
            continue
        record = btd6_data_service.get_hero(hero_id)
        if record is not None:
            lines.extend(_render_fixture_hero(record))
    for bloon in getattr(intent, "bloons", ()) or ():
        bloon_id = str(getattr(bloon, "id", "") or "")
        if not bloon_id:
            continue
        record = btd6_data_service.get_bloon(bloon_id)
        if record is not None:
            lines.extend(_render_fixture_bloon(record))
    # Rounds resolve to full RoundEntry records already (composition + RBE), so
    # render them directly rather than re-fetching by number.
    for round_entry in getattr(intent, "rounds", ()) or ():
        lines.extend(_render_fixture_round(round_entry))
    # CT relics carry their static effect from the catalog.
    for relic in getattr(intent, "ct_relics", ()) or ():
        lines.extend(_render_ct_relic(relic))
    return lines


def _upgrade_parent_tower_facts(
    message_text: str,
    resolved_tower_ids: set[str],
) -> list[str]:
    """Ground an upgrade's PARENT TOWER when the text named the upgrade, not it.

    Upgrade names / abbreviations (PMFC, POD, BEZ, "Plasma Monkey Fan Club")
    resolve as upgrades, but the intent resolver does not extract their parent
    tower — so a conceptual question like "what's the damage type when PMFC's
    ability is active" attaches only the upgrade's few detail lines (Pass 3c)
    and nothing about the tower. With so little to stand on the model tends to
    refuse despite holding the upgrade fact. Attaching the parent tower's
    fixture grounding (the same rich context a tower-named query gets) closes
    that gap; ``resolved_tower_ids`` dedupes so a tower the user *did* name is
    never grounded twice.

    Retrieval only — see ``docs/btd6-absence-claim-guard-design.md`` §4.1
    (Layer A / mechanism 2). Returns ``[]`` when no upgrade resolves or the
    parent tower is already grounded.
    """
    try:
        from services import btd6_data_service, btd6_upgrade_service
    except Exception:  # noqa: BLE001 — defensive
        return []

    res = btd6_upgrade_service.resolve_upgrade(message_text)
    upgrade = getattr(res, "upgrade", None)
    if upgrade is None:
        return []
    tower_id = str(getattr(upgrade, "tower_id", "") or "")
    if not tower_id or tower_id in resolved_tower_ids:
        return []
    record = btd6_data_service.get_tower(tower_id)
    if record is None:
        return []
    resolved_tower_ids.add(tower_id)
    return _render_fixture_tower(record)


# Resolver live-entity kinds → coverage areas, for the grounding signals.
_LIVE_KIND_TO_COVERAGE: dict[str, str] = {
    "btd6_boss": cov.AREA_BOSS,
    "btd6_odyssey": cov.AREA_ODYSSEY,
    "btd6_race": cov.AREA_RACES,
    "btd6_leaderboard": cov.AREA_LEADERBOARDS,
}


def _freshness_signal(live_rows: list[dict[str, Any]]) -> str:
    """One ``[btd6_freshness]`` line describing live-event data freshness.

    Buckets the newest ``fetched_at`` across the fetched live rows. When no
    rows were found at all, says so explicitly — that absence is itself the
    signal that tells the model not to answer from memory.
    """
    from services.btd6_source_registry import bucket_freshness

    newest = None
    for row in live_rows:
        ts = row.get("fetched_at")
        if ts is not None and (newest is None or ts > newest):
            newest = ts
    if newest is None:
        return (
            "[btd6_freshness] No current live-event data is loaded for this "
            "question — do not answer current boss/race/odyssey/leaderboard "
            "questions from memory; say the live data isn't available."
        )
    bucket = bucket_freshness(newest)
    if bucket in ("stale", "never"):
        return (
            "[btd6_freshness] Live-event data is stale (last update over 24h "
            "ago) — it may not reflect the current event; do not fill gaps "
            "from memory."
        )
    if bucket == "aging":
        return (
            "[btd6_freshness] Live-event data is aging — confirm it is current "
            "before relying on it."
        )
    return "[btd6_freshness] Live-event data is fresh (updated within the last hour)."


def _coverage_freshness_signals(
    intent: Any,
    live_rows: list[dict[str, Any]],
) -> list[str]:
    """Coverage + freshness signal lines for the grounding bundle.

    Coverage: for each partial-coverage area the intent touches, emit a
    ``[btd6_coverage] …`` line straight from the shared registry so the model
    states the same limit users see (top-page-only leaderboards, etc.).

    Freshness: for live-event kinds the intent asks about, emit a
    ``[btd6_freshness] …`` line — the signal the ``_TASK_CONTRACT`` directive
    keys on to refuse answering current-event questions from training data.

    Returns RAW lines; wrapping as untrusted data happens later in
    ``ai_instruction_service.assemble`` — not here.
    """
    signals: list[str] = []

    live_kinds = {
        getattr(m, "entity_kind", None)
        for m in (getattr(intent, "live_entities", ()) or ())
    }
    live_kinds.discard(None)

    areas: list[str] = []
    for kind in sorted(k for k in live_kinds if k):
        area = _LIVE_KIND_TO_COVERAGE.get(kind)
        if area is not None and area not in areas:
            areas.append(area)
    if getattr(intent, "heroes", ()) and cov.AREA_HERO_STATS not in areas:
        areas.append(cov.AREA_HERO_STATS)

    for area in areas:
        signals.append(f"[btd6_coverage] {cov.get_coverage(area).user_label}")

    if live_kinds:
        signals.append(_freshness_signal(live_rows))
    return signals


async def build(message_text: str) -> BTD6Context:
    """Build a BTD6 context bundle for ``message_text``.

    Four passes, each isolated so one failure cannot suppress the others:

    1. Resolver (sync, no DB) — extracts towers/heroes/maps/modes/bloons
       from the text.
    2. DB-backed facts — live event rows from ``btd6_facts`` +
       active-event restriction lines.  Skipped silently when the DB is
       unavailable.
    3. Fixture fallback (always) — injects cost / upgrade / ability data
       for every resolved tower/hero entity and immunity / property data
       for every resolved bloon, from the JSON fixture files. This pass is
       deliberately OUTSIDE the DB try/except so a missing or misconfigured
       ``btd6_facts`` table never suppresses it.
    4. Coverage + freshness signals — appends the same data-limit copy users
       see, plus a freshness flag for live-event kinds, so the model states
       limits and won't answer stale/missing live-event questions from memory.
    """
    facts: list[str] = []
    live_rows: list[dict[str, Any]] = []
    confidence = 0.0
    source_summary = _FALLBACK_SOURCE_SUMMARY

    # Pass 1: resolve intent (synchronous, no DB required).
    intent = None
    try:
        from services import btd6_resolver_service

        intent = btd6_resolver_service.resolve(message_text)
        confidence = float(getattr(intent, "confidence", 0.0) or 0.0)
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.debug("btd6_context_service: resolver unavailable (%s)", exc)

    if intent is not None:
        # Pass 2: DB-backed live facts + active-event restrictions.
        try:
            from services import btd6_fact_store

            queries = _intent_to_queries(intent)
            rows = await btd6_fact_store.fetch_for_intent(queries) if queries else []
            # PR-E: race / boss / CT / odyssey / challenge / event /
            # leaderboard facts.
            live_rows = await _fetch_live_entity_rows(intent)
            rows = rows + live_rows
            for row in rows:
                facts.append(_render_fact(row))
            # PR 2: tower/hero active-event restriction lines.
            facts.extend(await _restriction_lines_for_intent(intent))
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug("btd6_context_service: db grounding unavailable (%s)", exc)

        # CT relic tile locations — isolated so a failure in the block
        # above (or vice-versa) can't suppress it. The query is already
        # self-guarding, returning () when the DB is unavailable.
        try:
            facts.extend(await _ct_relic_location_lines(intent))
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: ct relic locations unavailable (%s)",
                exc,
            )

        # General CT relic/tile topic (no specific relic named) — list the
        # active map's relic tiles so "tiles and relics" questions get the
        # breakdown the event index alone can't provide.
        try:
            facts.extend(await _ct_active_tile_lines(intent))
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: ct active tiles unavailable (%s)",
                exc,
            )

        # Pass 3: fixture fallback — always runs so cost, category,
        # and upgrade/ability data reach the LLM even when the DB has
        # no rows for tower/hero entities (the common state before live
        # ingestion populates btd6_facts).
        facts.extend(_fixture_facts_for_intent(intent))

        # Pass 3b: a paragon named directly (not via its tower) — the resolver
        # doesn't key on paragon names, so ground those too (deduped against
        # towers already grounded above).
        resolved_tower_ids = {
            str(getattr(tower, "id", "") or "")
            for tower in getattr(intent, "towers", ()) or ()
        }
        facts.extend(_paragon_name_facts(message_text, resolved_tower_ids))
        facts.extend(_paragon_roster_facts(message_text))
        facts.extend(_entity_roster_facts(message_text))

        # Pass 3c: upgrade grounding — an upgrade named in the text by name,
        # abbreviation / nickname (PMFC / POD / BEZ / Prince of Darkness), or
        # path notation ("wizard 005"). Grounds its identity + per-attack /
        # minion / buff detail so upgrade-specific questions resolve even when
        # the tower isn't also named. Isolated so a failure can't suppress the
        # rest; the resolver underneath is deterministic and dataset-only.
        try:
            from services import btd6_upgrade_detail_service

            facts.extend(
                btd6_upgrade_detail_service.grounding_for_query(message_text),
            )
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: upgrade grounding unavailable (%s)",
                exc,
            )

        # Pass 3d: parent-tower grounding for an upgrade-only query. When the
        # text names an upgrade (PMFC / POD / BEZ) but NOT its tower, Pass 3
        # grounds no tower and Pass 3c attaches only the upgrade's few detail
        # lines — too thin for a conceptual question ("what's the damage type
        # when PMFC's ability is active") to stand on, so the model refuses
        # despite holding the upgrade fact. Ground the parent tower (the same
        # context a tower-named query gets), deduped against towers already
        # grounded above. Retrieval only — see
        # docs/btd6-absence-claim-guard-design.md §4.1 (Layer A / mechanism 2).
        try:
            facts.extend(
                _upgrade_parent_tower_facts(message_text, resolved_tower_ids),
            )
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: upgrade parent-tower grounding "
                "unavailable (%s)",
                exc,
            )

        # Pass 4: coverage + freshness signals (raw lines; the instruction
        # stack wraps the whole bundle as untrusted data). Paired with the
        # _TASK_CONTRACT live-event directive.
        facts.extend(_coverage_freshness_signals(intent, live_rows))

    if facts:
        source_summary = _DEFAULT_SOURCE_SUMMARY
    return BTD6Context(
        facts=tuple(facts),
        source_summary=source_summary,
        confidence=confidence,
    )


__all__ = ["BTD6Context", "build"]

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
from dataclasses import dataclass
from typing import Any

from utils.btd6 import tier_codes
from utils.btd6.grounding_format import DEFAULT_CAP as _FACT_TEXT_CAP
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


def _coerce_body(value: Any) -> dict[str, Any]:
    """Normalise ``body_json`` to a dict.

    Legacy ``btd6_facts`` rows were written via a double-encoded
    ``json.dumps`` path (fixed in utils.db.btd6_sources) and so
    round-trip as JSON strings. We decode on read so the grounding
    bundle keeps working for those rows until they're rewritten.
    """
    import json

    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


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
    body = _coerce_body(row.get("body_json"))
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
    lines.extend(_render_tower_stats(getattr(entry, "id", ""), canonical))
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
    return [
        _cap(
            f"[btd6_paragon] {canonical}'s Paragon (tier 6) is {name}, costing "
            f"{stats.paragon_cost} on Medium (source: bloonswiki)",
        ),
    ]


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
# and max. Keeps grounding bounded rather than dumping all 20 levels.
_HERO_GROUNDING_LEVELS: tuple[str, ...] = ("1", "3", "10", "20")


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


def _big(value: int) -> str:
    """Render BTD6's 9,999,999 'infinite' sentinel as ∞."""
    return "∞" if value >= 9_999_999 else str(value)


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

    lines.extend(_render_hero_stats(getattr(entry, "id", ""), canonical))
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
    return lines


async def build(message_text: str) -> BTD6Context:
    """Build a BTD6 context bundle for ``message_text``.

    Three independent passes, each isolated so one failure cannot
    suppress the others:

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
    """
    facts: list[str] = []
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

        # Pass 3: fixture fallback — always runs so cost, category,
        # and upgrade/ability data reach the LLM even when the DB has
        # no rows for tower/hero entities (the common state before live
        # ingestion populates btd6_facts).
        facts.extend(_fixture_facts_for_intent(intent))

    if facts:
        source_summary = _DEFAULT_SOURCE_SUMMARY
    return BTD6Context(
        facts=tuple(facts),
        source_summary=source_summary,
        confidence=confidence,
    )


__all__ = ["BTD6Context", "build"]

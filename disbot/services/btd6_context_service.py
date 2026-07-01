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
import unicodedata
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from utils.btd6 import coverage as cov
from utils.btd6 import tier_codes
from utils.btd6.body_coerce import coerce_body
from utils.btd6.grounding_format import DEFAULT_CAP as _FACT_TEXT_CAP
from utils.btd6.grounding_format import is_infinite as _is_infinite
from utils.btd6.grounding_format import relative_time as _relative_time
from utils.btd6.grounding_format import sanitise as _sanitise_helper
from utils.btd6.keywords import ABR_CUE_RE as _ABR_CUE_RE
from utils.btd6.keywords import degree_in_text as _degree_in_text

logger = logging.getLogger("bot.services.btd6_context")

_DEFAULT_SOURCE_SUMMARY = "data.ninjakiwi.com (Tier 1)"
# Fixture-only answers (no NK-sourced DB rows) must not claim the NK API as
# their source — answerability item 6c; the dataset label is the honest one.
_DATASET_SOURCE_SUMMARY = "local BTD6 dataset (game data + curated)"
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


def _dataset_label() -> str:
    """Source label for facts from the local committed dataset.

    Replaces the internal-ish ``fixture/btd6_data`` (a repo path-ism users saw
    verbatim, answerability item 6b) with the same vocabulary the stats facts
    use ("BTD6 game data 55.1"). Never raises — a label must not be able to
    suppress the fact it labels.
    """
    try:
        from services import btd6_data_service

        version = btd6_data_service.get_dataset().game_version
    except Exception:  # noqa: BLE001 — defensive
        return "BTD6 dataset"
    return f"BTD6 dataset, game v{version}" if version else "BTD6 dataset"


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
            _cap(f"[btd6_tower] {canonical} — {meta} (source: {_dataset_label()})")
            if meta
            else _cap(f"[btd6_tower] {canonical} (source: {_dataset_label()})")
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
                f"{upgrades_str} (source: {_dataset_label()})",
            ),
        )

    if description:
        lines.append(
            _cap(
                f"[btd6_tower] {canonical} — {description} (source: {_dataset_label()})",
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
            f"[btd6_cost] {canonical} pricing — Medium from {_dataset_label()}; "
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
    from utils.btd6.effect_lines import tier_effect_lines

    pstats = btd6_stats_service.get_paragon_stats_by_tower(tower_id)
    if pstats is None or not pstats.has_combat_stats:
        return []

    # Paragon base combat is game-sourced since the v55.1 cutover (the degree
    # 1-100 scaling curve remains the wiki-replica noted below).
    src = "bloonswiki article prose" if pstats.is_prose_sourced else "BTD6 game data"
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
    elite = paragon_degrees.elite_boss_multiplier(100)
    lines.append(
        _cap(
            f"[btd6_paragon_stats normal] {name} at Degree 100 (max): "
            f"{_sanitise(', '.join(max_bits)) if max_bits else 'see base'}; "
            f"boss-damage multiplier ×{boss}, elite-boss multiplier ×{elite:g} "
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
    lines.append(
        _cap(
            "[btd6_paragon_stats scaling] Against ELITE Bosses, paragons deal "
            "DOUBLE their boss damage — paragon-category only, at every degree "
            "(including Degree 1). So the elite-boss damage multiplier is twice "
            "the boss one (×2 to ×4.5: Degree 1 ×2, Degree 100 ×4.5). This ×2 "
            "elite factor is a runtime constant, not in the game files.",
        ),
    )
    # Degree-independent extras. Income + buff/zone auras were committed
    # (Navarch's cashPerRound 3200, its Trade Empire / Flagship / sellback
    # buffs) but no paragon grounding line ever rendered them — the model,
    # told only about the tower path's income, confidently answered that the
    # paragon "makes no coins" (live miss, 2026-06-10). Towers surface income
    # via specials and heroes via [btd6_hero_buff]; this is the paragon leg.
    income = pstats.income_per_round
    if income is not None:
        lines.append(
            _cap(
                f"[btd6_paragon_stats normal] {name} income: generates "
                f"${income:,} at the end of each round (degree-independent; "
                f"source: {src})",
            ),
        )
    effects: list[str] = []
    for effect in tier_effect_lines(pstats.base):
        if effect and effect not in effects:
            effects.append(effect)
    lines.extend(
        _cap(f"[btd6_paragon_stats effect] {name}: {_sanitise(effect)} (source: {src})")
        for effect in effects
    )
    return lines


def _paragon_degree_facts(message_text: str) -> list[str]:
    """Ground a paragon's stats at a SPECIFIC degree named in the text (BUG-0015).

    Players write "d67" (or "degree 67") to ask for a paragon at a given degree —
    only paragons have degrees (1-100). The standard paragon grounding
    (:func:`_render_paragon_stats`) only anchors Degree 1 and Degree 100, so
    without this leg the model has no degree-67 figure and, on the "d67"
    shorthand, misreads it as an upgrade path "0-6-7" and refuses it exists
    (live miss 2026-06-16). This surfaces the exact, NON-linear headline at the
    requested degree, explicitly labelled "Degree N" — which disambiguates the
    shorthand and hands the model the right numbers. Degree-INDEPENDENT facts
    (income, abilities, effects) already ground via :func:`_render_paragon`.
    """
    degree = _degree_in_text(message_text)
    # Degrees 1 and 100 are exactly the anchors _render_paragon_stats already
    # emits — only an INTERMEDIATE degree adds anything new here.
    if degree is None or degree in (1, 100):
        return []

    from services import btd6_stats_service
    from utils.btd6 import paragon_degrees

    paragon_id = btd6_stats_service.resolve_paragon(message_text)
    if paragon_id is None:
        return []
    pstats = btd6_stats_service.get_paragon_stats(paragon_id)
    if pstats is None or not pstats.has_combat_stats:
        return []
    bits = _paragon_main_bits(pstats.base, degree)
    if not bits:
        return []

    src = "bloonswiki article prose" if pstats.is_prose_sourced else "BTD6 game data"
    boss = paragon_degrees.boss_multiplier(degree)
    power = paragon_degrees.power_for_degree(degree)
    return [
        _cap(
            f"[btd6_paragon_stats degree {degree}] {pstats.canonical} at Degree "
            f"{degree}: {_sanitise(', '.join(bits))}; boss-damage ×{boss}; "
            f"{power:,} power (source: {src})",
        ),
        _cap(
            f"[btd6_paragon_stats degree {degree}] Note: 'd{degree}' / "
            f"'degree {degree}' is the paragon's DEGREE (1-100), NOT an "
            "upgrade-path code — paragons are tier 6, beyond the 0-5-5 cap.",
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
                f"{_sanitise(', '.join(bits))} (source: BTD6 game data)",
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

    Every hero has a game-data stats file since the v55.1 cutover; a hero
    without one (or without combat stats) still returns nothing.
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
                f"{_sanitise(', '.join(bits))} (source: BTD6 game data)",
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
    from services import btd6_stats_service, btd6_upgrade_detail_service

    stats = btd6_stats_service.get_tower_stats(tower_id)
    if stats is None:
        return []
    tier = stats.tier(code)
    if tier is None:
        return []
    name = _tier_name(stats, code)
    pretty = tier_codes.format_code(code)
    lines: list[str] = []
    bits = _normal_stat_bits(btd6_stats_service.normal_stats(tier))
    if bits:
        lines.append(
            _cap(
                f"[btd6_tower_stats normal] {canonical} {name} "
                f"({pretty}): {_sanitise(', '.join(bits))} "
                "(source: BTD6 game data)",
            ),
        )
    # The headline stats above omit buff/zone effects, and the upgrade-detail path
    # only sees a card's base tier — so a named crosspath's effects (e.g. 0-1-4
    # Heli's stronger MOAB Shove) reach the user nowhere else.
    for effect in btd6_upgrade_detail_service.tier_effect_lines(tier):
        lines.append(
            _cap(
                f"[btd6_tower_stats effect] {canonical} {name} "
                f"({pretty}): {_sanitise(effect)} (source: BTD6 game data)",
            ),
        )
    return lines


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
            _cap(f"[btd6_hero] {canonical} — {cost_str} (source: {_dataset_label()})")
            if cost_str
            else _cap(f"[btd6_hero] {canonical} (source: {_dataset_label()})")
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
                _cap(f"[btd6_hero] {canonical} {ab_str} (source: {_dataset_label()})"),
            )

    if description:
        lines.append(
            _cap(
                f"[btd6_hero] {canonical} — {description} (source: {_dataset_label()})",
            ),
        )

    hero_id = getattr(entry, "id", "")
    lines.extend(_render_hero_stats(hero_id, canonical))
    lines.extend(_render_hero_descriptions(hero_id, canonical))
    lines.extend(_render_hero_buffs(hero_id, canonical))
    return lines


def _render_hero_buffs(hero_id: str, canonical: str) -> list[str]:
    """Per-level buff/zone aura lines, emitted only where the set CHANGES.

    Hero levels carry decoded ``buffs``/``zones`` (Striker's explosive
    attack-speed aura, Etienne's range aura…) that no grounding line ever
    rendered — fully decoded but invisible (#655 answerability item 6d).
    Change-only emission keeps it bounded: Striker yields three lines
    (L4 ×0.9 → L8 +Bomb buff → L18 ×0.81), not twenty.
    """
    from services import btd6_stats_service
    from utils.btd6.effect_lines import tier_effect_lines

    stats = btd6_stats_service.get_hero_stats(hero_id)
    if stats is None:
        return []
    lines: list[str] = []
    previous: frozenset[str] = frozenset()
    for code in sorted(stats.levels or (), key=int):
        node = stats.level(code)
        if node is None:
            continue
        rendered = tier_effect_lines(node)
        # Compare as a SET: the decoded buff list's order shifts between
        # levels (L8 vs L10 carry identical auras in a different order),
        # and an order-only "change" would double-emit.
        current = frozenset(rendered)
        if rendered and current != previous:
            lines.append(
                _cap(
                    f"[btd6_hero_buff] {canonical} Level {code} auras: "
                    f"{_sanitise('; '.join(sorted(rendered)))} "
                    "(source: BTD6 game data)",
                ),
            )
        if rendered:
            previous = current
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
                f"[btd6_bloon] {canonical} — {meta} (source: {_dataset_label()})"
                if meta
                else f"[btd6_bloon] {canonical} (source: {_dataset_label()})"
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
                f"(source: {_dataset_label()})",
            ),
        )

    # MOAB-class bloons take a runtime late-game/freeplay health ramp (+2% of base
    # HP per round from round 81; ×1.40 by round 100) that is NOT in the game files,
    # so the base `health` above is only the round-≤80 value. Surface it so the
    # model never claims a BAD "keeps its 20,000 base" on a late round (the bug this
    # fixes) — this is the conversational-follow-up complement to the deterministic
    # "HP of <bloon> at round N" floor.
    if str(getattr(entry, "category", "")) == "moab_class" and isinstance(health, int):
        from services import btd6_data_service

        bid = str(getattr(entry, "id", ""))
        mult100 = btd6_data_service.moab_class_health_multiplier(100)
        if mult100 is not None:
            r100_hp = int(round(health * mult100))
            rbe100 = btd6_data_service.bloon_rbe_at_round(bid, 100)
            rbe_bit = f", {rbe100:,} RBE" if isinstance(rbe100, int) else ""
            lines.append(
                _cap(
                    f"[btd6_bloon] {canonical} — late-game/freeplay scaling: MOAB-class "
                    f"health ramps from round 81 (×{mult100:g} by round 100, steepening "
                    f"sharply past 100), so {health:,} HP holds only through round 80; it "
                    f"first appears on round 100 at {r100_hp:,} HP{rbe_bit}. Runtime ramp "
                    f"(health + spawned-tree RBE), not in the game files (source: "
                    f"{_dataset_label()}).",
                ),
            )

    if description:
        lines.append(
            _cap(
                f"[btd6_bloon] {canonical} — {description} (source: {_dataset_label()})",
            ),
        )

    return lines


def _render_fixture_round(entry: Any, *, roundset_label: str = "") -> list[str]:
    """Render a RoundEntry as 1-3 ``[btd6_round]`` grounding lines.

    Surfaces the facts round questions hinge on: danger, total (children-
    inclusive) RBE, the exact spawn composition, and any curated strategy note.
    Only resolver-matched round(s) are rendered, so grounding stays bounded.

    ``roundset_label`` (e.g. ``"ABR"``) stamps every line's round reference —
    BUG-0010: an Alternate Bloons Rounds entry rendered without the label is
    indistinguishable from standard, and the answer guard then either blocks
    the model's honest "Alternate Bloons Rounds" naming or lets a
    standard-as-ABR mislabel through.
    """
    from services import btd6_data_service

    number = getattr(entry, "round_number", None)
    if number is None:
        return []
    ref = f"Round {number} ({roundset_label})" if roundset_label else f"Round {number}"
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
        # before any income towers, and halved under Half Cash. An ABR entry's
        # cash follows ABR rules (entered at round 3) — never call it standard.
        economy = (
            f"{roundset_label} round-set economy, no income towers"
            if roundset_label
            else "standard economy, no income towers"
        )
        head.append(f"{bit} ({economy})")
    if threats:
        head.append(f"threats: {', '.join(_sanitise(t) for t in threats)}")
    headline = " | ".join(head)
    lines = [
        _cap(
            (
                f"[btd6_round] {ref} — {headline} (source: {_dataset_label()})"
                if headline
                else f"[btd6_round] {ref} (source: {_dataset_label()})"
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
        # Ground the total bloons that ENTER the round (sum of the spawn groups,
        # not counting children that appear only when a parent pops — that count
        # is the RBE above). Without this, "how many bloons spawn on rN" had no
        # grounded number, so the model's derived total (e.g. 75 + 122 = 197)
        # tripped the value-only faithfulness guard and got refused, while the
        # identical "list every bloon in rN" answered fine from the per-bloon
        # counts.
        total_spawned = sum(aggregated.values())
        lines.append(
            _cap(
                f"[btd6_round] {ref} composition — "
                f"{_sanitise(', '.join(parts))}; {total_spawned:,} bloons enter "
                f"this round in total (children spawned on pop are counted by the "
                f"RBE, not here) (source: {_dataset_label()})",
            ),
        )

    # Curated strategy blurb (skip the auto-generated "N Lead, M Ceramic…" ones).
    if summary and not summary[0].isdigit():
        lines.append(
            _cap(
                f"[btd6_round] {ref} — {summary} (source: {_dataset_label()})",
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
    # Ranking questions ("best paragon?") got ZERO grounding (2026-06-10
    # sweep) — the model ranked from memory with invented names. The roster
    # pins the 13 real candidates; the ranking itself stays the model's
    # clearly-subjective call.
    "best paragon",
    "strongest paragon",
    "top paragon",
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
    # Ranking questions ("strongest tower?") — same grounding rationale as
    # the paragon roster's best/strongest/top entries (2026-06-10 sweep).
    "best ",
    "strongest ",
    "top ",
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
                f"{len(maps) - water} are land-only. (source: {_dataset_label()})",
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
    # A map water/land/removables question is a list/count request even without a
    # generic "list/all" verb ("land-only maps", "which maps have removables").
    map_list = "map" in text and any(
        p in text
        for p in (
            "water",
            "naval",
            "land-only",
            "land only",
            "removable",
            "obstacle",
            "which",
            "without water",
            "no water",
        )
    )
    is_list = (
        any(phrase in text for phrase in _ROSTER_LIST_INTENT)
        or "all " in text
        or "every " in text
        or map_list
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

    if "boss" in text:
        bosses = dataset.bosses
        if not bosses:
            return None
        lines = [
            (
                f"• **{boss.canonical}** — {boss.tagline}"
                if getattr(boss, "tagline", "")
                else f"• **{boss.canonical}**"
            )
            for boss in bosses
        ]
        return (
            f"**BTD6 Bosses ({len(lines)})** — the boss bloons (each scales "
            "Tier 1–5, with an Elite variant):\n" + "\n".join(lines)
        )

    if "map" in text:
        return _map_roster_reply(text, list(dataset.maps))

    return None


def _map_roster_reply(text: str, maps: list) -> str:
    """Deterministic map list/count answers (water / land-only / removables).

    The model proved it cannot restate these — it gave five different water
    counts (73/75/76/77), each falsely "verified from the tool", while its own
    land-only list held the right 20. So floor map count/list questions to
    code-built truth, exactly like the hero/tower rosters. Returns the count
    alone for a pure "how many", otherwise the grouped name list(s).
    """
    water = [m for m in maps if m.has_water]
    land = [m for m in maps if not m.has_water]
    removable = [m for m in maps if getattr(m, "removables", "")]
    order = ("Beginner", "Intermediate", "Advanced", "Expert")

    def grouped(rows: list) -> str:
        out = []
        for diff in order:
            names = sorted(m.canonical for m in rows if m.difficulty == diff)
            if names:
                out.append(f"__{diff}__: " + ", ".join(names))
        return "\n".join(out)

    wants_count = ("how many" in text or "number of" in text) and not any(
        w in text for w in ("list", "name ", "which", "what are")
    )
    want_rem = "removable" in text or "obstacle" in text
    want_land = any(
        p in text for p in ("land-only", "land only", "without water", "no water")
    ) or ("land" in text and "water" not in text)
    want_water = (not want_land) and ("water" in text or "naval" in text)

    sections: list[str] = []
    if want_rem:
        sections.append(
            f"**Maps with removable obstacles ({len(removable)} of {len(maps)})** "
            "— ask about a specific map for what's removable:\n" + grouped(removable),
        )
    if want_water:
        if wants_count and not sections:
            return (
                f"Of {len(maps)} BTD6 maps, **{len(water)} have water** (naval "
                f"towers placeable) and **{len(land)} are land-only**."
            )
        sections.append(
            f"**Maps with water ({len(water)} of {len(maps)})** — naval towers "
            "placeable:\n" + grouped(water),
        )
    elif want_land:
        if wants_count and not sections:
            return (
                f"**{len(land)}** of {len(maps)} BTD6 maps are land-only (no "
                f"water); the other **{len(water)}** have water."
            )
        sections.append(
            f"**Land-only maps ({len(land)} of {len(maps)})** — no water, land "
            "towers only:\n" + grouped(land),
        )
    if sections:
        return "\n\n".join(sections)

    # A named difficulty ("list all expert maps", "what beginner maps are
    # there") filters the roster to that tier. Without this the user who asked
    # for the 13 Expert maps got all 86 grouped by difficulty — a BUG-0009
    # wrong-assembly miss (right values, wrong list).
    named_diffs = [d for d in order if d.lower() in text]
    if named_diffs:
        subset = [m for m in maps if m.difficulty in named_diffs]
        label = "/".join(named_diffs)
        if wants_count:
            return f"BTD6 has **{len(subset)} {label} maps**."
        names = ", ".join(sorted(m.canonical for m in subset))
        return f"**BTD6 {label} Maps ({len(subset)}):** {names}"

    # Generic "how many maps" / "list all maps".
    if wants_count:
        by_diff = ", ".join(
            f"{sum(1 for m in maps if m.difficulty == d)} {d}" for d in order
        )
        return (
            f"BTD6 has **{len(maps)} maps**: {by_diff}. **{len(water)}** have "
            f"water, **{len(land)}** are land-only."
        )
    return f"**BTD6 Maps ({len(maps)})** by difficulty:\n{grouped(maps)}"


# --- "Monkey Knowledge related to <tower>" deterministic reply (BUG-0009) -----
# The model, asked "which monkey knowledges relate to the farm", listed the
# whole Support *category* and labelled it farm-related (Big Traps / One More
# Spike / Vigilant Sentries are Engineer / Spike Factory). Every NAME was
# grounded, so the faithfulness guard (values, not claims) passed the wrong
# *grouping* — this class never reaches the post-hoc roster floor. The fix is
# the proven shape: the deterministic layer OWNS the labelled answer, served as
# a pre-emptive floor before the model assembles. The MK↔tower relation itself
# lives in btd6_data_service.monkey_knowledge_referencing().
_MK_CUE_RE = re.compile(r"\bmonkey\s+knowledges?\b|\bmk\b", re.I)
# A relation/enumeration cue — distinguishes "which MK relate to the farm" (this
# answer) from a single-MK lookup ("what does Farm Subsidy do", no cue → model).
_MK_LIST_RELATION_RE = re.compile(
    r"\b(?:related|relate|relating|relevant|associated|affects?|applies|apply|"
    r"improves?|buffs?|boosts?|helps?|all|every|which|list)\b|\bwhat\s+are\b",
    re.I,
)


def _scan_tower(text_lower: str, dataset: Any) -> Any | None:
    """The most specific tower named in ``text_lower`` (longest surface form),
    or ``None``. Whole-word matched on canonical names + aliases.
    """
    best = None
    best_len = 0
    for tower in dataset.towers:
        surfaces = [tower.canonical, *tower.aliases]
        for surface in surfaces:
            s = surface.lower()
            if len(s) < 3:
                continue
            if re.search(r"\b" + re.escape(s) + r"s?\b", text_lower):
                if len(s) > best_len:
                    best, best_len = tower, len(s)
    return best


def deterministic_mk_reference_reply(message_text: str) -> str | None:
    """A code-built "Monkey Knowledge related to <tower>" answer, or ``None``.

    Fires only on a clear MK-for-tower enumeration: an MK cue ("monkey
    knowledge"/"mk") + a relation/list cue + a resolvable tower. Returns
    ``None`` for single-MK lookups (no list cue), strategy/opinion questions,
    and anything without a tower — those still reach the model. The list is the
    deterministic relation, so the answer is always the correct grouping.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _MK_CUE_RE.search(low):
        return None
    if not _MK_LIST_RELATION_RE.search(low):
        return None
    if any(word in low for word in _ROSTER_STRATEGY_WORDS):
        return None

    from services import btd6_data_service

    dataset = btd6_data_service.get_dataset()
    tower = _scan_tower(low, dataset)
    if tower is None:
        return None

    # A complete "which MK affects <tower>" answer has two parts:
    #   1. points that NAME the tower or one of its upgrades, and
    #   2. CLASS-WIDE points that buff every tower in the tower's class without
    #      naming it (e.g. "Come On Everybody!" → all Primary towers).
    # The owner reported part 2 missing: "which MK affects the glue gunner" must
    # include Come On Everybody (2026-06-18). Both halves are deterministic
    # relations, so the floor owns the labelled answer.
    tab = tower.category.title()
    named = sorted(
        btd6_data_service.monkey_knowledge_referencing(tower),
        key=lambda mk: mk.canonical.lower(),
    )
    class_wide = sorted(
        btd6_data_service.monkey_knowledge_class_wide(tower.category),
        key=lambda mk: mk.canonical.lower(),
    )

    if not named and not class_wide:
        return (
            f"**No Monkey Knowledge specifically affects the "
            f"{tower.canonical}.** No point names it or one of its upgrades, and "
            f"no {tab}-tab point buffs the whole {tab} class."
        )

    total = len(named) + len(class_wide)
    lines = [
        f"**Monkey Knowledge that affects the {tower.canonical} ({total})** — "
        f"both points that name it and class-wide {tab} points that buff every "
        f"{tab} tower:",
    ]
    if named:
        lines.append("")
        lines.append(
            f"__Names the {tower.canonical} or an upgrade ({len(named)}):__",
        )
        lines.extend(f"• **{mk.canonical}** — {mk.description}" for mk in named)
    if class_wide:
        lines.append("")
        lines.append(
            f"__Class-wide {tab} Monkey Knowledge — buffs every {tab} tower "
            f"({len(class_wide)}):__",
        )
        lines.extend(f"• **{mk.canonical}** — {mk.description}" for mk in class_wide)
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


# --- "Monkey Knowledge by category/tab" deterministic roster (§7.6) -----------
# The §7.6 Monkey-Knowledge member of the BUG-0009 roster floor: asked "what
# Support monkey knowledges are there", the model lists the tab itself and can
# mis-bucket a point (the owner's verbatim miss was the *inverse* — calling the
# whole Support tab "related to the farm"). Every MK NAME is grounded, so the
# value-only faithfulness guard never catches a wrong *grouping*; the
# deterministic layer OWNS the labelled per-tab list. The grouping lives in
# btd6_data_service.monkey_knowledge_by_category(). Distinct from
# deterministic_mk_reference_reply (which owns "MK related to <tower>"): this one
# fires only on a *category/tab* cue and defers when a tower is named, so the two
# never both fire.
# (category key, the cue that names that in-game tab). Order mirrors the
# btd6_data_service tab order.
_MK_CATEGORY_CUES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Primary", re.compile(r"\bprimary\b", re.I)),
    ("Military", re.compile(r"\bmilitary\b", re.I)),
    ("Magic", re.compile(r"\bmagic\b", re.I)),
    ("Support", re.compile(r"\bsupport\b", re.I)),
    ("Heroes", re.compile(r"\bheroe?s?\b", re.I)),
    ("Powers", re.compile(r"\bpowers?\b", re.I)),
)
# Human label per tab for the roster header.
_MK_CATEGORY_LABELS: dict[str, str] = {
    "Primary": "Primary",
    "Military": "Military",
    "Magic": "Magic",
    "Support": "Support",
    "Heroes": "Heroes",
    "Powers": "Powers",
}
# An enumeration shape ("which/what/list ... monkey knowledge", "how many ...") so
# a single-MK lookup ("what does More Cash do") stays out of the roster floor.
_MK_ROSTER_LIST_RE = re.compile(
    r"\b(?:which|what|list|name|all|every|how\s+many|are\s+there)\b",
    re.I,
)
# A STRONG whole-catalog cue for the no-tab case ("list all monkey knowledge",
# "how many monkey knowledge are there"). Deliberately a *subset* of
# _MK_ROSTER_LIST_RE that excludes a bare "which"/"what": those weak cues fire on
# a single-MK effect lookup ("what does More Cash do"), which must still defer to
# the model. With no tab named, only an explicit all/every/list/how-many ask is a
# whole-catalog roster.
_MK_ALL_ROSTER_RE = re.compile(
    r"\b(?:all|every|complete|full|entire|list|name|how\s+many|are\s+there)\b",
    re.I,
)


def _match_mk_category(text_lower: str) -> str | None:
    """The single Monkey-Knowledge tab a roster question names, or ``None``."""
    for category, pattern in _MK_CATEGORY_CUES:
        if pattern.search(text_lower):
            return category
    return None


def _all_mk_roster_reply(
    grouped: dict[str, tuple[Any, ...]],
) -> str:
    """The whole-catalog Monkey-Knowledge roster, grouped by in-game tab.

    Serves "list all monkey knowledge" (no tab named) — the all-tabs sibling of
    the per-tab :func:`deterministic_mk_category_roster_reply` body. Empty tabs
    are skipped; the natural-language stage chunks the result for Discord, so no
    length cap is applied here.
    """
    total = sum(len(rows) for rows in grouped.values())
    lines = [f"**All Monkey Knowledge ({total}) by tab:**"]
    for category, rows in grouped.items():
        if not rows:
            continue
        label = _MK_CATEGORY_LABELS.get(category, category)
        names = ", ".join(f"**{mk.canonical}**" for mk in rows)
        lines.append(f"__{label}__ ({len(rows)}): {names}")
    return "\n".join(lines)


def deterministic_mk_category_roster_reply(message_text: str) -> str | None:
    """A code-built "Monkey Knowledge in the <tab>" roster, or ``None``.

    The §7.6 Monkey-Knowledge member of the BUG-0009 roster floor (sibling of the
    relic / capability rosters). Fires on an MK cue + an enumeration cue in two
    shapes:

    * a named tab (Primary/Military/Magic/Support/Heroes/Powers) → that tab's
      points, so the model can never mis-bucket the grouping; or
    * **no tab + a strong all/every/list cue** ("list all monkey knowledge") →
      the *whole catalog* grouped by tab. This branch restores the regression
      where the un-scoped ask refused with the version-stamped no-data message
      while "list all *primary* monkey knowledge" worked.

    Defers (``None``) for single-MK lookups (no list cue, or a bare which/what
    with no tab), strategy/opinion questions, and — crucially — anything naming a
    *tower* (that is :func:`deterministic_mk_reference_reply`'s "MK related to
    <tower>" job, which runs first in the dispatcher), so the two MK builders
    never both fire.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _MK_CUE_RE.search(low):
        return None
    if not _MK_ROSTER_LIST_RE.search(low):
        return None
    if any(word in low for word in _ROSTER_STRATEGY_WORDS):
        return None

    from services import btd6_data_service

    # A named tower means the tower-relation builder owns this — defer to it.
    dataset = btd6_data_service.get_dataset()
    if _scan_tower(low, dataset) is not None:
        return None

    grouped = btd6_data_service.monkey_knowledge_by_category()

    category = _match_mk_category(low)
    if category is None:
        # No tab named: only the *whole-catalog* roster ("list all monkey
        # knowledge") is ours. It needs a STRONG enumeration cue
        # (all/every/list/how-many) — a bare which/what is a single-MK effect
        # lookup ("what does More Cash do") that still defers to the model. This
        # restores the regression where the all-tabs ask refused with the
        # version-stamped no-data message instead of listing (live miss,
        # 2026-06-22): the per-tab "list all primary monkey knowledge" worked
        # but the un-scoped "list all monkey knowledge" had no builder, fell
        # through to the model, and its 70+ item list tripped the faithfulness
        # guard into the refusal.
        if not _MK_ALL_ROSTER_RE.search(low):
            return None
        return _all_mk_roster_reply(grouped)

    rows = grouped.get(category, ())
    label = _MK_CATEGORY_LABELS.get(category, category)
    if not rows:
        return f"**BTD6 — no Monkey Knowledge in the {label} tab.**"
    names = ", ".join(f"**{mk.canonical}**" for mk in rows)
    reply = f"**Monkey Knowledge in the {label} tab ({len(rows)}):** {names}"
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


# --- "Geraldo items per level" deterministic reply (BUG-0009 slice 2) ---------
# The model, asked "what does Geraldo unlock at each level", assembles the
# level→item grouping itself and mislabels which item unlocks when. Every item
# NAME is grounded, so the value-only faithfulness guard passes the wrong
# *grouping* (the BUG-0009 class) — so the deterministic layer OWNS the labelled
# per-level list. Served as a pre-emptive floor before the model. The grouping
# itself lives in btd6_data_service.geraldo_items_by_unlock_level().
_GERALDO_CUE_RE = re.compile(r"\bgeraldo'?s?\b", re.I)
# A per-level / enumeration cue — distinguishes "what does Geraldo unlock per
# level / list his items" (this answer) from a single-item lookup ("what does
# the Genie Bottle do", no level/list cue → model). "unlock(s|ed)" alone counts
# (the common "what does Geraldo unlock" / "when do you unlock X" phrasing).
_GERALDO_LIST_RELATION_RE = re.compile(
    r"\blevels?\b|\bunlocks?\b|\bunlocked\b|\beach\b|\bevery\b|\bper\b|"
    r"\ball\b|\blist\b|\bwhat\s+are\b|\bwhich\b|\bitems?\b|\bshop\b",
    re.I,
)
# A specific level number ("at level 7", "lvl 12", "level-3").
_GERALDO_LEVEL_NUM_RE = re.compile(r"\b(?:level|lvl|lv)\s*[-#]?\s*(\d{1,2})\b", re.I)
# The "starting kit" angle ("what does Geraldo start with", "Geraldo's starting
# items") — the buffer-slice gap the level/list cue missed. Maps to the level-0
# items (the kit Geraldo has before any level-ups).
_GERALDO_STARTING_RE = re.compile(
    r"\bstart(?:s|ing|ed)?\s+(?:with|out|kit|gear|loadout|inventory|items?)\b|"
    r"\bstarting\s+(?:items?|kit|gear|loadout|inventory)\b|"
    r"\bbegins?\s+with\b|\bcomes?\s+with\b",
    re.I,
)


def _format_geraldo_item_line(item: Any) -> str:
    return f"• **{item.canonical}** (${item.cost:,}) — {item.description}"


def deterministic_geraldo_per_level_reply(message_text: str) -> str | None:
    """A code-built "what Geraldo unlocks per level" answer, or ``None``.

    Fires only on a clear Geraldo per-level / list enumeration: a Geraldo cue +
    a level/list cue, and (for the full list) no single named item. Two shapes:

    * **a specific level** ("what does Geraldo unlock at level 7") → the items
      that unlock at exactly that level;
    * **the whole grouping** ("Geraldo items per level", "list Geraldo's items")
      → every item grouped by unlock level.

    Returns ``None`` for single-item lookups (a named item with no level/list
    cue), strategy/opinion questions, and anything without a Geraldo cue — those
    still reach the model. The grouping is the deterministic relation, so the
    answer is always correctly grouped.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _GERALDO_CUE_RE.search(low):
        return None
    starting = bool(_GERALDO_STARTING_RE.search(low))
    if not starting and not _GERALDO_LIST_RELATION_RE.search(low):
        return None
    if any(word in low for word in _ROSTER_STRATEGY_WORDS):
        return None

    from services import btd6_data_service

    grouped = btd6_data_service.geraldo_items_by_unlock_level()
    if not grouped:
        return None

    # The "starting kit" angle ("what does Geraldo start with") → his level-0
    # items specifically, unless the question also names a different level.
    if starting and not _GERALDO_LEVEL_NUM_RE.search(low):
        items = next((rows for lvl, rows in grouped if lvl == 0), ())
        if not items:
            return None
        body = "\n".join(_format_geraldo_item_line(i) for i in items)
        return f"**Geraldo starts with ({len(items)}):**\n{body}"

    # A specific level was named → just that level's unlocks. (Even if zero
    # items unlock there, the deterministic "nothing new unlocks at L<n>" is the
    # honest answer — the model would otherwise invent one.)
    level_match = _GERALDO_LEVEL_NUM_RE.search(low)
    if level_match:
        level = int(level_match.group(1))
        items = next((rows for lvl, rows in grouped if lvl == level), ())
        if not items:
            return (
                f"**Geraldo unlocks no new shop item at level {level}.** "
                "He gains a new item to sell at levels "
                + ", ".join(str(lvl) for lvl, _ in grouped)
                + "."
            )
        body = "\n".join(_format_geraldo_item_line(i) for i in items)
        return f"**Geraldo unlocks at level {level} ({len(items)}):**\n{body}"

    # Otherwise: the full per-level grouping.
    lines = ["**Geraldo's shop items by unlock level:**"]
    for level, items in grouped:
        label = "Start (level 0)" if level == 0 else f"Level {level}"
        names = ", ".join(f"**{i.canonical}**" for i in items)
        lines.append(f"__{label}__: {names}")
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


# --- "list the game modes" deterministic reply (BUG-0009, mode groupings) -----
# The model, asked "list all the game modes", mislabels which row is a
# difficulty vs. a mode vs. a modifier (the owner's "mode groupings" miss). Every
# name is grounded, so the value-only faithfulness guard passes the wrong
# grouping — so the deterministic layer OWNS the labelled, kind-grouped list. The
# grouping itself lives in btd6_data_service.modes_by_kind().
_MODES_CUE_RE = re.compile(r"\b(?:game\s*)?modes?\b|\bdifficult(?:y|ies)\b", re.I)
# Another primary roster entity in the message means "mode"/"difficulty" is most
# likely a *qualifier* ("which towers work on impoppable mode", "best hero on
# hard difficulty"), not the list subject — defer those to the model. (Monkey
# Knowledge is excluded by the dispatcher order: its builder runs first.)
_MODES_OTHER_ENTITY_RE = re.compile(
    r"\b(?:towers?|heroe?s?|paragons?|bloons?|bosse?s?|maps?|rounds?|"
    r"upgrades?|crosspaths?)\b",
    re.I,
)
# Human-readable heading per kind (game-correct phrasing, not the raw tag).
_MODE_KIND_LABELS = {
    "difficulty": "Difficulties",
    "mode": "Game modes",
    "modifier": "Modifiers",
}


def deterministic_modes_reply(message_text: str) -> str | None:
    """A code-built "list the BTD6 game modes" answer, or ``None``.

    Fires only on a clear modes enumeration: a mode/difficulty cue + a strong
    list-intent cue (the same set the roster floor uses) + no other roster
    entity (so a "mode" used as a qualifier stays with the model). Returns
    ``None`` for single-mode lookups ("what is CHIMPS", "what does Deflation
    do"), strategy/opinion questions, and anything without a modes cue. The list
    is the deterministic kind-grouping, so a difficulty is never mislabelled a
    mode.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _MODES_CUE_RE.search(low):
        return None
    if _MODES_OTHER_ENTITY_RE.search(low):
        return None
    is_list = (
        any(phrase in low for phrase in _ROSTER_LIST_INTENT)
        or "all " in low
        or "every " in low
    )
    if not is_list:
        return None
    if any(word in low for word in _ROSTER_STRATEGY_WORDS):
        return None

    from services import btd6_data_service

    grouped = btd6_data_service.modes_by_kind()
    if not grouped:
        return None

    total = sum(len(rows) for _, rows in grouped)
    lines = [
        f"**BTD6 game modes ({total})** — grouped by what they actually are "
        "(difficulty vs. game mode vs. opt-in modifier):",
    ]
    for kind, modes in grouped:
        label = _MODE_KIND_LABELS.get(kind, kind.capitalize())
        names = ", ".join(f"**{m.canonical}**" for m in modes)
        lines.append(f"__{label} ({len(modes)})__: {names}")
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


# --- "which costs more" deterministic reply (AI §7.5 multi-entity comparison) -
# A cost comparison ("is a 0-4-1 desperado cheaper than a 2-0-4 sniper", "compare
# the cost of a 5-0-0 ninja and a 0-5-0 wizard") is the same "grounded values,
# wrong assembly" class as BUG-0009 — every individual price is grounded, but the
# model freelances/mis-ranks the comparison itself (which is cheaper, by how much),
# and the value-only faithfulness guard cannot catch a mis-*ranking*. So the
# deterministic layer OWNS the labelled comparison: it prices each named candidate
# via btd6_data_service.compare_crosspath_costs (the §7.5 rank/diff primitive) and
# serves the ranked answer as a pre-emptive floor before the model.
#
# High-precision firing: an explicit cost-compare cue (NOT a bare "cheap"/"better")
# AND at least two resolvable (tower, crosspath) candidates. "vs"/"versus" stay
# allowed (normal cost-comparison connectors), unlike the roster strategy fence.
_COST_COMPARE_CUE_RE = re.compile(
    r"\bcheaper\b|\bcheapest\b|\bpricier\b|\bmore\s+expensive\b|"
    r"\bless\s+expensive\b|\bmost\s+expensive\b|\bleast\s+expensive\b|"
    r"\bcosts?\s+(?:more|less|the\s+same)\b|\bprice\s+difference\b|"
    r"\bcost\s+difference\b|\bbetter\s+value\b",
    re.I,
)
# "compare the cost of X and Y" / "cost comparison" — a compare verb anchored to a
# cost/price noun (so "compare the ninja and sniper" without a money word defers to
# the model, where it may be a stats comparison).
_COST_COMPARE_VERB_RE = re.compile(
    r"\bcompare\b.{0,40}\b(?:cost|price|pricing)\b|"
    r"\b(?:cost|price|pricing)\b.{0,40}\bcompare\b|"
    r"\b(?:cost|price)\s+comparison\b",
    re.I,
)
# Clearly-strategic intent that wants a recommendation, not a price — a cost answer
# would be a non-sequitur. Deliberately small (the cost cue already gates hard).
_COST_COMPARE_STRATEGY_EXCLUDE = (
    "should i",
    "recommend",
    "worth it",
    "tier list",
    "good against",
    "best for",
)
# A named difficulty in the question; default medium when absent.
_COST_DIFFICULTY_RE = re.compile(
    r"\b(easy|medium|hard|impoppable|impop|chimps)\b",
    re.I,
)
# An explicit paragon token — the disambiguator that routes a cost comparison to
# the paragon builder (and away from the base-tower cost builders, which match a
# tower alias like "dart"/"ninja" and would otherwise price the *base* tower).
_PARAGON_CUE_RE = re.compile(r"\bparagons?\b", re.I)

# --- §7.5 round-range cash comparison -----------------------------------------
# An income/earning noun (distinct from the cost cue above) — required so a
# round-range comparison fires only on a money question, not a stats one.
_EARN_NOUN_RE = re.compile(r"\b(?:cash|money|income|earn(?:ed|ings?|s)?)\b", re.I)
# A comparison signal: "more"/"less"/"most"/"better", "vs"/"or"/"than",
# or an explicit compare verb. Combined with the earn noun + two ranges, this
# keeps the floor off single-range questions (the round-cash workflow's job).
_EARN_COMPARE_RE = re.compile(
    r"\b(?:more|less|most|least|higher|lower|highest|lowest|better|worse)\b|"
    r"\bvs\.?\b|\bversus\b|\bor\b|\bthan\b|\bcompare[ds]?\b|\bcomparison\b|"
    r"\bdifference\b",
    re.I,
)
# A clearly-strategic intent that wants a recommendation, not a number — defer.
_EARN_STRATEGY_EXCLUDE = ("should i", "recommend", "worth it", "best for")
# An inclusive round range: "rounds 20-40", "round 20 to 40", "r20-40",
# "20 through 40" (a round token on the first anchor, optional on the second).
# The trailing digit boundary keeps "r2d2"-style tokens out.
_ROUND_RANGE_RE = re.compile(
    r"\b(?:rounds?|r)\s*(\d{1,3})\s*(?:to|through|thru|until|till|[-–])\s*"
    r"(?:(?:rounds?|r)\s*)?(\d{1,3})\b",
    re.I,
)
# "between rounds X and Y" — the connector form _ROUND_RANGE_RE does not cover.
_ROUND_RANGE_BETWEEN_RE = re.compile(
    r"\bbetween\s+(?:rounds?|r)?\s*(\d{1,3})\s+and\s+(?:(?:rounds?|r)\s*)?(\d{1,3})\b",
    re.I,
)


def _extract_round_ranges(text_lower: str) -> list[tuple[int, int]]:
    """The inclusive round ranges a comparison names, in order of appearance.

    Both the ``X-Y`` / ``X to Y`` form and the ``between X and Y`` form are
    scanned; each ``(lo, hi)`` is returned with endpoints normalised (lo ≤ hi).
    Order is preserved and deduped on the normalised pair so "rounds 20-40 or
    20-40" yields one range (the data primitive also dedups, but doing it here
    keeps the ≥2-ranges gate honest).
    """
    found: list[tuple[int, tuple[int, int]]] = []
    seen: set[tuple[int, int]] = set()
    for match in (
        *_ROUND_RANGE_RE.finditer(text_lower),
        *_ROUND_RANGE_BETWEEN_RE.finditer(text_lower),
    ):
        a, b = int(match.group(1)), int(match.group(2))
        pair = (min(a, b), max(a, b))
        if pair in seen:
            continue
        seen.add(pair)
        found.append((match.start(), pair))
    found.sort(key=lambda f: f[0])
    return [pair for _start, pair in found]


def _fmt_money(value: float) -> str:
    """Money string: no decimals for a whole-dollar amount, else two places."""
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


def _format_round_range_comparison(result: dict[str, Any]) -> str:
    set_label = result["set_label"]

    def _label(entry: dict[str, Any]) -> str:
        if entry["single_round"]:
            return f"Round {entry['round_start']}"
        return f"Rounds {entry['round_start']}–{entry['round_end']}"

    lines = [f"**Cash comparison — {set_label} round set, Medium:**"]
    for entry in result["entries"]:
        suffix = "" if entry["single_round"] else f" ({entry['rounds_counted']} rounds)"
        lines.append(
            f"• **{_label(entry)}** — **${_fmt_money(entry['earned'])}**{suffix}",
        )
    highest = result["highest"]
    if result["all_equal"]:
        lines.append(
            f"→ They earn the **same** (**${_fmt_money(highest['earned'])}**) each.",
        )
    elif len(result["entries"]) == 2:
        lowest = result["lowest"]
        lines.append(
            f"→ **{_label(highest)} earn more** by **${_fmt_money(result['spread'])}** "
            f"(vs {_label(lowest)}).",
        )
    else:
        lowest = result["lowest"]
        lines.append(
            f"→ Most: **{_label(highest)}** (${_fmt_money(highest['earned'])}). Least: "
            f"**{_label(lowest)}** (${_fmt_money(lowest['earned'])}). "
            f"Spread: **${_fmt_money(result['spread'])}**.",
        )
    lines.append(
        "_(Standard/Medium per-round cash, no income towers; each range is the "
        "inclusive sum of its rounds. Cash modifiers are not applied.)_",
    )
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_round_range_comparison_reply(message_text: str) -> str | None:
    """A code-built "which earns more cash, rounds X-Y or A-B" answer, or ``None``.

    The AI §7.5 *round-range* member of the multi-entity comparison floor — the
    income sibling of the cost builders. Ranks the total cash of **two or more**
    round ranges so the model can never mis-state which range earns more / by how
    much (the BUG-0009 "grounded values, wrong assembly" class). Fires only on an
    earning noun (``cash``/``money``/``income``/``earn``) **and** a comparison
    signal (``more``/``vs``/``or``/``compare`` …) **and** two-or-more parsed round
    ranges; an ABR cue routes the alternate round set. Returns ``None`` otherwise —
    a **single** range is the round-cash workflow's job (they stay non-overlapping
    on range count, and this floor short-circuits before the workflow runs), and
    strategy/recommendation questions reach the model untouched.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _EARN_NOUN_RE.search(low):
        return None
    if not _EARN_COMPARE_RE.search(low):
        return None
    if any(word in low for word in _EARN_STRATEGY_EXCLUDE):
        return None

    ranges = _extract_round_ranges(low)
    if len(ranges) < 2:
        return None

    from services import btd6_data_service
    from utils.btd6.keywords import ABR_CUE_RE

    roundset = "alternate" if ABR_CUE_RE.search(low) else "default"
    result = btd6_data_service.compare_round_ranges(ranges, roundset=roundset)
    if not result.get("found"):
        return None
    return _format_round_range_comparison(result)


def _scan_towers_with_positions(text_lower: str, dataset: Any) -> list[tuple[int, Any]]:
    """Every tower mentioned in ``text_lower``, as ``(start_index, tower)`` pairs
    in order of appearance, longest-surface-wins on overlap.

    Unlike :func:`_scan_tower` (which returns only the single best match), this
    finds *all* tower mentions so a multi-entity comparison can pair each with a
    crosspath. Whole-word matched on canonical names + aliases (≥3 chars), with an
    optional trailing ``s``. Overlapping matches (e.g. "super monkey" vs "monkey")
    resolve to the longest surface at that span.
    """
    spans: list[tuple[int, int, int, Any]] = []  # (start, end, surface_len, tower)
    for tower in dataset.towers:
        for surface in (tower.canonical, *tower.aliases):
            s = surface.lower()
            if len(s) < 3:
                continue
            for match in re.finditer(r"\b" + re.escape(s) + r"s?\b", text_lower):
                spans.append((match.start(), match.end(), len(s), tower))

    # Longest-surface-wins: walk by start, then by descending surface length, and
    # drop any span overlapping one already accepted.
    spans.sort(key=lambda sp: (sp[0], -sp[2]))
    accepted: list[tuple[int, int, Any]] = []
    for start, end, _slen, tower in spans:
        if any(start < a_end and end > a_start for a_start, a_end, _t in accepted):
            continue
        accepted.append((start, end, tower))
    accepted.sort(key=lambda a: a[0])
    return [(start, tower) for start, _end, tower in accepted]


def _extract_cost_comparison_candidates(
    text_lower: str,
    dataset: Any,
) -> list[tuple[str, str]]:
    """The ``(tower-canonical, crosspath-code)`` candidates a cost comparison names.

    Each tower mention is paired with the crosspath code immediately before it
    ("0-4-1 desperado"), within a short window; a tower with no preceding code is
    treated as the base tower (``000``). Deduped by ``(tower id, code)`` preserving
    order, so "0-4-1 desperado vs 2-0-4 desperado" yields two candidates while a
    repeated "the sniper … the sniper" yields one.
    """
    candidates: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for start, tower in _scan_towers_with_positions(text_lower, dataset):
        window = text_lower[max(0, start - 14) : start]
        code = "000"
        for cp in _CROSSPATH_RE.finditer(window):
            candidate_code = "".join(cp.groups())
            if tier_codes.is_legal(candidate_code):
                code = candidate_code  # last (closest to the tower) wins
        key = (tower.id, code)
        if key in seen:
            continue
        seen.add(key)
        candidates.append((tower.canonical, code))
    return candidates


def _format_cost_comparison(result: dict[str, Any]) -> str:
    diff = str(result["difficulty"]).capitalize()
    lines = [f"**Cost comparison — {diff} pricing:**"]
    for entry in result["entries"]:
        lines.append(
            f"• **{entry['tower']} {entry['code']}** ({entry['label']}) — "
            f"**${entry['unit_cost']:,}**",
        )
    cheapest = result["cheapest"]
    if result["all_equal"]:
        lines.append(
            f"→ They cost the **same** at **${cheapest['unit_cost']:,}** each.",
        )
    elif len(result["entries"]) == 2:
        lines.append(
            f"→ The **{cheapest['tower']} {cheapest['code']}** is cheaper by "
            f"**${result['spread']:,}**.",
        )
    else:
        dearest = result["most_expensive"]
        lines.append(
            f"→ Cheapest: **{cheapest['tower']} {cheapest['code']}** "
            f"(${cheapest['unit_cost']:,}). Most expensive: "
            f"**{dearest['tower']} {dearest['code']}** (${dearest['unit_cost']:,}). "
            f"Spread: **${result['spread']:,}**.",
        )
    lines.append(
        "_(Full per-tower cost: base + every upgrade, each purchase rounded to $5 "
        "at that difficulty, then summed.)_",
    )
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_cost_comparison_reply(message_text: str) -> str | None:
    """A code-built "which costs more / is cheaper" answer, or ``None``.

    The AI §7.5 multi-entity comparison floor. Fires only on a high-precision
    cost-compare cue (``cheaper``/``more expensive``/``compare … cost`` — never a
    bare "cheap"/"better") **and** at least two resolvable ``(tower, crosspath)``
    candidates. Returns ``None`` for single-entity cost lookups (handled by the
    grounding pricing leg), strategy/recommendation questions, and anything outside
    a clear two-or-more cost comparison — those reach the model untouched. The
    ranking is deterministic, so the model can never mis-state which is cheaper.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not (_COST_COMPARE_CUE_RE.search(low) or _COST_COMPARE_VERB_RE.search(low)):
        return None
    if any(word in low for word in _COST_COMPARE_STRATEGY_EXCLUDE):
        return None
    # A paragon cost comparison is the paragon builder's job — base-tower pricing
    # of a paragon's tower is the wrong answer (keeps the floor exactly-one-fires).
    if _PARAGON_CUE_RE.search(low):
        return None

    from services import btd6_data_service

    dataset = btd6_data_service.get_dataset()
    candidates = _extract_cost_comparison_candidates(low, dataset)
    if len(candidates) < 2:
        return None

    difficulty = "medium"
    diff_match = _COST_DIFFICULTY_RE.search(low)
    if diff_match:
        token = diff_match.group(1).lower()
        # CHIMPS is a mode, not a pricing difficulty — its prices are Hard's.
        difficulty = "hard" if token == "chimps" else token
        if difficulty == "impop":
            difficulty = "impoppable"

    result = btd6_data_service.compare_crosspath_costs(
        candidates,
        difficulty=difficulty,
    )
    if not result.get("found"):
        return None
    return _format_cost_comparison(result)


def _format_difficulty_cost_comparison(result: dict[str, Any]) -> str:
    tower = result["tower"]
    code = result["code"]
    label = result["label"]
    lines = [f"**Cost comparison — {tower} {code} ({label}) by difficulty:**"]
    for entry in result["entries"]:
        lines.append(
            f"• **{entry['difficulty'].capitalize()}** — **${entry['unit_cost']:,}**",
        )
    cheapest = result["cheapest"]
    if result["all_equal"]:
        lines.append(
            f"→ It costs the **same** (**${cheapest['unit_cost']:,}**) at every "
            "named difficulty.",
        )
    elif len(result["entries"]) == 2:
        dearest = result["most_expensive"]
        lines.append(
            f"→ Cheaper on **{cheapest['difficulty'].capitalize()}** by "
            f"**${result['spread']:,}** (vs **{dearest['difficulty'].capitalize()}**).",
        )
    else:
        dearest = result["most_expensive"]
        lines.append(
            f"→ Cheapest: **{cheapest['difficulty'].capitalize()}** "
            f"(${cheapest['unit_cost']:,}). Most expensive: "
            f"**{dearest['difficulty'].capitalize()}** (${dearest['unit_cost']:,}). "
            f"Spread: **${result['spread']:,}**.",
        )
    lines.append(
        "_(Same upgrade state priced at each difficulty: base + every tier, each "
        "purchase rounded to $5 at that difficulty, then summed.)_",
    )
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_difficulty_cost_comparison_reply(message_text: str) -> str | None:
    """A code-built "is it cheaper on easy or impoppable" answer, or ``None``.

    The AI §7.5 *difficulty* member of the multi-entity cost-comparison floor —
    the sibling of :func:`deterministic_cost_comparison_reply`, which ranks
    *different towers* at one difficulty. This ranks **one** upgrade state across
    two-or-more named difficulties, so the model can never mis-state which
    difficulty is cheaper / by how much. Fires only on a high-precision
    cost-compare cue, **exactly one** resolvable ``(tower, crosspath)`` candidate
    (two-or-more is the multi-tower builder's job — the two are mutually exclusive
    on candidate count), and **two-or-more** distinct named difficulties. Returns
    ``None`` otherwise (single-difficulty cost lookups, strategy questions, and
    anything outside a clear by-difficulty comparison reach the model untouched).
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not (_COST_COMPARE_CUE_RE.search(low) or _COST_COMPARE_VERB_RE.search(low)):
        return None
    if any(word in low for word in _COST_COMPARE_STRATEGY_EXCLUDE):
        return None
    # Paragon comparisons defer to the paragon builder (see the multi-tower one).
    if _PARAGON_CUE_RE.search(low):
        return None

    from services import btd6_data_service

    dataset = btd6_data_service.get_dataset()
    candidates = _extract_cost_comparison_candidates(low, dataset)
    if len(candidates) != 1:
        return None

    difficulties: list[str] = []
    seen: set[str] = set()
    for match in _COST_DIFFICULTY_RE.finditer(low):
        token = match.group(1).lower()
        if token == "impop":
            token = "impoppable"
        # CHIMPS prices as Hard — fold it so a phantom "hard vs chimps" dedups to
        # one entry and falls through to the model instead of a no-difference reply.
        elif token == "chimps":
            token = "hard"
        if token in seen:
            continue
        seen.add(token)
        difficulties.append(token)
    if len(difficulties) < 2:
        return None

    tower, code = candidates[0]
    result = btd6_data_service.compare_difficulty_costs(tower, code, difficulties)
    if not result.get("found"):
        return None
    return _format_difficulty_cost_comparison(result)


# --- §7.5 paragon base-cost comparison ----------------------------------------
def _extract_paragon_names(text_lower: str) -> list[str]:
    """The paragon ids a comparison names, in order of appearance, deduped.

    Scans every resolver surface (paragon names, tower names, ids, aliases) and
    keeps the longest surface at each span (so "ascended shadow" wins over a bare
    "ascended"), then dedups on the resolved id. Surfaces shorter than 3 chars are
    skipped to keep stray two-letter tokens out — the ``paragon`` word + cost cue
    already gate this builder hard. Returns ids (``resolve_paragon`` accepts them),
    so the data primitive re-resolves from a canonical key.
    """
    from utils.btd6 import paragon_math

    spans: list[tuple[int, int, int, str]] = []  # (start, end, surface_len, id)
    for surface, pid in paragon_math.paragon_surfaces():
        if len(surface) < 3:
            continue
        for match in re.finditer(r"\b" + re.escape(surface) + r"s?\b", text_lower):
            spans.append((match.start(), match.end(), len(surface), pid))

    spans.sort(key=lambda sp: (sp[0], -sp[2]))
    accepted: list[tuple[int, int, str]] = []
    for start, end, _slen, pid in spans:
        if any(start < a_end and end > a_start for a_start, a_end, _p in accepted):
            continue
        accepted.append((start, end, pid))
    accepted.sort(key=lambda a: a[0])

    seen: set[str] = set()
    names: list[str] = []
    for _start, _end, pid in accepted:
        if pid in seen:
            continue
        seen.add(pid)
        names.append(pid)
    return names


def _extract_hero_names(text_lower: str) -> list[str]:
    """The hero ids a comparison names, in order of appearance, deduped.

    Scans every hero surface (canonical + alias) and keeps the longest surface
    at each span (so "striker jones" wins over a bare "striker"), then dedups on
    the resolved hero id. Surfaces shorter than 3 chars are skipped so a stray
    one/two-letter alias ("q", "si") never trips the floor — the cost-compare cue
    + the ≥2-heroes gate already constrain this builder hard. Returns ids (the
    surface resolver accepts them), so the data primitive re-resolves cleanly.
    """
    from services import btd6_data_service

    heroes = btd6_data_service.get_dataset().heroes
    spans: list[tuple[int, int, int, str]] = []  # (start, end, surface_len, id)
    for hero in heroes:
        surfaces = {hero.canonical.lower(), *(a.lower() for a in hero.aliases)}
        for surface in surfaces:
            if len(surface) < 3:
                continue
            for match in re.finditer(r"\b" + re.escape(surface) + r"s?\b", text_lower):
                spans.append((match.start(), match.end(), len(surface), hero.id))

    spans.sort(key=lambda sp: (sp[0], -sp[2]))
    accepted: list[tuple[int, int, str]] = []
    for start, end, _slen, hid in spans:
        if any(start < a_end and end > a_start for a_start, a_end, _h in accepted):
            continue
        accepted.append((start, end, hid))
    accepted.sort(key=lambda a: a[0])

    seen: set[str] = set()
    names: list[str] = []
    for _start, _end, hid in accepted:
        if hid in seen:
            continue
        seen.add(hid)
        names.append(hid)
    return names


def _extract_power_names(text_lower: str) -> list[str]:
    """The power ids a comparison names, in order of appearance, deduped.

    Scans every power canonical (powers carry no aliases) and keeps the longest
    surface at each span (so "monkey boost pro" wins over a bare "monkey boost"),
    then dedups on the resolved power id. Surfaces shorter than 3 chars are
    skipped, though every power canonical is well over that — the cost-compare cue
    + the ≥2-powers gate already constrain this builder hard. Returns ids (the
    ``find_power`` resolver accepts them), so the data primitive re-resolves
    cleanly.
    """
    from services import btd6_data_service

    powers = btd6_data_service.get_dataset().powers
    spans: list[tuple[int, int, int, str]] = []  # (start, end, surface_len, id)
    for power in powers:
        surface = power.canonical.lower()
        if len(surface) < 3:
            continue
        for match in re.finditer(r"\b" + re.escape(surface) + r"s?\b", text_lower):
            spans.append((match.start(), match.end(), len(surface), power.id))

    spans.sort(key=lambda sp: (sp[0], -sp[2]))
    accepted: list[tuple[int, int, str]] = []
    for start, end, _slen, pid in spans:
        if any(start < a_end and end > a_start for a_start, a_end, _p in accepted):
            continue
        accepted.append((start, end, pid))
    accepted.sort(key=lambda a: a[0])

    seen: set[str] = set()
    names: list[str] = []
    for _start, _end, pid in accepted:
        if pid in seen:
            continue
        seen.add(pid)
        names.append(pid)
    return names


def _format_hero_cost_comparison(result: dict[str, Any]) -> str:
    diff = str(result["difficulty"]).capitalize()
    lines = [f"**Hero cost comparison — {diff} placement cost:**"]
    for entry in result["entries"]:
        lines.append(f"• **{entry['name']}** — **${entry['base_cost']:,}**")
    cheapest = result["cheapest"]
    if result["all_equal"]:
        lines.append(
            f"→ They cost the **same** to place (**${cheapest['base_cost']:,}** each).",
        )
    elif len(result["entries"]) == 2:
        lines.append(
            f"→ The **{cheapest['name']}** is cheaper by **${result['spread']:,}**.",
        )
    else:
        dearest = result["most_expensive"]
        lines.append(
            f"→ Cheapest: **{cheapest['name']}** (${cheapest['base_cost']:,}). Most "
            f"expensive: **{dearest['name']}** (${dearest['base_cost']:,}). "
            f"Spread: **${result['spread']:,}**.",
        )
    lines.append("_(Base placement cost at that difficulty — abilities are free.)_")
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_hero_cost_comparison_reply(message_text: str) -> str | None:
    """A code-built "is Quincy or Benjamin cheaper" answer, or ``None``.

    The AI §7.5 *hero* member of the multi-entity cost-comparison floor — the
    hero-entity sibling of :func:`deterministic_cost_comparison_reply` (towers),
    :func:`deterministic_difficulty_cost_comparison_reply` (one tower by
    difficulty), and :func:`deterministic_paragon_cost_comparison_reply`
    (paragons). Ranks the **base placement cost** of two-or-more heroes so the
    model can never mis-state which is cheaper / by how much (the BUG-0009
    "grounded values, wrong assembly" class). Fires on a high-precision
    cost-compare cue **and** two-or-more resolved heroes; defers on a ``paragon``
    cue (the paragon builder's job), strategy/recommendation questions, and
    single-hero lookups, which all reach the model untouched. Mutually exclusive
    with the tower/difficulty builders by construction — those need a resolvable
    ``(tower, crosspath)`` candidate, which a hero name never produces.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not (_COST_COMPARE_CUE_RE.search(low) or _COST_COMPARE_VERB_RE.search(low)):
        return None
    if any(word in low for word in _COST_COMPARE_STRATEGY_EXCLUDE):
        return None
    # A paragon cost comparison is the paragon builder's job.
    if _PARAGON_CUE_RE.search(low):
        return None

    names = _extract_hero_names(low)
    if len(names) < 2:
        return None

    difficulty = "medium"
    diff_match = _COST_DIFFICULTY_RE.search(low)
    if diff_match:
        token = diff_match.group(1).lower()
        # CHIMPS is a mode, not a pricing difficulty — its prices are Hard's.
        difficulty = "hard" if token == "chimps" else token
        if difficulty == "impop":
            difficulty = "impoppable"

    from services import btd6_data_service

    result = btd6_data_service.compare_hero_costs(names, difficulty=difficulty)
    if not result.get("found"):
        return None
    return _format_hero_cost_comparison(result)


def _format_power_cost_comparison(result: dict[str, Any]) -> str:
    lines = ["**Power cost comparison — Monkey Money store price:**"]
    for entry in result["entries"]:
        lines.append(f"• **{entry['name']}** — **{entry['cost']:,} MM**")
    cheapest = result["cheapest"]
    if result["all_equal"]:
        lines.append(
            f"→ They cost the **same** (**{cheapest['cost']:,} MM** each).",
        )
    elif len(result["entries"]) == 2:
        lines.append(
            f"→ The **{cheapest['name']}** is cheaper by **{result['spread']:,} MM**.",
        )
    else:
        dearest = result["most_expensive"]
        lines.append(
            f"→ Cheapest: **{cheapest['name']}** ({cheapest['cost']:,} MM). Most "
            f"expensive: **{dearest['name']}** ({dearest['cost']:,} MM). "
            f"Spread: **{result['spread']:,} MM**.",
        )
    lines.append("_(Monkey Money store price — the same on every difficulty.)_")
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_power_cost_comparison_reply(message_text: str) -> str | None:
    """A code-built "is Cash Drop or Monkey Boost cheaper" answer, or ``None``.

    The AI §7.5 *power* member of the multi-entity cost-comparison floor — the
    activated-ability sibling of :func:`deterministic_cost_comparison_reply`
    (towers), :func:`deterministic_difficulty_cost_comparison_reply`,
    :func:`deterministic_paragon_cost_comparison_reply`, and
    :func:`deterministic_hero_cost_comparison_reply`. Ranks the **Monkey Money**
    store price of two-or-more powers so the model can never mis-state which is
    cheaper / by how much (the BUG-0009 "grounded values, wrong assembly" class).
    Fires on a high-precision cost-compare cue **and** two-or-more resolved powers;
    defers on a ``paragon`` cue (the paragon builder's job), strategy /
    recommendation questions, and single-power lookups, which all reach the model
    untouched. Mutually exclusive with the tower/hero/paragon builders by
    construction — those resolve a ``(tower, crosspath)`` / hero / paragon
    candidate, which a power name never produces.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not (_COST_COMPARE_CUE_RE.search(low) or _COST_COMPARE_VERB_RE.search(low)):
        return None
    if any(word in low for word in _COST_COMPARE_STRATEGY_EXCLUDE):
        return None
    # A paragon cost comparison is the paragon builder's job.
    if _PARAGON_CUE_RE.search(low):
        return None

    names = _extract_power_names(low)
    if len(names) < 2:
        return None

    from services import btd6_data_service

    result = btd6_data_service.compare_power_costs(names)
    if not result.get("found"):
        return None
    return _format_power_cost_comparison(result)


def _format_paragon_cost_comparison(result: dict[str, Any]) -> str:
    diff = str(result["difficulty"]).capitalize()
    lines = [f"**Paragon cost comparison — {diff} base price:**"]
    for entry in result["entries"]:
        lines.append(
            f"• **{entry['name']}** ({entry['tower']}) — **${entry['base_cost']:,}**",
        )
    cheapest = result["cheapest"]
    if result["all_equal"]:
        lines.append(
            f"→ They cost the **same** to build (**${cheapest['base_cost']:,}** each).",
        )
    elif len(result["entries"]) == 2:
        lines.append(
            f"→ The **{cheapest['name']}** is cheaper by **${result['spread']:,}**.",
        )
    else:
        dearest = result["most_expensive"]
        lines.append(
            f"→ Cheapest: **{cheapest['name']}** (${cheapest['base_cost']:,}). Most "
            f"expensive: **{dearest['name']}** (${dearest['base_cost']:,}). "
            f"Spread: **${result['spread']:,}**.",
        )
    lines.append(
        "_(Base tier-6 build price at that difficulty — the degree-grind "
        "sacrifices are extra and depend on your build.)_",
    )
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_paragon_cost_comparison_reply(message_text: str) -> str | None:
    """A code-built "is Glaive Dominus or Ascended Shadow cheaper" answer, or ``None``.

    The AI §7.5 *paragon* member of the multi-entity cost-comparison floor — the
    paragon-entity sibling of :func:`deterministic_cost_comparison_reply` (which
    ranks tower upgrade states). Ranks the **base build price** of two-or-more
    paragons so the model can never mis-state which is cheaper / by how much (the
    BUG-0009 "grounded values, wrong assembly" class). Fires only on an explicit
    ``paragon`` token **and** a high-precision cost-compare cue **and** two-or-more
    resolved paragons. The ``paragon`` token is also what makes this mutually
    exclusive with the tower cost builders — they defer the moment "paragon" is
    present (a "dart/ninja paragon" question must not be priced as the base tower).
    Returns ``None`` otherwise (single-paragon lookups, strategy questions, and
    anything outside a clear two-or-more paragon cost comparison reach the model).
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _PARAGON_CUE_RE.search(low):
        return None
    if not (_COST_COMPARE_CUE_RE.search(low) or _COST_COMPARE_VERB_RE.search(low)):
        return None
    if any(word in low for word in _COST_COMPARE_STRATEGY_EXCLUDE):
        return None

    names = _extract_paragon_names(low)
    if len(names) < 2:
        return None

    difficulty = "medium"
    diff_match = _COST_DIFFICULTY_RE.search(low)
    if diff_match:
        token = diff_match.group(1).lower()
        # CHIMPS is a mode, not a pricing difficulty — its prices are Hard's.
        difficulty = "hard" if token == "chimps" else token
        if difficulty == "impop":
            difficulty = "impoppable"

    from services import btd6_data_service

    result = btd6_data_service.compare_paragon_costs(names, difficulty=difficulty)
    if not result.get("found"):
        return None
    return _format_paragon_cost_comparison(result)


# --- "which towers pop lead / see camo" capability roster (AI §7) -------------
# A capability/property roster ("which towers pop lead without upgrades", "what
# towers detect camo", "which monkeys pop purple") is the BUG-0009 wrong-assembly
# class: the model assembles the roster itself and can include/exclude the wrong
# towers, and because every tower NAME is grounded the value-only faithfulness
# guard never catches a mis-*roster*. The authoritative answer is already derived
# deterministically by services.btd6_capability_service (from the committed
# per-tier stats), so the floor OWNS the labelled list.
#
# High-precision firing: a capability cue (camo + a detection verb, OR a pop verb
# + a named bloon type) AND a roster discovery shape ("which/what ... towers"),
# with strategy/opinion deferred to the model.
_CAP_CAMO_RE = re.compile(r"\bcamo(?:flage)?\b", re.I)
_CAP_CAMO_VERB_RE = re.compile(
    r"\b(?:detect|detects|detecting|detection|see|sees|seeing|reveal|reveals"
    r"|spot|spots)\b",
    re.I,
)
# A popping verb is required for the bloon-immunity capabilities so a stray colour
# word ("the white monkey", "purple is the best path") never trips the floor.
_CAP_POP_VERB_RE = re.compile(r"\bpop(?:s|ped|ping)?\b", re.I)
# (capability-key prefix, the bloon word that must appear with a pop verb). The
# key matches services.btd6_capability_service.<KEY>_POPPING.
_CAP_BLOON_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("lead", r"\blead\b"),
    ("black", r"\bblack\b"),
    ("white", r"\bwhite\b"),
    ("purple", r"\bpurple\b"),
)
# The roster discovery shape: a "which/what/list ... tower(s)/paragon(s)/monkey(s)"
# question, or "tower(s) ... which/that/can". Keeps single-entity lookups ("does
# the dartling see camo") and yes/no checks out of the roster floor.
_CAP_SHAPE_RE = re.compile(
    r"\b(?:which|what|list|name|all|every)\b.{0,40}"
    r"\b(?:towers?|paragons?|monkeys?)\b|"
    r"\b(?:towers?|paragons?|monkeys?)\b.{0,40}\b(?:which|that|can)\b",
    re.I,
)
# An explicit "with upgrades / ever" signal flips the roster from the base (0-0-0)
# default to the earliest-upgrade roster.
_CAP_UPGRADED_RE = re.compile(
    r"\bwith\s+upgrades?\b|\bupgraded\b|\bever\b|\beventually\b|\bany\s+tower\b|"
    r"\bat\s+any\s+(?:tier|upgrade)\b",
    re.I,
)
# Human labels for the roster header.
_CAP_LABELS: dict[str, str] = {
    "camo_detection": "detect Camo",
    "lead_popping": "pop Lead",
    "black_popping": "pop Black",
    "white_popping": "pop White",
    "purple_popping": "pop Purple",
}


def _match_capability(text_lower: str) -> str | None:
    """Resolve the single capability key a roster question asks about, or ``None``."""
    from services import btd6_capability_service as cap_svc

    if _CAP_CAMO_RE.search(text_lower) and _CAP_CAMO_VERB_RE.search(text_lower):
        return cap_svc.CAMO_DETECTION
    if _CAP_POP_VERB_RE.search(text_lower):
        pop_keys = {
            "lead": cap_svc.LEAD_POPPING,
            "black": cap_svc.BLACK_POPPING,
            "white": cap_svc.WHITE_POPPING,
            "purple": cap_svc.PURPLE_POPPING,
        }
        for prefix, pattern in _CAP_BLOON_KEYWORDS:
            if re.search(pattern, text_lower):
                return pop_keys[prefix]
    return None


def _format_capability_roster(
    capability: str,
    hits: list[Any],
    *,
    upgraded: bool,
) -> str:
    """Render the labelled tower roster for a resolved capability."""
    label = _CAP_LABELS.get(capability, capability.replace("_", " "))
    scope = "(any tier, earliest shown)" if upgraded else "without upgrades (base tier)"
    if not hits:
        return f"**BTD6 — no tower can {label} {scope}.**"
    lines = [f"**BTD6 towers that {label} {scope} ({len(hits)}):**"]
    lines.extend(f"• **{hit.canonical}** — {hit.detail}" for hit in hits)
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def _format_paragon_capability_roster(hits: list[Any]) -> str | None:
    """Render the per-paragon Camo-detection roster (yes/no), or ``None`` if empty."""
    if not hits:
        return None
    yes = [h for h in hits if h.has_capability]
    no = [h for h in hits if not h.has_capability]
    lines = [f"**BTD6 paragons and Camo detection ({len(hits)}):**"]
    if yes:
        names = ", ".join(f"**{h.paragon}**" for h in yes)
        lines.append(f"__Detect Camo innately ({len(yes)})__: {names}")
    if no:
        names = ", ".join(f"**{h.paragon}**" for h in no)
        lines.append(f"__Need external Camo support ({len(no)})__: {names}")
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_capability_roster_reply(message_text: str) -> str | None:
    """A code-built "which towers have capability X" roster, or ``None``.

    Fires on a clear capability-roster question — "which towers pop lead without
    upgrades", "what towers detect camo", "which monkeys pop purple" — the
    BUG-0009 wrong-assembly class: every tower name is grounded, so the model can
    silently mis-*roster* (include a tower that can't, drop one that can) and the
    value-only faithfulness guard never catches it. The roster is derived
    deterministically by :mod:`services.btd6_capability_service` from the committed
    per-tier stats, so the floor OWNS the labelled list.

    Scope: base (0-0-0) by default — the genuinely-confused "innate" question; an
    explicit "with upgrades / ever" signal flips it to the earliest-upgrade
    roster. A ``paragon`` cue answers the per-paragon Camo roster (the only
    per-paragon capability the service verifies). Returns ``None`` for
    single-entity lookups, strategy/opinion, and anything outside the roster shape.
    """
    text = (message_text or "").strip().lower()
    if not text:
        return None
    if any(word in text for word in _ROSTER_STRATEGY_WORDS):
        return None
    if not _CAP_SHAPE_RE.search(text):
        return None

    from services import btd6_capability_service as cap_svc

    capability = _match_capability(text)
    if capability is None:
        return None

    if _PARAGON_CUE_RE.search(text):
        # Only Camo is verified per-paragon; defer other capabilities to the model.
        if capability != cap_svc.CAMO_DETECTION:
            return None
        return _format_paragon_capability_roster(
            cap_svc.paragons_with_capability(capability),
        )

    upgraded = bool(_CAP_UPGRADED_RE.search(text))
    hits = cap_svc.towers_with_capability(capability, unupgraded=not upgraded)
    return _format_capability_roster(capability, hits, upgraded=upgraded)


# --- "which bloons are immune to X / list the MOAB-class bloons" (AI §7) -------
# A bloon roster ("what are all the MOAB-class bloons", "which bloons are immune
# to sharp") is the same wrong-assembly class as the tower-capability floor above,
# on the other side of the matchup: the model assembles the bloon list itself and
# can miscount the blimp tier or mis-state an immunity, and because every bloon
# NAME is grounded the value-only faithfulness guard never catches a mis-roster.
# btd6_data_service exposes the committed bloon fields (category · immune_to), so
# the floor OWNS the labelled list. The sibling roster floor
# (deterministic_roster_reply) covers heroes/towers/paragons/maps but NOT bloons.
_BLOON_SUBJECT_RE = re.compile(r"\bbloons?\b|\bblimps?\b|\bmoab", re.I)
_BLOON_MOAB_CUE_RE = re.compile(r"\bmoab[-\s]?class\b|\bblimps?\b|\bmoab\b", re.I)
_BLOON_IMMUNE_CUE_RE = re.compile(
    r"\bimmune\b|\bimmunit|\bresist(?:s|ant|ance)?\b|"
    r"\bcan'?t\s+be\s+(?:popped|damaged|hurt)\b",
    re.I,
)
# A strict enumeration signal for the MOAB-class list (a bare "what"/"which" is
# NOT enough — "what is a moab" is a single lookup, not a roster).
_BLOON_MOAB_LIST_RE = re.compile(
    r"\blist\b|\bname\b|\ball\b|\bevery\b|\bhow many\b|\bwhich\b|\bwhat are\b|"
    r"\bthere are\b|\bare there\b",
    re.I,
)
# A looser enumeration signal for the immunity roster (the damage-keyword gate
# already keeps single-entity "is the lead immune to sharp" out — it has no
# which/what/list cue — so "what bloons" is safe to accept here).
_BLOON_IMMUNE_LIST_RE = re.compile(
    r"\bwhich\b|\bwhat\b|\blist\b|\bname\b|\ball\b|\bevery\b|\bhow many\b",
    re.I,
)
# (regex over the question, the canonical immune_to damage label). Order matters:
# the specific cold sub-types (Glacier/Frigid) are matched before generic cold/ice.
_BLOON_DAMAGE_KEYWORDS: tuple[tuple[str, str], ...] = (
    (r"\bexplos|\bbomb\b", "Explosion"),
    (r"\bfire\b|\bflame\b|\bburn", "Fire"),
    (r"\benerg", "Energy"),
    (r"\bplasma\b", "Plasma"),
    (r"\bglacier\b", "Glacier"),
    (r"\bfrigid\b", "Frigid"),
    (r"\bcold\b|\bice\b|\bfreez", "Cold"),
    (r"\bshatter", "Shatter"),
    (r"\bsharp", "Sharp"),
    (r"\bacid\b", "Acid"),
)


def _match_bloon_damage(text_lower: str) -> str | None:
    """The canonical immune_to damage label a question names, or ``None``."""
    for pattern, label in _BLOON_DAMAGE_KEYWORDS:
        if re.search(pattern, text_lower):
            return label
    return None


def _format_moab_class_roster(hits: list[Any]) -> str | None:
    if not hits:
        return None
    names = ", ".join(f"**{b.canonical}**" for b in hits)
    return f"**BTD6 MOAB-class bloons ({len(hits)})** — the blimp tier: {names}."


def _format_bloon_immunity_roster(label: str, hits: list[Any]) -> str:
    if not hits:
        return f"**BTD6 — no bloon is immune to {label} damage.**"
    names = ", ".join(f"**{b.canonical}**" for b in hits)
    return f"**BTD6 bloons immune to {label} damage ({len(hits)}):** {names}."


# --- "HP of <bloon> at round N" deterministic reply ---------------------------
# Owns the round-scaled bloon-health answer. The bot previously said a BAD "keeps
# its 20,000 HP base" on round 100 — wrong: MOAB-class bloons take a runtime
# late-game/freeplay health ramp (+2%/round from round 81; v(100)=1.40), so a BAD
# first spawns on round 100 already at 28,000 HP. The ramp is not in the dump
# (curated in bloon_scaling.json), and the base-only grounding let the model
# flatten it — so the deterministic layer OWNS the round-specific value. Fires
# only on a bloon + a round number + a health cue; otherwise defers (the base
# "how much HP does a BAD have" question still reaches the model with grounding).
_BLOON_HEALTH_CUE_RE = re.compile(r"\b(?:health|hp|hit\s?points?|hitpoints?)\b", re.I)
_BLOON_FORTIFIED_CUE_RE = re.compile(r"\bfortif(?:ied|y|ication)\b", re.I)


def _resolve_bloon_in_text(text_lower: str) -> Any | None:
    """The BloonEntry whose name/alias appears in ``text_lower``, or ``None``.

    Whole-word match against every bloon's id / canonical / aliases (modifier
    marker rows excluded), preferring the longest matched surface so "big airship
    of doom" beats a stray "bad" and a specific blimp beats a generic word.
    """
    from services import btd6_data_service

    best: Any | None = None
    best_len = 0
    for bloon in btd6_data_service.get_dataset().bloons:
        if bloon.category == "modifier":
            continue
        surfaces = {
            bloon.id,
            bloon.canonical.lower(),
            *(a.lower() for a in bloon.aliases),
        }
        for surface in surfaces:
            if not surface:
                continue
            if (
                re.search(rf"\b{re.escape(surface)}\b", text_lower)
                and len(surface) > best_len
            ):
                best, best_len = bloon, len(surface)
    return best


def deterministic_bloon_health_reply(message_text: str) -> str | None:
    """A code-built "HP of <bloon> on round N" answer, or ``None``.

    Fires on a resolvable bloon + a round number + a health/HP cue, served as a
    pre-emptive floor. For MOAB-class bloons it applies the late-game/freeplay
    ramp (``bloon_health_at_round``); for everything else it states the flat base
    health and that only MOAB-class bloons scale. Defers (``None``) without all
    three signals, or when the bloon's base health / scaling data is unavailable —
    those reach the model.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _BLOON_HEALTH_CUE_RE.search(low):
        return None
    number_match = _ROUND_XP_NUMBER_RE.search(low)
    if number_match is None:
        return None
    round_number = int(number_match.group(1) or number_match.group(2))
    bloon = _resolve_bloon_in_text(low)
    if bloon is None:
        return None

    from services import btd6_data_service

    fortified = bool(_BLOON_FORTIFIED_CUE_RE.search(low))
    base = bloon.health_fortified if fortified else bloon.health
    if not isinstance(base, int):
        return None
    fort_label = "fortified " if fortified else ""

    if bloon.category != "moab_class":
        return (
            f"A {fort_label}**{bloon.canonical}** has **{base:,} HP** — its health "
            f"is the same on every round. Only MOAB-class bloons "
            f"(MOAB/BFB/ZOMG/DDT/BAD) scale with the round in late game / freeplay "
            f"(from round 81); other bloons keep their base health."
        )

    scaled = btd6_data_service.bloon_health_at_round(
        bloon.id,
        round_number,
        fortified=fortified,
    )
    multiplier = btd6_data_service.moab_class_health_multiplier(round_number)
    if scaled is None or multiplier is None:
        return None
    rbe = btd6_data_service.bloon_rbe_at_round(
        bloon.id,
        round_number,
        fortified=fortified,
    )
    rbe_clause = f" and **{rbe:,} RBE**" if isinstance(rbe, int) else ""
    return (
        f"A {fort_label}**{bloon.canonical}** has **{scaled:,} HP**{rbe_clause} on "
        f"**round {round_number}** — base **{base:,}** × **{multiplier:g}** "
        f"late-game/freeplay scaling. MOAB-class bloons get tougher each round from "
        f"round 81 (×1.4 by round 100, then steepening sharply), so they sit well "
        f"above their {base:,} base on late rounds. (Runtime ramp — health and the "
        f"recomputed spawn-tree RBE — not stored in the game files.)"
    )


def deterministic_bloon_roster_reply(message_text: str) -> str | None:
    """A code-built bloon roster — MOAB-class list or immunity roster — or ``None``.

    Fires on a clear bloon enumeration: "what are all the MOAB-class bloons /
    blimps" (the category list) or "which bloons are immune to <damage>" (the
    immunity roster). Same wrong-assembly class as the tower-capability floor —
    every bloon name is grounded, so the model can miscount/mis-state and the
    value-only guard never catches the mis-roster. Defers (``None``) for
    single-bloon lookups ("what is a moab", "is the lead immune to sharp"),
    strategy/opinion, and anything without a bloon subject + enumeration shape.
    """
    text = (message_text or "").strip().lower()
    if not text:
        return None
    if any(word in text for word in _ROSTER_STRATEGY_WORDS):
        return None
    if not _BLOON_SUBJECT_RE.search(text):
        return None

    from services import btd6_data_service

    # "modifier" rows (camo / fortified / regrow) are property markers, not bloons.
    bloons = [
        b for b in btd6_data_service.get_dataset().bloons if b.category != "modifier"
    ]

    if _BLOON_IMMUNE_CUE_RE.search(text):
        if not _BLOON_IMMUNE_LIST_RE.search(text):
            return None
        label = _match_bloon_damage(text)
        if label is None:
            return None
        hits = [b for b in bloons if label in (b.immune_to or ())]
        return _format_bloon_immunity_roster(label, hits)

    if _BLOON_MOAB_CUE_RE.search(text) and _BLOON_MOAB_LIST_RE.search(text):
        hits = [b for b in bloons if b.category == "moab_class"]
        return _format_moab_class_roster(hits)

    return None


# --- §7.6 bloon-modifier explainer (slot-4 reframe, BUG-0009) -----------------
# Camo / Fortified / Regrow are universal *modifiers* applied to ANY bloon, not
# per-type properties — so "which bloons are camo?" has no clean roster (the
# night-queue slot-4 finding: a roster would wrongly imply only DDT can be camo),
# and "what does camo do?" on the general path is the BUG-0009 freelance class.
# The dataset files each modifier as a category=="modifier" marker carrying its
# description; this floor OWNS the grounded explanation + the "it can apply to any
# bloon" correction. Distinct from deterministic_bloon_roster_reply (which
# EXCLUDES modifier rows and fires only on the MOAB/immunity roster shapes) and
# from the capability roster (towers detecting camo) — it defers whenever a
# tower, a detection/pop verb, or a tower-subject is present, so none overlap.
_BLOON_MODIFIER_CUES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("camo", re.compile(r"\bcamo(?:flage)?\b", re.I)),
    ("fortified", re.compile(r"\bfortif(?:ied|y|ication)\b", re.I)),
    ("regrow", re.compile(r"\bregrow(?:th|s|ing)?\b", re.I)),
)
# The generic "what are the bloon modifiers/properties" ask (no specific one).
_BLOON_MODIFIER_GENERIC_RE = re.compile(
    r"\bbloons?\s+(?:modifiers?|propert(?:y|ies))\b|"
    r"\b(?:modifiers?|propert(?:y|ies))\s+(?:of|on|for)\s+(?:a\s+)?bloons?\b",
    re.I,
)
# A definition/roster-attempt shape — keeps a stray modifier word inside an
# unrelated sentence out, and is broad enough to catch both "what does camo do"
# and the (reframed) "which bloons are camo".
_BLOON_MODIFIER_SHAPE_RE = re.compile(
    r"\b(?:what|which|whats|explain|describe|tell|list|mean(?:s|ing)?|"
    r"is|are|does|do|have|property|modifier)\b",
    re.I,
)
# A tower-subject cue → the question is really about a tower's capability, not the
# modifier itself; defer to the model / capability roster.
_BLOON_MODIFIER_TOWER_SUBJECT_RE = re.compile(
    r"\btowers?\b|\bmonkeys?\b|\bparagons?\b|\bheroe?s?\b",
    re.I,
)


def _format_bloon_modifier(entry: Any) -> str:
    label = entry.canonical.removesuffix(" property").strip() or entry.canonical
    return (
        f"**{label} is a bloon modifier, not a bloon type.** {entry.description} "
        "It can be applied to many different bloons (set by the round / game mode), "
        "so there is no fixed list of "
        f"“{label.lower()} bloons.”"
    )


def deterministic_bloon_modifier_reply(message_text: str) -> str | None:
    """A code-built explainer for a bloon modifier (Camo/Fortified/Regrow), or ``None``.

    The §7.6 slot-4 *reframe*: "what does camo do?", "which bloons are camo?",
    "explain the regrow property" — the model either explains the modifier wrong
    or assembles a misleading "camo bloons" roster (BUG-0009), because camo /
    fortified / regrow are universal modifiers, not per-type properties. This
    floor OWNS the grounded explanation from the dataset's modifier marker
    entries. Defers (``None``) when a **tower**, a detection/pop **verb**, or a
    tower-subject is present (those are the capability roster's / model's job),
    on strategy/opinion, and when no modifier is named — so it never overlaps the
    bloon roster (MOAB/immunity) or the capability roster.
    """
    text = (message_text or "").strip().lower()
    if not text:
        return None
    if any(word in text for word in _ROSTER_STRATEGY_WORDS):
        return None
    # A tower's camo-detection / popping question belongs to the capability floor.
    if _CAP_CAMO_VERB_RE.search(text) or _CAP_POP_VERB_RE.search(text):
        return None
    if _BLOON_MODIFIER_TOWER_SUBJECT_RE.search(text):
        return None

    from services import btd6_data_service

    if _scan_tower(text, btd6_data_service.get_dataset()) is not None:
        return None

    named = [key for key, pattern in _BLOON_MODIFIER_CUES if pattern.search(text)]
    generic = bool(_BLOON_MODIFIER_GENERIC_RE.search(text))
    if not named and not generic:
        return None
    if not _BLOON_MODIFIER_SHAPE_RE.search(text):
        return None

    modifiers = {m.id: m for m in btd6_data_service.bloon_modifiers()}
    if not modifiers:
        return None

    # A single named modifier → its explanation.
    if len(named) == 1 and named[0] in modifiers:
        return _format_bloon_modifier(modifiers[named[0]])

    # Several named, or a generic "bloon modifiers" ask → all of them.
    wanted = [modifiers[k] for k in named if k in modifiers] or list(modifiers.values())
    lines = [
        "**BTD6 bloon modifiers** — these apply to bloons, they are not bloon types:",
    ]
    for entry in wanted:
        label = entry.canonical.removesuffix(" property").strip() or entry.canonical
        lines.append(f"• **{label}** — {entry.description}")
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


# --- §7.6 relic category/effect roster (AI §7) --------------------------------
# "what economy relics are there", "list all offensive relics", "which relics are
# utility" is the BUG-0009 wrong-assembly class: the model buckets the relics by
# category itself and can mis-bucket one (every relic NAME is grounded, so the
# value-only faithfulness guard never catches a mis-*grouping*). The authoritative
# grouping is derived deterministically by btd6_data_service.relics_by_category, so
# the floor OWNS the labelled list.
_RELIC_SUBJECT_RE = re.compile(r"\brelics?\b", re.I)
# An enumeration shape ("which/what/list ... relics", or "relics ... which/that/are
# there"), so single-relic effect lookups ("what does the el dorado relic do") and
# yes/no checks stay out of the roster floor.
_RELIC_LIST_RE = re.compile(
    r"\b(?:which|what|list|name|all|every|how\s+many)\b.{0,40}\brelics?\b|"
    r"\brelics?\b.{0,40}\b(?:which|that|are\s+there|exist)\b",
    re.I,
)
# (category key, the cue that names it). The key matches a btd6_data_service
# relic category; the order mirrors _RELIC_CATEGORY_ORDER.
_RELIC_CATEGORY_CUES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("offense", re.compile(r"\boffens(?:e|ive)\b|\bdamage\b|\battack(?:ing)?\b", re.I)),
    ("economy", re.compile(r"\beconom(?:y|ic)\b|\bcash\b|\bmoney\b|\bincome\b", re.I)),
    ("lives", re.compile(r"\blives\b|\bhealth\b|\bhp\b", re.I)),
    ("powerup", re.compile(r"\bpower[\s-]?ups?\b|\bpowerups?\b", re.I)),
    ("utility", re.compile(r"\butility\b|\butilit(?:ies|y)\b", re.I)),
)
# Human labels for the roster header.
_RELIC_CATEGORY_LABELS: dict[str, str] = {
    "offense": "Offense",
    "economy": "Economy",
    "lives": "Lives",
    "powerup": "Power-up",
    "utility": "Utility",
}


def _match_relic_category(text_lower: str) -> str | None:
    """The single relic category a roster question names, or ``None`` for all."""
    for category, pattern in _RELIC_CATEGORY_CUES:
        if pattern.search(text_lower):
            return category
    return None


def _mentions_specific_relic(text_lower: str) -> bool:
    """True when the message names a specific relic (an effect lookup, not a roster).

    Scans every relic surface (canonical + aliases + abbrev) so "what does the el
    dorado relic do" — which matches the enumeration regex by accident — is
    recognised as a single-relic lookup and deferred to the model. Surfaces under
    3 chars are skipped so a stray short token never trips the guard.
    """
    from services import btd6_data_service

    for relic in btd6_data_service.get_dataset().ct_relics:
        surfaces = {
            relic.canonical.lower(),
            relic.abbrev.lower(),
            *(a.lower() for a in relic.aliases),
        }
        for surface in surfaces:
            if len(surface) < 3:
                continue
            if re.search(r"\b" + re.escape(surface) + r"s?\b", text_lower):
                return True
    return False


def _format_relic_category_roster(category: str, relics: list[Any]) -> str:
    label = _RELIC_CATEGORY_LABELS.get(category, category.capitalize())
    if not relics:
        return f"**BTD6 — no {label} relics in the catalog.**"
    lines = [f"**BTD6 {label} relics ({len(relics)}):**"]
    lines.extend(f"• **{relic.canonical}** — {relic.effect}" for relic in relics)
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def _format_all_relics_roster(grouped: dict[str, tuple[Any, ...]]) -> str:
    total = sum(len(rels) for rels in grouped.values())
    lines = [f"**BTD6 Contested Territory relics by category ({total}):**"]
    for category, label in _RELIC_CATEGORY_LABELS.items():
        rels = grouped.get(category, ())
        if not rels:
            continue
        names = ", ".join(relic.canonical for relic in rels)
        lines.append(f"__{label}__ ({len(rels)}): {names}")
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_relic_roster_reply(message_text: str) -> str | None:
    """A code-built relic-by-category roster, or ``None``.

    The §7.6 *relic* member of the BUG-0009 roster floor — the sibling of
    :func:`deterministic_capability_roster_reply` (towers) and
    :func:`deterministic_bloon_roster_reply` (bloons). Fires on a relic
    enumeration: a named category ("what economy relics are there", "list all
    offensive relics", "which relics are utility") lists that category's relics +
    effects; a bare "what relics are there" / "list all relics" lists every relic
    grouped by category. Defers (``None``) for single-relic effect lookups ("what
    does the el dorado relic do"), strategy/opinion, and anything without the
    relic subject + an enumeration shape — those reach the model untouched.
    Mutually exclusive with the other floor builders by construction: it requires
    the literal ``relic`` token, which the tower/bloon/power/comparison builders
    never key on.
    """
    text = (message_text or "").strip().lower()
    if not text:
        return None
    if any(word in text for word in _ROSTER_STRATEGY_WORDS):
        return None
    if not _RELIC_SUBJECT_RE.search(text):
        return None
    if not _RELIC_LIST_RE.search(text):
        return None

    from services import btd6_data_service

    category = _match_relic_category(text)
    grouped = btd6_data_service.relics_by_category()
    if category is not None:
        return _format_relic_category_roster(category, list(grouped.get(category, ())))
    # An ungrouped "all relics" ask — but defer if it actually names one relic
    # (an effect lookup that matched the enumeration regex by accident).
    if _mentions_specific_relic(text):
        return None
    return _format_all_relics_roster(grouped)


# --- §7.6 hero ability roster (AI §7) -----------------------------------------
# "what abilities does Quincy have", "list Adora's abilities" is the BUG-0009
# wrong-assembly class: the model lists a hero's abilities itself and can
# mis-level / mislabel one (every ability NAME is grounded, so the value-only
# faithfulness guard never catches a wrong level or ordering). The authoritative
# per-hero list is derived deterministically by btd6_data_service.hero_abilities,
# so the floor OWNS the labelled list.
_ABILITY_CUE_RE = re.compile(r"\babilit(?:y|ies)\b", re.I)


def _format_hero_abilities(canonical: str, abilities: tuple[Any, ...]) -> str:
    if not abilities:
        return f"**{canonical}** has no recorded activated abilities."
    lines = [f"**{canonical} — abilities ({len(abilities)}):**"]
    lines.extend(
        f"• **{ability.name}** (Level {ability.level}) — {ability.summary}"
        for ability in abilities
    )
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_hero_ability_roster_reply(message_text: str) -> str | None:
    """A code-built "what abilities does <hero> have" list, or ``None``.

    The §7.6 *hero-ability* roster member of the BUG-0009 floor — the per-hero
    sibling of the capability / bloon / relic rosters. Fires on an ability cue +
    exactly one resolved hero, listing that hero's abilities (level + name +
    summary). Defers (``None``) on a **cost** cue (the hero *cost* comparison
    builder's job — same entity, different shape), strategy/opinion, zero heroes,
    and two-or-more heroes (an ambiguous multi-hero ask reaches the model).
    Mutually exclusive with the other floor builders by construction: it requires
    the literal ``ability``/``abilities`` token, which none of them key on.
    """
    text = (message_text or "").strip().lower()
    if not text:
        return None
    if not _ABILITY_CUE_RE.search(text):
        return None
    # A hero cost comparison is the hero-cost builder's job, not this roster.
    if _COST_COMPARE_CUE_RE.search(text) or _COST_COMPARE_VERB_RE.search(text):
        return None
    if any(word in text for word in _ROSTER_STRATEGY_WORDS):
        return None

    names = _extract_hero_names(text)
    if len(names) != 1:
        return None

    from services import btd6_data_service

    abilities = btd6_data_service.hero_abilities(names[0])
    if not abilities:
        return None
    hero = btd6_data_service.get_hero(names[0])
    canonical = hero.canonical if hero is not None else names[0]
    return _format_hero_abilities(canonical, abilities)


# --- §7.6 paragon ability roster (AI §7) --------------------------------------
# "what abilities does the Ascended Shadow paragon have", "list the dart monkey
# paragon's abilities" is the BUG-0009 wrong-assembly class for paragons: the
# model lists a paragon's activated/passive abilities itself and can invent one,
# mislabel activated vs passive, or drop one — and because every ability NAME is
# grounded the value-only faithfulness guard never catches the wrong assembly. The
# authoritative per-paragon list is the curated paragon_abilities.json (served via
# btd6_stats_service), so the floor OWNS the labelled list. The literal "paragon"
# token is what makes it mutually exclusive with the hero-ability roster (a hero
# question never carries it) and the paragon-cost comparison (which needs a cost
# cue this builder defers on).


def _format_paragon_abilities(canonical: str, abilities: tuple[Any, ...]) -> str:
    if not abilities:
        return (
            f"**{canonical}** has no special activated or passive ability — its "
            "power is its base attack alone."
        )
    lines = [f"**{canonical} — abilities ({len(abilities)}):**"]
    for ability in abilities:
        if ability.kind == "passive":
            tag = "passive"
        elif ability.cooldown:
            tag = f"activated, {ability.cooldown}s cooldown"
        else:
            tag = "activated"
        lines.append(f"• **{ability.name}** ({tag}) — {ability.description}")
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_paragon_ability_roster_reply(message_text: str) -> str | None:
    """A code-built "what abilities does <paragon> have" list, or ``None``.

    The §7.6 *paragon-ability* roster member of the BUG-0009 floor — the paragon
    sibling of :func:`deterministic_hero_ability_roster_reply`. Fires on an ability
    cue + the literal ``paragon`` token + exactly one resolved paragon, listing
    that paragon's curated activated/passive abilities (name + kind + cooldown +
    summary). Defers (``None``) on a **cost** cue (the paragon *cost* comparison
    builder's job — same entity, different shape), strategy/opinion phrasing, zero
    paragons, and two-or-more paragons (an ambiguous multi-paragon ask reaches the
    model). The ``paragon`` token keeps it mutually exclusive with the hero-ability
    roster (a hero question never carries it). A paragon with no special ability
    (e.g. Apex Plasma Master) still gets an explicit owned line so the model never
    invents one.
    """
    text = (message_text or "").strip().lower()
    if not text:
        return None
    if not _ABILITY_CUE_RE.search(text):
        return None
    if not _PARAGON_CUE_RE.search(text):
        return None
    # A paragon cost comparison is the paragon-cost builder's job, not this roster.
    if _COST_COMPARE_CUE_RE.search(text) or _COST_COMPARE_VERB_RE.search(text):
        return None
    if any(word in text for word in _ROSTER_STRATEGY_WORDS):
        return None

    names = _extract_paragon_names(text)
    if len(names) != 1:
        return None

    from services import btd6_stats_service

    pstats = btd6_stats_service.get_paragon_stats(names[0])
    if pstats is None:
        return None
    return _format_paragon_abilities(pstats.canonical, pstats.abilities)


# --- boss damage-immunity floor (BUG-0009) ------------------------------------
# "what is Lych immune to" / "which bosses are immune to fire" — the model can
# mis-state a boss's immunities (claim an immunity it doesn't have, or omit one),
# and every damage-type name is grounded so the value-only faithfulness guard
# can't catch the wrong *assembly*. The deterministic layer OWNS the answer off
# bosses[].immune_to. Requires a boss reference (a named boss or the literal
# "boss(es)" token) AND an immunity cue, so it never overlaps the bloon immunity
# roster (which keys on a bloon/blimp/moab subject, never on "boss").
_BOSS_IMMUNE_CUE_RE = re.compile(
    r"\bimmun(?:e|ity|ities)\b|\bresist(?:s|ant|ance)?\b",
    re.I,
)
_BOSS_SUBJECT_RE = re.compile(r"\bboss(?:es)?\b", re.I)


def _scan_boss(text_lower: str, bosses: Any) -> Any | None:
    """The most specific boss named in ``text_lower`` (longest canonical), or
    ``None``. Whole-word matched; boss names carry no aliases in the dataset.
    """
    best = None
    best_len = 0
    for boss in bosses:
        name = boss.canonical.lower()
        if len(name) < 3:
            continue
        if re.search(r"\b" + re.escape(name) + r"\b", text_lower):
            if len(name) > best_len:
                best, best_len = boss, len(name)
    return best


def deterministic_boss_immunity_reply(message_text: str) -> str | None:
    """A code-built boss damage-immunity answer, or ``None``.

    Handles three shapes off ``bosses[].immune_to``: a single boss's immunities
    ("what is Lych immune to"), a yes/no for one boss + damage ("is Blastapopoulos
    immune to fire"), and the cross-boss roster ("which bosses are immune to
    fire"). Fires only on a boss reference + an immunity cue, so it defers
    (``None``) for the bloon immunity roster (bloon subject, not boss), boss HP /
    strategy questions (no immunity cue), and anything else — which reach the model
    or another floor builder unchanged.
    """
    text = (message_text or "").strip().lower()
    if not text:
        return None
    if not _BOSS_IMMUNE_CUE_RE.search(text):
        return None
    if any(word in text for word in _ROSTER_STRATEGY_WORDS):
        return None

    from services import btd6_data_service

    bosses = btd6_data_service.get_dataset().bosses
    if not bosses:
        return None

    damage = _match_bloon_damage(text)
    named = _scan_boss(text, bosses)

    if named is not None:
        immunities = named.immune_to or ()
        if damage is not None:
            verdict = (
                "**is immune to**" if damage in immunities else "is **not** immune to"
            )
            return f"**{named.canonical}** {verdict} {damage} damage."
        if not immunities:
            return (
                f"**{named.canonical}** has no damage-type immunities — every "
                "damage type hurts it."
            )
        listed = ", ".join(immunities)
        return (
            f"**{named.canonical} is immune to ({len(immunities)}):** {listed} damage."
        )

    # No single boss named — the cross-boss roster needs the literal "boss(es)"
    # token plus a damage type (otherwise it is too vague to floor).
    if _BOSS_SUBJECT_RE.search(text) and damage is not None:
        hits = [b for b in bosses if damage in (b.immune_to or ())]
        if not hits:
            return f"**No BTD6 boss is immune to {damage} damage.**"
        names = ", ".join(f"**{b.canonical}**" for b in hits)
        return f"**BTD6 bosses immune to {damage} damage ({len(hits)}):** {names}."

    return None


# --- §7.5 boss tier-HP comparison floor (BUG-0009) ----------------------------
# "which boss has the most health at tier 5", "is Lych or Vortex tougher at tier
# 3" is the §7.5 comparison member of the wrong-assembly class for bosses: the
# model ranks the bosses itself off their per-tier health and can mis-state which
# is tougher / by how much (every HP figure is grounded, so the value-only
# faithfulness guard never catches a wrong RANKING). The authoritative per-tier
# health is bosses[].tiers / .elite_tiers, so the floor OWNS the ranking. A tier
# (1-5) is REQUIRED — without one the comparison is ambiguous (a boss has five
# different HP values), so the builder fails closed and the question reaches the
# model. Defers on an immunity cue (the boss-immunity floor's job).
_BOSS_HP_CUE_RE = re.compile(
    r"\b(?:hp|health|hit\s?points?|tough\w*|tank\w*|durab\w*|sturd\w*|beef\w*)\b",
    re.I,
)
_BOSS_HP_MOST_RE = re.compile(
    r"\b(?:most|highest|toughest|strongest|tankiest|beefiest|biggest|hardest)\b",
    re.I,
)
_BOSS_HP_LEAST_RE = re.compile(
    r"\b(?:least|lowest|weakest|squishiest|smallest|frailest)\b",
    re.I,
)
_BOSS_TIER_RE = re.compile(r"\btier\s*([1-5])\b|\bt([1-5])\b", re.I)
# A narrow strategy/how-to set — kept separate from _ROSTER_STRATEGY_WORDS because
# that set excludes "vs"/"better"/"against", which are legitimate HP-comparison
# phrasings ("Lych vs Vortex tier 5 hp"); only true strategy intent defers here.
_BOSS_HP_STRATEGY_EXCLUDE = ("counter", "how do i beat", "how to beat", "tier list")


def _scan_bosses(text_lower: str, bosses: Any) -> list[Any]:
    """Every boss named in ``text_lower``, in order of first appearance, deduped.

    Whole-word matched on the canonical (bosses carry no aliases). The plural
    sibling of :func:`_scan_boss`, used by the HP comparison floor to rank the
    specific bosses a question names.
    """
    hits: list[tuple[int, Any]] = []
    for boss in bosses:
        name = boss.canonical.lower()
        if len(name) < 3:
            continue
        match = re.search(r"\b" + re.escape(name) + r"\b", text_lower)
        if match:
            hits.append((match.start(), boss))
    hits.sort(key=lambda h: h[0])
    return [boss for _start, boss in hits]


def _boss_tier_health(boss: Any, tier: int, *, elite: bool) -> int | None:
    """One boss's health at ``tier`` (1-5), elite or normal, or ``None``."""
    rows = (boss.elite_tiers if elite else boss.tiers) or ()
    for row in rows:
        if row.get("tier") == tier:
            health = row.get("health")
            return int(health) if health is not None else None
    return None


def deterministic_boss_hp_comparison_reply(message_text: str) -> str | None:
    """A code-built boss tier-HP ranking, or ``None``.

    The §7.5 *boss* member of the multi-entity comparison floor. Two shapes off
    ``bosses[].tiers`` / ``.elite_tiers``: ranking the specific bosses a question
    names ("is Lych or Vortex tougher at tier 3") and the superlative over all
    bosses ("which boss has the most health at tier 5"). A tier (1-5) is REQUIRED —
    without one the answer is ambiguous (five HP values per boss), so the builder
    returns ``None`` and the model handles it. Defers (``None``) on an immunity cue
    (the boss-immunity floor's job), a strategy/how-to-beat ask, and a single-boss
    HP lookup (a value question the faithfulness guard already covers).
    """
    text = (message_text or "").strip().lower()
    if not text:
        return None
    if not _BOSS_HP_CUE_RE.search(text):
        return None
    # An immunity question is the boss-immunity floor's job, not an HP ranking.
    if _BOSS_IMMUNE_CUE_RE.search(text):
        return None
    if any(word in text for word in _BOSS_HP_STRATEGY_EXCLUDE):
        return None

    tier_match = _BOSS_TIER_RE.search(text)
    if not tier_match:
        return None
    tier = int(tier_match.group(1) or tier_match.group(2))
    elite = "elite" in text

    from services import btd6_data_service

    bosses = btd6_data_service.get_dataset().bosses
    if not bosses:
        return None

    named = _scan_bosses(text, bosses)
    superlative_most = _BOSS_HP_MOST_RE.search(text)
    superlative_least = _BOSS_HP_LEAST_RE.search(text)

    if len(named) >= 2:
        contenders = named
    elif (superlative_most or superlative_least) and _BOSS_SUBJECT_RE.search(text):
        contenders = list(bosses)
    else:
        return None

    ranked = []
    for boss in contenders:
        health = _boss_tier_health(boss, tier, elite=elite)
        if health is not None:
            ranked.append((boss, health))
    if len(ranked) < 2:
        return None

    ascending = superlative_least is not None and superlative_most is None
    ranked.sort(key=lambda rb: rb[1], reverse=not ascending)

    label = "elite tier" if elite else "tier"
    winner, winner_hp = ranked[0]
    verb = "least" if ascending else "most"
    lines = [
        f"**Boss HP at {label} {tier} — ranked ({verb} first):**",
    ]
    lines.extend(f"• **{boss.canonical}** — {health:,} HP" for boss, health in ranked)
    lines.append(
        f"**{winner.canonical}** has the {verb} health at {label} {tier} "
        f"({winner_hp:,} HP).",
    )
    return "\n".join(lines)


# --- "XP for round N" deterministic reply -------------------------------------
# Per-round XP is a fixed function of round number (round_xp.json, the
# bloonswiki-sourced formula). The model can't restate the table verbatim, so a
# "how much XP does round 63 give" answer either trips the faithfulness guard or
# is silently wrong — the deterministic layer OWNS it. Sibling of the round-cash
# workflow (which owns cash); this owns XP.
_ROUND_XP_CUE_RE = re.compile(r"\b(?:xp|experience)\b", re.I)
# A round reference: "round 63" / "round63" / "r63" (1-3 digits).
_ROUND_XP_NUMBER_RE = re.compile(r"\bround\s*(\d{1,3})\b|\br(\d{1,3})\b", re.I)
# Map-difficulty cue (the axis the XP multiplier scales on — distinct from the
# Easy/Medium/Hard game difficulty).
_ROUND_XP_DIFFICULTY_RE = re.compile(
    r"\b(beginner|intermediate|advanced|expert)\b",
    re.I,
)
_ROUND_XP_FREEPLAY_RE = re.compile(r"\bfree\s*play\b", re.I)


def _fmt_xp(value: float) -> str:
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


def deterministic_round_xp_reply(message_text: str) -> str | None:
    """A code-built "XP for round N" answer, or ``None``.

    Fires on an XP cue ("xp" / "experience") + a resolvable round number, served
    as a pre-emptive floor. Honours an optional map difficulty
    (Beginner/Intermediate/Advanced/Expert) and a ``freeplay`` cue. Defers
    (``None``) without an XP cue, without a round number, or for a round outside
    the table — those reach the model. XP is identical for the default and ABR
    round sets, so there is no roundset branch. The per-tower split and Monkey-
    Knowledge bonuses are gameplay-dependent and are noted, not computed.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _ROUND_XP_CUE_RE.search(low):
        return None
    number_match = _ROUND_XP_NUMBER_RE.search(low)
    if number_match is None:
        return None
    round_number = int(number_match.group(1) or number_match.group(2))

    from services import btd6_data_service

    base = btd6_data_service.round_base_xp(round_number)
    if base is None:
        return None
    difficulty_match = _ROUND_XP_DIFFICULTY_RE.search(low)
    difficulty = difficulty_match.group(1).lower() if difficulty_match else "beginner"
    freeplay = bool(_ROUND_XP_FREEPLAY_RE.search(low))
    earned = btd6_data_service.round_xp_earned(
        round_number,
        difficulty=difficulty,
        freeplay=freeplay,
    )
    if earned is None:
        return None

    if difficulty == "beginner" and not freeplay:
        return (
            f"**Round {round_number}** awards **{_fmt_xp(earned)} XP** (base — "
            "Beginner difficulty, before freeplay and Monkey Knowledge). Map "
            "difficulty scales it: ×1.1 Intermediate · ×1.2 Advanced · ×1.3 "
            "Expert. This is the round's total tower XP, split among your towers "
            "by share of cash invested."
        )
    qualifiers = []
    if difficulty != "beginner":
        qualifiers.append(f"on **{difficulty.title()}**")
    if freeplay:
        qualifiers.append("in **freeplay**")
    qualifier = " ".join(qualifiers)
    return (
        f"**Round {round_number}** {qualifier} awards **{_fmt_xp(earned)} XP** "
        f"(base **{base:,}** XP before Monkey Knowledge)."
    )


# --- "Economy of round N" deterministic reply ---------------------------------
# The consolidated round-economy answer: RBE + cash (+ cumulative) + XP in one
# grounded reply, matching the round embed's Economy field. Round economy is
# otherwise spread across three paths (cash → ai_round_cash_workflow, XP →
# deterministic_round_xp_reply, RBE → none), so "what's the economy of round 95"
# had no single answer. Registered BEFORE the XP builder so a multi-stat /
# economy question gets the consolidated answer while a pure "how much xp" (no
# economy cue) still routes to the narrower XP reply.
_ROUND_ECONOMY_CUE_RE = re.compile(
    r"\b(?:economy|economic|overview|summary|breakdown|stats?|rewards?|rbe)\b",
    re.I,
)


def _round_range_economy_reply(lo: int, hi: int, roundset: str) -> str | None:
    """Deterministic "total RBE + cash across rounds ``lo``-``hi``" answer, or ``None``.

    The range case of :func:`deterministic_round_economy_reply`, off the same audited
    engines the ``/btd6`` lookup commands use — total RBE (base + freeplay-scaled) via
    ``round_rbe``, total cash via ``round_cash``, heaviest rounds via
    ``round_composition``. ``None`` when the range is unknown (the data layer fails
    closed), so the query falls through to the model rather than inventing a partial sum.
    """
    from services import btd6_data_service

    rbe = btd6_data_service.round_rbe(lo, hi, roundset)
    if not rbe.get("found") or rbe.get("base_rbe_total") is None:
        return None
    set_label = "ABR" if roundset == "alternate" else "default rounds"
    base_total = rbe["base_rbe_total"]
    eff_total = rbe.get("effective_rbe_total")
    lines = [f"**Rounds {lo}–{hi} — totals** ({set_label})"]
    if rbe.get("scaled") and eff_total is not None and eff_total != base_total:
        lines.append(
            f"• **Total RBE** {base_total:,} base → **{eff_total:,}** with "
            "MOAB-class freeplay scaling",
        )
    else:
        lines.append(f"• **Total RBE** {base_total:,}")
    cash = btd6_data_service.round_cash(lo, hi, roundset)
    if cash.get("found") and cash.get("range_cash") is not None:
        lines.append(f"• **Total cash** ${cash['range_cash']:,.0f}")
    comp = btd6_data_service.round_composition(lo, hi, roundset=roundset)
    heaviest = comp.get("heaviest_by_rbe") if comp.get("found") else None
    if heaviest:
        top = ", ".join(f"R{h['round']} ({h['rbe']:,} RBE)" for h in heaviest[:3])
        lines.append(f"• **Heaviest rounds:** {top}")
    return "\n".join(lines)


def deterministic_round_economy_reply(message_text: str) -> str | None:
    """A code-built "economy of round N" answer (RBE + cash + XP), or ``None``.

    Fires on a round number + an economy cue (economy / overview / summary /
    stats / rewards / rbe / breakdown), served as a pre-emptive floor. Supports
    ABR via the standard cue (cash/RBE differ between sets; XP does not). Defers
    (``None``) without an economy cue, without a round number, or for a round not
    in the set — those reach the narrower builders or the model.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _ROUND_ECONOMY_CUE_RE.search(low):
        return None

    from services import btd6_data_service

    roundset = "alternate" if _ABR_CUE_RE.search(low) else "default"

    # A round RANGE ("r20 to r80", "rounds 8-66") asks for the range TOTAL, not one
    # round's economy. Without this, the single-number regex below grabs the first
    # endpoint and answers for that one round — the "rbe of r20 to r80 → only Round
    # 20" regression. Two+ ranges is the §7.5 comparison floor's job; defer there.
    proper_ranges = [(lo, hi) for lo, hi in _extract_round_ranges(low) if lo != hi]
    if len(proper_ranges) >= 2:
        return None
    if len(proper_ranges) == 1:
        lo, hi = proper_ranges[0]
        return _round_range_economy_reply(lo, hi, roundset)

    number_match = _ROUND_XP_NUMBER_RE.search(low)
    if number_match is None:
        return None
    round_number = int(number_match.group(1) or number_match.group(2))
    entry = btd6_data_service.get_round(round_number, roundset)
    if entry is None:
        return None
    base_xp = btd6_data_service.round_base_xp(round_number)

    set_label = "ABR" if roundset == "alternate" else "default rounds"
    lines = [f"**Round {round_number} — RBE, cash & XP** ({set_label})"]
    if entry.rbe is not None:
        rbe_line = f"• **RBE** {entry.rbe:,}"
        start = btd6_data_service.get_dataset().moab_health_start_round or 81
        if round_number >= start and entry.groups:
            # Recompute the round's total RBE with freeplay scaling, but only when
            # every spawn group resolves through the validated MOAB-class/ceramic
            # path (lone basic-bloon spawn-halving is out of scope, so it's skipped
            # rather than reported approximately).
            scaled_total = 0
            reliable = True
            for group in entry.groups:
                cid = str(group.get("bloon_id", ""))
                record = btd6_data_service.get_bloon(cid)
                if record is None or (
                    record.category != "moab_class" and record.id != "ceramic"
                ):
                    reliable = False
                    break
                fort = "fortified" in (group.get("modifiers", ()) or ())
                scaled = btd6_data_service.bloon_rbe_at_round(
                    cid,
                    round_number,
                    fortified=fort,
                )
                if scaled is None:
                    reliable = False
                    break
                scaled_total += int(group.get("count", 0)) * scaled
            if reliable and scaled_total != entry.rbe:
                rbe_line += (
                    f" base → **{scaled_total:,}** on round {round_number} "
                    f"(MOAB-class late-game/freeplay scaling)"
                )
        lines.append(rbe_line)
    if entry.cash is not None:
        cumulative = (
            f" (cumulative ${entry.cumulative_cash:,.0f})"
            if entry.cumulative_cash is not None
            else ""
        )
        lines.append(f"• **Cash** ${entry.cash:,.0f}{cumulative}")
    if base_xp is not None:
        lines.append(
            f"• **XP** {base_xp:,} (Beginner base, before freeplay/Monkey Knowledge)",
        )
    # Nothing groundable beyond the header → defer rather than send an empty card.
    if len(lines) == 1:
        return None
    return "\n".join(lines)


_ELITE_CUE_RE = re.compile(r"\belite\b", re.I)
_PARAGON_WORD_RE = re.compile(r"\bparagons?\b", re.I)
_ELITE_MULT_CUE_RE = re.compile(
    r"\b(?:multiplier|damage|dmg|bonus|double|doubled|x\s?2|×\s?2)\b",
    re.I,
)


def deterministic_paragon_elite_reply(message_text: str) -> str | None:
    """A code-built "paragon Elite-Boss damage multiplier" answer, or ``None``.

    Owns the elite-boss-multiplier question for paragons — general ("the elite boss
    multiplier for paragons") or a named one ("for the dart paragon"). Both refused
    in production: the #1402 elite grounding only fires for a *resolved* paragon, and
    the faithfulness floor killed the model's draft even when it did. The answer is a
    global runtime constant — paragons deal DOUBLE their boss damage to Elite Bosses,
    at every degree — so a deterministic reply is correct AND refusal-proof.

    Fires on ``elite`` + a damage/multiplier cue + paragon context (the word, or a
    resolvable paragon name); defers otherwise. Narrow enough to stay exclusive with
    the other paragon floors (cost/abilities), which carry no ``elite`` cue.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not (_ELITE_CUE_RE.search(low) and _ELITE_MULT_CUE_RE.search(low)):
        return None

    from services import btd6_stats_service
    from utils.btd6 import paragon_degrees

    has_paragon = bool(_PARAGON_WORD_RE.search(low)) or (
        btd6_stats_service.resolve_paragon(text) is not None
    )
    if not has_paragon:
        return None

    boss100 = paragon_degrees.boss_multiplier(100)
    elite1 = paragon_degrees.elite_boss_multiplier(1)
    elite100 = paragon_degrees.elite_boss_multiplier(100)
    return (
        "**Paragon Elite-Boss damage** — against **Elite** Bosses, every Paragon "
        "deals **double** its boss damage.\n"
        "• A flat **×2** on top of the boss-damage multiplier, at **every degree** "
        "(from Degree 1).\n"
        f"• So the elite-boss multiplier = 2 × the boss multiplier: **×{elite1:g} at "
        f"Degree 1**, rising to **×{elite100:g} at Degree 100** (boss is ×{boss100:g} "
        "at Degree 100).\n"
        "• Global to the whole Paragon category — not per-paragon — and a runtime "
        "constant, so it is not in the game's exported data."
    )


# A bloon-listing intent over a round RANGE: "list all the bloons from r29 till
# r63", "what bloons spawn between rounds 40 and 60", "which bloons in rounds
# 29-63". Anchored on a bloon/spawn/composition noun so an economy range question
# ("rbe of r29 to r63") still routes to deterministic_round_economy_reply above.
_ROUND_RANGE_BLOON_CUE_RE = re.compile(
    r"\b(?:bloons?|blimps?|moabs?|spawns?|spawned|spawning|composition|"
    r"enemies|threats?)\b",
    re.I,
)
# A bare "A-B" number-pair (no round token). Used ONLY to detect a second,
# token-less comparison range — "which has more bloons, rounds 20-40 or 40-60"
# (`_extract_round_ranges` needs a round token on each anchor, so it sees only
# the first) — so the roster defers to the model on a comparison rather than
# answering about the first range alone.
_BARE_ROUND_PAIR_RE = re.compile(
    r"(?<![\d-])(\d{1,3})\s*(?:to|through|thru|until|till|[-–])\s*(\d{1,3})(?![\d-])",
    re.I,
)


def _format_round_range_bloons(result: dict[str, Any]) -> str:
    """Render the :func:`btd6_data_service.round_range_bloon_roster` result."""
    lo = result["round_start"]
    hi = result["round_end"]
    roster = result["roster"]
    lines = [
        f"**Bloons across rounds {lo}–{hi}** "
        f"({result['roundset_label']} round set — {result['rounds_in_range']} "
        f"rounds, {result['total_bloons_entering']:,} bloons enter, "
        f"{result['total_rbe']:,} total RBE)",
        f"**Bloon types that appear ({len(roster)}):**",
    ]
    for record in roster:
        first, last = record["first_round"], record["last_round"]
        span = f"R{first}" if first == last else f"R{first}–R{last}"
        present = record["rounds_present"]
        lines.append(
            f"• **{record['bloon']}** — {span}, in {present} "
            f"round{'' if present == 1 else 's'} (~{record['total']:,} spawned)",
        )
    modifiers = result.get("modifiers_seen") or []
    if modifiers:
        lines.append(f"_Modifiers seen across the range: {', '.join(modifiers)}._")
    lines.append(
        f"_Per-round detail: `/btd6 round {lo} {hi}` (values table), or ask about "
        "a single round for its exact spawn composition._",
    )
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


def deterministic_round_range_bloons_reply(message_text: str) -> str | None:
    """A code-built "which bloons appear across rounds X-Y" answer, or ``None``.

    Fixes the "list all the bloons from r29 till r63" miss (owner-reported,
    2026-07-01): the NL resolver extracts the two endpoint round NUMBERS with no
    range concept, so the grounding pass rendered only rounds 29 and 63 and the
    answer listed those two rounds' bloons instead of the whole span. This floor
    OWNS the range roster — the distinct bloon TYPES across **every** round in the
    range, off the audited :func:`btd6_data_service.round_range_bloon_roster`
    engine — so the span is enumerated deterministically, never sampled at the
    endpoints.

    Fires on exactly ONE inclusive round range (``lo != hi``) + a bloon/spawn/
    composition cue. Defers (``None``) when an economy cue is present (that is
    :func:`deterministic_round_economy_reply`'s range case, earlier in the chain),
    on two-or-more ranges (the comparison builder), or without a range — so it
    stays mutually exclusive with its siblings and ordinary questions fall through
    to the model.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    low = text.lower()
    if not _ROUND_RANGE_BLOON_CUE_RE.search(low):
        return None
    # Economy range questions belong to deterministic_round_economy_reply.
    if _ROUND_ECONOMY_CUE_RE.search(low):
        return None
    distinct: set[tuple[int, int]] = {
        (min(a, b), max(a, b)) for a, b in _extract_round_ranges(low) if a != b
    }
    # A second (possibly token-less) range makes this a comparison, not a listing.
    for match in _BARE_ROUND_PAIR_RE.finditer(low):
        a, b = int(match.group(1)), int(match.group(2))
        if a != b:
            distinct.add((min(a, b), max(a, b)))
    if len(distinct) != 1:
        return None
    lo, hi = next(iter(distinct))

    from services import btd6_data_service

    roundset = "alternate" if _ABR_CUE_RE.search(low) else "default"
    result = btd6_data_service.round_range_bloon_roster(lo, hi, roundset)
    if not result.get("found"):
        return None
    return _format_round_range_bloons(result)


# --- BUG-0009 deterministic list-answer dispatcher ----------------------------
# The ordered floor builders the dispatcher fans out to. Each OWNS its labelled
# answer and is narrow (returns ``None`` for anything but its exact list shape),
# so their match sets are mutually exclusive on a real question; order resolves
# only a genuine overlap (e.g. a two-tower cost question reaches the multi-tower
# builder before the single-tower difficulty builder). Exposed at module level so
# the exclusivity invariant (`test_btd6_floor_builder_exclusivity.py`) iterates the
# *live* tuple — a builder added here is automatically held to the one-fires
# contract, no test edit needed. Append a new list family here.
_BTD6_LIST_BUILDERS: tuple[Callable[[str], str | None], ...] = (
    deterministic_round_economy_reply,
    deterministic_round_range_bloons_reply,
    deterministic_round_xp_reply,
    deterministic_mk_reference_reply,
    deterministic_mk_category_roster_reply,
    deterministic_geraldo_per_level_reply,
    deterministic_modes_reply,
    deterministic_capability_roster_reply,
    deterministic_bloon_health_reply,
    deterministic_bloon_roster_reply,
    deterministic_bloon_modifier_reply,
    deterministic_boss_immunity_reply,
    deterministic_boss_hp_comparison_reply,
    deterministic_relic_roster_reply,
    deterministic_hero_ability_roster_reply,
    deterministic_paragon_ability_roster_reply,
    deterministic_paragon_elite_reply,
    deterministic_paragon_cost_comparison_reply,
    deterministic_hero_cost_comparison_reply,
    deterministic_power_cost_comparison_reply,
    deterministic_cost_comparison_reply,
    deterministic_difficulty_cost_comparison_reply,
    deterministic_round_range_comparison_reply,
)


def deterministic_btd6_list_reply(message_text: str) -> str | None:
    """The single BUG-0009 floor seam: the first deterministic list-answer
    builder that matches ``message_text``, or ``None`` if none does.

    BUG-0009 is the "grounded facts, wrong assembly" class — the model groups /
    labels / orders an individually-grounded list incorrectly, and the
    value-only faithfulness guard cannot catch a mis-*grouping*. Each builder in
    :data:`_BTD6_LIST_BUILDERS` OWNS its labelled answer; the natural-language
    stage serves the result as a pre-emptive floor *before* the model. Builders
    are narrow (they return ``None`` for anything but their exact list shape), so
    ordinary BTD6 questions fall through to the model untouched.

    The AI §7.5 comparison builders ride the same seam: a "which costs more" /
    "which earns more" question (across towers, difficulties, or round ranges) is
    the comparison member of the same wrong-assembly class.
    """
    for builder in _BTD6_LIST_BUILDERS:
        reply = builder(message_text)
        if reply:
            return reply
    return None


# A capability/meta ask about the bot's BTD6 knowledge. Anchored on a
# btd6/bloons token on purpose: the floor only handles BTD6-routed messages,
# and requiring the anchor keeps entity questions ("do you know how much the
# navarch earns?") out of the meta path. Verb/object shapes cover the four
# live-miss phrasings (2026-06-10 screenshots): "what kind of things do you
# know about btd6", "list all the things that you know about btd6", "what
# can you tell me about btd6", "what can we ask this bot about btd6".
_META_ANCHOR_RE = re.compile(r"\bbtd\s?6\b|\bbloons\b", re.I)
_META_SHAPE_RES = (
    re.compile(r"\b(?:do|can|does)\s+(?:you|we|i|this bot)\b.{0,40}\bknow\b", re.I),
    re.compile(r"\bknow\s+about\b", re.I),
    # No auxiliary-verb requirement: "what CSN you tell me about btd6" (live
    # typo, 2026-06-10) must still match — "you tell me/us about" + the BTD6
    # anchor is unambiguous on a floored BTD6-routed message.
    re.compile(r"\b(?:you|this bot)\s+tell\s+(?:me|us)\s+about\b", re.I),
    # "ask" must target the bot ("ask you / this bot / the bot / it"), not a
    # third party ("can I ask a friend to play btd6" is a social turn).
    re.compile(r"\bask\s+(?:you|it|this\s+bot|the\s+bot)\b", re.I),
    re.compile(r"\bwhat\s+(?:btd\s?6\s+)?(?:data|questions?|topics?)\b", re.I),
    re.compile(r"\bwhat\s+can\s+you\s+(?:do|answer|help)\b", re.I),
)
# An entity-stats shape ("how much/many …", "what is the hp of …") is a real
# question even when it also says "do you know" — never serve it the meta
# summary; let it reach the model/refusal with its own grounding.
_META_EXCLUDE_RE = re.compile(
    r"\bhow\s+(?:much|many)\b|\bwhat\s+is\s+the\b|\bstats?\s+(?:of|for)\b",
    re.I,
)


def deterministic_meta_reply(message_text: str) -> str | None:
    """A code-built "what BTD6 do you know?" answer, or ``None``.

    The same floor pattern as :func:`deterministic_roster_reply`, for
    capability/meta questions: the model's own capability description trips
    the faithfulness guard (its counts/names are not in the fact ledger), so
    a healthy meta ask kept ending in the version-stamped no-data refusal —
    the wrong answer to "what do you know about btd6?" (live, 2026-06-10).
    Built from the introspection read model, so it *is* the source.
    """
    text = (message_text or "").strip()
    if not text:
        return None
    if not _META_ANCHOR_RE.search(text):
        return None
    if _META_EXCLUDE_RE.search(text):
        return None
    if not any(r.search(text) for r in _META_SHAPE_RES):
        return None

    from services import ai_introspection_service

    snap = ai_introspection_service.build_btd6_answerability()
    if not snap.available:
        return None

    fixtures = [d for d in snap.domains if d.kind == "deterministic_fixture"]
    calculations = [d for d in snap.domains if d.kind == "calculation"]
    live = [d for d in snap.domains if d.kind == "live"]
    unsupported = [d for d in snap.domains if d.kind == "unsupported"]

    def _label(d: Any) -> str:
        name = d.name.replace("_", " ")
        return f"{name} ({d.item_count})" if d.item_count else name

    def _bullets(domains: list[Any]) -> list[str]:
        # One "- name — note" bullet per domain: the owner compared the old
        # semicolon-run rendering against the bulleted tool-catalog list and
        # asked for "a clear list of everything it can do in a readable
        # format" (live, 2026-06-11).
        out = []
        for d in domains:
            name = d.name.replace("_", " ")
            out.append(f"- **{name}** — {d.note}" if d.note else f"- **{name}**")
        return out

    lines = [
        f"**What I know about BTD6** (game version {snap.game_version}, "
        f"{snap.source_label}):",
        "📚 **Verified data:** " + ", ".join(_label(d) for d in fixtures) + ".",
        "🔎 **Lookups:** any of the above by name — plus capability search "
        "(camo detection, lead/purple popping, …) and rankings by cost, "
        "damage, DPS, pierce, or range.",
    ]
    if calculations:
        lines.append("🧮 **Calculations:**")
        lines.extend(_bullets(calculations))
    if live:
        lines.append("📡 **Live:**")
        lines.extend(_bullets(live))
    if unsupported:
        lines.append(
            "🚫 **Not covered:** "
            + ", ".join(d.name.replace("_", " ") for d in unsupported)
            + ".",
        )
    lines.append(
        "Ask about a specific tower, hero, paragon, boss, round, or map — "
        "or try `!btd6menu` for the browsable panels.",
    )
    reply = "\n".join(lines)
    return reply if len(reply) <= 1900 else reply[:1899] + "…"


_PARAGON_NAME_FILLERS = frozenset({"the", "of"})

# Paragon shorthand distinctive enough to ground WITHOUT the word "paragon"
# in the message — coined/rare words with no ordinary-chat collision. Generic
# alias words (ice / boat / sub / root / …) must NOT join this set; they stay
# behind the "paragon" keyword gate.
_DISTINCTIVE_PARAGON_WORDS = frozenset(
    {"navarch", "doomship", "everfrost", "magus", "mmmf"},
)


def _squash_paragon_name(text: str) -> str:
    """Lowercase, strip punctuation, and drop filler words ("the"/"of").

    Users drop articles when naming paragons — the live miss was "navarch of
    seas" failing the exact-substring match against "Navarch of the Seas" and
    leaving the question with ZERO grounding (2026-06-10 screenshot). This
    normalises both sides of the match without loosening to fuzzy matching.
    """
    tokens = re.sub(r"[^a-z0-9]+", " ", text.lower()).split()
    return " ".join(t for t in tokens if t not in _PARAGON_NAME_FILLERS)


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
    squashed = _squash_paragon_name(text)
    out: list[str] = []
    grounded: set[str] = set(resolved_tower_ids)
    for paragon in paragon_math.PARAGONS:
        # Strip a parenthetical (e.g. "… (B.O.M.B.)") and match the bare name —
        # exactly, then article-tolerantly ("navarch of seas").
        name = paragon.name.split(" (")[0].strip().lower()
        if not name:
            continue
        if name not in text and _squash_paragon_name(name) not in squashed:
            continue
        pstats = btd6_stats_service.get_paragon_stats(paragon.paragon_id)
        if pstats is None or pstats.tower_id in grounded:
            continue
        grounded.add(pstats.tower_id)
        out.extend(_render_paragon(pstats.tower_id, pstats.tower_canonical))

    # A hyper-distinctive paragon word stands alone — "navarch" / "doomship"
    # is unambiguous even without the word "paragon" (the bare-name probe
    # grounded ZERO facts, 2026-06-10 sweep). Generic alias words ("ice",
    # "boat", "sub") stay behind the keyword gate below.
    squashed_tokens = frozenset(squashed.split())
    for word in _DISTINCTIVE_PARAGON_WORDS & squashed_tokens:
        resolved = paragon_math.resolve_paragon(word)
        if resolved is None:
            continue
        pstats = btd6_stats_service.get_paragon_stats(resolved.paragon_id)
        if pstats is None or pstats.tower_id in grounded:
            continue
        grounded.add(pstats.tower_id)
        out.extend(_render_paragon(pstats.tower_id, pstats.tower_canonical))

    # Shorthand the way players actually talk ("ice paragon", "boat paragon",
    # "navarch"): when the text says "paragon", try each word/word-pair against
    # the canonical shorthand resolver (tower names + curated aliases). Gating
    # on the keyword keeps generic alias words ("ice", "sub", "boat") from
    # grounding paragons in ordinary chat.
    if "paragon" in text:
        tokens = squashed.split()
        candidates = tokens + [
            " ".join(pair) for pair in zip(tokens, tokens[1:], strict=False)
        ]
        for candidate in candidates:
            resolved = paragon_math.resolve_paragon(candidate)
            if resolved is None:
                continue
            pstats = btd6_stats_service.get_paragon_stats(resolved.paragon_id)
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


# ---------------------------------------------------------------------------
# Minion / sub-tower name grounding (answerability item 6a)
# ---------------------------------------------------------------------------

# Minion names that are generic English words — matching them whole-word in
# ordinary chat would false-positive ("my plane leaves at 9"). Their stats stay
# reachable through the owning tier ("sun temple minions", "carrier flagship").
_MINION_NAME_STOPLIST = frozenset({"plane", "marine", "sentry", "tree", "beast"})

# How many matched minion names get the full owner grounding per message.
_MINION_MATCH_CAP = 2


def _fold_match_text(text: str) -> str:
    """Lowercase, fold diacritics, normalise punctuation to spaces.

    The match vocabulary the index and the message share — "Pouākai",
    "pouakai" and "Mini-Comanche"/"mini comanche" all land on one spelling.
    """
    folded = unicodedata.normalize("NFKD", text or "")
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", folded.lower()).split())


@lru_cache(maxsize=1)
def _minion_name_index() -> dict[str, tuple[str, str, str, str]]:
    """Map a folded minion name -> (kind, owner_id, code, display_name).

    Walks every stats file's ``subtowers`` (tower tiers, hero levels, paragon
    bases). Names that collide with an existing entity/upgrade vocabulary are
    skipped — the colliding owner already grounds them (beast names ARE their
    tier's upgrade-card names since the cutover; "Spectre" is the Ace upgrade).
    Owner preference: a tower tier (richest grounding: the upgrade card) over
    a hero/paragon, single-path codes over crosspaths, lowest code/level.
    """
    from services import btd6_data_service, btd6_stats_service, btd6_upgrade_service
    from utils.btd6 import paragon_math

    taken: set[str] = set()
    try:
        dataset = btd6_data_service.get_dataset()
        for entry in (*dataset.towers, *dataset.heroes, *dataset.bloons):
            taken.add(_fold_match_text(entry.canonical))
            taken.update(_fold_match_text(a) for a in entry.aliases)
        for upgrade in btd6_upgrade_service.all_upgrades():
            taken.add(_fold_match_text(upgrade.canonical))
    except Exception:  # noqa: BLE001 — defensive; an empty guard set is safer
        logger.debug("minion index: vocabulary guard unavailable", exc_info=True)
    taken.update(_fold_match_text(p.name) for p in paragon_math.PARAGONS)

    def _candidate_rank(kind: str, code: str) -> tuple[int, int, str]:
        # tier < hero < paragon; single-path/base tier codes before crosspaths.
        kind_rank = {"tier": 0, "hero": 1, "paragon": 2}[kind]
        crosspath = 0
        if kind == "tier":
            crosspath = (
                0 if tier_codes.is_base(code) or tier_codes.is_single_path(code) else 1
            )
        return (kind_rank, crosspath, code)

    best: dict[str, tuple[tuple[int, int, str], str, str, str, str]] = {}

    def _consider(kind: str, owner_id: str, code: str, node: dict[str, Any]) -> None:
        for sub in node.get("subtowers", []) or []:
            if not isinstance(sub, dict):
                continue
            display = str(sub.get("name") or "").strip()
            folded = _fold_match_text(display)
            if not folded or folded in taken or folded in _MINION_NAME_STOPLIST:
                continue
            rank = _candidate_rank(kind, code)
            prev = best.get(folded)
            if prev is None or rank < prev[0]:
                best[folded] = (rank, kind, owner_id, code, display)

    try:
        dataset = btd6_data_service.get_dataset()
        for tower in dataset.towers:
            stats = btd6_stats_service.get_tower_stats(getattr(tower, "id", ""))
            if stats is None:
                continue
            for code in stats.tier_codes():
                tier = stats.tier(code)
                if isinstance(tier, dict):
                    _consider("tier", stats.tower_id, code, tier)
        for hero in dataset.heroes:
            stats = btd6_stats_service.get_hero_stats(getattr(hero, "id", ""))
            if stats is None:
                continue
            for code in stats.levels or ():
                level = stats.level(code)
                if isinstance(level, dict):
                    _consider("hero", getattr(hero, "id", ""), code, level)
        for paragon_id in btd6_stats_service.list_paragon_ids():
            pstats = btd6_stats_service.get_paragon_stats(paragon_id)
            if pstats is not None:
                _consider("paragon", paragon_id, "base", pstats.base)
    except Exception:  # noqa: BLE001 — defensive
        logger.debug("minion index: stats walk failed", exc_info=True)

    return {
        folded: (kind, owner_id, code, display)
        for folded, (_rank, kind, owner_id, code, display) in best.items()
    }


def _subtower_name_facts(message_text: str, resolved_tower_ids: set[str]) -> list[str]:
    """Ground a minion named directly ("what does the Mini Sun Avatar do?").

    Minion stats live under the owning tier/level/paragon's ``subtowers`` —
    nothing keyed on the minion's own name, so these questions either drew a
    blank ("Crushing Sentry", "UAV") or mis-resolved to a similarly-named
    upgrade ("Mini Sun Avatar" landed on Sun Avatar, the wrong tier). Emits a
    resolution line naming the owner, then the owner's grounding.
    """
    from services import btd6_stats_service, btd6_upgrade_detail_service
    from utils.btd6.effect_lines import tier_effect_lines

    folded_text = f" {_fold_match_text(message_text)} "
    if len(folded_text) <= 2:
        return []
    matches = [
        (folded, owner)
        for folded, owner in _minion_name_index().items()
        if f" {folded} " in folded_text
    ]
    # Longest first, and drop a match embedded in a longer one (a hypothetical
    # "sun avatar" minion must not also fire inside "mini sun avatar").
    matches.sort(key=lambda m: len(m[0]), reverse=True)
    kept: list[tuple[str, tuple[str, str, str, str]]] = []
    for folded, owner in matches:
        if any(f" {folded} " in f" {longer} " for longer, _ in kept):
            continue
        kept.append((folded, owner))

    out: list[str] = []
    grounded: set[str] = set(resolved_tower_ids)
    for _folded, (kind, owner_id, code, display) in kept[:_MINION_MATCH_CAP]:
        if kind == "tier":
            detail = btd6_upgrade_detail_service.get_upgrade_detail(
                f"{owner_id}:{code}",
            )
            if detail is None:
                continue
            pretty = tier_codes.format_code(code)
            out.append(
                _cap(
                    f"[btd6_minion] {display} is a minion spawned by "
                    f"{detail.identity.tower_name}'s {detail.identity.canonical} "
                    f"({pretty}) — its stats are under that upgrade "
                    f"(source: BTD6 game data)",
                ),
            )
            out.extend(btd6_upgrade_detail_service.render_upgrade_grounding(detail))
        elif kind == "hero":
            stats = btd6_stats_service.get_hero_stats(owner_id)
            if stats is None:
                continue
            node = stats.level(code) or {}
            sub = next(
                (
                    s
                    for s in node.get("subtowers", []) or []
                    if isinstance(s, dict) and str(s.get("name") or "") == display
                ),
                None,
            )
            bits: list[str] = []
            if sub is not None:
                bits = _normal_stat_bits(btd6_stats_service.normal_stats(sub))
                # A support minion's effect lives in its buffs/zones, not its
                # attacks (Etienne's UAV grants Camo detection).
                bits.extend(tier_effect_lines(sub))
            tail = f": {_sanitise(', '.join(bits))}" if bits else ""
            out.append(
                _cap(
                    f"[btd6_minion] {display} is summoned by the hero "
                    f"{stats.canonical} (from Level {code}){tail} "
                    f"(source: BTD6 game data)",
                ),
            )
        else:  # paragon
            pstats = btd6_stats_service.get_paragon_stats(owner_id)
            if pstats is None or pstats.tower_id in grounded:
                continue
            out.append(
                _cap(
                    f"[btd6_minion] {display} is spawned by the paragon "
                    f"{pstats.canonical} (source: BTD6 game data)",
                ),
            )
            grounded.add(pstats.tower_id)
            out.extend(_render_paragon(pstats.tower_id, pstats.tower_canonical))
    return out


def _catalog_facts(message_text: str) -> list[str]:
    """Ground powers / Monkey Knowledge / bosses named in the text.

    These three fixture catalogs were reachable only through their dedicated
    AI tools (``btd6_power_lookup`` / ``btd6_monkey_knowledge_lookup`` /
    ``btd6_boss_lookup``) — the shared grounding pipeline never matched them,
    so the deterministic Ask path (and a single ``btd6_lookup`` call) drew a
    blank on "what does Super Monkey Storm do" (#655 answerability item 5).

    Matching mirrors ``_paragon_name_facts``: case-insensitive full-name
    substring. Boss and power names are distinctive coinages; Monkey
    Knowledge names are often generic English ("More Cash"), so MK
    additionally requires the text to mention knowledge / MK — the way
    users actually ask about an MK point.
    """
    try:
        from services import btd6_data_service

        dataset = btd6_data_service.get_dataset()
    except Exception:  # noqa: BLE001 — defensive
        return []

    text = (message_text or "").lower()
    if not text:
        return []
    out: list[str] = []

    def _effect_summary(effect: dict[str, Any]) -> str:
        import json

        return json.dumps(effect, sort_keys=True, separators=(",", ":"))

    for power in dataset.powers:
        name = power.canonical.strip().lower()
        if not name or name not in text:
            continue
        bits = [f"cost: {power.monkey_money_cost} Monkey Money"]
        if power.quantity:
            bits.append(f"max {power.quantity} per game")
        if power.between_rounds:
            bits.append("usable between rounds")
        out.append(
            f"[btd6_power] {power.canonical} (power) — {power.description} "
            f"({'; '.join(bits)})",
        )
        if power.effect:
            out.append(
                f"[btd6_power] {power.canonical} — decoded effect: "
                f"{_effect_summary(power.effect)}",
            )

    if "knowledge" in text or re.search(r"\bmk\b", text):
        for entry in dataset.monkey_knowledge:
            name = entry.canonical.strip().lower()
            if not name or name not in text:
                continue
            line = (
                f"[btd6_knowledge] {entry.canonical} ({entry.category} tree, "
                f"Monkey Knowledge) — {entry.description}"
            )
            if entry.effect:
                line += f" | decoded effect: {_effect_summary(entry.effect)}"
            if entry.prerequisites:
                line += f" | requires: {', '.join(entry.prerequisites)}"
            out.append(line)

    def _tier_bits(rows: Any) -> list[str]:
        bits = []
        for t in rows or ():
            tier = t.get("tier") if isinstance(t, dict) else getattr(t, "tier", None)
            hp = t.get("health") if isinstance(t, dict) else getattr(t, "health", None)
            spd = t.get("speed") if isinstance(t, dict) else getattr(t, "speed", None)
            if tier is None or hp is None:
                continue
            bit = f"T{tier} {hp:,} HP"
            if spd is not None:
                bit += f" (speed {spd})"
            bits.append(bit)
        return bits

    for boss in dataset.bosses:
        name = boss.canonical.strip().lower()
        if not name or name not in text:
            continue
        blurb = boss.tagline or boss.description
        line = f"[btd6_boss] {boss.canonical} (boss bloon) — {blurb}"
        if boss.immune_to:
            line += f" | immune to: {', '.join(boss.immune_to)}"
        if boss.tiers:
            line += f" | {len(boss.tiers)} tier(s) on record"
        out.append(line)
        # The HP numbers themselves — the live "base HP of Lych per tier"
        # miss (2026-06-10): the teaser line above told the model the tiers
        # exist without giving any figure, so a healthy answer had nothing
        # to ground and the faithfulness floor refused. Single bounded line
        # per named boss (≤5 tiers). Standard and Elite are labeled
        # explicitly (BUG-0002: standard figures were served as "Elite") —
        # the variant words must appear next to the numbers they describe.
        standard_bits = _tier_bits(boss.tiers)
        if standard_bits:
            out.append(
                f"[btd6_boss] {boss.canonical} per-tier health — Standard "
                "(non-Elite) ranked boss, single-player: " + " · ".join(standard_bits),
            )
        if "elite" in text:
            elite_bits = _tier_bits(boss.elite_tiers)
            if elite_bits:
                out.append(
                    f"[btd6_boss] ELITE {boss.canonical} per-tier health "
                    "(single-player): "
                    + " · ".join(elite_bits)
                    + " — answer Elite questions from these figures, NOT "
                    "from the Standard table.",
                )
            else:
                out.append(
                    f"[btd6_boss] Elite {boss.canonical} health is NOT in the "
                    "dataset — only standard-tier health is on record. If the "
                    "user supplies their own Elite modifier, apply it as THEIR "
                    "premise and say the base figures are the verified part.",
                )
    return out


def _fixture_facts_for_intent(intent: Any, *, message_text: str = "") -> list[str]:
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
    raw_text = str(getattr(intent, "raw_text", "") or "")
    crosspaths = _crosspaths_in_text(raw_text)
    for tower in getattr(intent, "towers", ()) or ():
        tower_id = str(getattr(tower, "id", "") or "")
        if not tower_id:
            continue
        record = btd6_data_service.get_tower(tower_id)
        if record is not None:
            lines.extend(_render_fixture_tower(record))
            for code in crosspaths:
                lines.extend(_render_tower_crosspath(tower_id, record.canonical, code))
            lines.extend(_crosspath_pricing_lines(record, crosspaths, raw_text))
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
    # render them directly rather than re-fetching by number. BUG-0010: the
    # resolver only knows the standard set — when the question says ABR
    # ("how much RBE is in r87 in ABR"), swap each round for its
    # Alternate Bloons Rounds entry and say so on every line, or the model
    # serves (or refuses over) standard data labeled ABR.
    abr_cue = bool(_ABR_CUE_RE.search(message_text or ""))
    for round_entry in getattr(intent, "rounds", ()) or ():
        if abr_cue:
            number = getattr(round_entry, "round_number", None)
            abr_entry = (
                btd6_data_service.get_round(int(number), roundset="abr")
                if number is not None
                else None
            )
            if abr_entry is not None:
                lines.extend(
                    _render_fixture_round(abr_entry, roundset_label="ABR"),
                )
                continue
            lines.append(
                f"[btd6_round] Round {number} has no Alternate Bloons Rounds "
                "entry in the dataset — the standard-set figures below are "
                "NOT the ABR values.",
            )
        lines.extend(_render_fixture_round(round_entry))
    # CT relics carry their static effect from the catalog.
    for relic in getattr(intent, "ct_relics", ()) or ():
        lines.extend(_render_ct_relic(relic))
    return lines


# Word-number quantities players actually write ("five 0-2-4 dart monkeys").
_QUANTITY_WORDS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fifteen": 15,
    "twenty": 20,
}

_QUANTITY_BEFORE_RE = re.compile(
    r"(?:\b(\d{1,4})|\b(" + "|".join(_QUANTITY_WORDS) + r"))\s*[x×*]?\s*$",
    re.I,
)


def _quantity_before(text: str, position: int) -> int | None:
    """The count immediately preceding ``position`` ("10 041", "five 024"), or None.

    Owner-corrected semantics (BUG-0003, 2026-06-11): "10 041 despos" means
    TEN 0-4-1 Desperados — quantity then crosspath — never the number 10,041
    (which players write without the space, and which the crosspath regex
    already rejects via its digit-adjacency guards).
    """
    match = _QUANTITY_BEFORE_RE.search(text[:position])
    if match is None:
        return None
    if match.group(1):
        value = int(match.group(1))
        return value if 0 < value <= 9999 else None
    return _QUANTITY_WORDS[match.group(2).lower()]


def _format_costs(costs: dict[str, int]) -> str:
    return " · ".join(f"{d.capitalize()} ${v:,}" for d, v in costs.items())


def _crosspath_pricing_lines(
    record: Any,
    crosspaths: list[str],
    raw_text: str,
) -> list[str]:
    """``[btd6_pricing]`` lines for the cost-question family the resolver sees.

    "how much do 10 041 despos cost on impop" needs the full 0-4-1 unit cost
    AND the ×10 totals in the grounded haystack — the faithfulness guard
    (rightly) blocks any sum the model derives itself, so without these lines
    the question is unanswerable on every path. One line per named crosspath
    (≤3, the `_crosspaths_in_text` cap); a bare "N <tower>s" with no
    crosspath gets the base-tower bulk line instead.
    """
    from services import btd6_data_service

    lines: list[str] = []
    lowered = raw_text.lower()
    for code in crosspaths:
        quantity = None
        for match in _CROSSPATH_RE.finditer(raw_text):
            if "".join(match.groups()) == code:
                quantity = _quantity_before(raw_text, match.start())
                break
        priced = btd6_data_service.crosspath_cost(
            record.canonical,
            code,
            quantity=quantity if quantity and quantity > 1 else None,
        )
        if not priced.get("found"):
            continue
        label = " + ".join(priced.get("upgrade_names") or ()) or "base"
        line = (
            f"[btd6_pricing] {priced['code']} {record.canonical} ({label}) "
            f"full cost per tower: "
            f"{_format_costs(priced['unit_costs_by_difficulty'])} "
            f"(base + each upgrade rounded to $5 per purchase at that "
            f"difficulty)."
        )
        totals = priced.get("total_costs_by_difficulty")
        if totals:
            # Spell the notation out AND negate the misreading: the model saw
            # "10 041" in the user text and multiplied the unit cost by 10,041
            # despite this line's ×10 total (live miss 2026-06-11 — the wrong
            # product entered the reply, and a tool call with the misread
            # quantity can even launder it into the trusted ledger). State the
            # only correct reading explicitly so the verifier's haystack and
            # the instruction agree.
            qty = priced["quantity"]
            line += (
                f" ×{qty} towers → {_format_costs(totals)}."
                f" (The user's '{qty} {priced['code']}' means {qty} towers at "
                f"crosspath {priced['code']} — it is NOT the single number "
                f"{qty}{priced['code'].replace('-', '')}. Use these grounded "
                f"totals verbatim; do not recompute.)"
            )
        lines.append(line)
    if not crosspaths:
        # "how much do 10 despos cost" — quantity straight before the tower
        # name/alias (optionally pluralised) prices N base towers.
        alts = sorted(
            {record.canonical.lower(), *(a.lower() for a in record.aliases)},
            key=len,
            reverse=True,
        )
        pattern = (
            r"\b(?:" + "|".join(re.escape(a) for a in alts if len(a) >= 3) + r")s?\b"
        )
        name_match = re.search(pattern, lowered)
        if name_match is not None:
            quantity = _quantity_before(lowered, name_match.start())
            if quantity and quantity > 1:
                priced = btd6_data_service.crosspath_cost(
                    record.canonical,
                    "000",
                    quantity=quantity,
                )
                if priced.get("found"):
                    lines.append(
                        f"[btd6_pricing] {priced['quantity']}× "
                        f"{record.canonical} (base tower, no upgrades): "
                        f"{_format_costs(priced['total_costs_by_difficulty'])} "
                        f"(per tower: "
                        f"{_format_costs(priced['unit_costs_by_difficulty'])}).",
                    )
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

    Retrieval only — see ``docs/btd6/btd6-absence-claim-guard-design.md`` §4.1
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


async def _conversation_carryover_facts(
    guild_id: int,
    channel_id: int,
    *,
    current_text: str = "",
) -> list[str]:
    """Ground the newest recent conversation turn that resolves BTD6 entities.

    Deterministic, read-only, no new state: scans the existing per-channel
    ``ai_conversation_service`` deque **with its default window** — grounding
    deliberately never reads more history than the model prompt's always-on
    floor can see. Each candidate turn is grounded through this module's own
    ``build`` (entity-bearing text → its full grounding, identical to what
    the original question got), with channel identity omitted so the
    fallback can never recurse. Plan:
    ``docs/planning/btd6-conversation-grounding-plan-2026-06-10.md``.

    ``current_text``: turns identical to the question being grounded are
    skipped — a cooldown-denied first attempt is recorded in the floor, and
    when the question itself resolves a generic entity ("…damage **lead**")
    that duplicate becomes the "newest entity-bearing turn", grounding the
    user's own re-ask instead of the conversation subject (live miss
    2026-06-11, the Geraldo follow-up's second floor).
    """
    from services import ai_conversation_service

    normalized_current = " ".join((current_text or "").lower().split())
    turns = ai_conversation_service.recent_turns(guild_id, channel_id)
    for turn in reversed(turns):  # newest first
        text = (getattr(turn, "text", "") or "").strip()
        if not text:
            continue
        if normalized_current and " ".join(text.lower().split()) == normalized_current:
            continue
        prior = await build(text)
        if not prior.facts:
            continue
        label = (
            "[btd6_carryover] The user's latest message names no BTD6 entity; "
            "the facts below are grounded from the recent conversation "
            "(most recent turn that named one). If the user appears to mean a "
            "different subject, ask instead of assuming."
        )
        return [label, *prior.facts]
    return []


async def build(
    message_text: str,
    *,
    guild_id: int | None = None,
    channel_id: int | None = None,
    conversation_followup: bool = False,
) -> BTD6Context:
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

    With ``guild_id`` + ``channel_id`` (the natural-language mention path), a
    zero-fact build falls back to **conversation carryover**: a follow-up
    like "does *it* make coins at the end of round" names no entity, so the
    passes above ground nothing and the model would answer from memory while
    sounding sourced (the 2026-06-10 Navarch screenshot, turn 2). The
    fallback grounds the newest recent turn that resolves BTD6 entities —
    typically the bot's own previous answer — labeled ``[btd6_carryover]``
    so the model can hedge. Callers without channel identity (the Ask
    command, the ``btd6_lookup`` tool) keep today's behaviour exactly.
    """
    facts: list[str] = []
    live_rows: list[dict[str, Any]] = []
    nk_rows_present = False
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
            nk_rows_present = bool(rows)
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
        facts.extend(_fixture_facts_for_intent(intent, message_text=message_text))

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

        # Pass 3b3: a paragon DEGREE named in the text ("d67 dart", "degree 67")
        # — only paragons have degrees (1-100). The name/tower passes above
        # ground the paragon's Degree 1/100 anchors; this adds the exact
        # NON-linear headline at the requested intermediate degree, explicitly
        # labelled, so the model neither interpolates nor misreads the "d67"
        # shorthand as an upgrade path "0-6-7" (BUG-0015). Isolated like the
        # other passes.
        try:
            facts.extend(_paragon_degree_facts(message_text))
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: paragon-degree grounding unavailable (%s)",
                exc,
            )

        # Pass 3b2: a minion/sub-tower named directly ("Mini Sun Avatar",
        # "Crushing Sentry", "UAV") — its stats live under the owning tier /
        # hero level / paragon, keyed by nothing the resolver knows. Isolated
        # like the other passes.
        try:
            facts.extend(_subtower_name_facts(message_text, resolved_tower_ids))
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: minion-name grounding unavailable (%s)",
                exc,
            )

        # Pass 3e: powers / Monkey Knowledge / bosses named in the text —
        # the three fixture catalogs the pipeline never grounded (their
        # dedicated AI tools were the only path; the deterministic Ask had
        # none). Isolated like the other passes.
        try:
            facts.extend(_catalog_facts(message_text))
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: catalog grounding unavailable (%s)",
                exc,
            )

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
        # docs/btd6/btd6-absence-claim-guard-design.md §4.1 (Layer A / mechanism 2).
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

        # Pass 3f: path/line-aware grounding — a "<tower> <top|middle|bottom> path"
        # reference ("bomb shooter middle path") resolves to no single upgrade, so
        # Pass 3c grounds nothing and the model fills the vacuum with a confident
        # false "no" ("that path has no MOAB bonus"). Ground the whole path's tier
        # line so the absence claim can't form. Retrieval only — the other half of
        # Layer A, see docs/btd6/btd6-absence-claim-guard-design.md §4.1 (Pass 3d is
        # mechanism 2; this is the path/line bullet). Isolated like its siblings.
        try:
            from services import btd6_upgrade_detail_service

            facts.extend(
                btd6_upgrade_detail_service.path_grounding_for_query(message_text),
            )
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: path grounding unavailable (%s)",
                exc,
            )

        # Pass 3g: damage-type / status-effect INTERACTION grounding. The
        # "can tower X deal with bloon Y?" class is the model's single biggest
        # BTD6 error source — the bloon immunities and the tower descriptions
        # are grounded separately, so the model invents the interaction rule (a
        # live screenshot had it claim "Lead resists glue" — false: glue is a
        # status effect that ignores damage-type immunity). This pass grounds
        # the explicit, wiki-verified rule from damage_types.json whenever a
        # damage type / status effect / bloon property is named with an
        # interaction cue. Message-keyed (not intent-keyed) and isolated like
        # its siblings.
        try:
            from services import btd6_interaction_service

            facts.extend(btd6_interaction_service.interaction_facts(message_text))
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: interaction grounding unavailable (%s)",
                exc,
            )

        # Pass 4: coverage + freshness signals (raw lines; the instruction
        # stack wraps the whole bundle as untrusted data). Paired with the
        # _TASK_CONTRACT live-event directive.
        facts.extend(_coverage_freshness_signals(intent, live_rows))

    # Zero-fact fallback — OR a router-detected follow-up. The zero-fact
    # condition alone misses partial grounding: "which of those can damage
    # lead" resolves the Lead BLOON (facts non-empty) while the actual
    # subject (the prior turn's Geraldo items) grounds nothing, so the reply
    # names the subject and floors (live miss 2026-06-11, first Haiku round).
    # When the router routed HERE because of the conversation cue
    # (``conversation_followup``), the carryover facts are always added.
    if (
        (not facts or conversation_followup)
        and guild_id is not None
        and channel_id is not None
    ):
        try:
            carryover = await _conversation_carryover_facts(
                guild_id,
                channel_id,
                current_text=message_text,
            )
            seen = set(facts)
            facts.extend(line for line in carryover if line not in seen)
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.debug(
                "btd6_context_service: carryover grounding unavailable (%s)",
                exc,
            )

    if facts:
        # NK-sourced DB rows (live or stored) → the Tier-1 summary; a
        # fixture/dataset-only answer must say so (item 6c) — its per-fact
        # labels and its headline source now agree.
        source_summary = (
            _DEFAULT_SOURCE_SUMMARY if nk_rows_present else _DATASET_SOURCE_SUMMARY
        )
    return BTD6Context(
        facts=tuple(facts),
        source_summary=source_summary,
        confidence=confidence,
    )


__all__ = ["BTD6Context", "build"]

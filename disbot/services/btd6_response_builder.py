"""BTD6 response builder.

Renders deterministic knowledge into a stable domain object the
BTD6 Cog (Module 4) turns into a Discord embed. Keeping the shape
in a single place lets later modules (AI augmentation in Module 5)
add explanatory text without changing the deterministic fields.

The shape mirrors the user's plan: short answer, why it matters,
recommended options, common mistakes, version sensitivity,
confidence, sources, follow-up. Fields not relevant to a given
query stay empty rather than carrying placeholder prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from services.btd6_data_service import HeroEntry, MapEntry, ModeEntry
from services.btd6_knowledge_service import (
    RoundFact,
    TowerFact,
    data_version,
    game_version,
)
from services.btd6_live_query_service import TowerRestrictionContext
from services.btd6_resolver_service import ResolvedIntent


@dataclass(frozen=True)
class BTD6Response:
    """Stable BTD6 response shape consumed by the Cog renderer."""

    title: str
    short_answer: str
    why_it_matters: str = ""
    recommended_options: tuple[str, ...] = ()
    common_mistakes: tuple[str, ...] = ()
    version_sensitivity: str = ""
    confidence: str = "medium"
    sources: tuple[str, ...] = ()
    follow_up: str = ""
    fields: tuple[tuple[str, str], tuple[str, str]] | tuple = field(
        default_factory=tuple,
    )
    # Optional live grounding bundle from btd6_context_service. Already
    # sanitised + provenance-labelled; the renderer surfaces these as a
    # dedicated "Live data" field separate from the deterministic body.
    live_facts: tuple[str, ...] = ()


def _source_label() -> str:
    return f"BTD6 data v{data_version()} (game v{game_version()})"


def _event_label(ctx: TowerRestrictionContext) -> str:
    """Render the event kind + name suffix for restriction lines."""
    kind_map = {
        "btd6_race": "race",
        "btd6_boss_difficulty": "boss",
        "btd6_odyssey_difficulty": "odyssey",
        "btd6_challenge": "challenge",
    }
    return f"{kind_map.get(ctx.event_kind, ctx.event_kind)} '{ctx.event_name}'"


def _ends_in(end_ms: int | None) -> str:
    """Compact ``ends in Xh`` suffix; empty when ``end_ms`` is unknown / past."""
    if not isinstance(end_ms, (int, float)) or end_ms <= 0:
        return ""
    try:
        end = datetime.fromtimestamp(end_ms / 1000.0, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return ""
    delta = end - datetime.now(tz=timezone.utc)
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return ""
    if seconds < 3600:
        return f" (ends in {seconds // 60}m)"
    if seconds < 86_400:
        return f" (ends in {seconds // 3600}h)"
    return f" (ends in {seconds // 86_400}d)"


def _format_restriction_lines(
    restrictions: tuple[TowerRestrictionContext, ...],
) -> tuple[str, ...]:
    """One line per restricted event; skip stance='allowed'. Sentinel
    ``sentinel_all_heroes_banned`` renders with explicit
    'ALL HEROES BANNED' wording so callers can phrase it correctly.
    """
    lines: list[str] = []
    for ctx in restrictions:
        if ctx.stance == "allowed":
            continue
        label = _event_label(ctx)
        ends = _ends_in(ctx.end_ms)
        if ctx.sentinel_all_heroes_banned:
            lines.append(f"{label}: 🚫 ALL HEROES BANNED{ends}")
            continue
        if ctx.stance == "banned":
            lines.append(f"{label}: 🚫 BANNED{ends}")
        elif ctx.stance == "limited":
            parts = [f"max {ctx.max_count}"]
            for label_text, count in (
                ("path1 top", ctx.path1_blocked),
                ("path2 top", ctx.path2_blocked),
                ("path3 top", ctx.path3_blocked),
            ):
                if count:
                    parts.append(f"{label_text} {count}")
            lines.append(f"{label}: ⚠️ LIMITED ({', '.join(parts)}){ends}")
        elif ctx.stance == "path_blocked":
            parts = []
            for label_text, count in (
                ("path1 top", ctx.path1_blocked),
                ("path2 top", ctx.path2_blocked),
                ("path3 top", ctx.path3_blocked),
            ):
                if count:
                    parts.append(f"{label_text} {count}")
            lines.append(f"{label}: 🪜 {', '.join(parts)} blocked{ends}")
    return tuple(lines)


def for_tower(
    fact: TowerFact,
    *,
    restrictions: tuple[TowerRestrictionContext, ...] = (),
) -> BTD6Response:
    tower = fact.tower
    recommended: list[str] = []
    for path, tiers in tower.upgrade_paths.items():
        recommended.append(
            f"{path}: "
            + " → ".join(tiers[:3])
            + (f" (… {len(tiers) - 3} more)" if len(tiers) > 3 else ""),
        )
    return BTD6Response(
        title=f"{tower.canonical} — overview",
        short_answer=tower.description,
        why_it_matters=(f"Base cost: {fact.base_cost}. Category: {tower.category}."),
        recommended_options=tuple(recommended),
        common_mistakes=(
            "Buying high-tier upgrades on the wrong path can stall economy.",
        ),
        version_sensitivity=(
            "Tower stats and crosspath interactions can change patch-to-patch; "
            "always confirm against the latest patch notes for competitive play."
        ),
        confidence="high",
        sources=(tower.wiki_url, _source_label()),
        follow_up="Ask about a specific upgrade tier with `!btd6 tower <name>`.",
        live_facts=_format_restriction_lines(restrictions),
    )


def for_hero(
    hero: HeroEntry,
    *,
    restrictions: tuple[TowerRestrictionContext, ...] = (),
) -> BTD6Response:
    abilities = tuple(
        f"L{ability.level}: {ability.name} — {ability.summary}"
        for ability in hero.abilities
    )
    return BTD6Response(
        title=f"{hero.canonical} — overview",
        short_answer=hero.description,
        why_it_matters=f"Base cost: {hero.base_cost}.",
        recommended_options=abilities,
        version_sensitivity=(
            "Hero balance changes are common; check patch notes for buffs/nerfs."
        ),
        confidence="medium",
        sources=(hero.wiki_url, _source_label()),
        follow_up="Try `!btd6 round <N>` to see what waves the hero faces.",
        live_facts=_format_restriction_lines(restrictions),
    )


def for_map(game_map: MapEntry) -> BTD6Response:
    return BTD6Response(
        title=f"{game_map.canonical} ({game_map.difficulty})",
        short_answer=game_map.description,
        why_it_matters=game_map.lines_of_sight_notes,
        sources=(game_map.wiki_url, _source_label()),
        confidence="high",
        follow_up="Pair with `!btd6 mode <name>` for mode-specific advice.",
    )


def for_mode(mode: ModeEntry) -> BTD6Response:
    return BTD6Response(
        title=f"{mode.canonical} mode",
        short_answer=mode.description,
        why_it_matters=(
            f"Starting cash: {mode.starting_cash}. "
            f"Starting lives: {mode.starting_lives}."
        ),
        recommended_options=mode.restrictions,
        confidence="high",
        sources=(_source_label(),),
    )


def for_round(fact: RoundFact) -> BTD6Response:
    return BTD6Response(
        title=f"Round {fact.round_number} — danger: {fact.danger}",
        short_answer=fact.summary,
        why_it_matters=(
            "Threats this round: "
            + (", ".join(fact.common_threats) if fact.common_threats else "—")
        ),
        version_sensitivity=(
            "Round composition is stable but can shift slightly during major patches."
        ),
        confidence="high",
        sources=(_source_label(),),
        follow_up="Use `!btd6 ask` for strategy advice on a specific round.",
    )


def for_unresolved(intent: ResolvedIntent) -> BTD6Response:
    return BTD6Response(
        title="No BTD6 entities recognised",
        short_answer=(
            "I couldn't find a tower, hero, map, mode, or round in your message."
        ),
        why_it_matters=(
            f"Confidence: {intent.confidence:.2f}. Try mentioning a tower "
            "by name (e.g. ``Dart Monkey``), a map, or a round number "
            "like ``round 63``."
        ),
        confidence="low",
        sources=(_source_label(),),
        follow_up=("Use `!btd6 status` to confirm the BTD6 assistant is enabled."),
    )

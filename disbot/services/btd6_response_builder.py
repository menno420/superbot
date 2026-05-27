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

from services.btd6_data_service import HeroEntry, MapEntry, ModeEntry
from services.btd6_knowledge_service import (
    RoundFact,
    TowerFact,
    data_version,
    game_version,
)
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


def for_tower(fact: TowerFact) -> BTD6Response:
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
    )


def for_hero(hero: HeroEntry) -> BTD6Response:
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

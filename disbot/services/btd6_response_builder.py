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

from services.btd6_data_service import BloonEntry, HeroEntry, MapEntry, ModeEntry
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
    # Named (label, value) sections rendered as their own embed fields.
    # Towers use these for the per-path upgrade-cost breakdown.
    fields: tuple[tuple[str, str], ...] = field(default_factory=tuple)
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


def format_restriction_lines(
    restrictions: tuple[TowerRestrictionContext, ...],
) -> tuple[str, ...]:
    """Public: tower event-restriction display lines (skips ``stance='allowed'``).

    Used by the tower-detail event-status drill-down view.
    """
    return _format_restriction_lines(restrictions)


_PATH_LABELS = {"top": "Top path", "mid": "Middle path", "bot": "Bottom path"}


def _format_upgrade_path(
    tiers: tuple[str, ...],
    costs: tuple[int, ...],
) -> str:
    """Render one path as ``Name ($cost) → …``; cost ``0`` means unknown."""
    parts: list[str] = []
    for index, name in enumerate(tiers):
        cost = costs[index] if index < len(costs) else 0
        parts.append(f"{name} (${cost:,})" if cost > 0 else name)
    return " → ".join(parts)


def for_tower(
    fact: TowerFact,
    *,
    restrictions: tuple[TowerRestrictionContext, ...] = (),
) -> BTD6Response:
    tower = fact.tower
    path_fields: list[tuple[str, str]] = []
    for path, tiers in tower.upgrade_paths.items():
        if not tiers:
            continue
        label = _PATH_LABELS.get(path, f"{path.title()} path")
        costs = tower.upgrade_costs.get(path, ())
        path_fields.append((label, _format_upgrade_path(tiers, costs)))
    short_answer = tower.description or (
        f"A {tower.category} tower costing ${fact.base_cost:,} to place. "
        "Upgrade paths and per-tier costs are listed below."
    )
    return BTD6Response(
        title=f"{tower.canonical} — overview",
        short_answer=short_answer,
        why_it_matters=(
            f"Base cost: ${fact.base_cost:,}. Category: {tower.category.title()}."
        ),
        fields=tuple(path_fields),
        common_mistakes=(
            "Buying high-tier upgrades on the wrong path can stall economy.",
        ),
        version_sensitivity=(
            "Tower stats and crosspath interactions can change patch-to-patch; "
            "always confirm against the latest patch notes for competitive play."
        ),
        confidence="high",
        sources=(_source_label(),),
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
        sources=(_source_label(),),
        follow_up="Try `!btd6 round <N>` to see what waves the hero faces.",
        live_facts=_format_restriction_lines(restrictions),
    )


def for_map(game_map: MapEntry) -> BTD6Response:
    why = game_map.lines_of_sight_notes
    # Removable obstacles ride alongside line-of-sight (most removables ARE LoS
    # blockers). Only present for maps with curated data; absent = unknown.
    if game_map.removables:
        why = f"{why} Removable obstacles: {game_map.removables}"
    return BTD6Response(
        title=f"{game_map.canonical} ({game_map.difficulty})",
        short_answer=game_map.description,
        why_it_matters=why,
        sources=(_source_label(),),
        confidence="high",
        follow_up="Pair with `!btd6 mode <name>` for mode-specific advice.",
    )


def for_mode(mode: ModeEntry) -> BTD6Response:
    # Modifiers (Double Cash, Fast Track) have no fixed cash/lives — their effect
    # is relative — so only state those numbers when the row carries them.
    bits: list[str] = []
    if mode.starting_cash is not None:
        bits.append(f"Starting cash: {mode.starting_cash}.")
    if mode.starting_lives is not None:
        bits.append(f"Starting lives: {mode.starting_lives}.")
    return BTD6Response(
        title=f"{mode.canonical} mode",
        short_answer=mode.description,
        why_it_matters=" ".join(bits),
        recommended_options=mode.restrictions,
        confidence="high",
        sources=(_source_label(),),
    )


def for_round(fact: RoundFact) -> BTD6Response:
    economy_bits: list[str] = []
    if fact.rbe is not None:
        economy_bits.append(f"RBE **{fact.rbe:,}**")
    if fact.cash is not None:
        cumulative = (
            f" (cumulative **${fact.cumulative_cash:,.0f}**)"
            if fact.cumulative_cash is not None
            else ""
        )
        economy_bits.append(f"Cash **${fact.cash:,.0f}**{cumulative}")
    if fact.base_xp is not None:
        economy_bits.append(f"XP **{fact.base_xp:,}**")
    fields: tuple[tuple[str, str], ...] = (
        (("Economy", " · ".join(economy_bits)),) if economy_bits else ()
    )
    return BTD6Response(
        title=f"Round {fact.round_number} — danger: {fact.danger}",
        short_answer=fact.summary,
        why_it_matters=(
            "Threats this round: "
            + (", ".join(fact.common_threats) if fact.common_threats else "—")
        ),
        fields=fields,
        version_sensitivity=(
            "Round composition is stable but can shift slightly during major patches."
        ),
        confidence="high",
        sources=(_source_label(),),
        follow_up="Use `!btd6 ask` for strategy advice on a specific round.",
    )


def for_bloon(bloon: BloonEntry) -> BTD6Response:
    """Deterministic bloon answer — health/RBE/speed + what it pops into.

    The resolver has matched bloons for a while, but ``deterministic_answer``
    had no branch for them, so "what does a ceramic pop into" fell through to
    the unresolved refusal (found by the #655 answerability verification).
    """
    stat_bits: list[str] = []
    if bloon.health is not None:
        fortified = (
            f" ({bloon.health_fortified} fortified)"
            if bloon.health_fortified is not None
            else ""
        )
        stat_bits.append(f"Health: {bloon.health}{fortified}")
    if bloon.rbe is not None:
        fortified = (
            f" ({bloon.rbe_fortified} fortified)"
            if bloon.rbe_fortified is not None
            else ""
        )
        stat_bits.append(f"RBE: {bloon.rbe}{fortified}")
    if bloon.speed is not None:
        stat_bits.append(f"Speed: {bloon.speed:g}")
    options: list[str] = []
    if bloon.children:
        options.append(f"Pops into: {bloon.children}")
    if bloon.immune_to:
        options.append(f"Immune to: {', '.join(bloon.immune_to)}")
    if bloon.properties:
        options.append(f"Properties: {', '.join(bloon.properties)}")
    return BTD6Response(
        title=f"{bloon.canonical} — bloon ({bloon.category})",
        short_answer=bloon.description,
        why_it_matters=" · ".join(stat_bits),
        recommended_options=tuple(options),
        confidence="high",
        sources=(_source_label(),),
        follow_up="Ask about a specific round to see where this bloon appears.",
    )


def for_reference_facts(facts: tuple[str, ...]) -> BTD6Response:
    """Facts-led answer for queries no entity intent matches but the shared
    grounding pipeline (``btd6_context_service``) answered anyway — powers,
    Monkey Knowledge, bosses, Geraldo items, CT relics…

    Without this, the menu's Ask path showed the right facts under a
    "couldn't find anything" headline (the #655 verification's item-5 gap);
    the AI tool path had no such problem because the model reads the facts
    directly. The first fact leads; the renderer's Live-data field carries
    the full list.
    """
    headline = facts[0]
    # Strip the machine-ish "[btd6_kind]" routing prefix from the headline —
    # the full prefixed lines still render in the Live-data field.
    if headline.startswith("[") and "] " in headline:
        headline = headline.split("] ", 1)[1]
    return BTD6Response(
        title="BTD6 reference",
        short_answer=headline,
        why_it_matters=(
            f"Matched {len(facts)} verified fact(s) from the BTD6 dataset "
            "(full list below)."
        ),
        confidence="medium",
        sources=(_source_label(),),
        live_facts=facts,
    )


def for_list_reply(reply: str) -> BTD6Response:
    """Wrap a deterministic list-floor string as a :class:`BTD6Response`.

    The BUG-0009 / round-range list floors (``btd6_context_service`` —
    e.g. "list all the bloons from r29 till r63") return a self-contained
    markdown answer the conversational stage sends verbatim. The Ask modal /
    ``!btd6 ask`` render a :class:`BTD6Response` instead, so this carries the
    floor string through unchanged as the embed body — the two surfaces serve
    the one authoritative answer rather than the Ask path re-deriving a weaker
    one from the endpoint-only intent. High confidence: the floor is
    code-built, not model-authored.
    """
    return BTD6Response(
        title="BTD6",
        short_answer=reply,
        confidence="high",
        sources=(_source_label(),),
    )


# The one string the unresolved path is recognised by (``answer_question``
# upgrades an unresolved response to ``for_reference_facts`` when grounding
# found facts anyway) — never compare against a literal copy of the title.
UNRESOLVED_TITLE = "No BTD6 entities recognised"


def for_unresolved(intent: ResolvedIntent) -> BTD6Response:
    return BTD6Response(
        title=UNRESOLVED_TITLE,
        short_answer=(
            "I couldn't find a tower, hero, map, mode, round, or bloon in your message."
        ),
        why_it_matters=(
            f"Confidence: {intent.confidence:.2f}. Try mentioning a tower "
            "by name (e.g. ``Dart Monkey``), a map, a bloon, a power, or a "
            "round number like ``round 63``."
        ),
        confidence="low",
        sources=(_source_label(),),
        follow_up=("Use `!btd6 status` to confirm the BTD6 assistant is enabled."),
    )

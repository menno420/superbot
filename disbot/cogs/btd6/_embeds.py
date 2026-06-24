"""Embed builders for BTD6 (extracted from btd6_cog.py for size).

Most builders are pure functions over BTD6 service output and never
touch I/O. The exception is :func:`build_status_embed`, which is
``async`` and reads ``btd6_facts`` aggregates via
``btd6_knowledge_service.fact_summary_by_kind`` so the status panel
reflects live ingestion. No provider calls anywhere.

The cog and the panel view both consume from here so the cog itself
stays small enough to satisfy the S4.6 cog-size invariant.
"""

from __future__ import annotations

from datetime import datetime, timezone

import discord

from services import btd6_data_service, btd6_knowledge_service
from services.btd6_resolver_service import resolve
from utils.btd6.freshness_render import BUCKET_EMOJI as _BUCKET_EMOJI
from utils.btd6.mode_rules import summarize_mode_rules
from utils.btd6.response_embed import response_to_embed

# Useful-first display order for the Live facts block. Kinds not in
# this tuple are appended alphabetically — operators see the most
# relevant rotations first as the API grows.
_LIVE_KIND_ORDER = (
    "btd6_event",
    "btd6_map",
    "btd6_boss",
    "btd6_race",
    "btd6_challenge",
    "btd6_odyssey",
    "btd6_ct",
)


def _live_kind_sort_key(entity_kind: str) -> tuple[int, str]:
    """Useful-first ordering for live facts.

    Known kinds get their explicit rank; everything else falls through
    to an alphabetical tail so new kinds don't disappear from the panel.
    """
    try:
        return (_LIVE_KIND_ORDER.index(entity_kind), entity_kind)
    except ValueError:
        return (len(_LIVE_KIND_ORDER), entity_kind)


def _short_kind(entity_kind: str) -> str:
    """Strip the leading ``btd6_`` so the panel doesn't shout it 12 times."""
    if entity_kind.startswith("btd6_"):
        return entity_kind[len("btd6_") :]
    return entity_kind


def _format_age(last_fetched_at: datetime | None) -> str:
    """Render newest-fact age as ``Xm ago`` / ``Xh ago`` / ``Xd ago``.

    ``None`` → ``"never fetched"`` so the placeholder is grammatical.
    Naive datetimes are interpreted as UTC.
    """
    if last_fetched_at is None:
        return "never fetched"
    if last_fetched_at.tzinfo is None:
        last_fetched_at = last_fetched_at.replace(tzinfo=timezone.utc)
    seconds = int((datetime.now(tz=timezone.utc) - last_fetched_at).total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86_400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86_400}d ago"


def _format_live_facts_value(
    summaries: tuple[btd6_knowledge_service.FactKindSummary, ...],
    *,
    max_rows: int = 12,
) -> str:
    """Render the Live facts field value, ordered useful-first.

    Caps at ``max_rows`` so the embed never exceeds Discord's 1024-char
    field-value limit even with many kinds; the cap is well below the
    25-row embed-field maximum.
    """
    if not summaries:
        return (
            "No facts ingested yet. Run `!btd6 refresh-source <key>` "
            "or wait for the next supervisor cycle."
        )
    ordered = sorted(summaries, key=lambda s: _live_kind_sort_key(s.entity_kind))
    kept = ordered[:max_rows]
    lines = []
    for summary in kept:
        emoji = _BUCKET_EMOJI.get(summary.bucket, "⚪")
        age = _format_age(summary.last_fetched_at)
        count = f"{summary.fact_count} facts" if summary.fact_count != 1 else "1 fact"
        lines.append(
            f"{emoji} `{_short_kind(summary.entity_kind):<10}` "
            f"{count} · newest fact {age}",
        )
    dropped = len(ordered) - len(kept)
    if dropped > 0:
        lines.append(f"… (+{dropped} more)")
    return "\n".join(lines)


async def build_status_embed() -> discord.Embed:
    """BTD6 status: seed taxonomy + live ``btd6_facts`` aggregates.

    Two blocks. The "Reference (seed)" block reflects the static
    fixture set — towers, heroes, modes, rounds — and is what the
    deterministic resolver answers from. The "Live facts" block
    aggregates ``btd6_facts`` by ``entity_kind`` and bucketizes the
    newest-fact age via the central freshness helper. Per-source-key
    health stays in ``!btd6 source-health``.
    """
    embed = discord.Embed(
        title="🐵 BTD6 Assistant — Status",
        description=(
            "Deterministic facts plus live grounding for matched intents. "
            "Natural-language replies are gated by the AI Platform."
        ),
        color=discord.Color.green(),
    )
    embed.add_field(
        name="📚 Reference (seed)",
        value=(
            f"Data version: `{btd6_knowledge_service.data_version()}` · "
            f"Game version: `{btd6_knowledge_service.game_version()}`\n"
            f"Towers: **{len(btd6_knowledge_service.list_towers())}** · "
            f"Heroes: **{len(btd6_knowledge_service.list_heroes())}** · "
            f"Maps: **{len(btd6_knowledge_service.list_maps())}** · "
            f"Modes: **{len(btd6_knowledge_service.list_modes())}** · "
            f"Rounds: **{len(btd6_knowledge_service.list_rounds())}**"
        ),
        inline=False,
    )
    summaries = await btd6_knowledge_service.fact_summary_by_kind()
    embed.add_field(
        name="📊 Live facts (btd6_facts)",
        value=_format_live_facts_value(summaries),
        inline=False,
    )
    embed.add_field(
        name="🗄️ Data source",
        value=f"`{btd6_data_service.data_source_label()}`",
        inline=False,
    )
    drift = btd6_data_service.served_data_drift()
    if drift is not None:
        served, bundled = drift
        embed.add_field(
            name="⚠️ Data drift",
            value=(
                f"The deployed files carry **{bundled}** but this store is "
                f"serving **{served}** — data PRs do not refresh a "
                "postgres/cloud store. Run `!btd6 ops seed-data` to update "
                "(applies immediately, no restart)."
            ),
            inline=False,
        )
    else:
        # Same-version content drift (no game_version bump) — strict-(b)
        # auto-seed won't fire, so remind the operator to seed manually.
        changed = btd6_data_service.content_drift()
        if changed:
            embed.add_field(
                name="⚠️ Data drift (same version)",
                value=(
                    f"**{len(changed)}** committed data file(s) differ from this "
                    "store at the same version (e.g. "
                    f"`{'`, `'.join(changed[:3])}`). Run `!btd6 ops seed-data` to "
                    "apply (applies immediately, no restart)."
                ),
                inline=False,
            )
    from utils.btd6.context_footer import append_context_footer

    return append_context_footer(embed, "btd6_status:global")


def build_diagnostics_embed() -> discord.Embed:
    """Detailed diagnostics: source labels and entry catalogues."""
    embed = discord.Embed(
        title="🐵 BTD6 Assistant — Diagnostics",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="Towers",
        value=", ".join(t.canonical for t in btd6_knowledge_service.list_towers()),
        inline=False,
    )
    embed.add_field(
        name="Heroes",
        value=", ".join(h.canonical for h in btd6_knowledge_service.list_heroes()),
        inline=False,
    )
    # Counts only: the full 86-name roster blew Discord's 1024-char field cap
    # (the send 400s, it does not truncate), and the names already have one
    # canonical home — build_maps_embed, grouped by difficulty.
    maps = btd6_knowledge_service.list_maps()
    by_difficulty: dict[str, int] = {}
    for game_map in maps:
        by_difficulty[game_map.difficulty] = (
            by_difficulty.get(game_map.difficulty, 0) + 1
        )
    embed.add_field(
        name="Maps",
        value=(
            f"{len(maps)} loaded — "
            + " · ".join(
                f"{d} {by_difficulty[d]}"
                for d in _MAP_DIFFICULTY_ORDER
                if d in by_difficulty
            )
            + " (full list: the 🗺️ Maps panel)"
        ),
        inline=False,
    )
    embed.add_field(
        name="Modes",
        value=", ".join(m.canonical for m in btd6_knowledge_service.list_modes()),
        inline=False,
    )
    rounds = ", ".join(
        str(r.round_number) for r in btd6_knowledge_service.list_rounds()
    )
    embed.add_field(name="Rounds tracked", value=rounds, inline=False)
    embed.add_field(
        name="Data source",
        value=(
            f"`{btd6_data_service.data_source_label()}`"
            f" · available: **{btd6_data_service.data_available()}**"
        ),
        inline=False,
    )
    from utils.btd6.context_footer import append_context_footer

    return append_context_footer(embed, "btd6_diagnostics:catalog")


def build_towers_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🐵 BTD6 — Towers",
        color=discord.Color.green(),
    )
    for tower in btd6_knowledge_service.list_towers():
        embed.add_field(
            name=tower.canonical,
            value=f"Cost: {tower.base_cost} • Category: {tower.category}",
            inline=True,
        )
    from utils.btd6.context_footer import append_context_footer

    return append_context_footer(embed, "btd6_tower:catalog")


_MAP_DIFFICULTY_ORDER = ("Beginner", "Intermediate", "Advanced", "Expert")


def build_maps_embed() -> discord.Embed:
    """Map catalogue grouped by difficulty (all 89 from game data).

    A water drop marks maps with water tiles (naval-tower placement) — the
    ``has_water`` fact added in the maps cutover. One field per difficulty keeps
    the full roster inside Discord's field limits.
    """
    embed = discord.Embed(
        title="🗺️ BTD6 — Maps",
        color=discord.Color.green(),
    )
    maps = btd6_knowledge_service.list_maps()
    by_difficulty: dict[str, list[str]] = {d: [] for d in _MAP_DIFFICULTY_ORDER}
    for game_map in maps:
        label = f"{game_map.canonical} 💧" if game_map.has_water else game_map.canonical
        by_difficulty.setdefault(game_map.difficulty, []).append(label)
    for difficulty in _MAP_DIFFICULTY_ORDER:
        names = by_difficulty.get(difficulty) or []
        if names:
            embed.add_field(
                name=f"{difficulty} ({len(names)})",
                value=", ".join(names),
                inline=False,
            )
    embed.set_footer(text="💧 = has water (naval towers placeable)")
    from utils.btd6.context_footer import append_context_footer

    return append_context_footer(embed, "btd6_diagnostics:maps_catalog")


def build_modes_embed() -> discord.Embed:
    """Difficulties, modes, and modifiers — grouped, mirroring the in-game
    difficulty/mode select screens (difficulty sets lives/speed/prices; Standard
    is the base mode in every difficulty; modifiers are opt-in cash/round changes).
    """
    embed = discord.Embed(
        title="🐵 BTD6 — Difficulties & Modes",
        color=discord.Color.green(),
    )
    modes = btd6_knowledge_service.list_modes()
    difficulties = [m for m in modes if m.kind == "difficulty"]
    play_modes = [m for m in modes if m.kind == "mode"]
    modifiers = [m for m in modes if m.kind == "modifier"]

    if difficulties:
        embed.description = (
            "**Difficulties** (set lives, bloon speed, prices)\n"
            + "\n".join(
                f"• **{d.canonical}** — {d.starting_lives} lives. {d.description}"
                for d in difficulties
            )
        )
    for mode in play_modes:
        tag = (
            f"  [{' / '.join(d.title() for d in mode.difficulties)}]"
            if mode.difficulties
            else ""
        )
        value = mode.description
        if mode.restrictions:
            value += "\n• " + "\n• ".join(mode.restrictions)
        rule_clauses = summarize_mode_rules(getattr(mode, "rules", {}) or {})
        if rule_clauses:
            value += f"\n📋 {'; '.join(rule_clauses)}"
        embed.add_field(name=f"{mode.canonical}{tag}", value=value[:1024], inline=False)
    for mod in modifiers:
        embed.add_field(
            name=f"⚙️ {mod.canonical} (modifier)",
            value=mod.description[:1024],
            inline=False,
        )
    from utils.btd6.context_footer import append_context_footer

    return append_context_footer(embed, "btd6_diagnostics:modes_catalog")


def build_heroes_embed() -> discord.Embed:
    """Hero catalogue — mirrors build_towers_embed shape."""
    embed = discord.Embed(
        title="🐵 BTD6 — Heroes",
        color=discord.Color.green(),
    )
    for hero in btd6_knowledge_service.list_heroes():
        embed.add_field(
            name=hero.canonical,
            value=f"Cost: {hero.base_cost} • {hero.description[:80]}",
            inline=False,
        )
    from utils.btd6.context_footer import append_context_footer

    return append_context_footer(embed, "btd6_hero:catalog")


def build_test_intent_embed(text: str) -> discord.Embed:
    """Resolver introspection — useful for operators tuning the cog."""
    intent = resolve(text)
    embed = discord.Embed(
        title="🐵 BTD6 — test-intent",
        description=f"Resolved intent for: ``{text[:200]}``",
        color=discord.Color.green(),
    )
    embed.add_field(name="Confidence", value=f"{intent.confidence:.2f}")
    embed.add_field(
        name="Towers",
        value=", ".join(t.canonical for t in intent.towers) or "—",
        inline=False,
    )
    embed.add_field(
        name="Heroes",
        value=", ".join(h.canonical for h in intent.heroes) or "—",
        inline=False,
    )
    embed.add_field(
        name="Maps",
        value=", ".join(m.canonical for m in intent.maps) or "—",
        inline=False,
    )
    embed.add_field(
        name="Modes",
        value=", ".join(m.canonical for m in intent.modes) or "—",
        inline=False,
    )
    embed.add_field(
        name="Rounds",
        value=", ".join(str(n) for n in intent.candidate_round_numbers) or "—",
        inline=False,
    )
    return embed


__all__ = [
    "build_diagnostics_embed",
    "build_heroes_embed",
    "build_maps_embed",
    "build_modes_embed",
    "build_status_embed",
    "build_test_intent_embed",
    "build_towers_embed",
    "response_to_embed",
]

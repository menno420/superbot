"""Embed builders for BTD6 (extracted from btd6_cog.py for size).

Pure functions that take BTD6 service output and produce
:class:`discord.Embed` instances. No DB access, no provider calls.
The cog and the panel view both consume from here so the cog itself
stays small enough to satisfy the S4.6 cog-size invariant.
"""

from __future__ import annotations

from typing import Any

import discord

from services import btd6_knowledge_service
from services.btd6_resolver_service import resolve


def response_to_embed(response: Any) -> discord.Embed:
    """Convert a :class:`BTD6Response` into a Discord embed."""
    color = {
        "high": discord.Color.green(),
        "medium": discord.Color.gold(),
        "low": discord.Color.light_grey(),
    }.get(response.confidence, discord.Color.light_grey())
    embed = discord.Embed(
        title=response.title,
        description=response.short_answer,
        color=color,
    )
    if response.why_it_matters:
        embed.add_field(
            name="Why it matters",
            value=response.why_it_matters,
            inline=False,
        )
    if response.recommended_options:
        embed.add_field(
            name="Recommended options",
            value="\n".join(f"• {opt}" for opt in response.recommended_options),
            inline=False,
        )
    if response.common_mistakes:
        embed.add_field(
            name="Common mistakes",
            value="\n".join(f"• {m}" for m in response.common_mistakes),
            inline=False,
        )
    if response.version_sensitivity:
        embed.add_field(
            name="Version sensitivity",
            value=response.version_sensitivity,
            inline=False,
        )
    if response.follow_up:
        embed.add_field(name="Follow-up", value=response.follow_up, inline=False)
    if response.sources:
        embed.set_footer(text="Sources: " + " · ".join(response.sources))
    return embed


def build_status_embed() -> discord.Embed:
    """BTD6 status: data version + entity counts."""
    embed = discord.Embed(
        title="🐵 BTD6 Assistant — Status",
        description=(
            "Deterministic facts plus live grounding for matched intents. "
            "Natural-language replies are gated by the AI Platform."
        ),
        color=discord.Color.green(),
    )
    embed.add_field(
        name="Data version",
        value=btd6_knowledge_service.data_version(),
        inline=True,
    )
    embed.add_field(
        name="Game version",
        value=btd6_knowledge_service.game_version(),
        inline=True,
    )
    embed.add_field(
        name="Towers",
        value=str(len(btd6_knowledge_service.list_towers())),
        inline=True,
    )
    embed.add_field(
        name="Heroes",
        value=str(len(btd6_knowledge_service.list_heroes())),
        inline=True,
    )
    embed.add_field(
        name="Maps",
        value=str(len(btd6_knowledge_service.list_maps())),
        inline=True,
    )
    embed.add_field(
        name="Rounds",
        value=str(len(btd6_knowledge_service.list_rounds())),
        inline=True,
    )
    return embed


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
    embed.add_field(
        name="Maps",
        value=", ".join(m.canonical for m in btd6_knowledge_service.list_maps()),
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
    return embed


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
    return embed


def build_modes_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🐵 BTD6 — Modes",
        color=discord.Color.green(),
    )
    for mode in btd6_knowledge_service.list_modes():
        embed.add_field(
            name=mode.canonical,
            value=(
                f"Starting cash: {mode.starting_cash} • "
                f"Lives: {mode.starting_lives}"
            ),
            inline=False,
        )
    return embed


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
    "build_modes_embed",
    "build_status_embed",
    "build_test_intent_embed",
    "build_towers_embed",
    "response_to_embed",
]

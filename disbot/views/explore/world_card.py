"""Explore world card — the cross-game identity read surface (spine PR 3).

One read-only card characterizing a player across the whole federated open
world: their **global** game level (the shared progression pool) and each
game's **own** standing (Mining · Crafting · Fishing · …). It is the read
mirror of the world hub (PR 1) — the hub is *where you go*, the card is *who
you are* across those places.

Design (plan §4, PR 3):
- **Read-only, stranger-grade (Q-0080):** no writes, no mutation import, no PII
  beyond the public display name / avatar. Scoped to the invoking user by the
  caller (the command / button is self-only).
- Pure composition over :func:`services.game_xp_service.world_identity` — the
  data layer already keys ``game_xp`` per game and derives the level from the
  shared total, so no new schema and no second progression model.

Plan: ``docs/planning/explore-hub-federated-world-plan-2026-06-19.md`` §4 (PR 3).
"""

from __future__ import annotations

import discord

from services import game_xp_service
from utils.ui_constants import GAME_COLOR

# A short text progress bar for the global level (10 cells). Kept local + tiny
# rather than reaching for a shared helper — the mining bars are durability bars
# with different semantics.
_BAR_CELLS = 10


def _progress_bar(into: int, needed: int) -> str:
    """A 10-cell ``█/░`` bar for ``into``/``needed`` (guards a 0 denominator)."""
    if needed <= 0:
        filled = _BAR_CELLS
    else:
        filled = max(0, min(_BAR_CELLS, round(_BAR_CELLS * into / needed)))
    return "█" * filled + "░" * (_BAR_CELLS - filled)


async def build_world_card_embed(
    user: discord.abc.User,
    guild_id: int | None,
) -> discord.Embed:
    """Compose the read-only cross-game world card for ``user``.

    With no ``guild_id`` (a DM) game progression has no scope, so the card says
    so honestly instead of rendering zeros. Otherwise it shows the global level
    + per-game standings, or a friendly empty state for a player who has not
    earned any game XP yet.
    """
    embed = discord.Embed(
        title=f"🪪 {user.display_name} — world card",
        description=(
            "Who you are across the open world: your shared **world level** and "
            "where you stand in each game."
        ),
        color=GAME_COLOR,
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    if guild_id is None:
        embed.add_field(
            name="Per-server progress",
            value=(
                "Game progress is tracked per server — run this in a server to "
                "see your world card there."
            ),
            inline=False,
        )
        embed.set_footer(text="Only you can see this card.")
        return embed

    identity = await game_xp_service.world_identity(guild_id, user.id)

    if not identity.has_progress:
        embed.add_field(
            name="🌍 World level — 0",
            value=(
                "You have not earned any game XP here yet. Mine, craft, or fish "
                "to start your world ladder — run **`!world`** to pick a place."
            ),
            inline=False,
        )
        embed.set_footer(text="Only you can see this card.")
        return embed

    bar = _progress_bar(identity.global_into, identity.global_needed)
    embed.add_field(
        name=f"🌍 World level — {identity.global_level}",
        value=(
            f"`{bar}`  {identity.global_into:,}/{identity.global_needed:,} XP to "
            f"level {identity.global_level + 1}\n"
            f"*{identity.global_total:,} total XP across every game.*"
        ),
        inline=False,
    )

    lines = [
        f"{s.emoji} **{s.label}** — Lv {s.level} · {s.xp:,} XP"
        for s in identity.per_game
    ]
    embed.add_field(name="Per-game standing", value="\n".join(lines), inline=False)
    embed.set_footer(
        text="Only you can see this card · shared level, separate ladders.",
    )
    return embed


__all__ = ["build_world_card_embed"]

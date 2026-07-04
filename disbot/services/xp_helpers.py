"""Shared XP helpers (S4.2-followup extraction).

These were top-level helpers in ``cogs/xp_cog.py`` consumed by the rank
command, the rank view, the hub panel, and the config panel.  Hosted in
``services/`` (the shared-logic layer) so they live importable by both
the cog and ``views/xp/*`` without ``views`` reaching back into ``cogs``.

Public-ish names (no leading underscore in spirit, but kept consistent
with the historical naming so the diff stays small):

    _STAT_TYPES         — vocabulary accepted by !rank / !leaderboard
    _guild_xp_settings  — tuple shim around get_xp_config (cache-aware)
    _progress_bar       — ascii bar renderer
    _build_rank_embed   — rank card embed builder
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import discord

from utils import db
from utils.guild_config_accessors import get_xp_config
from utils.rank_render import render_rank_card
from utils.ui_constants import UTILITY_COLOR

_STAT_TYPES: set[str] = {"xp", "coins", "both"}

# Filename for the attached rank image card (the `attachment://` embed image).
RANK_CARD_FILENAME = "rank.png"


async def fetch_avatar_png(member: discord.Member) -> bytes | None:
    """Fetch a member's avatar as PNG bytes for the rank card, or ``None``.

    This is the one seam where the otherwise-pure card pipeline touches the
    network: the renderer stays pure (``utils`` takes bytes), and this service
    helper fetches them.  A small static PNG is forced so the Pillow renderer
    always gets a format it can decode without extra codecs.  Any failure
    (network, CDN, unexpected asset) returns ``None`` so the card degrades to
    the initials disc instead of failing the whole ``!rank`` command.
    """
    try:
        asset = member.display_avatar.replace(size=128, static_format="png")
        return await asset.read()
    except Exception:  # noqa: BLE001 — network/asset failure → initials fallback
        return None


async def _guild_xp_settings(guild_id: int) -> tuple[int, int, int]:
    """Return (xp_min, xp_max, cooldown_seconds) for this guild.

    Thin shim around ``guild_config_accessors.get_xp_config`` retained
    for the few callers that want the tuple shape directly.  Cache-aware
    — uses the same F-1 cache as the on_message hot path.
    """
    cfg = await get_xp_config(guild_id)
    return cfg.xp_min, cfg.xp_max, cfg.cooldown


def _progress_bar(current: int, needed: int, width: int = 10) -> str:
    filled = int((current / needed) * width) if needed else width
    return "█" * filled + "░" * (width - filled)


@dataclass(frozen=True)
class RankCardData:
    """One member's rank standing — fetched once, rendered to embed *and* image.

    The single source of truth for the ``!rank`` card so the embed and the
    image card never drift and the DB / rank-registry lookups run a single
    time per render (the leaderboard's fetch-once pattern).
    """

    display_name: str
    avatar_url: str
    xp_rank: int | str
    co_rank: int | str
    level: int
    total_xp: int
    messages: int
    coins: int
    current: int
    needed: int


async def build_rank_card_data(
    member: discord.Member,
    guild: discord.Guild,
) -> RankCardData:
    """Resolve a member's rank standing once.

    Ranks come from the canonical :mod:`services.rank_providers` registry
    (its docstring names this builder as a consumer) — the inline rank SQL
    this function used to carry was the drift the registry exists to kill.
    """
    from services.rank_providers import get_provider

    row = await db.get_xp(member.id, guild.id)
    level, current, needed = db.level_progress(row["xp"])

    async def _rank(provider_name: str) -> int | str:
        provider = get_provider(provider_name)
        if provider is None:  # registry always has xp/coins; stay crash-proof
            return "?"
        position, _ = await provider.member_rank(guild, member.id)
        return position if position is not None else "?"

    return RankCardData(
        display_name=member.display_name,
        avatar_url=member.display_avatar.url,
        xp_rank=await _rank("xp"),
        co_rank=await _rank("coins"),
        level=level,
        total_xp=row["xp"],
        messages=row["messages"],
        coins=row.get("coins", 0),
        current=current,
        needed=needed,
    )


def _rank_embed_from_data(data: RankCardData, stat: str) -> discord.Embed:
    """Build the rank-card embed from already-fetched data (byte-identical to
    the historical inline builder — the embed stays the source of truth and the
    Pillow-less fallback).
    """
    embed = discord.Embed(title=f"📊 {data.display_name}", color=UTILITY_COLOR)
    embed.set_thumbnail(url=data.avatar_url)

    if stat in ("both", "xp"):
        bar = _progress_bar(data.current, data.needed)
        embed.add_field(name="XP Rank", value=f"#{data.xp_rank}", inline=True)
        embed.add_field(name="Level", value=str(data.level), inline=True)
        embed.add_field(name="Total XP", value=str(data.total_xp), inline=True)
        embed.add_field(
            name="Progress",
            value=f"`{bar}` {data.current}/{data.needed} XP",
            inline=False,
        )
        embed.add_field(name="Messages", value=str(data.messages), inline=True)

    if stat in ("both", "coins"):
        embed.add_field(name="Coin Rank", value=f"#{data.co_rank}", inline=True)
        embed.add_field(name="🪙 Coins", value=str(data.coins), inline=True)

    return embed


def _rank_card_stats(data: RankCardData, stat: str) -> list[tuple[str, str]]:
    """The grid panels for the image card — same content as the embed fields."""
    stats: list[tuple[str, str]] = []
    if stat in ("both", "xp"):
        stats.extend(
            [
                ("XP Rank", f"#{data.xp_rank}"),
                ("Level", str(data.level)),
                ("Total XP", str(data.total_xp)),
                ("Messages", str(data.messages)),
            ],
        )
    if stat in ("both", "coins"):
        stats.extend(
            [
                ("Coin Rank", f"#{data.co_rank}"),
                ("Coins", str(data.coins)),
            ],
        )
    return stats


def _render_rank_image(
    data: RankCardData,
    guild: discord.Guild,
    stat: str,
    avatar_png: bytes | None = None,
) -> bytes | None:
    """Render the rank card as a PNG, or ``None`` for the embed-only fallback."""
    progress: tuple[str, float] | None = None
    if stat in ("both", "xp"):
        fraction = (data.current / data.needed) if data.needed else 1.0
        progress = (
            f"Level {data.level} → {data.level + 1} · {data.current}/{data.needed} XP",
            fraction,
        )
    return render_rank_card(
        display_name=data.display_name,
        subtitle=f"{guild.name} · rank",
        stats=_rank_card_stats(data, stat),
        progress=progress,
        avatar_png=avatar_png,
    )


async def _build_rank_embed(
    member: discord.Member,
    guild: discord.Guild,
    stat: str,
) -> discord.Embed:
    """Build the rank-card embed for a member (embed-only; the fetch-once data
    path is :func:`build_rank_response`).
    """
    data = await build_rank_card_data(member, guild)
    return _rank_embed_from_data(data, stat)


async def build_rank_response(
    member: discord.Member,
    guild: discord.Guild,
    stat: str,
) -> tuple[discord.Embed, discord.File | None]:
    """Fetch once and return the rank embed plus an optional image card.

    The image is the showpiece (visual card engine, H3); the embed stays the
    source of truth and the fallback, so a Pillow-less host renders exactly as
    before.  When the image renders, the embed's image is pointed at the
    attachment so Discord shows the card.
    """
    data = await build_rank_card_data(member, guild)
    embed = _rank_embed_from_data(data, stat)
    avatar_png = await fetch_avatar_png(member)
    png = _render_rank_image(data, guild, stat, avatar_png)
    if png is None:
        return embed, None
    embed.set_image(url=f"attachment://{RANK_CARD_FILENAME}")
    return embed, discord.File(io.BytesIO(png), filename=RANK_CARD_FILENAME)

"""Unified guild-resource resolver (Phase D extraction).

Consolidates the fragmented ``guild.get_channel`` / ``get_role`` /
``get_member`` call sites into a single typed surface so:

- missing-resource handling is uniform (return ``None`` instead of
  KeyError / AttributeError on ``int(None)`` casts);
- settings-key → channel-id binding has one helper, not one per cog;
- leaderboards can batch-fetch members instead of doing N individual
  ``guild.get_member`` calls.

This is a **pure-read primitive**. Mutations stay where they belong:

- Channel / category / role *creation* lives in ``utils/channels.py``
  (``safe_channel_name``, ``get_or_create_category``,
  ``create_private_channel``, ``cleanup_category``).
- Audited state mutations (coins, XP, moderation) stay in the
  ``services/`` layer per ``docs/ownership.md``.

Sync vs. async:
    The cache-only resolvers (``resolve_channel``, ``resolve_role``,
    ``resolve_member``, ``resolve_members``, ``member_display``) are
    sync because the underlying discord.py calls are sync.  Functions
    that perform I/O (``ensure_channel`` creates via the Discord API;
    ``resolve_settings_channel`` reads from the DB) are async.

    If a future migration adds ``guild.fetch_member`` fallback on
    cache miss, the affected resolvers will become async — that is a
    breaking change and will get its own ADR.

Public surface:
    resolve_channel(guild, *, channel_id=None, name=None, category=None,
                    kind="text")             → GuildChannel | None
    ensure_channel(guild, name, *, kind="text",
                   category=None, overwrites=None)
                                              → TextChannel | VoiceChannel
    resolve_role(guild, *, role_id=None, name=None) → Role | None
    resolve_member(guild, member_id)          → Member | None
    resolve_members(guild, member_ids)        → dict[int, Member]
    member_display(guild, member_id)          → str
    resolve_settings_channel(guild, setting_key)
                                              → GuildChannel | None
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Literal

import discord

logger = logging.getLogger("bot.runtime.guild_resources")

ChannelKind = Literal["text", "voice", "category", "any"]


# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------


def resolve_channel(
    guild: discord.Guild,
    *,
    channel_id: int | str | None = None,
    name: str | None = None,
    category: str | discord.CategoryChannel | None = None,
    kind: ChannelKind = "text",
) -> discord.abc.GuildChannel | None:
    """Resolve a channel by ID (preferred) or by name with optional filters.

    Behavior:
        - If ``channel_id`` is given, ``guild.get_channel(int(channel_id))``
          is tried first. Returns ``None`` if not in cache or the int cast
          fails.
        - If ``name`` is given (and channel_id missed), the guild is scanned
          for a channel matching name + kind + optional category.
        - If both are given, ``channel_id`` wins on hit.

    The ``category`` filter accepts either the category name (string) or a
    ``CategoryChannel`` instance.

    Returns ``None`` on any miss (cache absent, invalid id, no match).
    """
    if channel_id is not None:
        try:
            cid_int = int(channel_id)
        except (TypeError, ValueError):
            cid_int = None
        if cid_int is not None:
            ch = guild.get_channel(cid_int)
            if ch is not None:
                return ch

    if name is None:
        return None

    if isinstance(category, str):
        cat = discord.utils.get(guild.categories, name=category)
    else:
        cat = category

    candidates: Iterable[discord.abc.GuildChannel]
    if kind == "text":
        candidates = guild.text_channels
    elif kind == "voice":
        candidates = guild.voice_channels
    elif kind == "category":
        candidates = guild.categories
    else:  # "any"
        candidates = guild.channels

    for ch in candidates:
        if ch.name != name:
            continue
        if cat is not None and getattr(ch, "category_id", None) != cat.id:
            continue
        return ch
    return None


async def ensure_channel(
    guild: discord.Guild,
    name: str,
    *,
    kind: Literal["text", "voice"] = "text",
    category: discord.CategoryChannel | None = None,
    overwrites: dict | None = None,
) -> discord.TextChannel | discord.VoiceChannel:
    """Return a channel matching ``name`` + ``kind``, creating it if absent.

    The match is performed via :func:`resolve_channel` with ``kind`` and
    ``category`` filters. If a match is found it is returned unchanged
    (overwrites are NOT reconciled — callers managing permission templates
    should call ``channel.edit`` themselves).

    On miss, the channel is created via ``guild.create_text_channel`` or
    ``guild.create_voice_channel``. ``overwrites`` defaults to empty.
    """
    existing = resolve_channel(guild, name=name, category=category, kind=kind)
    if existing is not None:
        return existing  # type: ignore[return-value]

    if kind == "voice":
        return await guild.create_voice_channel(
            name,
            category=category,
            overwrites=overwrites or {},
        )
    return await guild.create_text_channel(
        name,
        category=category,
        overwrites=overwrites or {},
    )


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


def resolve_role(
    guild: discord.Guild,
    *,
    role_id: int | str | None = None,
    name: str | None = None,
) -> discord.Role | None:
    """Resolve a role by ID (preferred) or exact name.

    ``role_id`` wins on hit. Name match is exact (case-sensitive); for
    normalized lookup use ``views/roles/_helpers.py:_find_role_normalized``.
    """
    if role_id is not None:
        try:
            rid_int = int(role_id)
        except (TypeError, ValueError):
            rid_int = None
        if rid_int is not None:
            role = guild.get_role(rid_int)
            if role is not None:
                return role

    if name is None:
        return None
    return discord.utils.get(guild.roles, name=name)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


def resolve_member(
    guild: discord.Guild,
    member_id: int | str,
) -> discord.Member | None:
    """Cache-only member lookup.

    Returns ``None`` on cache miss or invalid id. Does not fall back to
    ``guild.fetch_member`` (that would be an I/O operation; callers who
    need the slow path can fetch explicitly).
    """
    try:
        mid_int = int(member_id)
    except (TypeError, ValueError):
        return None
    return guild.get_member(mid_int)


def resolve_members(
    guild: discord.Guild,
    member_ids: Iterable[int | str],
) -> dict[int, discord.Member]:
    """Batch cache-only member lookup.

    Returns a dict mapping resolved IDs to ``Member`` objects. Missing or
    invalid IDs are silently dropped — callers iterate over the input
    list and use ``member_display`` for fallback strings.

    Fixes the leaderboard N+1 pattern: one method call instead of N
    individual ``guild.get_member`` calls scattered across an embed
    builder.
    """
    out: dict[int, discord.Member] = {}
    for raw in member_ids:
        try:
            mid_int = int(raw)
        except (TypeError, ValueError):
            continue
        m = guild.get_member(mid_int)
        if m is not None:
            out[mid_int] = m
    return out


def member_display(
    guild: discord.Guild,
    member_id: int | str,
) -> str:
    """Return ``member.display_name`` if cached, else a mention fallback.

    Mirrors the ad-hoc pattern used by leaderboard rendering today:
    ``guild.get_member(id) or f"<@{id}>"`` — but typed and one-call.
    """
    try:
        mid_int = int(member_id)
    except (TypeError, ValueError):
        return f"<@{member_id}>"
    m = guild.get_member(mid_int)
    if m is not None:
        return m.display_name
    return f"<@{mid_int}>"


# ---------------------------------------------------------------------------
# Settings-bound channel resolution
# ---------------------------------------------------------------------------


async def resolve_settings_channel(
    guild: discord.Guild,
    setting_key: str,
) -> discord.abc.GuildChannel | None:
    """Resolve the channel ID stored under ``setting_key`` for ``guild``.

    Reads ``guild_settings(guild_id, setting_key)`` via ``utils.db``, then
    looks the result up via :func:`resolve_channel`. Returns ``None`` if
    the setting is unset, malformed, or points at a channel not in the
    guild cache.

    Replaces the ~6 inline ``cid = await db.get_setting(...);
    bot.get_channel(int(cid))`` patterns scattered across cogs.
    """
    from utils import db

    raw = await db.get_setting(guild.id, setting_key, "")
    if not raw:
        return None
    return resolve_channel(guild, channel_id=raw)

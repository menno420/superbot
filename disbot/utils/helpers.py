from __future__ import annotations

import re

import discord
from discord.ext import commands

# NOTE: ``from core.runtime import resources`` deliberately omitted at
# module scope.  ``core/runtime/__init__.py`` imports
# ``core.runtime.bindings`` (Phase 2b), which imports
# ``core.resources.discovery``, which imports this module for
# :func:`normalize_name`.  A top-level dependency on ``core.runtime``
# here re-enters that partially-initialised package and crashes startup
# with ``ImportError: cannot import name 'resources'``.  Each consumer
# of the resolver primitives imports them locally instead.


def _parse_member(guild: discord.Guild, text: str) -> discord.Member | None:
    """Resolve a member from a mention, ID, or username/display-name string."""
    from core.runtime import guild_resources

    text = text.strip()
    mention_match = re.match(r"<@!?(\d+)>", text)
    if mention_match:
        return guild_resources.resolve_member(guild, mention_match.group(1))
    if text.isdigit():
        return guild_resources.resolve_member(guild, text)
    return discord.utils.find(
        lambda m: m.name == text or m.display_name == text,
        guild.members,
    )


_CUSTOM_EMOJI_RE = re.compile(r"<a?:(\w+):(\d+)>")


def safe_select_emoji(
    value: str | discord.PartialEmoji | None,
) -> str | discord.PartialEmoji | None:
    """Return a valid SelectOption emoji or None if the value cannot be used.

    Handles unicode emoji strings, <:name:id> custom emoji, and PartialEmoji
    objects. Rejects plain ASCII characters that Discord rejects.
    """
    if value is None:
        return None
    if isinstance(value, discord.PartialEmoji):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    stripped = value.strip()
    m = _CUSTOM_EMOJI_RE.match(stripped)
    if m:
        animated = stripped.startswith("<a:")
        return discord.PartialEmoji(
            name=m.group(1),
            id=int(m.group(2)),
            animated=animated,
        )
    # Reject single plain ASCII characters (e.g. "#") — not valid Discord emoji
    if len(stripped) == 1 and ord(stripped) < 128:
        return None
    return stripped


async def post_log_embed(
    bot: commands.Bot,
    guild_id: int,
    embed: discord.Embed,
) -> None:
    """Post an embed to the guild's configured economy_log_channel (if set).

    Read flows through the Phase 2 arbitration helper so the canary
    flip of ``bindings.primary`` is a single change in
    :mod:`core.runtime.config_arbitration`.  This function MUST NOT
    branch on ``is_enabled("bindings.primary", ...)`` directly —
    that is forbidden by the invariant test in PR-7.
    """
    # Local imports preserve the PR #74 cycle-protection pattern:
    # neither core.runtime.* nor core.resources.* lives at module
    # scope in utils.helpers.
    from core.runtime.config_arbitration import get_economy_log_channel

    guild = bot.get_guild(guild_id)
    if guild is None:
        return
    log_channel_result = await get_economy_log_channel(guild_id)
    channel_id = log_channel_result.value
    if channel_id is None:
        return
    ch = guild.get_channel(channel_id)
    if ch is None:
        return
    try:
        await ch.send(embed=embed)  # type: ignore[union-attr]
    except Exception:
        pass


def normalize_name(name: str) -> str:
    """Normalize a name to lowercase with no spaces or underscores for consistent role matching."""
    return name.lower().replace(" ", "").replace("_", "")

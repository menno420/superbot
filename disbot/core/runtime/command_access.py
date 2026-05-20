"""Command-access helpers for fresh-guild bootstrap flows.

The global channel guard in ``bot1.py`` restricts most prefix commands to
``BOT_ALLOWED_CHANNELS``.  That is appropriate for day-to-day command
traffic, but it can strand a newly invited guild: the operator needs a
small, safe set of setup / diagnostics entry points before the guild has
configured channel bindings or command-policy state.

This module owns that exception in one place.  It does not execute command
logic and it does not bypass command-level permission decorators; it only
answers whether the entry-point channel guard may let a bootstrap command
reach the normal discord.py checks.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from discord.ext import commands

BOOTSTRAP_COMMANDS: frozenset[str] = frozenset(
    {
        "admin",
        "adminmenu",
        "check_database",
        "checkdb",
        "diag",
        "diag_status",
        "diagnostic_bot_status",
        "diagnostics",
        "find_command",
        "findcmd",
        "help",
        "latency",
        "list_commands_detailed",
        "listcmds",
        "ping",
        "platform",
        "settings",
        "setup",
        "slashes",
        "slashlist",
        "syncs",
        "syncslash",
        "system_info",
        "sysinfo",
    },
)


def is_bootstrap_command(command_name: str | None) -> bool:
    """Return ``True`` if ``command_name`` is a bootstrap command.

    Accepts both bare names (``"help"``) and qualified group names
    (``"platform identity"``).  The root of a qualified name is checked so
    existing platform/settings/admin subcommands inherit their parent gate.
    """
    if not command_name:
        return False
    normalized = command_name.strip().lower()
    if not normalized:
        return False
    root = normalized.split(maxsplit=1)[0]
    return normalized in BOOTSTRAP_COMMANDS or root in BOOTSTRAP_COMMANDS


def _candidate_command_names(ctx: commands.Context) -> Iterable[str]:
    """Yield every command spelling worth checking for bootstrap access."""
    command = getattr(ctx, "command", None)
    if command is not None:
        name = getattr(command, "name", None)
        if name:
            yield str(name)
        qualified_name = getattr(command, "qualified_name", None)
        if qualified_name:
            yield str(qualified_name)
        for alias in getattr(command, "aliases", ()) or ():
            if alias:
                yield str(alias)
    invoked_with = getattr(ctx, "invoked_with", None)
    if invoked_with:
        yield str(invoked_with)


def _is_guild_operator(author: Any, guild: Any) -> bool:
    """Return whether ``author`` can bootstrap configuration for ``guild``."""
    author_id = getattr(author, "id", None)
    if author_id is not None and author_id == getattr(guild, "owner_id", None):
        return True

    permissions = getattr(author, "guild_permissions", None)
    if permissions is None:
        return False
    return bool(
        getattr(permissions, "administrator", False)
        or getattr(permissions, "manage_guild", False),
    )


async def _is_bot_owner(ctx: commands.Context) -> bool:
    """Best-effort bot-owner check used as an operator escape hatch."""
    bot = getattr(ctx, "bot", None)
    is_owner = getattr(bot, "is_owner", None)
    if not callable(is_owner):
        return False
    try:
        return bool(await is_owner(getattr(ctx, "author", None)))
    except Exception:
        return False


async def can_bypass_channel_guard(ctx: commands.Context) -> bool:
    """Return whether ``ctx`` may bypass the global channel allowlist.

    This is deliberately narrower than command authorization:

    * DMs never bypass; setup is guild-scoped.
    * Non-bootstrap commands never bypass.
    * The guild owner, administrators, members with ``manage_guild``, and
      bot owners may bypass for bootstrap commands only.

    Command-specific decorators such as ``@commands.has_permissions`` still
    run after this check, so this helper does not grant access to the command
    itself.  It only prevents fresh-guild operators from being blocked before
    setup can run.
    """
    guild = getattr(ctx, "guild", None)
    if guild is None:
        return False

    if not any(is_bootstrap_command(name) for name in _candidate_command_names(ctx)):
        return False

    author = getattr(ctx, "author", None)
    if _is_guild_operator(author, guild):
        return True

    return await _is_bot_owner(ctx)


__all__ = [
    "BOOTSTRAP_COMMANDS",
    "can_bypass_channel_guard",
    "is_bootstrap_command",
]

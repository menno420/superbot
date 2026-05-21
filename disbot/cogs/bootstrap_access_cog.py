"""Fresh-guild bootstrap access wiring.

This cog is intentionally loaded first.  It replaces the legacy entry-point
channel guard with the centralized helper from
``core.runtime.command_access`` so setup/help/platform/admin/settings commands
remain reachable for guild operators before a new server has configured bot
channels.

The replacement stays narrow:

* normal commands still require ``BOT_ALLOWED_CHANNELS``;
* ``!force`` remains the explicit admin escape hatch;
* bootstrap bypass only applies to guild owners, administrators,
  ``manage_guild`` members, and bot owners;
* command-level permission decorators still run after this guard.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from discord.ext import commands

import config
from core.runtime.command_access import (
    can_bypass_channel_guard,
    is_bootstrap_command,
)

logger = logging.getLogger("bot.cogs.bootstrap_access")


def _find_channel_guard_checks(bot: commands.Bot) -> list[Any]:
    """Return installed global checks that look like the legacy guard."""
    checks: Iterable[Any] = getattr(bot, "_checks", ())
    return [
        check for check in checks if getattr(check, "__name__", "") == "_channel_guard"
    ]


def _check_is_owned_by_bootstrap_cog(check: Any) -> bool:
    """Return True if ``check`` is a bound method of a
    :class:`BootstrapAccessCog` instance.

    Used by :func:`setup` to recognise a leftover check from a previous
    load that didn't clean up properly.  The shape we look for is a
    bound method (``__self__`` is the cog instance).
    """
    owner = getattr(check, "__self__", None)
    return isinstance(owner, BootstrapAccessCog)


def _is_shutting_down_from_legacy_guard(legacy_guard: Any | None) -> bool:
    """Read ``_shutting_down`` from the original guard's globals, if present."""
    if legacy_guard is None:
        return False
    return bool(getattr(legacy_guard, "__globals__", {}).get("_shutting_down", False))


def _command_name(ctx: commands.Context) -> str | None:
    command = getattr(ctx, "command", None)
    if command is None:
        return getattr(ctx, "invoked_with", None)
    return getattr(command, "qualified_name", None) or getattr(command, "name", None)


class BootstrapAccessCog(commands.Cog):
    """Installs the fresh-guild-aware global channel guard."""

    def __init__(self, bot: commands.Bot, *, legacy_guard: Any | None = None) -> None:
        self.bot = bot
        self._legacy_guard = legacy_guard

    def cog_unload(self) -> None:
        """Remove the global channel guard so a reload doesn't leave a
        duplicate registered on the next ``setup()`` call.

        ``commands.Bot.reload_extension`` calls this hook before
        re-loading the cog.  Without it, the second ``setup()`` would
        register a *second* ``_channel_guard`` check, leading to
        unpredictable command rejection in production guilds (one
        check accepts the command, the other rejects, depending on
        which one fires first).
        """
        try:
            self.bot.remove_check(self._channel_guard)
        except Exception:
            logger.exception(
                "BootstrapAccessCog.cog_unload: failed to remove "
                "channel guard during teardown",
            )

    async def _channel_guard(self, ctx: commands.Context) -> bool:
        if _is_shutting_down_from_legacy_guard(self._legacy_guard):
            return False
        if ctx.guild is None:
            return False
        if ctx.channel.id in config.ALLOWED_CHANNELS:
            return True
        if ctx.command is not None and ctx.command.name == "force":
            return True
        return await can_bypass_channel_guard(ctx)

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """Surface bootstrap permission/usage errors outside allowed channels.

        The entry-point ``bot1.on_command_error`` intentionally suppresses
        user-facing replies outside ``BOT_ALLOWED_CHANNELS``.  Once bootstrap
        commands can bypass that channel guard, operators still need feedback
        for ordinary decorator failures such as ``MissingPermissions`` or a
        bad argument.  Only bootstrap commands outside allowed channels are
        handled here, so normal command channels keep the existing behavior.
        """
        if ctx.guild is None or ctx.channel.id in config.ALLOWED_CHANNELS:
            return
        if not is_bootstrap_command(_command_name(ctx)):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "❌ You do not have permission to use this bootstrap command.",
                delete_after=10,
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                f"❌ I'm missing permissions to do that: `{error.missing_permissions}`",
                delete_after=10,
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"⚠️ Missing argument: `{error.param.name}`. Use `!help {ctx.command}` for usage.",
                delete_after=10,
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"⚠️ Bad argument: {error}", delete_after=10)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏰ This command is on cooldown. Try again in **{error.retry_after:.1f}s**.",
                delete_after=8,
            )


async def setup(bot: commands.Bot) -> None:
    """Replace the legacy channel guard with the fresh-guild-aware version.

    Reload-safe: if a previous BootstrapAccessCog left its check
    installed (e.g. a Discord interaction was running during reload
    and ``cog_unload`` couldn't fire cleanly), the leftover check is
    removed before we install ours.  This stops double-load from
    silently breaking command access in production guilds.
    """
    existing_checks = _find_channel_guard_checks(bot)
    legacy_guards = [
        c for c in existing_checks if not _check_is_owned_by_bootstrap_cog(c)
    ]
    bootstrap_remnants = [
        c for c in existing_checks if _check_is_owned_by_bootstrap_cog(c)
    ]
    legacy_guard = legacy_guards[0] if legacy_guards else None
    for guard in existing_checks:
        bot.remove_check(guard)
    cog = BootstrapAccessCog(bot, legacy_guard=legacy_guard)
    bot.add_check(cog._channel_guard)
    await bot.add_cog(cog)
    logger.info(
        "BootstrapAccessCog loaded; replaced %d legacy guard(s) + "
        "cleaned %d bootstrap remnant(s).",
        len(legacy_guards),
        len(bootstrap_remnants),
    )


__all__ = ["BootstrapAccessCog", "setup"]

"""Prefix-command admission via the central command-access resolver.

This cog owns the single global ``commands.Bot`` check that gates every
prefix command.  Loaded first (see ``INITIAL_EXTENSIONS`` ordering in
``disbot/config.py``) so the gate is installed before any other cog
registers a command.

Pre-PR-4 the gate consulted ``config.ALLOWED_CHANNELS`` (a global env
var with hardcoded fallback IDs) and only special-cased bootstrap
commands.  After PR-4 the gate delegates to
:func:`core.runtime.command_access.resolve_command_access`, which reads
the per-guild DB-backed policy through the cached typed accessor.  The
admin escape hatches (``!force``, bootstrap commands for guild
operators) are preserved — the former is handled inline here, the
latter inside the resolver.

The replacement is intentionally narrow:

* Resolver denial with feedback → post the feedback (delete_after=10)
  before returning ``False`` so the channel-guard CheckFailure does
  not look like a silent crash to the operator (PR-4 fixes the
  "invoked but not completed" UX bug).
* Lifecycle / DM denials are silent — feedback would race the close
  or send into a DM context the operator did not initiate.
* ``!force`` keeps the legacy admin override semantics (the per-
  command ``@commands.has_permissions(administrator=True)`` on the
  ``force`` definition is what makes the override admin-only).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from discord.ext import commands

from core.runtime import command_access

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


class BootstrapAccessCog(commands.Cog):
    """Installs the central command-access guard for prefix commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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
        # !force is the explicit admin channel-restriction bypass.
        # Per-command ``@commands.has_permissions(administrator=True)``
        # on the ``force`` definition is what makes it admin-only; here
        # we only short-circuit the policy check so admins can use the
        # override under ``selected_channels`` / ``disabled`` modes.
        command = getattr(ctx, "command", None)
        if command is not None and getattr(command, "name", None) == "force":
            return True

        access_ctx = await command_access.from_prefix_ctx(ctx)
        decision = await command_access.resolve_command_access(access_ctx)
        if decision.allowed:
            return True

        # Surface the resolver's user-facing feedback before returning
        # False — otherwise the CheckFailure raised by discord.py
        # produces no reply and the operator sees the same "invoked
        # but not completed" silent failure that PR-4 was written to
        # eliminate.  Lifecycle / DM denials carry feedback=None on
        # purpose and stay silent.
        if decision.feedback is not None:
            try:
                await ctx.send(decision.feedback, delete_after=10)
            except Exception:
                logger.debug(
                    "BootstrapAccessCog: failed to send denial feedback "
                    "(guild=%s channel=%s command=%s reason=%s)",
                    access_ctx.guild_id,
                    access_ctx.channel_id,
                    access_ctx.command_name,
                    decision.reason.value,
                )
        # Structured log so denials are observable as intentional
        # decisions rather than vanishing into the "CheckFailure"
        # silence.  Distinct from on_command_error which sees a
        # generic CheckFailure with no context.
        logger.info(
            "command_access deny | guild=%s channel=%s user=%s command=%s "
            "invocation=prefix reason=%s source=%s mode=%s",
            access_ctx.guild_id,
            access_ctx.channel_id,
            access_ctx.user_id,
            access_ctx.command_name,
            decision.reason.value,
            decision.source.value,
            decision.mode.value if decision.mode is not None else None,
        )
        return False


async def setup(bot: commands.Bot) -> None:
    """Install the central command-access guard.

    Reload-safe: if a previous BootstrapAccessCog left its check
    installed (e.g. a Discord interaction was running during reload
    and ``cog_unload`` couldn't fire cleanly), the leftover check is
    removed before we install ours.  This stops double-load from
    silently breaking command access in production guilds.

    Also removes any leftover ``_channel_guard`` check from a previous
    boot — historically the cog had to displace a check defined in
    ``bot1.py``; that definition is gone post-PR-4 but the cleanup
    sweep is retained so a hot-reload from an older codebase still
    settles to a single check.
    """
    existing_checks = _find_channel_guard_checks(bot)
    legacy_count = sum(
        1 for c in existing_checks if not _check_is_owned_by_bootstrap_cog(c)
    )
    remnant_count = len(existing_checks) - legacy_count
    for guard in existing_checks:
        bot.remove_check(guard)
    cog = BootstrapAccessCog(bot)
    bot.add_check(cog._channel_guard)
    await bot.add_cog(cog)
    logger.info(
        "BootstrapAccessCog loaded; replaced %d legacy guard(s) + "
        "cleaned %d bootstrap remnant(s).",
        legacy_count,
        remnant_count,
    )


__all__ = ["BootstrapAccessCog", "setup"]

"""Prefix + slash command admission via the central command-access resolver.

This cog owns the two guards that gate every command:

* ``bot.add_check(self._channel_guard)`` — prefix commands (PR-4).
* ``bot.tree.interaction_check = self._slash_access_check`` — slash
  commands + every other app command discord.py routes through the
  tree (PR-5).

Loaded first (see ``INITIAL_EXTENSIONS`` ordering in
``disbot/config.py``) so both gates are installed before any cog
registers a command.

Both gates delegate to
:func:`core.runtime.command_access.resolve_command_access`, which
reads the per-guild DB-backed policy through the cached typed
accessor.  The admin escape hatches (``!force``, bootstrap commands
for guild operators) are preserved — the prefix-only ``!force``
short-circuit is handled inline here, the bootstrap bypass is inside
the resolver.

Denial feedback is surface-appropriate:

* Prefix: ``ctx.send(decision.feedback, delete_after=10)``.
* Slash: ``interaction.response.send_message(decision.feedback,
  ephemeral=True)`` — only the invoker sees the message and there is
  no channel clutter.

Lifecycle / DM denials carry ``feedback=None`` and stay silent on
both surfaces; surfacing a message under shutdown would race the
connection close.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from discord.ext import commands

from core.runtime import command_access

if TYPE_CHECKING:
    import discord

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


def _interaction_check_owned_by_bootstrap_cog(tree: Any) -> bool:
    """Return True if the tree's interaction_check is a leftover
    bound method on a previous :class:`BootstrapAccessCog` instance.

    A hot-reload leaves the previous cog's bound method on
    ``bot.tree.interaction_check`` because discord.py has no
    cog_unload equivalent for the tree.  :func:`setup` uses this to
    decide whether to overwrite without warning.
    """
    current = getattr(tree, "interaction_check", None)
    if current is None:
        return False
    owner = getattr(current, "__self__", None)
    return isinstance(owner, BootstrapAccessCog)


class BootstrapAccessCog(commands.Cog):
    """Installs the central command-access guards for prefix + slash."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def cog_unload(self) -> None:
        """Remove both gates so a reload doesn't leave duplicates.

        ``commands.Bot.reload_extension`` calls this hook before
        re-loading the cog.  Without it, the second ``setup()`` would
        register a *second* ``_channel_guard`` check, leading to
        unpredictable command rejection in production guilds (one
        check accepts the command, the other rejects, depending on
        which one fires first).

        The slash gate uses a different cleanup discipline because
        ``CommandTree.interaction_check`` is a single attribute rather
        than a list — we restore it to the discord.py default (a
        coroutine that always returns ``True``) only if the current
        value is our own bound method.  Anything else means another
        consumer overwrote it post-load and we leave that consumer's
        value intact.
        """
        try:
            self.bot.remove_check(self._channel_guard)
        except Exception:
            logger.exception(
                "BootstrapAccessCog.cog_unload: failed to remove "
                "channel guard during teardown",
            )
        tree = getattr(self.bot, "tree", None)
        if tree is not None:
            current = getattr(tree, "interaction_check", None)
            if getattr(current, "__self__", None) is self:
                try:
                    # discord.py's CommandTree.interaction_check
                    # default is an instance coroutine that returns
                    # True; we cannot import the unbound original here
                    # without coupling to a private symbol, so set the
                    # attribute to a trivial coroutine that mirrors
                    # that default.
                    tree.interaction_check = _default_interaction_check
                except Exception:
                    logger.exception(
                        "BootstrapAccessCog.cog_unload: failed to "
                        "reset tree.interaction_check during teardown",
                    )

    async def _channel_guard(self, ctx: commands.Context) -> bool:
        # !force is the explicit admin channel-restriction bypass.
        # Per-command ``@admin_or_owner()``
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

    async def _slash_access_check(self, interaction: discord.Interaction) -> bool:
        """Central admission gate for every app command.

        Mirrors ``_channel_guard`` for slash invocations: builds the
        normalized context via the resolver's interaction adapter,
        delegates to ``resolve_command_access``, surfaces ephemeral
        feedback on denial, returns the boolean.

        discord.py raises ``app_commands.CheckFailure`` when this
        returns ``False``; the ephemeral reply has already been sent
        so the invoker sees the policy reason rather than the generic
        "command failed" notice that ``on_app_command_error`` would
        otherwise emit.
        """
        access_ctx = await command_access.from_interaction(interaction)
        decision = await command_access.resolve_command_access(access_ctx)
        if decision.allowed:
            return True

        if decision.feedback is not None:
            try:
                # interaction_check runs BEFORE the handler defers, so
                # ``response.send_message`` is the right entry point
                # (followup would 404 — no initial response yet).
                # ``is_done`` guards the (rare) case where another
                # observer raced ahead of us.
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        decision.feedback,
                        ephemeral=True,
                    )
                else:
                    await interaction.followup.send(
                        decision.feedback,
                        ephemeral=True,
                    )
            except Exception:
                logger.debug(
                    "BootstrapAccessCog: failed to send slash denial "
                    "feedback (guild=%s channel=%s command=%s reason=%s)",
                    access_ctx.guild_id,
                    access_ctx.channel_id,
                    access_ctx.command_name,
                    decision.reason.value,
                )

        logger.info(
            "command_access deny | guild=%s channel=%s user=%s command=%s "
            "invocation=slash reason=%s source=%s mode=%s",
            access_ctx.guild_id,
            access_ctx.channel_id,
            access_ctx.user_id,
            access_ctx.command_name,
            decision.reason.value,
            decision.source.value,
            decision.mode.value if decision.mode is not None else None,
        )
        return False


async def _default_interaction_check(_interaction: discord.Interaction) -> bool:
    """Match discord.py's default ``CommandTree.interaction_check`` shape.

    Defined at module scope so :meth:`BootstrapAccessCog.cog_unload`
    can restore it without re-creating a closure on every unload (the
    closure case would also keep the cog instance alive through the
    bound-method ``__self__`` link).
    """
    return True


async def setup(bot: commands.Bot) -> None:
    """Install the central command-access guards.

    Reload-safe on both surfaces:

    * Prefix: any leftover ``_channel_guard`` check (legacy from a
      pre-PR-4 ``bot1.py`` definition, or a remnant from a previous
      :class:`BootstrapAccessCog` instance that didn't clean up
      cleanly) is removed before installing the new one.
    * Slash: any ``tree.interaction_check`` already owned by a
      previous :class:`BootstrapAccessCog` instance is overwritten
      silently; an unfamiliar value (someone else installed their
      own check) is *also* overwritten, with a WARNING log so the
      conflict is visible.  Leaving an unfamiliar value in place
      would silently bypass policy for every slash command.
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

    tree = getattr(bot, "tree", None)
    tree_overwrite_kind = "none"
    if tree is not None:
        if _interaction_check_owned_by_bootstrap_cog(tree):
            tree_overwrite_kind = "bootstrap_remnant"
        elif getattr(tree, "interaction_check", None) is _default_interaction_check:
            tree_overwrite_kind = "default_post_unload"
        else:
            # Either discord.py's default (an instance coroutine we
            # can't reliably introspect across versions) or some other
            # value.  We unconditionally take ownership because
            # BootstrapAccessCog is loaded first and must be the only
            # gate; a downstream cog that wants to extend admission
            # logic can compose into the resolver rather than
            # overwriting our installed check.
            tree_overwrite_kind = "default_or_unknown"
        tree.interaction_check = cog._slash_access_check

    await bot.add_cog(cog)
    logger.info(
        "BootstrapAccessCog loaded; replaced %d legacy guard(s) + "
        "cleaned %d bootstrap remnant(s); slash tree overwrite=%s.",
        legacy_count,
        remnant_count,
        tree_overwrite_kind,
    )


__all__ = ["BootstrapAccessCog", "setup"]

"""Async webhook reporter — sends structured Discord embed logs to a webhook URL.

Extracted from bot1.py so bot startup logic stays lean and this service can
be tested, replaced, or disabled without touching the entry point.

Every embed is run through :func:`_redact_embed` immediately before
``wh.send`` so secret-looking substrings (Discord tokens, API keys,
``postgres://`` URLs, bearer tokens, emails, secret-bearing URL query
params) are scrubbed before they reach the operator channel.
"""

from __future__ import annotations

import datetime
import logging
import traceback
from typing import TYPE_CHECKING

import aiohttp
import discord

from core.runtime.ai.redaction import redact_text

if TYPE_CHECKING:
    from core.runtime.lifecycle import PendingShutdown

logger = logging.getLogger("bot.webhook")


def _command_counts(bot: object) -> tuple[int, int]:
    """Return (prefix incl. subcommands, slash incl. subcommands), best-effort.

    ``len(bot.commands)`` is only *top-level* prefix commands — it omits group
    subcommands and every slash command (those live in ``bot.tree``). Walking both
    surfaces makes the status embed report the true total. Never raises: a status
    embed must not break startup reporting.
    """
    walk = getattr(bot, "walk_commands", None)
    try:
        prefix = (
            len(list(walk()))
            if callable(walk)
            else len(getattr(bot, "commands", ()) or ())
        )
    except Exception:
        prefix = 0
    slash = 0
    tree_walk = getattr(getattr(bot, "tree", None), "walk_commands", None)
    if callable(tree_walk):
        try:
            slash = len(list(tree_walk()))
        except Exception:
            slash = 0
    return prefix, slash


def _redact_embed(embed: discord.Embed) -> dict[str, int]:
    """Scrub sensitive substrings from text fields of ``embed`` in place.

    Operates on title, description, every field name + value, footer
    text, and author name. Returns aggregate replacement counts so
    callers can observe redactions without re-walking the embed.
    """
    counts: dict[str, int] = {}

    def _scrub(text: str) -> str:
        result = redact_text(text)
        for key, n in result.replacements.items():
            counts[key] = counts.get(key, 0) + n
        return result.value

    if embed.title:
        embed.title = _scrub(embed.title)
    if embed.description:
        embed.description = _scrub(embed.description)
    for index, field in enumerate(embed.fields):
        embed.set_field_at(
            index,
            name=_scrub(field.name) if field.name else field.name,
            value=_scrub(field.value) if field.value else field.value,
            inline=field.inline,
        )
    if embed.footer and embed.footer.text:
        embed.set_footer(
            text=_scrub(embed.footer.text),
            icon_url=embed.footer.icon_url,
        )
    if embed.author and embed.author.name:
        embed.set_author(
            name=_scrub(embed.author.name),
            url=embed.author.url,
            icon_url=embed.author.icon_url,
        )
    return counts


class WebhookReporter:
    """Sends structured Discord embed logs to a webhook URL."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _send(self, embed: discord.Embed, username: str = "Bot Logger") -> None:
        if not self.url or not self._session:
            return
        counts = _redact_embed(embed)
        if counts:
            logger.debug("Webhook embed redacted: %s", counts)
        import time as _time

        from services import metrics as _metrics

        dispatch_started_at = _time.monotonic()
        try:
            wh = discord.Webhook.from_url(self.url, session=self._session)
            await wh.send(embed=embed, username=username)
        except Exception as exc:
            _metrics.webhook_dispatch_seconds.observe(
                _time.monotonic() - dispatch_started_at,
            )
            _metrics.webhook_dispatch_total.labels(outcome="error").inc()
            logger.debug("Webhook send failed: %s", exc)
        else:
            _metrics.webhook_dispatch_seconds.observe(
                _time.monotonic() - dispatch_started_at,
            )
            _metrics.webhook_dispatch_total.labels(outcome="success").inc()

    async def on_startup(self, bot) -> None:
        embed = discord.Embed(
            title="🚀 Bot Online",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(name="Prefix", value=f"`{bot.command_prefix}`", inline=True)
        embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
        prefix_n, slash_n = _command_counts(bot)
        embed.add_field(
            name="Commands",
            value=f"{prefix_n + slash_n} ({prefix_n} prefix · {slash_n} slash)",
            inline=True,
        )
        embed.add_field(name="Loaded cogs", value=str(len(bot.cogs)), inline=True)
        embed.set_footer(text=f"Logged in as {bot.user}")
        await self._send(embed, username="Bot Status")

    async def on_startup_summary(self, outcomes: object) -> None:
        """Deterministic startup-outcome summary (LP-7).

        Posts a single coloured embed listing every recorded startup
        phase with its status and duration, derived purely from the
        in-memory :mod:`core.runtime.startup_outcome` ledger. Called
        from ``main()`` after the catalogue-build phases run but
        before ``await bot.start(...)`` — operators see the boot
        outcome immediately rather than waiting for the Discord
        handshake + ``on_ready`` (which is what :meth:`on_startup`
        used to fire from).

        ``outcomes`` is an iterable of
        :class:`core.runtime.startup_outcome.StartupOutcome`. The
        signature accepts ``object`` so this reporter has no static
        import of the recorder module — the caller (``bot1.py``) owns
        the dependency.
        """
        from core.runtime import startup_outcome as _startup_outcome

        items: tuple = tuple(outcomes)  # type: ignore[arg-type]
        status = _startup_outcome.summary_status(items)
        if status is _startup_outcome.SummaryStatus.OK:
            title = "✅ Startup Summary — OK"
            color = discord.Color.green()
        elif status is _startup_outcome.SummaryStatus.DEGRADED:
            title = "⚠️ Startup Summary — DEGRADED"
            color = discord.Color.gold()
        elif status is _startup_outcome.SummaryStatus.FAILED:
            title = "🛑 Startup Summary — FAILED"
            color = discord.Color.dark_red()
        else:  # EMPTY
            title = "ℹ️ Startup Summary — no outcomes recorded"
            color = discord.Color.greyple()

        if items:
            lines = []
            for outcome in items:
                emoji = "✅" if outcome.success else "❌"
                duration_part = (
                    f" ({outcome.duration_ms:.0f} ms)"
                    if outcome.duration_ms is not None
                    else ""
                )
                error_part = f" — `{outcome.error}`" if outcome.error else ""
                lines.append(
                    f"{emoji} `{outcome.name}`{duration_part}{error_part}",
                )
            description = "\n".join(lines)[:4000]
        else:
            description = (
                "No startup phases recorded — the orchestrator did "
                "not reach the outcome-recording stage. Investigate "
                "the boot logs."
            )

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        successes = sum(1 for o in items if o.success)
        failures = len(items) - successes
        embed.add_field(name="Total", value=str(len(items)), inline=True)
        embed.add_field(name="Succeeded", value=str(successes), inline=True)
        embed.add_field(name="Failed", value=str(failures), inline=True)
        await self._send(embed, username="Bot Startup")

    async def on_identity_findings(
        self,
        summary: dict[str, object],
        *,
        strict: bool,
        aborting: bool,
    ) -> None:
        """Post the identity-contract finding summary (PR I1b).

        Called from ``bot1.py`` at startup when the validator reports any
        findings.  ``aborting`` is True when STRICT mode is on AND the
        summary contains at least one ``fatal``-tier finding — the bot
        will exit shortly after this coroutine returns.
        """
        # ``summary`` is the return value of
        # ``utils.subsystem_registry.summarize_findings`` which produces
        # a dict[str, object]; the by_tier / by_kind values are themselves
        # dicts and total is an int.  Cast at the boundary so mypy sees
        # the runtime shape the helper guarantees.
        by_tier: dict[str, int] = summary.get("by_tier") or {}  # type: ignore[assignment]
        by_kind: dict[str, int] = summary.get("by_kind") or {}  # type: ignore[assignment]
        fatal = int(by_tier.get("fatal", 0))
        auto = int(by_tier.get("auto_healable", 0))
        warn = int(by_tier.get("warn_only", 0))
        total_obj = summary.get("total", 0)
        total = int(total_obj) if isinstance(total_obj, int) else 0
        if aborting:
            title = "🛑 Identity contract — STRICT abort"
            color = discord.Color.dark_red()
        elif fatal:
            title = "🪪 Identity contract — fatal finding(s)"
            color = discord.Color.red()
        else:
            title = "🪪 Identity contract — auto-healable finding(s)"
            color = discord.Color.orange()
        embed = discord.Embed(
            title=title,
            description=(
                f"**total** {total}  ·  **fatal** {fatal}  ·  "
                f"**auto_healable** {auto}  ·  **warn_only** {warn}"
            ),
            color=color,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        if by_kind:
            lines = [f"`{k}` — {v}" for k, v in by_kind.items() if v]
            if lines:
                embed.add_field(
                    name="By kind",
                    value="\n".join(lines)[:1024],
                    inline=False,
                )
        embed.add_field(
            name="STRICT",
            value="on" if strict else "off",
            inline=True,
        )
        embed.add_field(
            name="Action",
            value="aborting startup" if aborting else "continuing",
            inline=True,
        )
        await self._send(embed, username="Identity Contract")

    async def on_cog_fail(self, ext: str, error: Exception) -> None:
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__),
        )
        if len(tb) > 1800:
            tb = tb[-1800:]
        embed = discord.Embed(
            title="🔴 Cog Load Failure",
            description=f"**Extension:** `{ext}`\n```py\n{tb}\n```",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        await self._send(embed, username="Bot Loader")

    async def on_health_startup_failed(self, error: BaseException) -> None:
        """Health-server bind step raised — bot startup is being aborted.

        Phase S2.4 / O-2b: the bot used to silently keep running with
        an unbound health endpoint, leaving orchestration probes wedged.
        This alert fires from bot1.main before SystemExit(1) so the
        operator sees the cause before the container restarts.
        """
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__),
        )
        if len(tb) > 1800:
            tb = tb[-1800:]
        embed = discord.Embed(
            title="🛑 Health Server Bind Failed",
            description=(
                f"**Aborting startup.**  The health server could not "
                f"bind its listener — orchestration probes would have "
                f"wedged silently.\n```py\n{tb}\n```"
            ),
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        await self._send(embed, username="Bot Health")

    async def on_lifecycle_close_beginning(
        self,
        pending: PendingShutdown,
    ) -> None:
        """Posted by the close-driver immediately before ``bot.close()``.

        Operators see one canonical "the bot is about to close" signal
        for both SIGTERM shutdown and ``!restart``.  The caller wraps
        this in best-effort try/except + ``asyncio.wait_for`` so a
        stalled webhook cannot delay ``bot.close()`` and the finalizer.
        """
        is_restart = pending.kind == "restart"
        title = "♻️ Bot Restart Beginning" if is_restart else "🛑 Bot Shutdown Beginning"
        color = discord.Color.gold() if is_restart else discord.Color.red()
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(name="Kind", value=pending.kind, inline=True)
        embed.add_field(
            name="Reason",
            value=pending.reason or "<unknown>",
            inline=True,
        )
        embed.add_field(
            name="Actor",
            value=pending.actor or "<unknown>",
            inline=True,
        )
        await self._send(embed, username="Bot Lifecycle")

    async def on_lifecycle_close_completed(
        self,
        pending: PendingShutdown,
        *,
        duration_seconds: float | None = None,
    ) -> None:
        """Posted by ``main()``'s finalizer after cleanup completes but
        before ``reporter.close()`` tears down the HTTP session.

        Companion to :meth:`on_lifecycle_close_beginning`: operators see
        a paired "starting" / "complete" signal so the gap between them
        — close + finalizer cleanup duration — is visible end-to-end in
        the operator channel without parsing Prometheus.  Caller wraps
        this in ``asyncio.wait_for`` with a small timeout so a stalled
        webhook cannot delay process exit.
        """
        is_restart = pending.kind == "restart"
        title = "♻️ Bot Restart Complete" if is_restart else "🛑 Bot Shutdown Complete"
        color = discord.Color.gold() if is_restart else discord.Color.dark_red()
        embed = discord.Embed(
            title=title,
            color=color,
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(name="Kind", value=pending.kind, inline=True)
        embed.add_field(
            name="Reason",
            value=pending.reason or "<unknown>",
            inline=True,
        )
        embed.add_field(
            name="Actor",
            value=pending.actor or "<unknown>",
            inline=True,
        )
        if duration_seconds is not None:
            embed.add_field(
                name="Close duration",
                value=f"{duration_seconds:.2f}s",
                inline=True,
            )
        await self._send(embed, username="Bot Lifecycle")

    async def on_lifecycle_close_timeout(
        self,
        pending: PendingShutdown,
        *,
        timeout_seconds: float,
    ) -> None:
        """Posted by the close-driver when ``bot.close()`` exceeds the
        configured timeout, immediately before ``os._exit(1)``.

        Operators see this embed instead of the paired "complete" embed
        so a wedged close is unambiguous in the operator channel: the
        bot did not unwind cleanly and the orchestrator is being asked
        to respawn the container.  The caller wraps this in
        ``asyncio.wait_for`` with a small timeout so a stalled webhook
        cannot delay the force-exit further than it already is.
        """
        embed = discord.Embed(
            title="🛑 Bot Close Timeout",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(name="Kind", value=pending.kind, inline=True)
        embed.add_field(
            name="Reason",
            value=pending.reason or "<unknown>",
            inline=True,
        )
        embed.add_field(
            name="Actor",
            value=pending.actor or "<unknown>",
            inline=True,
        )
        embed.add_field(
            name="Timeout",
            value=f"{timeout_seconds:.2f}s",
            inline=True,
        )
        await self._send(embed, username="Bot Lifecycle")

    async def on_app_task_died(self, name: str, error: BaseException) -> None:
        """A supervised application task raised after startup.

        Phase S2.4 / C-2: every task spawned via bot1._supervised_task
        registers a done-callback that posts here on unhandled
        exception, so silent task deaths are visible in the operator
        feed.  Cancellation never triggers this alert.
        """
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__),
        )
        if len(tb) > 1800:
            tb = tb[-1800:]
        embed = discord.Embed(
            title="💀 App Task Died",
            description=(
                f"**Task:** `{name}`\n"
                f"The task exited with an unhandled exception.  The bot "
                f"continues running but this background work is no "
                f"longer happening.\n```py\n{tb}\n```"
            ),
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        await self._send(embed, username="Bot Supervisor")

    async def on_command(self, ctx) -> None:
        embed = discord.Embed(
            title="📥 Command Invoked",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(
            name="Input",
            value=f"`{ctx.message.content[:200]}`",
            inline=False,
        )
        embed.add_field(
            name="User",
            value=f"{ctx.author} (`{ctx.author.id}`)",
            inline=True,
        )
        embed.add_field(name="Channel", value=f"#{ctx.channel}", inline=True)
        embed.add_field(name="Server", value=str(ctx.guild), inline=True)
        cog_name = ctx.cog.qualified_name if ctx.cog else "—"
        embed.set_footer(text=f"Cog: {cog_name}")
        await self._send(embed)

    async def on_command_success(self, ctx) -> None:
        embed = discord.Embed(
            title="✅ Command Completed",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(
            name="Command",
            value=f"`{ctx.command.qualified_name}`",
            inline=True,
        )
        embed.add_field(name="User", value=str(ctx.author), inline=True)
        embed.add_field(name="Server", value=str(ctx.guild), inline=True)
        await self._send(embed)

    async def on_command_error(self, ctx, error) -> None:
        from discord.ext import commands

        if isinstance(error, commands.CheckFailure):
            return

        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="❓ Unknown Command",
                description=f"Input: `{ctx.message.content[:150]}`",
                color=discord.Color.greyple(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            embed.add_field(name="User", value=str(ctx.author), inline=True)
            embed.add_field(name="Server", value=str(ctx.guild), inline=True)
            await self._send(embed)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="⚠️ Missing Argument",
                description=(
                    f"Command `!{ctx.command}` is missing: `{error.param.name}`\n"
                    f"Input: `{ctx.message.content[:150]}`"
                ),
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            embed.add_field(name="User", value=str(ctx.author), inline=True)
            embed.add_field(name="Server", value=str(ctx.guild), inline=True)
            await self._send(embed)
            return

        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="⚠️ Bad Argument",
                description=f"{error}\nInput: `{ctx.message.content[:150]}`",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            embed.add_field(name="User", value=str(ctx.author), inline=True)
            embed.add_field(name="Server", value=str(ctx.guild), inline=True)
            await self._send(embed)
            return

        if isinstance(
            error,
            (commands.MissingPermissions, commands.BotMissingPermissions),
        ):
            label = "User" if isinstance(error, commands.MissingPermissions) else "Bot"
            embed = discord.Embed(
                title=f"🔒 {label} Missing Permissions",
                description=str(error),
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            embed.add_field(name="Command", value=f"`!{ctx.command}`", inline=True)
            embed.add_field(name="User", value=str(ctx.author), inline=True)
            embed.add_field(name="Server", value=str(ctx.guild), inline=True)
            await self._send(embed)
            return

        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"`!{ctx.command}` — retry in **{error.retry_after:.1f}s**",
                color=discord.Color.yellow(),
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
            embed.add_field(name="User", value=str(ctx.author), inline=True)
            embed.add_field(name="Server", value=str(ctx.guild), inline=True)
            await self._send(embed)
            return

        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb = "".join(tb_lines)
        if len(tb) > 1500:
            tb = "...(truncated)\n" + tb[-1500:]

        embed = discord.Embed(
            title="❌ Unexpected Error",
            description=f"**{type(error).__name__}**: {error}\n\n```py\n{tb}\n```",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(
            name="Input",
            value=f"`{ctx.message.content[:150]}`",
            inline=False,
        )
        embed.add_field(name="Command", value=f"`{ctx.command}`", inline=True)
        embed.add_field(
            name="User",
            value=f"{ctx.author} (`{ctx.author.id}`)",
            inline=True,
        )
        embed.add_field(
            name="Channel",
            value=f"#{ctx.channel} in {ctx.guild}",
            inline=True,
        )
        await self._send(embed)

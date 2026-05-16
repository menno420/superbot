"""Async webhook reporter — sends structured Discord embed logs to a webhook URL.

Extracted from bot1.py so bot startup logic stays lean and this service can
be tested, replaced, or disabled without touching the entry point.
"""

from __future__ import annotations

import datetime
import logging
import traceback

import aiohttp
import discord

logger = logging.getLogger("bot.webhook")


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
        try:
            wh = discord.Webhook.from_url(self.url, session=self._session)
            await wh.send(embed=embed, username=username)
        except Exception as exc:
            logger.debug("Webhook send failed: %s", exc)

    async def on_startup(self, bot) -> None:
        embed = discord.Embed(
            title="🚀 Bot Online",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(name="Prefix", value=f"`{bot.command_prefix}`", inline=True)
        embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
        embed.add_field(name="Commands", value=str(len(bot.commands)), inline=True)
        embed.add_field(name="Loaded cogs", value=str(len(bot.cogs)), inline=True)
        embed.set_footer(text=f"Logged in as {bot.user}")
        await self._send(embed, username="Bot Status")

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
        by_tier = summary.get("by_tier", {})
        by_kind = summary.get("by_kind", {})
        fatal = int(by_tier.get("fatal", 0))
        auto = int(by_tier.get("auto_healable", 0))
        warn = int(by_tier.get("warn_only", 0))
        total = int(summary.get("total", 0))
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

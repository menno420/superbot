from __future__ import annotations
import discord
import asyncio
import atexit
import logging
import os
import signal
import json
import traceback
import datetime
import aiohttp
import config
from discord.ext import commands
from utils import db
from utils.synonyms import find_command as _find_synonym

# ---------------------------------------------------------------------------
# Console + file logging  (always active, regardless of webhook)
# ---------------------------------------------------------------------------
_fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
_root = logging.getLogger()
_root.setLevel(logging.INFO)

for _h in (logging.FileHandler("bot.log"), logging.StreamHandler()):
    _h.setFormatter(_fmt)
    _root.addHandler(_h)

logger = logging.getLogger("bot")


# ---------------------------------------------------------------------------
# Async webhook reporter  (rich embeds, one persistent aiohttp session)
# ---------------------------------------------------------------------------
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

    # ------------------------------------------------------------------ events

    async def on_startup(self, bot: commands.Bot) -> None:
        embed = discord.Embed(
            title="🚀 Bot Online",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(name="Prefix", value=f"`{config.PREFIX}`", inline=True)
        embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
        embed.add_field(name="Commands", value=str(len(bot.commands)), inline=True)
        embed.add_field(name="Loaded cogs", value=str(len(bot.cogs)), inline=True)
        embed.set_footer(text=f"Logged in as {bot.user}")
        await self._send(embed, username="Bot Status")

    async def on_cog_fail(self, ext: str, error: Exception) -> None:
        tb = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        if len(tb) > 1800:
            tb = tb[-1800:]
        embed = discord.Embed(
            title="🔴 Cog Load Failure",
            description=f"**Extension:** `{ext}`\n```py\n{tb}\n```",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow(),
        )
        await self._send(embed, username="Bot Loader")

    async def on_command(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="📥 Command Invoked",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(
            name="Input", value=f"`{ctx.message.content[:200]}`", inline=False
        )
        embed.add_field(
            name="User", value=f"{ctx.author} (`{ctx.author.id}`)", inline=True
        )
        embed.add_field(name="Channel", value=f"#{ctx.channel}", inline=True)
        embed.add_field(name="Server", value=str(ctx.guild), inline=True)
        cog_name = ctx.cog.qualified_name if ctx.cog else "—"
        embed.set_footer(text=f"Cog: {cog_name}")
        await self._send(embed)

    async def on_command_success(self, ctx: commands.Context) -> None:
        embed = discord.Embed(
            title="✅ Command Completed",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(
            name="Command", value=f"`{ctx.command.qualified_name}`", inline=True
        )
        embed.add_field(name="User", value=str(ctx.author), inline=True)
        embed.add_field(name="Server", value=str(ctx.guild), inline=True)
        await self._send(embed)

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        # CheckFailure just means the channel-guard fired — not worth logging
        if isinstance(error, commands.CheckFailure):
            return

        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="❓ Unknown Command",
                description=f"Input: `{ctx.message.content[:150]}`",
                color=discord.Color.greyple(),
                timestamp=datetime.datetime.utcnow(),
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
                timestamp=datetime.datetime.utcnow(),
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
                timestamp=datetime.datetime.utcnow(),
            )
            embed.add_field(name="User", value=str(ctx.author), inline=True)
            embed.add_field(name="Server", value=str(ctx.guild), inline=True)
            await self._send(embed)
            return

        if isinstance(
            error, (commands.MissingPermissions, commands.BotMissingPermissions)
        ):
            label = "User" if isinstance(error, commands.MissingPermissions) else "Bot"
            embed = discord.Embed(
                title=f"🔒 {label} Missing Permissions",
                description=str(error),
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow(),
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
                timestamp=datetime.datetime.utcnow(),
            )
            embed.add_field(name="User", value=str(ctx.author), inline=True)
            embed.add_field(name="Server", value=str(ctx.guild), inline=True)
            await self._send(embed)
            return

        # Unexpected / unhandled error — include full traceback
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb = "".join(tb_lines)
        if len(tb) > 1500:
            tb = "...(truncated)\n" + tb[-1500:]

        embed = discord.Embed(
            title="❌ Unexpected Error",
            description=(
                f"**{type(error).__name__}**: {error}\n\n" f"```py\n{tb}\n```"
            ),
            color=discord.Color.red(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(
            name="Input", value=f"`{ctx.message.content[:150]}`", inline=False
        )
        embed.add_field(name="Command", value=f"`{ctx.command}`", inline=True)
        embed.add_field(
            name="User", value=f"{ctx.author} (`{ctx.author.id}`)", inline=True
        )
        embed.add_field(
            name="Channel", value=f"#{ctx.channel} in {ctx.guild}", inline=True
        )
        await self._send(embed)


# ---------------------------------------------------------------------------
# Initialise reporter (session created later inside async context)
# ---------------------------------------------------------------------------
reporter: WebhookReporter | None = (
    WebhookReporter(config.WEBHOOK_URL) if config.WEBHOOK_URL else None
)

if not config.WEBHOOK_URL:
    logger.warning("DISCORD_WEBHOOK_URL not set — webhook logging disabled.")


# ---------------------------------------------------------------------------
# Prevent multiple instances
# ---------------------------------------------------------------------------
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.pid")


def check_existing_instance() -> None:
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            if os.path.exists(f"/proc/{old_pid}"):
                logger.warning("Bot is already running (PID %d). Exiting.", old_pid)
                raise SystemExit(1)
        except (ValueError, FileNotFoundError):
            pass
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def _remove_pid() -> None:
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


check_existing_instance()
atexit.register(_remove_pid)
signal.signal(signal.SIGTERM, lambda *_: _remove_pid())


# ---------------------------------------------------------------------------
# Bot instance
# ---------------------------------------------------------------------------
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    help_command=None,
)

ALLOWED_CHANNELS = config.ALLOWED_CHANNELS

# ---------------------------------------------------------------------------
# Load aliases from localization.json
# ---------------------------------------------------------------------------
LOCALIZATION_PATH = os.path.join(
    os.path.dirname(__file__), "data/json/localization.json"
)


def _load_aliases() -> dict:
    if not os.path.exists(LOCALIZATION_PATH):
        return {}
    try:
        with open(LOCALIZATION_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("en", {}).get("aliases", {})
    except json.JSONDecodeError:
        logger.error("localization.json is corrupted.")
    except Exception as exc:
        logger.error("Failed to load aliases: %s", exc)
    return {}


_aliases = _load_aliases()


# ---------------------------------------------------------------------------
# Bot events
# ---------------------------------------------------------------------------
@bot.event
async def on_ready() -> None:
    bot.uptime = datetime.datetime.utcnow()
    bot._reporter = reporter  # expose so cogs can call reporter directly
    logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    logger.info("Connected to %d server(s)", len(bot.guilds))
    logger.info("Loaded cogs: %s", ", ".join(bot.cogs.keys()))

    for cmd_name, alias_list in _aliases.items():
        cmd = bot.get_command(cmd_name)
        if cmd:
            cmd.aliases = alias_list

    if reporter:
        await reporter.on_startup(bot)


@bot.event
async def on_command(ctx: commands.Context) -> None:
    logger.info(
        "CMD | %s (%s) | #%s | %s | %s",
        ctx.author,
        ctx.author.id,
        ctx.channel,
        ctx.guild,
        ctx.message.content[:150],
    )
    if reporter:
        await reporter.on_command(ctx)


@bot.event
async def on_command_completion(ctx: commands.Context) -> None:
    logger.info(
        "CMD ✅ | %s | %s | %s", ctx.command.qualified_name, ctx.author, ctx.guild
    )
    if reporter:
        await reporter.on_command_success(ctx)


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    # Always log to webhook (reporter filters CheckFailure internally)
    if reporter:
        await reporter.on_command_error(ctx, error)

    # User-facing responses only in allowed channels
    in_allowed = ctx.channel.id in ALLOWED_CHANNELS
    is_force = ctx.command is not None and ctx.command.name == "force"
    if not in_allowed and not is_force:
        return

    if isinstance(error, commands.CheckFailure):
        return  # channel guard — no user message needed

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ You do not have permission to use this command.", delete_after=10
        )

    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(
            f"❌ I'm missing permissions to do that: `{error.missing_permissions}`",
            delete_after=10,
        )

    elif isinstance(error, commands.CommandNotFound):
        raw = ctx.invoked_with or ""
        suggestion = _find_synonym(raw)
        if suggestion:
            await ctx.send(
                f"❓ Unknown command `{raw}`. Did you mean `{config.PREFIX}{suggestion}`?",
                delete_after=15,
            )
        else:
            await ctx.send(
                "❌ Command not found. Use `!help` for available commands.",
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

    else:
        logger.error(
            "CMD ❌ | %s | %s | %s | %s: %s",
            ctx.command,
            ctx.author,
            ctx.guild,
            type(error).__name__,
            error,
            exc_info=True,
        )
        await ctx.send(
            "⚠️ An unexpected error occurred. Please try again.", delete_after=10
        )


# ---------------------------------------------------------------------------
# Global check — restrict commands to allowed channels
# ---------------------------------------------------------------------------
@bot.check
async def _channel_guard(ctx: commands.Context) -> bool:
    return ctx.guild is not None and (
        ctx.channel.id in ALLOWED_CHANNELS
        or (ctx.command is not None and ctx.command.name == "force")
    )


# ---------------------------------------------------------------------------
# !force — admin override
# ---------------------------------------------------------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def force(ctx: commands.Context, command_name: str, *args) -> None:
    """Overrides channel restrictions and runs a command (admins only)."""
    cmd = bot.get_command(command_name)
    if cmd:
        await ctx.invoke(cmd, *args)
    else:
        await ctx.send("❌ Command not found.", delete_after=10)


# ---------------------------------------------------------------------------
# Load cogs
# ---------------------------------------------------------------------------
async def _load_cogs() -> None:
    for ext in config.INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
            logger.info("✅ Loaded %s", ext)
        except Exception as exc:
            logger.error(
                "❌ Failed to load %s: %s: %s",
                ext,
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            if reporter:
                await reporter.on_cog_fail(ext, exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main() -> None:
    await db.init()
    if reporter:
        await reporter.start()
    try:
        async with bot:
            await _load_cogs()
            logger.info("Starting bot...")
            await bot.start(config.DISCORD_BOT_TOKEN)
    finally:
        await db.close()
        if reporter:
            await reporter.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        logger.error("Critical startup error: %s", exc, exc_info=True)

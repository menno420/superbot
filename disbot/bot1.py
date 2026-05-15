from __future__ import annotations

import asyncio
import atexit
import datetime
import logging
import logging.handlers
import os
import signal

import config
import discord
from discord.ext import commands
from services.webhook_reporter import WebhookReporter
from utils import db
from utils.synonyms import find_command as _find_synonym

# ---------------------------------------------------------------------------
# Logging — rotating file (10 MB × 5 backups) + stderr
# ---------------------------------------------------------------------------
_fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
_root = logging.getLogger()
_root.setLevel(logging.INFO)

for _h in (
    logging.handlers.RotatingFileHandler(
        "bot.log", maxBytes=10_000_000, backupCount=5, encoding="utf-8"
    ),
    logging.StreamHandler(),
):
    _h.setFormatter(_fmt)
    _root.addHandler(_h)

logger = logging.getLogger("bot")

# ---------------------------------------------------------------------------
# Webhook reporter
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

# ---------------------------------------------------------------------------
# Bot instance
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    help_command=None,
)

ALLOWED_CHANNELS = config.ALLOWED_CHANNELS

# Set by SIGTERM handler — channel guard rejects new commands during drain.
_shutting_down = False


def _begin_shutdown(*_) -> None:
    global _shutting_down
    _shutting_down = True
    _remove_pid()


signal.signal(signal.SIGTERM, _begin_shutdown)

# ---------------------------------------------------------------------------
# Bot events
# ---------------------------------------------------------------------------


@bot.event
async def on_ready() -> None:
    bot.uptime = datetime.datetime.utcnow()
    bot._reporter = reporter
    logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    logger.info("Connected to %d server(s)", len(bot.guilds))
    logger.info("Loaded cogs: %s", ", ".join(bot.cogs.keys()))
    if reporter:
        await reporter.on_startup(bot)


@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
    from services import governance_service

    governance_service.forget_guild(guild.id)


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
    if reporter:
        await reporter.on_command_error(ctx, error)

    in_allowed = ctx.channel.id in ALLOWED_CHANNELS
    is_force = ctx.command is not None and ctx.command.name == "force"
    if not in_allowed and not is_force:
        return

    if isinstance(error, commands.CheckFailure):
        return

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
# Global check — restrict commands to allowed channels; block during shutdown
# ---------------------------------------------------------------------------


@bot.check
async def _channel_guard(ctx: commands.Context) -> bool:
    if _shutting_down:
        return False
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
    from services import governance_service
    from utils.subsystem_registry import SUBSYSTEMS

    failed_exts: set[str] = set()
    for ext in config.INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
            logger.info("✅ Loaded %s", ext)
        except Exception as exc:
            failed_exts.add(ext)
            logger.error(
                "❌ Failed to load %s: %s: %s",
                ext,
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            if reporter:
                await reporter.on_cog_fail(ext, exc)

    if failed_exts:
        loaded_command_names = {cmd.name for cmd in bot.commands}
        failed_subsystems: set[str] = set()
        for name, meta in SUBSYSTEMS.items():
            entry_points = meta.get("entry_points", [])
            if entry_points and not any(ep in loaded_command_names for ep in entry_points):
                failed_subsystems.add(name)
                logger.warning(
                    "Subsystem %r has no loaded commands — marking INTERNAL", name
                )
        if failed_subsystems:
            governance_service.register_failed_subsystems(failed_subsystems)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    from services.governance_exceptions import GovernanceError
    from utils.subsystem_registry import validate_registry

    try:
        validate_registry()
        logger.info("Registry validated and frozen.")
    except GovernanceError as exc:
        logger.critical("Registry validation failed — aborting startup: %s", exc)
        raise SystemExit(1) from exc

    await db.init()
    if reporter:
        await reporter.start()
    health_task: asyncio.Task | None = None
    try:
        async with bot:
            from healthserver import start_health_server

            health_task = asyncio.create_task(start_health_server(bot))
            await _load_cogs()
            logger.info("Starting bot...")
            await bot.start(config.DISCORD_BOT_TOKEN)
    finally:
        if health_task and not health_task.done():
            health_task.cancel()
        # Graceful drain: allow up to 5 s for in-flight coroutines to finish.
        if _shutting_down:
            pending = {t for t in asyncio.all_tasks() if not t.done()}
            pending.discard(asyncio.current_task())
            if pending:
                _, still_pending = await asyncio.wait(pending, timeout=5.0)
                for t in still_pending:
                    t.cancel()
        await db.close()
        if reporter:
            await reporter.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        logger.error("Critical startup error: %s", exc, exc_info=True)

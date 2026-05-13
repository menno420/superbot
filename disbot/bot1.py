from __future__ import annotations
import discord
import asyncio
import logging
import os
import json
import datetime
import urllib.request
import aiohttp
import config  # Ensure config.py exists and contains PREFIX & DISCORD_BOT_TOKEN
from discord.ext import commands

# ==========================
# Webhook Log Handler
# ==========================
class WebhookLogHandler(logging.Handler):
    """Forwards log records to a Discord webhook synchronously."""

    ICONS = {"DEBUG": "🔍", "INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🚨"}

    def __init__(self, url: str):
        super().__init__(level=logging.INFO)
        self.url = url
        self.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(message)s", datefmt="%H:%M:%S"))

    def emit(self, record: logging.LogRecord):
        if not self.url:
            return
        try:
            msg = self.format(record)
            if len(msg) > 1900:
                msg = msg[:1900] + "…"
            icon = self.ICONS.get(record.levelname, "ℹ️")
            payload = json.dumps({
                "content": f"{icon} `[{record.levelname}]` {msg}",
                "username": "Bot Logger",
            }).encode()
            req = urllib.request.Request(
                self.url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

# ==========================
# Logging Setup
# ==========================
_webhook_handler: WebhookLogHandler | None = None

_fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
_root = logging.getLogger()
_root.setLevel(logging.INFO)

for _h in (logging.FileHandler("bot.log"), logging.StreamHandler()):
    _h.setFormatter(_fmt)
    _root.addHandler(_h)

if config.WEBHOOK_URL:
    _webhook_handler = WebhookLogHandler(config.WEBHOOK_URL)
    _root.addHandler(_webhook_handler)

logger = logging.getLogger("bot")

# ==========================
# Prevent Multiple Instances
# ==========================
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.pid")

def check_existing_instance():
    """ Prevents multiple instances of the bot from running. """
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if os.path.exists(f"/proc/{old_pid}"):
                logger.warning("⚠️ Bot is already running. Exiting...")
                exit(1)
        except (ValueError, FileNotFoundError):
            pass  # Handle corrupt or missing PID file

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

check_existing_instance()

# ==========================
# Bot Configuration
# ==========================
intents = discord.Intents.all()
intents.message_content = True  # Ensure message content intent is enabled
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents, help_command=None)  # Disable default help command

# Define allowed command channels (Only these two)
ALLOWED_CHANNELS = {1348795460948590622, 1403818013408624642}

# ==========================
# Load Aliases from localization.json
# ==========================
LOCALIZATION_PATH = os.path.join(os.path.dirname(__file__), "data/json/localization.json")

def load_aliases():
    """Loads command aliases from localization.json."""
    if not os.path.exists(LOCALIZATION_PATH):
        return {}

    try:
        with open(LOCALIZATION_PATH, "r", encoding="utf-8") as file:
            localization_data = json.load(file)
        return localization_data.get("en", {}).get("aliases", {})
    except json.JSONDecodeError:
        logger.error("❌ Error: localization.json is corrupted. Fix it before restarting the bot.")
    except Exception as e:
        logger.error(f"❌ Unexpected error while loading aliases: {e}")
    return {}

aliases = load_aliases()

@bot.event
async def on_ready():
    bot.uptime = datetime.datetime.utcnow()
    bot._webhook_handler = _webhook_handler  # expose to cogs for !loglevel
    logger.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"🔗 Connected to {len(bot.guilds)} servers")
    logger.info("🚀 Bot is ready!")

    for command_name, alias_list in aliases.items():
        cmd = bot.get_command(command_name)
        if cmd:
            cmd.aliases = alias_list
            logger.info(f"🔄 Loaded aliases for {command_name}: {alias_list}")

    await _send_startup_message()

@bot.event
async def on_command(ctx):
    logger.info(f"CMD | {ctx.author} | #{ctx.channel} | {ctx.message.content[:150]}")

@bot.event
async def on_command_completion(ctx):
    logger.info(f"CMD ✅ | {ctx.command.qualified_name} completed for {ctx.author}")

async def _send_startup_message():
    if not config.WEBHOOK_URL:
        return
    try:
        prefix = config.PREFIX
        embed = discord.Embed(
            title="🚀 Bot is Online",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(name="Prefix", value=f"`{prefix}` — e.g. `{prefix}help`, `{prefix}cog`", inline=False)
        embed.add_field(name="Servers", value=str(len(bot.guilds)), inline=True)
        embed.add_field(name="Commands", value=str(len(bot.commands)), inline=True)
        embed.add_field(name="Loaded Cogs", value=str(len(bot.cogs)), inline=True)
        embed.set_footer(text=f"Logged in as {bot.user}")

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(config.WEBHOOK_URL, session=session)
            await webhook.send(embed=embed, username="Bot Status")
    except Exception as e:
        logger.error(f"Failed to send startup webhook: {e}")

# ==========================
# Restrict Commands to Specific Channels
# ==========================
@bot.check
async def globally_block_dms(ctx):
    """ Ensure commands are only executed in allowed channels without any feedback if not allowed, except for force command. """
    return ctx.guild is not None and (ctx.channel.id in ALLOWED_CHANNELS or (ctx.command is not None and ctx.command.name == "force"))

# ==========================
# Force Command Override (Admins Only)
# ==========================
@bot.command()
@commands.has_permissions(administrator=True)
async def force(ctx, command_name: str, *args):
    """ Overrides channel restrictions and forces a command execution (Admins only). """
    command = bot.get_command(command_name)
    if command:
        await ctx.invoke(command, *args)
    else:
        await ctx.send("❌ Command not found.", delete_after=10)

# ==========================
# Event: Command Error Handling
# ==========================
@bot.event
async def on_command_error(ctx, error):
    if ctx.channel.id not in ALLOWED_CHANNELS and (ctx.command is None or ctx.command.name != "force"):
        return  # Ignore errors for unauthorized channels unless using force

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.", delete_after=10)
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help` for available commands.", delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing argument. Check `!help` for usage.", delete_after=10)
    else:
        logger.error(f"CMD ❌ | {ctx.command} | {ctx.author} | {type(error).__name__}: {error}", exc_info=True)
        await ctx.send("⚠️ An unexpected error occurred. Please try again later.", delete_after=10)

# ==========================
# Load Cogs (Extensions)
# ==========================
async def load_cogs():
    for ext in config.INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
            logger.info(f"✅ Successfully loaded {ext}")
        except Exception as e:
            msg = f"❌ Failed to load `{ext}`: {type(e).__name__}: {e}"
            logger.error(msg, exc_info=True)
            # Post directly to webhook in case logging pipeline isn't working
            if config.WEBHOOK_URL:
                try:
                    async with aiohttp.ClientSession() as session:
                        wh = discord.Webhook.from_url(config.WEBHOOK_URL, session=session)
                        await wh.send(f"🔴 **Cog load failure**\n```{msg}```", username="Bot Loader")
                except Exception:
                    pass

# ==========================
# Bot Startup
# ==========================
async def main():
    async with bot:
        await load_cogs()
        logger.info("🚀 Starting bot...")
        await bot.start(config.DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}", exc_info=True)

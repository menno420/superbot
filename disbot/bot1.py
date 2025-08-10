import discord
import asyncio
import logging
import os
import json
import config  # Ensure config.py exists and contains PREFIX & DISCORD_BOT_TOKEN
from discord.ext import commands

# ==========================
# Logging Setup
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Logs to file
        logging.StreamHandler()  # Logs to console
    ]
)

logger = logging.getLogger("bot")

# ==========================
# Prevent Multiple Instances
# ==========================
PID_FILE = "bot.pid"

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
ALLOWED_CHANNELS = {1348795460948590622}

# ==========================
# Load Aliases from localization.json
# ==========================
LOCALIZATION_PATH = "/home/menno/disbot/data/json/localization.json"

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
    logger.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info(f"🔗 Connected to {len(bot.guilds)} servers")
    logger.info("🚀 Bot is ready!")

    for command_name, alias_list in aliases.items():
        cmd = bot.get_command(command_name)
        if cmd:
            cmd.aliases = alias_list
            logger.info(f"🔄 Loaded aliases for {command_name}: {alias_list}")

# ==========================
# Restrict Commands to Specific Channels
# ==========================
@bot.check
async def globally_block_dms(ctx):
    """ Ensure commands are only executed in allowed channels without any feedback if not allowed, except for force command. """
    return ctx.guild is not None and (ctx.channel.id in ALLOWED_CHANNELS or ctx.command.name == "force")

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
    if ctx.channel.id not in ALLOWED_CHANNELS and ctx.command.name != "force":
        return  # Ignore errors for unauthorized channels unless using force

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have permission to use this command.", delete_after=10)
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help` for available commands.", delete_after=10)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing argument. Check `!help` for usage.", delete_after=10)
    else:
        logger.error(f"⚠️ Unhandled error: {error}", exc_info=True)
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
            logger.error(f"❌ Failed to load {ext}: {e}", exc_info=True)

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
    except RuntimeError:  # Handles event loop issues on some environments
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}", exc_info=True)
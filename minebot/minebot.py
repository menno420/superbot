# minebot.py
import discord
from discord.ext import commands
from config import Config
from utils.logging import setup_logging, init_log_session, close_logging, log_info, log_error
from utils.error_handling import setup_global_error_handler
from utils.data_manager import DatabaseManager
import asyncio

setup_logging()  # Sets up file/console logging (no aiohttp session yet)

intents = discord.Intents.all()
bot_prefixes = tuple(prefix.strip() for prefix in Config.COMMAND_PREFIXES)

bot = commands.Bot(
    command_prefix=bot_prefixes,
    intents=intents,
    help_command=None,
    owner_id=Config.BOT_OWNER_ID
)

async def load_initial_cogs():
    for cog in Config.INITIAL_COGS:
        try:
            await bot.load_extension(cog)
            log_info(f"✅ Loaded cog: {cog}")
        except Exception as e:
            log_error(f"❌ Failed to load cog '{cog}': {e}")

@bot.event
async def on_ready():
    await bot.wait_until_ready()

    try:
        await init_log_session()  # ✅ Init aiohttp logging session here
        log_info("📡 Logging webhook session initialized.")
    except Exception as e:
        print(f"[LOGGING INIT ERROR] {e}")

    try:
        synced = await bot.tree.sync()
        log_info(f"✅ Synced {len(synced)} application (slash) commands.")
    except Exception as e:
        log_error(f"❌ Failed to sync slash commands: {e}")

    log_info(f"🤖 Bot is online as {bot.user} (ID: {bot.user.id})")
    log_info(f"Active prefixes: {bot_prefixes}")

setup_global_error_handler(bot)

async def main():
    try:
        await DatabaseManager.initialize()
        async with bot:
            await load_initial_cogs()
            await bot.start(Config.BOT_TOKEN)
    finally:
        await close_logging()  # ✅ Properly close aiohttp session

if __name__ == "__main__":
    asyncio.run(main())

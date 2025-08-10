# config.py (corrected version)
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Token & API Keys
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "your-discord-user-id"))

    if not BOT_TOKEN:
        raise ValueError("Missing BOT_TOKEN in .env")

    # Command Prefixes (Fixed here!)
    COMMAND_PREFIXES = tuple(prefix.strip() for prefix in os.getenv("BOT_PREFIXES", "!,pls").split(","))

    # Channels
    ALLOWED_CHANNELS = {int(ch) for ch in os.getenv("ALLOWED_CHANNELS", "").split(",") if ch}

    # Debug & Logging
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    ERROR_LOG_WEBHOOK = os.getenv("ERROR_LOG_WEBHOOK")
    ACTIVITY_LOG_WEBHOOK = os.getenv("ACTIVITY_LOG_WEBHOOK")

    # Directories (Absolute Paths)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    HELPERS_DIR = os.path.join(BASE_DIR, "helpers")
    UTILS_DIR = os.path.join(BASE_DIR, "utils")
    COGS_DIR = os.path.join(BASE_DIR, "cogs")
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    DATA_DIR = os.path.join(BASE_DIR, "data")

    # Database
    DB_FILE = os.path.join(DATA_DIR, "minebot.db")

    # JSON Data
    ITEM_STATS_FILE = os.path.join(DATA_DIR, "item_stats.json")
    ITEM_ALIASES_FILE = os.path.join(DATA_DIR, "item_aliases.json")
    RECIPES_FILE = os.path.join(DATA_DIR, "recipes.json")

    # Initial cogs to load at startup
    INITIAL_COGS = [
        "cogs.help_cog",
        "cogs.admin_cog",
        "cogs.data_admin_cog",
        "cogs.inventory_cog",
        "cogs.botstats_cog",
        "cogs.mining_cog",
        "cogs.crafting_cog",
        "cogs.tools_cog",
        "cogs.debug_cog",
    ]

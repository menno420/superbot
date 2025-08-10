# config.py - Clean and optimized version
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ==========================
# Discord Bot Token
# ==========================
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN_PRODUCTION")

# Ensure the token is properly loaded
if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN.strip() == "":
    raise ValueError("ERROR: DISCORD_BOT_TOKEN is missing or empty!")

# ==========================
# Bot Prefix
# ==========================
PREFIX = os.getenv("BOT_PREFIX", "!")

# ==========================
# Initial Cogs (Extensions)
# ==========================
INITIAL_EXTENSIONS = [
    "cogs.admin_cog",
    "cogs.help_cog",
    "cogs.role_cog",
    "cogs.moderation_cog",
    "cogs.German_cog",
    "cogs.utility_cog",
    "cogs.cleanup_cog",

]

# ==========================
# Logging Level
# ==========================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ==========================
# Print Configuration (Optional Debugging)
# ==========================
print(f"Bot is starting with prefix: '{PREFIX}'")
print(f"Loaded Cogs: {INITIAL_EXTENSIONS}")
print(f"Logging level set to: {LOG_LEVEL}")
print(f"Token type: {type(DISCORD_BOT_TOKEN)}, Length: {len(DISCORD_BOT_TOKEN)}")
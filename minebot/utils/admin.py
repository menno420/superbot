# utils/admin.py
import os
import sys
import json
import importlib
from config import Config
from utils.logging import log_info, log_error

# ---- Bot Restart ---- #
async def restart_bot(bot):
    """Safely restarts the bot process."""
    try:
        log_info("Attempting to restart the bot...")
        await bot.close()
        python = sys.executable
        os.execv(python, [python] + sys.argv)
    except Exception as e:
        log_error(f"Failed to restart bot: {e}")
        raise

# ---- Cog Management ---- #
async def load_cog(bot, cog: str):
    """Dynamically loads a cog."""
    try:
        await bot.load_extension(cog)
        log_info(f"✅ Loaded cog: {cog}")
    except Exception as e:
        log_error(f"❌ Failed to load cog {cog}: {e}")
        raise

async def unload_cog(bot, cog: str):
    """Dynamically unloads a cog."""
    try:
        await bot.unload_extension(cog)
        log_info(f"🗑️ Unloaded cog: {cog}")
    except Exception as e:
        log_error(f"❌ Failed to unload cog {cog}: {e}")
        raise

async def reload_cog(bot, cog: str):
    """Dynamically reloads a cog."""
    try:
        await bot.reload_extension(cog)
        log_info(f"🔄 Reloaded cog: {cog}")
    except Exception as e:
        log_error(f"❌ Failed to reload cog {cog}: {e}")
        raise

async def reload_all_cogs(bot, cogs: list):
    """Reloads all cogs."""
    for cog in cogs:
        await reload_cog(bot, cog)

# ---- JSON Data Management ---- #
def reload_json_files():
    """Dynamically reloads JSON data files."""
    data_files = {
        "item_stats": Config.ITEM_STATS_FILE,
        "item_aliases": Config.ITEM_ALIASES_FILE,
        "recipes": Config.RECIPES_FILE,
    }
    loaded_data = {}
    for key, path in data_files.items():
        try:
            with open(path, "r") as f:
                loaded_data[key] = json.load(f)
            log_info(f"📁 Reloaded JSON: {key}")
        except Exception as e:
            log_error(f"Failed to reload JSON file '{path}': {e}")
    return loaded_data

# ---- Helpers & Utils Reloading ---- #
def reload_modules():
    """Dynamically reloads all modules in helpers and utils directories."""
    reloaded_modules = []
    for directory in [Config.HELPERS_DIR, Config.UTILS_DIR]:
        for filename in os.listdir(directory):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                module_path = f"{os.path.basename(directory)}.{module_name}"
                try:
                    module = sys.modules.get(module_path)
                    if module:
                        importlib.reload(module)
                        log_info(f"🔁 Reloaded module: {module_path}")
                    else:
                        importlib.import_module(module_path)
                        log_info(f"📦 Imported new module: {module_path}")
                    reloaded_modules.append(module_path)
                except Exception as e:
                    log_error(f"Failed to reload module {module_path}: {e}")
    return reloaded_modules

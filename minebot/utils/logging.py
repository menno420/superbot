# utils/logging.py
import logging
import asyncio
import aiohttp
from config import Config

session: aiohttp.ClientSession = None

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
        format="[%(asctime)s] [%(levelname)s]: %(message)s",
        handlers=[
            logging.FileHandler(f"{Config.DATA_DIR}/bot.log"),
            logging.StreamHandler()
        ]
    )
    log_info("Logging initialized.")

async def init_log_session():
    """Call this from within an async context (like on_ready)."""
    global session
    if session is None:
        session = aiohttp.ClientSession()

def log_info(message):
    logging.info(message)
    _schedule_discord_log(message, "info")

def log_warning(message):
    logging.warning(message)
    _schedule_discord_log(f"⚠️ {message}", "warn")

def log_error(message):
    logging.error(message)
    _schedule_discord_log(f"❌ {message}", "error")

def _schedule_discord_log(message: str, level: str):
    # Only schedule if there's an active loop
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_discord_log(message, level))
    except RuntimeError:
        pass  # No loop running (likely during early startup)

async def _send_discord_log(message: str, level: str):
    if getattr(Config, "DEBUG", "False") == "True":
        return

    if session is None:
        return

    webhook_url = Config.ERROR_LOG_WEBHOOK if level == "error" else Config.ACTIVITY_LOG_WEBHOOK
    if not webhook_url:
        return

    try:
        async with session.post(webhook_url, json={"content": message}, timeout=5) as resp:
            if resp.status >= 400:
                print(f"[LOGGING ERROR] Failed to post to webhook ({resp.status})")
    except Exception as e:
        print(f"[LOGGING ERROR] {e}")

async def close_logging():
    global session
    if session:
        await session.close()
        session = None

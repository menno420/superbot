"""Minimal HTTP health server for container orchestration probes.

Exposes two endpoints on 0.0.0.0:8080 (configurable via HEALTH_PORT env var):

  GET /health  — liveness probe; returns 200 while the event loop is running
  GET /ready   — readiness probe; returns 200 once the bot is logged in to Discord,
                 503 while still connecting

The server runs as a background asyncio task alongside the bot, sharing the
same event loop. It adds no threads and has negligible overhead.

Usage (from bot1.py main()):
    from healthserver import start_health_server
    health_task = asyncio.create_task(start_health_server(bot))
    ...
    health_task.cancel()
"""

from __future__ import annotations

import datetime
import json
import logging
import os

from aiohttp import web
from discord.ext import commands

logger = logging.getLogger("bot.health")

_HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8080"))


async def _health_handler(request: web.Request) -> web.Response:
    """Liveness probe — always 200 while the event loop is alive."""
    bot: commands.Bot = request.app["bot"]
    uptime = (
        str(datetime.datetime.utcnow() - bot.uptime)
        if hasattr(bot, "uptime")
        else "starting"
    )
    body = json.dumps(
        {
            "status": "ok",
            "uptime": uptime,
            "guilds": len(bot.guilds),
            "latency_ms": round(bot.latency * 1000, 1),
        }
    )
    return web.Response(text=body, content_type="application/json")


async def _ready_handler(request: web.Request) -> web.Response:
    """Readiness probe — 503 until Discord gateway connection is established."""
    bot: commands.Bot = request.app["bot"]
    if bot.is_ready():
        body = json.dumps({"status": "ready", "user": str(bot.user)})
        return web.Response(text=body, content_type="application/json")
    return web.Response(
        text=json.dumps({"status": "not_ready"}),
        status=503,
        content_type="application/json",
    )


async def start_health_server(bot: commands.Bot) -> None:
    """Start the aiohttp health server and block until cancelled."""
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/health", _health_handler)
    app.router.add_get("/ready", _ready_handler)

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", _HEALTH_PORT)
    await site.start()
    logger.info("Health server listening on 0.0.0.0:%d", _HEALTH_PORT)

    try:
        # Keep running until the task is cancelled (bot shutdown).
        import asyncio

        await asyncio.get_running_loop().create_future()
    finally:
        await runner.cleanup()

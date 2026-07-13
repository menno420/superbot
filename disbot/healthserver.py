"""Minimal HTTP health server for container orchestration probes.

Exposes these endpoints on ``[::]:8080`` — IPv6 dual-stack so Railway private
networking can reach it (host/port via HEALTH_HOST / HEALTH_PORT):

  GET /health     — liveness probe; returns 200 while the event loop is running
  GET /ready      — readiness probe; returns 200 only when the bot is logged in
                    to Discord AND the lifecycle service is admitting commands.
                    Returns 503 during STARTING (gateway not connected yet) or
                    any draining/terminal phase (DRAINING, SHUTTING_DOWN,
                    RESTARTING, STOPPED) so the orchestrator routes traffic
                    away during graceful shutdown / restart.
  GET /lifecycle  — diagnostic dump of the full lifecycle snapshot (phase,
                    pending request, recent events).  Always returns 200 with
                    the snapshot JSON.  Operators ``curl`` this during an
                    incident when the bot is unresponsive in Discord but the
                    HTTP server is still serving.

The server runs as a background asyncio task alongside the bot, sharing the
same event loop. It adds no threads and has negligible overhead.

Usage (from bot1.py main()):
    from healthserver import start_health_server
    bind_ready = asyncio.Event()
    health_task = supervised_task(
        start_health_server(bot, ready_event=bind_ready),
        name="health_server",
    )
    # main() waits on bind_ready before bot.start() so a bind failure
    # fails the process fast rather than running an undiscoverable bot
    # behind a wedged orchestration probe (Phase S2.4 / O-2b).

If the bind step (runner.setup / site.start) raises, the exception now
propagates with cleanup, instead of escaping the task silently.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os

from aiohttp import web
from discord.ext import commands

from core.runtime import lifecycle

try:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"

    def generate_latest() -> bytes:  # type: ignore[misc]
        return b"# prometheus_client not installed\n"


logger = logging.getLogger("bot.health")

_HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8080"))
# Bind IPv6 dual-stack (``::``) by default so the server is reachable over
# Railway's **private network** (IPv6-only) — e.g. the dashboard control panel
# reaching the control API at ``worker.railway.internal:8080``. On Linux ``::``
# also accepts IPv4-mapped connections, so IPv4/local health checks keep working.
# Kill-switch: set ``HEALTH_HOST=0.0.0.0`` if a runtime ever lacks IPv6.
_HEALTH_HOST = os.environ.get("HEALTH_HOST", "::")


async def _health_handler(request: web.Request) -> web.Response:
    """Liveness probe — always 200 while the event loop is alive."""
    bot: commands.Bot = request.app["bot"]
    uptime = (
        str(datetime.datetime.now(tz=datetime.timezone.utc) - bot.uptime)
        if hasattr(bot, "uptime")
        else "starting"
    )
    body = json.dumps(
        {
            "status": "ok",
            "uptime": uptime,
            "guilds": len(bot.guilds),
            "latency_ms": round(bot.latency * 1000, 1),
        },
    )
    return web.Response(text=body, content_type="application/json")


async def _ready_handler(request: web.Request) -> web.Response:
    """Readiness probe — 200 only when the bot is fully serving traffic.

    Returns 200 when both:
      - ``bot.is_ready()`` — Discord gateway handshake is complete
      - ``lifecycle.can_accept_commands()`` — the lifecycle service is
        in ``STARTING`` or ``RUNNING`` (i.e., not draining)

    Returns 503 in every other case.  The payload always includes the
    lifecycle ``phase`` and ``accepting_commands`` so the orchestrator
    can distinguish "still connecting" from "draining for shutdown"
    when alerting or routing traffic.

    The lifecycle gate matters during graceful shutdown: SIGTERM moves
    the bot into ``DRAINING`` before ``bot.close()`` is awaited, and
    ``bot.is_ready()`` stays True for some of that window.  Without
    the lifecycle check, the orchestrator would keep routing traffic
    to a draining replica.
    """
    bot: commands.Bot = request.app["bot"]
    phase = lifecycle.get_phase()
    accepting = lifecycle.can_accept_commands()
    is_ready = bot.is_ready()

    if is_ready and accepting:
        body = json.dumps(
            {
                "status": "ready",
                "phase": phase.value,
                "accepting_commands": True,
                "user": str(bot.user),
            },
        )
        return web.Response(text=body, content_type="application/json")

    reason = "gateway_not_ready" if not is_ready else f"lifecycle_{phase.value}"
    return web.Response(
        text=json.dumps(
            {
                "status": "not_ready",
                "phase": phase.value,
                "accepting_commands": accepting,
                "reason": reason,
            },
        ),
        status=503,
        content_type="application/json",
    )


async def _lifecycle_handler(request: web.Request) -> web.Response:
    """Diagnostic dump of the full lifecycle snapshot as JSON.

    Always returns 200 — this is a diagnostic endpoint, not a probe.
    The same data is available via ``!platform lifecycle`` and the
    ``!lc`` shortcut, but those require the bot to be responsive in
    Discord.  This endpoint works as long as the aiohttp server is
    serving, so operators can ``curl`` the bot during an incident
    where the Discord gateway is wedged but the HTTP listener is up.

    The payload is the same shape returned by
    :func:`core.runtime.lifecycle.diagnostics_snapshot`, suitable
    for piping into ``jq`` for ad-hoc queries.
    """
    return web.Response(
        text=json.dumps(lifecycle.diagnostics_snapshot()),
        content_type="application/json",
    )


async def _metrics_handler(request: web.Request) -> web.Response:
    """Prometheus metrics exposition endpoint."""
    return web.Response(body=generate_latest(), content_type=CONTENT_TYPE_LATEST)


async def start_health_server(
    bot: commands.Bot,
    *,
    ready_event: asyncio.Event | None = None,
) -> None:
    """Start the aiohttp health server and block until cancelled.

    Args:
        bot: the discord bot, attached to the aiohttp app so handlers
            can introspect uptime / readiness.
        ready_event: optional ``asyncio.Event`` set after the TCP bind
            succeeds.  ``bot1.main`` waits on this event before
            ``bot.start()`` so a bind failure surfaces immediately
            instead of running a healthless bot behind a wedged probe.

    Bind failures (port-in-use, permission-denied) propagate out of
    this coroutine after cleanup runs.  ``ready_event`` is **not** set
    in that case, so callers waiting on it must also observe the task
    exception (or use ``asyncio.wait`` with both signals).
    """
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/health", _health_handler)
    app.router.add_get("/ready", _ready_handler)
    app.router.add_get("/lifecycle", _lifecycle_handler)
    app.router.add_get("/metrics", _metrics_handler)

    # Private control API (Q-0156/Q-0159) — dormant unless CONTROL_API_TOKEN is
    # set. Wrapped so a control-API issue can never break the health server (and
    # thus bot startup): the orchestration probes must always come up.
    try:
        from control_api import register_control_routes

        register_control_routes(app, bot)
    except Exception:  # noqa: BLE001 - control API must never break health
        logger.exception("control_api: route registration failed; continuing")

    # Mineverse WRITE endpoint (mineverse FLAG 2) — dormant unless
    # MINING_WRITE_SHARED_SECRET is set. Same wrapping rule as the control
    # API: a relay issue can never break the health server or bot startup.
    try:
        from mining_write_api import register_mining_write_routes

        register_mining_write_routes(app, bot)
    except Exception:  # noqa: BLE001 - the relay must never break health
        logger.exception("mining_write_api: route registration failed; continuing")

    runner = web.AppRunner(app, access_log=None)
    try:
        await runner.setup()
        site = web.TCPSite(runner, _HEALTH_HOST, _HEALTH_PORT)
        await site.start()
        logger.info("Health server listening on %s:%d", _HEALTH_HOST, _HEALTH_PORT)
        if ready_event is not None:
            ready_event.set()
        # Keep running until the task is cancelled (bot shutdown).
        await asyncio.get_running_loop().create_future()
    finally:
        await runner.cleanup()

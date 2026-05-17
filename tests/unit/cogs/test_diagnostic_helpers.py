"""Embed-builder contract tests for DiagnosticCog.

The hub panel buttons call ``self.cog.build_*_embed()`` to populate the
panel embed in place (instead of spawning new messages).  These tests
pin the shape of those helpers so future refactors don't accidentally
re-introduce the ``ctx.invoke`` pattern that caused the panel to spam
new messages on every click.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.diagnostic_cog import DiagnosticCog


def _make_cog(bot: MagicMock | None = None) -> DiagnosticCog:
    if bot is None:
        bot = MagicMock()
        bot.guilds = []
        bot.commands = []
        bot.cogs = {}
        bot.latency = 0.05
    return DiagnosticCog(bot)


def test_build_latency_embed_is_sync_and_returns_embed():
    cog = _make_cog()
    embed = cog.build_latency_embed()
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Bot Latency"


def test_build_status_embed_returns_embed():
    cog = _make_cog()
    with patch("cogs.diagnostic_cog.psutil") as psutil_mock:
        psutil_mock.cpu_percent.return_value = 5
        psutil_mock.virtual_memory.return_value = MagicMock(percent=33)
        embed = cog.build_status_embed()
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Bot Status"


def test_build_system_info_embed_returns_embed():
    cog = _make_cog()
    embed = cog.build_system_info_embed()
    assert isinstance(embed, discord.Embed)
    assert embed.title == "System Information"


def test_build_json_validation_embed_returns_embed():
    cog = _make_cog()
    with patch("cogs.diagnostic_cog.os.path.isdir", return_value=False):
        embed = cog.build_json_validation_embed()
    assert isinstance(embed, discord.Embed)
    assert embed.title == "JSON Files Validation"


@pytest.mark.asyncio
async def test_build_database_embed_returns_embed_even_on_db_failure():
    cog = _make_cog()
    with patch(
        "cogs.diagnostic_cog.db.fetchall",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connection refused"),
    ):
        embed = await cog.build_database_embed()
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Database Schema Check"
    assert "Could not query database" in (embed.description or "")


@pytest.mark.asyncio
async def test_build_recent_errors_embed_returns_embed_when_empty():
    cog = _make_cog()
    with patch(
        "cogs.diagnostic_cog.db.fetchall",
        new_callable=AsyncMock,
        return_value=[],
    ):
        embed = await cog.build_recent_errors_embed(limit=10)
    assert isinstance(embed, discord.Embed)
    assert embed.title == "Recent Errors"
    assert "No recent errors" in (embed.description or "")


@pytest.mark.asyncio
async def test_send_test_notification_returns_error_when_no_reporter():
    bot = MagicMock()
    bot._reporter = None
    cog = DiagnosticCog(bot)
    embed = await cog.send_test_notification()
    assert isinstance(embed, discord.Embed)
    assert "No webhook reporter" in (embed.description or "")

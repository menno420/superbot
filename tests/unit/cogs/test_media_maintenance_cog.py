"""Unit tests for MediaMaintenanceCog — the YouTube cache retention owner.

The loop body is exercised directly via the wrapped coroutine (``.coro``) so no
real scheduler/event loop is needed (P0-2 / Q-0099).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from cogs.media_maintenance_cog import MediaMaintenanceCog  # noqa: E402


def _cog() -> MediaMaintenanceCog:
    return MediaMaintenanceCog(MagicMock())


async def test_purge_loop_calls_service(monkeypatch):
    purge = AsyncMock(return_value=3)
    monkeypatch.setattr(
        "services.video_reference_cache_service.purge_expired",
        purge,
    )
    cog = _cog()
    await cog._purge_loop.coro(cog)
    purge.assert_called_once()


async def test_purge_loop_swallows_errors(monkeypatch):
    """A transient DB failure must not propagate out of the loop body."""
    monkeypatch.setattr(
        "services.video_reference_cache_service.purge_expired",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    cog = _cog()
    # Should not raise.
    await cog._purge_loop.coro(cog)


async def test_purge_loop_records_success_outcome(monkeypatch):
    from services import youtube_diagnostics

    youtube_diagnostics._reset_for_tests()
    monkeypatch.setattr(
        "services.video_reference_cache_service.purge_expired",
        AsyncMock(return_value=2),
    )
    cog = _cog()
    await cog._purge_loop.coro(cog)
    snap = youtube_diagnostics.last_purge_snapshot()
    assert snap is not None and snap["rows"] == 2 and snap["ok"] is True
    youtube_diagnostics._reset_for_tests()


async def test_purge_loop_records_failure_outcome(monkeypatch):
    from services import youtube_diagnostics

    youtube_diagnostics._reset_for_tests()
    monkeypatch.setattr(
        "services.video_reference_cache_service.purge_expired",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    cog = _cog()
    await cog._purge_loop.coro(cog)
    snap = youtube_diagnostics.last_purge_snapshot()
    assert snap is not None and snap["ok"] is False
    youtube_diagnostics._reset_for_tests()


async def test_setup_registers_media_diagnostics_provider(monkeypatch):
    from cogs import media_maintenance_cog
    from services import diagnostics_service

    # Register only the media provider and clean it up — do NOT wipe the
    # shared import-populated diagnostics registry (that would leak an empty
    # registry into sibling tests under a parallel run).
    bot = MagicMock()
    bot.add_cog = AsyncMock()
    try:
        await media_maintenance_cog.setup(bot)
        assert "media" in diagnostics_service.registered_names()
        # the provider returns the content-free snapshot shape
        snap = diagnostics_service.snapshot("media")
        assert set(snap) == {"provider_outcomes", "last_purge"}
    finally:
        diagnostics_service.unregister("media")

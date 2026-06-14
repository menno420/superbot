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

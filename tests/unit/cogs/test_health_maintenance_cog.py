"""Unit tests for HealthMaintenanceCog — the findings-retention loop owner.

The loop body is exercised directly via the wrapped coroutine (``.coro``) so no
real scheduler/event loop is needed (P1-2 / Q-0097).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from cogs.health_maintenance_cog import HealthMaintenanceCog  # noqa: E402


def _cog() -> HealthMaintenanceCog:
    return HealthMaintenanceCog(MagicMock())


async def test_retention_loop_calls_service(monkeypatch):
    run_retention = AsyncMock(return_value=2)
    monkeypatch.setattr(
        "services.health_findings_service.run_retention",
        run_retention,
    )
    cog = _cog()
    await cog._retention_loop.coro(cog)
    run_retention.assert_called_once()


async def test_retention_loop_swallows_errors(monkeypatch):
    """A transient DB failure must not propagate out of the loop body."""
    monkeypatch.setattr(
        "services.health_findings_service.run_retention",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    cog = _cog()
    # Should not raise.
    await cog._retention_loop.coro(cog)

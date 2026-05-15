"""Shared fixtures for governance unit tests.

Provides:
  - clear_cache: function-scoped autouse, wipes module-level governance state
  - mock_db: function-scoped, patches db.get() and db.get_cleanup_policy()
  - make_ctx / make_visibility_row: test-data helpers

Registry validation and sys.path/env setup live in tests/conftest.py and run
once per session before any fixture here is invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

import services.governance_service as gs
import utils.db as db_module
from services.governance_service import GovernanceContext


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset all module-level mutable state in governance_service between tests."""
    gs._CACHE.clear()
    gs._CACHE_VERSION.clear()
    gs._guild_has_role_overrides.clear()
    gs._FAILED_SUBSYSTEMS.clear()
    gs._FEEDBACK_COOLDOWN.clear()
    yield
    gs._CACHE.clear()
    gs._CACHE_VERSION.clear()
    gs._guild_has_role_overrides.clear()
    gs._FAILED_SUBSYSTEMS.clear()
    gs._FEEDBACK_COOLDOWN.clear()


@pytest.fixture
def mock_db(monkeypatch):
    """Patch db.get() and db.get_cleanup_policy() with in-memory stubs.

    Returns the mock pool object so individual tests can set .fetch.return_value.
    Default: fetch returns [] (no DB overrides), get_cleanup_policy returns None.
    """
    pool = MagicMock()
    pool.fetch = AsyncMock(return_value=[])
    monkeypatch.setattr(db_module, "get", lambda: pool)
    monkeypatch.setattr(db_module, "get_cleanup_policy", AsyncMock(return_value=None))
    return pool


def make_ctx(
    guild_id: int = 100,
    channel_id: int | None = 200,
    category_id: int | None = 300,
) -> GovernanceContext:
    """Build a GovernanceContext with no Discord member (yields tier='user')."""
    return GovernanceContext(
        guild_id=guild_id,
        channel_id=channel_id,
        category_id=category_id,
        member=None,
    )


def make_visibility_row(
    scope_type: str,
    scope_id: int,
    subsystem: str,
    enabled: bool | None,
) -> dict:
    """Build a fake asyncpg-like row dict for subsystem_visibility queries."""
    return {
        "scope_type": scope_type,
        "scope_id": scope_id,
        "subsystem": subsystem,
        "enabled": enabled,
    }

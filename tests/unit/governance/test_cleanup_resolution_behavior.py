"""Behaviour-identical pin for cleanup resolution (server-management PR8).

PR8 adds a ``policy_version`` column + a level vocabulary but must NOT change how
a stored policy resolves at runtime. These tests lock the current mapping so any
future edit to ``governance/cleanup.py`` (or the level table) that would alter
resolved behaviour fails here.

Pinned facts (the resolver's current contract — preserved, not "fixed"):
* ``delete_message`` derives ONLY from ``delete_invalid_commands``;
  ``delete_failed_commands`` does not affect resolution and ``CleanupPolicy`` has
  no field for it.
* ``delete_after_seconds`` passes through unchanged; ``send_feedback`` is True for
  an override; the source is the matched scope.
* An extra ``policy_version`` key in the row is inert.
* With no override and a non-whitelisted channel, the hardcoded default is
  delete=True / 5s / FALLBACK_DEFAULT.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import governance.cleanup as cleanup_mod
from governance.models import GovernanceContext, PolicySource
from services.cleanup_levels import LEVELS


def _ctx() -> GovernanceContext:
    # channel_id set, no category/thread → scope chain = [channel, guild].
    return GovernanceContext(guild_id=789, channel_id=123)


@pytest.mark.asyncio
@pytest.mark.parametrize("level", list(LEVELS))
async def test_each_level_resolves_to_stable_policy(level: str, monkeypatch):
    cols = LEVELS[level]
    fake_db = MagicMock()
    fake_db.get_cleanup_policy = AsyncMock(return_value=dict(cols))
    monkeypatch.setattr(cleanup_mod, "db", fake_db)

    policy = await cleanup_mod.resolve_cleanup_policy(_ctx())

    assert policy.delete_message == cols["delete_invalid_commands"]
    assert policy.delete_after_seconds == cols["delete_after_seconds"]
    assert policy.send_feedback is True
    assert policy.resolved_from == PolicySource.CHANNEL_OVERRIDE


@pytest.mark.asyncio
async def test_extra_policy_version_key_is_inert(monkeypatch):
    """A row carrying the new column resolves identically to one without it."""
    row = {
        "delete_invalid_commands": True,
        "delete_failed_commands": True,
        "delete_after_seconds": 5,
        "policy_version": 1,
    }
    fake_db = MagicMock()
    fake_db.get_cleanup_policy = AsyncMock(return_value=row)
    monkeypatch.setattr(cleanup_mod, "db", fake_db)

    policy = await cleanup_mod.resolve_cleanup_policy(_ctx())

    assert policy.delete_message is True
    assert policy.delete_after_seconds == 5
    assert policy.resolved_from == PolicySource.CHANNEL_OVERRIDE


@pytest.mark.asyncio
async def test_no_override_falls_back_to_default(monkeypatch):
    """No row + non-whitelisted channel → hardcoded compat default (unchanged)."""
    fake_db = MagicMock()
    fake_db.get_cleanup_policy = AsyncMock(return_value=None)
    monkeypatch.setattr(cleanup_mod, "db", fake_db)
    # Ensure the channel is not in the whitelist fallback.
    monkeypatch.setattr(cleanup_mod._config, "CLEANUP_WHITELIST_CHANNELS", set())

    policy = await cleanup_mod.resolve_cleanup_policy(_ctx())

    assert policy.delete_message is True
    assert policy.delete_after_seconds == 5
    assert policy.send_feedback is True
    assert policy.resolved_from == PolicySource.FALLBACK_DEFAULT

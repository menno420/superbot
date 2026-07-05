"""Stage-2 walk bug #7 (+ #8 teardown) — new guild-leave teardown steps.

Three role tables (``role_thresholds``, ``role_automation_exemptions``,
``reaction_roles``) and the proof-channel lock table had no teardown step, so
their rows accumulated forever after a guild left. Each new ``_teardown_*``
helper deletes its table for the departed guild and isolates its own failure
(one bad step must never abort the whole sweep).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import guild_lifecycle

# ruff: noqa: S101

_STEPS = [
    ("_teardown_role_thresholds", "utils.db.roles.delete_role_thresholds_for_guild"),
    ("_teardown_role_exemptions", "utils.db.roles.delete_role_exemptions_for_guild"),
    ("_teardown_reaction_roles", "utils.db.roles.delete_reaction_roles_for_guild"),
    (
        "_teardown_proof_channel_locks",
        "utils.db.proof_channel_locks.delete_for_guild",
    ),
]


@pytest.mark.parametrize(("step", "target"), _STEPS)
@pytest.mark.asyncio
async def test_new_teardown_step_deletes_for_guild(monkeypatch, step, target):
    mock = AsyncMock(return_value=3)
    monkeypatch.setattr(target, mock)
    await getattr(guild_lifecycle, step)(99)
    mock.assert_awaited_once_with(99)


@pytest.mark.parametrize(("step", "target"), _STEPS)
@pytest.mark.asyncio
async def test_new_teardown_step_isolates_failure(monkeypatch, step, target):
    monkeypatch.setattr(target, AsyncMock(side_effect=RuntimeError("DB blip")))
    # Must swallow — one failing step cannot abort the guild-leave sweep.
    await getattr(guild_lifecycle, step)(99)

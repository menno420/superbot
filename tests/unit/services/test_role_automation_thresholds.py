"""Tests for the audited threshold-setter seam in role_automation (PR11).

``set_time_threshold`` / ``set_xp_threshold`` give the auto-role
thresholds a single audited service seam so the setup wizard's
``set_role_threshold`` op can route through a service (not raw DB) and
the change surfaces on the audit channel.  Pins:

* the canonical DB writer is called with id-groundwork captured,
* the XP path invalidates the XP-threshold cache,
* both emit the ``audit.action_recorded`` companion and return a
  ``mutation_id``.

DB-free: the canonical writers + cache + audit emit are patched.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import role_automation


@pytest.mark.asyncio
async def test_set_time_threshold_writes_and_audits():
    with (
        patch(
            "utils.db.roles.set_role_threshold",
            new_callable=AsyncMock,
        ) as writer,
        patch(
            "services.role_automation.emit_audit_action",
            new_callable=AsyncMock,
        ) as emit,
    ):
        mid = await role_automation.set_time_threshold(
            guild_id=1,
            role_id=555,
            role_name="Veteran",
            days=7,
            actor_id=99,
        )

    assert mid  # a mutation_id is returned
    writer.assert_awaited_once()
    args, kwargs = writer.await_args.args, writer.await_args.kwargs
    assert args[0] == 1  # guild_id
    assert args[1] == "Veteran"  # role_name (the row key)
    assert args[2] == 7  # days
    # id-groundwork captured so a rename does not orphan the tier.
    assert kwargs["role_id"] == 555
    assert kwargs["display_name"] == "Veteran"

    emit.assert_awaited_once()
    ekw = emit.await_args.kwargs
    assert ekw["subsystem"] == "role_automation"
    assert ekw["mutation_type"] == "set_time_threshold"
    assert ekw["target"] == "role:555"
    assert ekw["guild_id"] == 1
    assert ekw["actor_id"] == 99
    assert ekw["new_value"] == "7d"
    assert ekw["mutation_id"] == mid


@pytest.mark.asyncio
async def test_set_time_threshold_name_only_when_role_id_none():
    """``role_id=None`` (the legacy free-text ``!setrole`` path, where the named
    role may not exist) still writes + audits; the audit target falls back to the
    role name since there is no id to reference.
    """
    with (
        patch(
            "utils.db.roles.set_role_threshold",
            new_callable=AsyncMock,
        ) as writer,
        patch(
            "services.role_automation.emit_audit_action",
            new_callable=AsyncMock,
        ) as emit,
    ):
        mid = await role_automation.set_time_threshold(
            guild_id=1,
            role_id=None,
            role_name="Ghost",
            days=5,
            actor_id=99,
        )

    assert mid
    writer.assert_awaited_once()
    assert writer.await_args.kwargs["role_id"] is None
    emit.assert_awaited_once()
    assert emit.await_args.kwargs["target"] == "role:Ghost"  # name fallback


@pytest.mark.asyncio
async def test_set_xp_threshold_writes_invalidates_and_audits():
    invalidate = MagicMock()
    with (
        patch(
            "utils.db.roles.set_role_xp_threshold",
            new_callable=AsyncMock,
        ) as writer,
        patch(
            "utils.guild_config_accessors.invalidate_xp_threshold_roles",
            invalidate,
        ),
        patch(
            "services.role_automation.emit_audit_action",
            new_callable=AsyncMock,
        ) as emit,
    ):
        mid = await role_automation.set_xp_threshold(
            guild_id=1,
            role_id=777,
            role_name="Pro",
            level=25,
            actor_id=99,
        )

    assert mid
    writer.assert_awaited_once()
    args, kwargs = writer.await_args.args, writer.await_args.kwargs
    assert args[0] == 1  # guild_id
    assert args[1] == "Pro"  # role_name
    assert args[2] == 25  # level_required
    assert args[3] is True  # auto_assign (default)
    assert kwargs["role_id"] == 777
    assert kwargs["display_name"] == "Pro"

    # The live XP listener reads a cache that must be dropped on write.
    invalidate.assert_called_once_with(1)

    emit.assert_awaited_once()
    ekw = emit.await_args.kwargs
    assert ekw["mutation_type"] == "set_xp_threshold"
    assert ekw["target"] == "role:777"
    assert ekw["new_value"] == "L25"
    assert ekw["mutation_id"] == mid

"""Phase 2 — guild_lifecycle.teardown wires Phase 2 cleanup primitives.

Two new steps were added to ``guild_lifecycle.teardown`` in this PR:

* **Step 5** — :func:`utils.db.bindings.delete_active_bindings_for_guild`
  purges ``subsystem_bindings`` rows and **preserves**
  ``binding_audit_log``.  The audit primitive is split into
  :func:`utils.db.bindings.purge_binding_audit_for_guild` which is
  reserved for explicit forensic cleanup and is **never** called from
  teardown.
* **Step 6** — :func:`utils.db.resource_cache.delete_for_guild` drops
  cached resource validation rows (the primitive shipped in PR #72; the
  wiring landed here).

These tests pin the contract for both:

* Both new primitives are awaited during teardown.
* The audit-purge primitive is **not** awaited (retention guarantee).
* Per-step failure does not abort the rest of the teardown sequence
  (matches the existing try/except discipline in
  ``disbot/guild_lifecycle.py``).
* Repeated invocation of teardown is safe (idempotent — primitives are
  ``DELETE WHERE`` statements that return zero on a second run).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def _teardown_patches():
    """Patch every other teardown step so the test isolates Phase 2 wiring.

    The lifecycle sequence touches scheduler / sessions / panel anchors /
    governance caches / scope_locks / etc.  None of those are under test
    here; mocking them keeps the test independent of cross-cutting
    runtime imports.
    """
    with (
        patch(
            "utils.db.delete_sessions_for_guild",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "utils.db.delete_guild_session_state",
            new_callable=AsyncMock,
        ),
        patch(
            "utils.db.delete_guild_panel_anchors",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "core.runtime.live_update_scheduler.forget_guild",
            return_value=0,
        ),
        patch(
            "governance.execution.forget_guild_capabilities",
        ),
        patch(
            "governance.cache.forget_guild",
        ),
        patch(
            "core.runtime.guild_config.forget_guild",
        ),
        patch(
            "core.runtime.scope_locks.teardown_guild",
            return_value=0,
        ),
    ):
        yield


# ---------------------------------------------------------------------------
# Step 5 — subsystem bindings active rows deleted; audit preserved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_active_bindings(_teardown_patches):
    """The active-row delete primitive is awaited exactly once with guild_id."""
    import guild_lifecycle

    with patch(
        "utils.db.bindings.delete_active_bindings_for_guild",
        new_callable=AsyncMock,
        return_value=2,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_does_not_purge_binding_audit(_teardown_patches):
    """Audit retention guarantee: teardown never calls the purge primitive.

    If a future contributor wires the audit-purge primitive into the
    teardown sequence, this test fails and they must update both the
    retention policy (``docs/platform-consistency-ledger.md`` §3) AND
    this assertion deliberately.
    """
    import guild_lifecycle

    with (
        patch(
            "utils.db.bindings.delete_active_bindings_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "utils.db.bindings.purge_binding_audit_for_guild",
            new_callable=AsyncMock,
        ) as mock_purge,
    ):
        await guild_lifecycle.teardown(99)
        mock_purge.assert_not_awaited()


@pytest.mark.asyncio
async def test_teardown_binding_step_failure_is_isolated(_teardown_patches):
    """If the binding-delete primitive raises, the resource-cache step still runs."""
    import guild_lifecycle

    with (
        patch(
            "utils.db.bindings.delete_active_bindings_for_guild",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
        patch(
            "utils.db.resource_cache.delete_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ) as mock_resource_delete,
    ):
        await guild_lifecycle.teardown(99)
        mock_resource_delete.assert_awaited_once_with(99)


# ---------------------------------------------------------------------------
# Step 6 — resource validation cache rows deleted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_resource_cache(_teardown_patches):
    """The resource-cache delete primitive is awaited exactly once with guild_id."""
    import guild_lifecycle

    with (
        patch(
            "utils.db.bindings.delete_active_bindings_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "utils.db.resource_cache.delete_for_guild",
            new_callable=AsyncMock,
            return_value=3,
        ) as mock_delete,
    ):
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_resource_cache_step_failure_is_isolated(_teardown_patches):
    """If resource-cache delete raises, the rest of teardown continues."""
    import guild_lifecycle

    with (
        patch(
            "utils.db.bindings.delete_active_bindings_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "utils.db.resource_cache.delete_for_guild",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
        patch(
            "governance.execution.forget_guild_capabilities",
        ) as mock_caps,
    ):
        await guild_lifecycle.teardown(99)
        # downstream step still invoked despite resource_cache failure
        mock_caps.assert_called_once_with(99)


# ---------------------------------------------------------------------------
# Idempotency — calling teardown twice produces no error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_is_idempotent(_teardown_patches):
    """Re-running teardown for the same guild is a no-op safety net."""
    import guild_lifecycle

    with (
        patch(
            "utils.db.bindings.delete_active_bindings_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ) as mock_bindings_delete,
        patch(
            "utils.db.resource_cache.delete_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ) as mock_resource_delete,
    ):
        await guild_lifecycle.teardown(99)
        await guild_lifecycle.teardown(99)
        assert mock_bindings_delete.await_count == 2
        assert mock_resource_delete.await_count == 2

"""Phase 2 — guild_lifecycle.teardown wires Phase 2 cleanup primitives.

PR-1 added two steps to ``guild_lifecycle.teardown``:

* **Step 5** — :func:`utils.db.bindings.delete_active_bindings_for_guild`
  purges ``subsystem_bindings`` rows and **preserves**
  ``binding_audit_log``.  The audit primitive is split into
  :func:`utils.db.bindings.purge_binding_audit_for_guild` which is
  reserved for explicit forensic cleanup and is **never** called from
  teardown.
* **Step 6** — :func:`utils.db.resource_cache.delete_for_guild` drops
  cached resource validation rows (the primitive shipped in PR #72;
  the wiring landed here).

PR-2 added three more (Phase 2d feature-flag substrate):

* **Step 7** — :func:`utils.db.feature_flag_state.delete_for_guild`
  drops the per-guild override rows; global rows are preserved.
* **Step 8** — :func:`utils.db.environment_tiers.delete_for_guild`
  removes the environment-tier row so the guild re-defaults to
  PRODUCTION on re-invite.
* **Step 9** — :func:`core.runtime.feature_flags.clear_cache` purges
  cached evaluator decisions for the guild.

PR-5 adds:

* **Step 10** —
  :func:`utils.db.platform_migration_checkpoints.delete_for_guild`
  drops per-guild migration checkpoint rows; global rows are
  preserved.

These tests pin the contract:

* Every new primitive is awaited (or called, for the sync one) during
  teardown.
* The binding audit-purge primitive is **never** awaited (retention
  guarantee).
* Global feature-flag overrides are preserved — the primitive scopes
  to guild rows only.
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
        # Phase 2d defaults — patched here so individual tests can
        # override via additional with patch(...) blocks when they need
        # to assert against the new feature-flag/environment-tier steps.
        patch(
            "utils.db.feature_flag_state.delete_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "utils.db.environment_tiers.delete_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "core.runtime.feature_flags.clear_cache",
            return_value=0,
        ),
        # PR-5 default: migration checkpoint delete primitive.
        patch(
            "utils.db.platform_migration_checkpoints.delete_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ),
        # PR-8 defaults: participation table + cache.
        patch(
            "utils.db.user_participation.delete_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "core.runtime.user_config.forget_guild",
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
    retention policy (``docs/health/platform-consistency-ledger.md`` §3) AND
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


# ---------------------------------------------------------------------------
# Step 7 — feature_flag_state per-guild overrides deleted; globals preserved
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_feature_flag_guild_overrides(_teardown_patches):
    """The feature_flag guild-override primitive is awaited from teardown."""
    import guild_lifecycle

    with patch(
        "utils.db.feature_flag_state.delete_for_guild",
        new_callable=AsyncMock,
        return_value=2,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_feature_flag_step_failure_is_isolated(_teardown_patches):
    """If the feature-flag delete raises, downstream steps still run."""
    import guild_lifecycle

    with (
        patch(
            "utils.db.feature_flag_state.delete_for_guild",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
        patch(
            "utils.db.environment_tiers.delete_for_guild",
            new_callable=AsyncMock,
            return_value=0,
        ) as mock_et,
    ):
        await guild_lifecycle.teardown(99)
        mock_et.assert_awaited_once_with(99)


# ---------------------------------------------------------------------------
# Step 8 — environment_tier row deleted
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_environment_tier(_teardown_patches):
    import guild_lifecycle

    with patch(
        "utils.db.environment_tiers.delete_for_guild",
        new_callable=AsyncMock,
        return_value=1,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


# ---------------------------------------------------------------------------
# Step 9 — feature_flag cache cleared per guild
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_clears_feature_flag_cache(_teardown_patches):
    """Cache clear is called scoped to the guild (guild_id kwarg)."""
    import guild_lifecycle

    with patch(
        "core.runtime.feature_flags.clear_cache",
        return_value=0,
    ) as mock_clear:
        await guild_lifecycle.teardown(99)
        mock_clear.assert_called_once_with(guild_id=99)


# ---------------------------------------------------------------------------
# Step 10 — platform migration checkpoints (per-guild rows only)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_migration_checkpoints(_teardown_patches):
    """Per-guild checkpoint delete primitive is awaited from teardown."""
    import guild_lifecycle

    with patch(
        "utils.db.platform_migration_checkpoints.delete_for_guild",
        new_callable=AsyncMock,
        return_value=1,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_migration_checkpoint_failure_is_isolated(_teardown_patches):
    """If the checkpoint delete raises, downstream steps still run."""
    import guild_lifecycle

    with (
        patch(
            "utils.db.platform_migration_checkpoints.delete_for_guild",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
        patch(
            "governance.execution.forget_guild_capabilities",
        ) as mock_caps,
    ):
        await guild_lifecycle.teardown(99)
        # downstream step still invoked despite checkpoint delete failure
        mock_caps.assert_called_once_with(99)


# ---------------------------------------------------------------------------
# Steps 11 + 12 — per-user participation rows + cache (Phase 2c PR-8)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_user_participation_rows(_teardown_patches):
    """The four-table participation delete primitive is awaited."""
    import guild_lifecycle

    with patch(
        "utils.db.user_participation.delete_for_guild",
        new_callable=AsyncMock,
        return_value=5,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_clears_user_config_cache(_teardown_patches):
    """user_config.forget_guild is called scoped to the guild."""
    import guild_lifecycle

    with patch(
        "core.runtime.user_config.forget_guild",
        return_value=0,
    ) as mock_forget:
        await guild_lifecycle.teardown(99)
        mock_forget.assert_called_once_with(99)


@pytest.mark.asyncio
async def test_teardown_participation_failure_is_isolated(_teardown_patches):
    """If participation delete raises, the user_config cache step still runs."""
    import guild_lifecycle

    with (
        patch(
            "utils.db.user_participation.delete_for_guild",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
        patch(
            "core.runtime.user_config.forget_guild",
            return_value=0,
        ) as mock_forget,
    ):
        await guild_lifecycle.teardown(99)
        mock_forget.assert_called_once_with(99)


# ---------------------------------------------------------------------------
# Step 22 — command-access policy + cached snapshot (command-access PR-3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_calls_command_access_forget_guild(_teardown_patches):
    """Step 22 awaits ``core.runtime.command_access.forget_guild`` so
    both the typed-accessor cache entry and the
    ``guild_command_access_policy`` row are dropped on guild leave.
    """
    import guild_lifecycle

    with patch(
        "core.runtime.command_access.forget_guild",
        new_callable=AsyncMock,
    ) as mock_forget:
        await guild_lifecycle.teardown(99)
        mock_forget.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_command_access_failure_is_isolated(_teardown_patches):
    """A failure in command-access teardown must not abort the
    surrounding lifecycle sequence — matches the try/except discipline
    every other step uses.
    """
    import guild_lifecycle

    with patch(
        "core.runtime.command_access.forget_guild",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB blip"),
    ):
        # No exception escapes — the lifecycle swallows + logs.
        await guild_lifecycle.teardown(99)


# ---------------------------------------------------------------------------
# Step 23 — role menus deleted (reaction-roles overhaul)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_role_menus(_teardown_patches):
    """Step 23 awaits ``utils.db.role_menus.delete_for_guild`` so the new
    ``role_menus`` table (and its cascading options) never accumulates rows
    for a departed guild (architecture INV-I).
    """
    import guild_lifecycle

    with patch(
        "utils.db.role_menus.delete_for_guild",
        new_callable=AsyncMock,
        return_value=2,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_role_menu_failure_is_isolated(_teardown_patches):
    """A failure in the role-menu teardown step must not abort the sequence."""
    import guild_lifecycle

    with patch(
        "utils.db.role_menus.delete_for_guild",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB blip"),
    ):
        # No exception escapes — the lifecycle swallows + logs.
        await guild_lifecycle.teardown(99)


# ---------------------------------------------------------------------------
# Step 24 — per-message reaction modes deleted (reaction-roles overhaul PR 3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_reaction_modes(_teardown_patches):
    """Step 24 awaits ``delete_reaction_modes_for_guild`` so per-message
    reaction-mode rows never accumulate for a departed guild (INV-I).
    """
    import guild_lifecycle

    with patch(
        "utils.db.delete_reaction_modes_for_guild",
        new_callable=AsyncMock,
        return_value=3,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_reaction_modes_failure_is_isolated(_teardown_patches):
    """A failure in the reaction-mode teardown step must not abort the sequence."""
    import guild_lifecycle

    with patch(
        "utils.db.delete_reaction_modes_for_guild",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB blip"),
    ):
        await guild_lifecycle.teardown(99)


# ---------------------------------------------------------------------------
# Step 25 — temporary role grants deleted (reaction-roles overhaul PR 4)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_role_grants(_teardown_patches):
    """Step 25 awaits ``utils.db.role_grants.delete_for_guild`` so pending temp
    grants never accumulate for a departed guild (INV-I).
    """
    import guild_lifecycle

    with patch(
        "utils.db.role_grants.delete_for_guild",
        new_callable=AsyncMock,
        return_value=4,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_role_grants_failure_is_isolated(_teardown_patches):
    """A failure in the role-grant teardown step must not abort the sequence."""
    import guild_lifecycle

    with patch(
        "utils.db.role_grants.delete_for_guild",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB blip"),
    ):
        await guild_lifecycle.teardown(99)


# ---------------------------------------------------------------------------
# Step 26 — role-pickup analytics deleted (reaction-roles overhaul PR 5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teardown_deletes_role_pickup_stats(_teardown_patches):
    """Step 26 awaits ``role_menus.delete_pickup_stats_for_guild`` so analytics
    rows never accumulate for a departed guild (INV-I).
    """
    import guild_lifecycle

    with patch(
        "utils.db.role_menus.delete_pickup_stats_for_guild",
        new_callable=AsyncMock,
        return_value=2,
    ) as mock_delete:
        await guild_lifecycle.teardown(99)
        mock_delete.assert_awaited_once_with(99)


@pytest.mark.asyncio
async def test_teardown_pickup_stats_failure_is_isolated(_teardown_patches):
    """A failure in the pickup-stats teardown step must not abort the sequence."""
    import guild_lifecycle

    with patch(
        "utils.db.role_menus.delete_pickup_stats_for_guild",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB blip"),
    ):
        await guild_lifecycle.teardown(99)

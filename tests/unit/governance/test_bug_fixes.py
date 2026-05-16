"""Regression tests for confirmed bug fixes.

Covers:
  BUG-002  EVT_CACHE_INVALIDATED emission from mutation pipeline
  BUG-005  runtime.setup() idempotency
  BUG-006  _NO_OVERRIDE sentinel removed from cache
  ARCH-005 unknown capability fails closed
  GAP-001  panel anchors deleted from DB on guild teardown
  DEBT-001 capability override cache TTL refresh
  DEBT-002 internal bypass persists audit row
  DEBT-003 EVT_CLEANUP_CHANGED subscription
  DEBT-006 _last_edit cleanup is unconditional & per-guild

Deletions (P1 PR-5):
  - TestMaybeDecodeLegacy   — 6 trivial passthrough tests on a
    pure-data shim; removing them costs zero coverage.
  - TestThreadScopeAccepted — constant-membership checks; the
    invariant is enforced by migration 009 + the registry tests.
  - TestForgetGuildCapabilities — exercised private module-level
    state; the behaviour is now covered indirectly by
    TestCapabilityOverrideTTL.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# BUG-005 — setup() idempotency
# ---------------------------------------------------------------------------


class TestSetupIdempotency:
    @pytest.mark.asyncio
    async def test_double_setup_registers_one_handler_per_event(self):
        import importlib

        # Re-import a clean copy of the module to test against.
        import core.runtime as rt

        # Reset the guard for testing purposes
        rt._SETUP_DONE = False

        mock_bus = MagicMock()
        mock_bus.on = MagicMock()

        with patch("core.events.bus", mock_bus):
            with patch("services.governance_service.EVT_VISIBILITY_CHANGED", "vis"):
                with patch("services.governance_service.EVT_CACHE_INVALIDATED", "inv"):
                    await rt.setup()
                    first_call_count = mock_bus.on.call_count

                    await rt.setup()  # second call — must be a no-op
                    second_call_count = mock_bus.on.call_count

        assert first_call_count == second_call_count, (
            f"setup() called bus.on {second_call_count} times on second invocation; "
            "expected 0 (idempotency violation)."
        )

        # Reset for other tests
        rt._SETUP_DONE = False


# ---------------------------------------------------------------------------
# BUG-006 — _NO_OVERRIDE sentinel removed
# ---------------------------------------------------------------------------


class TestNoOverrideSentinelRemoved:
    def test_no_override_not_exported(self):
        import governance.cache as cache_module

        assert not hasattr(
            cache_module, "_NO_OVERRIDE"
        ), "_NO_OVERRIDE was removed as dead code — it should not exist in cache.py"

    def test_resolver_does_not_import_no_override(self):
        import inspect

        import governance.resolver as resolver_module

        source = inspect.getsource(resolver_module)
        assert (
            "_NO_OVERRIDE" not in source
        ), "resolver.py must not reference the removed _NO_OVERRIDE sentinel"


# ---------------------------------------------------------------------------
# ARCH-005 — unknown capabilities fail closed
# ---------------------------------------------------------------------------


class TestUnknownCapabilityFailsClosed:
    @pytest.mark.asyncio
    async def test_unknown_capability_denied(self):
        from governance.execution import resolve_execution
        from governance.models import GovernanceContext

        ctx = GovernanceContext(guild_id=1, channel_id=1)

        # Patch _load_capability_overrides to no-op and CAPABILITY_TO_SUBSYSTEM
        # to return nothing for a made-up capability.
        with patch("governance.execution._loaded_guilds", {1}):
            with patch(
                "governance.execution.CAPABILITY_TO_SUBSYSTEM",
                {},  # empty — capability is unknown
            ):
                result = await resolve_execution(ctx, "totally.fake.capability")

        assert result.allowed is False
        assert "unknown" in (result.reason or "").lower()

    @pytest.mark.asyncio
    async def test_known_capability_uses_visibility(self):
        """A known capability is gated on visibility (not unconditionally allowed)."""
        from governance.execution import resolve_execution
        from governance.models import GovernanceContext, VisibilityResult

        ctx = GovernanceContext(guild_id=2, channel_id=2)

        mock_visibility = VisibilityResult(
            visible_subsystems=set(),  # everything disabled
            member_tier="user",
            resolved_from={},
            traces={},
        )

        with patch("governance.execution._loaded_guilds", {2}):
            with patch(
                "governance.execution.CAPABILITY_TO_SUBSYSTEM",
                {"economy.coins.claim": "economy"},
            ):
                with patch(
                    "governance.execution.resolve_visibility",
                    AsyncMock(return_value=mock_visibility),
                ):
                    result = await resolve_execution(ctx, "economy.coins.claim")

        assert result.allowed is False


# ---------------------------------------------------------------------------
# BUG-002 — EVT_CACHE_INVALIDATED is emitted (via mutation pipeline)
# ---------------------------------------------------------------------------


class TestCacheInvalidatedEmitted:
    @pytest.mark.asyncio
    async def test_set_visibility_emits_cache_invalidated(self):
        from governance.models import GovernanceContext

        # Build a mock member with sufficient authority
        member = MagicMock()
        member.id = 1
        member.guild_permissions.administrator = True
        member.guild_permissions.moderate_members = True
        member.guild.owner_id = 0
        member.guild_permissions.manage_guild = True

        ctx = GovernanceContext(guild_id=777, channel_id=1, member=member)

        emitted_events: list[str] = []

        async def mock_emit(event_name, payload):
            emitted_events.append(event_name)

        with patch("governance.writes.db") as mock_db:
            mock_db.get_visibility_override = AsyncMock(return_value=None)
            mock_db.set_subsystem_visibility = AsyncMock()
            mock_db.write_governance_audit = AsyncMock()
            # Simulate transaction context manager
            txn = MagicMock()
            txn.__aenter__ = AsyncMock(return_value=txn)
            txn.__aexit__ = AsyncMock(return_value=False)
            mock_pool = MagicMock()
            mock_pool.transaction = MagicMock(return_value=txn)
            mock_db.get = MagicMock(return_value=mock_pool)
            with patch("governance.writes.invalidate_guild_cache"):
                with patch(
                    "governance.writes._emit_governance_event", side_effect=mock_emit
                ):
                    with patch("governance.writes.SUBSYSTEMS", {"economy": {}}):
                        from governance.writes import GovernanceMutationPipeline

                        pipeline = GovernanceMutationPipeline()
                        await pipeline.set_visibility(
                            ctx, "guild", 777, "economy", False
                        )

        from governance.events import EVT_CACHE_INVALIDATED, EVT_VISIBILITY_CHANGED

        assert (
            EVT_VISIBILITY_CHANGED in emitted_events
        ), "EVT_VISIBILITY_CHANGED must be emitted from set_visibility"
        assert (
            EVT_CACHE_INVALIDATED in emitted_events
        ), "EVT_CACHE_INVALIDATED must be emitted from set_visibility (BUG-002 fix)"


# ---------------------------------------------------------------------------
# GAP-001 — panel anchors deleted from DB on guild teardown
# ---------------------------------------------------------------------------


class TestPanelAnchorTeardown:
    @pytest.mark.asyncio
    async def test_guild_lifecycle_deletes_panel_anchors(self):
        """guild_lifecycle.teardown() must call db.delete_guild_panel_anchors."""
        import guild_lifecycle

        guild_id = 4242
        with patch(
            "utils.db.delete_guild_panel_anchors", new_callable=AsyncMock
        ) as mock_del:
            mock_del.return_value = 3
            # Patch the other DB-touching steps so we isolate the anchor path.
            with patch("utils.db.get") as mock_get:
                pool = MagicMock()
                pool.execute = AsyncMock(return_value="DELETE 0")
                mock_get.return_value = pool
                with patch(
                    "utils.db.delete_guild_session_state", new_callable=AsyncMock
                ):
                    await guild_lifecycle.teardown(guild_id)

            mock_del.assert_awaited_once_with(guild_id)

    def test_db_function_signature(self):
        from utils import db as db_module

        assert hasattr(
            db_module, "delete_guild_panel_anchors"
        ), "db.delete_guild_panel_anchors must exist (GAP-001)"


# ---------------------------------------------------------------------------
# DEBT-001 — capability override cache has a TTL refresh
# ---------------------------------------------------------------------------


class TestCapabilityOverrideTTL:
    @pytest.mark.asyncio
    async def test_stale_cache_triggers_reload(self, monkeypatch):
        """Once _OVERRIDE_TTL elapses, the next resolve_execution reloads."""
        import time as _time

        from governance import execution as exec_module
        from governance.models import GovernanceContext

        exec_module._loaded_guilds.add(5555)
        exec_module._loaded_guilds_at[5555] = _time.monotonic() - 9999.0  # stale
        exec_module._capability_execution_overrides[(5555, "test.cap.do")] = True

        load_calls: list[int] = []

        async def fake_load(guild_id: int) -> None:
            load_calls.append(guild_id)
            # Simulate DB returning nothing (clears prior entry).
            exec_module._loaded_guilds_at[guild_id] = _time.monotonic()

        monkeypatch.setattr(exec_module, "_load_capability_overrides", fake_load)
        monkeypatch.setattr(
            exec_module,
            "CAPABILITY_TO_SUBSYSTEM",
            {"test.cap.do": "test_subsystem"},
        )
        monkeypatch.setattr(
            exec_module,
            "resolve_visibility",
            AsyncMock(
                return_value=type(
                    "V",
                    (),
                    {
                        "visible_subsystems": {"test_subsystem"},
                        "traces": {},
                    },
                )()
            ),
        )

        # Prior override existed, but a refresh is forced because cache is stale.
        await exec_module.resolve_execution(
            GovernanceContext(guild_id=5555, channel_id=1),
            "test.cap.do",
        )
        assert load_calls == [5555], "stale cache must trigger a reload"

        # Cleanup
        exec_module._loaded_guilds.discard(5555)
        exec_module._loaded_guilds_at.pop(5555, None)
        exec_module._capability_execution_overrides.pop((5555, "test.cap.do"), None)

    def test_overrides_stale_detection(self):
        import time as _time

        from governance.execution import (
            _OVERRIDE_TTL,
            _loaded_guilds_at,
            _overrides_stale,
        )

        _loaded_guilds_at[7777] = _time.monotonic()
        assert not _overrides_stale(7777)
        _loaded_guilds_at[7777] = _time.monotonic() - (_OVERRIDE_TTL + 1.0)
        assert _overrides_stale(7777)
        # Cleanup
        _loaded_guilds_at.pop(7777, None)

    def test_load_clears_prior_entries(self):
        """_load_capability_overrides must purge stale rows before reloading."""
        import inspect

        from governance import execution as exec_module

        source = inspect.getsource(exec_module._load_capability_overrides)
        assert (
            "stale_keys" in source or "pop" in source
        ), "_load_capability_overrides must clear prior entries before insert"


# ---------------------------------------------------------------------------
# DEBT-002 — internal bypass persists a DB audit row
# ---------------------------------------------------------------------------


class TestInternalBypassAudit:
    @pytest.mark.asyncio
    async def test_bypass_writes_audit_row(self, monkeypatch):
        from governance import execution as exec_module
        from governance.models import GovernanceContext

        # Ensure the guild's overrides skip the DB load path.
        exec_module._loaded_guilds.add(8888)
        import time as _time

        exec_module._loaded_guilds_at[8888] = _time.monotonic()

        captured: dict = {}

        async def fake_audit(**kwargs):
            captured.update(kwargs)

        monkeypatch.setattr("utils.db.write_governance_audit", fake_audit)
        monkeypatch.setattr(
            exec_module,
            "CAPABILITY_TO_SUBSYSTEM",
            {"moderation.member.ban": "moderation"},
        )

        result = await exec_module.resolve_execution(
            GovernanceContext(guild_id=8888, channel_id=1),
            "moderation.member.ban",
            check_visibility=False,
        )

        assert result.allowed is True
        assert captured.get("action") == "execution_bypass"
        assert captured.get("guild_id") == 8888
        assert captured.get("subsystem") == "moderation"
        nv = captured.get("new_value") or {}
        assert nv.get("capability") == "moderation.member.ban"
        assert nv.get("visibility_check_skipped") is True

        # Cleanup
        exec_module._loaded_guilds.discard(8888)
        exec_module._loaded_guilds_at.pop(8888, None)


# ---------------------------------------------------------------------------
# DEBT-003 — runtime subscribes to EVT_CLEANUP_CHANGED
# ---------------------------------------------------------------------------


class TestCleanupChangedSubscription:
    @pytest.mark.asyncio
    async def test_setup_subscribes_to_cleanup_changed(self):
        import core.runtime as rt

        rt._SETUP_DONE = False
        mock_bus = MagicMock()
        mock_bus.on = MagicMock()

        subscribed_events: list[str] = []

        def capture_on(event_name, handler):
            subscribed_events.append(event_name)

        mock_bus.on.side_effect = capture_on

        with patch("core.events.bus", mock_bus):
            with patch("services.governance_service.EVT_VISIBILITY_CHANGED", "vis"):
                with patch("services.governance_service.EVT_CACHE_INVALIDATED", "inv"):
                    with patch(
                        "services.governance_service.EVT_CLEANUP_CHANGED", "cleanup"
                    ):
                        await rt.setup()

        assert (
            "cleanup" in subscribed_events
        ), "runtime.setup() must subscribe to EVT_CLEANUP_CHANGED (DEBT-003)"
        rt._SETUP_DONE = False


# ---------------------------------------------------------------------------
# DEBT-006 — _last_edit cleanup is unconditional and per-guild
# ---------------------------------------------------------------------------


class TestLastEditTeardown:
    def test_keying_is_guild_scoped(self):
        from core.runtime import live_update_scheduler as sched

        sched._last_edit[(111, 1001)] = 1.0
        sched._last_edit[(111, 1002)] = 2.0
        sched._last_edit[(222, 2001)] = 3.0

        removed = sched.forget_guild(111)

        assert removed == 2
        assert (111, 1001) not in sched._last_edit
        assert (111, 1002) not in sched._last_edit
        # Guild 222 untouched.
        assert (222, 2001) in sched._last_edit

        # Cleanup
        sched._last_edit.pop((222, 2001), None)

    def test_no_size_gate_in_teardown(self):
        """Cleanup must always run regardless of dict size (DEBT-006)."""
        import inspect

        import guild_lifecycle

        src = inspect.getsource(guild_lifecycle._teardown_scheduler)
        assert (
            "5_000" not in src and "5000" not in src
        ), "guild_lifecycle._teardown_scheduler must not size-gate cleanup"
        assert (
            "_sched_forget" in src or "forget_guild" in src
        ), "_teardown_scheduler must call scheduler.forget_guild(guild_id)"

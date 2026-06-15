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


def _make_pool_stub():
    """Return ``(db_stub, conn_mock)`` mirroring the real asyncpg Pool API.

    asyncpg.Pool exposes ``acquire()`` returning an async-context-manager
    that yields a Connection.  ``Connection.transaction()`` returns its
    own async-context-manager.  This helper assembles a MagicMock graph
    that matches that shape so tests exercise the same call path as
    production rather than a synthetic ``.transaction()`` on the pool.
    """
    conn = MagicMock()
    conn.execute = AsyncMock()

    txn_cm = MagicMock()
    txn_cm.__aenter__ = AsyncMock(return_value=txn_cm)
    txn_cm.__aexit__ = AsyncMock(return_value=False)
    conn.transaction = MagicMock(return_value=txn_cm)

    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)

    pool_stub = MagicMock()
    pool_stub.acquire = MagicMock(return_value=acquire_cm)

    db_stub = MagicMock(get=MagicMock(return_value=pool_stub))
    return db_stub, conn


class TestCacheInvalidatedEmitted:
    """BUG-002 regression — set_visibility must emit both events.

    P1 PR-6 rewrite: the prior version patched seven module attributes
    to exercise the entire pipeline; that broke under any internal
    refactor without protecting the actual contract. The contract is
    just "after a successful set_visibility, EVT_VISIBILITY_CHANGED and
    EVT_CACHE_INVALIDATED both fire, in that order".
    """

    @pytest.mark.asyncio
    async def test_set_visibility_emits_visibility_changed_then_cache_invalidated(
        self,
    ):
        from governance.events import EVT_CACHE_INVALIDATED, EVT_VISIBILITY_CHANGED
        from governance.writes import GovernanceMutationPipeline

        emitted: list[str] = []

        async def capture(event_name, payload):
            emitted.append(event_name)

        # Mock shape mirrors the real asyncpg Pool API: pool.acquire()
        # returns an async-context-manager yielding a Connection, and
        # conn.transaction() returns an async-context-manager.  An older
        # version of this test mocked .transaction() on the pool itself,
        # which hid a production regression where ``pool.transaction()``
        # was called directly — asyncpg.Pool has no such method.
        db_stub, conn = _make_pool_stub()
        db_stub.get_visibility_override = AsyncMock(return_value=None)

        member = MagicMock()
        member.id = 1
        member.guild_permissions.administrator = True
        from governance.models import GovernanceContext

        ctx = GovernanceContext(guild_id=777, channel_id=1, member=member)

        with (
            patch("governance.writes.db", db_stub),
            patch("governance.writes.invalidate_guild_cache"),
            patch("governance.writes._emit_governance_event", side_effect=capture),
            patch("governance.writes.SUBSYSTEMS", {"economy": {}}),
        ):
            await GovernanceMutationPipeline().set_visibility(
                ctx,
                "guild",
                777,
                "economy",
                False,
            )

        assert emitted[:2] == [EVT_VISIBILITY_CHANGED, EVT_CACHE_INVALIDATED]
        # The pipeline must execute SQL on the acquired connection, not on
        # the pool: every transactional write goes through conn.execute.
        assert conn.execute.await_count >= 2, (
            "set_visibility must run both the visibility upsert and the "
            "audit-log insert on the acquired connection (got "
            f"{conn.execute.await_count} conn.execute call(s))."
        )

    @pytest.mark.asyncio
    async def test_set_visibility_uses_connection_transaction_not_pool(self):
        """Pool.transaction() does not exist on asyncpg.Pool — only Connection
        has .transaction().  This test would have caught the production
        regression where pipeline called ``db.get().transaction()`` directly
        on a Pool, raising AttributeError at runtime.
        """
        from governance.writes import GovernanceMutationPipeline

        db_stub, conn = _make_pool_stub()
        db_stub.get_visibility_override = AsyncMock(return_value=None)
        pool_stub = db_stub.get.return_value

        # If production code calls pool.transaction() directly, hasattr is
        # False on the real pool — but a MagicMock would silently create
        # one.  We assert that .transaction is NEVER called on the pool,
        # only on conn (the canonical asyncpg pattern).
        pool_stub.transaction = MagicMock(
            side_effect=AttributeError(
                "'Pool' object has no attribute 'transaction'",
            ),
        )

        member = MagicMock()
        member.id = 1
        member.guild_permissions.administrator = True
        from governance.models import GovernanceContext

        ctx = GovernanceContext(guild_id=778, channel_id=1, member=member)

        async def _noop(*_args, **_kwargs):
            pass

        with (
            patch("governance.writes.db", db_stub),
            patch("governance.writes.invalidate_guild_cache"),
            patch("governance.writes._emit_governance_event", side_effect=_noop),
            patch("governance.writes.SUBSYSTEMS", {"economy": {}}),
        ):
            # Must complete without AttributeError.
            await GovernanceMutationPipeline().set_visibility(
                ctx,
                "guild",
                778,
                "economy",
                True,
            )

        assert (
            pool_stub.transaction.call_count == 0
        ), "Pipeline must not call .transaction() on the pool (asyncpg.Pool has no such method)."
        assert (
            conn.transaction.call_count >= 1
        ), "Pipeline must open the transaction on the acquired connection."

    @pytest.mark.asyncio
    async def test_set_cleanup_policy_uses_connection_transaction(self):
        """Mirrors the visibility-pipeline regression for cleanup_policies —
        both pipeline methods are affected by the same bug class.
        """
        from governance.writes import GovernanceMutationPipeline

        db_stub, conn = _make_pool_stub()
        pool_stub = db_stub.get.return_value
        pool_stub.transaction = MagicMock(
            side_effect=AttributeError(
                "'Pool' object has no attribute 'transaction'",
            ),
        )

        member = MagicMock()
        member.id = 1
        member.guild_permissions.administrator = True
        from governance.models import GovernanceContext

        ctx = GovernanceContext(guild_id=779, channel_id=1, member=member)

        async def _noop(*_args, **_kwargs):
            pass

        with (
            patch("governance.writes.db", db_stub),
            patch("governance.writes.invalidate_guild_cache"),
            patch("governance.writes._emit_governance_event", side_effect=_noop),
        ):
            await GovernanceMutationPipeline().set_cleanup_policy(
                ctx,
                "guild",
                779,
                delete_invalid_commands=True,
                delete_failed_commands=True,
                delete_after_seconds=5,
            )

        assert pool_stub.transaction.call_count == 0
        assert conn.transaction.call_count >= 1
        assert conn.execute.await_count >= 2


# ---------------------------------------------------------------------------
# GAP-001 — panel anchors deleted from DB on guild teardown
# ---------------------------------------------------------------------------


class TestPanelAnchorTeardown:
    @pytest.mark.asyncio
    async def test_guild_lifecycle_deletes_panel_anchors(self):
        """guild_lifecycle.teardown() must call db.delete_guild_panel_anchors."""
        import guild_lifecycle

        guild_id = 4242
        with (
            patch(
                "utils.db.delete_guild_panel_anchors",
                new_callable=AsyncMock,
            ) as mock_del,
            patch(
                "utils.db.delete_sessions_for_guild",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "utils.db.delete_guild_session_state",
                new_callable=AsyncMock,
            ),
        ):
            mock_del.return_value = 3
            await guild_lifecycle.teardown(guild_id)
            mock_del.assert_awaited_once_with(guild_id)

    def test_db_function_signature(self):
        from utils import db as db_module

        assert hasattr(
            db_module, "delete_guild_panel_anchors"
        ), "db.delete_guild_panel_anchors must exist (GAP-001)"


# ---------------------------------------------------------------------------
# PR N1 — navigation_stack.forget is wired into every session deletion path
# ---------------------------------------------------------------------------


class TestNavigationForgetWiring:
    """Every session-deletion path calls navigation_stack.forget so the
    in-process lock dict cannot accumulate stale entries.
    """

    @pytest.mark.asyncio
    async def test_session_manager_remove_calls_forget(self):
        from core.runtime import navigation_stack, session_manager

        forgotten: list[str] = []
        with (
            patch("utils.db.delete_session", new_callable=AsyncMock),
            patch.object(
                navigation_stack,
                "forget",
                side_effect=forgotten.append,
            ),
        ):
            await session_manager.remove("session-abc")
        assert forgotten == ["session-abc"]

    @pytest.mark.asyncio
    async def test_invalidate_subsystem_sessions_forgets_every_id(self):
        from core.runtime import navigation_stack, session_manager

        forgotten: list[str] = []
        with (
            patch(
                "utils.db.delete_sessions_for_scope",
                new_callable=AsyncMock,
                return_value=["sid-1", "sid-2", "sid-3"],
            ),
            patch.object(
                navigation_stack,
                "forget",
                side_effect=forgotten.append,
            ),
        ):
            await session_manager.invalidate_subsystem_sessions(
                guild_id=99,
                subsystem="economy",
                channel_id=None,
            )
        assert forgotten == ["sid-1", "sid-2", "sid-3"]

    @pytest.mark.asyncio
    async def test_session_gc_loop_forgets_every_expired_id(self):
        """One synthetic GC sweep is exercised by patching the
        cancellation point so the loop runs exactly once.
        """
        import asyncio as _asyncio

        from core.runtime import navigation_stack, session_gc

        forgotten: list[str] = []
        expired = ["expired-1", "expired-2"]
        # Force the loop body to run exactly once: first sleep returns
        # immediately, second sleep raises CancelledError to exit.
        sleeps_remaining = [None, _asyncio.CancelledError()]

        async def fake_sleep(_seconds):
            nxt = sleeps_remaining.pop(0)
            if isinstance(nxt, BaseException):
                raise nxt
            return nxt

        with (
            patch.object(session_gc.asyncio, "sleep", side_effect=fake_sleep),
            patch(
                "utils.db.delete_expired_sessions",
                new_callable=AsyncMock,
                return_value=expired,
            ),
            patch(
                "utils.db.delete_stale_panel_anchors",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "utils.db.count_active_sessions",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch.object(
                navigation_stack,
                "forget",
                side_effect=forgotten.append,
            ),
        ):
            with pytest.raises(_asyncio.CancelledError):
                await session_gc._run_gc_loop()
        assert forgotten == expired

    @pytest.mark.asyncio
    async def test_guild_lifecycle_teardown_forgets_every_session_id(self):
        import guild_lifecycle
        from core.runtime import navigation_stack

        forgotten: list[str] = []
        with (
            patch(
                "utils.db.delete_sessions_for_guild",
                new_callable=AsyncMock,
                return_value=["g-sid-1", "g-sid-2"],
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
            patch.object(
                navigation_stack,
                "forget",
                side_effect=forgotten.append,
            ),
        ):
            await guild_lifecycle.teardown(7777)
        assert forgotten == ["g-sid-1", "g-sid-2"]


# NOTE: the former ``TestGameStateGcSweep`` moved to
# ``tests/unit/runtime/test_cleanup_registry.py`` when the stale-game_state
# refund sweep was extracted from session_gc into the game_state cleanup
# provider (RC-7).


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

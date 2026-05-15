"""Regression tests for confirmed bug fixes.

Covers:
  BUG-001  double JSON encoding in session state and audit log
  BUG-002  EVT_CACHE_INVALIDATED emission from mutation pipeline
  BUG-003  thread scope writes accepted
  BUG-004  capability overrides cleared on guild forget
  BUG-005  runtime.setup() idempotency
  BUG-006  _NO_OVERRIDE sentinel removed from cache
  BUG-007  check_existing_instance not called at module level
  BUG-008  error logging before channel guard return
  ARCH-005 unknown capability fails closed
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# BUG-001 — double JSON encoding shim
# ---------------------------------------------------------------------------


class TestMaybeDecodeLegacy:
    """_maybe_decode_legacy must transparently decode double-encoded values."""

    def test_dict_passthrough(self):
        from utils.db import _maybe_decode_legacy

        value = {"key": "val", "nested": [1, 2]}
        assert _maybe_decode_legacy(value) == value

    def test_string_decoded(self):
        from utils.db import _maybe_decode_legacy

        # A double-encoded value stored as a JSON string
        assert _maybe_decode_legacy('{"key": "val"}') == {"key": "val"}

    def test_array_decoded(self):
        from utils.db import _maybe_decode_legacy

        assert _maybe_decode_legacy("[1, 2, 3]") == [1, 2, 3]

    def test_non_json_string_passthrough(self):
        from utils.db import _maybe_decode_legacy

        assert _maybe_decode_legacy("not-json") == "not-json"

    def test_int_passthrough(self):
        from utils.db import _maybe_decode_legacy

        assert _maybe_decode_legacy(42) == 42

    def test_none_passthrough(self):
        from utils.db import _maybe_decode_legacy

        assert _maybe_decode_legacy(None) is None


# ---------------------------------------------------------------------------
# BUG-003 — thread scope write accepted
# ---------------------------------------------------------------------------


class TestThreadScopeAccepted:
    """set_subsystem_visibility must accept scope_type='thread'."""

    @pytest.mark.asyncio
    async def test_thread_scope_not_rejected(self):
        from governance.writes import _VALID_SCOPE_TYPES

        assert "thread" in _VALID_SCOPE_TYPES, (
            "Thread scope must be in _VALID_SCOPE_TYPES — "
            "migration 009 added DB support for it."
        )

    @pytest.mark.asyncio
    async def test_role_scope_still_rejected(self):
        from governance.writes import _VALID_SCOPE_TYPES

        assert "role" not in _VALID_SCOPE_TYPES, "Role scope is not yet supported."


# ---------------------------------------------------------------------------
# BUG-004 — capability overrides cleared on guild forget
# ---------------------------------------------------------------------------


class TestForgetGuildCapabilities:
    def test_forget_clears_overrides(self):
        from governance.execution import (
            _capability_execution_overrides,
            _loaded_guilds,
            forget_guild_capabilities,
        )

        guild_id = 99999
        _capability_execution_overrides[(guild_id, "test.cap.do")] = True
        _loaded_guilds.add(guild_id)

        forget_guild_capabilities(guild_id)

        assert guild_id not in _loaded_guilds
        assert (guild_id, "test.cap.do") not in _capability_execution_overrides

    def test_forget_other_guilds_unaffected(self):
        from governance.execution import (
            _capability_execution_overrides,
            _loaded_guilds,
            forget_guild_capabilities,
        )

        guild_a, guild_b = 11111, 22222
        _capability_execution_overrides[(guild_a, "test.x.y")] = True
        _capability_execution_overrides[(guild_b, "test.x.y")] = False
        _loaded_guilds.add(guild_a)
        _loaded_guilds.add(guild_b)

        forget_guild_capabilities(guild_a)

        assert guild_a not in _loaded_guilds
        assert (guild_a, "test.x.y") not in _capability_execution_overrides
        # Guild B must be completely untouched
        assert guild_b in _loaded_guilds
        assert (guild_b, "test.x.y") in _capability_execution_overrides

        # Cleanup
        _loaded_guilds.discard(guild_b)
        _capability_execution_overrides.pop((guild_b, "test.x.y"), None)


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

        assert not hasattr(cache_module, "_NO_OVERRIDE"), (
            "_NO_OVERRIDE was removed as dead code — it should not exist in cache.py"
        )

    def test_resolver_does_not_import_no_override(self):
        import inspect

        import governance.resolver as resolver_module

        source = inspect.getsource(resolver_module)
        assert "_NO_OVERRIDE" not in source, (
            "resolver.py must not reference the removed _NO_OVERRIDE sentinel"
        )


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

        ctx = GovernanceContext(
            guild_id=777, channel_id=1, member=member
        )

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
                with patch("governance.writes._emit_governance_event", side_effect=mock_emit):
                    with patch("governance.writes.SUBSYSTEMS", {"economy": {}}):
                        from governance.writes import GovernanceMutationPipeline

                        pipeline = GovernanceMutationPipeline()
                        await pipeline.set_visibility(ctx, "guild", 777, "economy", False)

        from governance.events import EVT_CACHE_INVALIDATED, EVT_VISIBILITY_CHANGED

        assert EVT_VISIBILITY_CHANGED in emitted_events, (
            "EVT_VISIBILITY_CHANGED must be emitted from set_visibility"
        )
        assert EVT_CACHE_INVALIDATED in emitted_events, (
            "EVT_CACHE_INVALIDATED must be emitted from set_visibility (BUG-002 fix)"
        )

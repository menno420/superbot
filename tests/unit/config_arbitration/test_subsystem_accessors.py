"""Phase 2 PR-7 — per-subsystem convenience accessors.

The accessors collapse the migrated-key arguments to ``read_config``
into a single call.  Tests verify:

* Each accessor passes the correct subsystem / binding_name /
  legacy_key / binding_kind to ``read_config``.
* The value is normalized to the expected type (``str`` for XP
  announce channel, ``int`` for economy log channel and trusted-tier
  role).
* Unparseable legacy strings on int-valued accessors become
  ``source='missing'`` with a diagnostic explaining the parse failure.
* Counters from ``read_config`` continue to accumulate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from core.resources.status import ResourceStatus
from core.runtime import config_arbitration
from core.runtime.bindings import BindingValue
from core.runtime.config_arbitration import (
    get_economy_log_channel,
    get_trusted_tier_role,
    get_xp_announce_channel,
)
from core.runtime.subsystem_schema import BindingKind


@pytest.fixture(autouse=True)
def _reset_counters():
    config_arbitration._reset_counters_for_tests()
    yield
    config_arbitration._reset_counters_for_tests()


def _bv(*, kind, target_id, status):
    return BindingValue(
        guild_id=1,
        subsystem="x",
        binding_name="y",
        kind=kind,
        target_id=target_id,
        status=status,
        last_validated_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        version=1,
    )


# ---------------------------------------------------------------------------
# get_xp_announce_channel — legacy str pass-through; binding int stringified
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_xp_announce_channel_reads_binding_first_even_when_flag_off():
    """Retired pointer (P0-3): the accessor forces binding-first and the
    binding int is stringified — regardless of the global ``bindings.primary``
    flag, which is *not even consulted*.
    """
    is_enabled = AsyncMock(return_value=False)  # global flag OFF
    with (
        patch("core.runtime.feature_flags.is_enabled", new=is_enabled),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(
                kind=BindingKind.CHANNEL,
                target_id=999999,
                status=ResourceStatus.BOUND,
            ),
        ),
    ):
        result = await get_xp_announce_channel(guild_id=1)
    assert result.value == "999999"
    assert isinstance(result.value, str)
    assert result.source == "binding"
    is_enabled.assert_not_awaited()  # retired pointer bypasses the flag


@pytest.mark.asyncio
async def test_xp_announce_channel_falls_back_to_legacy_when_unbound():
    """Binding unbound → legacy KV is the rollback fallback (string)."""
    with (
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(
                kind=BindingKind.CHANNEL,
                target_id=None,
                status=ResourceStatus.UNRESOLVED,
            ),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="123456",
        ),
    ):
        result = await get_xp_announce_channel(guild_id=1)
    assert result.value == "123456"
    assert isinstance(result.value, str)
    assert result.source == "fallback"


@pytest.mark.asyncio
async def test_xp_announce_channel_missing_returns_none():
    with (
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(
                kind=BindingKind.CHANNEL,
                target_id=None,
                status=ResourceStatus.UNRESOLVED,
            ),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="",
        ),
    ):
        result = await get_xp_announce_channel(guild_id=1)
    assert result.value is None
    assert result.source == "missing"


# ---------------------------------------------------------------------------
# get_economy_log_channel — value coerced to int|None
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_economy_log_channel_reads_binding_first_even_when_flag_off():
    """Retired pointer (P0-3): binding-first int, flag bypassed."""
    is_enabled = AsyncMock(return_value=False)
    with (
        patch("core.runtime.feature_flags.is_enabled", new=is_enabled),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(
                kind=BindingKind.CHANNEL,
                target_id=999,
                status=ResourceStatus.BOUND,
            ),
        ),
    ):
        result = await get_economy_log_channel(guild_id=1)
    assert result.value == 999
    assert isinstance(result.value, int)
    assert result.source == "binding"
    is_enabled.assert_not_awaited()


@pytest.mark.asyncio
async def test_economy_log_channel_falls_back_to_legacy_when_unbound():
    """Binding unbound → legacy KV fallback, parsed to int."""
    with (
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(
                kind=BindingKind.CHANNEL,
                target_id=None,
                status=ResourceStatus.UNRESOLVED,
            ),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="777777",
        ),
    ):
        result = await get_economy_log_channel(guild_id=1)
    assert result.value == 777777
    assert isinstance(result.value, int)
    assert result.source == "fallback"


@pytest.mark.asyncio
async def test_economy_log_channel_unparseable_legacy_becomes_missing():
    """A legacy KV holding junk that can't be int-parsed should not crash."""
    with (
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(
                kind=BindingKind.CHANNEL,
                target_id=None,
                status=ResourceStatus.UNRESOLVED,
            ),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="not-a-number",
        ),
    ):
        result = await get_economy_log_channel(guild_id=1)
    assert result.value is None
    assert result.source == "missing"
    assert any("could not be parsed as int" in d for d in result.diagnostics)


# ---------------------------------------------------------------------------
# get_trusted_tier_role — value coerced to int|None, kind=role
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trusted_tier_role_passes_role_kind_to_read_config():
    """The accessor MUST declare binding_kind='role' so kind drift is caught.

    The XP/economy accessors declare 'channel'; this one must declare
    'role' or a future schema mistake (binding declared as channel)
    would be silently accepted.
    """
    with patch(
        "core.runtime.config_arbitration.read_config",
        new_callable=AsyncMock,
    ) as mock_read:
        mock_read.return_value = config_arbitration.ConfigReadResult(
            value=None,
            source="missing",
            binding_status="n/a",
            flag_state="off",
            diagnostics=[],
        )
        await get_trusted_tier_role(guild_id=1)
    call = mock_read.await_args
    assert call.kwargs["subsystem"] == "governance"
    assert call.kwargs["binding_name"] == "trusted_role"
    assert call.kwargs["legacy_key"] == "trusted_tier_role_id"
    assert call.kwargs["binding_kind"] == "role"


@pytest.mark.asyncio
async def test_trusted_tier_role_legacy_int_returned():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="111222333",
        ),
    ):
        result = await get_trusted_tier_role(guild_id=1)
    assert result.value == 111222333


# ---------------------------------------------------------------------------
# Counters accumulate across accessors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_counters_increment_across_accessors():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(
                kind=BindingKind.CHANNEL,
                target_id=None,
                status=ResourceStatus.UNRESOLVED,
            ),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="123",
        ),
    ):
        await get_xp_announce_channel(guild_id=1)  # retired → forced binding-first
        await get_economy_log_channel(guild_id=1)  # retired → forced binding-first
        await get_trusted_tier_role(guild_id=1)  # flag-gated → honours OFF flag
    snap = config_arbitration.counters_snapshot()
    assert snap["calls_total"] == 3
    # The two retired pointers force binding-primary (flag_state on, falling
    # back to legacy as the binding is unbound); the governance role pointer
    # still honours the (off) global flag.
    assert snap["by_flag_state"]["on"] == 2
    assert snap["by_flag_state"]["off"] == 1

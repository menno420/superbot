"""Phase 2 PR-4 — central read-source arbitration.

Verifies the resolution ladder for ``read_config``:

* flag OFF → legacy (binding never consulted)
* flag ON + binding BOUND → binding value
* flag ON + binding MISSING/INVALID/UNRESOLVED → legacy fallback
* flag ON + neither legacy nor binding produced a value → missing
* failure isolation: ``is_enabled`` raising falls back to legacy;
  ``get_binding`` raising falls back to legacy.

Also pins:
* No cache layer added by the arbitration helper itself.
* Counters accumulate for the diagnostics provider.
* ``ConfigReadResult`` carries provenance fields needed by setup-wizard
  previews and the future ``!platform consistency`` view.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from core.resources.status import ResourceStatus
from core.runtime import config_arbitration
from core.runtime.bindings import BindingValue
from core.runtime.config_arbitration import ConfigReadResult, read_config
from core.runtime.subsystem_schema import BindingKind


@pytest.fixture(autouse=True)
def _reset_counters():
    config_arbitration._reset_counters_for_tests()
    yield
    config_arbitration._reset_counters_for_tests()


def _bv(*, target_id: int | None, status: ResourceStatus) -> BindingValue:
    return BindingValue(
        guild_id=1,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
        target_id=target_id,
        status=status,
        last_validated_at=datetime.now(timezone.utc),
        last_updated_at=datetime.now(timezone.utc),
        version=1,
    )


# ---------------------------------------------------------------------------
# Flag OFF → legacy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flag_off_returns_legacy_value_binding_not_consulted():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
        ) as mock_binding,
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="12345",
        ),
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert result == ConfigReadResult(
        value="12345",
        source="legacy",
        binding_status="n/a",
        flag_state="off",
        diagnostics=[],
    )
    mock_binding.assert_not_awaited()


@pytest.mark.asyncio
async def test_flag_off_legacy_missing_returns_none_with_missing_source():
    """Flag OFF + legacy empty → source='missing' (PR-4 review correction).

    The earlier behavior returned ``source='legacy'`` because legacy
    was where the ``None`` came from.  The review pointed out that
    this makes the ``!platform consistency`` "how many guilds have
    nothing configured?" query painful — operators would have to
    filter by ``(source=='legacy' AND value is None)`` instead of a
    single counter.  ``source='missing'`` is now returned whenever
    the resolved value is ``None``, regardless of which side produced
    it; ``flag_state`` and ``binding_status`` carry the distinguishing
    context.
    """
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="",
        ),
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert result.value is None
    assert result.source == "missing"
    assert result.flag_state == "off"
    assert result.binding_status == "n/a"


# ---------------------------------------------------------------------------
# Binding-kind verification (PR-4 enhancement)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_binding_kind_match_returns_binding_source():
    """Caller-declared kind matches the binding's declared kind → binding wins."""
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=999, status=ResourceStatus.BOUND),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
        ) as mock_legacy,
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
            binding_kind="channel",
        )
    assert result.value == 999
    assert result.source == "binding"
    assert result.binding_status == "bound"
    mock_legacy.assert_not_awaited()


@pytest.mark.asyncio
async def test_binding_kind_mismatch_falls_back_with_drift_diagnostic():
    """Caller asked for 'role' but the binding declares 'channel' → fallback.

    A kind drift means schema and runtime disagree (a future schema
    change reshaped the binding); the safest behavior is to treat the
    binding as INVALID and fall back to legacy.  The drift is recorded
    in ``diagnostics`` so ``!platform consistency`` can surface it.
    """
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=999, status=ResourceStatus.BOUND),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="legacy-value",
        ),
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
            binding_kind="role",
        )
    assert result.value == "legacy-value"
    assert result.source == "fallback"
    assert any("binding kind drift" in d for d in result.diagnostics)


@pytest.mark.asyncio
async def test_binding_kind_omitted_does_not_verify():
    """When no expected kind is supplied, the binding wins as before."""
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=999, status=ResourceStatus.BOUND),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
        ),
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
            # binding_kind intentionally omitted
        )
    assert result.source == "binding"
    assert not any("kind drift" in d for d in result.diagnostics)


# ---------------------------------------------------------------------------
# Flag ON + binding BOUND
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flag_on_binding_bound_returns_binding_value():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=999, status=ResourceStatus.BOUND),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
        ) as mock_legacy,
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert result.value == 999
    assert result.source == "binding"
    assert result.binding_status == "bound"
    assert result.flag_state == "on"
    # Legacy must not be consulted when binding is BOUND
    mock_legacy.assert_not_awaited()


# ---------------------------------------------------------------------------
# Flag ON + binding MISSING/INVALID/UNRESOLVED → fallback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "binding_status",
    [
        ResourceStatus.MISSING,
        ResourceStatus.INVALID,
        ResourceStatus.UNRESOLVED,
    ],
)
@pytest.mark.asyncio
async def test_flag_on_binding_not_bound_falls_back_to_legacy(binding_status):
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=None, status=binding_status),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="legacy-value",
        ),
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert result.value == "legacy-value"
    assert result.source == "fallback"
    assert result.binding_status == binding_status.value
    assert result.flag_state == "on"
    assert any("binding not bound" in d for d in result.diagnostics)


@pytest.mark.asyncio
async def test_flag_on_both_empty_returns_missing():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            return_value=_bv(target_id=None, status=ResourceStatus.UNRESOLVED),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="",
        ),
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert result.value is None
    assert result.source == "missing"


# ---------------------------------------------------------------------------
# Failure isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_enabled_failure_falls_back_to_legacy_off_path():
    """If is_enabled raises, arbitration treats the flag as OFF."""
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            side_effect=RuntimeError("evaluator crashed"),
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
        ) as mock_binding,
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="legacy-value",
        ),
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert result.source == "legacy"
    assert result.flag_state == "off"
    assert any("is_enabled raised" in d for d in result.diagnostics)
    mock_binding.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_binding_failure_falls_back_to_legacy():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="legacy-value",
        ),
    ):
        result = await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
    assert result.value == "legacy-value"
    assert result.source == "fallback"
    assert result.flag_state == "on"
    assert any("get_binding raised" in d for d in result.diagnostics)


# ---------------------------------------------------------------------------
# Counters + diagnostics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_counters_increment_per_call():
    with (
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="x",
        ),
    ):
        await read_config(
            guild_id=1,
            subsystem="xp",
            binding_name="announce_channel",
            legacy_key="xp_announce_channel",
        )
        await read_config(
            guild_id=2,
            subsystem="economy",
            binding_name="log_channel",
            legacy_key="economy_log_channel",
        )
    snap = config_arbitration.counters_snapshot()
    assert snap["calls_total"] == 2
    assert snap["by_source"]["legacy"] == 2
    assert snap["by_flag_state"]["off"] == 2


def test_diagnostics_provider_registered():
    """!platform consistency consumer reads the counters via this provider."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("config_arbitration")
    assert "arbitration" in snap
    assert "calls_total" in snap["arbitration"]
    assert "by_source" in snap["arbitration"]

"""Unit tests for the global settings tier in services.settings_resolution.

The resolver resolves a scalar ``SettingSpec`` per-guild row → **global
row** (``guild_id = GLOBAL_GUILD_ID``, the owner's cross-server default)
→ declared default. These tests pin that inheritance, the ``global_kv``
provenance, the coercion/validation parity with the per-guild tier, and
the ``include_global=False`` opt-out the mutation pipeline relies on.

Each assertion fails against the pre-change (per-guild-only) behavior.
"""

from __future__ import annotations

import pytest

from core.runtime import guild_config
from core.runtime import subsystem_schema as schema_mod
from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema
from services import settings_resolution as sr_mod
from services.settings_resolution import counters_snapshot, resolve_setting
from utils import db as db_pkg
from utils.db import settings as settings_db
from utils.db.settings import GLOBAL_GUILD_ID

GUILD = 1234


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    sr_mod._reset_counters_for_tests()
    guild_config._reset_for_tests()

    _kv: dict[tuple[int, str], str] = {}

    async def _fake_get_setting(
        guild_id: int,
        key: str,
        default: str = "",
    ) -> str:
        return _kv.get((guild_id, key), default)

    monkeypatch.setattr(settings_db, "get_setting", _fake_get_setting)
    monkeypatch.setattr(db_pkg, "get_setting", _fake_get_setting)

    yield {"kv": _kv}

    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    sr_mod._reset_counters_for_tests()
    guild_config._reset_for_tests()


def _register(subsystem: str, *specs: SettingSpec) -> None:
    schema_mod.register(SubsystemSchema(subsystem=subsystem, settings=specs))


def _xp_min() -> None:
    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=15,
            settings_key="XP_MIN",
        ),
    )


# ---------------------------------------------------------------------------
# Global tier fires only on a per-guild miss
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_global_row_drives_value_on_per_guild_miss(_reset_state):
    _xp_min()
    _reset_state["kv"][(GLOBAL_GUILD_ID, "XP_MIN")] = "42"
    # No per-guild row → inherit the global value.
    result = await resolve_setting(GUILD, "xp", "xp_min")
    assert result is not None
    assert result.value == 42
    assert result.provenance == "global_kv"
    assert result.raw == "42"
    assert result.valid is True


@pytest.mark.asyncio
async def test_per_guild_row_wins_over_global(_reset_state):
    _xp_min()
    _reset_state["kv"][(GLOBAL_GUILD_ID, "XP_MIN")] = "42"
    _reset_state["kv"][(GUILD, "XP_MIN")] = "7"
    result = await resolve_setting(GUILD, "xp", "xp_min")
    assert result is not None
    assert result.value == 7
    assert result.provenance == "legacy_kv"


@pytest.mark.asyncio
async def test_no_row_anywhere_falls_back_to_default(_reset_state):
    _xp_min()
    result = await resolve_setting(GUILD, "xp", "xp_min")
    assert result is not None
    assert result.value == 15
    assert result.provenance == "default"
    # The empty per-guild read is preserved as raw="" (byte-identical
    # to the prior per-guild-only contract).
    assert result.raw == ""


# ---------------------------------------------------------------------------
# Coercion / validation parity with the per-guild tier
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_malformed_global_row_falls_back_to_default_invalid(_reset_state):
    _xp_min()
    _reset_state["kv"][(GLOBAL_GUILD_ID, "XP_MIN")] = "not-an-int"
    result = await resolve_setting(GUILD, "xp", "xp_min")
    assert result is not None
    assert result.value == 15  # spec default
    assert result.provenance == "global_kv"
    assert result.valid is False
    assert result.diagnostics  # records the coercion failure


@pytest.mark.asyncio
async def test_global_row_runs_the_validator(_reset_state):
    def _reject_negatives(v: int) -> None:
        if v < 0:
            raise ValueError("must be non-negative")

    _register(
        "xp",
        SettingSpec(
            name="xp_min",
            value_type=int,
            default=15,
            settings_key="XP_MIN",
            validator=_reject_negatives,
        ),
    )
    _reset_state["kv"][(GLOBAL_GUILD_ID, "XP_MIN")] = "-5"
    result = await resolve_setting(GUILD, "xp", "xp_min")
    assert result is not None
    assert result.value == 15
    assert result.provenance == "global_kv"
    assert result.valid is False


# ---------------------------------------------------------------------------
# include_global=False — the mutation-pipeline scope-local contract
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_include_global_false_suppresses_inheritance(_reset_state):
    _xp_min()
    _reset_state["kv"][(GLOBAL_GUILD_ID, "XP_MIN")] = "42"
    # A per-guild miss with the global tier suppressed → the declared
    # default, NOT the global value. This is what _read_previous relies on.
    result = await resolve_setting(GUILD, "xp", "xp_min", include_global=False)
    assert result is not None
    assert result.value == 15
    assert result.provenance == "default"
    assert result.raw == ""


@pytest.mark.asyncio
async def test_resolving_at_global_sentinel_reads_its_own_row(_reset_state):
    _xp_min()
    _reset_state["kv"][(GLOBAL_GUILD_ID, "XP_MIN")] = "42"
    # Resolving *at* guild 0 reads the global row as its per-guild row and
    # never self-inherits (no infinite/duplicate global read).
    result = await resolve_setting(GLOBAL_GUILD_ID, "xp", "xp_min")
    assert result is not None
    assert result.value == 42
    assert result.provenance == "legacy_kv"


# ---------------------------------------------------------------------------
# Counters track the new provenance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_global_kv_provenance_counter_increments(_reset_state):
    _xp_min()
    _reset_state["kv"][(GLOBAL_GUILD_ID, "XP_MIN")] = "42"
    await resolve_setting(GUILD, "xp", "xp_min")
    snap = counters_snapshot()
    assert snap["by_provenance"]["global_kv"] == 1
    assert snap["by_provenance"]["legacy_kv"] == 0

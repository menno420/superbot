"""``!platform setting`` detail + enriched ``settings-registry`` (PR3).

Both surfaces reuse the existing ``SettingResolution`` from
``services.settings_resolution`` rather than inventing a command-specific
shape, so the tests feed crafted resolutions and assert the rendering.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.diagnostic._platform_embeds import (
    build_setting_detail_embed,
    build_settings_registry_embed,
)
from services.settings_resolution import SettingResolution


def _guild(gid: int = 7) -> MagicMock:
    guild = MagicMock()
    guild.id = gid
    return guild


# ---------------------------------------------------------------------------
# build_setting_detail_embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setting_detail_renders_resolution_fields():
    res = SettingResolution(
        subsystem="xp",
        name="xp_min",
        value=15,
        provenance="legacy_kv",
        default=15,
        valid=True,
        raw="15",
        diagnostics=(),
    )
    with patch(
        "services.settings_resolution.resolve_setting",
        AsyncMock(return_value=res),
    ):
        embed = await build_setting_detail_embed(_guild(), "xp", "xp_min")
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Value"] == "`15`"
    assert fields["Provenance"] == "`legacy_kv`"
    assert fields["Default"] == "`15`"
    assert "yes" in fields["Valid"]
    assert fields["Raw KV"] == "`15`"


@pytest.mark.asyncio
async def test_setting_detail_flags_invalid_value_and_diagnostics():
    res = SettingResolution(
        subsystem="xp",
        name="xp_min",
        value=15,
        provenance="legacy_kv",
        default=15,
        valid=False,
        raw="-3",
        diagnostics=("validator rejected value: out of range",),
    )
    with patch(
        "services.settings_resolution.resolve_setting",
        AsyncMock(return_value=res),
    ):
        embed = await build_setting_detail_embed(_guild(), "xp", "xp_min")
    fields = {f.name: f.value for f in embed.fields}
    assert "no" in fields["Valid"]
    assert "Diagnostics" in fields


@pytest.mark.asyncio
async def test_setting_detail_unknown_setting_is_clear_not_a_crash():
    with patch(
        "services.settings_resolution.resolve_setting",
        AsyncMock(return_value=None),
    ):
        embed = await build_setting_detail_embed(_guild(), "nope", "missing")
    assert "Unknown setting" in (embed.title or "")


# ---------------------------------------------------------------------------
# build_settings_registry_embed — per-guild enrichment
# ---------------------------------------------------------------------------


_SNAP = {
    "status": "built",
    "version": 1,
    "entry_count": 2,
    "subsystems": 1,
    "findings_total": 0,
    "by_subsystem": {"xp": 2},
    "findings": {},
}


@pytest.mark.asyncio
async def test_registry_embed_lists_per_guild_values_when_guild_given():
    resolutions = (
        SettingResolution("xp", "xp_min", 15, "legacy_kv", 15, True, "15", ()),
        SettingResolution("xp", "xp_max", 25, "default", 25, True, None, ()),
    )
    with (
        patch(
            "services.diagnostics_service.snapshot",
            return_value=dict(_SNAP),
        ),
        patch(
            "services.settings_resolution.resolve_batch",
            AsyncMock(return_value=resolutions),
        ),
    ):
        embed = await build_settings_registry_embed(_guild())
    field_names = [f.name for f in embed.fields]
    assert "xp" in field_names
    xp_field = next(f for f in embed.fields if f.name == "xp")
    assert "xp_min" in xp_field.value
    assert "src=legacy_kv" in xp_field.value


@pytest.mark.asyncio
async def test_registry_embed_counts_only_without_guild():
    with patch("services.diagnostics_service.snapshot", return_value=dict(_SNAP)):
        embed = await build_settings_registry_embed(None)
    field_names = [f.name for f in embed.fields]
    assert "By subsystem" in field_names
    assert "xp" not in field_names  # no per-value field without a guild


# ---------------------------------------------------------------------------
# Command wiring
# ---------------------------------------------------------------------------


def test_platform_setting_command_exists():
    from cogs.diagnostic_cog import DiagnosticCog

    sub = DiagnosticCog.platform_grp.get_command("setting")
    assert sub is not None
    assert sub.name == "setting"

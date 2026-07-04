"""Unit tests for the counter config read model (services.counter_config)."""

from __future__ import annotations

import pytest

from services import counter_config
from services.counter_config import CounterPolicy, parse_id, render_counter_name


def test_parse_id_tolerant():
    assert parse_id("42") == 42
    assert parse_id("") is None
    assert parse_id(None) is None
    assert parse_id("nope") is None


def test_render_counter_name_expands_and_caps():
    assert render_counter_name("👥 Members: {count}", 1235) == "👥 Members: 1,235"
    # Stray brace renders literally (injection-safe).
    assert render_counter_name("x {y} {count}", 3) == "x {y} 3"
    # Capped at Discord's 100-char channel-name limit.
    long = render_counter_name("z" * 200 + "{count}", 1)
    assert len(long) <= counter_config.MAX_CHANNEL_NAME_LENGTH


def test_active_requires_master_switch():
    bound = CounterPolicy(total_channel_id=10, humans_channel_id=20)
    # Master off → maintains nothing even with channels bound.
    assert CounterPolicy(enabled=False, total_channel_id=10).active == ()
    assert not CounterPolicy(enabled=False, total_channel_id=10).any_bound
    # Master on → only the bound counters are active, in kind order.
    on = CounterPolicy(enabled=True, total_channel_id=10, humans_channel_id=20)
    assert on.any_bound
    kinds = [k for k, _cid, _tpl in on.active]
    assert kinds == [counter_config.KIND_TOTAL, counter_config.KIND_HUMANS]
    # The unbound bots counter is absent.
    assert all(k != counter_config.KIND_BOTS for k, _c, _t in on.active)
    assert bound  # constructed fine without enabled


def test_defaults_master_off_unbound():
    pol = CounterPolicy()
    assert pol.enabled is False
    assert pol.total_channel_id is None
    assert not pol.any_bound


@pytest.mark.asyncio
async def test_load_policy_composes_typed_values(monkeypatch):
    stored = {
        "enabled": True,
        "total_channel": "100",
        "bots_channel": "300",
        "total_template": "M: {count}",
    }

    async def fake_resolve(guild_id, subsystem, name, fallback):
        assert subsystem == "counters"
        return stored.get(name, fallback)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    pol = await counter_config.load_policy(guild_id=1)
    assert pol.enabled is True
    assert pol.total_channel_id == 100
    assert pol.bots_channel_id == 300
    assert pol.humans_channel_id is None  # unset → unbound
    assert pol.total_template == "M: {count}"
    # Two bound counters (total + bots), humans skipped.
    assert {k for k, _c, _t in pol.active} == {
        counter_config.KIND_TOTAL,
        counter_config.KIND_BOTS,
    }


# ---------------------------------------------------------------------------
# Template presets (completion punch #1)
# ---------------------------------------------------------------------------


def test_default_preset_is_byte_identical_to_canonical_defaults():
    default = counter_config.get_preset("default")
    assert default is not None
    assert default.template_for(counter_config.KIND_TOTAL) == (
        counter_config.DEFAULT_TOTAL_TEMPLATE
    )
    assert default.template_for(counter_config.KIND_HUMANS) == (
        counter_config.DEFAULT_HUMANS_TEMPLATE
    )
    assert default.template_for(counter_config.KIND_BOTS) == (
        counter_config.DEFAULT_BOTS_TEMPLATE
    )


def test_get_preset_is_case_insensitive_and_tolerant():
    assert counter_config.get_preset("MINIMAL") is counter_config.get_preset("minimal")
    assert counter_config.get_preset("  brackets  ") is not None
    assert counter_config.get_preset("does-not-exist") is None


def test_every_preset_covers_every_kind_within_caps():
    keys = {p.key for p in counter_config.TEMPLATE_PRESETS}
    # Keys are unique and there is at least the curated set.
    assert len(keys) == len(counter_config.TEMPLATE_PRESETS) >= 4
    for preset in counter_config.TEMPLATE_PRESETS:
        for kind in counter_config.KINDS:
            template = preset.template_for(kind)
            assert "{count}" in template
            assert 0 < len(template) <= counter_config.MAX_TEMPLATE_LENGTH
            # Rendered name stays within Discord's channel-name limit.
            rendered = counter_config.render_counter_name(template, 123_456)
            assert len(rendered) <= counter_config.MAX_CHANNEL_NAME_LENGTH


def test_preset_setting_writes_maps_kinds_to_template_settings():
    preset = counter_config.get_preset("minimal")
    assert preset is not None
    writes = dict(counter_config.preset_setting_writes(preset))
    # One write per template SettingSpec, mapped from the kind's template.
    assert writes == {
        "total_template": preset.template_for(counter_config.KIND_TOTAL),
        "humans_template": preset.template_for(counter_config.KIND_HUMANS),
        "bots_template": preset.template_for(counter_config.KIND_BOTS),
    }
    # The setting names match the declared template SettingSpecs.
    from cogs.counters.schemas import COUNTERS_SETTINGS

    declared = {s.name for s in COUNTERS_SETTINGS}
    assert set(writes) <= declared

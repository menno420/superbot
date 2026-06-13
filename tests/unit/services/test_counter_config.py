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

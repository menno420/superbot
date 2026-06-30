"""Tests for the CountersCog surface — preset apply, preset list, slash status.

Completion-cert deepening (Q-0209): punch #1 (preset templates) and #2 (slash
surface).  The command callbacks are invoked directly (``.callback``) on an
``__new__``-constructed cog so no Bot is required.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.counters_cog import CountersCog
from services import counter_config


def _cog() -> CountersCog:
    cog = CountersCog.__new__(CountersCog)  # bypass __init__ (needs a Bot)
    return cog


def _ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.guild = MagicMock(id=42)
    ctx.author = MagicMock(id=7)
    ctx.send = AsyncMock()
    return ctx


# ---------------------------------------------------------------------------
# !counterpreset — list (no name) and unknown-name paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_counterpreset_no_name_lists_presets():
    cog, ctx = _cog(), _ctx()
    await cog.counter_preset.callback(cog, ctx, None)
    ctx.send.assert_awaited_once()
    embed = ctx.send.await_args.kwargs["embed"]
    # Every curated preset key is named in the listing.
    for preset in counter_config.TEMPLATE_PRESETS:
        assert f"`{preset.key}`" in embed.description


@pytest.mark.asyncio
async def test_counterpreset_unknown_name_is_rejected(monkeypatch):
    cog, ctx = _cog(), _ctx()
    import services.settings_mutation as sm

    pipeline_ctor = MagicMock()
    monkeypatch.setattr(sm, "SettingsMutationPipeline", pipeline_ctor)

    await cog.counter_preset.callback(cog, ctx, "nonsense")
    msg = ctx.send.await_args.args[0]
    assert "Unknown preset" in msg
    # No mutation pipeline is even constructed for an unknown preset.
    pipeline_ctor.assert_not_called()


# ---------------------------------------------------------------------------
# !counterpreset <name> — applies through the audited mutation pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_counterpreset_applies_through_pipeline(monkeypatch):
    cog, ctx = _cog(), _ctx()
    import services.settings_mutation as sm

    fake_pipeline = MagicMock()
    fake_pipeline.set_value = AsyncMock()
    monkeypatch.setattr(sm, "SettingsMutationPipeline", lambda: fake_pipeline)

    await cog.counter_preset.callback(cog, ctx, "minimal")

    preset = counter_config.get_preset("minimal")
    expected = counter_config.preset_setting_writes(preset)
    # One pipeline write per template setting, in kind order, with the cog's
    # guild + author as actor (so the capability check runs against the caller).
    assert fake_pipeline.set_value.await_count == len(expected)
    for call, (setting_name, template) in zip(
        fake_pipeline.set_value.await_args_list,
        expected,
    ):
        guild, subsystem, name, value, actor = call.args
        assert guild is ctx.guild
        assert subsystem == counter_config.SUBSYSTEM
        assert name == setting_name
        assert value == template
        assert actor is ctx.author
    assert "Applied" in ctx.send.await_args.args[0]


@pytest.mark.asyncio
async def test_counterpreset_reports_mutation_error(monkeypatch):
    cog, ctx = _cog(), _ctx()
    import services.settings_mutation as sm

    fake_pipeline = MagicMock()
    fake_pipeline.set_value = AsyncMock(
        side_effect=sm.SettingsValidationError("nope"),
    )
    monkeypatch.setattr(sm, "SettingsMutationPipeline", lambda: fake_pipeline)

    await cog.counter_preset.callback(cog, ctx, "default")
    msg = ctx.send.await_args.args[0]
    assert "Could not apply preset" in msg


# ---------------------------------------------------------------------------
# /counters — slash status surface (punch #2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_counters_slash_renders_status(monkeypatch):
    cog = _cog()
    interaction = MagicMock()
    interaction.guild = MagicMock(id=42)
    interaction.response.send_message = AsyncMock()

    monkeypatch.setattr(
        counter_config,
        "load_policy",
        AsyncMock(return_value=counter_config.CounterPolicy()),
    )
    monkeypatch.setattr(
        CountersCog,
        "_policy_embed",
        staticmethod(lambda guild, policy: MagicMock(name="embed")),
    )

    await cog.counters_slash.callback(cog, interaction)
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_counters_slash_outside_guild_is_graceful():
    cog = _cog()
    interaction = MagicMock()
    interaction.guild = None
    interaction.response.send_message = AsyncMock()

    await cog.counters_slash.callback(cog, interaction)
    msg = interaction.response.send_message.await_args.args[0]
    assert "only available in a server" in msg


# ---------------------------------------------------------------------------
# _counter_sync_loop — per-guild backoff wiring (completion cert punch #3)
# ---------------------------------------------------------------------------


def _loop_cog(guild_ids: list[int]) -> CountersCog:
    from services import counter_service

    cog = CountersCog.__new__(CountersCog)
    cog.bot = MagicMock()
    cog.bot.guilds = [MagicMock(id=gid) for gid in guild_ids]
    cog._backoff = counter_service.GuildSyncBackoff()
    return cog


@pytest.mark.asyncio
async def test_loop_skips_a_failing_guild_on_the_next_tick(monkeypatch):
    from services import counter_service

    cog = _loop_cog([1])
    sync = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(counter_service, "sync_guild", sync)

    # Tick 1: attempted (raises) → records a failure → cooldown 1 tick.
    await cog._counter_sync_loop.coro(cog)
    assert sync.await_count == 1
    assert cog._backoff.fail_streak(1) == 1

    # Tick 2: skipped (backed off) — sync_guild not called again.
    await cog._counter_sync_loop.coro(cog)
    assert sync.await_count == 1

    # Tick 3: eligible again, retried.
    await cog._counter_sync_loop.coro(cog)
    assert sync.await_count == 2


@pytest.mark.asyncio
async def test_loop_success_keeps_a_healthy_guild_attempted_every_tick(monkeypatch):
    from services import counter_service

    cog = _loop_cog([1])
    sync = AsyncMock(return_value=0)
    monkeypatch.setattr(counter_service, "sync_guild", sync)

    await cog._counter_sync_loop.coro(cog)
    await cog._counter_sync_loop.coro(cog)
    # A clean sync never backs off → attempted on every tick.
    assert sync.await_count == 2
    assert cog._backoff.fail_streak(1) == 0

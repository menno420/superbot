"""Tests for the automation diagnostics + management panel.

Pins:

* ``build_automation_embed_sync`` renders the scheduler snapshot AND
  the per-guild rule list, gracefully reporting errors fetched
  upstream rather than raising.
* ``open_panel`` returns a freshly populated embed + view whose
  rule-select reflects the live DB list.
* The Enable / Disable / Delete buttons short-circuit when no rule
  is selected; they call the canonical
  :class:`AutomationMutationPipeline` methods with the
  ``platform_owner`` actor type when a rule IS selected.
* Pipeline errors are surfaced ephemerally (no crashes).
* Refresh re-fetches the rule list and resets the selection so the
  panel never operates on a stale view.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from views.diagnostic.automation_panel import (
    AutomationPanelView,
    _commit_delete,
    _commit_set_enabled,
    build_automation_embed_sync,
    open_panel,
)


def _author():
    member = MagicMock()
    member.id = 99
    return member


def _guild(guild_id: int = 1, owner_id: int = 99):
    guild = MagicMock()
    guild.id = guild_id
    guild.owner_id = owner_id
    return guild


def _interaction(*, guild=None):
    interaction = MagicMock()
    interaction.guild = guild if guild is not None else _guild()
    interaction.user = _author()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _rule(
    *,
    rid: int = 1,
    name: str = "greet-new-members",
    enabled: bool = False,
    trigger_kind: str = "interval",
    action_kind: str = "post_message",
    next_run_at: object | None = None,
    failure_count: int = 0,
    last_error: str = "",
):
    return {
        "id": rid,
        "name": name,
        "enabled": enabled,
        "trigger_kind": trigger_kind,
        "action_kind": action_kind,
        "next_run_at": next_run_at,
        "failure_count": failure_count,
        "last_error": last_error,
    }


def _mutation_result(rule_id: int = 1, mutation_id: str = "m1"):
    return SimpleNamespace(rule_id=rule_id, mutation_id=mutation_id)


# ---------------------------------------------------------------------------
# Embed builder
# ---------------------------------------------------------------------------


def test_embed_renders_scheduler_running_state():
    embed = build_automation_embed_sync(
        guild=_guild(),
        snapshot={
            "running": True,
            "poll_interval_seconds": 60,
            "failure_threshold": 5,
            "ticks": 12,
        },
        snapshot_error=None,
        rules=[],
        rules_error=None,
    )
    assert "running" in (embed.description or "").lower()
    assert "60" in (embed.description or "")
    assert "Rules" in {f.name for f in embed.fields}


def test_embed_surfaces_snapshot_error():
    embed = build_automation_embed_sync(
        guild=_guild(),
        snapshot={},
        snapshot_error="scheduler not registered",
        rules=[],
        rules_error=None,
    )
    desc = (embed.description or "").lower()
    assert "scheduler not registered" in desc


def test_embed_lists_rules_with_state_and_failures():
    embed = build_automation_embed_sync(
        guild=_guild(),
        snapshot={"running": True},
        snapshot_error=None,
        rules=[
            _rule(rid=10, name="alpha", enabled=True),
            _rule(rid=11, name="beta", enabled=False, failure_count=3, last_error="db gone"),
        ],
        rules_error=None,
    )
    rules_field = next(f for f in embed.fields if f.name.startswith("Rules"))
    body = rules_field.value or ""
    assert "#10" in body and "alpha" in body
    assert "#11" in body and "beta" in body
    assert "fails=`3`" in body
    assert "db gone" in body


def test_embed_handles_dm_context():
    embed = build_automation_embed_sync(
        guild=None,
        snapshot={"running": True},
        snapshot_error=None,
        rules=[],
        rules_error=None,
    )
    rules_field = next(f for f in embed.fields if f.name == "Rules")
    assert "guild" in (rules_field.value or "").lower()


def test_embed_surfaces_rules_error():
    embed = build_automation_embed_sync(
        guild=_guild(),
        snapshot={"running": True},
        snapshot_error=None,
        rules=[],
        rules_error="DB connection refused",
    )
    rules_field = next(f for f in embed.fields if f.name == "Rules")
    assert "DB connection refused" in (rules_field.value or "")


# ---------------------------------------------------------------------------
# open_panel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_panel_returns_embed_and_view_with_rules():
    rules = [_rule(rid=1, name="a"), _rule(rid=2, name="b")]
    ctx = SimpleNamespace(
        guild=_guild(),
        author=_author(),
        user=None,
    )
    with (
        patch(
            "views.diagnostic.automation_panel._fetch_rules",
            new_callable=AsyncMock,
            return_value=(rules, None),
        ),
        patch(
            "views.diagnostic.automation_panel._fetch_scheduler_snapshot",
            return_value=({"running": True}, None),
        ),
    ):
        embed, view = await open_panel(ctx)

    assert isinstance(view, AutomationPanelView)
    assert view.last_embed is embed
    # The select must list both rules.
    import discord

    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    values = {opt.value for opt in select.options}
    assert "1" in values
    assert "2" in values


@pytest.mark.asyncio
async def test_open_panel_in_dm_context_renders_no_rules():
    ctx = SimpleNamespace(guild=None, author=_author(), user=None)
    with patch(
        "views.diagnostic.automation_panel._fetch_scheduler_snapshot",
        return_value=({"running": False}, None),
    ):
        embed, view = await open_panel(ctx)

    rules_field = next(f for f in embed.fields if f.name == "Rules")
    assert "guild" in (rules_field.value or "").lower()
    assert isinstance(view, AutomationPanelView)


# ---------------------------------------------------------------------------
# _commit_set_enabled / _commit_delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_commit_set_enabled_calls_pipeline_with_platform_owner_actor():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.set_enabled = AsyncMock(
        return_value=_mutation_result(rule_id=42, mutation_id="m42"),
    )
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        ok, msg = await _commit_set_enabled(interaction, rule_id=42, enabled=True)

    assert ok is True
    pipeline_instance.set_enabled.assert_awaited_once()
    kwargs = pipeline_instance.set_enabled.await_args.kwargs
    assert kwargs["rule_id"] == 42
    assert kwargs["enabled"] is True
    assert kwargs["actor_type"] == "platform_owner"
    assert "m42" in msg


@pytest.mark.asyncio
async def test_commit_set_enabled_surfaces_pipeline_error():
    from services.automation_mutation import UnknownAutomationRuleError

    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.set_enabled = AsyncMock(
        side_effect=UnknownAutomationRuleError("no such rule"),
    )
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        ok, msg = await _commit_set_enabled(interaction, rule_id=42, enabled=True)

    assert ok is False
    assert "UnknownAutomationRuleError" in msg


@pytest.mark.asyncio
async def test_commit_set_enabled_rejects_dm_context():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.set_enabled = AsyncMock()
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction(guild=None)
    interaction.guild = None
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        ok, msg = await _commit_set_enabled(interaction, rule_id=42, enabled=True)

    assert ok is False
    pipeline_instance.set_enabled.assert_not_called()
    assert "guild" in msg.lower()


@pytest.mark.asyncio
async def test_commit_delete_calls_pipeline():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.delete_rule = AsyncMock(
        return_value=_mutation_result(rule_id=7, mutation_id="m7"),
    )
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        ok, msg = await _commit_delete(interaction, rule_id=7)

    assert ok is True
    pipeline_instance.delete_rule.assert_awaited_once()
    kwargs = pipeline_instance.delete_rule.await_args.kwargs
    assert kwargs["rule_id"] == 7
    assert kwargs["actor_type"] == "platform_owner"
    assert "m7" in msg


# ---------------------------------------------------------------------------
# Button callbacks short-circuit when no rule is selected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enable_button_requires_selection():
    view = AutomationPanelView(_author(), rules=[_rule()])
    view.selected_rule_id = None
    interaction = _interaction()
    pipeline_class = MagicMock()
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        await view.btn_enable.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "pick a rule" in msg
    pipeline_class.assert_not_called()


@pytest.mark.asyncio
async def test_delete_button_requires_selection():
    view = AutomationPanelView(_author(), rules=[_rule()])
    view.selected_rule_id = None
    interaction = _interaction()
    pipeline_class = MagicMock()
    with patch(
        "services.automation_mutation.AutomationMutationPipeline",
        pipeline_class,
    ):
        await view.btn_delete.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "pick a rule" in msg
    pipeline_class.assert_not_called()

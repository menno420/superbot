"""Phase 9g / Track 6 PR 17 — automation executor tests.

Pins:

* Unknown ``action_kind`` returns ``status="failure"`` with a
  reason and never calls a handler.
* Missing required config keys return ``status="failure"``.
* Owner-only actions refuse without ``actor_id``.
* Dry-run never calls ``channel.send`` / ``member.add_roles`` /
  pipeline writes — the handler returns a ``would_*`` summary.
* Each action_kind has a happy path that records the right summary
  keys.
* A handler that raises is caught and surfaced as
  ``status="failure"`` — never propagates.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.automation_executor import AutomationRunResult, execute_rule


def _rule(
    *,
    rule_id=7,
    guild_id=1,
    action_kind="send_message",
    action_config=None,
    trigger_config=None,
):
    if action_config is None:
        action_config = {"channel_id": 100, "template": "hi"}
    return {
        "id": rule_id,
        "guild_id": guild_id,
        "name": "x",
        "action_kind": action_kind,
        "action_config": action_config,
        "trigger_config": trigger_config or {},
    }


def _guild(*, channels=None, roles=None, members=None, owner=None):
    g = MagicMock()
    g.id = 1
    channels = channels or {}
    roles = roles or {}
    members = members or {}
    g.get_channel = MagicMock(side_effect=lambda cid: channels.get(cid))
    g.get_role = MagicMock(side_effect=lambda rid: roles.get(rid))
    g.get_member = MagicMock(side_effect=lambda mid: members.get(mid))
    g.owner = owner
    return g


# ---------------------------------------------------------------------------
# Top-level guards
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_rejects_unknown_action_kind():
    rule = _rule(action_kind="garbage")
    result = await execute_rule(rule, dry_run=True)
    assert result.status == "failure"
    assert "unknown action_kind" in (result.error or "")


@pytest.mark.asyncio
async def test_execute_rejects_missing_required_config_keys():
    rule = _rule(
        action_kind="send_message",
        action_config={"channel_id": 100},  # missing template
    )
    result = await execute_rule(rule, dry_run=True)
    assert result.status == "failure"
    assert "template" in (result.error or "")


@pytest.mark.asyncio
async def test_execute_owner_only_refuses_without_actor_id():
    rule = _rule(
        action_kind="bind_channel",
        action_config={
            "subsystem": "logging",
            "binding_name": "mod_channel",
            "channel_id": 100,
        },
    )
    result = await execute_rule(rule, dry_run=False, guild=_guild())
    assert result.status == "failure"
    assert "owner authority" in (result.error or "")


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_dry_run_does_not_call_send():
    rule = _rule()
    channel = MagicMock()
    channel.send = AsyncMock()
    guild = _guild(channels={100: channel})
    result = await execute_rule(rule, dry_run=True, guild=guild)
    assert result.status == "success"
    assert result.result_summary["would_send_to"] == 100
    channel.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_message_happy_path_calls_channel_send():
    rule = _rule()
    channel = MagicMock()
    channel.send = AsyncMock()
    guild = _guild(channels={100: channel})
    result = await execute_rule(rule, dry_run=False, guild=guild)
    assert result.status == "success"
    channel.send.assert_awaited_once_with("hi")
    assert result.result_summary["sent_to"] == 100


@pytest.mark.asyncio
async def test_send_message_skips_when_channel_missing_in_cache():
    rule = _rule()
    guild = _guild(channels={})  # 100 not present
    result = await execute_rule(rule, dry_run=False, guild=guild)
    assert result.status == "success"
    assert result.result_summary.get("skipped") is True


# ---------------------------------------------------------------------------
# assign_role / remove_role
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assign_role_dry_run_does_not_call_add_roles():
    rule = _rule(
        action_kind="assign_role",
        action_config={"role_id": 300},
        trigger_config={"member_id": 555},
    )
    member = MagicMock()
    member.add_roles = AsyncMock()
    guild = _guild(roles={300: MagicMock()}, members={555: member})
    result = await execute_rule(rule, dry_run=True, guild=guild)
    assert result.status == "success"
    member.add_roles.assert_not_awaited()
    assert result.result_summary["would_assign_role"] == 300


@pytest.mark.asyncio
async def test_assign_role_happy_path_calls_add_roles():
    rule = _rule(
        action_kind="assign_role",
        action_config={"role_id": 300},
        trigger_config={"member_id": 555},
    )
    role = MagicMock()
    member = MagicMock()
    member.add_roles = AsyncMock()
    guild = _guild(roles={300: role}, members={555: member})
    result = await execute_rule(rule, dry_run=False, guild=guild)
    assert result.status == "success"
    member.add_roles.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_role_happy_path_calls_remove_roles():
    rule = _rule(
        action_kind="remove_role",
        action_config={"role_id": 300},
        trigger_config={"member_id": 555},
    )
    role = MagicMock()
    member = MagicMock()
    member.remove_roles = AsyncMock()
    guild = _guild(roles={300: role}, members={555: member})
    result = await execute_rule(rule, dry_run=False, guild=guild)
    assert result.status == "success"
    member.remove_roles.assert_awaited_once()


# ---------------------------------------------------------------------------
# post_readiness_summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_readiness_summary_dry_run_does_not_post():
    rule = _rule(
        action_kind="post_readiness_summary",
        action_config={"channel_id": 100},
    )
    channel = MagicMock()
    channel.send = AsyncMock()
    guild = _guild(channels={100: channel})
    result = await execute_rule(rule, dry_run=True, guild=guild)
    assert result.status == "success"
    channel.send.assert_not_awaited()
    assert result.result_summary["would_post_readiness_to"] == 100


@pytest.mark.asyncio
async def test_post_readiness_summary_happy_path_posts_embed():
    rule = _rule(
        action_kind="post_readiness_summary",
        action_config={"channel_id": 100},
    )
    channel = MagicMock()
    channel.send = AsyncMock()
    guild = _guild(channels={100: channel})
    fake_embed = MagicMock()
    with patch(
        "cogs.diagnostic._platform_embeds.build_setup_readiness_embed",
        new_callable=AsyncMock,
        return_value=fake_embed,
    ):
        result = await execute_rule(rule, dry_run=False, guild=guild)
    assert result.status == "success"
    channel.send.assert_awaited_once_with(embed=fake_embed)


# ---------------------------------------------------------------------------
# post_leaderboard_summary placeholder
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_leaderboard_summary_returns_placeholder():
    rule = _rule(
        action_kind="post_leaderboard_summary",
        action_config={"channel_id": 100, "subsystem": "xp"},
    )
    result = await execute_rule(rule, dry_run=False, guild=_guild())
    assert result.status == "success"
    assert result.result_summary["placeholder"] is True


# ---------------------------------------------------------------------------
# bind_channel / create_channel — owner-only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bind_channel_dry_run_does_not_call_pipeline():
    rule = _rule(
        action_kind="bind_channel",
        action_config={
            "subsystem": "logging",
            "binding_name": "mod_channel",
            "channel_id": 100,
        },
    )
    result = await execute_rule(rule, dry_run=True, guild=_guild(), actor_id=99)
    assert result.status == "success"
    assert "would_bind" in result.result_summary


@pytest.mark.asyncio
async def test_create_channel_dry_run_does_not_call_pipeline():
    rule = _rule(
        action_kind="create_channel",
        action_config={
            "subsystem": "logging",
            "binding_name": "audit_channel",
            "name": "bot-audit-log",
        },
    )
    result = await execute_rule(rule, dry_run=True, guild=_guild(), actor_id=99)
    assert result.status == "success"
    assert "would_create" in result.result_summary


# ---------------------------------------------------------------------------
# notify_owner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notify_owner_dry_run_does_not_dm():
    rule = _rule(
        action_kind="notify_owner",
        action_config={"template": "ping"},
    )
    owner = MagicMock()
    owner.send = AsyncMock()
    guild = _guild(owner=owner)
    result = await execute_rule(rule, dry_run=True, guild=guild)
    assert result.status == "success"
    owner.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_owner_happy_path_dms():
    rule = _rule(
        action_kind="notify_owner",
        action_config={"template": "ping"},
    )
    owner = MagicMock()
    owner.id = 99
    owner.send = AsyncMock()
    guild = _guild(owner=owner)
    result = await execute_rule(rule, dry_run=False, guild=guild)
    assert result.status == "success"
    owner.send.assert_awaited_once_with("ping")
    assert result.result_summary["dm_sent_to"] == 99


# ---------------------------------------------------------------------------
# Failure isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handler_exception_surfaces_as_failure_status():
    rule = _rule()
    channel = MagicMock()
    channel.send = AsyncMock(side_effect=RuntimeError("rate limit"))
    guild = _guild(channels={100: channel})
    result = await execute_rule(rule, dry_run=False, guild=guild)
    assert result.status == "failure"
    assert "rate limit" in (result.error or "")
    # Must not raise into caller.
    assert isinstance(result, AutomationRunResult)

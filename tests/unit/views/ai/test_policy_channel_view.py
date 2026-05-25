"""PR4A — channel-scope select + modal write through ai_policy_mutation only."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import ai_policy_mutation  # noqa: E402
from views.ai.policy.channel_view import (  # noqa: E402
    ChannelPolicyModal,
    ChannelPolicySelectView,
    _parse_optional_int,
)


# ---------------------------------------------------------------------------
# _parse_optional_int helper
# ---------------------------------------------------------------------------


def test_parse_optional_int_returns_none_for_blank():
    assert _parse_optional_int("", field="x") is None
    assert _parse_optional_int("   ", field="x") is None


def test_parse_optional_int_parses_decimal():
    assert _parse_optional_int("42", field="x") == 42


def test_parse_optional_int_rejects_non_integer():
    with pytest.raises(ValueError, match="must be an integer"):
        _parse_optional_int("nope", field="cooldown_seconds")


def test_parse_optional_int_enforces_minimum():
    with pytest.raises(ValueError, match=">= 0"):
        _parse_optional_int("-1", field="cooldown_seconds")


# ---------------------------------------------------------------------------
# ChannelPolicyModal — submit path goes through ai_policy_mutation only.
# ---------------------------------------------------------------------------


def _fake_channel(channel_id: int = 555_111, name: str = "general") -> MagicMock:
    channel = MagicMock()
    channel.id = channel_id
    channel.name = name
    channel.mention = f"<#{channel_id}>"
    return channel


def _admin_modal_interaction(guild_id: int = 999_888) -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.user.guild_permissions.administrator = True
    interaction.user.id = 12345
    interaction.response.send_message = AsyncMock()
    return interaction


def _set_inputs(modal: ChannelPolicyModal, *, mode: str, level: str, cooldown: str):
    """Bypass discord.ui.TextInput's runtime restrictions by setting
    its underlying ``_value``. The modal reads ``.value`` which falls
    back to the input."""
    modal.mode_input._value = mode
    modal.min_level_input._value = level
    modal.cooldown_input._value = cooldown


async def test_submit_writes_through_set_channel_policy(monkeypatch):
    captured: dict = {}

    async def _capture(guild_id, channel_id, *, mode, min_level,
                       cooldown_seconds, instruction_profile_id, actor):
        captured.update(
            guild_id=guild_id,
            channel_id=channel_id,
            mode=mode,
            min_level=min_level,
            cooldown_seconds=cooldown_seconds,
            instruction_profile_id=instruction_profile_id,
            actor=actor,
        )
        result = MagicMock()
        result.generation = 7
        return result

    monkeypatch.setattr(ai_policy_mutation, "set_channel_policy", _capture)
    channel = _fake_channel(channel_id=555_111, name="bot-spam")
    modal = ChannelPolicyModal(channel)
    _set_inputs(modal, mode="always_reply", level="3", cooldown="60")
    interaction = _admin_modal_interaction(guild_id=999_888)

    await modal.on_submit(interaction)

    assert captured["guild_id"] == 999_888
    assert captured["channel_id"] == 555_111
    assert captured["mode"] == "always_reply"
    assert captured["min_level"] == 3
    assert captured["cooldown_seconds"] == 60
    # PR4A scope: instruction_profile_id always None — profile UI is
    # a separate surface.
    assert captured["instruction_profile_id"] is None
    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "✅" in args[0]
    assert "always_reply" in args[0]
    assert "generation 7" in args[0]
    assert kwargs.get("ephemeral") is True


async def test_submit_passes_none_for_blank_optional_fields(monkeypatch):
    captured: dict = {}

    async def _capture(guild_id, channel_id, *, mode, min_level,
                       cooldown_seconds, instruction_profile_id, actor):
        captured.update(
            min_level=min_level,
            cooldown_seconds=cooldown_seconds,
        )
        result = MagicMock()
        result.generation = 1
        return result

    monkeypatch.setattr(ai_policy_mutation, "set_channel_policy", _capture)
    modal = ChannelPolicyModal(_fake_channel())
    _set_inputs(modal, mode="inherit", level="", cooldown="")
    interaction = _admin_modal_interaction()

    await modal.on_submit(interaction)
    assert captured["min_level"] is None
    assert captured["cooldown_seconds"] is None


async def test_submit_rejects_invalid_mode_without_calling_mutation(monkeypatch):
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True
        raise AssertionError("mutation must not run for invalid mode")

    monkeypatch.setattr(ai_policy_mutation, "set_channel_policy", _explode)
    modal = ChannelPolicyModal(_fake_channel())
    _set_inputs(modal, mode="nope", level="", cooldown="")
    interaction = _admin_modal_interaction()

    await modal.on_submit(interaction)
    assert called["hit"] is False
    interaction.response.send_message.assert_awaited_once()
    args, _ = interaction.response.send_message.call_args
    assert "mode must be one of" in args[0]
    for valid in ("inherit", "always_reply", "mention_only", "disabled"):
        assert valid in args[0]


async def test_submit_rejects_non_integer_min_level(monkeypatch):
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True

    monkeypatch.setattr(ai_policy_mutation, "set_channel_policy", _explode)
    modal = ChannelPolicyModal(_fake_channel())
    _set_inputs(modal, mode="inherit", level="abc", cooldown="")
    interaction = _admin_modal_interaction()

    await modal.on_submit(interaction)
    assert called["hit"] is False
    args, _ = interaction.response.send_message.call_args
    assert "min_level" in args[0]


async def test_submit_requires_guild_context(monkeypatch):
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True

    monkeypatch.setattr(ai_policy_mutation, "set_channel_policy", _explode)
    modal = ChannelPolicyModal(_fake_channel())
    _set_inputs(modal, mode="inherit", level="", cooldown="")
    interaction = _admin_modal_interaction()
    interaction.guild = None

    await modal.on_submit(interaction)
    assert called["hit"] is False
    args, _ = interaction.response.send_message.call_args
    assert "guild context" in args[0]


async def test_submit_surfaces_mutation_pipeline_error(monkeypatch):
    async def _raise(*args, **kwargs):
        raise ai_policy_mutation.UnauthorizedAIPolicyMutationError(
            "this should not happen but proves error path works",
        )

    monkeypatch.setattr(ai_policy_mutation, "set_channel_policy", _raise)
    modal = ChannelPolicyModal(_fake_channel())
    _set_inputs(modal, mode="inherit", level="", cooldown="")
    interaction = _admin_modal_interaction()

    await modal.on_submit(interaction)
    args, _ = interaction.response.send_message.call_args
    assert "Unauthorized" in args[0]


# ---------------------------------------------------------------------------
# ChannelPolicySelectView — admin gate + select component shape.
# ---------------------------------------------------------------------------


def test_select_view_holds_a_channel_select_restricted_to_text_channels():
    import discord

    view = ChannelPolicySelectView()
    selects = [
        item for item in view.children if isinstance(item, discord.ui.ChannelSelect)
    ]
    assert len(selects) == 1
    select = selects[0]
    assert select.channel_types == [discord.ChannelType.text]
    assert select.min_values == 1
    assert select.max_values == 1


async def test_select_view_rejects_non_admin():
    view = ChannelPolicySelectView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response.send_message = AsyncMock()
    allowed = await view.interaction_check(interaction)
    assert allowed is False
    interaction.response.send_message.assert_awaited_once()
    args, _ = interaction.response.send_message.call_args
    assert "Administrator" in args[0]

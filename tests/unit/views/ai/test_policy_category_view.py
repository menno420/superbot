"""PR4A — category-scope select + modal write through ai_policy_mutation only."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import ai_policy_mutation  # noqa: E402
from views.ai.policy.category_view import (  # noqa: E402
    CategoryPolicyModal,
    CategoryPolicySelectView,
)


def _fake_category(category_id: int = 444_222, name: str = "general-chat") -> MagicMock:
    cat = MagicMock()
    cat.id = category_id
    cat.name = name
    return cat


def _admin_modal_interaction(guild_id: int = 999_888) -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.user.guild_permissions.administrator = True
    interaction.user.id = 12345
    interaction.response.send_message = AsyncMock()
    return interaction


def _set_inputs(modal: CategoryPolicyModal, *, mode: str, level: str, cooldown: str):
    modal.mode_input._value = mode
    modal.min_level_input._value = level
    modal.cooldown_input._value = cooldown


# ---------------------------------------------------------------------------
# CategoryPolicyModal — submit goes through set_category_policy only.
# ---------------------------------------------------------------------------


async def test_submit_writes_through_set_category_policy(monkeypatch):
    captured: dict = {}

    async def _capture(guild_id, category_id, *, mode, min_level,
                       cooldown_seconds, instruction_profile_id, actor):
        captured.update(
            guild_id=guild_id,
            category_id=category_id,
            mode=mode,
            min_level=min_level,
            cooldown_seconds=cooldown_seconds,
            instruction_profile_id=instruction_profile_id,
            actor=actor,
        )
        result = MagicMock()
        result.generation = 9
        return result

    monkeypatch.setattr(ai_policy_mutation, "set_category_policy", _capture)
    modal = CategoryPolicyModal(_fake_category(category_id=444_222, name="quiet"))
    _set_inputs(modal, mode="mention_only", level="2", cooldown="120")
    interaction = _admin_modal_interaction(guild_id=999_888)

    await modal.on_submit(interaction)

    assert captured["guild_id"] == 999_888
    assert captured["category_id"] == 444_222
    assert captured["mode"] == "mention_only"
    assert captured["min_level"] == 2
    assert captured["cooldown_seconds"] == 120
    # PR-C-pre: modal preserves any existing profile binding via
    # UNCHANGED sentinel.
    from services.ai_policy_mutation import UNCHANGED

    assert captured["instruction_profile_id"] is UNCHANGED
    args, kwargs = interaction.response.send_message.call_args
    assert "✅" in args[0]
    assert "category **quiet**" in args[0]
    assert "mention_only" in args[0]
    assert "generation 9" in args[0]
    assert kwargs.get("ephemeral") is True


async def test_submit_passes_none_for_blank_optional_fields(monkeypatch):
    captured: dict = {}

    async def _capture(guild_id, category_id, *, mode, min_level,
                       cooldown_seconds, instruction_profile_id, actor):
        captured.update(min_level=min_level, cooldown_seconds=cooldown_seconds)
        result = MagicMock()
        result.generation = 1
        return result

    monkeypatch.setattr(ai_policy_mutation, "set_category_policy", _capture)
    modal = CategoryPolicyModal(_fake_category())
    _set_inputs(modal, mode="inherit", level="", cooldown="")
    await modal.on_submit(_admin_modal_interaction())
    assert captured["min_level"] is None
    assert captured["cooldown_seconds"] is None


async def test_submit_rejects_invalid_mode(monkeypatch):
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True

    monkeypatch.setattr(ai_policy_mutation, "set_category_policy", _explode)
    modal = CategoryPolicyModal(_fake_category())
    _set_inputs(modal, mode="not_valid", level="", cooldown="")
    interaction = _admin_modal_interaction()
    await modal.on_submit(interaction)
    assert called["hit"] is False
    args, _ = interaction.response.send_message.call_args
    assert "mode must be one of" in args[0]


async def test_submit_requires_guild_context(monkeypatch):
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True

    monkeypatch.setattr(ai_policy_mutation, "set_category_policy", _explode)
    modal = CategoryPolicyModal(_fake_category())
    _set_inputs(modal, mode="inherit", level="", cooldown="")
    interaction = _admin_modal_interaction()
    interaction.guild = None
    await modal.on_submit(interaction)
    assert called["hit"] is False
    args, _ = interaction.response.send_message.call_args
    assert "guild context" in args[0]


async def test_submit_surfaces_mutation_pipeline_error(monkeypatch):
    async def _raise(*args, **kwargs):
        raise ai_policy_mutation.InvalidAIPolicyValueError("bad value")

    monkeypatch.setattr(ai_policy_mutation, "set_category_policy", _raise)
    modal = CategoryPolicyModal(_fake_category())
    _set_inputs(modal, mode="inherit", level="", cooldown="")
    interaction = _admin_modal_interaction()
    await modal.on_submit(interaction)
    args, _ = interaction.response.send_message.call_args
    assert "InvalidAIPolicyValueError" in args[0]


# ---------------------------------------------------------------------------
# CategoryPolicySelectView shape + admin gate.
# ---------------------------------------------------------------------------


def test_select_view_holds_a_channel_select_restricted_to_categories():
    view = CategoryPolicySelectView()
    selects = [
        item for item in view.children if isinstance(item, discord.ui.ChannelSelect)
    ]
    assert len(selects) == 1
    assert selects[0].channel_types == [discord.ChannelType.category]


async def test_select_view_rejects_non_admin():
    view = CategoryPolicySelectView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response.send_message = AsyncMock()
    allowed = await view.interaction_check(interaction)
    assert allowed is False
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Chooser button now opens the real category view.
# ---------------------------------------------------------------------------


async def test_chooser_category_button_opens_real_select_view():
    from views.ai.policy.chooser import PolicyChooserView

    view = PolicyChooserView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.response.edit_message = AsyncMock()
    # In-place navigation (AI nav plan PR 2): the anchor is edited to the
    # category-policy page rather than a new ephemeral.
    await view.category_btn.callback(interaction)
    _, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs["view"], CategoryPolicySelectView)

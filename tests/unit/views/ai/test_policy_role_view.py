"""PR4A — role-scope select + modal write through ai_policy_mutation only."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import ai_policy_mutation  # noqa: E402
from views.ai.policy.role_view import (  # noqa: E402
    RolePolicyModal,
    RolePolicySelectView,
    _parse_bool,
)

# ---------------------------------------------------------------------------
# _parse_bool helper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("token", ["yes", "Yes", "YES", "y", "true", "1", "on"])
def test_parse_bool_accepts_truthy_tokens(token):
    assert _parse_bool(token, field="x") is True


@pytest.mark.parametrize("token", ["no", "No", "n", "false", "0", "off", "", "  "])
def test_parse_bool_treats_blank_and_negatives_as_false(token):
    assert _parse_bool(token, field="x") is False


def test_parse_bool_rejects_unknown():
    with pytest.raises(ValueError, match="expected yes/no"):
        _parse_bool("maybe", field="bypass_cooldown")


# ---------------------------------------------------------------------------
# RolePolicyModal — submit goes through set_role_policy only.
# ---------------------------------------------------------------------------


def _fake_role(role_id: int = 333_777, name: str = "moderators") -> MagicMock:
    role = MagicMock()
    role.id = role_id
    role.name = name
    role.mention = f"<@&{role_id}>"
    return role


def _admin_modal_interaction(guild_id: int = 999_888) -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.user.guild_permissions.administrator = True
    interaction.user.id = 12345
    interaction.response.send_message = AsyncMock()
    return interaction


def _set_inputs(modal, *, decision: str, level: str, bypass: str):
    modal.decision_input._value = decision
    modal.min_level_input._value = level
    modal.bypass_input._value = bypass


async def test_submit_writes_through_set_role_policy(monkeypatch):
    captured: dict = {}

    async def _capture(guild_id, role_id, *, decision, min_level_override,
                       bypass_cooldown, actor):
        captured.update(
            guild_id=guild_id,
            role_id=role_id,
            decision=decision,
            min_level_override=min_level_override,
            bypass_cooldown=bypass_cooldown,
            actor=actor,
        )
        result = MagicMock()
        result.generation = 4
        return result

    monkeypatch.setattr(ai_policy_mutation, "set_role_policy", _capture)
    modal = RolePolicyModal(_fake_role(role_id=333_777, name="mods"))
    _set_inputs(modal, decision="allow", level="0", bypass="yes")
    interaction = _admin_modal_interaction(guild_id=999_888)

    await modal.on_submit(interaction)

    assert captured["guild_id"] == 999_888
    assert captured["role_id"] == 333_777
    assert captured["decision"] == "allow"
    assert captured["min_level_override"] == 0
    assert captured["bypass_cooldown"] is True
    args, kwargs = interaction.response.send_message.call_args
    assert "✅" in args[0]
    assert "allow" in args[0]
    assert "bypass_cooldown=`True`" in args[0]
    assert "generation 4" in args[0]
    assert kwargs.get("ephemeral") is True


async def test_submit_normalises_decision_case(monkeypatch):
    """Operators sometimes type 'Deny' or 'INHERIT'. The modal
    lowercases before validation so the typed enum is respected.
    """
    captured: dict = {}

    async def _capture(guild_id, role_id, *, decision, **kw):
        captured["decision"] = decision
        result = MagicMock()
        result.generation = 1
        return result

    monkeypatch.setattr(ai_policy_mutation, "set_role_policy", _capture)
    modal = RolePolicyModal(_fake_role())
    _set_inputs(modal, decision="DENY", level="", bypass="")
    await modal.on_submit(_admin_modal_interaction())
    assert captured["decision"] == "deny"


async def test_submit_blank_inputs_clear_to_defaults(monkeypatch):
    captured: dict = {}

    async def _capture(guild_id, role_id, *, decision, min_level_override,
                       bypass_cooldown, actor):
        captured.update(
            min_level_override=min_level_override,
            bypass_cooldown=bypass_cooldown,
        )
        result = MagicMock()
        result.generation = 1
        return result

    monkeypatch.setattr(ai_policy_mutation, "set_role_policy", _capture)
    modal = RolePolicyModal(_fake_role())
    _set_inputs(modal, decision="inherit", level="", bypass="")
    await modal.on_submit(_admin_modal_interaction())
    assert captured["min_level_override"] is None
    assert captured["bypass_cooldown"] is False


async def test_submit_rejects_invalid_decision(monkeypatch):
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True

    monkeypatch.setattr(ai_policy_mutation, "set_role_policy", _explode)
    modal = RolePolicyModal(_fake_role())
    _set_inputs(modal, decision="banned", level="", bypass="")
    interaction = _admin_modal_interaction()
    await modal.on_submit(interaction)
    assert called["hit"] is False
    args, _ = interaction.response.send_message.call_args
    assert "decision must be one of" in args[0]


async def test_submit_rejects_bad_bypass_token(monkeypatch):
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True

    monkeypatch.setattr(ai_policy_mutation, "set_role_policy", _explode)
    modal = RolePolicyModal(_fake_role())
    _set_inputs(modal, decision="allow", level="", bypass="kinda")
    interaction = _admin_modal_interaction()
    await modal.on_submit(interaction)
    assert called["hit"] is False
    args, _ = interaction.response.send_message.call_args
    assert "bypass_cooldown" in args[0]


async def test_submit_requires_guild_context(monkeypatch):
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True

    monkeypatch.setattr(ai_policy_mutation, "set_role_policy", _explode)
    modal = RolePolicyModal(_fake_role())
    _set_inputs(modal, decision="allow", level="", bypass="")
    interaction = _admin_modal_interaction()
    interaction.guild = None
    await modal.on_submit(interaction)
    assert called["hit"] is False
    args, _ = interaction.response.send_message.call_args
    assert "guild context" in args[0]


async def test_submit_surfaces_mutation_pipeline_error(monkeypatch):
    async def _raise(*args, **kwargs):
        raise ai_policy_mutation.InvalidAIPolicyValueError("min level too high")

    monkeypatch.setattr(ai_policy_mutation, "set_role_policy", _raise)
    modal = RolePolicyModal(_fake_role())
    _set_inputs(modal, decision="allow", level="999", bypass="")
    interaction = _admin_modal_interaction()
    await modal.on_submit(interaction)
    args, _ = interaction.response.send_message.call_args
    assert "InvalidAIPolicyValueError" in args[0]


# ---------------------------------------------------------------------------
# RolePolicySelectView shape + admin gate.
# ---------------------------------------------------------------------------


def test_select_view_holds_a_role_select():
    view = RolePolicySelectView()
    selects = [
        item for item in view.children if isinstance(item, discord.ui.RoleSelect)
    ]
    assert len(selects) == 1
    assert selects[0].min_values == 1
    assert selects[0].max_values == 1


async def test_select_view_rejects_non_admin():
    view = RolePolicySelectView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response.send_message = AsyncMock()
    allowed = await view.interaction_check(interaction)
    assert allowed is False


# ---------------------------------------------------------------------------
# Chooser button now opens the real role view.
# ---------------------------------------------------------------------------


async def test_chooser_role_button_opens_real_select_view():
    from views.ai.policy.chooser import PolicyChooserView

    view = PolicyChooserView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.response.send_message = AsyncMock()
    await view.role_btn.callback(interaction)
    _, kwargs = interaction.response.send_message.call_args
    assert isinstance(kwargs["view"], RolePolicySelectView)
    assert kwargs.get("ephemeral") is True

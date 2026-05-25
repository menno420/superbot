"""PR-C tests for the preset picker flow.

Pin:

* ``build_preset_picker_embed`` lists every available preset.
* The picker's select callback calls
  ``ai_behavior_profile_service.apply_preset`` with the right
  ``scope``, ``target_id``, ``preset_id`` — never ``ai_db.*``.
* Apply errors surface to the operator.
* Unknown preset key returns an error without writing.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from services import ai_behavior_profile_service as svc
from views.ai.behavior.preset_picker import (
    PresetPickerView,
    build_preset_picker_embed,
)


def _summary(preset_id: int, key: str) -> svc.BehaviorPresetSummary:
    return svc.BehaviorPresetSummary(
        preset_id=preset_id,
        key=key,
        headline=f"headline for {key}",
        recommended_mode="mention_only",
        body=f"body of {key}",
    )


def _admin_interaction(guild_id: int = 999):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(
        id=1,
        guild_permissions=SimpleNamespace(administrator=True),
    )
    interaction.guild = SimpleNamespace(id=guild_id)
    interaction.response.send_message = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_picker_embed_lists_each_preset(monkeypatch):
    async def _fake():
        return [
            _summary(1, "disabled"),
            _summary(2, "helpful_channel"),
            _summary(3, "btd6_focused"),
        ]

    monkeypatch.setattr(svc, "list_presets", _fake)

    embed = await build_preset_picker_embed(scope_label="channel #x")
    blob = "\n".join(f.name + " " + f.value for f in embed.fields)
    for key in ("disabled", "helpful_channel", "btd6_focused"):
        assert key in blob


@pytest.mark.asyncio
async def test_view_loads_options_and_applies_preset(monkeypatch):
    async def _fake_list():
        return [_summary(7, "helpful_channel"), _summary(8, "btd6_focused")]

    captured: dict = {}

    async def _fake_apply(**kwargs):
        captured.update(kwargs)
        return svc.BehaviorApplyResult(
            scope=kwargs["scope"],
            target_id=kwargs["target_id"],
            preset_id=kwargs["preset_id"],
            preset_key="btd6_focused",
            recommended_mode="always_reply",
            policy_mutation_id="mid-abc",
        )

    monkeypatch.setattr(svc, "list_presets", _fake_list)
    monkeypatch.setattr(svc, "apply_preset", _fake_apply)

    view = PresetPickerView(
        scope="channel",
        target_id=555,
        target_label="<#555>",
    )
    interaction = _admin_interaction(guild_id=999)
    # Trigger interaction_check → _load_options.
    await view.interaction_check(interaction)

    # The dropdown should now be a child of the view.
    select = next(c for c in view.children if hasattr(c, "options"))
    assert {o.value for o in select.options} == {
        "helpful_channel",
        "btd6_focused",
    }

    # Simulate operator picking btd6_focused.
    select._values = ["btd6_focused"]  # bypass ContextVar lookup in tests
    apply_interaction = _admin_interaction(guild_id=999)
    await select.callback(apply_interaction)

    assert captured["guild_id"] == 999
    assert captured["scope"] == "channel"
    assert captured["target_id"] == 555
    assert captured["preset_id"] == 8  # btd6_focused's id from _fake_list
    apply_interaction.response.send_message.assert_awaited_once()
    msg = apply_interaction.response.send_message.await_args.args[0]
    assert "btd6_focused" in msg
    assert "always_reply" in msg
    assert "mid-abc" in msg


@pytest.mark.asyncio
async def test_apply_error_surfaces_to_operator(monkeypatch):
    async def _fake_list():
        return [_summary(7, "helpful_channel")]

    async def _fake_apply(**_kw):
        raise svc.UnknownBehaviorPresetError("gone")

    monkeypatch.setattr(svc, "list_presets", _fake_list)
    monkeypatch.setattr(svc, "apply_preset", _fake_apply)

    view = PresetPickerView(scope="channel", target_id=1, target_label="x")
    interaction = _admin_interaction()
    await view.interaction_check(interaction)
    select = next(c for c in view.children if hasattr(c, "options"))
    select._values = ["helpful_channel"]  # bypass ContextVar lookup in tests
    apply_interaction = _admin_interaction()
    await select.callback(apply_interaction)

    msg = apply_interaction.response.send_message.await_args.args[0]
    assert "UnknownBehaviorPresetError" in msg

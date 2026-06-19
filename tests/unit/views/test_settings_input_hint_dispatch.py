"""PR #7 — tests for input_hint-based dispatch and the three new widgets.

The dispatcher ``views.settings.subsystem_view.dispatch_edit_setting``
(extracted from the old ``_EditSettingSelect`` callback when the edit picker
moved onto the shared windowed select, Lane A2) routes off
``SettingSpec.input_hint`` with three branches:

* ``"channel"`` → ``ChannelSettingSelectView``
* ``"role"`` → ``RoleSettingSelectView``
* ``"numeric_presets"`` (with non-empty ``presets``) →
  ``NumericPresetsView``

Settings without ``input_hint`` keep their S6 widget. Tests below pin
each branch + the SettingSpec field shapes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.runtime.subsystem_schema import SettingSpec
from views.settings.edit_channel import ChannelSettingSelectView
from views.settings.edit_number_presets import NumericPresetsView
from views.settings.edit_role import RoleSettingSelectView
from views.settings.subsystem_view import dispatch_edit_setting

# ---------------------------------------------------------------------------
# SettingSpec carries the new fields with safe defaults
# ---------------------------------------------------------------------------


def test_setting_spec_defaults_are_backward_compatible():
    spec = SettingSpec(name="dummy", value_type=int, default=0)
    assert spec.input_hint == ""
    assert spec.presets == ()


def test_setting_spec_accepts_input_hint_and_presets():
    spec = SettingSpec(
        name="dummy",
        value_type=int,
        default=60,
        input_hint="numeric_presets",
        presets=(0, 30, 60, 120),
    )
    assert spec.input_hint == "numeric_presets"
    assert spec.presets == (0, 30, 60, 120)


# ---------------------------------------------------------------------------
# Dispatcher routing
# ---------------------------------------------------------------------------


async def _dispatch(spec: SettingSpec, interaction: MagicMock) -> None:
    """Route ``spec`` through the extracted dispatcher (was the select callback)."""
    await dispatch_edit_setting(interaction, "xp", spec.name)


def _patch_schema(spec: SettingSpec):
    schema = MagicMock()
    schema.settings = (spec,)
    return patch(
        "core.runtime.subsystem_schema.get_schema",
        return_value=schema,
    )


def _patch_resolution(value: object | None):
    if value is None:
        return patch(
            "services.settings_resolution.resolve_setting",
            new=AsyncMock(return_value=None),
        )
    resolution = MagicMock()
    resolution.value = value
    return patch(
        "services.settings_resolution.resolve_setting",
        new=AsyncMock(return_value=resolution),
    )


def _mock_interaction() -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.guild_id = 7
    interaction.message = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_dispatch_channel_hint_opens_channel_select():
    spec = SettingSpec(
        name="ch",
        value_type=str,
        default="",
        input_hint="channel",
    )
    interaction = _mock_interaction()
    with _patch_schema(spec), _patch_resolution("123"):
        await _dispatch(spec, interaction)
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert isinstance(kwargs["view"], ChannelSettingSelectView)
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_dispatch_role_hint_opens_role_select():
    spec = SettingSpec(
        name="r",
        value_type=str,
        default="",
        input_hint="role",
    )
    interaction = _mock_interaction()
    with _patch_schema(spec), _patch_resolution(""):
        await _dispatch(spec, interaction)
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert isinstance(kwargs["view"], RoleSettingSelectView)
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_dispatch_numeric_presets_opens_presets_view():
    spec = SettingSpec(
        name="cd",
        value_type=int,
        default=60,
        input_hint="numeric_presets",
        presets=(0, 15, 30, 60),
    )
    interaction = _mock_interaction()
    with _patch_schema(spec), _patch_resolution(30):
        await _dispatch(spec, interaction)
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert isinstance(kwargs["view"], NumericPresetsView)


@pytest.mark.asyncio
async def test_dispatch_numeric_presets_with_empty_presets_falls_back_to_modal():
    """A hint of ``"numeric_presets"`` without any ``presets`` declared
    should NOT raise — it falls through to the S6 modal so the value
    is still reachable.
    """
    spec = SettingSpec(
        name="cd",
        value_type=int,
        default=60,
        input_hint="numeric_presets",
        presets=(),
    )
    interaction = _mock_interaction()
    with _patch_schema(spec), _patch_resolution(30):
        await _dispatch(spec, interaction)
    interaction.response.send_modal.assert_awaited_once()
    interaction.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_unknown_input_hint_falls_through_to_default_routing():
    """An unrecognised hint must not error; the default
    value_type-based routing takes over.
    """
    spec = SettingSpec(
        name="cd",
        value_type=int,
        default=60,
        input_hint="not-a-known-mode",
    )
    interaction = _mock_interaction()
    with _patch_schema(spec), _patch_resolution(30):
        await _dispatch(spec, interaction)
    interaction.response.send_modal.assert_awaited_once()


# ---------------------------------------------------------------------------
# Widget shapes — minimal smoke (full pipeline calls are exercised in
# the existing modal / select test files)
# ---------------------------------------------------------------------------


def test_channel_view_has_select_and_clear_button():
    # (Uses a still-live channel setting; xp_announce_channel was retired
    # to the binding lane in P0-3.)
    view = ChannelSettingSelectView("moderation", "public_log_channel", None)
    types = {type(c).__name__ for c in view.children}
    assert "_ChannelPickSelect" in types
    assert "_ClearChannelButton" in types


def test_role_view_has_select_and_clear_button():
    view = RoleSettingSelectView("role", "moderator_role", None)
    types = {type(c).__name__ for c in view.children}
    assert "_RolePickSelect" in types
    assert "_ClearRoleButton" in types


def test_presets_view_renders_one_button_per_preset_plus_override():
    view = NumericPresetsView(
        subsystem="xp",
        setting_name="xp_cooldown",
        value_type=int,
        current_value=60,
        default_value=60,
        presets=(0, 15, 30, 60, 300),
        parent_message=None,
    )
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    # 5 preset buttons + 1 override button
    assert len(buttons) == 6
    override_buttons = [b for b in buttons if b.label == "Override…"]
    assert len(override_buttons) == 1


def test_presets_view_highlights_current_preset_in_primary_style():
    view = NumericPresetsView(
        subsystem="xp",
        setting_name="xp_cooldown",
        value_type=int,
        current_value=30,
        default_value=60,
        presets=(0, 15, 30, 60),
        parent_message=None,
    )
    primary = [
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.style is discord.ButtonStyle.primary
    ]
    # Exactly one button should be highlighted — the one matching current.
    assert len(primary) == 1
    assert primary[0].label == "30"


def test_presets_view_truncates_when_too_many_presets():
    """More presets than the 19-button cap drop with a WARNING; override
    button stays available.
    """
    presets = tuple(range(30))
    view = NumericPresetsView(
        subsystem="xp",
        setting_name="xp_cooldown",
        value_type=int,
        current_value=0,
        default_value=60,
        presets=presets,
        parent_message=None,
    )
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    # 19 capped presets + override.
    assert len(buttons) == 20


# ---------------------------------------------------------------------------
# Channel SettingSpec wiring (PR #7) + the P0-3 pointer-lane retirement
# ---------------------------------------------------------------------------


def test_xp_cooldown_uses_numeric_presets_hint():
    from cogs.xp.schemas import XP_SETTINGS

    by_name = {spec.name: spec for spec in XP_SETTINGS}
    assert by_name["xp_cooldown"].input_hint == "numeric_presets"
    assert len(by_name["xp_cooldown"].presets) > 0


def test_retired_channel_pointers_are_not_scalar_settings():
    """P0-3 arc PR 2 retired the ``xp_announce_channel`` +
    ``economy_log_channel`` scalar SettingSpecs, so the channel
    input-hint dispatch no longer surfaces them.  They live in the
    binding lane now (``xp.announce_channel`` / ``economy.log_channel``);
    the no-dual-declared-pointer invariant pins that they are not also
    scalars.
    """
    from cogs.economy.schemas import ECONOMY_BINDINGS, ECONOMY_SETTINGS
    from cogs.xp.schemas import XP_BINDINGS, XP_SETTINGS

    assert "xp_announce_channel" not in {s.name for s in XP_SETTINGS}
    assert "economy_log_channel" not in {s.name for s in ECONOMY_SETTINGS}
    # The binding is the canonical pointer home.
    assert "announce_channel" in {b.name for b in XP_BINDINGS}
    assert "log_channel" in {b.name for b in ECONOMY_BINDINGS}

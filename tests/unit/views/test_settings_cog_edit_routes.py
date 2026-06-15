"""Unit tests for the S6 edit-dispatch routing in SubsystemSettingsView.

Verifies that the Edit-Setting select on the per-subsystem view
dispatches to the correct widget based on the SettingSpec shape:

* ``bool``                                  → BooleanSettingToggle
* ``int`` / ``float``                       → NumberSettingModal
* ``str`` with empty ``allowed_values``     → TextSettingModal
* ``str`` with non-empty ``allowed_values`` → EnumSettingSelectView

Independent of the modal-on-submit tests in
``test_settings_edit_modals.py``: this file pins the dispatch
shape, those files pin the per-widget mutation path.
"""

from __future__ import annotations

import discord
import pytest

from core.runtime import guild_config
from core.runtime import subsystem_schema as schema_mod
from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema
from utils import db as db_pkg
from utils.db import settings as settings_db
from views.settings.subsystem_view import (
    SubsystemSettingsView,
    _EditSettingSelect,
)

# ---------------------------------------------------------------------------
# Fakes (kept minimal — the on_submit paths are covered elsewhere)
# ---------------------------------------------------------------------------


class _FakeGuild:
    def __init__(self, guild_id: int = 1):
        self.id = guild_id


class _FakeMember:
    def __init__(self, member_id: int = 7, *, guild: _FakeGuild | None = None):
        self.id = member_id
        self.guild = guild or _FakeGuild()


class _FakeMessage:
    pass


class _FakeResponse:
    def __init__(self):
        self.sent_modals: list = []
        self.sent_messages: list = []

    async def send_message(self, content=None, *, ephemeral=False, view=None, **_kw):
        self.sent_messages.append({"content": content, "view": view})

    async def send_modal(self, modal):
        self.sent_modals.append(modal)


class _FakeInteraction:
    def __init__(self, guild: _FakeGuild | None = None):
        self.guild = guild
        self.guild_id = guild.id if guild else None
        self.user = _FakeMember(guild=guild)
        self.message = _FakeMessage()
        self.response = _FakeResponse()


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch):
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    guild_config._reset_for_tests()

    _kv: dict[tuple[int, str], str] = {}

    async def _fake_get_setting(
        guild_id: int,
        key: str,
        default: str = "",
    ) -> str:
        return _kv.get((guild_id, key), default)

    monkeypatch.setattr(settings_db, "get_setting", _fake_get_setting)
    monkeypatch.setattr(db_pkg, "get_setting", _fake_get_setting)
    yield {"kv": _kv}
    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    guild_config._reset_for_tests()


# ---------------------------------------------------------------------------
# View shape: edit + reset selects appear when settings exist
# ---------------------------------------------------------------------------


def test_view_adds_edit_and_reset_selects_when_settings_exist():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    view = SubsystemSettingsView(_FakeMember(), "moderation")
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    # One edit select + one reset select = two.
    assert len(selects) == 2
    placeholders = {s.placeholder for s in selects}
    assert any("Edit" in p for p in placeholders)
    assert any("Reset" in p for p in placeholders)


def test_view_omits_selects_when_subsystem_has_no_settings():
    view = SubsystemSettingsView(_FakeMember(), "blackjack")  # no schema
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert selects == []
    # Two buttons: "Back to Hub" + "Open Panel" (PR 3 navigation).
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 2
    labels = [b.label or "" for b in buttons]
    assert any("Back" in lbl for lbl in labels)
    assert any("Open Panel" in lbl for lbl in labels)


def test_view_omits_selects_when_specs_have_no_settings_key():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                # No settings_key → not editable.
                SettingSpec(name="placeholder", value_type=int, default=0),
            ),
        ),
    )
    view = SubsystemSettingsView(_FakeMember(), "moderation")
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    assert selects == []


# ---------------------------------------------------------------------------
# Dispatch by value_type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_int_dispatches_to_number_modal(monkeypatch):
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    select = _EditSettingSelect(
        "moderation", [spec for spec in schema_mod.get_schema("moderation").settings],
    )
    select._values = ["warn_threshold"]
    interaction = _FakeInteraction(guild=_FakeGuild())
    await select.callback(interaction)
    assert len(interaction.response.sent_modals) == 1
    from views.settings.edit_number import NumberSettingModal

    assert isinstance(interaction.response.sent_modals[0], NumberSettingModal)


@pytest.mark.asyncio
async def test_float_dispatches_to_number_modal():
    schema_mod.register(
        SubsystemSchema(
            subsystem="rate",
            settings=(
                SettingSpec(
                    name="multiplier",
                    value_type=float,
                    default=1.0,
                    settings_key="RATE_MULTIPLIER",
                ),
            ),
        ),
    )
    select = _EditSettingSelect(
        "rate", [spec for spec in schema_mod.get_schema("rate").settings],
    )
    select._values = ["multiplier"]
    interaction = _FakeInteraction(guild=_FakeGuild())
    await select.callback(interaction)
    from views.settings.edit_number import NumberSettingModal

    assert isinstance(interaction.response.sent_modals[0], NumberSettingModal)


@pytest.mark.asyncio
async def test_str_without_allowed_values_dispatches_to_text_modal():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="dm_template",
                    value_type=str,
                    default="hello",
                    settings_key="DM_TEMPLATE",
                ),
            ),
        ),
    )
    select = _EditSettingSelect(
        "moderation", [spec for spec in schema_mod.get_schema("moderation").settings],
    )
    select._values = ["dm_template"]
    interaction = _FakeInteraction(guild=_FakeGuild())
    await select.callback(interaction)
    from views.settings.edit_text import TextSettingModal

    assert isinstance(interaction.response.sent_modals[0], TextSettingModal)


@pytest.mark.asyncio
async def test_str_with_allowed_values_dispatches_to_enum_view():
    schema_mod.register(
        SubsystemSchema(
            subsystem="cleanup",
            settings=(
                SettingSpec(
                    name="strictness",
                    value_type=str,
                    default="normal",
                    settings_key="CLEANUP_STRICTNESS",
                    allowed_values=("off", "light", "normal", "strict"),
                ),
            ),
        ),
    )
    select = _EditSettingSelect(
        "cleanup", [spec for spec in schema_mod.get_schema("cleanup").settings],
    )
    select._values = ["strictness"]
    interaction = _FakeInteraction(guild=_FakeGuild())
    await select.callback(interaction)
    # No modal — the enum widget is a follow-up view.
    assert interaction.response.sent_modals == []
    # An ephemeral message with a view was sent instead.
    assert len(interaction.response.sent_messages) == 1
    from views.settings.edit_enum import EnumSettingSelectView

    msg = interaction.response.sent_messages[0]
    assert isinstance(msg["view"], EnumSettingSelectView)


@pytest.mark.asyncio
async def test_bool_dispatches_to_toggle_directly(monkeypatch, _isolated_state):
    """Bool select pick toggles the value via the pipeline directly
    instead of opening a modal.
    """
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="dm_on_action",
                    value_type=bool,
                    default=False,
                    settings_key="MOD_DM_ON_ACTION",
                ),
            ),
        ),
    )
    # Monkeypatch the pipeline through to track that toggle ran.
    from views.settings import edit_boolean

    captured: dict = {}
    real_toggle = edit_boolean.toggle_setting

    async def _spy_toggle(*args, **kwargs):
        captured["called"] = True
        captured["args"] = args
        # Don't actually run the pipeline — the modal tests cover that
        # path.  Just call the interaction.response.send_message stub so
        # the spy looks like real behaviour.
        interaction = args[0]
        await interaction.response.send_message("spy toggle ran", ephemeral=True)

    monkeypatch.setattr(edit_boolean, "toggle_setting", _spy_toggle)

    select = _EditSettingSelect(
        "moderation", [spec for spec in schema_mod.get_schema("moderation").settings],
    )
    select._values = ["dm_on_action"]
    interaction = _FakeInteraction(guild=_FakeGuild())
    await select.callback(interaction)
    assert captured.get("called") is True
    # No modal opened.
    assert interaction.response.sent_modals == []


@pytest.mark.asyncio
async def test_unknown_setting_in_select_rejected():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    select = _EditSettingSelect(
        "moderation", [spec for spec in schema_mod.get_schema("moderation").settings],
    )
    # Pick a value that wouldn't appear in options — defensive against
    # client-side tampering.
    select._values = ["no_such_setting"]
    interaction = _FakeInteraction(guild=_FakeGuild())
    await select.callback(interaction)
    last = interaction.response.sent_messages[-1]
    assert "Unknown setting" in (last.get("content") or "")

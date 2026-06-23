"""Tools & Workflows admin UI — panel button, chooser, scope writes (Phase 3)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import discord

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import ai_orchestration_presets as presets  # noqa: E402
from views.ai import panel  # noqa: E402
from views.ai.tools import ToolsChooserView, build_tools_embed  # noqa: E402
from views.ai.tools.scope_view import (  # noqa: E402
    GuildToolsProfileView,
    _ProfileChoiceView,
    _ProfileSelect,
)


def _admin_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.guild = MagicMock()
    interaction.guild.id = 999
    interaction.guild_id = 999
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


# --- panel button ----------------------------------------------------------


def test_panel_advertises_tools_button() -> None:
    view = panel.AIPanelView()
    custom_ids = [
        item.custom_id for item in view.children if isinstance(item, discord.ui.Button)
    ]
    assert "ai:tools" in custom_ids
    # Existing custom_ids stay intact (compatibility contract I-5).
    for cid in ("ai:policy", "ai:behavior", "ai:settings"):
        assert cid in custom_ids


def test_tools_button_is_success_on_second_row() -> None:
    view = panel.AIPanelView()
    by_id = {
        item.custom_id: item
        for item in view.children
        if isinstance(item, discord.ui.Button)
    }
    tools_btn = by_id["ai:tools"]
    assert tools_btn.row == by_id["ai:behavior"].row
    assert tools_btn.style == discord.ButtonStyle.success


# --- router fallback -------------------------------------------------------


async def test_router_dispatches_tools_in_place() -> None:
    interaction = _admin_interaction()
    await panel.handle_ai_interaction(
        interaction,
        "tools",
        session=None,
        request_id="req",
    )
    # In-place navigation (AI nav plan PR 2): the persistent anchor is
    # edited to the Tools chooser page, not a new ephemeral.
    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs.get("view"), ToolsChooserView)
    interaction.response.send_message.assert_not_awaited()


async def test_router_rejects_non_admin_for_tools() -> None:
    interaction = _admin_interaction()
    interaction.user.guild_permissions.administrator = False
    await panel.handle_ai_interaction(
        interaction,
        "tools",
        session=None,
        request_id="req",
    )
    interaction.response.send_message.assert_awaited_once()
    args, _ = interaction.response.send_message.call_args
    assert "Administrator" in args[0]


# --- chooser + embed -------------------------------------------------------


def test_chooser_has_scope_and_preview_buttons() -> None:
    view = ToolsChooserView()
    labels = {c.label for c in view.children if isinstance(c, discord.ui.Button)}
    assert {"Guild", "Channel", "Category"}.issubset(labels)
    assert any("Preview" in lbl for lbl in labels)


def test_tools_embed_shows_current_from_snapshot() -> None:
    static = build_tools_embed()
    assert static.title == "AI Tools & Workflows"
    snapshot = MagicMock()
    snapshot.orchestration.guild_profile_key = "btd6_grounded"
    snapshot.orchestration.channel_override_count = 2
    snapshot.orchestration.category_override_count = 1
    with_current = build_tools_embed(snapshot)
    field_names = [f.name for f in with_current.fields]
    assert "Current" in field_names


# --- profile select options ------------------------------------------------


def test_guild_profile_select_lists_presets_without_clear() -> None:
    view = GuildToolsProfileView()
    select = next(c for c in view.children if isinstance(c, _ProfileSelect))
    values = {o.value for o in select.options}
    assert values == set(presets.known_profile_keys())
    assert "__inherit__" not in values  # guild scope cannot "inherit"


def test_channel_profile_choice_offers_clear() -> None:
    view = _ProfileChoiceView(scope="channel", target_id=3, target_label="#x")
    select = next(c for c in view.children if isinstance(c, _ProfileSelect))
    values = {o.value for o in select.options}
    assert "__inherit__" in values
    assert set(presets.known_profile_keys()).issubset(values)


# --- select callback writes through the audited mutation -------------------


async def test_guild_select_callback_calls_mutation(monkeypatch) -> None:
    captured: dict = {}

    async def fake_set_guild(guild_id, *, profile_key, actor):
        captured["args"] = (guild_id, profile_key)
        return MagicMock(generation=3)

    monkeypatch.setattr(
        "services.ai_orchestration_mutation.set_guild_orchestration",
        fake_set_guild,
    )

    view = GuildToolsProfileView()
    select = next(c for c in view.children if isinstance(c, _ProfileSelect))
    # Drive the select the way discord.py exposes chosen values (repo pattern).
    select._values = ["balanced_helper"]  # type: ignore[attr-defined]
    type(select).values = property(lambda self: self._values)

    interaction = _admin_interaction()
    await select.callback(interaction)

    assert captured["args"] == (999, "balanced_helper")
    interaction.response.edit_message.assert_awaited_once()


async def test_channel_select_callback_clear_passes_none(monkeypatch) -> None:
    captured: dict = {}

    async def fake_set_channel(guild_id, channel_id, *, profile_key, actor):
        captured["args"] = (guild_id, channel_id, profile_key)
        return MagicMock(generation=4)

    monkeypatch.setattr(
        "services.ai_orchestration_mutation.set_channel_orchestration",
        fake_set_channel,
    )

    view = _ProfileChoiceView(scope="channel", target_id=55, target_label="#x")
    select = next(c for c in view.children if isinstance(c, _ProfileSelect))
    select._values = ["__inherit__"]  # type: ignore[attr-defined]
    type(select).values = property(lambda self: self._values)

    interaction = _admin_interaction()
    await select.callback(interaction)

    assert captured["args"] == (999, 55, None)  # cleared

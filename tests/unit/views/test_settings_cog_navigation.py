"""Unit tests for settings → cog panel navigation (PR 3).

The per-subsystem settings page (``SubsystemSettingsView``) gains an
``_OpenRelatedPanelButton`` that routes into the related cog's
``build_help_menu_view`` hook when one exists, or shows a fallback
embed listing entry_points when no hook is available.  Sub-views
opened from this path get a "↩ Back to Settings" button so the
operator can return to the subsystem page.

These tests:

- verify the button is present on the view;
- exercise the dispatch path through a mocked cog hook;
- exercise the fallback path when no hook is registered;
- exercise the exception path when the hook raises;
- verify ``attach_back_to_settings_button`` builds a working back
  button and handles the 25-component cap.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.settings.subsystem_view import (
    SubsystemSettingsView,
    _build_no_panel_embed,
    _OpenRelatedPanelButton,
    _resolve_cog_for_subsystem,
    attach_back_to_settings_button,
)


def _author(id_: int = 1) -> MagicMock:
    author = MagicMock()
    author.id = id_
    return author


def _find_button(view: discord.ui.View, label_substr: str) -> discord.ui.Button:
    for child in view.children:
        if isinstance(child, discord.ui.Button) and label_substr in (child.label or ""):
            return child
    raise AssertionError(f"No button with label containing {label_substr!r}")


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_includes_open_panel_button():
    view = SubsystemSettingsView(_author(), "moderation")
    open_btn = _find_button(view, "Open Panel")
    assert isinstance(open_btn, _OpenRelatedPanelButton)
    assert open_btn.subsystem == "moderation"
    assert open_btn.row == 0


def test_view_open_panel_button_is_distinct_from_back_button():
    view = SubsystemSettingsView(_author(), "economy")
    open_btn = _find_button(view, "Open Panel")
    back_btn = _find_button(view, "Back to Hub")
    assert open_btn is not back_btn


# ---------------------------------------------------------------------------
# Dispatch — hook found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_panel_button_calls_cog_hook_and_attaches_back():
    btn = _OpenRelatedPanelButton("moderation")
    # Manually attach a parent view so callbacks can edit it back.
    parent = SubsystemSettingsView(_author(), "moderation")
    btn._view = parent  # type: ignore[attr-defined]

    interaction = MagicMock()
    interaction.user = _author()
    interaction.client = MagicMock()

    fake_cog = MagicMock()
    fake_embed = discord.Embed(title="Moderation panel")
    fake_view = discord.ui.View()
    fake_cog.build_help_menu_view = AsyncMock(return_value=(fake_embed, fake_view))

    with patch(
        "views.settings.subsystem_view._resolve_cog_for_subsystem",
        return_value=fake_cog,
    ), patch(
        "core.runtime.interaction_helpers.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "core.runtime.interaction_helpers.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)

    fake_cog.build_help_menu_view.assert_awaited_once_with(interaction)
    edit.assert_awaited_once()
    swapped_view = edit.await_args.kwargs["view"]
    # The fake_view should have gained a "↩ Back to Settings" button.
    back_btns = [
        c
        for c in swapped_view.children
        if isinstance(c, discord.ui.Button) and "Back to Settings" in (c.label or "")
    ]
    assert len(back_btns) == 1


# ---------------------------------------------------------------------------
# Dispatch — no hook
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_panel_button_shows_fallback_when_no_cog():
    btn = _OpenRelatedPanelButton("moderation")
    parent = SubsystemSettingsView(_author(), "moderation")
    btn._view = parent  # type: ignore[attr-defined]

    interaction = MagicMock()
    interaction.user = _author()
    interaction.client = MagicMock()

    with patch(
        "views.settings.subsystem_view._resolve_cog_for_subsystem",
        return_value=None,
    ), patch(
        "core.runtime.interaction_helpers.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "core.runtime.interaction_helpers.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)

    embed = edit.await_args.kwargs["embed"]
    assert "No interactive panel" in (embed.title or "")
    # Stay on the parent view rather than swapping.
    assert edit.await_args.kwargs["view"] is parent


@pytest.mark.asyncio
async def test_open_panel_button_shows_fallback_when_cog_has_no_hook():
    btn = _OpenRelatedPanelButton("moderation")
    parent = SubsystemSettingsView(_author(), "moderation")
    btn._view = parent  # type: ignore[attr-defined]

    interaction = MagicMock()
    interaction.user = _author()
    interaction.client = MagicMock()

    fake_cog = MagicMock(spec=[])  # no build_help_menu_view attribute

    with patch(
        "views.settings.subsystem_view._resolve_cog_for_subsystem",
        return_value=fake_cog,
    ), patch(
        "core.runtime.interaction_helpers.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "core.runtime.interaction_helpers.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)

    embed = edit.await_args.kwargs["embed"]
    assert "No interactive panel" in (embed.title or "")


# ---------------------------------------------------------------------------
# Dispatch — hook raises
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_panel_button_handles_hook_exception():
    btn = _OpenRelatedPanelButton("moderation")
    parent = SubsystemSettingsView(_author(), "moderation")
    btn._view = parent  # type: ignore[attr-defined]

    interaction = MagicMock()
    interaction.user = _author()
    interaction.client = MagicMock()

    fake_cog = MagicMock()
    fake_cog.build_help_menu_view = AsyncMock(side_effect=RuntimeError("boom"))

    with patch(
        "views.settings.subsystem_view._resolve_cog_for_subsystem",
        return_value=fake_cog,
    ), patch(
        "core.runtime.interaction_helpers.safe_defer",
        new_callable=AsyncMock,
        return_value=True,
    ), patch(
        "core.runtime.interaction_helpers.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as edit:
        await btn.callback(interaction)

    embed = edit.await_args.kwargs["embed"]
    assert "Could not open" in (embed.title or "")
    assert "RuntimeError" in (embed.description or "")
    # Stay on the parent view.
    assert edit.await_args.kwargs["view"] is parent


@pytest.mark.asyncio
async def test_open_panel_button_bails_when_defer_fails():
    btn = _OpenRelatedPanelButton("moderation")
    parent = SubsystemSettingsView(_author(), "moderation")
    btn._view = parent  # type: ignore[attr-defined]

    interaction = MagicMock()
    interaction.user = _author()

    with patch(
        "core.runtime.interaction_helpers.safe_defer",
        new_callable=AsyncMock,
        return_value=False,
    ), patch(
        "views.settings.subsystem_view._resolve_cog_for_subsystem",
    ) as resolver:
        await btn.callback(interaction)
    resolver.assert_not_called()


# ---------------------------------------------------------------------------
# _build_no_panel_embed
# ---------------------------------------------------------------------------


def test_build_no_panel_embed_lists_entry_points_when_available():
    embed = _build_no_panel_embed("moderation")
    assert "No interactive panel" in (embed.title or "")
    field = next(f for f in embed.fields if f.name == "Typed commands")
    # SUBSYSTEMS["moderation"]["entry_points"] includes modmenu.
    assert "modmenu" in field.value


def test_build_no_panel_embed_handles_unknown_subsystem():
    embed = _build_no_panel_embed("not_a_real_subsystem")
    assert "No interactive panel" in (embed.title or "")
    field = next(f for f in embed.fields if f.name == "Typed commands")
    assert "no entry_points declared" in field.value


# ---------------------------------------------------------------------------
# _resolve_cog_for_subsystem
# ---------------------------------------------------------------------------


def test_resolve_cog_delegates_to_help_cog():
    """The settings → cog router reuses help_cog._cog_for_subsystem."""
    bot = MagicMock()
    fake_cog = MagicMock()
    with patch(
        "cogs.help_cog._cog_for_subsystem",
        return_value=fake_cog,
    ) as delegate:
        result = _resolve_cog_for_subsystem(bot, "moderation")
    delegate.assert_called_once_with(bot, "moderation")
    assert result is fake_cog


def test_resolve_cog_returns_none_on_resolver_exception():
    bot = MagicMock()
    with patch(
        "cogs.help_cog._cog_for_subsystem",
        side_effect=RuntimeError("registry busted"),
    ):
        result = _resolve_cog_for_subsystem(bot, "moderation")
    assert result is None


# ---------------------------------------------------------------------------
# attach_back_to_settings_button helper
# ---------------------------------------------------------------------------


def test_attach_back_to_settings_button_adds_a_button():
    sub_view: discord.ui.View = discord.ui.View()
    author = MagicMock()
    author.id = 7
    attach_back_to_settings_button(sub_view, author, "moderation")
    btns = [c for c in sub_view.children if isinstance(c, discord.ui.Button)]
    assert len(btns) == 1
    assert "Back to Settings" in (btns[0].label or "")
    assert btns[0].custom_id == "settings:back"
    assert btns[0].row == 4


def test_attach_back_to_settings_button_noop_when_view_full():
    sub_view: discord.ui.View = discord.ui.View()
    for i in range(25):
        sub_view.add_item(
            discord.ui.Button(label=f"x{i}", custom_id=f"x{i}", row=i // 5),
        )
    author = MagicMock()
    attach_back_to_settings_button(sub_view, author, "moderation")
    assert len(sub_view.children) == 25

"""Q-0059 Home-message builder (audit Phase 5, PR B).

Pins the mandatory-preview rule (Save disabled until the *current* draft
was previewed; any edit re-disables), one audited save call with the
staged values, the reset-to-default write, and the preview composing
through the shared frame (mention suppression included).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.help_overlay import GuildHelpOverlay, HomeMessage
from views.help.home_builder import (
    HomeMessageBuilderView,
    _PreviewButton,
    _ResetButton,
    _SaveButton,
    build_builder_embed,
)

GUILD = 99


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock(id=1)
    interaction.user.guild_permissions = MagicMock(administrator=True)
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    return interaction


def _builder() -> HomeMessageBuilderView:
    return HomeMessageBuilderView(MagicMock(id=1), GUILD)


def _save_button(view: HomeMessageBuilderView) -> _SaveButton:
    return next(c for c in view.children if isinstance(c, _SaveButton))


def _preview_button(view: HomeMessageBuilderView) -> _PreviewButton:
    return next(c for c in view.children if isinstance(c, _PreviewButton))


# ---------------------------------------------------------------------------
# Mandatory preview
# ---------------------------------------------------------------------------


def test_save_starts_disabled():
    assert _save_button(_builder()).disabled is True


@pytest.mark.asyncio
async def test_preview_unlocks_save_and_shows_exact_frame():
    view = _builder()
    view.stage(title="Hello", body="@everyone welcome")
    interaction = _interaction()

    await _preview_button(view).callback(interaction)

    assert view.previewed is True
    assert _save_button(view).disabled is False
    embeds = interaction.response.edit_message.await_args.kwargs["embeds"]
    preview = embeds[1]
    assert preview.title == "Hello"
    assert "@everyone" not in preview.description  # mention suppression
    assert "everyone" in preview.description


def test_any_edit_after_preview_relocks_save():
    view = _builder()
    view.previewed = True
    view._rebuild_items()
    assert _save_button(view).disabled is False

    view.stage(title="changed")

    assert view.previewed is False
    assert _save_button(view).disabled is True


@pytest.mark.asyncio
async def test_save_without_preview_writes_nothing():
    view = _builder()  # never previewed
    interaction = _interaction()
    with patch(
        "views.help.home_builder.set_home_message",
        AsyncMock(),
    ) as set_mock:
        await _save_button(view).callback(interaction)

    set_mock.assert_not_awaited()
    assert "Preview" in interaction.response.send_message.await_args.args[0]


# ---------------------------------------------------------------------------
# Save / reset — one audited call each
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_writes_staged_values_once():
    view = _builder()
    view.stage(title="Welcome", body="Read the rules", color=0x57F287)
    view.previewed = True
    view._rebuild_items()
    interaction = _interaction()
    with (
        patch(
            "views.help.home_builder.set_home_message",
            AsyncMock(return_value=MagicMock()),
        ) as set_mock,
        patch(
            "views.help.editor.build_editor_home_embed",
            AsyncMock(return_value=discord.Embed()),
        ),
        patch("views.help.editor.get_guild_help_overlay"),
    ):
        await _save_button(view).callback(interaction)

    set_mock.assert_awaited_once()
    kwargs = set_mock.await_args.kwargs
    assert kwargs["title"] == "Welcome"
    assert kwargs["body"] == "Read the rules"
    assert kwargs["color"] == 0x57F287


@pytest.mark.asyncio
async def test_reset_writes_all_none_and_clears_draft():
    view = _builder()
    view.stage(title="Something")
    interaction = _interaction()
    with patch(
        "views.help.home_builder.set_home_message",
        AsyncMock(return_value=MagicMock()),
    ) as set_mock:
        await next(c for c in view.children if isinstance(c, _ResetButton)).callback(
            interaction
        )

    kwargs = set_mock.await_args.kwargs
    assert kwargs["title"] is None
    assert kwargs["body"] is None
    assert kwargs["color"] is None
    assert view.staged_title is None and view.previewed is False


# ---------------------------------------------------------------------------
# Pre-staging from the saved state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_from_current_prestages_saved_home():
    overlay = GuildHelpOverlay(
        guild_id=GUILD,
        home=HomeMessage(title="Saved title", body=None, color=0xED4245),
    )
    with patch(
        "views.help.home_builder.get_guild_help_overlay",
        AsyncMock(return_value=overlay),
    ):
        view = await HomeMessageBuilderView.from_current(MagicMock(id=1), GUILD)

    assert view.staged_title == "Saved title"
    assert view.staged_color == 0xED4245
    assert view.previewed is False  # saved ≠ previewed; Save stays locked


def test_builder_embed_reflects_draft_state():
    view = _builder()
    view.stage(title="Welcome")
    embed = build_builder_embed(view)
    title_field = next(f for f in embed.fields if f.name == "Draft title")
    assert "Welcome" in title_field.value
    assert "Preview the draft" in (embed.footer.text or "")

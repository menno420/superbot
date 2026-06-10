"""Help overlay editor (audit Phase 5, PR A).

Pins the plan §6 contract: admin re-checked at callback time (non-admin →
no write), every editor action is exactly one audited mutation-service
call, reset-all has a mandatory confirm step, pickers render custom +
default + stable key (Q-0058) with 🙈 hidden markers, and mutation-contract
errors surface as copy instead of crashes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.help_overlay import GuildHelpOverlay, HelpOverlayRow
from services.help_overlay_mutation import InvalidHelpOverlayValueError
from views.help.editor import (
    EntityPickerView,
    HelpEditorHomeView,
    HelpEntityEditorView,
    _EntitySelect,
    _ResetAllConfirmView,
    build_editor_home_embed,
    build_entity_editor_embed,
)

GUILD = 99


def _interaction(*, admin: bool = True, user_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = GUILD
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.user.guild_permissions = MagicMock(administrator=admin)
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.response.defer = AsyncMock()
    return interaction


def _catalogue() -> MagicMock:
    hub_entry = MagicMock()
    hub_entry.display_name = "Games"
    hub_entry.purpose = "Play games"
    hub_row = MagicMock(key="games", entry=hub_entry)

    sub_row = MagicMock()
    sub_row.key = "economy"
    sub_row.display_name = "Economy"
    sub_row.description = "Coins and jobs"

    catalogue = MagicMock()
    catalogue.hubs = (hub_row,)
    catalogue.subsystems = (sub_row,)
    catalogue.hub = lambda key: hub_row if key == "games" else None
    catalogue.subsystem = lambda key: sub_row if key == "economy" else None
    return catalogue


def _overlay(*rows: HelpOverlayRow) -> GuildHelpOverlay:
    return GuildHelpOverlay(guild_id=GUILD, rows=tuple(rows))


def _patched(overlay: GuildHelpOverlay):
    return (
        patch(
            "views.help.editor.get_guild_help_overlay",
            AsyncMock(return_value=overlay),
        ),
        patch("views.help.editor.build_help_catalogue", return_value=_catalogue()),
        patch(
            "views.help.editor.set_overlay_fields",
            AsyncMock(return_value=MagicMock()),
        ),
        patch(
            "views.help.editor.reset_guild_overlay",
            AsyncMock(return_value=MagicMock()),
        ),
    )


# ---------------------------------------------------------------------------
# Authority — re-checked at callback time
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_admin_is_denied_at_callback_time_without_write():
    author = MagicMock(id=1)
    for view in (
        HelpEditorHomeView(author, GUILD),
        EntityPickerView(author, GUILD, "subsystem"),
        HelpEntityEditorView(author, GUILD, "subsystem", "economy"),
        _ResetAllConfirmView(author, GUILD),
    ):
        interaction = _interaction(admin=False)
        allowed = await view.interaction_check(interaction)
        assert allowed is False
        assert "Administrator" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_admin_passes_callback_check():
    view = HelpEditorHomeView(MagicMock(id=1), GUILD)
    assert await view.interaction_check(_interaction(admin=True)) is True


# ---------------------------------------------------------------------------
# Entity editor — one action, one audited service call
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hide_button_writes_display_hidden_true():
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay())
    view = HelpEntityEditorView(MagicMock(id=1), GUILD, "subsystem", "economy")
    interaction = _interaction()
    with overlay_p, cat_p, set_p as set_mock, reset_p:
        await type(view).hide_btn(view, interaction, MagicMock())

    set_mock.assert_awaited_once()
    kwargs = set_mock.await_args.kwargs
    assert kwargs["display_hidden"] is True
    args = set_mock.await_args.args
    assert args == (GUILD, "subsystem", "economy")
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_unhide_resets_field_to_inherit():
    hidden_row = HelpOverlayRow(
        entity_kind="subsystem",
        entity_key="economy",
        display_hidden=True,
    )
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay(hidden_row))
    view = HelpEntityEditorView(
        MagicMock(id=1),
        GUILD,
        "subsystem",
        "economy",
        hidden=True,
    )
    with overlay_p, cat_p, set_p as set_mock, reset_p:
        await type(view).hide_btn(view, _interaction(), MagicMock())

    assert set_mock.await_args.kwargs["display_hidden"] is None


@pytest.mark.asyncio
async def test_reset_entity_resets_all_three_fields():
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay())
    view = HelpEntityEditorView(MagicMock(id=1), GUILD, "subsystem", "economy")
    with overlay_p, cat_p, set_p as set_mock, reset_p:
        await type(view).reset_entity_btn(view, _interaction(), MagicMock())

    kwargs = set_mock.await_args.kwargs
    assert kwargs["display_hidden"] is None
    assert kwargs["display_name"] is None
    assert kwargs["description"] is None


@pytest.mark.asyncio
async def test_mutation_error_surfaces_as_copy_not_crash():
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay())
    view = HelpEntityEditorView(MagicMock(id=1), GUILD, "subsystem", "economy")
    interaction = _interaction()
    with overlay_p, cat_p, set_p as set_mock, reset_p:
        set_mock.side_effect = InvalidHelpOverlayValueError("display_name too long")
        await type(view).rename_btn(view, interaction, MagicMock())
        # rename opens a modal; drive its submit directly
        modal = interaction.response.send_modal.await_args.args[0]
        modal.name_input = MagicMock(value="x" * 5)
        submit_interaction = _interaction()
        await modal.on_submit(submit_interaction)

    msg = submit_interaction.response.send_message.await_args
    assert "display_name too long" in msg.args[0]
    assert msg.kwargs["ephemeral"] is True
    submit_interaction.response.edit_message.assert_not_awaited()


# ---------------------------------------------------------------------------
# Reset-all — confirm step is mandatory
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reset_all_first_click_writes_nothing():
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay())
    view = HelpEditorHomeView(MagicMock(id=1), GUILD)
    interaction = _interaction()
    with overlay_p, cat_p, set_p, reset_p as reset_mock:
        await type(view).reset_all_btn(view, interaction, MagicMock())

    reset_mock.assert_not_awaited()
    # ...and the confirm view is now on the message.
    new_view = interaction.response.edit_message.await_args.kwargs["view"]
    assert isinstance(new_view, _ResetAllConfirmView)


@pytest.mark.asyncio
async def test_reset_all_confirm_performs_the_audited_reset():
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay())
    view = _ResetAllConfirmView(MagicMock(id=1), GUILD)
    interaction = _interaction()
    with overlay_p, cat_p, set_p, reset_p as reset_mock:
        await type(view).confirm_btn(view, interaction, MagicMock())

    reset_mock.assert_awaited_once()
    assert reset_mock.await_args.args == (GUILD,)


# ---------------------------------------------------------------------------
# Picker + embeds — Q-0058 rendering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_picker_renders_custom_name_hidden_marker_and_default_key():
    rows = (
        HelpOverlayRow(
            entity_kind="subsystem",
            entity_key="economy",
            display_hidden=True,
            display_name="Bank",
        ),
    )
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay(*rows))
    picker = EntityPickerView(MagicMock(id=1), GUILD, "subsystem")
    with overlay_p, cat_p, set_p, reset_p:
        await picker.build_embed()

    select = next(c for c in picker.children if isinstance(c, _EntitySelect))
    option = select.options[0]
    assert option.label == "🙈 Bank"  # custom name + hidden marker
    assert option.value == "economy"
    assert "default: Economy" in option.description  # Q-0058
    assert "economy" in option.description  # stable key


@pytest.mark.asyncio
async def test_entity_embed_shows_custom_default_and_key():
    rows = (
        HelpOverlayRow(
            entity_kind="subsystem",
            entity_key="economy",
            display_name="Bank",
        ),
    )
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay(*rows))
    with overlay_p, cat_p, set_p, reset_p:
        embed = await build_entity_editor_embed(GUILD, "subsystem", "economy")

    name_field = next(f for f in embed.fields if f.name == "Name")
    assert "Bank" in name_field.value and "Economy" in name_field.value
    assert "economy" in (embed.footer.text or "")


@pytest.mark.asyncio
async def test_home_embed_counts_and_orphans():
    rows = (
        HelpOverlayRow(
            entity_kind="subsystem",
            entity_key="economy",
            display_hidden=True,
        ),
        HelpOverlayRow(
            entity_kind="subsystem",
            entity_key="retired_thing",
            display_name="Ghost",
        ),
    )
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay(*rows))
    with overlay_p, cat_p, set_p, reset_p:
        embed = await build_editor_home_embed(GUILD)

    counts = next(f for f in embed.fields if f.name == "Current overrides")
    assert "hidden: **1**" in counts.value
    assert "renamed: **1**" in counts.value
    orphan_field = next(f for f in embed.fields if "Orphaned" in f.name)
    assert "retired_thing" in orphan_field.value


@pytest.mark.asyncio
async def test_select_opens_entity_editor():
    overlay_p, cat_p, set_p, reset_p = _patched(_overlay())
    picker = EntityPickerView(MagicMock(id=1), GUILD, "subsystem")
    with overlay_p, cat_p, set_p, reset_p:
        await picker.build_embed()
        select = next(c for c in picker.children if isinstance(c, _EntitySelect))
        select._values = ["economy"]  # discord.py populates from the payload
        interaction = _interaction()
        with patch.object(
            type(select),
            "values",
            property(lambda self: ["economy"]),
        ):
            await select.callback(interaction)

    new_view = interaction.response.edit_message.await_args.kwargs["view"]
    assert isinstance(new_view, HelpEntityEditorView)
    assert new_view.key == "economy"


# ---------------------------------------------------------------------------
# Display-only guarantee — the editor module imports no admission path
# ---------------------------------------------------------------------------


def test_editor_module_imports_only_the_audited_seam():
    import ast
    from pathlib import Path

    src = (
        Path(__file__).resolve().parents[3] / "disbot" / "views" / "help" / "editor.py"
    ).read_text()
    imported: set[str] = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    # Writes only through the audited seam; no db module, no admission path.
    assert "services.help_overlay_mutation" in imported
    assert not any("utils.db" in m for m in imported)
    assert not any("command_access" in m or "governance" in m for m in imported)


def test_editor_copy_says_display_only():
    """Q-0055: hidden entries are labeled still-executable."""
    from views.help.editor import _HIDDEN_NOTE

    assert "still executable" in _HIDDEN_NOTE


@pytest.mark.asyncio
async def test_modal_buttons_never_defer_first():
    """``send_modal`` must be the FIRST response on the interaction — a
    deferred modal silently dies (Discord rejects it after a defer). The
    merged editor behaves correctly; this pins the dead-modal regression
    class so a future "defer everything up front" refactor can't break
    Rename/Re-describe. (Salvaged from the parallel PR A build, #678.)"""
    view = HelpEntityEditorView(MagicMock(id=1), GUILD, "subsystem", "economy")
    for label in ("✏️ Rename…", "📝 Re-describe…"):
        button = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.label == label
        )
        interaction = _interaction()
        await button.callback(interaction)
        interaction.response.send_modal.assert_awaited_once()
        interaction.response.defer.assert_not_awaited()

"""Help overlay editor views (audit Phase 5, PR A).

Pins the editor plan's contracts: administrator floor re-checked at callback
time; **every action is exactly one audited mutation-service call** (no
direct db imports — the seam stays the only writer); hide semantics are
toggle-to-inherit; Q-0058 labels (custom + default + stable key) in the
picker; Q-0055 display-only copy on every surface that hides.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.help_overlay import GuildHelpOverlay, HelpOverlayRow
from views.help.editor import (
    EntityEditorView,
    EntityPickerView,
    HelpEditorHomeView,
    _ResetAllConfirmView,
    build_editor_home_embed,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _interaction(*, admin: bool = True) -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.user = MagicMock()
    interaction.user.id = 1
    interaction.user.guild_permissions = MagicMock(administrator=admin)
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.edit_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.followup.edit_message = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.message = MagicMock()
    interaction.message.edit = AsyncMock()
    return interaction


def _item(view, custom_id: str):
    for child in view.children:
        if getattr(child, "custom_id", None) == custom_id:
            return child
    raise AssertionError(f"no item {custom_id!r} on {type(view).__name__}")


# ---------------------------------------------------------------------------
# Write discipline: services-only, one call per action
# ---------------------------------------------------------------------------


def test_module_writes_only_through_the_mutation_seam():
    """The editor may import the audited seam — and nothing db-shaped."""
    src = (_REPO_ROOT / "disbot" / "views" / "help" / "editor.py").read_text()
    tree = ast.parse(src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert not {m for m in imported if m.startswith("utils.db")}, imported
    assert any("help_overlay_mutation" in m or m == "services" for m in imported)


@pytest.mark.asyncio
async def test_hide_toggle_is_one_audited_call_each_way():
    view = EntityEditorView(MagicMock(), kind="subsystem", key="economy", hidden=False)
    interaction = _interaction()
    with (
        patch(
            "views.help.editor.help_overlay_mutation.set_overlay_fields",
            AsyncMock(),
        ) as write,
        patch("views.help.editor._open_entity_refresh", AsyncMock()),
    ):
        await _item(view, "help_editor:hide_toggle").callback(interaction)
    write.assert_awaited_once()
    kwargs = write.await_args.kwargs
    assert kwargs["display_hidden"] is True
    assert kwargs["actor"] is interaction.user
    assert write.await_args.args == (99, "subsystem", "economy")

    # Already hidden → the toggle RESETS to inherit (None), never False-pins.
    view = EntityEditorView(MagicMock(), kind="hub", key="games", hidden=True)
    with (
        patch(
            "views.help.editor.help_overlay_mutation.set_overlay_fields",
            AsyncMock(),
        ) as write,
        patch("views.help.editor._open_entity_refresh", AsyncMock()),
    ):
        await _item(view, "help_editor:hide_toggle").callback(_interaction())
    assert write.await_args.kwargs["display_hidden"] is None


@pytest.mark.asyncio
async def test_reset_entity_clears_all_three_fields_in_one_call():
    view = EntityEditorView(MagicMock(), kind="subsystem", key="xp", hidden=True)
    with (
        patch(
            "views.help.editor.help_overlay_mutation.set_overlay_fields",
            AsyncMock(),
        ) as write,
        patch("views.help.editor._open_entity_refresh", AsyncMock()),
    ):
        await _item(view, "help_editor:reset_entity").callback(_interaction())
    write.assert_awaited_once()
    kwargs = write.await_args.kwargs
    assert (
        kwargs["display_hidden"] is None
        and kwargs["display_name"] is None
        and kwargs["description"] is None
    )


@pytest.mark.asyncio
async def test_rename_button_opens_a_modal_without_deferring():
    """send_modal must be the first response — a deferred modal is dead."""
    view = EntityEditorView(MagicMock(), kind="subsystem", key="xp", hidden=False)
    interaction = _interaction()
    await _item(view, "help_editor:rename").callback(interaction)
    interaction.response.send_modal.assert_awaited_once()
    interaction.response.defer.assert_not_awaited()


@pytest.mark.asyncio
async def test_reset_all_requires_the_confirm_step():
    home = HelpEditorHomeView(MagicMock())
    interaction = _interaction()
    with patch(
        "views.help.editor.help_overlay_mutation.reset_guild_overlay",
        AsyncMock(),
    ) as reset:
        await _item(home, "help_editor:reset_all").callback(interaction)
        reset.assert_not_awaited()  # the first click only opens the confirm

        confirm = _ResetAllConfirmView(MagicMock())
        with patch("views.help.editor._back_to_home", AsyncMock()):
            await _item(confirm, "help_editor:reset_all_confirm").callback(
                _interaction(),
            )
        reset.assert_awaited_once()
        assert reset.await_args.args == (99,)


@pytest.mark.asyncio
async def test_admin_floor_is_rechecked_at_callback_time():
    """Opening the panel never authorises later clicks (ADR-005 pattern)."""
    for view in (
        HelpEditorHomeView(MagicMock()),
        EntityEditorView(MagicMock(), kind="hub", key="games", hidden=False),
        _ResetAllConfirmView(MagicMock()),
    ):
        interaction = _interaction(admin=False)
        assert await view.interaction_check(interaction) is False
        interaction.response.send_message.assert_awaited_once()
        assert interaction.response.send_message.await_args.kwargs.get("ephemeral")


# ---------------------------------------------------------------------------
# Q-0058 labels + Q-0055 copy
# ---------------------------------------------------------------------------


def test_picker_options_show_custom_default_and_key():
    labels = {
        "economy": ("Bank stuff", "Economy", False),  # renamed
        "games": ("Games", "Games", True),  # hidden, default name
    }
    view = EntityPickerView(
        MagicMock(),
        kind="subsystem",
        keys=("economy", "games"),
        labels=labels,
        page=0,
    )
    select = next(c for c in view.children if hasattr(c, "options"))
    by_value = {o.value: o for o in select.options}
    assert by_value["economy"].label == "Bank stuff"
    assert by_value["economy"].description == "Economy · economy"  # Q-0058
    assert by_value["games"].label.startswith("🙈 ")
    assert by_value["games"].description == "games"  # default name → key only


@pytest.mark.asyncio
async def test_home_embed_counts_and_display_only_copy():
    overlay = GuildHelpOverlay(
        guild_id=99,
        rows=(
            HelpOverlayRow("subsystem", "economy", display_hidden=True),
            HelpOverlayRow("hub", "games", display_name="Arcade"),
        ),
    )
    with patch(
        "views.help.editor.get_guild_help_overlay",
        AsyncMock(return_value=overlay),
    ):
        embed = await build_editor_home_embed(99)
    text = f"{embed.description} " + " ".join(
        f"{f.name} {f.value}" for f in embed.fields
    )
    assert "display-only" in text  # Q-0055, verbatim promise
    assert "hidden: **1**" in text
    assert "renamed: **1**" in text
    assert "Help Preview" in text  # the verify pointer

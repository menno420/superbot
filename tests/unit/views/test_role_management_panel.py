"""Role management panel — edit-by-select + multi-select-delete-with-confirm.

Owner-directed UX overhaul (2026-06-21): you no longer type a role name to edit
(pick it from a select), and delete is a multi-select gated behind an explicit
confirmation step instead of a single select that deleted immediately.  These
pin the new control flow against regression.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.user.id = 7
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


def _parent() -> MagicMock:
    parent = MagicMock()
    parent._author = SimpleNamespace(id=7)
    parent._rerender = AsyncMock()
    return parent


@pytest.mark.asyncio
async def test_edit_role_modal_edits_the_picked_role_by_id():
    """The Edit modal acts on the already-picked role (id-first) and routes the
    change through the audited RoleLifecycleService, then re-renders the panel.
    """
    from services.lifecycle import SUCCESS
    from views.roles.management_panel import EditRoleModal

    parent = _parent()
    role = SimpleNamespace(id=555, name="OldName")
    modal = EditRoleModal(parent, role)
    modal.new_name = MagicMock(value="NewName")
    modal.new_color = MagicMock(value="")

    interaction = _interaction()
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=SimpleNamespace(outcome=SUCCESS, first_error=None))
    with (
        patch(
            "views.roles.management_panel.resources.resolve_role",
            return_value=role,
        ),
        patch(
            "views.roles.management_panel.RoleLifecycleService",
            return_value=svc,
        ),
        patch(
            "views.roles.management_panel.safe_defer",
            AsyncMock(return_value=True),
        ),
    ):
        await modal.on_submit(interaction)

    svc.apply.assert_awaited_once()
    req = svc.apply.await_args.args[1]
    assert req.operation == "edit"
    assert req.role_id == 555
    assert req.name == "NewName"
    parent._rerender.assert_awaited_once()


@pytest.mark.asyncio
async def test_edit_role_modal_rejects_an_empty_change():
    """Blank name + blank colour is a no-op, surfaced to the operator without a
    lifecycle call.
    """
    from views.roles.management_panel import EditRoleModal

    parent = _parent()
    role = SimpleNamespace(id=555, name="X")
    modal = EditRoleModal(parent, role)
    modal.new_name = MagicMock(value="   ")
    modal.new_color = MagicMock(value="")

    interaction = _interaction()
    svc = MagicMock()
    svc.apply = AsyncMock()
    with (
        patch(
            "views.roles.management_panel.resources.resolve_role",
            return_value=role,
        ),
        patch(
            "views.roles.management_panel.RoleLifecycleService",
            return_value=svc,
        ),
    ):
        await modal.on_submit(interaction)

    svc.apply.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_view_requires_at_least_one_selection():
    """Pressing Delete Selected with nothing chosen prompts instead of deleting."""
    from views.roles.management_panel import _DeleteRolesView

    parent = _parent()
    roles = [SimpleNamespace(id=1, name="A"), SimpleNamespace(id=2, name="B")]
    view = _DeleteRolesView(parent, roles)  # selected_ids empty

    interaction = _interaction()
    await _DeleteRolesView.confirm_btn(view, interaction, MagicMock())

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_view_advances_to_a_confirmation_step():
    """A multi-selection routes to an explicit confirmation listing every role —
    nothing is deleted yet.
    """
    from views.roles.management_panel import _ConfirmDeleteView, _DeleteRolesView

    parent = _parent()
    roles = [SimpleNamespace(id=1, name="Alpha"), SimpleNamespace(id=2, name="Beta")]
    view = _DeleteRolesView(parent, roles)
    view.selected_ids = [1, 2]

    interaction = _interaction()
    with patch("views.roles.management_panel.RoleLifecycleService") as svc:
        await _DeleteRolesView.confirm_btn(view, interaction, MagicMock())

    # Confirmation only — no deletion happened at this stage.
    svc.assert_not_called()
    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert "Alpha" in kwargs["content"] and "Beta" in kwargs["content"]
    assert isinstance(kwargs["view"], _ConfirmDeleteView)


@pytest.mark.asyncio
async def test_confirm_delete_deletes_every_selected_role():
    """Confirming the batch deletes each selected role through the audited
    lifecycle service and re-renders the panel.
    """
    from services.lifecycle import SUCCESS
    from views.roles.management_panel import _ConfirmDeleteView

    parent = _parent()
    view = _ConfirmDeleteView(parent, [1, 2])
    roles = {
        1: SimpleNamespace(id=1, name="Alpha"),
        2: SimpleNamespace(id=2, name="Beta"),
    }

    interaction = _interaction()
    svc = MagicMock()
    svc.apply = AsyncMock(return_value=SimpleNamespace(outcome=SUCCESS, first_error=None))
    with (
        patch(
            "views.roles.management_panel.resources.resolve_role",
            side_effect=lambda _g, *, role_id: roles.get(role_id),
        ),
        patch(
            "views.roles.management_panel.RoleLifecycleService",
            return_value=svc,
        ),
        patch(
            "views.roles.management_panel.safe_defer",
            AsyncMock(return_value=True),
        ),
    ):
        await _ConfirmDeleteView.confirm(view, interaction, MagicMock())

    assert svc.apply.await_count == 2
    deleted_ops = {svc.apply.await_args_list[i].args[1].operation for i in range(2)}
    assert deleted_ops == {"delete"}
    parent._rerender.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()

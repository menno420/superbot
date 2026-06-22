"""The shared 📦 Role Packs bulk-create flow (views.roles._role_pack_flow).

CI-safe with no Discord gateway: the category step swaps to a role multiselect,
and committing creates one role per picked name through the audited
``ensure_role`` seam, then hands the new ids to the ``on_created`` hook.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from utils import role_packs
from views.roles import _role_pack_flow
from views.roles._role_pack_flow import RolePackView


def _interaction() -> SimpleNamespace:
    return SimpleNamespace(
        user=SimpleNamespace(
            id=42,
            guild_permissions=SimpleNamespace(manage_roles=True, administrator=False),
        ),
        response=SimpleNamespace(
            is_done=lambda: False,
            defer=AsyncMock(),
            edit_message=AsyncMock(),
            send_message=AsyncMock(),
        ),
        followup=SimpleNamespace(send=AsyncMock()),
    )


def _view(on_created=None) -> RolePackView:
    return RolePackView(
        SimpleNamespace(id=42),
        SimpleNamespace(id=1),
        on_created=on_created,
    )


@pytest.mark.asyncio
async def test_on_pack_swaps_to_role_multiselect() -> None:
    view = _view()
    interaction = _interaction()
    await view._on_pack(interaction, "pronouns")
    assert view._pack is role_packs.get_pack("pronouns")
    interaction.response.edit_message.assert_awaited_once()
    # The category select is gone; a multiselect now occupies the view.
    assert not any(
        isinstance(c, _role_pack_flow._PackCategorySelect) for c in view.children
    )


@pytest.mark.asyncio
async def test_commit_creates_each_role_and_runs_hook() -> None:
    on_created = AsyncMock()
    view = _view(on_created=on_created)
    view._pack = role_packs.get_pack("pronouns")
    interaction = _interaction()

    ids = iter([101, 102])
    ensure = AsyncMock(side_effect=lambda *a, **k: (next(ids), True, ""))
    with patch("services.reaction_role_service.ensure_role", new=ensure):
        await _role_pack_flow._commit_pack_roles(
            interaction,
            view,
            ["He/Him", "She/Her"],
        )

    assert ensure.await_count == 2
    # Names + appearance come straight from the catalogue spec.
    created_names = {c.kwargs["name"] for c in ensure.await_args_list}
    assert created_names == {"He/Him", "She/Her"}
    interaction.response.defer.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()
    on_created.assert_awaited_once()
    assert on_created.await_args.args[1] == [101, 102]


@pytest.mark.asyncio
async def test_commit_requires_manage_roles() -> None:
    view = _view()
    view._pack = role_packs.get_pack("pronouns")
    interaction = _interaction()
    interaction.user.guild_permissions = SimpleNamespace(
        manage_roles=False,
        administrator=False,
    )
    ensure = AsyncMock()
    with patch("services.reaction_role_service.ensure_role", new=ensure):
        await _role_pack_flow._commit_pack_roles(interaction, view, ["He/Him"])
    ensure.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_commit_with_no_names_is_a_noop() -> None:
    view = _view()
    view._pack = role_packs.get_pack("pronouns")
    interaction = _interaction()
    ensure = AsyncMock()
    with patch("services.reaction_role_service.ensure_role", new=ensure):
        await _role_pack_flow._commit_pack_roles(interaction, view, [])
    ensure.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Custom bulk creation
# ---------------------------------------------------------------------------


def test_parse_role_names_splits_dedups_and_caps() -> None:
    raw = "Artist\nWriter, Gamer\n artist \n\nWriter"
    # newlines + commas split; case-insensitive dedup; first-seen order kept.
    assert _role_pack_flow._parse_role_names(raw) == ["Artist", "Writer", "Gamer"]
    # batch cap drops extras.
    many = ",".join(f"R{i}" for i in range(40))
    assert len(_role_pack_flow._parse_role_names(many, limit=25)) == 25
    assert _role_pack_flow._parse_role_names("   \n , ") == []


@pytest.mark.asyncio
async def test_custom_bulk_commit_applies_colour_and_runs_hook() -> None:
    import discord

    on_created = AsyncMock()
    flow = _view(on_created=on_created)
    bulk = _role_pack_flow._BulkColourView(flow, ["Artist", "Writer"])
    interaction = _interaction()

    ids = iter([201, 202])
    ensure = AsyncMock(side_effect=lambda *a, **k: (next(ids), True, ""))
    with patch("services.reaction_role_service.ensure_role", new=ensure):
        await _role_pack_flow._commit_custom_roles(
            interaction,
            bulk,
            discord.Color(0x3498DB),
        )

    assert ensure.await_count == 2
    names = [c.kwargs["name"] for c in ensure.await_args_list]
    assert names == ["Artist", "Writer"]
    # The chosen preset colour is applied to every role in the batch.
    assert all(
        c.kwargs["color"] == discord.Color(0x3498DB) for c in ensure.await_args_list
    )
    on_created.assert_awaited_once()
    assert on_created.await_args.args[1] == [201, 202]


@pytest.mark.asyncio
async def test_custom_bulk_commit_no_colour_uses_default() -> None:
    import discord

    flow = _view()
    bulk = _role_pack_flow._BulkColourView(flow, ["Artist"])
    interaction = _interaction()
    ensure = AsyncMock(return_value=(301, True, ""))
    with patch("services.reaction_role_service.ensure_role", new=ensure):
        await _role_pack_flow._commit_custom_roles(interaction, bulk, None)
    assert ensure.await_args.kwargs["color"] == discord.Color.default()

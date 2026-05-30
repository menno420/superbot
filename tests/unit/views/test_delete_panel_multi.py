"""Tests for the multi-channel delete sub-panel (audit P1-10).

``_DeleteSubView`` adopted the shared ``views.selectors.MultiSelect`` —
the destructive sibling of the restrict panel's multi-lock.  Because
deletion is irreversible, ``_DeleteConfirmView`` names every target
before anything happens.  These tests pin:

- the picker is a MultiSelect recording every selected id;
- "Delete Selected" requires a selection and hands all targets to the
  confirm view, whose embed lists them by name;
- Confirm deletes every channel and partitions the outcome into
  deleted / permission-denied / not-found / failed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.selectors import MultiSelect


def _options(*pairs: tuple[int, str]) -> list[discord.SelectOption]:
    return [discord.SelectOption(label=name, value=str(cid)) for cid, name in pairs]


def _build_view(options: list[discord.SelectOption]):
    from views.channels.delete_panel import _DeleteSubView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    return _DeleteSubView(ctx, options=options, manager_message=None)


def _build_confirm(channels: list[tuple[int, str]]):
    from views.channels.delete_panel import _DeleteConfirmView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    return _DeleteConfirmView(ctx, channels=channels, manager_message=None)


async def _click(view, label: str, interaction) -> None:
    """Invoke a decorator-defined button callback the way discord.py does."""
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == label
    )
    btn._view = view  # discord.py binds the parent view via Item._view
    await btn.callback(interaction)


def test_delete_picker_is_multiselect():
    view = _build_view(_options((10, "alpha"), (20, "beta")))
    assert isinstance(view.channel_select, MultiSelect)
    assert view.channel_select.min_values == 1
    assert view.channel_select.max_values == 2


@pytest.mark.asyncio
async def test_selecting_channels_records_all_ids():
    view = _build_view(_options((10, "alpha"), (20, "beta")))
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    await view._on_channels_selected(interaction, [10, 20])
    assert view.selected_channel_ids == [10, 20]
    assert view._selected_names() == ["alpha", "beta"]
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_btn_requires_a_selection():
    view = _build_view(_options((10, "alpha")))
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    await _click(view, "Delete Selected", interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "at least one" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_delete_btn_hands_all_targets_to_confirm_view():
    view = _build_view(_options((10, "alpha"), (20, "beta")))
    view.selected_channel_ids = [10, 20]
    interaction = MagicMock()
    captured: dict[str, object] = {}

    async def _edit(*, embed, view):
        captured["embed"] = embed
        captured["view"] = view

    interaction.response.edit_message = AsyncMock(side_effect=_edit)
    await _click(view, "Delete Selected", interaction)

    from views.channels.delete_panel import _DeleteConfirmView

    assert isinstance(captured["view"], _DeleteConfirmView)
    assert captured["view"].channels == [(10, "alpha"), (20, "beta")]
    # confirm embed names every target
    desc = captured["embed"].description
    assert "alpha" in desc and "beta" in desc
    assert "cannot be undone" in desc


def test_confirm_embed_lists_every_channel():
    view = _build_confirm([(10, "alpha"), (20, "beta"), (30, "gamma")])
    embed = view.build_confirm_embed()
    assert "3 channels" in embed.description
    for name in ("alpha", "beta", "gamma"):
        assert name in embed.description


@pytest.mark.asyncio
async def test_confirm_deletes_every_selected_channel():
    view = _build_confirm([(10, "alpha"), (20, "beta")])
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()

    ch_a = MagicMock()
    ch_a.delete = AsyncMock()
    ch_b = MagicMock()
    ch_b.delete = AsyncMock()
    by_id = {10: ch_a, 20: ch_b}

    captured: dict[str, discord.Embed] = {}

    async def _edit(_inter, *, embed, view):  # noqa: ARG001
        captured["embed"] = embed
        return True

    with (
        patch("views.channels.delete_panel.resources") as mock_res,
        patch("views.channels.delete_panel.safe_defer", AsyncMock(return_value=True)),
        patch("views.channels.delete_panel.safe_edit", AsyncMock(side_effect=_edit)),
        patch(
            "views.channels.delete_panel.restore_parent_or_send_fresh",
            AsyncMock(return_value=None),
        ),
        patch("views.channels.delete_panel.asyncio.sleep", AsyncMock()),
    ):
        mock_res.resolve_channel = MagicMock(
            side_effect=lambda _g, *, channel_id, kind: by_id.get(channel_id)
        )
        await _click(view, "Confirm Delete", interaction)

    ch_a.delete.assert_awaited_once()
    ch_b.delete.assert_awaited_once()
    field_values = " ".join(f.value for f in captured["embed"].fields)
    assert "alpha" in field_values
    assert "beta" in field_values


@pytest.mark.asyncio
async def test_confirm_partitions_partial_failures():
    view = _build_confirm([(10, "ok"), (20, "forbidden"), (30, "gone")])
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()

    ch_ok = MagicMock()
    ch_ok.delete = AsyncMock()
    ch_forbidden = MagicMock()
    ch_forbidden.delete = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "nope"))
    by_id = {10: ch_ok, 20: ch_forbidden}  # 30 resolves to None (gone)

    captured: dict[str, discord.Embed] = {}

    async def _edit(_inter, *, embed, view):  # noqa: ARG001
        captured["embed"] = embed
        return True

    with (
        patch("views.channels.delete_panel.resources") as mock_res,
        patch("views.channels.delete_panel.safe_defer", AsyncMock(return_value=True)),
        patch("views.channels.delete_panel.safe_edit", AsyncMock(side_effect=_edit)),
        patch(
            "views.channels.delete_panel.restore_parent_or_send_fresh",
            AsyncMock(return_value=None),
        ),
        patch("views.channels.delete_panel.asyncio.sleep", AsyncMock()),
    ):
        mock_res.resolve_channel = MagicMock(
            side_effect=lambda _g, *, channel_id, kind: by_id.get(channel_id)
        )
        await _click(view, "Confirm Delete", interaction)

    names = {f.name: f.value for f in captured["embed"].fields}
    joined = " || ".join(f"{k}={v}" for k, v in names.items())
    assert "ok" in joined
    assert "forbidden" in joined
    assert "gone" in joined

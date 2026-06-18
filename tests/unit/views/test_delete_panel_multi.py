"""Tests for the multi-channel delete sub-panel (audit P1-10 + PR A).

``_DeleteSubView`` adopted the shared ``views.selectors.MultiSelect`` —
the destructive sibling of the restrict panel's multi-lock.  Because
deletion is irreversible, ``_DeleteConfirmView`` names every target
before anything happens.  These tests pin:

- the picker is a MultiSelect recording every selected id;
- "Delete Selected" requires a selection and hands all targets to the
  confirm view, whose embed lists them by name;
- Confirm **routes through the audited ``ChannelLifecycleService``** (not a
  direct ``channel.delete()``) with ``operation="delete", confirmed=True``,
  and renders the typed result, partitioning deleted / permission-denied /
  not-found / failed (re-mapping the service's id-named not-found step back
  to the display name).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.lifecycle import SUCCESS, LifecycleResult, StepResult


def _windowed_select(view) -> discord.ui.Select:
    """The windowed multi-select the panel attached to itself."""
    return next(c for c in view.children if isinstance(c, discord.ui.Select))


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


def _result(
    applied: list[tuple[int, str]] | None = None,
    failed: list[tuple[int, str, str]] | None = None,
) -> LifecycleResult:
    """A typed delete result: ``applied`` = (id, name); ``failed`` = (id, name, error)."""
    steps = tuple(StepResult(cid, name, True) for cid, name in (applied or []))
    steps += tuple(
        StepResult(cid, name, False, err) for cid, name, err in (failed or [])
    )
    return LifecycleResult(
        mutation_id="m",
        guild_id=1,
        domain="channel",
        operation="delete",
        outcome=SUCCESS,
        reversibility="irreversible",
        steps=steps,
    )


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
    sel = _windowed_select(view)
    assert sel.min_values == 1
    assert sel.max_values == 2


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
async def test_confirm_routes_delete_through_service():
    view = _build_confirm([(10, "alpha"), (20, "beta")])
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.user = MagicMock()
    interaction.channel = MagicMock()

    captured: dict[str, discord.Embed] = {}

    async def _edit(_inter, *, embed, view):  # noqa: ARG001
        captured["embed"] = embed
        return True

    with (
        patch("views.channels.delete_panel.safe_defer", AsyncMock(return_value=True)),
        patch("views.channels.delete_panel.safe_edit", AsyncMock(side_effect=_edit)),
        patch(
            "views.channels.delete_panel.restore_parent_or_send_fresh",
            AsyncMock(return_value=None),
        ),
        patch("views.channels.delete_panel.asyncio.sleep", AsyncMock()),
        patch("views.channels.delete_panel.ChannelLifecycleService") as Svc,
    ):
        Svc.return_value.apply = AsyncMock(
            return_value=_result(applied=[(10, "alpha"), (20, "beta")]),
        )
        await _click(view, "Confirm Delete", interaction)

    # Routed through the audited service (emits audit + lifecycle event),
    # not a direct channel.delete():
    Svc.return_value.apply.assert_awaited_once()
    call = Svc.return_value.apply.await_args
    request = call.args[1]
    assert request.operation == "delete"
    assert request.channel_ids == (10, 20)
    assert call.kwargs.get("confirmed") is True
    field_values = " ".join(f.value for f in captured["embed"].fields)
    assert "alpha" in field_values and "beta" in field_values


@pytest.mark.asyncio
async def test_confirm_partitions_partial_failures():
    view = _build_confirm([(10, "ok"), (20, "forbidden"), (30, "gone")])
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.user = MagicMock()
    interaction.channel = MagicMock()

    captured: dict[str, discord.Embed] = {}

    async def _edit(_inter, *, embed, view):  # noqa: ARG001
        captured["embed"] = embed
        return True

    # The service reports the channel id as the name for a not-found step;
    # the panel must re-map it to the display name it captured ("gone").
    result = _result(
        applied=[(10, "ok")],
        failed=[
            (20, "forbidden", "missing permission"),
            (30, "30", "channel not found"),
        ],
    )
    with (
        patch("views.channels.delete_panel.safe_defer", AsyncMock(return_value=True)),
        patch("views.channels.delete_panel.safe_edit", AsyncMock(side_effect=_edit)),
        patch(
            "views.channels.delete_panel.restore_parent_or_send_fresh",
            AsyncMock(return_value=None),
        ),
        patch("views.channels.delete_panel.asyncio.sleep", AsyncMock()),
        patch("views.channels.delete_panel.ChannelLifecycleService") as Svc,
    ):
        Svc.return_value.apply = AsyncMock(return_value=result)
        await _click(view, "Confirm Delete", interaction)

    fields = {f.name: f.value for f in captured["embed"].fields}
    assert any("Deleted" in k and "ok" in v for k, v in fields.items())
    assert any("Permission" in k and "forbidden" in v for k, v in fields.items())
    # not-found name re-mapped from id 30 -> "gone"
    assert any("Not found" in k and "gone" in v for k, v in fields.items())

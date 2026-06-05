"""Move/reorder sub-panel (server-management PR7).

Pins that the panel routes bulk move + top/bottom reorder through the audited
``ChannelLifecycleService`` (never mutating channels directly), guards on an
empty selection / unchosen destination, and builds the right typed request.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.lifecycle import SUCCESS, LifecycleResult, StepResult


def _options(*pairs: tuple[int, str]) -> list[discord.SelectOption]:
    return [discord.SelectOption(label=n, value=str(c)) for c, n in pairs]


def _build_view(options: list[discord.SelectOption]):
    from views.channels.move_panel import _MoveSubView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    ctx.guild.categories = []
    return _MoveSubView(ctx, options=options, manager_message=None)


def _interaction() -> MagicMock:
    i = MagicMock()
    i.user = MagicMock()
    i.user.id = 1
    i.guild = MagicMock()
    i.response.send_message = AsyncMock()
    return i


def _result(outcome: str = SUCCESS, applied=(10,), failed=()) -> LifecycleResult:
    steps = tuple(StepResult(c, f"c{c}", True) for c in applied)
    steps += tuple(StepResult(c, f"c{c}", False, "missing permission") for c in failed)
    return LifecycleResult(
        mutation_id="m",
        guild_id=1,
        domain="channel",
        operation="reorder",
        outcome=outcome,
        reversibility="compensatable",
        steps=steps,
    )


async def _click(view, label: str, interaction) -> None:
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == label
    )
    btn._view = view  # discord.py binds the parent view via Item._view
    await btn.callback(interaction)


@pytest.mark.asyncio
async def test_send_to_top_routes_reorder_through_service():
    view = _build_view(_options((10, "general"), (20, "random")))
    view.selected_channel_ids = [10, 20]
    interaction = _interaction()
    with (
        patch("views.channels.move_panel.safe_defer", AsyncMock(return_value=True)),
        patch("views.channels.move_panel.safe_edit", AsyncMock()),
        patch("views.channels.move_panel.ChannelLifecycleService") as Svc,
    ):
        Svc.return_value.apply = AsyncMock(return_value=_result())
        await _click(view, "Send to Top", interaction)
    req = Svc.return_value.apply.await_args.args[1]
    assert req.operation == "reorder"
    assert req.position == "top"
    assert req.channel_ids == (10, 20)


@pytest.mark.asyncio
async def test_move_to_category_requires_destination():
    view = _build_view(_options((10, "general")))
    view.selected_channel_ids = [10]
    interaction = _interaction()
    with patch("views.channels.move_panel.ChannelLifecycleService") as Svc:
        Svc.return_value.apply = AsyncMock()
        await _click(view, "Move to Category", interaction)
    Svc.return_value.apply.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_move_to_category_routes_when_chosen():
    view = _build_view(_options((10, "general")))
    view.selected_channel_ids = [10]
    view.category_chosen = True
    view.selected_category_id = 55
    interaction = _interaction()
    with (
        patch("views.channels.move_panel.safe_defer", AsyncMock(return_value=True)),
        patch("views.channels.move_panel.safe_edit", AsyncMock()),
        patch("views.channels.move_panel.ChannelLifecycleService") as Svc,
    ):
        Svc.return_value.apply = AsyncMock(return_value=_result(outcome=SUCCESS))
        await _click(view, "Move to Category", interaction)
    req = Svc.return_value.apply.await_args.args[1]
    assert req.operation == "move"
    assert req.category_id == 55


@pytest.mark.asyncio
async def test_reorder_requires_channel_selection():
    view = _build_view(_options((10, "general")))
    interaction = _interaction()
    with patch("views.channels.move_panel.ChannelLifecycleService") as Svc:
        Svc.return_value.apply = AsyncMock()
        await _click(view, "Send to Bottom", interaction)
    Svc.return_value.apply.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()

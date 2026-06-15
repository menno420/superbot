"""Economy view family — unified BaseView lifecycle (RS10, Batch 9).

The four economy views (`_ShopView` / `_ShopSubView` / `_WorkView` /
`_WorkResultView`) carried four hand-rolled copies of ownership +
timeout handling with drifted denial copy and a silent-swallow timeout.
They now inherit BaseView's canonical handling — these tests pin the
unified behavior for the whole family (and BaseView's `on_error` hook
now covers them, which the hand-rolled versions never had).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from views.base import BaseView
from views.economy.shop_panel import _ShopSubView, _ShopView
from views.economy.work_panel import _WorkResultView, _WorkSubView, _WorkView

_AUTHOR = MagicMock(id=1)


def _family():
    with patch(
        "views.economy.shop_panel.SHOP_ITEMS",
        {"laptop": {"emoji": "💻", "price": 100, "desc": "d"}},
    ):
        yield _ShopView(_AUTHOR, 42)
        yield _ShopSubView(_AUTHOR, 42)
    yield _WorkView(_AUTHOR, 42, ["janitor"])
    yield _WorkSubView(_AUTHOR, 42, ["janitor"])
    yield _WorkResultView(_AUTHOR)


def test_every_family_member_is_a_baseview():
    for view in _family():
        assert isinstance(view, BaseView), type(view).__name__


@pytest.mark.asyncio
async def test_owner_passes_other_user_denied_with_unified_copy():
    for view in _family():
        owner = MagicMock()
        owner.user = MagicMock(id=1)
        owner.response.send_message = AsyncMock()
        assert await view.interaction_check(owner) is True, type(view).__name__

        other = MagicMock()
        other.user = MagicMock(id=99)
        other.response.send_message = AsyncMock()
        assert await view.interaction_check(other) is False, type(view).__name__
        args, kwargs = other.response.send_message.call_args
        assert args[0] == "This panel isn't yours."  # one copy for the family
        assert kwargs["ephemeral"] is True


@pytest.mark.asyncio
async def test_timeout_disables_children_and_edits_message():
    for view in _family():
        message = MagicMock()
        message.edit = AsyncMock()
        view.message = message

        await view.on_timeout()

        assert all(c.disabled for c in view.children), type(view).__name__
        message.edit.assert_awaited_once_with(view=view)


@pytest.mark.asyncio
async def test_timeout_edit_failure_is_swallowed():
    """A deleted message at timeout must not raise (BaseView logs at DEBUG
    — the old hand-rolled versions swallowed silently; behavior preserved,
    now observable).
    """
    view = _WorkResultView(_AUTHOR)
    message = MagicMock()
    message.edit = AsyncMock(side_effect=RuntimeError("message deleted"))
    view.message = message

    await view.on_timeout()  # must not raise

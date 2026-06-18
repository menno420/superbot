"""The Access Map feature drill-down select is windowed, not front-truncated.

Pins the #1040 select-truncation fix for ``AccessMapView``: a guild whose
projection lists more than Discord's 25-option cap must still expose *every*
feature for inspection across pages, and picking one still opens its source
chain as an ephemeral.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.access_projection import AccessDecision
from views.paginated_select import _PageButton, _WindowSelect
from views.server_management.access_map import AccessMapView


def _decisions(n: int) -> tuple[AccessDecision, ...]:
    return tuple(
        AccessDecision(
            feature=f"feature_{i}",
            command_name=f"cmd_{i}",
            effective="allow",
            deciding_axis=None,
            reason=None,
            source_chain=(),
            remediation=None,
        )
        for i in range(n)
    )


def _author():
    return SimpleNamespace(id=7)


def _selects(view):
    return [c for c in view.children if isinstance(c, _WindowSelect)]


def _nav(view):
    return [c for c in view.children if isinstance(c, _PageButton)]


def test_over_25_features_paginate_without_dropping_any():
    view = AccessMapView(_author(), _decisions(53), tier="user")
    select_band = _selects(view)
    assert len(select_band) == 1
    assert len(_nav(view)) == 2  # multi-page → Prev/Next present

    # Walk every page via the underlying window; no feature is dropped.
    window = select_band[0]._window
    seen: set[str] = set()
    for page in range(window.page_count):
        window.page = page
        window.render()
        cur = _selects(view)[0]
        assert len(cur.options) <= 25
        seen.update(o.value for o in cur.options)
    assert seen == {f"feature_{i}" for i in range(53)}


def test_few_features_have_no_nav():
    view = AccessMapView(_author(), _decisions(5), tier="user")
    assert len(_selects(view)) == 1
    assert _nav(view) == []


@pytest.mark.asyncio
async def test_picking_a_feature_opens_its_source_chain_ephemeral():
    view = AccessMapView(_author(), _decisions(3), tier="user")
    sel = _selects(view)[0]
    send = AsyncMock()
    interaction = SimpleNamespace(response=SimpleNamespace(send_message=send))
    await sel._window._dispatch(interaction, ["feature_1"])
    send.assert_awaited_once()
    assert send.await_args.kwargs.get("ephemeral") is True
    embed = send.await_args.kwargs.get("embed")
    assert embed is not None
    assert "feature_1" in embed.title


@pytest.mark.asyncio
async def test_unknown_feature_value_is_reported_safely():
    view = AccessMapView(_author(), _decisions(3), tier="user")
    sel = _selects(view)[0]
    send = AsyncMock()
    interaction = SimpleNamespace(response=SimpleNamespace(send_message=send))
    await sel._window._dispatch(interaction, ["nope"])
    send.assert_awaited_once()
    assert "not in the current projection" in send.await_args.args[0]

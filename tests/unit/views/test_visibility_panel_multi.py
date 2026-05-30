"""Tests for the multi-channel subsystem-visibility panel (audit P1-10).

``_VisibilitySubView`` adopted ``views.selectors.MultiSelect`` and the
shared ``_SubsystemToggleView`` now applies each toggle to *every*
selected channel.  Buttons reflect the aggregate state (mixed = blue);
clicking force-sets all channels to the next state in the cycle.  These
tests pin: the picker is multi-select with id coercion; aggregation
across channels (uniform vs mixed); the toggle writes to all channels;
a mixed group converges to ON; and partial failures are surfaced and
leave the group mixed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import governance_service
from views.selectors import MultiSelect

_ONE_SUBSYSTEM = [("economy", {"display_name": "Economy"})]


def _channels(*pairs: tuple[int, str]):
    out = []
    for cid, name in pairs:
        ch = MagicMock()
        ch.id = cid
        ch.name = name
        out.append(ch)
    return out


def _build_picker(*pairs: tuple[int, str]):
    from views.channels.visibility_panel import _VisibilitySubView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    ctx.guild.text_channels = _channels(*pairs)
    return _VisibilitySubView(ctx, manager_message=None)


def _toggle_view(channels: list[tuple[int, str]]):
    from views.channels.visibility_panel import _SubsystemToggleView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    return _SubsystemToggleView(ctx, channels=channels, manager_message=None)


def _interaction():
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild_id = 99
    return interaction


# --------------------------------------------------------------------------
# Picker
# --------------------------------------------------------------------------


def test_picker_is_multiselect():
    view = _build_picker((10, "a"), (20, "b"))
    assert isinstance(view.channel_select, MultiSelect)
    assert view.channel_select.min_values == 1


@pytest.mark.asyncio
async def test_selection_coerces_ids_and_resolves_names():
    view = _build_picker((10, "a"), (20, "b"))
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    await view._on_channels_selected(interaction, ["10", "20"])
    assert view.selected_channel_ids == [10, 20]
    assert view._selected_names() == ["#a", "#b"]


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------


def test_aggregate_uniform_vs_mixed():
    view = _toggle_view([(10, "#a"), (20, "#b")])
    view._channel_rows = [{"economy": True}, {"economy": True}]
    assert view._aggregate("economy") is True
    view._channel_rows = [{"economy": True}, {"economy": False}]
    assert view._aggregate("economy") == "mixed"
    view._channel_rows = [{}, {}]  # both inherit
    assert view._aggregate("economy") is None


@pytest.mark.asyncio
async def test_load_reads_every_channel():
    view = _toggle_view([(10, "#a"), (20, "#b")])
    rows_by_id = {10: {"economy": True}, 20: {"economy": False}}

    async def _get(_g, _t, cid):
        return dict(rows_by_id[cid])

    with (
        patch(
            "views.channels.visibility_panel.all_subsystems_sorted",
            return_value=_ONE_SUBSYSTEM,
        ),
        patch("utils.db.get_subsystem_visibility", AsyncMock(side_effect=_get)),
    ):
        await view.load(99)

    assert view._aggregate("economy") == "mixed"


# --------------------------------------------------------------------------
# Toggle writes
# --------------------------------------------------------------------------


async def _run_toggle(view, subsystem, interaction, *, set_side_effect):
    with (
        patch(
            "views.channels.visibility_panel.all_subsystems_sorted",
            return_value=_ONE_SUBSYSTEM,
        ),
        patch(
            "views.channels.visibility_panel.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch("views.channels.visibility_panel.safe_edit", AsyncMock()),
        patch("views.channels.visibility_panel.safe_followup", AsyncMock()) as followup,
        patch("views.channels.visibility_panel.GovernanceContext") as gctx,
        patch.object(
            governance_service,
            "set_subsystem_visibility",
            AsyncMock(side_effect=set_side_effect),
        ),
    ):
        gctx.from_interaction.return_value = MagicMock()
        await view._make_toggle_callback(subsystem)(interaction)
    return followup


@pytest.mark.asyncio
async def test_toggle_writes_all_channels_from_inherit_to_on():
    view = _toggle_view([(10, "#a"), (20, "#b")])
    view._channel_rows = [{}, {}]  # aggregate None -> next is True
    calls: list[tuple] = []

    async def _set(_gctx, scope, cid, sub, val):
        calls.append((scope, cid, sub, val))

    await _run_toggle(view, "economy", _interaction(), set_side_effect=_set)

    assert calls == [
        ("channel", 10, "economy", True),
        ("channel", 20, "economy", True),
    ]
    assert view._channel_rows == [{"economy": True}, {"economy": True}]


@pytest.mark.asyncio
async def test_mixed_group_converges_to_on():
    view = _toggle_view([(10, "#a"), (20, "#b")])
    view._channel_rows = [{"economy": True}, {"economy": False}]  # mixed
    vals: list[object] = []

    async def _set(_gctx, _scope, _cid, _sub, val):
        vals.append(val)

    await _run_toggle(view, "economy", _interaction(), set_side_effect=_set)

    assert vals == [True, True]  # mixed jumps straight to ON for all
    assert view._aggregate("economy") is True


@pytest.mark.asyncio
async def test_partial_failure_notifies_and_stays_mixed():
    view = _toggle_view([(10, "#a"), (20, "#b")])
    view._channel_rows = [{}, {}]  # both inherit -> next True

    async def _set(_gctx, _scope, cid, _sub, _val):
        if cid == 20:
            raise RuntimeError("boom")

    followup = await _run_toggle(view, "economy", _interaction(), set_side_effect=_set)

    # ch 10 succeeded, ch 20 left untouched -> aggregate is mixed
    assert view._channel_rows[0] == {"economy": True}
    assert view._channel_rows[1] == {}
    assert view._aggregate("economy") == "mixed"
    followup.assert_awaited_once()


# --------------------------------------------------------------------------
# Embed
# --------------------------------------------------------------------------


def test_toggle_embed_lists_channels_and_count():
    view = _toggle_view([(10, "#a"), (20, "#b")])
    embed = view.build_embed()
    assert "2 channels" in embed.title
    assert "#a" in embed.description and "#b" in embed.description

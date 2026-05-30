"""Tests for the multi-channel restrict sub-panel (audit P1-10).

``_RestrictSubView`` adopted the shared ``views.selectors.MultiSelect``
so admins can lock/unlock several channels in one action.  These tests
pin:

- the picker is a MultiSelect (not a single-select);
- selecting channels records every id and refreshes the embed;
- applying a restriction calls ``set_permissions`` once per channel and
  partitions the result into succeeded / forbidden / failed.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.selectors import MultiSelect


def _options(*pairs: tuple[int, str]) -> list[discord.SelectOption]:
    return [discord.SelectOption(label=name, value=str(cid)) for cid, name in pairs]


def _build_view(options: list[discord.SelectOption]):
    from views.channels.restrict_panel import _RestrictSubView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    return _RestrictSubView(ctx, options=options, manager_message=None)


def test_restrict_picker_is_multiselect():
    view = _build_view(_options((10, "alpha"), (20, "beta")))
    assert isinstance(view.channel_select, MultiSelect)
    # min 1, and max defaults to "all options".
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
async def test_apply_requires_a_selection():
    view = _build_view(_options((10, "alpha")))
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    await view._apply_restriction(
        interaction,
        send_messages=False,
        action_label="🔒 Lock",
        past_tense="locked",
        embed_color=discord.Color.red(),
    )
    interaction.response.send_message.assert_awaited_once()
    assert "at least one" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_lock_applies_to_every_selected_channel():
    view = _build_view(_options((10, "alpha"), (20, "beta")))
    view.selected_channel_ids = [10, 20]
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()

    ch_a = MagicMock()
    ch_a.set_permissions = AsyncMock()
    ch_b = MagicMock()
    ch_b.set_permissions = AsyncMock()
    by_id = {10: ch_a, 20: ch_b}

    captured: dict[str, discord.Embed] = {}

    async def _edit(_inter, *, embed, view):  # noqa: ARG001
        captured["embed"] = embed
        return True

    with (
        patch("views.channels.restrict_panel.resources") as mock_res,
        patch("views.channels.restrict_panel.safe_defer", AsyncMock(return_value=True)),
        patch("views.channels.restrict_panel.safe_edit", AsyncMock(side_effect=_edit)),
        patch(
            "views.channels.restrict_panel.restore_parent_or_send_fresh",
            AsyncMock(return_value=None),
        ),
        patch("views.channels.restrict_panel.asyncio.sleep", AsyncMock()),
    ):
        mock_res.resolve_channel = MagicMock(
            side_effect=lambda _g, *, channel_id, kind: by_id.get(channel_id)
        )
        await view._apply_restriction(
            interaction,
            send_messages=False,
            action_label="🔒 Lock",
            past_tense="locked",
            embed_color=discord.Color.red(),
        )

    ch_a.set_permissions.assert_awaited_once()
    ch_b.set_permissions.assert_awaited_once()
    # both channels reported as succeeded
    field_values = " ".join(f.value for f in captured["embed"].fields)
    assert "alpha" in field_values
    assert "beta" in field_values


@pytest.mark.asyncio
async def test_partial_failure_partitions_results():
    view = _build_view(_options((10, "ok"), (20, "forbidden"), (30, "gone")))
    view.selected_channel_ids = [10, 20, 30]
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()

    ch_ok = MagicMock()
    ch_ok.set_permissions = AsyncMock()
    ch_forbidden = MagicMock()
    ch_forbidden.set_permissions = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(), "nope")
    )
    by_id = {10: ch_ok, 20: ch_forbidden}  # 30 resolves to None (gone)

    captured: dict[str, discord.Embed] = {}

    async def _edit(_inter, *, embed, view):  # noqa: ARG001
        captured["embed"] = embed
        return True

    with (
        patch("views.channels.restrict_panel.resources") as mock_res,
        patch("views.channels.restrict_panel.safe_defer", AsyncMock(return_value=True)),
        patch("views.channels.restrict_panel.safe_edit", AsyncMock(side_effect=_edit)),
        patch(
            "views.channels.restrict_panel.restore_parent_or_send_fresh",
            AsyncMock(return_value=None),
        ),
        patch("views.channels.restrict_panel.asyncio.sleep", AsyncMock()),
    ):
        mock_res.resolve_channel = MagicMock(
            side_effect=lambda _g, *, channel_id, kind: by_id.get(channel_id)
        )
        await view._apply_restriction(
            interaction,
            send_messages=False,
            action_label="🔒 Lock",
            past_tense="locked",
            embed_color=discord.Color.red(),
        )

    names = {f.name: f.value for f in captured["embed"].fields}
    joined = " || ".join(f"{k}={v}" for k, v in names.items())
    assert "ok" in joined
    assert "forbidden" in joined
    assert "gone" in joined

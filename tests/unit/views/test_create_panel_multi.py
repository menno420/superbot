"""Tests for the multi-name channel-create panel (audit P1-10).

``_CreateSubView`` adopted ``views.selectors.MultiSelect`` for the name
picker: an admin can pick several preset names and add custom names, all
created under one chosen category in a single pass.  These tests pin:

- the name picker is a MultiSelect (presets), category stays single;
- preset selections + custom-modal entries compose into ``all_names``
  (de-duplicated, order preserved);
- "Create Channel" requires at least one name;
- create loops over every name under the one category and partitions the
  outcome into created / renamed / permission-denied / failed.

NB: ``create_btn`` calls ``restore_parent_or_send_fresh`` twice — first
with the *result* embed, then with the manager-panel embed — so tests
capture every embed and assert against the first (the result).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.selectors import MultiSelect


def _build_view():
    from views.channels.create_panel import _CreateSubView

    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.guild = MagicMock()
    ctx.guild.categories = []
    return _CreateSubView(ctx, manager_message=None)


async def _click(view, label: str, interaction) -> None:
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == label
    )
    btn._view = view
    await btn.callback(interaction)


def test_name_picker_is_multiselect_category_single():
    view = _build_view()
    assert isinstance(view.name_select, MultiSelect)
    assert view.name_select.min_values == 0  # custom-only allowed
    # category stays single-select
    assert view.cat_select.max_values == 1


@pytest.mark.asyncio
async def test_preset_and_custom_names_compose_dedup():
    view = _build_view()
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    await view._on_names_selected(interaction, ["general", "random"])
    # custom modal appends; "general" duplicate is dropped
    view.custom_names = ["general", "my-team"]
    assert view.all_names == ["general", "random", "my-team"]


@pytest.mark.asyncio
async def test_create_requires_at_least_one_name():
    view = _build_view()
    interaction = MagicMock()
    interaction.response.send_message = AsyncMock()
    await _click(view, "Create Channel", interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "at least one" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_create_makes_every_channel_under_one_category():
    view = _build_view()
    view.selected_presets = ["alpha", "beta"]
    view.chosen_cat = "Community"

    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()

    made: list[str] = []

    async def _create(name, category=None):  # noqa: ARG001
        made.append(name)
        ch = MagicMock()
        ch.mention = f"#{name}"
        return ch

    interaction.guild.create_text_channel = AsyncMock(side_effect=_create)
    embeds: list[discord.Embed] = []

    async def _restore(*, parent_message, channel, embed, view):  # noqa: ARG001
        embeds.append(embed)
        return MagicMock()

    with (
        patch("views.channels.create_panel.safe_defer", AsyncMock(return_value=True)),
        patch(
            "views.channels.create_panel.safe_channel_name",
            AsyncMock(side_effect=lambda _g, n: n),
        ),
        patch(
            "views.channels.create_panel.get_or_create_category",
            AsyncMock(return_value=MagicMock()),
        ),
        patch(
            "views.channels.create_panel.restore_parent_or_send_fresh",
            AsyncMock(side_effect=_restore),
        ),
        patch("views.channels.create_panel.asyncio.sleep", AsyncMock()),
    ):
        await _click(view, "Create Channel", interaction)

    assert made == ["alpha", "beta"]
    # First restore call carries the result embed (second is the manager panel).
    field_text = " ".join(f.value for f in embeds[0].fields)
    assert "#alpha" in field_text and "#beta" in field_text


@pytest.mark.asyncio
async def test_create_partitions_partial_failures():
    view = _build_view()
    view.selected_presets = ["ok", "denied", "boom"]

    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.channel = MagicMock()

    async def _create(name, category=None):  # noqa: ARG001
        if name == "denied":
            raise discord.Forbidden(MagicMock(), "no")
        if name == "boom":
            raise discord.HTTPException(MagicMock(), "boom")
        ch = MagicMock()
        ch.mention = f"#{name}"
        return ch

    interaction.guild.create_text_channel = AsyncMock(side_effect=_create)
    embeds: list[discord.Embed] = []

    async def _restore(*, parent_message, channel, embed, view):  # noqa: ARG001
        embeds.append(embed)
        return MagicMock()

    with (
        patch("views.channels.create_panel.safe_defer", AsyncMock(return_value=True)),
        patch(
            "views.channels.create_panel.safe_channel_name",
            AsyncMock(side_effect=lambda _g, n: n),
        ),
        patch(
            "views.channels.create_panel.restore_parent_or_send_fresh",
            AsyncMock(side_effect=_restore),
        ),
        patch("views.channels.create_panel.asyncio.sleep", AsyncMock()),
    ):
        await _click(view, "Create Channel", interaction)

    fields = {f.name: f.value for f in embeds[0].fields}
    joined = " || ".join(f"{k}={v}" for k, v in fields.items())
    assert "#ok" in joined
    assert "denied" in joined  # permission-denied bucket
    assert "boom" in joined  # failed bucket


@pytest.mark.asyncio
async def test_custom_modal_appends_without_duplicates():
    from views.channels.create_panel import _CustomNameModal

    view = _build_view()
    view.custom_names = ["existing"]
    view.manager_message = None

    modal = _CustomNameModal(view)
    modal.channel_name = MagicMock()
    modal.channel_name.value = "My Channel"
    interaction = MagicMock()

    with patch("views.channels.create_panel.safe_defer", AsyncMock(return_value=True)):
        await modal.on_submit(interaction)

    # normalised + appended
    assert "my-channel" in view.custom_names
    assert view.custom_names.count("existing") == 1

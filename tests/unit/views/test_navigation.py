"""Tests for the shared panel navigation helper (Phase 3.5).

Covers:

* ``attach_back_button`` adds a button with the expected label /
  custom_id / row / style.
* ``attach_back_button`` returns ``False`` and logs a WARNING when
  the view is already at Discord's 25-component cap; the button is
  not added.
* The button's callback follows defer → build → edit-in-place,
  routing through ``safe_defer`` / ``safe_edit`` so slow rebuilds
  don't exhaust Discord's 3-second response window.
* If ``safe_defer`` returns ``False`` the callback bails silently.
* If ``parent_builder`` raises after defer, the user gets an
  ephemeral via ``followup.send`` and the original message is NOT
  edited.
* If ``parent_builder`` succeeds, ``safe_edit`` swaps in the new
  ``(embed, view)``.
* ``transition_to`` defers, builds, and edits via ``safe_edit``.
* ``transition_to`` surfaces builder errors as ephemerals without
  crashing.

Migration-pin tests:

* ``help_cog._attach_back_to_help_button`` delegates to
  ``views.navigation.attach_back_button``.
* ``LoggingRoutesView.btn_back`` delegates to
  ``views.navigation.transition_to``.

These pins ensure a future edit can't quietly back-port the inline
implementation without failing CI.
"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.navigation import (
    MAX_COMPONENTS,
    NAV_HELP_ID,
    BackTarget,
    attach_back_button,
    attach_back_target,
    attach_standard_nav,
    carry_back,
    chain_back,
    has_standard_nav,
    help_nav_attachments,
    help_nav_card,
    help_nav_send_kwargs,
    transition_to,
)


def _interaction(*, is_done: bool = False) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = 7
    interaction.guild = MagicMock()
    interaction.guild_id = 42
    interaction.channel = MagicMock()
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=is_done)
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# attach_back_button — component-cap guard
# ---------------------------------------------------------------------------


def test_attach_back_button_adds_button_with_expected_props():
    view = discord.ui.View()

    async def fake_builder(_interaction):
        return discord.Embed(title="parent"), discord.ui.View()

    added = attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )
    assert added is True
    assert len(view.children) == 1
    btn = view.children[0]
    assert isinstance(btn, discord.ui.Button)
    assert btn.label == "↩ Back"
    assert btn.custom_id == "test:back"
    assert btn.row == 4
    assert btn.style == discord.ButtonStyle.secondary


def test_attach_back_button_returns_false_at_component_cap():
    view = discord.ui.View()
    # Fill to the cap. Use buttons across 5 rows.
    for i in range(MAX_COMPONENTS):
        view.add_item(
            discord.ui.Button(
                label=f"b{i}",
                custom_id=f"filler:{i}",
                style=discord.ButtonStyle.secondary,
                row=i // 5,
            ),
        )

    async def fake_builder(_interaction):
        return discord.Embed(), discord.ui.View()

    added = attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )
    assert added is False
    # The cap-filling 25 buttons are still there; nothing got added.
    assert len(view.children) == MAX_COMPONENTS


def test_attach_back_button_warns_when_skipping(caplog):
    import logging as stdlib_logging

    caplog.set_level(stdlib_logging.WARNING, logger="bot.views.navigation")
    view = discord.ui.View()
    for i in range(MAX_COMPONENTS):
        view.add_item(
            discord.ui.Button(
                label=f"b{i}",
                custom_id=f"filler:{i}",
                style=discord.ButtonStyle.secondary,
                row=i // 5,
            ),
        )

    async def fake_builder(_interaction):
        return discord.Embed(), discord.ui.View()

    attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )
    # The skip was logged at WARNING — operators must be able to see it.
    assert any("skipped" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# attach_back_button — click-time behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_attach_back_button_callback_defers_before_calling_builder():
    """The Back callback must follow defer → build → edit-in-place.

    A shared ``order`` list records every step; the final assertion
    catches both "builder before defer" and "edit before build"
    regressions in one check.
    """
    view = discord.ui.View()
    parent_embed = discord.Embed(title="parent")
    parent_view = discord.ui.View()
    order: list[str] = []

    async def fake_defer(_interaction, **_kwargs):
        order.append("defer")
        return True

    async def fake_builder(_interaction):
        order.append("builder")
        return parent_embed, parent_view

    async def fake_edit(_interaction, **_kwargs):
        order.append("edit")
        return True

    attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )

    interaction = _interaction()
    btn = view.children[0]
    with (
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            AsyncMock(side_effect=fake_defer),
        ),
        patch(
            "core.runtime.interaction_helpers.safe_edit",
            AsyncMock(side_effect=fake_edit),
        ) as patched_edit,
    ):
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    assert order == ["defer", "builder", "edit"]
    _args, kwargs = patched_edit.call_args
    assert kwargs["embed"] is parent_embed
    assert kwargs["view"] is parent_view
    # A cardless parent clears any prior screen's attachment (navigate-away).
    assert kwargs["attachments"] == []


@pytest.mark.asyncio
async def test_attach_back_button_callback_forwards_the_parent_help_nav_card():
    """Forward-path pin (help-nav attachment seam, H3): when the rebuilt parent
    carries a ``help_nav_card``, the in-place edit must forward it as
    ``attachments=[card]`` so the card survives the back-navigation. A future
    edit that drops the forwarding fails here.
    """
    view = discord.ui.View()
    parent_embed = discord.Embed(title="parent")
    parent_view = discord.ui.View()
    card = discord.File(io.BytesIO(b"\x89PNG\r\n\x1a\nfake"), filename="card.png")
    parent_view.help_nav_card = card  # type: ignore[attr-defined]

    async def fake_builder(_interaction):
        return parent_embed, parent_view

    attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )

    interaction = _interaction()
    btn = view.children[0]
    with (
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch(
            "core.runtime.interaction_helpers.safe_edit",
            AsyncMock(return_value=True),
        ) as patched_edit,
    ):
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    _args, kwargs = patched_edit.call_args
    assert kwargs["attachments"] == [card]


@pytest.mark.asyncio
async def test_attach_back_button_callback_aborts_when_defer_fails():
    """When ``safe_defer`` returns ``False`` the callback must bail
    silently: no builder call, no edit, no followup.
    """
    view = discord.ui.View()

    async def fake_builder(_interaction):
        raise AssertionError("builder must not be called when defer fails")

    attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )

    interaction = _interaction()
    btn = view.children[0]
    with (
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            AsyncMock(return_value=False),
        ),
        patch(
            "core.runtime.interaction_helpers.safe_edit",
            AsyncMock(),
        ) as fake_edit,
    ):
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    fake_edit.assert_not_called()
    interaction.followup.send.assert_not_called()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_attach_back_button_callback_surfaces_builder_error_as_followup_ephemeral():
    """When the builder raises after defer, the user must see an
    ephemeral via ``followup.send`` and the original message must be
    left untouched. The old pre-defer ``response.send_message`` route
    must not be reachable.
    """
    view = discord.ui.View()

    async def fake_builder(_interaction):
        raise RuntimeError("governance unavailable")

    attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
        error_message="Couldn't load help — please retry.",
    )

    interaction = _interaction()
    btn = view.children[0]
    with (
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch(
            "core.runtime.interaction_helpers.safe_edit",
            AsyncMock(),
        ) as fake_edit,
    ):
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.followup.send.assert_awaited_once()
    args, kwargs = interaction.followup.send.call_args
    assert "Couldn't load help" in (args[0] if args else kwargs.get("content", ""))
    assert kwargs.get("ephemeral") is True
    fake_edit.assert_not_called()
    interaction.response.edit_message.assert_not_called()
    interaction.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_attach_back_button_callback_success_calls_safe_defer_and_safe_edit():
    """Happy path: ``safe_defer`` and ``safe_edit`` are both awaited,
    the builder receives the click interaction, and the raw
    ``response.edit_message`` / ``edit_original_response`` routes are
    not touched.
    """
    view = discord.ui.View()
    parent_embed = discord.Embed(title="parent")
    parent_view = discord.ui.View()
    captured: list[discord.Interaction] = []

    async def fake_builder(interaction):
        captured.append(interaction)
        return parent_embed, parent_view

    attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )

    interaction = _interaction()
    btn = view.children[0]
    with (
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            AsyncMock(return_value=True),
        ) as fake_defer,
        patch(
            "core.runtime.interaction_helpers.safe_edit",
            AsyncMock(return_value=True),
        ) as fake_edit,
    ):
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    fake_defer.assert_awaited_once()
    assert len(captured) == 1
    assert captured[0] is interaction
    fake_edit.assert_awaited_once()
    _args, kwargs = fake_edit.call_args
    assert kwargs["embed"] is parent_embed
    assert kwargs["view"] is parent_view
    interaction.response.edit_message.assert_not_called()
    interaction.edit_original_response.assert_not_called()


# ---------------------------------------------------------------------------
# transition_to
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transition_to_defers_then_builds_then_edits():
    interaction = _interaction()
    parent_embed = discord.Embed(title="parent")
    parent_view = discord.ui.View()

    async def fake_builder(_interaction):
        return parent_embed, parent_view

    # Patch the in-module imports used by transition_to.
    with (
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            AsyncMock(return_value=True),
        ) as fake_defer,
        patch(
            "core.runtime.interaction_helpers.safe_edit",
            AsyncMock(),
        ) as fake_edit,
    ):
        await transition_to(interaction, builder=fake_builder)

    fake_defer.assert_awaited_once()
    fake_edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_transition_to_aborts_when_defer_fails():
    interaction = _interaction()

    async def fake_builder(_interaction):
        raise AssertionError("builder must not be called when defer fails")

    with (
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            AsyncMock(return_value=False),
        ),
        patch(
            "core.runtime.interaction_helpers.safe_edit",
            AsyncMock(),
        ) as fake_edit,
    ):
        await transition_to(interaction, builder=fake_builder)

    fake_edit.assert_not_called()


@pytest.mark.asyncio
async def test_transition_to_surfaces_builder_error_as_ephemeral():
    interaction = _interaction()

    async def fake_builder(_interaction):
        raise RuntimeError("boom")

    with (
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch(
            "core.runtime.interaction_helpers.safe_edit",
            AsyncMock(),
        ) as fake_edit,
    ):
        await transition_to(
            interaction,
            builder=fake_builder,
            error_message="Cleanup couldn't open — see logs.",
        )

    fake_edit.assert_not_called()
    interaction.followup.send.assert_awaited_once()


# ---------------------------------------------------------------------------
# Migration-pin tests
# ---------------------------------------------------------------------------


def test_help_cog_back_button_uses_shared_navigation_helper():
    """``help_cog._attach_back_to_help_button`` must call into
    ``views.navigation.attach_back_button``. Pins the migration
    against an accidental in-line revert.
    """
    import inspect

    from cogs import help_cog

    src = inspect.getsource(help_cog._attach_back_to_help_button)
    assert "attach_back_button" in src
    assert "views.navigation" in src or "from views.navigation" in src


def test_help_cog_back_button_rebuilds_category_view_via_governance():
    """S3: the help-specific builder kept inside ``help_cog`` must still
    re-resolve the audience at click time (so visibility/tier are fresh)
    and must rebuild :class:`HelpCategoryView` — the new top of Help.

    HLP-2/3: the click-time resolve goes through the cog's one projection
    seam (``_resolve_projection`` = governance ``resolve_visibility`` +
    the guild Help overlay), so this pins the builder calling the seam and
    the seam containing the governance resolve.
    """
    import inspect

    from cogs import help_cog

    src = inspect.getsource(help_cog._attach_back_to_help_button)
    # The audience is still resolved at click time — via the projection seam.
    assert "_resolve_projection" in src
    seam_src = inspect.getsource(help_cog._resolve_projection)
    assert "resolve_visibility" in seam_src
    # The new top-of-Help is the category index, not the paginated list.
    assert "HelpCategoryView" in src
    assert "build_categories_overview_embed" in src


def test_logging_routes_back_uses_shared_navigation_helper():
    """``LoggingRoutesView.btn_back`` must call into
    ``views.navigation.transition_to``. Pins the migration.

    ``@discord.ui.button`` leaves the decorated function as a plain
    function on the class (with ``__discord_ui_model_*`` annotations);
    ``inspect.getsource`` works on it directly.
    """
    import inspect

    from cogs.logging.routes_panel import LoggingRoutesView

    src = inspect.getsource(LoggingRoutesView.btn_back)
    assert "transition_to" in src
    assert "views.navigation" in src or "from views.navigation" in src


# ---------------------------------------------------------------------------
# BackTarget / attach_back_target / chain_back (AB2)
# ---------------------------------------------------------------------------


async def _stub_builder(_interaction):
    return discord.Embed(title="stub"), discord.ui.View()


def test_back_target_is_frozen_and_hashable():
    """``BackTarget`` is a frozen dataclass — values are immutable and
    the instance is hashable so it can be safely stashed on views
    without surprising aliasing.
    """
    target = BackTarget(
        builder=_stub_builder,
        label="↩ Back to X",
        custom_id="x:back",
    )
    # Hashable.
    {target}
    # Frozen.
    with pytest.raises(Exception):
        target.label = "mutated"  # type: ignore[misc]


def test_attach_back_target_delegates_to_attach_back_button():
    """``attach_back_target(view, target)`` is equivalent to
    ``attach_back_button(view, label=…, custom_id=…, parent_builder=…)``
    — verify the button properties match.
    """
    view = discord.ui.View()
    target = BackTarget(
        builder=_stub_builder,
        label="↩ Back to X",
        custom_id="x:back",
    )

    added = attach_back_target(view, target)

    assert added is True
    assert len(view.children) == 1
    btn = view.children[0]
    assert isinstance(btn, discord.ui.Button)
    assert btn.label == target.label
    assert btn.custom_id == target.custom_id


def test_chain_back_identity_when_no_grandparent():
    """With ``grandparent=None``, ``chain_back`` returns the builder
    unchanged — direct-entry openers must not pick up a spurious
    back button on rebuild.
    """
    wrapped = chain_back(_stub_builder, None)
    assert wrapped is _stub_builder


@pytest.mark.asyncio
async def test_chain_back_re_attaches_grandparent_on_rebuild():
    """When ``grandparent`` is provided, the wrapped builder rebuilds
    the parent AND attaches the grandparent's back button on it.
    """
    parent_embed = discord.Embed(title="parent")
    parent_view = discord.ui.View()

    async def builder(_interaction):
        return parent_embed, parent_view

    grandparent = BackTarget(
        builder=_stub_builder,
        label="↩ Back to Grandparent",
        custom_id="gp:back",
    )

    wrapped = chain_back(builder, grandparent)
    # Not the identity transform when grandparent is provided.
    assert wrapped is not builder

    embed, view = await wrapped(_interaction())
    assert embed is parent_embed
    assert view is parent_view
    # The rebuilt view now carries the grandparent's button.
    custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert "gp:back" in custom_ids


@pytest.mark.asyncio
async def test_chain_back_composes_arbitrarily_deep():
    """Composition is associative: a chain of three builders unwinds
    via two ``chain_back`` calls and the rebuilt top-most view ends
    up carrying both intermediate back buttons.
    """
    top_view = discord.ui.View()

    async def build_top(_interaction):
        return discord.Embed(title="top"), top_view

    mid_target = BackTarget(
        builder=build_top,
        label="↩ Back to Top",
        custom_id="top:back",
    )

    async def build_middle(_interaction):
        return discord.Embed(title="middle"), discord.ui.View()

    composed_mid = chain_back(build_middle, mid_target)
    leaf_target = BackTarget(
        builder=composed_mid,
        label="↩ Back to Middle",
        custom_id="middle:back",
    )

    leaf_view = discord.ui.View()
    attach_back_target(leaf_view, leaf_target)
    # Leaf has back-to-middle.
    leaf_custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in leaf_view.children
        if isinstance(c, discord.ui.Button)
    }
    assert "middle:back" in leaf_custom_ids

    # Pressing back-to-middle invokes the composed builder; the
    # rebuilt middle view must carry back-to-top.
    middle_btn = next(
        c
        for c in leaf_view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "middle:back"
    )
    interaction = _interaction()
    await middle_btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    rebuilt_middle = kwargs["view"]
    mid_custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in rebuilt_middle.children
        if isinstance(c, discord.ui.Button)
    }
    assert "top:back" in mid_custom_ids


# ---------------------------------------------------------------------------
# Help cog stashes BackTarget for downstream chain composition (AB2)
# ---------------------------------------------------------------------------


def test_help_cog_back_button_stashes_back_target():
    """``_attach_back_to_help_button`` must stash a ``BackTarget`` on
    the view so downstream openers can use ``chain_back`` to keep
    back-to-Help attached when they rebuild their own parent panels.
    """
    from cogs import help_cog

    view = discord.ui.View()
    help_cog._attach_back_to_help_button(view)
    target = getattr(view, "_back_target", None)
    assert target is not None
    assert isinstance(target, BackTarget)
    assert target.label == "↩ Back to Help"
    assert target.custom_id == "help:back"


# ---------------------------------------------------------------------------
# Economy back chain (AB2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_attach_back_to_economy_button_re_attaches_grandparent():
    """If ``attach_back_to_economy_button`` is called with a grandparent,
    the rebuilt Economy panel produced by clicking back-to-Economy
    must also have the grandparent's button re-attached. This is the
    Help → Economy → Inventory → back path.
    """
    from views.economy.main_panel import attach_back_to_economy_button

    grandparent = BackTarget(
        builder=_stub_builder,
        label="↩ Back to Help",
        custom_id="help:back",
    )

    view = discord.ui.View()
    author = MagicMock()

    # Patch the binding at the point of use — main_panel imports the
    # helper at module load, so patching the source module would not
    # affect the rebound reference.
    with patch(
        "views.economy.main_panel._build_economy_embed",
        AsyncMock(return_value=discord.Embed(title="Economy")),
    ):
        attach_back_to_economy_button(view, author, grandparent=grandparent)

        # The Inventory view now has back-to-Economy.
        economy_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "economy:back"
        )

        # Clicking back-to-Economy rebuilds Economy. The rebuilt view
        # must carry back-to-Help (grandparent).
        interaction = _interaction()
        await economy_btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    rebuilt_economy = kwargs["view"]
    rebuilt_custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in rebuilt_economy.children
        if isinstance(c, discord.ui.Button)
    }
    assert "help:back" in rebuilt_custom_ids


def test_attach_back_to_economy_button_stashes_back_target_on_child():
    """The Inventory view must receive ``_back_target`` so its own
    children (e.g. a Category view) can chain back through Economy
    if they want to rebuild.
    """
    from views.economy.main_panel import attach_back_to_economy_button

    view = discord.ui.View()
    attach_back_to_economy_button(view, MagicMock(), grandparent=None)
    target = getattr(view, "_back_target", None)
    assert target is not None
    assert isinstance(target, BackTarget)
    assert target.label == "↩ Back to Economy"
    assert target.custom_id == "economy:back"


def _shop_view_back_button(shop_view) -> discord.ui.Button:
    """Look up the ``↩ Back`` button from a ``_ShopSubView`` instance.

    The decorator-defined button is added to ``children`` on view
    construction; iterate to find it rather than calling the raw
    function descriptor on the class.
    """
    for child in shop_view.children:
        if (
            isinstance(child, discord.ui.Button)
            and child.label is not None
            and "Back" in child.label
        ):
            return child
    raise AssertionError("Shop subview has no Back button")


@pytest.mark.asyncio
async def test_shop_subview_back_btn_re_attaches_origin_on_rebuild():
    """When ``_ShopSubView`` was opened from an EconomyPanelView that
    has a propagated origin (e.g. back-to-Help), the shop's Back
    button must re-attach that origin on the rebuilt Economy.
    """
    from views.economy.shop_panel import _ShopSubView

    shop_view = _ShopSubView(MagicMock(id=1), guild_id=42)
    # Mimic the propagation that EconomyPanelView.shop_btn does.
    shop_view._back_target = BackTarget(  # type: ignore[attr-defined]
        builder=_stub_builder,
        label="↩ Back to Help",
        custom_id="help:back",
    )

    interaction = _interaction()
    interaction.guild_id = 42

    with patch(
        "views.economy.shop_panel._build_economy_embed",
        AsyncMock(return_value=discord.Embed(title="Economy")),
    ):
        await _shop_view_back_button(shop_view).callback(  # type: ignore[union-attr,misc]
            interaction,
        )

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    rebuilt_economy = kwargs["view"]
    rebuilt_custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in rebuilt_economy.children
        if isinstance(c, discord.ui.Button)
    }
    assert "help:back" in rebuilt_custom_ids


@pytest.mark.asyncio
async def test_shop_subview_back_btn_with_no_origin_omits_chain():
    """When ``_ShopSubView`` was opened directly (e.g. !shop / direct
    !economymenu → shop), there is no origin to chain — the rebuilt
    Economy must NOT have a spurious back button.
    """
    from views.economy.shop_panel import _ShopSubView

    shop_view = _ShopSubView(MagicMock(id=1), guild_id=42)
    # No _back_target propagated.

    interaction = _interaction()
    interaction.guild_id = 42

    with patch(
        "views.economy.shop_panel._build_economy_embed",
        AsyncMock(return_value=discord.Embed(title="Economy")),
    ):
        await _shop_view_back_button(shop_view).callback(  # type: ignore[union-attr,misc]
            interaction,
        )

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    rebuilt_economy = kwargs["view"]
    rebuilt_custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in rebuilt_economy.children
        if isinstance(c, discord.ui.Button)
    }
    # No spurious back buttons.
    assert "help:back" not in rebuilt_custom_ids
    assert "economy:back" not in rebuilt_custom_ids


# ---------------------------------------------------------------------------
# carry_back — the games/admin panel back-loss fix
# ---------------------------------------------------------------------------
#
# Regression guard for the class the owner's live walk surfaced (2026-06-23):
# a panel that redraws onto a FRESH view instance on an action (the
# edit_in_place idiom) dropped the Back-to-[hub] button the hub attached to the
# ORIGINAL instance. carry_back() re-applies it. This is the runtime check the
# static `back_button` consistency rule structurally cannot make (it only checks
# a view CLASS has a back affordance somewhere, not that a redraw keeps it).


async def _parent_builder(_interaction):
    return discord.Embed(title="parent"), discord.ui.View()


def _back_ids(view: discord.ui.View) -> set[str]:
    return {
        b.custom_id
        for b in view.children
        if isinstance(b, discord.ui.Button) and b.custom_id
    }


def test_carry_back_reattaches_back_to_a_fresh_view():
    old = discord.ui.View()
    attach_back_button(
        old,
        label="↩ Back to Games",
        custom_id="games:back",
        parent_builder=_parent_builder,
    )
    assert "games:back" in _back_ids(old)

    new = discord.ui.View()  # the fresh redraw instance — no back of its own
    assert "games:back" not in _back_ids(new)

    carry_back(old, new)
    assert "games:back" in _back_ids(new)  # the fix: it survives the redraw


def test_carry_back_replays_every_recorded_back():
    """Both Back-to-[hub] and a chained Back-to-Help survive together."""
    old = discord.ui.View()
    attach_back_button(
        old,
        label="↩ Back to Games",
        custom_id="games:back",
        parent_builder=_parent_builder,
    )
    attach_back_button(
        old,
        label="↩ Back to Help",
        custom_id="help:back",
        parent_builder=_parent_builder,
    )
    new = discord.ui.View()
    carry_back(old, new)
    assert {"games:back", "help:back"} <= _back_ids(new)


def test_carry_back_is_noop_without_a_recorded_back():
    old = discord.ui.View()  # never had a back attached
    new = discord.ui.View()
    carry_back(old, new)  # must not raise
    assert _back_ids(new) == set()


def test_carry_back_carries_the_back_target_for_chaining():
    old = discord.ui.View()
    target = BackTarget(
        label="↩ Back to Help",
        custom_id="help:back",
        builder=_parent_builder,
    )
    attach_back_target(old, target)
    new = discord.ui.View()
    carry_back(old, new)
    assert getattr(new, "_back_target", None) is target


# ---------------------------------------------------------------------------
# Idempotency guard (the lynchpin that lets auto-nav coexist with the legacy
# external back-pushers without ever duplicating a control).
# ---------------------------------------------------------------------------


def test_attach_back_button_is_idempotent_by_custom_id():
    view = discord.ui.View()
    assert attach_back_button(
        view, label="A", custom_id="dup", parent_builder=_parent_builder,
    )
    # Second attach with the same custom_id (different label) is a no-op.
    assert attach_back_button(
        view, label="B", custom_id="dup", parent_builder=_parent_builder,
    )
    dup_buttons = [c for c in view.children if getattr(c, "custom_id", None) == "dup"]
    assert len(dup_buttons) == 1
    assert dup_buttons[0].label == "A"  # the first one wins


# ---------------------------------------------------------------------------
# Standard nav — the "never stranded" auto-attach (owner directive 2026-06-23).
# ---------------------------------------------------------------------------


class _NavView(discord.ui.View):
    """A minimal view that opts into standard nav for a given subsystem."""

    def __init__(self, subsystem: str, *, standard_nav: bool = True) -> None:
        super().__init__(timeout=None)
        self.SUBSYSTEM = subsystem
        self.STANDARD_NAV = standard_nav
        attach_standard_nav(self)


def test_standard_nav_attaches_help_and_back_to_hub_for_a_child_subsystem():
    # farm → parent_hub "games"
    view = _NavView("farm")
    assert _back_ids(view) == {NAV_HELP_ID, "nav:hub:games"}
    assert has_standard_nav(view)


def test_standard_nav_attaches_only_help_for_a_top_level_hub():
    # games is a mother hub — no parent_hub, so only the Help button.
    view = _NavView("games")
    assert _back_ids(view) == {NAV_HELP_ID}


def test_standard_nav_skips_help_button_on_the_help_menu_itself():
    view = _NavView("help")
    assert _back_ids(view) == set()


def test_standard_nav_is_noop_without_a_subsystem():
    view = discord.ui.View()
    attach_standard_nav(view)  # no SUBSYSTEM attr
    assert _back_ids(view) == set()
    assert not has_standard_nav(view)


def test_standard_nav_respects_the_opt_out_flag():
    view = _NavView("farm", standard_nav=False)
    assert _back_ids(view) == set()


def test_standard_nav_is_idempotent_across_redraws():
    view = _NavView("farm")
    before = _back_ids(view)
    attach_standard_nav(view)  # a second construction-style call
    assert _back_ids(view) == before


def test_standard_nav_skips_unknown_subsystem():
    view = _NavView("not_a_real_subsystem")
    assert _back_ids(view) == set()


class _OverviewNavView(discord.ui.View):
    """A SUBSYSTEM panel whose only nav-shaped control is a labelled button —
    the ``LoggingPanelView`` / ``EconomyPanelView`` shape (an ``↩ Overview``
    self-refresh). The button is added before ``attach_standard_nav`` so the
    ``_self_navigates`` heuristic sees it, as it does at runtime.
    """

    def __init__(self, subsystem: str, label: str) -> None:
        super().__init__(timeout=None)
        self.SUBSYSTEM = subsystem
        self.add_item(discord.ui.Button(label=label, custom_id="panel.local"))
        attach_standard_nav(self)


def test_standard_nav_covers_a_panel_whose_only_nav_is_overview():
    """Regression (LoggingPanelView / EconomyPanelView): an ``↩ Overview``
    button is a self-refresh, NOT parent-nav, so a panel whose only nav-shaped
    control is Overview must still receive the universal Help + hub back.
    """
    view = _OverviewNavView("farm", "↩ Overview")  # farm → parent_hub games
    assert {NAV_HELP_ID, "nav:hub:games"} <= _back_ids(view)


def test_standard_nav_skips_a_panel_with_its_own_back_to_parent():
    """A genuine ``↩ Back to <parent>`` button IS self-navigation — the panel
    keeps its own nav and must not get a duplicate from auto-nav.
    """
    view = _OverviewNavView("farm", "↩ Back to Games")
    ids = _back_ids(view)
    assert NAV_HELP_ID not in ids
    assert "nav:hub:games" not in ids


def test_has_standard_nav_detects_hub_back_without_help():
    view = discord.ui.View()
    attach_back_button(
        view, label="↩ Games", custom_id="nav:hub:games", parent_builder=_parent_builder,
    )
    assert has_standard_nav(view)


# ---------------------------------------------------------------------------
# Help-nav attachment seam (visual card-engine H3): the view carries its own
# image card via ``help_nav_card``; render sites forward it. A view without the
# attribute (every embed-only hub, the default) yields no card → embed-only.
# ---------------------------------------------------------------------------


class _CardView(discord.ui.View):
    """Minimal view that opts into the help-nav card seam."""

    def __init__(self, card: object) -> None:
        super().__init__()
        self.help_nav_card = card  # type: ignore[assignment]


def _png() -> discord.File:
    return discord.File(io.BytesIO(b"\x89PNG\r\n\x1a\nfake"), filename="card.png")


def test_help_nav_card_returns_the_file_when_present():
    card = _png()
    assert help_nav_card(_CardView(card)) is card


def test_help_nav_card_is_none_when_absent_or_view_is_none():
    # A plain view (no attribute) and ``None`` both yield no card — the default
    # embed-only behaviour every un-migrated hub keeps.
    assert help_nav_card(discord.ui.View()) is None
    assert help_nav_card(None) is None


def test_help_nav_card_ignores_a_non_file_attribute():
    # Defensive: a stray non-File value must not crash navigation.
    assert help_nav_card(_CardView("not-a-file")) is None
    assert help_nav_card(_CardView(None)) is None


def test_help_nav_attachments_sets_or_clears():
    card = _png()
    # A card → ``[card]`` (sets it on the in-place edit).
    assert help_nav_attachments(_CardView(card)) == [card]
    # No card → ``[]`` (clears any prior screen's attachment).
    assert help_nav_attachments(_CardView(None)) == []
    assert help_nav_attachments(discord.ui.View()) == []


def test_help_nav_send_kwargs_omits_file_when_no_card():
    card = _png()
    # A card → ``{"file": card}``; no card → ``{}`` so a fresh send never passes
    # ``file=None`` (which ``InteractionResponse.send_message`` mis-reads as a
    # broken attachment rather than "no file").
    assert help_nav_send_kwargs(_CardView(card)) == {"file": card}
    assert help_nav_send_kwargs(_CardView(None)) == {}
    assert help_nav_send_kwargs(discord.ui.View()) == {}

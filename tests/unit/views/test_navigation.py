"""Tests for the shared panel navigation helper (Phase 3.5).

Covers:

* ``attach_back_button`` adds a button with the expected label /
  custom_id / row / style.
* ``attach_back_button`` returns ``False`` and logs a WARNING when
  the view is already at Discord's 25-component cap; the button is
  not added.
* The button's callback calls ``parent_builder`` at click time.
* If ``parent_builder`` raises, the user gets an ephemeral fallback
  and the original message is NOT edited.
* If ``parent_builder`` succeeds, the message is edited in place
  with the new ``(embed, view)``.
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

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.navigation import (
    MAX_COMPONENTS,
    attach_back_button,
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
async def test_attach_back_button_callback_calls_parent_builder_at_click_time():
    view = discord.ui.View()
    captured_interaction: list[discord.Interaction] = []
    parent_embed = discord.Embed(title="parent")
    parent_view = discord.ui.View()

    async def fake_builder(interaction):
        captured_interaction.append(interaction)
        return parent_embed, parent_view

    attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )

    interaction = _interaction()
    btn = view.children[0]
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    assert len(captured_interaction) == 1
    assert captured_interaction[0] is interaction
    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is parent_embed
    assert kwargs["view"] is parent_view


@pytest.mark.asyncio
async def test_attach_back_button_callback_surfaces_builder_error_as_ephemeral():
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

    interaction = _interaction(is_done=False)
    btn = view.children[0]
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    args, kwargs = interaction.response.send_message.call_args
    assert "Couldn't load help" in (args[0] if args else kwargs.get("content", ""))
    assert kwargs.get("ephemeral") is True
    # The original message is NOT edited.
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_attach_back_button_callback_uses_edit_original_when_deferred():
    """If the interaction was already deferred before the button fires
    (e.g. by an upstream handler), edit_message would 4xx — fall through
    to edit_original_response."""
    view = discord.ui.View()
    parent_embed = discord.Embed(title="parent")
    parent_view = discord.ui.View()

    async def fake_builder(_interaction):
        return parent_embed, parent_view

    attach_back_button(
        view,
        label="↩ Back",
        custom_id="test:back",
        parent_builder=fake_builder,
    )
    interaction = _interaction(is_done=True)
    btn = view.children[0]
    await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.edit_original_response.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


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
    with patch(
        "core.runtime.interaction_helpers.safe_defer",
        AsyncMock(return_value=True),
    ) as fake_defer, patch(
        "core.runtime.interaction_helpers.safe_edit",
        AsyncMock(),
    ) as fake_edit:
        await transition_to(interaction, builder=fake_builder)

    fake_defer.assert_awaited_once()
    fake_edit.assert_awaited_once()


@pytest.mark.asyncio
async def test_transition_to_aborts_when_defer_fails():
    interaction = _interaction()

    async def fake_builder(_interaction):
        raise AssertionError("builder must not be called when defer fails")

    with patch(
        "core.runtime.interaction_helpers.safe_defer",
        AsyncMock(return_value=False),
    ), patch(
        "core.runtime.interaction_helpers.safe_edit",
        AsyncMock(),
    ) as fake_edit:
        await transition_to(interaction, builder=fake_builder)

    fake_edit.assert_not_called()


@pytest.mark.asyncio
async def test_transition_to_surfaces_builder_error_as_ephemeral():
    interaction = _interaction()

    async def fake_builder(_interaction):
        raise RuntimeError("boom")

    with patch(
        "core.runtime.interaction_helpers.safe_defer",
        AsyncMock(return_value=True),
    ), patch(
        "core.runtime.interaction_helpers.safe_edit",
        AsyncMock(),
    ) as fake_edit:
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


def test_help_cog_back_button_still_clamps_pagination_in_builder():
    """The help-specific builder kept inside ``help_cog`` must still
    re-resolve governance and clamp pagination — that logic is help's
    concern, not the shared helper's.
    """
    import inspect

    from cogs import help_cog

    src = inspect.getsource(help_cog._attach_back_to_help_button)
    assert "resolve_visibility" in src
    assert "math.ceil" in src or "_PAGE_SIZE" in src
    assert "parent_hub" in src  # the Phase 4 filter pin


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

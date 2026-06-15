"""Tests for the wizard navigation/rendering helper.

Covers the two public functions in :mod:`views.setup.wizard_nav`:

* :func:`render_wizard_step` — rebuilds the wizard anchor at a given
  step and edits it in place via :func:`safe_edit`.
* :func:`render_step_detail` — swaps the anchor to a section's detail
  embed + view, with an injected ``↩ Back to step`` button on row 4
  whose callback restores the wizard view.

All tests follow the existing setup test style (``MagicMock`` + ``AsyncMock``,
patching service modules, no real Discord or DB).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import views.setup.sections  # noqa: F401 — populate REGISTRY for tests
from services.setup_sections import SetupSection
from services.setup_session import SetupSession
from views.setup import wizard_nav


async def _noop_run(interaction, hub):  # pragma: no cover
    return None


def _section(slug: str = "fake", *, with_detail: bool = False) -> SetupSection:
    embed_builder = (
        AsyncMock(return_value=discord.Embed(title=f"{slug} detail"))
        if with_detail
        else None
    )
    view_builder = MagicMock(return_value=discord.ui.View()) if with_detail else None
    return SetupSection(
        slug=slug,
        label=slug.title(),
        style=discord.ButtonStyle.secondary,
        run=_noop_run,
        emoji="🛰",
        order=10,
        op_kinds=frozenset(),
        detail_embed_builder=embed_builder,
        detail_view_builder=view_builder,
    )


def _session(current_step: str | None = None) -> SetupSession:
    return SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=current_step,
        delegated_admins=(),
        depth=None,
    )


def _owner_member():
    m = MagicMock(spec=discord.Member)
    m.id = 99
    m.guild = SimpleNamespace(owner_id=99)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _interaction(member):
    interaction = MagicMock()
    interaction.user = member
    interaction.guild_id = 1
    interaction.guild = MagicMock(id=1, name="Test", owner_id=99)
    interaction.message = MagicMock(id=4242)
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.edit_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# render_wizard_step
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_render_wizard_step_edits_anchor_inline():
    """render_wizard_step builds a wizard embed + view and calls safe_edit."""
    from services.setup_sections import REGISTRY

    section = _section("zz_render_test")
    REGISTRY.register(section)
    try:
        guild = MagicMock(spec=discord.Guild)
        guild.id = 1
        member = _owner_member()
        interaction = _interaction(member)
        session = _session(current_step="zz_render_test")

        with (
            patch(
                "views.setup.wizard_nav.setup_session.resume_session",
                new_callable=AsyncMock,
                return_value=session,
            ),
            patch(
                "views.setup.wizard_nav.setup_draft.list_rows",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "views.setup.wizard_nav.safe_edit",
                new_callable=AsyncMock,
                return_value=True,
            ) as safe_edit_mock,
        ):
            ok = await wizard_nav.render_wizard_step(
                interaction,
                guild=guild,
                member=member,
                session=session,
                step_index=None,
            )

        assert ok is True
        safe_edit_mock.assert_awaited_once()
        kw = safe_edit_mock.await_args.kwargs
        # safe_edit receives both an embed and the new wizard view.
        assert isinstance(kw["embed"], discord.Embed)
        from views.setup.wizard import LinearWizardView

        assert isinstance(kw["view"], LinearWizardView)
    finally:
        REGISTRY.unregister("zz_render_test")


# ---------------------------------------------------------------------------
# render_step_detail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_render_step_detail_swaps_anchor_to_detail_embed_and_view():
    """render_step_detail edits the anchor with the section's detail
    embed + view, with an injected Back-to-step button on row 4.
    """
    section = _section("zz_detail_test", with_detail=True)
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    member = _owner_member()
    interaction = _interaction(member)
    session = _session()

    with (
        patch(
            "views.setup.wizard_nav.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.wizard_nav.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
        patch(
            "views.setup.wizard_nav.safe_edit",
            new_callable=AsyncMock,
            return_value=True,
        ) as safe_edit_mock,
        patch(
            "views.setup.wizard_nav.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        ok = await wizard_nav.render_step_detail(
            interaction,
            guild=guild,
            member=member,
            session=session,
            section=section,
            step_index=2,
        )

    assert ok is True
    section.detail_embed_builder.assert_awaited_once()
    section.detail_view_builder.assert_called_once()
    safe_edit_mock.assert_awaited_once()
    kw = safe_edit_mock.await_args.kwargs
    view = kw["view"]
    # The injected Back button lives on row 4 with a back_to_step custom_id.
    back_buttons = [
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id
        and c.custom_id.startswith("setup_wizard:back_to_step:")
    ]
    assert len(back_buttons) == 1
    assert back_buttons[0].custom_id == "setup_wizard:back_to_step:2"
    assert back_buttons[0].row == 4


@pytest.mark.asyncio
async def test_render_step_detail_returns_false_when_builders_missing():
    """A section without detail builders returns False (no anchor edit)."""
    section = _section("zz_no_detail", with_detail=False)
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    member = _owner_member()
    interaction = _interaction(member)

    with patch(
        "views.setup.wizard_nav.safe_edit",
        new_callable=AsyncMock,
        return_value=True,
    ) as safe_edit_mock:
        ok = await wizard_nav.render_step_detail(
            interaction,
            guild=guild,
            member=member,
            session=_session(),
            section=section,
            step_index=0,
        )

    assert ok is False
    safe_edit_mock.assert_not_called()


@pytest.mark.asyncio
async def test_back_to_step_button_callback_restores_wizard():
    """The injected Back-to-step button calls render_wizard_step with the
    originating step_index.
    """
    section = _section("zz_back_test", with_detail=True)
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    member = _owner_member()
    interaction = _interaction(member)

    captured_view: list[discord.ui.View] = []

    async def _capture_safe_edit(_interaction, *, embed=None, view=None, content=None):
        captured_view.append(view)
        return True

    with (
        patch(
            "views.setup.wizard_nav.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.wizard_nav.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
        patch(
            "views.setup.wizard_nav.safe_edit",
            side_effect=_capture_safe_edit,
        ),
        patch(
            "views.setup.wizard_nav.safe_defer",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        await wizard_nav.render_step_detail(
            interaction,
            guild=guild,
            member=member,
            session=_session(),
            section=section,
            step_index=3,
        )

    assert captured_view, "safe_edit was not called"
    detail_view = captured_view[0]
    back_btn = next(
        c
        for c in detail_view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_wizard:back_to_step:3"
    )

    # Click the Back button; assert render_wizard_step gets called.
    back_interaction = _interaction(member)
    with (
        patch(
            "views.setup.wizard_nav.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.wizard_nav.render_wizard_step",
            new_callable=AsyncMock,
            return_value=True,
        ) as render_wizard_mock,
    ):
        await back_btn.callback(back_interaction)

    render_wizard_mock.assert_awaited_once()
    kw = render_wizard_mock.await_args.kwargs
    assert kw["step_index"] == 3

"""Tests for ``views.setup.section_card`` — shared section panel."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import views.setup.sections  # noqa: F401 — populate REGISTRY for tests
from services.setup_operations import SetupOperation
from services.setup_progress import SectionProgress, SectionStatus
from services.setup_sections import REGISTRY, SetupSection
from views.setup.section_card import SectionCardView, build_section_card, show

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _noop_run(_interaction, _hub):  # pragma: no cover — not exercised here
    return None


def _section(slug="cleanup", *, description_if_skipped="", emoji="🧹"):
    return SetupSection(
        slug=slug,
        label=slug.replace("_", " ").title(),
        style=discord.ButtonStyle.secondary,
        run=_noop_run,
        emoji=emoji,
        order=60,
        op_kinds=frozenset({"set_cleanup_policy"}),
        description_if_skipped=description_if_skipped,
    )


def _progress(*, status=SectionStatus.NOT_STARTED, pending_ops=0, slug="cleanup"):
    return SectionProgress(slug=slug, status=status, pending_ops=pending_ops)


def _owner_member(user_id: int = 99):
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=user_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _interaction_with_guild(user, *, guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = user
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id, name="Test", owner_id=99)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    return interaction


# ---------------------------------------------------------------------------
# build_section_card embed
# ---------------------------------------------------------------------------


def test_card_embed_includes_step_and_status():
    """Section registered in REGISTRY (production sections always are) gets
    a 'Step N of M' header derived from registry order."""
    # The production cleanup section is registered; use its real registered
    # SetupSection so the step index resolves.
    section = REGISTRY.get("cleanup")
    assert section is not None
    progress = _progress()
    embed = build_section_card(
        section=section,
        progress=progress,
        detected_state="Resolver walks thread → channel → category → guild.",
        has_recommended=True,
        has_customize=True,
    )
    title = embed.title or ""
    assert "Cleanup" in title
    description = embed.description or ""
    assert "Step" in description
    assert "Not started" in description


def test_card_embed_unregistered_section_omits_step():
    """Sections constructed in tests (not in REGISTRY) just show the badge."""
    section = _section(slug="not_registered")
    progress = _progress(slug="not_registered")
    embed = build_section_card(
        section=section,
        progress=progress,
        detected_state="",
        has_recommended=True,
        has_customize=True,
    )
    description = embed.description or ""
    assert "Step" not in description
    assert "Not started" in description


def test_card_embed_renders_skip_impact_when_present():
    section = _section(description_if_skipped="Cleanup stays at the current default.")
    embed = build_section_card(
        section=section,
        progress=_progress(),
        detected_state="",
        has_recommended=True,
        has_customize=True,
    )
    fields = {(f.name or "").lower(): (f.value or "") for f in embed.fields}
    assert "if you skip this" in fields
    assert "current default" in fields["if you skip this"].lower()


def test_card_embed_omits_skip_impact_when_empty():
    section = _section(description_if_skipped="")
    embed = build_section_card(
        section=section,
        progress=_progress(),
        detected_state="",
        has_recommended=True,
        has_customize=True,
    )
    fields = {(f.name or "").lower() for f in embed.fields}
    assert "if you skip this" not in fields


def test_card_embed_surfaces_pending_op_count():
    embed = build_section_card(
        section=_section(),
        progress=_progress(status=SectionStatus.CUSTOMIZED, pending_ops=3),
        detected_state="",
        has_recommended=True,
        has_customize=True,
    )
    fields = {(f.name or "").lower(): (f.value or "") for f in embed.fields}
    assert "pending" in fields
    assert "3 operations" in fields["pending"]


def test_card_embed_explains_when_no_recommended_action():
    embed = build_section_card(
        section=_section(),
        progress=_progress(),
        detected_state="",
        has_recommended=False,
        has_customize=True,
    )
    fields = {(f.name or "").lower(): (f.value or "") for f in embed.fields}
    assert "recommended action" in fields
    assert "no recommended" in fields["recommended action"].lower()


# ---------------------------------------------------------------------------
# SectionCardView buttons
# ---------------------------------------------------------------------------


def test_view_disables_apply_recommended_when_no_builder():
    section = _section()
    view = SectionCardView(
        _owner_member(),
        section=section,
        hub=None,
        on_customize=_noop_run,
        recommended_ops_builder=None,
    )
    apply_btn = next(c for c in view.children if c.label == "Apply Recommended")
    assert apply_btn.disabled is True


def test_view_disables_customize_when_no_callback():
    section = _section()
    view = SectionCardView(
        _owner_member(),
        section=section,
        hub=None,
        on_customize=None,
        recommended_ops_builder=lambda g: [],
    )
    customize_btn = next(c for c in view.children if c.label == "Customize")
    assert customize_btn.disabled is True


def test_view_has_skip_and_hub_buttons():
    view = SectionCardView(
        _owner_member(),
        section=_section(),
        hub=None,
        on_customize=_noop_run,
        recommended_ops_builder=lambda g: [],
    )
    labels = {c.label for c in view.children}
    assert "Skip" in labels
    assert "↩ Hub" in labels


@pytest.mark.asyncio
async def test_apply_recommended_stages_ops_with_recommended_source():
    section = _section()
    ops = [
        SetupOperation(
            kind="set_cleanup_policy",
            subsystem="cleanup",
            target_kind="guild",
            target_id=1,
            value="Light",
        ),
    ]
    view = SectionCardView(
        _owner_member(),
        section=section,
        hub=None,
        on_customize=_noop_run,
        recommended_ops_builder=lambda g: ops,
    )
    interaction = _interaction_with_guild(_owner_member())

    with (
        patch(
            "views.setup.section_card.setup_draft.append",
            new_callable=AsyncMock,
        ) as append_mock,
        patch(
            "views.setup.section_card.setup_session.unmark_section_skipped",
            new_callable=AsyncMock,
        ),
    ):
        await view._apply_recommended(interaction)

    append_mock.assert_awaited_once()
    metadata = append_mock.await_args.kwargs["metadata"]
    assert metadata["source"] == "setup_ux:recommended"
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "1 recommended operation" in msg


@pytest.mark.asyncio
async def test_apply_recommended_handles_empty_builder_output():
    view = SectionCardView(
        _owner_member(),
        section=_section(),
        hub=None,
        on_customize=_noop_run,
        recommended_ops_builder=lambda g: [],
    )
    interaction = _interaction_with_guild(_owner_member())

    with patch(
        "views.setup.section_card.setup_draft.append",
        new_callable=AsyncMock,
    ) as append_mock:
        await view._apply_recommended(interaction)

    append_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "no recommended" in msg.lower()


@pytest.mark.asyncio
async def test_skip_marks_section_skipped():
    view = SectionCardView(
        _owner_member(),
        section=_section(),
        hub=None,
        on_customize=_noop_run,
        recommended_ops_builder=lambda g: [],
    )
    interaction = _interaction_with_guild(_owner_member())

    with patch(
        "views.setup.section_card.setup_session.mark_section_skipped",
        new_callable=AsyncMock,
    ) as skip_mock:
        await view._skip(interaction)

    skip_mock.assert_awaited_once_with(1, "cleanup")
    msg = interaction.response.send_message.await_args.args[0]
    assert "skipped" in msg.lower()


@pytest.mark.asyncio
async def test_customize_calls_supplied_callback():
    seen = []

    async def fake_customize(interaction, hub):
        seen.append((interaction, hub))

    view = SectionCardView(
        _owner_member(),
        section=_section(),
        hub=None,
        on_customize=fake_customize,
        recommended_ops_builder=lambda g: [],
    )
    interaction = _interaction_with_guild(_owner_member())

    await view._customize(interaction)

    assert len(seen) == 1
    assert seen[0][0] is interaction


# ---------------------------------------------------------------------------
# show() entry point
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_show_posts_ephemeral_card_and_marks_step():
    section = _section()
    interaction = _interaction_with_guild(_owner_member())

    with (
        patch(
            "views.setup.section_card.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "views.setup.section_card.setup_draft.list_ops",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.section_card.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await show(
            interaction,
            hub=None,
            section=section,
            detected_state="Test",
            on_customize=_noop_run,
            recommended_ops_builder=lambda g: [],
        )

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs.get("view"), SectionCardView)
    mark_mock.assert_awaited_once()
    assert mark_mock.await_args.kwargs.get("step") == "cleanup"


# ---------------------------------------------------------------------------
# Cleanup section integration — it is now wired through the card
# ---------------------------------------------------------------------------


def test_cleanup_section_registers_description_if_skipped():
    """The cleanup registration must carry a non-empty skip-impact string
    so PR 3's section card can surface it without code changes."""
    section = REGISTRY.get("cleanup")
    assert section is not None
    assert "cleanup" in section.description_if_skipped.lower()

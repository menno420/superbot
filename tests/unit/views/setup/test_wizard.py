"""Tests for :mod:`views.setup.wizard` — the linear setup wizard.

Pins Phase 3 invariants:

* ``LinearWizardView`` renders the current step embed.
* Navigation buttons (``Back`` / ``Continue``) update ``step_index``
  in place; the last step's ``Continue`` opens Final Review.
* Mutating buttons (``Apply Recommended`` / ``Skip``) re-check
  :func:`services.setup_access.can_apply_setup`.
* ``Apply Recommended`` routes through
  :func:`services.setup_draft.replace_recommended_for_section`
  (no bare ``setup_draft.append`` loops).
* ``Skip`` writes ``mark_section_skipped`` AND deletes the section's
  Phase-0 provenance rows so Final Review never applies what was
  skipped.
* ``open_setup_workspace`` ensures the setup channel, posts /
  edits the anchor message, and persists the message id via
  :func:`services.setup_session.set_setup_message_id`.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import views.setup.sections  # noqa: F401 — populate REGISTRY for tests
from services.setup_draft import (
    DraftOperationRow,
    ReplaceRecommendedResult,
)
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY, SetupSection
from services.setup_session import SetupSession
from views.setup.wizard import (
    LinearWizardView,
    build_wizard_step_embed,
    open_setup_workspace,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _noop_run(_interaction, _hub):  # pragma: no cover — never invoked
    return None


async def _builder_one_op(_guild):
    return [
        SetupOperation(
            kind="set_cleanup_policy",
            subsystem="cleanup",
            target_kind="guild",
            target_id=1,
            value="Light",
        ),
    ]


def _section(
    slug: str = "cleanup",
    *,
    op_kinds: frozenset[str] = frozenset({"set_cleanup_policy"}),
    description_if_skipped: str = "",
    builder=None,
    order: int = 60,
) -> SetupSection:
    return SetupSection(
        slug=slug,
        label=slug.replace("_", " ").title(),
        style=discord.ButtonStyle.secondary,
        run=_noop_run,
        emoji="🧹",
        order=order,
        op_kinds=op_kinds,
        description_if_skipped=description_if_skipped,
        recommended_ops_builder=builder,
    )


def _session(
    *,
    depth: str | None = "standard",
    delegated: tuple[int, ...] = (),
    setup_message_id: int | None = None,
    setup_channel_id: int | None = None,
    current_step: str | None = None,
    skipped: frozenset[str] = frozenset(),
    acknowledged: frozenset[str] = frozenset(),
    status: str = "in_progress",
) -> SetupSession:
    return SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status=status,
        setup_channel_id=setup_channel_id,
        setup_message_id=setup_message_id,
        last_readiness_score=None,
        current_step=current_step,
        delegated_admins=delegated,
        skipped_sections=skipped,
        acknowledged_sections=acknowledged,
        depth=depth,
    )


def _owner_member(user_id: int = 99) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=user_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _interaction(member, *, guild_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.user = member
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id, name="Test", owner_id=99)
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


def _make_text_channel(channel_id: int = 7000) -> MagicMock:
    ch = MagicMock(spec=discord.TextChannel)
    ch.id = channel_id
    ch.name = "superbot-setup"
    ch.mention = f"<#{channel_id}>"
    ch.send = AsyncMock()
    ch.fetch_message = AsyncMock()
    return ch


# ---------------------------------------------------------------------------
# build_wizard_step_embed
# ---------------------------------------------------------------------------


def test_wizard_step_embed_shows_step_counter():
    sections = [_section("cleanup"), _section("channels", order=70)]
    embed = build_wizard_step_embed(
        session=_session(),
        section=sections[0],
        step_index=0,
        total_steps=len(sections),
        draft_rows=[],
    )
    title = (embed.title or "")
    assert "Step 1/2" in title
    assert "Cleanup" in (embed.description or "")


def test_wizard_step_embed_indicates_no_recommended_when_builder_missing():
    section = _section("readonly", op_kinds=frozenset(), builder=None)
    embed = build_wizard_step_embed(
        session=_session(),
        section=section,
        step_index=0,
        total_steps=1,
        draft_rows=[],
    )
    fields = {(f.name or "").lower(): (f.value or "") for f in embed.fields}
    assert "no recommended" in fields["recommended action"].lower()


def test_wizard_step_embed_renders_skip_impact():
    section = _section(
        "cleanup",
        description_if_skipped="Cleanup keeps the legacy defaults.",
        builder=_builder_one_op,
    )
    embed = build_wizard_step_embed(
        session=_session(),
        section=section,
        step_index=0,
        total_steps=1,
        draft_rows=[],
    )
    fields = {(f.name or "").lower(): (f.value or "") for f in embed.fields}
    assert "if you skip this" in fields
    assert "legacy defaults" in fields["if you skip this"].lower()


def test_wizard_step_embed_surfaces_staged_op_count():
    section = _section("cleanup", builder=_builder_one_op)
    row = DraftOperationRow(
        id=1,
        seq=1,
        section_slug="cleanup",
        staging_kind="recommended",
        group_id=None,
        parent_seq=None,
        label="x",
        op=SetupOperation(kind="set_cleanup_policy", subsystem="cleanup"),
    )
    embed = build_wizard_step_embed(
        session=_session(),
        section=section,
        step_index=0,
        total_steps=1,
        draft_rows=[row],
    )
    fields = {(f.name or "").lower(): (f.value or "") for f in embed.fields}
    assert "1 recommended" in fields["current state"]


# ---------------------------------------------------------------------------
# LinearWizardView — buttons + navigation
# ---------------------------------------------------------------------------


def test_view_has_navigation_buttons_in_layout():
    sections = [_section("cleanup", builder=_builder_one_op)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    custom_ids = {
        getattr(c, "custom_id", None)
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert "setup_wizard:back" in custom_ids
    assert "setup_wizard:apply_recommended" in custom_ids
    assert "setup_wizard:customize" in custom_ids
    assert "setup_wizard:skip" in custom_ids
    assert "setup_wizard:continue" in custom_ids
    assert "setup_wizard:open_hub" in custom_ids
    assert "setup_wizard:cancel" in custom_ids


def test_view_back_button_disabled_on_first_step():
    sections = [_section("cleanup", builder=_builder_one_op), _section("channels", order=70)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    back = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_wizard:back"
    )
    assert back.disabled is True


def test_view_apply_recommended_disabled_when_no_builder():
    sections = [_section("readonly", op_kinds=frozenset(), builder=None)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    apply_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_wizard:apply_recommended"
    )
    assert apply_btn.disabled is True


def test_view_continue_button_label_is_final_review_on_last_step():
    sections = [_section("cleanup", builder=_builder_one_op)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    cont = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_wizard:continue"
    )
    assert "Final" in (cont.label or "")


def test_view_continue_label_is_continue_when_not_last_step():
    sections = [_section("cleanup", builder=_builder_one_op), _section("channels", order=70)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    cont = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_wizard:continue"
    )
    assert "Continue" in (cont.label or "")


@pytest.mark.asyncio
async def test_apply_recommended_routes_through_replace_recommended():
    sections = [_section("cleanup", builder=_builder_one_op)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.wizard.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.wizard.setup_draft.replace_recommended_for_section",
            new_callable=AsyncMock,
            return_value=ReplaceRecommendedResult(
                inserted_seqs=[1],
                deleted_count=0,
                conflicts=[],
            ),
        ) as replace_mock,
        patch(
            "views.setup.wizard.setup_session.unmark_section_skipped",
            new_callable=AsyncMock,
        ),
    ):
        # The view's first button callback for apply_recommended.
        apply_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_wizard:apply_recommended"
        )
        await apply_btn.callback(interaction)

    replace_mock.assert_awaited_once()
    args = replace_mock.await_args.args
    assert args[0] == 1
    assert args[1] == "cleanup"
    assert len(args[2]) == 1
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_recommended_rejects_non_delegated_admin():
    """Non-applicants can't stage anything via the wizard either."""
    sections = [_section("cleanup", builder=_builder_one_op)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.wizard.setup_session.resume_session",
            new_callable=AsyncMock,
            # Different session: no delegation, no owner match.
            return_value=_session(delegated=()),
        ),
        # Patch can_apply_setup to reject.
        patch(
            "views.setup.wizard.setup_access.can_apply_setup",
            return_value=False,
        ),
        patch(
            "views.setup.wizard.setup_draft.replace_recommended_for_section",
            new_callable=AsyncMock,
        ) as replace_mock,
    ):
        apply_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_wizard:apply_recommended"
        )
        await apply_btn.callback(interaction)

    replace_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "delegate" in msg or "owner" in msg


@pytest.mark.asyncio
async def test_skip_deletes_section_rows_when_provenance_present():
    """Skip writes mark_section_skipped AND drops the section's
    provenance-tagged rows so Final Review never applies them.
    """
    sections = [
        _section("cleanup", builder=_builder_one_op),
        _section("channels", order=70),
    ]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    interaction = _interaction(_owner_member())

    rows = [
        DraftOperationRow(
            id=11,
            seq=1,
            section_slug="cleanup",
            staging_kind="recommended",
            group_id=None,
            parent_seq=None,
            label="x",
            op=SetupOperation(kind="set_cleanup_policy", subsystem="cleanup"),
        ),
    ]

    with (
        patch(
            "views.setup.wizard.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.wizard.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
        ) as skip_mock,
        patch(
            "views.setup.wizard.setup_draft.list_by_section",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "views.setup.wizard.setup_draft.delete_by_ids",
            new_callable=AsyncMock,
            return_value=1,
        ) as delete_mock,
        patch(
            "views.setup.wizard.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        skip_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_wizard:skip"
        )
        await skip_btn.callback(interaction)

    skip_mock.assert_awaited_once_with(1, "cleanup")
    delete_mock.assert_awaited_once_with(1, [11])
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_continue_on_last_step_opens_final_review():
    sections = [_section("cleanup", builder=_builder_one_op)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,  # only step → last step
    )
    interaction = _interaction(_owner_member())

    with patch(
        "views.setup.wizard.setup_draft.list_ops",
        new_callable=AsyncMock,
        return_value=[],
    ):
        cont = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_wizard:continue"
        )
        await cont.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    from views.setup.final_review import FinalReviewView

    sent_view = interaction.response.send_message.await_args.kwargs["view"]
    assert isinstance(sent_view, FinalReviewView)


@pytest.mark.asyncio
async def test_continue_on_non_last_step_advances():
    sections = [
        _section("cleanup", builder=_builder_one_op),
        _section("channels", order=70),
    ]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.wizard.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.wizard.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        cont = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_wizard:continue"
        )
        await cont.callback(interaction)

    assert view.step_index == 1
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_back_button_decrements_step():
    sections = [
        _section("cleanup", builder=_builder_one_op),
        _section("channels", order=70),
    ]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=1,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.wizard.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.wizard.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        back = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_wizard:back"
        )
        await back.callback(interaction)

    assert view.step_index == 0


# ---------------------------------------------------------------------------
# open_setup_workspace
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_workspace_returns_no_channel_when_ensure_fails():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    member = _owner_member()
    with patch(
        "views.setup.wizard.setup_channel.ensure_setup_channel",
        new_callable=AsyncMock,
        return_value=(None, False),
    ):
        channel, message, reason = await open_setup_workspace(
            guild, member=member, session=_session(),
        )
    assert channel is None
    assert message is None
    assert reason == "no_channel"


@pytest.mark.asyncio
async def test_open_workspace_posts_new_anchor_when_id_missing():
    """No prior message id → post a new anchor and persist its id."""
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    member = _owner_member()
    channel = _make_text_channel()
    posted_msg = MagicMock(id=5555, jump_url="https://x/y/z")
    channel.send = AsyncMock(return_value=posted_msg)

    with (
        patch(
            "views.setup.wizard.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(channel, True),
        ),
        patch(
            "views.setup.wizard.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.wizard.setup_session.set_setup_message_id",
            new_callable=AsyncMock,
        ) as set_id_mock,
        patch(
            "views.setup.wizard.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        ch, msg, reason = await open_setup_workspace(
            guild,
            member=member,
            session=_session(setup_message_id=None),
        )

    assert reason == "ok"
    assert ch is channel
    assert msg is posted_msg
    channel.send.assert_awaited_once()
    set_id_mock.assert_awaited_once_with(1, 5555)
    mark_mock.assert_awaited_once_with(1, step="wizard")


@pytest.mark.asyncio
async def test_open_workspace_edits_existing_anchor_in_place():
    """When a fetchable anchor id is on the session, edit in place
    instead of posting a new message (idempotency of /setup re-runs).
    """
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    member = _owner_member()
    channel = _make_text_channel()
    existing_msg = MagicMock(id=5555)
    edited_msg = MagicMock(id=5555, jump_url="https://x/y/z")
    existing_msg.edit = AsyncMock(return_value=edited_msg)
    channel.fetch_message = AsyncMock(return_value=existing_msg)

    with (
        patch(
            "views.setup.wizard.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(channel, False),
        ),
        patch(
            "views.setup.wizard.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.wizard.setup_session.set_setup_message_id",
            new_callable=AsyncMock,
        ) as set_id_mock,
        patch(
            "views.setup.wizard.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        ch, msg, reason = await open_setup_workspace(
            guild,
            member=member,
            session=_session(setup_message_id=5555),
        )

    assert reason == "ok"
    existing_msg.edit.assert_awaited_once()
    # No new id persisted — the message was edited in place.
    set_id_mock.assert_not_awaited()
    channel.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_workspace_recovers_when_anchor_404():
    """A stale message id (404 on fetch) triggers a fresh post and
    persists the new id.  This is the restart / "expired" recovery
    Option B from the plan.
    """
    guild = MagicMock(spec=discord.Guild)
    guild.id = 1
    member = _owner_member()
    channel = _make_text_channel()
    channel.fetch_message = AsyncMock(
        side_effect=discord.NotFound(MagicMock(), "gone"),
    )
    posted_msg = MagicMock(id=7777, jump_url="https://x/y/z")
    channel.send = AsyncMock(return_value=posted_msg)

    with (
        patch(
            "views.setup.wizard.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(channel, False),
        ),
        patch(
            "views.setup.wizard.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.wizard.setup_session.set_setup_message_id",
            new_callable=AsyncMock,
        ) as set_id_mock,
        patch(
            "views.setup.wizard.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        ch, msg, reason = await open_setup_workspace(
            guild,
            member=member,
            session=_session(setup_message_id=5555),
        )

    assert reason == "ok"
    assert msg is posted_msg
    # The stale id was cleared and the fresh one persisted (two
    # set_setup_message_id calls: clear None + set new).
    assert set_id_mock.await_count == 2
    assert set_id_mock.await_args_list[0].args == (1, None)
    assert set_id_mock.await_args_list[1].args == (1, 7777)


# ---------------------------------------------------------------------------
# Phase 7 — recovery view mount on section-flow failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_recommended_mounts_recovery_view_on_builder_failure():
    """When the section's recommended-ops builder raises, the wizard
    edits the anchor to show the Phase 7 recovery embed + view
    instead of just emitting a flat error ephemeral.
    """
    from views.setup.recovery import SectionRecoveryView

    async def _broken_builder(_guild, **_kw):
        raise RuntimeError("builder boom")

    sections = [_section("cleanup", builder=_broken_builder)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    interaction = _interaction(_owner_member())

    with patch(
        "views.setup.wizard.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_session(),
    ):
        apply_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_wizard:apply_recommended"
        )
        await apply_btn.callback(interaction)

    # The anchor message is edited (not just an ephemeral) and the
    # new view is the recovery view.
    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert isinstance(kwargs.get("view"), SectionRecoveryView)


@pytest.mark.asyncio
async def test_apply_recommended_mounts_recovery_view_on_replace_failure():
    """Same flow when replace_recommended_for_section raises."""
    from views.setup.recovery import SectionRecoveryView

    sections = [_section("cleanup", builder=_builder_one_op)]
    view = LinearWizardView(
        _owner_member(),
        session=_session(),
        sections=sections,
        step_index=0,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.wizard.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.wizard.setup_draft.replace_recommended_for_section",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ),
    ):
        apply_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_wizard:apply_recommended"
        )
        await apply_btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert isinstance(kwargs.get("view"), SectionRecoveryView)

"""Tests for the Phase 4 server-purpose section.

Pins:

* Picking a purpose writes to ``setup_session.set_purpose`` AND
  acknowledges the section via ``setup_session.ack_section``.
* No draft operation is staged.
* Unauthorised members can't change the purpose.
* The embed highlights the current pick.
* Re-picking the same purpose is idempotent at the embed level
  (still applies set_purpose / ack — DB layer is set-semantics).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import views.setup.sections  # noqa: F401 — populate REGISTRY
from services.setup_sections import REGISTRY
from services.setup_session import SetupSession
from views.setup.sections.purpose import (
    PURPOSE_OPTIONS,
    SLUG,
    PurposePickerView,
    build_purpose_embed,
    get_option,
    run,
)


def _owner_member(user_id: int = 99) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=user_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _random_member(user_id: int = 42) -> MagicMock:
    """Non-owner, non-administrator, non-delegated member."""
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=99)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _session(*, purpose: str | None = None, delegated=()):
    return SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=delegated,
        purpose=purpose,
    )


def _interaction(member, *, guild_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.user = member
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.message = MagicMock(id=2000)
    return interaction


# ---------------------------------------------------------------------------
# Registry presence
# ---------------------------------------------------------------------------


def test_purpose_section_is_registered_first():
    """Purpose must register with a low ``order`` so the wizard
    renders it as the first step.
    """
    section = REGISTRY.get(SLUG)
    assert section is not None
    # Other production sections register at order >= 10; purpose should
    # be strictly lower so it comes first in REGISTRY.all() / for_depth().
    assert section.order < 10


def test_purpose_section_has_no_op_kinds():
    """Purpose stages zero draft ops — its ``op_kinds`` must be empty."""
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.op_kinds == frozenset()


def test_purpose_section_appears_in_all_depths():
    """Purpose is the orienting question — it runs in every depth."""
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.depths == frozenset({"quick", "standard", "advanced"})


def test_purpose_section_has_no_recommended_ops_builder():
    """Purpose has nothing to stage; the builder slot is intentionally
    unset so the section card's ``Apply Recommended`` button is
    disabled.
    """
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.recommended_ops_builder is None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_get_option_returns_known_slug():
    opt = get_option("community")
    assert opt is not None
    assert opt.slug == "community"


def test_get_option_returns_none_for_unknown_and_none():
    assert get_option(None) is None
    assert get_option("garbage") is None


def test_purpose_option_slugs_match_known_purposes():
    """Every option's slug must be in the DB-layer allowlist so a
    selection actually persists.
    """
    from utils.db.setup_session import KNOWN_PURPOSES

    expected = {opt.slug for opt in PURPOSE_OPTIONS}
    assert expected == KNOWN_PURPOSES


# ---------------------------------------------------------------------------
# build_purpose_embed
# ---------------------------------------------------------------------------


def test_embed_lists_every_option():
    embed = build_purpose_embed(None)
    options_field = next((f for f in embed.fields if f.name == "Options"), None)
    assert options_field is not None
    rendered = options_field.value or ""
    for opt in PURPOSE_OPTIONS:
        assert opt.label in rendered


def test_embed_highlights_current_pick():
    embed = build_purpose_embed("community")
    current_field = next((f for f in embed.fields if f.name == "Current pick"), None)
    assert current_field is not None
    assert "Community" in (current_field.value or "")


def test_embed_indicates_no_pick_when_none():
    embed = build_purpose_embed(None)
    current_field = next((f for f in embed.fields if f.name == "Current pick"), None)
    assert current_field is not None
    assert "no purpose" in (current_field.value or "").lower()


# ---------------------------------------------------------------------------
# PurposePickerView
# ---------------------------------------------------------------------------


def test_view_has_one_button_per_option():
    view = PurposePickerView(_owner_member(), session_purpose=None)
    button_custom_ids = {
        c.custom_id
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    expected = {f"setup_purpose:{opt.slug}" for opt in PURPOSE_OPTIONS}
    assert button_custom_ids == expected


def test_view_highlights_current_pick_button():
    """The current pick renders in success-style; others in secondary."""
    view = PurposePickerView(_owner_member(), session_purpose="community")
    community_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_purpose:community"
    )
    assert community_btn.style is discord.ButtonStyle.success
    other_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_purpose:moderation"
    )
    assert other_btn.style is discord.ButtonStyle.secondary


@pytest.mark.asyncio
async def test_picking_purpose_writes_set_purpose_and_ack():
    view = PurposePickerView(_owner_member(), session_purpose=None)
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.purpose.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.purpose.setup_session.set_purpose",
            new_callable=AsyncMock,
        ) as set_mock,
        patch(
            "views.setup.sections.purpose.setup_session.ack_section",
            new_callable=AsyncMock,
        ) as ack_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_purpose:community"
        )
        await btn.callback(interaction)

    set_mock.assert_awaited_once_with(1, "community")
    ack_mock.assert_awaited_once_with(1, SLUG)


@pytest.mark.asyncio
async def test_picking_purpose_stages_no_draft_ops():
    """Pin Phase 4's "purpose is metadata, not a mutation" invariant
    by verifying setup_draft.append / setup_draft.replace_recommended
    are never called from the purpose flow.
    """
    view = PurposePickerView(_owner_member(), session_purpose=None)
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.purpose.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.purpose.setup_session.set_purpose",
            new_callable=AsyncMock,
        ),
        patch(
            "views.setup.sections.purpose.setup_session.ack_section",
            new_callable=AsyncMock,
        ),
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
        ) as append_mock,
        patch(
            "services.setup_draft.replace_recommended_for_section",
            new_callable=AsyncMock,
        ) as replace_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_purpose:gaming_btd6"
        )
        await btn.callback(interaction)

    append_mock.assert_not_awaited()
    replace_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_picking_purpose_rejects_non_delegated_admin():
    view = PurposePickerView(_random_member(), session_purpose=None)
    interaction = _interaction(_random_member())

    with (
        patch(
            "views.setup.sections.purpose.setup_session.resume_session",
            new_callable=AsyncMock,
            # Non-delegated session — random member can't apply.
            return_value=_session(delegated=()),
        ),
        patch(
            "views.setup.sections.purpose.setup_session.set_purpose",
            new_callable=AsyncMock,
        ) as set_mock,
        patch(
            "views.setup.sections.purpose.setup_session.ack_section",
            new_callable=AsyncMock,
        ) as ack_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_purpose:community"
        )
        await btn.callback(interaction)

    set_mock.assert_not_awaited()
    ack_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "owner" in msg or "delegate" in msg


@pytest.mark.asyncio
async def test_picking_same_purpose_is_idempotent():
    """Re-picking the current purpose still routes through set_purpose
    + ack_section (set semantics at the DB layer); the embed re-renders
    with the same highlight.
    """
    view = PurposePickerView(_owner_member(), session_purpose="community")
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.purpose.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(purpose="community"),
        ),
        patch(
            "views.setup.sections.purpose.setup_session.set_purpose",
            new_callable=AsyncMock,
        ) as set_mock,
        patch(
            "views.setup.sections.purpose.setup_session.ack_section",
            new_callable=AsyncMock,
        ) as ack_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_purpose:community"
        )
        await btn.callback(interaction)

    set_mock.assert_awaited_once_with(1, "community")
    ack_mock.assert_awaited_once_with(1, SLUG)


@pytest.mark.asyncio
async def test_picking_purpose_surfaces_db_failure():
    """A DB failure surfaces an error reply instead of pretending the
    write succeeded.
    """
    view = PurposePickerView(_owner_member(), session_purpose=None)
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.purpose.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.purpose.setup_session.set_purpose",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ),
        patch(
            "views.setup.sections.purpose.setup_session.ack_section",
            new_callable=AsyncMock,
        ) as ack_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_purpose:community"
        )
        await btn.callback(interaction)

    # ack should not fire if set_purpose failed.
    ack_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "could not" in msg


# ---------------------------------------------------------------------------
# Section run callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_posts_picker_with_current_purpose():
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.purpose.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(purpose="community"),
        ),
        patch(
            "views.setup.sections.purpose.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await run(interaction, hub=None)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    sent_view = kwargs.get("view")
    assert isinstance(sent_view, PurposePickerView)
    assert sent_view.session_purpose == "community"
    mark_mock.assert_awaited_once_with(1, step=SLUG)


@pytest.mark.asyncio
async def test_run_handles_resume_failure_gracefully():
    """A resume_session DB failure still opens the picker (with
    purpose=None) rather than crashing the section button.
    """
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.purpose.setup_session.resume_session",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ),
        patch(
            "views.setup.sections.purpose.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await run(interaction, hub=None)

    interaction.response.send_message.assert_awaited_once()
    sent_view = interaction.response.send_message.await_args.kwargs["view"]
    assert isinstance(sent_view, PurposePickerView)
    assert sent_view.session_purpose is None

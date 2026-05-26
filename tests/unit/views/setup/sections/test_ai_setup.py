"""Tests for the Phase 6 AI-setup link-only section.

Pins:

* The section is registered with a stable slug, low op_kinds set
  (empty — it stages nothing), and runs in every depth.
* ``resolve_ai_policy_link`` returns ``</aimenu:id>`` when the
  command id is resolvable; falls back to ``` `/aimenu` ``` text on
  fetch failure, missing id, or absent tree.
* The Open button writes ``ack_section`` and surfaces the link in
  an ephemeral follow-up.
* The Skip button writes ``mark_section_skipped``.
* Both mutating buttons re-check ``can_apply_setup``.
* No draft operation is staged from either button.
* The reserved "Ask SuperBot" button is present but disabled.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import views.setup.sections  # noqa: F401 — populate REGISTRY
from services.setup_sections import REGISTRY
from services.setup_session import SetupSession
from views.setup.sections.ai_setup import (
    AI_POLICY_COMMAND_NAME,
    SLUG,
    AISetupView,
    build_ai_setup_embed,
    resolve_ai_policy_link,
    run,
)


def _owner_member(user_id: int = 99) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=user_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _random_member(user_id: int = 42) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=99)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _session(
    *,
    delegated=(),
    acknowledged: frozenset[str] = frozenset(),
    skipped: frozenset[str] = frozenset(),
):
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
        acknowledged_sections=acknowledged,
        skipped_sections=skipped,
    )


def _interaction(
    member,
    *,
    guild_id: int = 1,
    fetched_commands=None,
) -> MagicMock:
    interaction = MagicMock()
    interaction.user = member
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.message = MagicMock(id=4000)
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.client = MagicMock()
    if fetched_commands is None:
        interaction.client.tree = None
    else:
        interaction.client.tree = MagicMock()
        interaction.client.tree.fetch_commands = AsyncMock(
            return_value=fetched_commands,
        )
    return interaction


# ---------------------------------------------------------------------------
# Registry invariants
# ---------------------------------------------------------------------------


def test_ai_setup_section_registered():
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.label == "AI setup"


def test_ai_setup_section_stages_no_ops():
    """Section's ``op_kinds`` must be empty — Phase 6 is link-only."""
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.op_kinds == frozenset()


def test_ai_setup_section_runs_in_every_depth():
    """AI setup is a universal step; runs in every depth."""
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.depths == frozenset({"quick", "standard", "advanced"})


def test_ai_setup_has_no_recommended_builder():
    """Link-only sections have nothing to stage — no builder."""
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.recommended_ops_builder is None


def test_ai_setup_orders_after_logging_presets():
    """Both touch operator platform features; neighbouring them in
    the wizard preserves a coherent step order.
    """
    section = REGISTRY.get(SLUG)
    logging_section = REGISTRY.get("logging_presets")
    assert section is not None
    assert logging_section is not None
    assert section.order > logging_section.order


# ---------------------------------------------------------------------------
# resolve_ai_policy_link
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_link_returns_mention_when_command_found():
    """Happy path: fetch_commands returns a match → ``</aimenu:id>``."""
    cmd = MagicMock(name="aimenu_cmd")
    cmd.name = AI_POLICY_COMMAND_NAME
    cmd.id = 9001
    interaction = _interaction(_owner_member(), fetched_commands=[cmd])
    link = await resolve_ai_policy_link(interaction)
    assert link == f"</{AI_POLICY_COMMAND_NAME}:9001>"


@pytest.mark.asyncio
async def test_resolve_link_falls_back_when_tree_missing():
    """A client without a tree (test harness, lightweight stand-in)
    falls back to plain text without raising."""
    interaction = _interaction(_owner_member(), fetched_commands=None)
    link = await resolve_ai_policy_link(interaction)
    assert link == f"`/{AI_POLICY_COMMAND_NAME}`"


@pytest.mark.asyncio
async def test_resolve_link_falls_back_when_fetch_raises():
    """Network blip / rate-limit during fetch → plain text fallback."""
    interaction = _interaction(_owner_member(), fetched_commands=[])
    interaction.client.tree.fetch_commands = AsyncMock(
        side_effect=RuntimeError("rate limited"),
    )
    link = await resolve_ai_policy_link(interaction)
    assert link == f"`/{AI_POLICY_COMMAND_NAME}`"


@pytest.mark.asyncio
async def test_resolve_link_falls_back_when_no_matching_command():
    """No aimenu command in the synced set (just-deployed bot) →
    plain text fallback."""
    # Fetch returns a different command set.
    other = MagicMock()
    other.name = "ping"
    other.id = 1234
    interaction = _interaction(_owner_member(), fetched_commands=[other])
    # Guild fetch returns nothing either.
    interaction.client.tree.fetch_commands = AsyncMock(side_effect=[[other], []])
    link = await resolve_ai_policy_link(interaction)
    assert link == f"`/{AI_POLICY_COMMAND_NAME}`"


@pytest.mark.asyncio
async def test_resolve_link_falls_back_when_id_missing():
    """A matched command with no .id (improbable, defensive) → fallback."""
    cmd = MagicMock()
    cmd.name = AI_POLICY_COMMAND_NAME
    cmd.id = None
    interaction = _interaction(_owner_member(), fetched_commands=[cmd])
    # Guild fetch returns nothing either.
    interaction.client.tree.fetch_commands = AsyncMock(side_effect=[[cmd], []])
    link = await resolve_ai_policy_link(interaction)
    assert link == f"`/{AI_POLICY_COMMAND_NAME}`"


# ---------------------------------------------------------------------------
# build_ai_setup_embed
# ---------------------------------------------------------------------------


def test_embed_pending_state():
    embed = build_ai_setup_embed(acknowledged=False, skipped=False)
    state_field = next(f for f in embed.fields if f.name == "State")
    assert "not yet" in (state_field.value or "").lower()


def test_embed_acknowledged_state():
    embed = build_ai_setup_embed(acknowledged=True, skipped=False)
    state_field = next(f for f in embed.fields if f.name == "State")
    assert "acknowledged" in (state_field.value or "").lower()


def test_embed_skipped_state():
    embed = build_ai_setup_embed(acknowledged=False, skipped=True)
    state_field = next(f for f in embed.fields if f.name == "State")
    assert "skipped" in (state_field.value or "").lower()


def test_embed_always_notes_zero_staging():
    embed = build_ai_setup_embed(acknowledged=False, skipped=False)
    staging_field = next(
        f for f in embed.fields if "stages" in (f.name or "").lower()
    )
    assert "nothing" in (staging_field.value or "").lower()


# ---------------------------------------------------------------------------
# AISetupView buttons
# ---------------------------------------------------------------------------


def test_view_has_open_skip_and_disabled_ask_buttons():
    view = AISetupView(_owner_member(), acknowledged=False, skipped=False)
    custom_ids = {
        c.custom_id
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert "setup_ai:open" in custom_ids
    assert "setup_ai:skip" in custom_ids
    assert "setup_ai:ask" in custom_ids
    ask_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "setup_ai:ask"
    )
    assert ask_btn.disabled is True


def test_view_highlights_acknowledged_open_button():
    view = AISetupView(_owner_member(), acknowledged=True, skipped=False)
    open_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "setup_ai:open"
    )
    assert open_btn.style is discord.ButtonStyle.success


def test_view_highlights_skipped_skip_button():
    view = AISetupView(_owner_member(), acknowledged=False, skipped=True)
    skip_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "setup_ai:skip"
    )
    assert skip_btn.style is discord.ButtonStyle.success


@pytest.mark.asyncio
async def test_open_button_writes_ack_and_surfaces_link():
    view = AISetupView(_owner_member(), acknowledged=False, skipped=False)
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.ai_setup.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.ai_setup.setup_session.ack_section",
            new_callable=AsyncMock,
        ) as ack_mock,
        patch(
            "views.setup.sections.ai_setup.resolve_ai_policy_link",
            new_callable=AsyncMock,
            return_value="</aimenu:9001>",
        ),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_ai:open"
        )
        await btn.callback(interaction)

    ack_mock.assert_awaited_once_with(1, SLUG)
    # The link reply is sent as a followup so the embed edit and the
    # link reply both make it to the operator.
    interaction.followup.send.assert_awaited_once()
    followup_msg = interaction.followup.send.await_args.args[0]
    assert "</aimenu:9001>" in followup_msg


@pytest.mark.asyncio
async def test_open_button_stages_no_draft_ops():
    """Open is link-only — pressing it must not touch the draft store."""
    view = AISetupView(_owner_member(), acknowledged=False, skipped=False)
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.ai_setup.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.ai_setup.setup_session.ack_section",
            new_callable=AsyncMock,
        ),
        patch(
            "views.setup.sections.ai_setup.resolve_ai_policy_link",
            new_callable=AsyncMock,
            return_value="</aimenu:1>",
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
            and c.custom_id == "setup_ai:open"
        )
        await btn.callback(interaction)

    append_mock.assert_not_awaited()
    replace_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_open_button_rejects_non_delegated_admin():
    view = AISetupView(_random_member(), acknowledged=False, skipped=False)
    interaction = _interaction(_random_member())

    with (
        patch(
            "views.setup.sections.ai_setup.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(delegated=()),
        ),
        patch(
            "views.setup.sections.ai_setup.setup_session.ack_section",
            new_callable=AsyncMock,
        ) as ack_mock,
        patch(
            "views.setup.sections.ai_setup.resolve_ai_policy_link",
            new_callable=AsyncMock,
        ) as link_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_ai:open"
        )
        await btn.callback(interaction)

    ack_mock.assert_not_awaited()
    link_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "owner" in msg or "delegate" in msg


@pytest.mark.asyncio
async def test_skip_button_writes_mark_section_skipped():
    view = AISetupView(_owner_member(), acknowledged=False, skipped=False)
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.ai_setup.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.ai_setup.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
        ) as skip_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_ai:skip"
        )
        await btn.callback(interaction)

    skip_mock.assert_awaited_once_with(1, SLUG)


@pytest.mark.asyncio
async def test_skip_button_surfaces_db_failure():
    view = AISetupView(_owner_member(), acknowledged=False, skipped=False)
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.ai_setup.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.ai_setup.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_ai:skip"
        )
        await btn.callback(interaction)

    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "could not" in msg


# ---------------------------------------------------------------------------
# Section run callback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_opens_view_with_acknowledged_state_from_session():
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.ai_setup.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(acknowledged=frozenset({SLUG})),
        ),
        patch(
            "views.setup.sections.ai_setup.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await run(interaction, hub=None)

    interaction.response.send_message.assert_awaited_once()
    sent_view = interaction.response.send_message.await_args.kwargs["view"]
    assert isinstance(sent_view, AISetupView)
    assert sent_view.acknowledged is True
    assert sent_view.skipped is False
    mark_mock.assert_awaited_once_with(1, step=SLUG)


@pytest.mark.asyncio
async def test_run_opens_view_with_skipped_state_from_session():
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.ai_setup.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(skipped=frozenset({SLUG})),
        ),
        patch(
            "views.setup.sections.ai_setup.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await run(interaction, hub=None)

    sent_view = interaction.response.send_message.await_args.kwargs["view"]
    assert sent_view.skipped is True
    assert sent_view.acknowledged is False


@pytest.mark.asyncio
async def test_run_tolerates_resume_failure():
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.ai_setup.setup_session.resume_session",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ),
        patch(
            "views.setup.sections.ai_setup.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await run(interaction, hub=None)

    interaction.response.send_message.assert_awaited_once()
    sent_view = interaction.response.send_message.await_args.kwargs["view"]
    assert isinstance(sent_view, AISetupView)
    # Defaults to pending when resume fails.
    assert sent_view.acknowledged is False
    assert sent_view.skipped is False

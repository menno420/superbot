"""Phase 9e / Track 4 PR 9 — ``cogs.setup_cog`` tests.

Pins:

* ``pick_launcher_channel`` walks the documented preference order:
  system → admin/mod/staff → bot → first sendable → None.
* ``post_launcher`` falls back to DMing the owner when no channel
  is sendable.
* ``on_guild_join`` upserts the session row via
  :mod:`services.setup_session` regardless of where the launcher
  ended up.
* Button gating refuses non-owner / non-admin members appropriately.
* The Dismiss button calls ``setup_session.dismiss`` and posts an
  ephemeral confirmation.
* Coming-soon buttons send an ephemeral message and do not touch
  any pipeline.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.setup_cog import (
    SetupLauncherView,
    pick_launcher_channel,
    post_launcher,
)
from services.setup_session import SetupSession

# ---------------------------------------------------------------------------
# Channel selection
# ---------------------------------------------------------------------------


def _perms(*, view=True, send=True, embed=True):
    return SimpleNamespace(
        view_channel=view,
        send_messages=send,
        embed_links=embed,
    )


def _channel(name: str, perms, type_=None):
    import discord

    if type_ is None:
        type_ = discord.TextChannel
    ch = MagicMock(spec=type_)
    ch.name = name
    ch.id = hash(name) & 0xFFFFFF
    ch.permissions_for = MagicMock(return_value=perms)
    return ch


def _guild(
    *,
    system: object | None = None,
    text_channels=(),
    me=None,
    owner=None,
    guild_id: int = 1,
    name: str = "Test",
    owner_id: int = 99,
):
    import discord

    g = MagicMock(spec=discord.Guild)
    g.id = guild_id
    g.name = name
    g.owner_id = owner_id
    g.system_channel = system
    g.text_channels = list(text_channels)
    g.me = me
    g.owner = owner
    return g


def test_pick_launcher_returns_system_channel_when_sendable():
    me = MagicMock()
    system = _channel("general", _perms())
    other = _channel("random", _perms())
    g = _guild(system=system, text_channels=[system, other], me=me)
    assert pick_launcher_channel(g) is system


def test_pick_launcher_skips_system_when_not_sendable():
    me = MagicMock()
    system = _channel("general", _perms(send=False))
    admin = _channel("admin-chat", _perms())
    g = _guild(system=system, text_channels=[system, admin], me=me)
    assert pick_launcher_channel(g) is admin


def test_pick_launcher_prefers_admin_over_bot_keyword():
    me = MagicMock()
    bot_ch = _channel("bot-spam", _perms())
    mod_ch = _channel("mod-log", _perms())
    g = _guild(text_channels=[bot_ch, mod_ch], me=me)
    assert pick_launcher_channel(g) is mod_ch


def test_pick_launcher_falls_back_to_bot_keyword_then_first_sendable():
    me = MagicMock()
    bot_ch = _channel("bot-spam", _perms())
    random_ch = _channel("random", _perms())
    g = _guild(text_channels=[random_ch, bot_ch], me=me)
    assert pick_launcher_channel(g) is bot_ch


def test_pick_launcher_returns_first_sendable_when_no_keyword_match():
    me = MagicMock()
    random1 = _channel("random", _perms())
    random2 = _channel("chatter", _perms())
    g = _guild(text_channels=[random1, random2], me=me)
    assert pick_launcher_channel(g) is random1


def test_pick_launcher_returns_none_when_no_sendable_channels():
    me = MagicMock()
    silent = _channel("locked", _perms(send=False))
    g = _guild(text_channels=[silent], me=me)
    assert pick_launcher_channel(g) is None


def test_pick_launcher_returns_none_when_bot_member_missing():
    g = _guild(me=None, text_channels=[_channel("general", _perms())])
    assert pick_launcher_channel(g) is None


# ---------------------------------------------------------------------------
# post_launcher
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_launcher_sends_to_picked_channel():
    me = MagicMock()
    sendable = _channel("general", _perms())
    sendable.send = AsyncMock(return_value=MagicMock(id=12345))
    g = _guild(system=sendable, text_channels=[sendable], me=me)

    channel, message = await post_launcher(g)
    assert channel is sendable
    assert message.id == 12345
    sendable.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_launcher_falls_back_to_owner_dm_when_no_channel():
    g = _guild(text_channels=[], me=MagicMock())
    g.owner = MagicMock()
    g.owner.id = 99
    g.owner.send = AsyncMock(return_value=MagicMock(id=99001))

    channel, message = await post_launcher(g)
    assert channel is None
    assert message.id == 99001
    g.owner.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_launcher_returns_none_pair_when_dm_also_fails():
    import discord

    g = _guild(text_channels=[], me=MagicMock())
    g.owner = MagicMock()
    g.owner.id = 99
    g.owner.send = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(), "dms closed"),
    )

    channel, message = await post_launcher(g)
    assert channel is None
    assert message is None


@pytest.mark.asyncio
async def test_post_launcher_falls_back_to_dm_on_forbidden_in_channel():
    import discord

    me = MagicMock()
    ch = _channel("general", _perms())
    ch.send = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "no perm"))
    g = _guild(system=ch, text_channels=[ch], me=me)
    g.owner = MagicMock()
    g.owner.id = 99
    g.owner.send = AsyncMock(return_value=MagicMock(id=42))

    channel, message = await post_launcher(g)
    assert channel is None
    assert message.id == 42


# ---------------------------------------------------------------------------
# on_guild_join → setup_session.start_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_guild_join_uses_setup_channel_when_creatable():
    """The bot now tries to auto-create a private setup channel first
    and posts the launcher there with an owner ping."""
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    setup_ch = MagicMock()
    setup_ch.id = 7000
    setup_ch.send = AsyncMock(return_value=MagicMock(id=8000))
    g = _guild(
        system=None,
        text_channels=[],
        me=MagicMock(),
        owner_id=99,
        guild_id=42,
        name="My Server",
    )
    g.owner = MagicMock()
    g.owner.mention = "<@99>"

    with (
        patch(
            "services.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(setup_ch, True),
        ),
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.setup_cog.setup_session.start_session",
            new_callable=AsyncMock,
        ) as start_mock,
    ):
        await cog._handle_join(g)

    setup_ch.send.assert_awaited_once()
    # Owner mention surfaces in the posted content.
    sent_content = setup_ch.send.await_args.kwargs.get("content")
    assert sent_content is not None and "<@99>" in sent_content
    kwargs = start_mock.await_args.kwargs
    assert kwargs["setup_channel_id"] == 7000
    assert kwargs["setup_message_id"] == 8000


@pytest.mark.asyncio
async def test_on_guild_join_falls_back_to_post_launcher_when_no_setup_channel():
    """When the bot lacks Manage Channels (or create fails) the join
    handler falls back to the legacy post_launcher path."""
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    me = MagicMock()
    ch = _channel("general", _perms())
    ch.id = 5555
    ch.send = AsyncMock(return_value=MagicMock(id=8888))
    g = _guild(
        system=ch,
        text_channels=[ch],
        me=me,
        owner_id=99,
        guild_id=42,
        name="My Server",
    )

    with (
        patch(
            "services.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(None, False),
        ),
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.setup_cog.setup_session.start_session",
            new_callable=AsyncMock,
        ) as start_mock,
    ):
        await cog._handle_join(g)

    start_mock.assert_awaited_once()
    kwargs = start_mock.await_args.kwargs
    assert kwargs["guild_id"] == 42
    assert kwargs["setup_channel_id"] == 5555
    assert kwargs["setup_message_id"] == 8888


@pytest.mark.asyncio
async def test_on_guild_join_records_none_ids_when_dm_succeeds():
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    g = _guild(text_channels=[], me=MagicMock())
    g.owner = MagicMock()
    g.owner.send = AsyncMock(return_value=MagicMock(id=99001))

    with (
        patch(
            "services.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(None, False),
        ),
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.setup_cog.setup_session.start_session",
            new_callable=AsyncMock,
        ) as start_mock,
    ):
        await cog._handle_join(g)

    kwargs = start_mock.await_args.kwargs
    assert kwargs["setup_channel_id"] is None
    # DM message id still captured.
    assert kwargs["setup_message_id"] == 99001


@pytest.mark.asyncio
async def test_on_guild_join_skips_double_post_on_restart():
    """If a setup channel already exists with a stored message id, the
    handler reuses the prior message rather than posting a second one."""
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    existing_ch = MagicMock()
    existing_ch.id = 7000
    existing_ch.send = AsyncMock()
    g = _guild(text_channels=[], me=MagicMock(), guild_id=42, name="Test")

    prior_session = SetupSession(
        guild_id=42,
        guild_name="Test",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=7000,
        setup_message_id=8000,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=prior_session,
        ),
        patch(
            "services.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(existing_ch, False),  # not just created
        ),
        patch(
            "cogs.setup_cog.setup_session.start_session",
            new_callable=AsyncMock,
        ) as start_mock,
    ):
        await cog._handle_join(g)

    existing_ch.send.assert_not_awaited()
    kwargs = start_mock.await_args.kwargs
    assert kwargs["setup_channel_id"] == 7000
    assert kwargs["setup_message_id"] == 8000


@pytest.mark.asyncio
async def test_on_guild_join_swallows_handler_failure():
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    g = MagicMock()
    g.id = 1
    g.name = "x"

    with (
        patch(
            "services.setup_channel.ensure_setup_channel",
            new_callable=AsyncMock,
            return_value=(None, False),
        ),
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.setup_cog.post_launcher",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
    ):
        # Must not raise.
        await cog._handle_join(g)


# ---------------------------------------------------------------------------
# Button gating
# ---------------------------------------------------------------------------


def _owner_member(guild_owner_id: int = 99):
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = guild_owner_id
    m.guild = SimpleNamespace(owner_id=guild_owner_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _admin_member(guild_owner_id: int = 99, user_id: int = 42):
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=guild_owner_id)
    m.guild_permissions = SimpleNamespace(administrator=True)
    return m


def _random_member(guild_owner_id: int = 99, user_id: int = 42):
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=guild_owner_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _mock_interaction(user, guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = user
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_start_button_refuses_non_owner():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    await view._start.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert (
        "server owner" in interaction.response.send_message.await_args.args[0].lower()
    )


@pytest.mark.asyncio
async def test_start_button_opens_setup_hub_for_owner():
    """Start Setup must open ``SetupHubView`` — no longer a stub."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    with patch("services.setup_session.resume_session", AsyncMock(return_value=None)):
        with patch(
            "services.setup_session.mark_in_progress",
            AsyncMock(),
        ) as mark_mock:
            await view._start.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    # Hub is rendered with an embed + view, sent ephemerally.
    assert kwargs.get("ephemeral") is True
    assert kwargs.get("embed") is not None
    sent_view = kwargs.get("view")
    assert sent_view is not None
    # The view dispatched must be the wizard hub, not the launcher.
    from views.setup.hub import SetupHubView

    assert isinstance(sent_view, SetupHubView)
    # Session step is persisted so the launcher relabels after restart.
    mark_mock.assert_awaited_once()
    assert mark_mock.await_args.kwargs.get("step") == "hub"


@pytest.mark.asyncio
async def test_start_button_requires_guild_context():
    """No guild_id → deny rather than crash inside SetupHubView."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())
    interaction.guild_id = None

    await view._start.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "guild" in msg.lower()


@pytest.mark.asyncio
async def test_smart_suggestions_button_owner_only():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    await view._suggestions.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert (
        "server owner" in interaction.response.send_message.await_args.args[0].lower()
    )


@pytest.mark.asyncio
async def test_smart_suggestions_opens_ai_review_for_owner():
    """Owner click runs deterministic advisor + opens AIReviewPanelView."""
    from services.guild_snapshot import GuildSnapshot
    from services.setup_plan import (
        SetupPlanDraft,
        SetupRecommendation,
    )
    from views.setup.ai_review.main_panel import AIReviewPanelView

    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    fake_snapshot = MagicMock(spec=GuildSnapshot)
    fake_recommendation = SetupRecommendation(
        subsystem="moderation",
        binding_name="mod_log",
        target_kind="channel",
        target_id=42,
        target_name="mod-logs",
        confidence="high",
        reason="name-match",
    )
    fake_draft = SetupPlanDraft(
        recommendations=(fake_recommendation,),
        source="deterministic",
    )
    fake_advisor = MagicMock()
    fake_advisor.suggest = AsyncMock(return_value=fake_draft)

    with (
        patch(
            "services.guild_snapshot.collect",
            new_callable=AsyncMock,
            return_value=fake_snapshot,
        ),
        patch(
            "services.setup_ai_advisor.build_advisor",
            return_value=fake_advisor,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await view._suggestions.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    sent_view = interaction.response.send_message.await_args.kwargs.get("view")
    assert isinstance(sent_view, AIReviewPanelView)
    assert interaction.response.send_message.await_args.kwargs.get("ephemeral") is True
    mark_mock.assert_awaited_once()
    assert mark_mock.await_args.kwargs.get("step") == "suggestions"


@pytest.mark.asyncio
async def test_smart_suggestions_falls_back_when_advisor_raises():
    """If snapshot/advisor blows up, owner sees an apology — no crash."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    with (
        patch(
            "services.guild_snapshot.collect",
            new_callable=AsyncMock,
            side_effect=RuntimeError("snapshot down"),
        ),
    ):
        await view._suggestions.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "smart suggestions" in msg.lower()


@pytest.mark.asyncio
async def test_preset_button_owner_only():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    await view._preset.callback(interaction)

    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_preset_button_opens_template_picker_for_owner():
    """Owner click opens the template picker view, not a stub."""
    from views.setup.template_picker import TemplatePickerView

    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    await view._preset.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert isinstance(kwargs.get("view"), TemplatePickerView)
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_view_summary_denies_when_status_not_complete():
    """View Summary refuses cleanly when the wizard has not finished."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())
    pending_session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="pending",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=pending_session,
    ):
        await view._view_summary.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "not complete" in msg.lower()


@pytest.mark.asyncio
async def test_view_summary_opens_summary_view_when_complete():
    """View Summary builds a snapshot + opens SummaryView."""
    from services.setup_session import DriftReport
    from views.setup.summary import SummarySnapshot, SummaryView

    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())
    complete_session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="complete",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=80,
        current_step=None,
        delegated_admins=(),
    )

    fake_drift = DriftReport(
        has_drift=False,
        score_delta=None,
        prev_score=80,
        current_score=80,
        summary="No drift detected.",
    )
    fake_snapshot = SummarySnapshot(applied=(), drift=fake_drift)

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=complete_session,
        ),
        patch(
            "views.setup.summary.build_summary_snapshot",
            new_callable=AsyncMock,
            return_value=fake_snapshot,
        ) as snapshot_mock,
    ):
        await view._view_summary.callback(interaction)

    snapshot_mock.assert_awaited_once()
    interaction.response.send_message.assert_awaited_once()
    sent_view = interaction.response.send_message.await_args.kwargs.get("view")
    assert isinstance(sent_view, SummaryView)
    assert interaction.response.send_message.await_args.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_view_summary_button_random_denied():
    """Random non-admin members must be denied."""
    view = SetupLauncherView()
    random = _random_member()
    interaction = _mock_interaction(random)
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="complete",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )
    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=session,
    ):
        await view._view_summary.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "setup admin" in msg.lower()


@pytest.mark.asyncio
async def test_readiness_button_admin_allowed():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    fake_embed = MagicMock()
    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.diagnostic._platform_embeds.build_setup_readiness_embed",
            new_callable=AsyncMock,
            return_value=fake_embed,
        ) as build_mock,
    ):
        await view._readiness.callback(interaction)

    build_mock.assert_awaited_once()
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs["embed"] is fake_embed


@pytest.mark.asyncio
async def test_readiness_button_random_denied():
    view = SetupLauncherView()
    random = _random_member()
    interaction = _mock_interaction(random)
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="pending",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=session,
    ):
        await view._readiness.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "admin" in msg.lower() or "owner" in msg.lower()


@pytest.mark.asyncio
async def test_dismiss_button_owner_calls_dismiss():
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    with patch(
        "cogs.setup_cog.setup_session.dismiss",
        new_callable=AsyncMock,
    ) as dismiss_mock:
        await view._dismiss.callback(interaction)

    dismiss_mock.assert_awaited_once_with(interaction.guild_id)
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_dismiss_button_refuses_non_owner():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    with patch(
        "cogs.setup_cog.setup_session.dismiss",
        new_callable=AsyncMock,
    ) as dismiss_mock:
        await view._dismiss.callback(interaction)

    dismiss_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Track 4 PR 10: status-aware labels + on_ready resumption
# ---------------------------------------------------------------------------


def _find_button(view, custom_id: str):
    import discord

    return next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == custom_id
    )


def test_launcher_view_default_label_is_start_setup():
    view = SetupLauncherView()
    assert _find_button(view, "setup:start").label == "Start Setup"


def test_launcher_view_in_progress_relabels_to_resume_setup():
    view = SetupLauncherView(status="in_progress")
    assert _find_button(view, "setup:start").label == "Resume Setup"


def test_launcher_view_complete_relabels_to_re_run_setup():
    view = SetupLauncherView(status="complete")
    assert _find_button(view, "setup:start").label == "Re-run Setup"


def test_launcher_view_pending_keeps_default_label():
    view = SetupLauncherView(status="pending")
    assert _find_button(view, "setup:start").label == "Start Setup"


def test_launcher_view_dismissed_keeps_default_label():
    view = SetupLauncherView(status="dismissed")
    assert _find_button(view, "setup:start").label == "Start Setup"


def _session_with_message(
    *,
    status: str = "in_progress",
    channel_id: int = 5555,
    message_id: int = 8888,
):
    return SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status=status,
        setup_channel_id=channel_id,
        setup_message_id=message_id,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )


@pytest.mark.asyncio
async def test_resume_one_launcher_edits_message_with_status_aware_view():
    import discord

    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    message = MagicMock()
    message.edit = AsyncMock()
    channel = MagicMock(spec=discord.TextChannel)
    channel.fetch_message = AsyncMock(return_value=message)
    guild = MagicMock(id=1)
    guild.get_channel = MagicMock(return_value=channel)

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_session_with_message(status="in_progress"),
    ):
        result = await cog._resume_one_launcher(guild)

    assert result is True
    channel.fetch_message.assert_awaited_once_with(8888)
    message.edit.assert_awaited_once()
    edited_view = message.edit.await_args.kwargs["view"]
    assert isinstance(edited_view, SetupLauncherView)
    assert _find_button(edited_view, "setup:start").label == "Resume Setup"


@pytest.mark.asyncio
async def test_resume_one_launcher_skips_when_no_session_row():
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)
    guild = MagicMock(id=1)

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await cog._resume_one_launcher(guild)

    assert result is False


@pytest.mark.asyncio
async def test_resume_one_launcher_skips_when_channel_or_message_id_missing():
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)
    guild = MagicMock(id=1)

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_session_with_message(channel_id=None, message_id=None),
    ):
        result = await cog._resume_one_launcher(guild)

    assert result is False


@pytest.mark.asyncio
async def test_resume_one_launcher_handles_deleted_message_silently():
    import discord

    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    channel = MagicMock(spec=discord.TextChannel)
    channel.fetch_message = AsyncMock(
        side_effect=discord.NotFound(MagicMock(), "gone"),
    )
    guild = MagicMock(id=1)
    guild.get_channel = MagicMock(return_value=channel)

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_session_with_message(),
    ):
        # Must not raise.
        result = await cog._resume_one_launcher(guild)

    assert result is False


@pytest.mark.asyncio
async def test_resume_one_launcher_handles_forbidden_silently():
    import discord

    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    cog = SetupCog(bot)

    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "general"
    channel.fetch_message = AsyncMock(
        side_effect=discord.Forbidden(MagicMock(), "no perm"),
    )
    guild = MagicMock(id=1)
    guild.get_channel = MagicMock(return_value=channel)

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_session_with_message(),
    ):
        result = await cog._resume_one_launcher(guild)

    assert result is False


@pytest.mark.asyncio
async def test_resume_launchers_iterates_every_guild_and_isolates_failures():
    from cogs.setup_cog import SetupCog

    bot = MagicMock()
    g1 = MagicMock(id=1)
    g2 = MagicMock(id=2)
    g3 = MagicMock(id=3)
    bot.guilds = [g1, g2, g3]
    cog = SetupCog(bot)

    seen_ids: list[int] = []

    async def fake_resume_one(guild):
        seen_ids.append(guild.id)
        if guild.id == 2:
            raise RuntimeError("boom on guild 2")
        return True

    with patch.object(
        cog,
        "_resume_one_launcher",
        side_effect=fake_resume_one,
    ):
        await cog._resume_launchers()

    # All three guilds processed, the failure on guild 2 did not
    # short-circuit the sweep.
    assert seen_ids == [1, 2, 3]


# ---------------------------------------------------------------------------
# Direct entry: !setup prefix command + /setup slash command
# ---------------------------------------------------------------------------


def _mock_ctx(author, guild=None, guild_id: int = 1):
    """Construct a minimal commands.Context double for prefix-command tests."""
    if guild is None:
        guild = MagicMock()
        guild.id = guild_id
        guild.name = "Test"
        guild.owner_id = 99
    ctx = MagicMock()
    ctx.author = author
    ctx.guild = guild
    ctx.send = AsyncMock()
    return ctx


def _delegated_session(
    *,
    owner_id: int = 99,
    delegated=(42,),
    depth: str | None = "standard",
) -> SetupSession:
    """Test fixture session.

    Defaults ``depth="standard"`` so callers exercising the hub path
    don't accidentally hit the depth picker. Pass ``depth=None`` to
    test the picker flow.
    """
    return SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=owner_id,
        setup_status="pending",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=tuple(delegated),
        depth=depth,
    )


@pytest.mark.asyncio
async def test_setup_cmd_opens_hub_for_owner():
    from cogs.setup_cog import SetupCog
    from views.setup.hub import SetupHubView

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "cogs.setup_cog.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await cog.setup_cmd.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    sent_view = ctx.send.await_args.kwargs.get("view")
    assert isinstance(sent_view, SetupHubView)
    mark_mock.assert_awaited_once()
    assert mark_mock.await_args.kwargs.get("step") == "hub"


@pytest.mark.asyncio
async def test_setup_cmd_starts_session_when_missing():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.setup_cog.setup_session.start_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ) as start_mock,
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "cogs.setup_cog.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await cog.setup_cmd.callback(cog, ctx)

    start_mock.assert_awaited_once()
    ctx.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_setup_cmd_shows_depth_picker_when_depth_unset():
    """First-time entry (session.depth=None) routes the operator
    through the depth picker before opening the hub."""
    from cogs.setup_cog import SetupCog
    from views.setup.depth_panel import DepthPanelView

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(depth=None),
        ),
        patch(
            "cogs.setup_cog.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await cog.setup_cmd.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    sent_view = ctx.send.await_args.kwargs.get("view")
    assert isinstance(sent_view, DepthPanelView)
    # mark_in_progress should NOT fire — the operator hasn't reached
    # the hub yet.
    mark_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_setup_cmd_returns_readiness_for_plain_admin():
    """A Discord administrator with no delegation gets the readiness embed,
    not the hub — they may scan but not apply."""
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_admin_member())

    fake_embed = MagicMock()
    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "cogs.diagnostic._platform_embeds.build_setup_readiness_embed",
            new_callable=AsyncMock,
            return_value=fake_embed,
        ),
    ):
        await cog.setup_cmd.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    # Readiness path sends an embed but no hub view.
    assert ctx.send.await_args.kwargs.get("embed") is fake_embed
    assert ctx.send.await_args.kwargs.get("view") is None


@pytest.mark.asyncio
async def test_setup_cmd_opens_hub_for_delegated_admin():
    from cogs.setup_cog import SetupCog
    from views.setup.hub import SetupHubView

    cog = SetupCog(MagicMock())
    # Delegated admin: not the owner, not a Discord administrator, but
    # listed in session.delegated_admins.
    member = _random_member(user_id=42)
    ctx = _mock_ctx(member)

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=(42,)),
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "cogs.setup_cog.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await cog.setup_cmd.callback(cog, ctx)

    sent_view = ctx.send.await_args.kwargs.get("view")
    assert isinstance(sent_view, SetupHubView)


@pytest.mark.asyncio
async def test_setup_cmd_denies_random_member():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_random_member())

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_delegated_session(delegated=()),
    ):
        await cog.setup_cmd.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    msg = ctx.send.await_args.args[0]
    assert "owner" in msg.lower() or "admin" in msg.lower()
    # Denial path sends a string with no embed/view.
    assert ctx.send.await_args.kwargs == {}


@pytest.mark.asyncio
async def test_setup_cmd_requires_guild_context():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_owner_member(), guild=None)
    # Author isn't a discord.Member outside a guild — make it a User.
    ctx.author = MagicMock()  # not isinstance discord.Member

    await cog.setup_cmd.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    assert "server" in ctx.send.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_setup_slash_opens_hub_for_owner():
    from cogs.setup_cog import SetupCog
    from views.setup.hub import SetupHubView

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "cogs.setup_cog.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await cog.setup_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs.get("view"), SetupHubView)
    mark_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_setup_slash_returns_readiness_for_plain_admin():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_admin_member())

    fake_embed = MagicMock()
    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "cogs.diagnostic._platform_embeds.build_setup_readiness_embed",
            new_callable=AsyncMock,
            return_value=fake_embed,
        ),
    ):
        await cog.setup_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert kwargs.get("embed") is fake_embed
    assert "view" not in kwargs or kwargs.get("view") is None


# ---------------------------------------------------------------------------
# Repost launcher button
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_repost_launcher_admin_can_repost():
    """Admin click reposts launcher in current guild and refreshes session ids."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())
    interaction.guild = MagicMock()
    interaction.guild.id = 1
    interaction.guild.name = "Test"
    interaction.guild.owner_id = 99

    fake_channel = MagicMock()
    fake_channel.id = 7777
    fake_message = MagicMock()
    fake_message.id = 9999

    with (
        patch(
            "views.setup.launcher.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "views.setup.launcher.post_launcher",
            new_callable=AsyncMock,
            return_value=(fake_channel, fake_message),
        ),
        patch(
            "views.setup.launcher.setup_session.start_session",
            new_callable=AsyncMock,
        ) as start_mock,
    ):
        await view._repost_launcher.callback(interaction)

    start_mock.assert_awaited_once()
    kwargs = start_mock.await_args.kwargs
    assert kwargs["setup_channel_id"] == 7777
    assert kwargs["setup_message_id"] == 9999
    interaction.response.send_message.assert_awaited_once()
    assert "7777" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_repost_launcher_denies_random_member():
    view = SetupLauncherView()
    interaction = _mock_interaction(_random_member())

    with (
        patch(
            "views.setup.launcher.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "views.setup.launcher.post_launcher",
            new_callable=AsyncMock,
        ) as post_mock,
    ):
        await view._repost_launcher.callback(interaction)

    post_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_repost_launcher_handles_no_target():
    """When no channel is sendable AND owner DM is closed, surface a deny."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())
    interaction.guild = MagicMock(id=1, name="Test", owner_id=99)

    with (
        patch(
            "views.setup.launcher.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "views.setup.launcher.post_launcher",
            new_callable=AsyncMock,
            return_value=(None, None),
        ),
        patch(
            "views.setup.launcher.setup_session.start_session",
            new_callable=AsyncMock,
        ) as start_mock,
    ):
        await view._repost_launcher.callback(interaction)

    start_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "could not" in msg.lower() or "sendable" in msg.lower()


def test_launcher_view_has_repost_launcher_button():
    view = SetupLauncherView()
    btn = _find_button(view, "setup:repost_launcher")
    assert btn.label == "Repost launcher"
    assert btn.row == 1


# ---------------------------------------------------------------------------
# /setup-status slash command
# ---------------------------------------------------------------------------


def test_status_embed_no_session_renders_no_session_row():
    from cogs.setup_cog import _build_status_embed

    embed = _build_status_embed(None, pending_ops=0)
    assert "no session" in (embed.description or "").lower()
    field_names = {f.name for f in embed.fields}
    assert "No session row" in field_names


def test_status_embed_full_session_renders_every_data_point():
    from cogs.setup_cog import _build_status_embed

    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=7000,
        setup_message_id=8000,
        last_readiness_score=85,
        current_step="cleanup",
        delegated_admins=(42,),
        skipped_sections=frozenset({"identity"}),
        depth="standard",
    )
    embed = _build_status_embed(session, pending_ops=3)
    field_names = {f.name for f in embed.fields}
    assert "Depth" in field_names
    assert "Current step" in field_names
    assert "Readiness" in field_names
    assert "Pending operations" in field_names
    assert "Skipped sections" in field_names
    assert "Delegated admins" in field_names
    assert "Setup channel" in field_names


def test_status_embed_omits_optional_fields_when_unset():
    from cogs.setup_cog import _build_status_embed

    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="pending",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )
    embed = _build_status_embed(session, pending_ops=0)
    field_names = {f.name for f in embed.fields}
    assert "Depth" not in field_names
    assert "Current step" not in field_names
    assert "Readiness" not in field_names
    # Pending operations is always shown.
    assert "Pending operations" in field_names


@pytest.mark.asyncio
async def test_setup_status_slash_returns_embed_for_admin():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_admin_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=2,
        ),
    ):
        await cog.setup_status_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_setup_status_slash_denies_random_member():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_random_member())

    with patch(
        "cogs.setup_cog.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_delegated_session(delegated=()),
    ):
        await cog.setup_status_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "owner" in msg.lower() or "admin" in msg.lower()

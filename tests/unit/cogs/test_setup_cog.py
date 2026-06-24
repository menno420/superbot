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

    with patch("services.setup_session.resume_session", AsyncMock(return_value=None)):
        with patch(
            "services.setup_session.start_session", AsyncMock(return_value=None)
        ):
            await view._start.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert (
        "server owner" in interaction.response.send_message.await_args.args[0].lower()
    )


@pytest.mark.asyncio
async def test_start_button_opens_wizard_for_owner():
    """Start Setup must open the linear wizard in #superbot-setup."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    mock_channel = MagicMock()
    mock_channel.mention = "#superbot-setup"
    mock_message = MagicMock()
    mock_message.jump_url = "https://discord.com/channels/1/2/3"

    with patch("services.setup_session.resume_session", AsyncMock(return_value=None)):
        with patch(
            "services.setup_session.start_session", AsyncMock(return_value=None)
        ):
            with patch(
                "views.setup.wizard.open_setup_workspace",
                AsyncMock(return_value=(mock_channel, mock_message, "ok")),
            ) as open_mock:
                await view._start.callback(interaction)

    # open_setup_workspace must be called exactly once.
    open_mock.assert_awaited_once()

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    msg = interaction.response.send_message.await_args.args[0]
    assert "#superbot-setup" in msg
    assert "wizard" in msg.lower() or "open" in msg.lower()


@pytest.mark.asyncio
async def test_start_button_requires_guild_context():
    """No guild → deny rather than crash."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())
    interaction.guild_id = None
    interaction.guild = None

    await view._start.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "server" in msg.lower()


@pytest.mark.asyncio
async def test_smart_suggestions_button_denies_plain_admin():
    """A plain administrator (not owner, not delegated) is rejected; the
    gate is the owner-or-delegated ladder (can_apply_setup), not owner-only."""
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    with patch(
        "services.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=None,
    ):
        await view._suggestions.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "owner" in msg or "delegate" in msg


@pytest.mark.asyncio
async def test_smart_suggestions_button_allows_delegated_admin():
    """A delegated (non-owner) setup admin can open Smart Suggestions."""
    from services.setup_plan import SetupPlanDraft
    from views.setup.ai_review.main_panel import AIReviewPanelView

    delegated = _random_member(user_id=7)
    view = SetupLauncherView()
    interaction = _mock_interaction(delegated)
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(7,),
    )
    fake_advisor = MagicMock()
    fake_advisor.suggest = AsyncMock(
        return_value=SetupPlanDraft(recommendations=(), source="deterministic"),
    )
    with (
        patch(
            "services.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=session,
        ),
        patch(
            "services.guild_snapshot.collect",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ),
        patch(
            "services.setup_ai_advisor.build_advisor",
            return_value=fake_advisor,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await view._suggestions.callback(interaction)

    sent_view = interaction.response.send_message.await_args.kwargs.get("view")
    assert isinstance(sent_view, AIReviewPanelView)


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
            "services.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
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
            "services.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
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
async def test_preset_button_denies_plain_admin():
    view = SetupLauncherView()
    interaction = _mock_interaction(_admin_member())

    with patch(
        "services.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=None,
    ):
        await view._preset.callback(interaction)

    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_preset_button_opens_template_picker_for_owner():
    """Owner click opens the template picker view, not a stub."""
    from views.setup.template_picker import TemplatePickerView

    view = SetupLauncherView()
    interaction = _mock_interaction(_owner_member())

    with patch(
        "services.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=None,
    ):
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


def _mock_channel_for_workspace(mention: str = "<#7000>") -> MagicMock:
    """Mock target channel returned by open_setup_workspace."""
    ch = MagicMock()
    ch.mention = mention
    return ch


def _mock_workspace_message(jump_url: str = "https://discord.com/x/y/z") -> MagicMock:
    """Mock anchor message returned by open_setup_workspace."""
    msg = MagicMock()
    msg.jump_url = jump_url
    return msg


@pytest.mark.asyncio
async def test_setup_cmd_opens_wizard_for_owner():
    """Phase 3: !setup posts the wizard in #superbot-setup and replies
    in the invoking channel with a jump link.  No hub view is sent
    in-channel anymore — that lives in /setup-hub.
    """
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_owner_member())

    channel = _mock_channel_for_workspace()
    message = _mock_workspace_message()
    with (
        patch(
            "cogs.setup._wizard_entry.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "cogs.setup._wizard_entry.open_setup_workspace",
            new_callable=AsyncMock,
            return_value=(channel, message, "ok"),
        ) as open_mock,
    ):
        await cog.setup_cmd.callback(cog, ctx)

    open_mock.assert_awaited_once()
    # Invoking channel reply mentions the workspace channel and the
    # jump link to the anchor message.
    ctx.send.assert_awaited_once()
    sent = ctx.send.await_args.args[0]
    assert channel.mention in sent
    assert message.jump_url in sent
    # No hub view is sent into the invoking channel anymore.
    assert "view" not in ctx.send.await_args.kwargs


@pytest.mark.asyncio
async def test_setup_cmd_starts_session_when_missing():
    """No session row → !setup starts one before opening the wizard."""
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_owner_member())

    channel = _mock_channel_for_workspace()
    message = _mock_workspace_message()
    with (
        patch(
            "cogs.setup._wizard_entry.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.setup._wizard_entry.setup_session.start_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ) as start_mock,
        patch(
            "cogs.setup._wizard_entry.open_setup_workspace",
            new_callable=AsyncMock,
            return_value=(channel, message, "ok"),
        ),
    ):
        await cog.setup_cmd.callback(cog, ctx)

    start_mock.assert_awaited_once()
    ctx.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_setup_cmd_handles_missing_setup_channel():
    """If ensure_setup_channel fails (no Manage Channels perm),
    !setup surfaces the recovery hint in the invoking channel.
    """
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_owner_member())

    with (
        patch(
            "cogs.setup._wizard_entry.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "cogs.setup._wizard_entry.open_setup_workspace",
            new_callable=AsyncMock,
            return_value=(None, None, "no_channel"),
        ),
    ):
        await cog.setup_cmd.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    msg = ctx.send.await_args.args[0].lower()
    assert "manage channels" in msg


@pytest.mark.asyncio
async def test_setup_hub_slash_opens_hub_for_owner():
    """The new /setup-hub compatibility command preserves the
    pre-Phase-3 behavior: opens the hub view ephemerally in the
    invoking channel.  Used by operators / tests that prefer the
    section-list UI to the linear wizard.
    """
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
        await cog.setup_hub_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs.get("view"), SetupHubView)
    mark_mock.assert_awaited_once()
    assert mark_mock.await_args.kwargs.get("step") == "hub"


@pytest.mark.asyncio
async def test_setup_hub_slash_shows_depth_picker_when_depth_unset():
    """The hub compat command still routes through the depth picker
    when no depth has been chosen yet (preserves the pre-Phase-3
    behavior under its new name).
    """
    from cogs.setup_cog import SetupCog
    from views.setup.depth_panel import DepthPanelView

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_owner_member())

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
        await cog.setup_hub_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    sent_view = interaction.response.send_message.await_args.kwargs.get("view")
    assert isinstance(sent_view, DepthPanelView)
    # mark_in_progress should NOT fire — the operator hasn't reached
    # the hub yet.
    mark_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_setup_cmd_returns_readiness_for_plain_admin():
    """A Discord administrator with no delegation gets the readiness embed,
    not the wizard — they may scan but not apply.  The new prefix
    flow preserves this branch.
    """
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_admin_member())

    fake_embed = MagicMock()
    with (
        patch(
            "cogs.setup._wizard_entry.setup_session.resume_session",
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
    # Readiness path sends an embed but no view.
    assert ctx.send.await_args.kwargs.get("embed") is fake_embed
    assert ctx.send.await_args.kwargs.get("view") is None


@pytest.mark.asyncio
async def test_setup_cmd_opens_wizard_for_delegated_admin():
    """Delegated admin (non-owner) gets the wizard workspace flow."""
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    # Delegated admin: not the owner, not a Discord administrator, but
    # listed in session.delegated_admins.
    member = _random_member(user_id=42)
    ctx = _mock_ctx(member)

    channel = _mock_channel_for_workspace()
    message = _mock_workspace_message()
    with (
        patch(
            "cogs.setup._wizard_entry.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=(42,)),
        ),
        patch(
            "cogs.setup._wizard_entry.open_setup_workspace",
            new_callable=AsyncMock,
            return_value=(channel, message, "ok"),
        ) as open_mock,
    ):
        await cog.setup_cmd.callback(cog, ctx)

    open_mock.assert_awaited_once()
    ctx.send.assert_awaited_once()
    sent = ctx.send.await_args.args[0]
    assert channel.mention in sent


@pytest.mark.asyncio
async def test_setup_cmd_denies_random_member():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    ctx = _mock_ctx(_random_member())

    with patch(
        "cogs.setup._wizard_entry.setup_session.resume_session",
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
async def test_setup_slash_opens_wizard_for_owner():
    """Phase 3: /setup opens the wizard via the workspace flow and
    replies ephemerally in the invoking channel with a jump link.
    """
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_owner_member())

    channel = _mock_channel_for_workspace()
    message = _mock_workspace_message()
    with (
        patch(
            "cogs.setup._wizard_entry.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "cogs.setup._wizard_entry.open_setup_workspace",
            new_callable=AsyncMock,
            return_value=(channel, message, "ok"),
        ) as open_mock,
    ):
        await cog.setup_slash.callback(cog, interaction)

    open_mock.assert_awaited_once()
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    sent = interaction.response.send_message.await_args.args[0]
    assert channel.mention in sent
    assert message.jump_url in sent


@pytest.mark.asyncio
async def test_setup_slash_returns_readiness_for_plain_admin():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_admin_member())

    fake_embed = MagicMock()
    with (
        patch(
            "cogs.setup._wizard_entry.setup_session.resume_session",
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


# ---------------------------------------------------------------------------
# /setup-reset slash command
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_reset_slash_clears_draft_for_owner():
    from cogs.setup_cog import SetupCog

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
            return_value=5,
        ),
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
    ):
        await cog.setup_reset_slash.callback(cog, interaction)

    clear_mock.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "5" in msg
    assert "cleared" in msg.lower()


@pytest.mark.asyncio
async def test_setup_reset_slash_short_circuits_when_draft_empty():
    """Empty draft → friendly 'nothing to clear' message, no clear call."""
    from cogs.setup_cog import SetupCog

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
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
    ):
        await cog.setup_reset_slash.callback(cog, interaction)

    clear_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "already empty" in msg.lower() or "no staged" in msg.lower()


@pytest.mark.asyncio
async def test_setup_reset_slash_denies_random_member():
    """Random members (no owner / delegation) cannot clear the draft."""
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_random_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
    ):
        await cog.setup_reset_slash.callback(cog, interaction)

    clear_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "owner" in msg.lower()


@pytest.mark.asyncio
async def test_setup_reset_slash_handles_clear_failure():
    from cogs.setup_cog import SetupCog

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
            return_value=3,
        ),
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
            side_effect=RuntimeError("db down"),
        ),
    ):
        await cog.setup_reset_slash.callback(cog, interaction)

    msg = interaction.response.send_message.await_args.args[0]
    assert "could not" in msg.lower() or "logs" in msg.lower()


# ---------------------------------------------------------------------------
# Launcher embed copy
# ---------------------------------------------------------------------------


def test_launcher_embed_mentions_slash_commands():
    """Regression: the persistent launcher embed should surface the
    direct-entry / status / reset slash commands so operators can
    discover them without exploring the slash UI."""
    from views.setup.launcher import _build_launcher_embed

    embed = _build_launcher_embed(None)
    description = (embed.description or "").lower()
    assert "!setup" in description or "/setup" in description
    assert "/setup-status" in description
    assert "/setup-reset" in description


# ---------------------------------------------------------------------------
# /setup-skip and /setup-unskip slash commands
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_skip_slash_marks_section_skipped():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "cogs.setup_cog.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
        ) as skip_mock,
    ):
        await cog.setup_skip_slash.callback(cog, interaction, section="cleanup")

    skip_mock.assert_awaited_once_with(1, "cleanup")
    msg = interaction.response.send_message.await_args.args[0]
    assert "cleanup" in msg.lower()
    assert "skipped" in msg.lower()


@pytest.mark.asyncio
async def test_setup_unskip_slash_unmarks_section():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "cogs.setup_cog.setup_session.unmark_section_skipped",
            new_callable=AsyncMock,
        ) as unskip_mock,
    ):
        await cog.setup_unskip_slash.callback(
            cog,
            interaction,
            section="cleanup",
        )

    unskip_mock.assert_awaited_once_with(1, "cleanup")
    msg = interaction.response.send_message.await_args.args[0]
    assert "un-skipped" in msg.lower() or "unskipped" in msg.lower()


@pytest.mark.asyncio
async def test_setup_skip_slash_rejects_unknown_section():
    """Unknown slugs surface a list of valid options."""
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(),
        ),
        patch(
            "cogs.setup_cog.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
        ) as skip_mock,
    ):
        await cog.setup_skip_slash.callback(
            cog,
            interaction,
            section="bogus-section",
        )

    skip_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "unknown" in msg.lower()


@pytest.mark.asyncio
async def test_setup_skip_slash_denies_random_member():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_random_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "cogs.setup_cog.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
        ) as skip_mock,
    ):
        await cog.setup_skip_slash.callback(
            cog,
            interaction,
            section="cleanup",
        )

    skip_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "owner" in msg.lower()


# ---------------------------------------------------------------------------
# /setup-depth slash command
# ---------------------------------------------------------------------------


def _depth_choice(value: str):
    """Build an app_commands.Choice mock for the /setup-depth tests."""
    return SimpleNamespace(
        name={
            "quick": "Quick (3 steps)",
            "standard": "Standard (5–6 steps)",
            "advanced": "Advanced (all sections)",
        }[value],
        value=value,
    )


@pytest.mark.asyncio
async def test_setup_depth_slash_persists_owner_choice():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(depth=None),
        ),
        patch(
            "cogs.setup_cog.setup_session.set_depth",
            new_callable=AsyncMock,
        ) as set_depth_mock,
    ):
        await cog.setup_depth_slash.callback(
            cog,
            interaction,
            depth=_depth_choice("standard"),
        )

    set_depth_mock.assert_awaited_once_with(1, "standard")
    msg = interaction.response.send_message.await_args.args[0]
    assert "standard" in msg.lower()


@pytest.mark.asyncio
async def test_setup_depth_slash_starts_session_when_missing():
    """Setting depth with no session row creates one first so the
    choice persists."""
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_owner_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.setup_cog.setup_session.start_session",
            new_callable=AsyncMock,
        ) as start_mock,
        patch(
            "cogs.setup_cog.setup_session.set_depth",
            new_callable=AsyncMock,
        ) as set_depth_mock,
    ):
        await cog.setup_depth_slash.callback(
            cog,
            interaction,
            depth=_depth_choice("quick"),
        )

    start_mock.assert_awaited_once()
    set_depth_mock.assert_awaited_once_with(1, "quick")


@pytest.mark.asyncio
async def test_setup_depth_slash_denies_random_member():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    interaction = _mock_interaction(_random_member())

    with (
        patch(
            "cogs.setup_cog.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "cogs.setup_cog.setup_session.set_depth",
            new_callable=AsyncMock,
        ) as set_depth_mock,
    ):
        await cog.setup_depth_slash.callback(
            cog,
            interaction,
            depth=_depth_choice("advanced"),
        )

    set_depth_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "owner" in msg.lower()


# ---------------------------------------------------------------------------
# /setup-delegate and /setup-undelegate slash commands (Phase 1)
# ---------------------------------------------------------------------------


def _target_member(member_id: int = 77):
    """Member object passed to /setup-delegate as the grant target."""
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = member_id
    m.mention = f"<@{member_id}>"
    m.bot = False
    return m


def _bot_target_member(member_id: int = 88):
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = member_id
    m.mention = f"<@{member_id}>"
    m.bot = True
    return m


def _delegate_interaction(actor, *, guild_id: int = 1, guild_owner_id: int = 99):
    """Mock interaction with a guild.id / guild.owner_id pair used by
    /setup-delegate / /setup-undelegate.
    """
    interaction = _mock_interaction(actor, guild_id=guild_id)
    interaction.guild.owner_id = guild_owner_id
    interaction.guild.name = "Test"
    return interaction


@pytest.mark.asyncio
async def test_setup_delegate_slash_grants_owner_can_promote():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    actor = _owner_member()
    target = _target_member(77)
    interaction = _delegate_interaction(actor)

    with (
        patch(
            "cogs.setup._helpers.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "cogs.setup._helpers.setup_session.add_delegated_admin",
            new_callable=AsyncMock,
        ) as add_mock,
        patch(
            "services.setup_channel.recompute_setup_channel_overwrites",
            new_callable=AsyncMock,
            return_value=True,
        ) as recompute_mock,
    ):
        await cog.setup_delegate_slash.callback(cog, interaction, member=target)

    add_mock.assert_awaited_once_with(1, 77, actor_id=99)
    # Channel overwrites recomputed so the new delegate gets explicit
    # channel access without needing to wait for the next ensure call.
    recompute_mock.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "delegated" in msg.lower()


@pytest.mark.asyncio
async def test_setup_undelegate_slash_owner_can_revoke():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    actor = _owner_member()
    target = _target_member(77)
    interaction = _delegate_interaction(actor)

    with (
        patch(
            "cogs.setup._helpers.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=(77,)),
        ),
        patch(
            "cogs.setup._helpers.setup_session.remove_delegated_admin",
            new_callable=AsyncMock,
        ) as remove_mock,
        patch(
            "services.setup_channel.recompute_setup_channel_overwrites",
            new_callable=AsyncMock,
            return_value=True,
        ) as recompute_mock,
    ):
        await cog.setup_undelegate_slash.callback(cog, interaction, member=target)

    remove_mock.assert_awaited_once_with(1, 77, actor_id=99)
    recompute_mock.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "un-delegated" in msg.lower() or "undelegated" in msg.lower()


@pytest.mark.asyncio
async def test_setup_delegate_slash_denies_non_owner():
    """Plain admin (not owner) cannot grant delegation — capability-
    significant promotion is owner-only on purpose.
    """
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    actor = _admin_member()  # admin=True but id=42, not owner=99
    target = _target_member(77)
    interaction = _delegate_interaction(actor)

    with (
        patch(
            "cogs.setup._helpers.setup_session.add_delegated_admin",
            new_callable=AsyncMock,
        ) as add_mock,
        patch(
            "services.setup_channel.recompute_setup_channel_overwrites",
            new_callable=AsyncMock,
        ) as recompute_mock,
    ):
        await cog.setup_delegate_slash.callback(cog, interaction, member=target)

    add_mock.assert_not_awaited()
    recompute_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "owner" in msg.lower()


@pytest.mark.asyncio
async def test_setup_undelegate_slash_denies_non_owner():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    actor = _admin_member()
    target = _target_member(77)
    interaction = _delegate_interaction(actor)

    with (
        patch(
            "cogs.setup._helpers.setup_session.remove_delegated_admin",
            new_callable=AsyncMock,
        ) as remove_mock,
    ):
        await cog.setup_undelegate_slash.callback(cog, interaction, member=target)

    remove_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "owner" in msg.lower()


@pytest.mark.asyncio
async def test_setup_delegate_slash_rejects_bot_target():
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    actor = _owner_member()
    target = _bot_target_member(88)
    interaction = _delegate_interaction(actor)

    with patch(
        "cogs.setup._helpers.setup_session.add_delegated_admin",
        new_callable=AsyncMock,
    ) as add_mock:
        await cog.setup_delegate_slash.callback(cog, interaction, member=target)

    add_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "bot" in msg.lower()


@pytest.mark.asyncio
async def test_setup_delegate_slash_rejects_owner_target():
    """Granting the owner delegation is a no-op the slash command
    rejects with a friendly message rather than silently succeeding.
    """
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    actor = _owner_member()  # id=99
    target = _target_member(99)  # also id=99, matches guild.owner_id
    interaction = _delegate_interaction(actor)

    with patch(
        "cogs.setup._helpers.setup_session.add_delegated_admin",
        new_callable=AsyncMock,
    ) as add_mock:
        await cog.setup_delegate_slash.callback(cog, interaction, member=target)

    add_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "owner" in msg.lower()


@pytest.mark.asyncio
async def test_setup_delegate_slash_starts_session_when_missing():
    """If no session row exists yet, the command initialises one so the
    delegation actually persists.
    """
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    actor = _owner_member()
    target = _target_member(77)
    interaction = _delegate_interaction(actor)

    # First resume_session call returns None; start_session then runs;
    # second resume_session (for the recompute) returns the new session.
    with (
        patch(
            "cogs.setup._helpers.setup_session.resume_session",
            new_callable=AsyncMock,
            side_effect=[None, _delegated_session(delegated=(77,))],
        ),
        patch(
            "cogs.setup._helpers.setup_session.start_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ) as start_mock,
        patch(
            "cogs.setup._helpers.setup_session.add_delegated_admin",
            new_callable=AsyncMock,
        ) as add_mock,
        patch(
            "services.setup_channel.recompute_setup_channel_overwrites",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        await cog.setup_delegate_slash.callback(cog, interaction, member=target)

    start_mock.assert_awaited_once()
    add_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_setup_delegate_slash_surfaces_db_failure():
    """A DB error during delegation surfaces as an error reply, not a
    fake success.
    """
    from cogs.setup_cog import SetupCog

    cog = SetupCog(MagicMock())
    actor = _owner_member()
    target = _target_member(77)
    interaction = _delegate_interaction(actor)

    with (
        patch(
            "cogs.setup._helpers.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_delegated_session(delegated=()),
        ),
        patch(
            "cogs.setup._helpers.setup_session.add_delegated_admin",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB exploded"),
        ),
    ):
        await cog.setup_delegate_slash.callback(cog, interaction, member=target)

    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "could not" in msg


# ---------------------------------------------------------------------------
# PR 3 — /setup-status posts to workspace as durable notice
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_status_slash_posts_durable_notice_in_workspace():
    """Aggressive ephemeral policy: /setup-status pushes the snapshot
    to #superbot-setup as a durable notice; the interaction reply is
    a short ephemeral pointer ("📋 Setup status posted in <#…>").
    """
    from cogs.setup_cog import SetupCog

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
            return_value=3,
        ),
        patch(
            "views.setup._anchor.push_setup_notice",
            new_callable=AsyncMock,
            return_value=True,
        ) as push_mock,
    ):
        await cog.setup_status_slash.callback(cog, interaction)

    push_mock.assert_awaited_once()
    # Pointer reply is ephemeral and references the workspace channel.
    interaction.response.send_message.assert_awaited_once()
    call = interaction.response.send_message.await_args
    assert call.kwargs.get("ephemeral") is True
    # Pointer carries the workspace mention.
    msg = call.args[0]
    assert "posted in" in msg.lower()


@pytest.mark.asyncio
async def test_setup_status_slash_falls_back_to_ephemeral_when_workspace_unreachable():
    """If push_setup_notice returns False (no workspace channel),
    fall back to the historic ephemeral embed reply so the operator
    still sees the snapshot.
    """
    from cogs.setup_cog import SetupCog

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
            "views.setup._anchor.push_setup_notice",
            new_callable=AsyncMock,
            return_value=False,
        ),
    ):
        await cog.setup_status_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    call_kwargs = interaction.response.send_message.await_args.kwargs
    # Fallback path sends the embed itself, still ephemeral.
    assert call_kwargs.get("ephemeral") is True
    assert call_kwargs.get("embed") is not None

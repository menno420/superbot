"""Tests for Essential Setup — the plain-language, direct-apply setup spine.

Pins:
* Flow navigation: advance / back / current_view / step counter / summary.
* Each step applies its config IMMEDIATELY through the audited
  ``SettingsMutationPipeline`` (direct lane) — and refuses (no write) until the
  required pick is made.
* The entry point is admin-gated and server-only.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime.subsystem_schema import BindingKind
from views.setup import essential_setup as es


def _member(admin: bool = True):
    return SimpleNamespace(
        id=99,
        guild_permissions=SimpleNamespace(administrator=admin),
    )


def _guild(gid: int = 1):
    return SimpleNamespace(id=gid, name="Test")


def _interaction():
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


@pytest.fixture
def pipeline():
    # The pipeline is imported lazily inside the step (setup views must not
    # import mutation pipelines at top level), so patch it at its source.
    with patch("services.settings_mutation.SettingsMutationPipeline") as cls:
        cls.return_value.set_value = AsyncMock()
        yield cls.return_value


@pytest.fixture
def binding_pipeline():
    # BindingMutationPipeline is also lazy-imported inside the log-channel step
    # (no-top-level-pipeline-import invariant) — patch at its source.
    with patch("services.binding_mutation.BindingMutationPipeline") as cls:
        cls.return_value.set_binding = AsyncMock()
        yield cls.return_value


@pytest.fixture
def channel_service():
    # ChannelLifecycleService (auto-create) is lazy-imported inside the step.
    with patch(
        "services.channel_lifecycle_service.ChannelLifecycleService",
    ) as cls:
        cls.return_value.create_channels = AsyncMock()
        yield cls.return_value


@pytest.fixture
def role_automation():
    # role_automation's threshold setters are lazy-imported inside the reward
    # step (`from services import role_automation`) — patch at the module.
    with (
        patch(
            "services.role_automation.set_xp_threshold",
            new=AsyncMock(),
        ) as xp,
        patch(
            "services.role_automation.set_time_threshold",
            new=AsyncMock(),
        ) as time,
    ):
        yield SimpleNamespace(set_xp_threshold=xp, set_time_threshold=time)


@pytest.fixture
def role_service():
    # RoleLifecycleService (role auto-create) is lazy-imported inside the step.
    with patch(
        "services.role_lifecycle_service.RoleLifecycleService",
    ) as cls:
        cls.return_value.apply = AsyncMock()
        yield cls.return_value


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


def test_flow_counter_and_navigation():
    flow = es.EssentialFlow(_member(), _guild())
    assert flow.total == 7
    assert flow.step_counter() == "Step 1 of 7"
    expected = [
        es.ServerTypeStep,
        es.GreetMembersStep,
        es.ModeratorsStep,
        es.BlockSpamStep,
        es.LogChannelStep,
        es.RewardActivityStep,
        es.HelpDeskStep,
    ]
    for i, cls in enumerate(expected):
        assert flow.step_counter() == f"Step {i + 1} of 7"
        assert isinstance(flow.current_view(), cls)
        flow.advance()

    assert flow.done
    assert isinstance(flow.current_view(), es.EssentialSummaryView)

    flow.back()
    assert isinstance(flow.current_view(), es.HelpDeskStep)


def test_first_step_has_no_back_button():
    flow = es.EssentialFlow(_member(), _guild())
    step = es.ServerTypeStep(flow)
    assert not any(isinstance(c, es._BackButton) for c in step.children)
    # the second step does get a Back button
    flow.advance()
    step2 = es.GreetMembersStep(flow)
    assert any(isinstance(c, es._BackButton) for c in step2.children)


@pytest.mark.asyncio
async def test_skip_records_step_for_summary():
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 1
    step = es.GreetMembersStep(flow)

    await step.skip(_interaction())

    # Skipping records the step so the summary's "Skipped" recap can list it.
    assert flow.skipped == ["Greet new members"]
    assert flow.index == 2
    summary = es.EssentialSummaryView(flow).render()
    blob = (summary.description or "") + " ".join(f.value for f in summary.fields)
    assert "Greet new members" in blob


# ---------------------------------------------------------------------------
# Server type (step 0)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_server_type_requires_a_pick(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.ServerTypeStep(flow)
    interaction = _interaction()

    await step.apply(interaction)

    pipeline.set_value.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert flow.index == 0  # did not advance


@pytest.mark.asyncio
async def test_server_type_community_applies_bundle_and_xp_rate(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.ServerTypeStep(flow)
    step.server_type = "community"

    await step.apply(_interaction())

    settings = {
        (c.args[1], c.args[2]): c.args[3] for c in pipeline.set_value.await_args_list
    }
    # The curated automod + moderation bundle is applied verbatim.
    assert settings[("automod", "enabled")] is True
    assert settings[("automod", "caps_enabled")] is False  # community: caps allowed
    assert settings[("moderation", "dm_on_action")] is True
    # The "standard" XP rate triplet is applied (resolved from _XP_RATES).
    rate = es._XP_RATES["standard"]
    assert settings[("xp", "xp_min")] == rate[1]
    assert settings[("xp", "xp_max")] == rate[2]
    assert settings[("xp", "xp_cooldown")] == rate[3]
    assert flow.index == 1  # advanced
    assert flow.applied and "Community" in flow.applied[0]


@pytest.mark.asyncio
async def test_server_type_exploring_is_minimal_and_skips_xp(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.ServerTypeStep(flow)
    step.server_type = "exploring"

    await step.apply(_interaction())

    settings = {
        (c.args[1], c.args[2]): c.args[3] for c in pipeline.set_value.await_args_list
    }
    # Exploring = just basic spam protection; XP left untouched (xp_rate=None).
    assert settings == {
        ("automod", "enabled"): True,
        ("automod", "spam_enabled"): True,
    }
    assert not any(c.args[1] == "xp" for c in pipeline.set_value.await_args_list)
    assert flow.index == 1


@pytest.mark.asyncio
async def test_server_type_gaming_allows_invites(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    step = es.ServerTypeStep(flow)
    step.server_type = "gaming"

    await step.apply(_interaction())

    settings = {
        (c.args[1], c.args[2]): c.args[3] for c in pipeline.set_value.await_args_list
    }
    # Gaming servers share invite links → that filter is off; mass-ping on.
    assert settings[("automod", "invites_enabled")] is False
    assert settings[("automod", "mentions_enabled")] is True
    assert flow.index == 1


def test_every_server_type_uses_only_known_settings():
    # Step 0 must stay channel-independent: only the proven settings the other
    # spine steps write, and an xp_rate that resolves in _XP_RATES.
    allowed = {
        ("automod", "enabled"),
        ("automod", "spam_enabled"),
        ("automod", "invites_enabled"),
        ("automod", "caps_enabled"),
        ("automod", "mentions_enabled"),
        ("moderation", "dm_on_action"),
    }
    for preset in es._SERVER_TYPES:
        for subsystem, name, _value in preset.settings:
            assert (subsystem, name) in allowed, f"{preset.key}: {subsystem}.{name}"
        if preset.xp_rate is not None:
            assert preset.xp_rate in es._XP_RATES


# ---------------------------------------------------------------------------
# Greet members
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_greet_requires_channel_before_applying(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 1
    step = es.GreetMembersStep(flow)
    interaction = _interaction()

    await step.apply(interaction)

    pipeline.set_value.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert "channel" in interaction.response.send_message.await_args.args[0].lower()
    assert flow.index == 1  # did not advance


@pytest.mark.asyncio
async def test_greet_applies_welcome_settings_and_advances(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 1
    step = es.GreetMembersStep(flow)
    step.channel_id = 555
    step.entry_role_id = 777
    interaction = _interaction()

    await step.apply(interaction)

    # enabled + join_enabled + channel + entry_role = 4 immediate writes
    assert pipeline.set_value.await_count == 4
    subsystems = {c.args[1] for c in pipeline.set_value.await_args_list}
    names = {c.args[2] for c in pipeline.set_value.await_args_list}
    assert subsystems == {"welcome"}
    assert {"enabled", "join_enabled", "channel", "entry_role"} == names
    assert flow.index == 2  # advanced
    assert flow.applied and "555" in flow.applied[0]


@pytest.mark.asyncio
async def test_greet_without_role_writes_three_settings(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 1
    step = es.GreetMembersStep(flow)
    step.channel_id = 555
    await step.apply(_interaction())
    assert pipeline.set_value.await_count == 3


# ---------------------------------------------------------------------------
# Moderators
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moderators_requires_role(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 2
    step = es.ModeratorsStep(flow)
    interaction = _interaction()
    await step.apply(interaction)
    pipeline.set_value.assert_not_awaited()
    assert flow.index == 2


@pytest.mark.asyncio
async def test_moderators_applies_role_and_dm(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 2
    step = es.ModeratorsStep(flow)
    step.mod_role_id = 4242
    await step.apply(_interaction())
    assert pipeline.set_value.await_count == 2
    calls = {(c.args[1], c.args[2]) for c in pipeline.set_value.await_args_list}
    assert ("moderation", "moderator_role") in calls
    assert ("moderation", "dm_on_action") in calls
    assert flow.index == 3


# ---------------------------------------------------------------------------
# Block spam
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_block_spam_applies_automod_with_all_filters(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 3
    step = es.BlockSpamStep(flow)
    await step.apply(_interaction())
    # enabled + 4 filters = 5 immediate writes, all to automod
    assert pipeline.set_value.await_count == 5
    subsystems = {c.args[1] for c in pipeline.set_value.await_args_list}
    assert subsystems == {"automod"}
    names = {c.args[2] for c in pipeline.set_value.await_args_list}
    assert names == {
        "enabled",
        "spam_enabled",
        "invites_enabled",
        "caps_enabled",
        "mentions_enabled",
    }
    assert flow.index == 4


@pytest.mark.asyncio
async def test_block_spam_respects_toggled_off_filter(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 3
    step = es.BlockSpamStep(flow)
    step.filters.discard("caps_enabled")  # untick one in the multi-select
    await step.apply(_interaction())
    by_name = {c.args[2]: c.args[3] for c in pipeline.set_value.await_args_list}
    assert by_name["caps_enabled"] is False
    assert by_name["spam_enabled"] is True


# ---------------------------------------------------------------------------
# Choose a log channel
# ---------------------------------------------------------------------------


def _created(target_id: int):
    return SimpleNamespace(
        applied=(SimpleNamespace(target_id=target_id),),
        first_error="",
    )


@pytest.mark.asyncio
async def test_log_channel_defaults_create_both_and_bind(
    pipeline,
    binding_pipeline,
    channel_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 4
    step = es.LogChannelStep(flow)  # defaults: members + roles on, messages off
    # No channels picked → auto-create both (mod first, then activity).
    channel_service.create_channels.side_effect = [_created(111), _created(222)]

    await step.apply(_interaction())

    # Both default channels created, in order.
    assert channel_service.create_channels.await_count == 2
    names = [c.args[1][0] for c in channel_service.create_channels.await_args_list]
    assert names == ["mod-log", "server-log"]
    # logging enabled + the three category flags applied per the defaults.
    settings = {
        (c.args[1], c.args[2]): c.args[3] for c in pipeline.set_value.await_args_list
    }
    assert settings[("logging", "enabled")] is True
    assert settings[("logging", "members_enabled")] is True
    assert settings[("logging", "roles_enabled")] is True
    assert settings[("logging", "messages_enabled")] is False  # privacy: off default
    # mod_channel → the mod log, events_channel → the activity log.
    binds = {c.args[2]: c.args[4] for c in binding_pipeline.set_binding.await_args_list}
    assert binds == {"mod_channel": 111, "events_channel": 222}
    assert all(
        c.args[3] == BindingKind.CHANNEL
        for c in binding_pipeline.set_binding.await_args_list
    )
    assert flow.index == 5


@pytest.mark.asyncio
async def test_log_channel_picked_channels_bind_without_create(
    pipeline,
    binding_pipeline,
    channel_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 4
    step = es.LogChannelStep(flow)
    step.mod_channel_id = 700
    step.activity_channel_id = 800

    await step.apply(_interaction())

    channel_service.create_channels.assert_not_awaited()
    binds = {c.args[2]: c.args[4] for c in binding_pipeline.set_binding.await_args_list}
    assert binds == {"mod_channel": 700, "events_channel": 800}
    assert flow.index == 5


@pytest.mark.asyncio
async def test_log_channel_no_activity_logs_moderation_only(
    pipeline,
    binding_pipeline,
    channel_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 4
    step = es.LogChannelStep(flow)
    step.activity = set()  # operator unticked every activity type
    step.mod_channel_id = 700

    await step.apply(_interaction())

    # Only the moderation channel is bound — no activity channel, no create.
    channel_service.create_channels.assert_not_awaited()
    assert {c.args[2] for c in binding_pipeline.set_binding.await_args_list} == {
        "mod_channel"
    }
    # The three activity flags are explicitly written off.
    settings = {
        (c.args[1], c.args[2]): c.args[3] for c in pipeline.set_value.await_args_list
    }
    assert settings[("logging", "members_enabled")] is False
    assert settings[("logging", "roles_enabled")] is False
    assert settings[("logging", "messages_enabled")] is False
    assert flow.index == 5


@pytest.mark.asyncio
async def test_log_channel_create_failure_blocks(
    pipeline,
    binding_pipeline,
    channel_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 4
    step = es.LogChannelStep(flow)  # defaults; no channels picked → tries mod create
    channel_service.create_channels.return_value = SimpleNamespace(
        applied=(),
        first_error="missing permission",
    )
    interaction = _interaction()

    await step.apply(interaction)

    # The mod-channel create failed → surfaced an error, wrote nothing, no advance.
    channel_service.create_channels.assert_awaited_once()
    binding_pipeline.set_binding.assert_not_awaited()
    pipeline.set_value.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert flow.index == 4


@pytest.mark.asyncio
async def test_log_channel_custom_names_used_when_creating(
    pipeline,
    binding_pipeline,
    channel_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 4
    step = es.LogChannelStep(flow)
    # Optional typing: custom names for both auto-created channels.
    step.mod_channel_name = "staff-log"
    step.activity_channel_name = "member-log"
    channel_service.create_channels.side_effect = [_created(11), _created(22)]

    await step.apply(_interaction())

    names = [c.args[1][0] for c in channel_service.create_channels.await_args_list]
    assert names == ["staff-log", "member-log"]
    assert flow.index == 5


# ---------------------------------------------------------------------------
# Reward active members
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reward_no_rewards_applies_rate_only(
    pipeline, role_automation, role_service
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 5
    step = es.RewardActivityStep(flow)
    step.xp_rate = "active"  # rewards stay empty

    await step.on_next(_interaction())

    # XP-rate scalars applied; no role work; advanced past the step.
    names = {(c.args[1], c.args[2]) for c in pipeline.set_value.await_args_list}
    assert {("xp", "xp_min"), ("xp", "xp_max"), ("xp", "xp_cooldown")} <= names
    role_automation.set_xp_threshold.assert_not_awaited()
    role_service.apply.assert_not_awaited()
    assert flow.index == 6


@pytest.mark.asyncio
async def test_reward_keep_rate_no_rewards_is_noop_advance(pipeline, role_automation):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 5
    step = es.RewardActivityStep(flow)  # xp_rate="keep", rewards empty

    await step.on_next(_interaction())

    pipeline.set_value.assert_not_awaited()
    role_automation.set_xp_threshold.assert_not_awaited()
    assert flow.index == 6


@pytest.mark.asyncio
async def test_reward_next_with_rewards_enters_role_phase(pipeline):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 5
    step = es.RewardActivityStep(flow)
    step.rewards = {"level"}

    await step.on_next(_interaction())

    # Moves to screen 2 without applying or advancing.
    assert step.phase == "roles"
    pipeline.set_value.assert_not_awaited()
    assert flow.index == 5


@pytest.mark.asyncio
async def test_reward_recommended_creates_role_and_sets_level(
    pipeline,
    role_automation,
    role_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 5
    step = es.RewardActivityStep(flow)
    step.rewards = {"level"}
    step.phase = "roles"
    step.role_source = "recommended"
    role_service.apply.return_value = SimpleNamespace(
        applied=(SimpleNamespace(target_id=900),),
        first_error="",
    )

    await step.apply(_interaction())

    # A role was created and the XP-level reward was set on it.
    role_service.apply.assert_awaited_once()
    role_automation.set_xp_threshold.assert_awaited_once()
    kwargs = role_automation.set_xp_threshold.await_args.kwargs
    assert kwargs["role_id"] == 900
    assert kwargs["role_name"] == "Regular"
    assert kwargs["level"] == 10
    assert kwargs["guild_id"] == 1
    assert kwargs["actor_id"] == 99
    role_automation.set_time_threshold.assert_not_awaited()
    assert flow.index == 6


@pytest.mark.asyncio
async def test_reward_existing_role_both_triggers(
    pipeline,
    role_automation,
    role_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 5
    step = es.RewardActivityStep(flow)
    step.rewards = {"level", "time"}
    step.phase = "roles"
    step.role_source = "existing"
    step.existing_role_id = 555
    step.existing_role_name = "Member"

    await step.apply(_interaction())

    # No role created; both rewards set on the existing role.
    role_service.apply.assert_not_awaited()
    assert role_automation.set_xp_threshold.await_args.kwargs["role_id"] == 555
    assert role_automation.set_time_threshold.await_args.kwargs["role_id"] == 555
    assert role_automation.set_time_threshold.await_args.kwargs["days"] == 30
    assert flow.index == 6


@pytest.mark.asyncio
async def test_reward_existing_requires_a_pick(pipeline, role_automation, role_service):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 5
    step = es.RewardActivityStep(flow)
    step.rewards = {"level"}
    step.phase = "roles"
    step.role_source = "existing"  # existing_role_id stays None
    interaction = _interaction()

    await step.apply(interaction)

    role_service.apply.assert_not_awaited()
    role_automation.set_xp_threshold.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert flow.index == 5  # did not advance


@pytest.mark.asyncio
async def test_reward_role_create_failure_blocks(
    pipeline,
    role_automation,
    role_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 5
    step = es.RewardActivityStep(flow)
    step.rewards = {"level"}
    step.phase = "roles"
    step.role_source = "recommended"
    role_service.apply.return_value = SimpleNamespace(
        applied=(),
        first_error="missing permission",
    )
    interaction = _interaction()

    await step.apply(interaction)

    role_service.apply.assert_awaited_once()
    role_automation.set_xp_threshold.assert_not_awaited()
    pipeline.set_value.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert flow.index == 5


@pytest.mark.asyncio
async def test_reward_create_uses_custom_role_name(
    pipeline,
    role_automation,
    role_service,
):
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 5
    step = es.RewardActivityStep(flow)
    step.rewards = {"level"}
    step.phase = "roles"
    step.role_source = "create"
    step.new_role_name = "Champion"  # optional typing → custom role name
    role_service.apply.return_value = SimpleNamespace(
        applied=(SimpleNamespace(target_id=909),),
        first_error="",
    )

    await step.apply(_interaction())

    # The role is created with the typed name, and the reward is set on it.
    request = role_service.apply.await_args.args[1]
    assert request.name == "Champion"
    assert role_automation.set_xp_threshold.await_args.kwargs["role_name"] == "Champion"
    assert role_automation.set_xp_threshold.await_args.kwargs["role_id"] == 909
    assert flow.index == 6


# ---------------------------------------------------------------------------
# Help desk
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_desk_requires_staff_role():
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 6
    step = es.HelpDeskStep(flow)
    interaction = _interaction()
    with patch("services.ticket_mutation.update_config", new=AsyncMock()) as upd:
        await step.apply(interaction)
    upd.assert_not_awaited()
    assert flow.index == 6
    assert "staff" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_help_desk_enables_tickets_and_advances():
    flow = es.EssentialFlow(_member(), _guild())
    flow.index = 6
    step = es.HelpDeskStep(flow)
    step.staff_role_id = 321
    step.log_channel_id = 654
    with patch("services.ticket_mutation.update_config", new=AsyncMock()) as upd:
        await step.apply(_interaction())
    upd.assert_awaited_once()
    kwargs = upd.await_args.kwargs
    assert kwargs["enabled"] is True
    assert kwargs["staff_role_id"] == 321
    assert kwargs["log_channel_id"] == 654
    assert flow.index == 7


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def test_summary_lists_applied_changes():
    flow = es.EssentialFlow(_member(), _guild())
    flow.record_applied("Greetings on")
    flow.record_applied("Moderator role set")
    embed = es.EssentialSummaryView(flow).render()
    blob = (embed.description or "") + " ".join(f.value for f in embed.fields)
    assert "Greetings on" in blob
    assert "Moderator role set" in blob


# ---------------------------------------------------------------------------
# Entry gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_entry_rejects_dm():
    interaction = _interaction()
    interaction.guild = None
    interaction.user = _member()
    await es.open_essential_setup(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "server" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_entry_rejects_non_admin():
    interaction = _interaction()
    interaction.guild = _guild()
    member = MagicMock()
    member.guild_permissions.administrator = False
    interaction.user = member
    # isinstance(member, discord.Member) must hold for the admin branch; patch it.
    with patch.object(es.discord, "Member", MagicMock):
        await es.open_essential_setup(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "admin" in interaction.response.send_message.await_args.args[0].lower()


# ---------------------------------------------------------------------------
# Separate setup channel — the flow opens in #superbot-setup, not in-channel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_open_in_setup_channel_posts_flow_and_returns_ok():
    guild = _guild()
    member = _member()
    channel = MagicMock()
    channel.name = "superbot-setup"
    channel.send = AsyncMock(return_value=MagicMock(id=123))

    with (
        patch(
            "services.setup_session.resume_session",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.setup_channel.ensure_setup_channel",
            new=AsyncMock(return_value=(channel, True)),
        ),
    ):
        ch, msg, reason = await es.open_essential_setup_in_setup_channel(guild, member)

    assert reason == "ok"
    assert ch is channel
    channel.send.assert_awaited_once()
    # The posted message carries the first step's embed + an interactive view.
    assert channel.send.await_args.kwargs.get("view") is not None
    assert channel.send.await_args.kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_open_in_setup_channel_reports_no_channel_when_uncreatable():
    guild = _guild()
    member = _member()

    with (
        patch(
            "services.setup_session.resume_session",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "services.setup_channel.ensure_setup_channel",
            new=AsyncMock(return_value=(None, False)),
        ),
    ):
        ch, msg, reason = await es.open_essential_setup_in_setup_channel(guild, member)

    assert reason == "no_channel"
    assert ch is None
    assert msg is None


@pytest.mark.asyncio
async def test_open_essential_setup_slash_points_to_channel():
    """Happy path: the flow posts to #superbot-setup; the slash reply is an
    ephemeral pointer, not the flow itself."""
    interaction = _interaction()
    interaction.guild = _guild()
    member = MagicMock()
    member.guild_permissions.administrator = True
    interaction.user = member

    channel = MagicMock(mention="<#777>")
    message = MagicMock(jump_url="https://discord.com/channels/1/2/3")

    with (
        patch.object(es.discord, "Member", MagicMock),
        patch.object(
            es,
            "open_essential_setup_in_setup_channel",
            new=AsyncMock(return_value=(channel, message, "ok")),
        ),
    ):
        await es.open_essential_setup(interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    # Pointer reply mentions the channel; no view is sent in the invoking channel.
    assert "<#777>" in interaction.response.send_message.await_args.args[0]
    assert kwargs.get("view") is None


@pytest.mark.asyncio
async def test_open_essential_setup_slash_falls_back_in_channel():
    """No Manage Channels → the flow opens inline in the invoking channel so
    setup still works, with a one-line hint."""
    interaction = _interaction()
    interaction.guild = _guild()
    member = MagicMock()
    member.guild_permissions.administrator = True
    interaction.user = member

    with (
        patch.object(es.discord, "Member", MagicMock),
        patch.object(
            es,
            "open_essential_setup_in_setup_channel",
            new=AsyncMock(return_value=(None, None, "no_channel")),
        ),
    ):
        await es.open_essential_setup(interaction)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    # Inline fallback: the flow (embed + view) is sent in the invoking channel.
    assert kwargs.get("view") is not None
    assert kwargs.get("embed") is not None
    assert "manage channels" in (kwargs.get("content") or "").lower()


@pytest.mark.asyncio
async def test_open_essential_setup_prefix_points_to_channel():
    channel = MagicMock(mention="<#777>")
    message = MagicMock(jump_url="https://discord.com/channels/1/2/3")
    ctx = SimpleNamespace(
        guild=_guild(),
        author=MagicMock(),
        send=AsyncMock(),
    )
    ctx.author.guild_permissions.administrator = True

    with (
        patch.object(es.discord, "Member", MagicMock),
        patch.object(
            es,
            "open_essential_setup_in_setup_channel",
            new=AsyncMock(return_value=(channel, message, "ok")),
        ),
    ):
        await es.open_essential_setup_prefix(ctx)

    ctx.send.assert_awaited_once()
    assert "<#777>" in ctx.send.await_args.args[0]
    assert ctx.send.await_args.kwargs.get("view") is None

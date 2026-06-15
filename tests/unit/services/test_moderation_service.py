"""Tests for services.moderation_service (P3 PR-15)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.events_catalogue import KNOWN_EVENTS
from services import moderation_service
from services.history_cleanup import CleanupApplyResult, HistoryCleanupPlan
from services.moderation_config import ModerationPolicy
from services.moderation_service import EVT_MOD_ACTION, ReasonRequiredError


@pytest.fixture(autouse=True)
def _default_policy():
    """Patch the PR10 policy loader for every service test.

    Default is the behaviour-preserving baseline (DMs off, no ban purge,
    28-day timeout ceiling), so the convergence-era exact-call assertions
    still hold.  Config-behaviour tests set ``.return_value`` to a
    configured :class:`ModerationPolicy`.

    Note: the default escalation action is ``timeout`` at threshold 3, so a
    warn test that drives ``add_warning`` to/over 3 without exercising
    escalation sets ``warn_escalation_action="none"``.
    """
    with patch(
        "services.moderation_config.load_policy",
        new_callable=AsyncMock,
        return_value=ModerationPolicy(),
    ) as loader:
        yield loader


@pytest.fixture(autouse=True)
def _mute_audit_companion():
    """Patch the best-effort audit-routing companion for every test.

    ``moderation_service`` emits ``audit.action_recorded`` via
    :func:`emit_audit_action` (imported into its namespace) on top of the
    domain ``EVT_MOD_ACTION``.  Both resolve to the same EventBus object,
    so without this the per-test ``bus.emit`` patch would see two awaits.
    Muting the companion keeps the domain-event assertions exact; the
    companion is asserted explicitly in its own test.
    """
    with patch(
        "services.moderation_service.emit_audit_action",
        new_callable=AsyncMock,
    ) as companion:
        yield companion


def test_event_is_catalogued():
    assert EVT_MOD_ACTION in KNOWN_EVENTS


def _make_member(member_id: int = 12345, guild_id: int = 99999) -> MagicMock:
    member = MagicMock()
    member.id = member_id
    member.guild = MagicMock()
    member.guild.id = guild_id
    member.ban = AsyncMock()
    member.kick = AsyncMock()
    member.timeout = AsyncMock()
    return member


def _make_guild(guild_id: int = 99999) -> MagicMock:
    guild = MagicMock()
    guild.id = guild_id
    guild.ban = AsyncMock()
    guild.unban = AsyncMock()
    return guild


def _make_user(user_id: int = 54321) -> MagicMock:
    u = MagicMock()
    u.id = user_id
    return u


@pytest.mark.asyncio
async def test_warn_increments_count_and_emits_event(_default_policy):
    # Escalation off so this stays a pure single-warn assertion at count 3.
    _default_policy.return_value = ModerationPolicy(warn_escalation_action="none")
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        outcome = await moderation_service.warn(
            member,
            reason="spam",
            actor_id=42,
        )

    assert outcome.count == 3
    log_mod.assert_awaited_once_with(
        member.guild.id,
        "warn",
        member.id,
        42,
        "spam",
    )
    emit.assert_awaited_once()
    assert emit.await_args.args[0] == EVT_MOD_ACTION
    assert emit.await_args.kwargs["action"] == "warn"
    assert emit.await_args.kwargs["actor_id"] == 42


@pytest.mark.asyncio
async def test_timeout_calls_discord_api_and_emits_event():
    member = _make_member()
    until = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.timeout(
            member,
            until=until,
            reason="cooldown",
        )

    member.timeout.assert_awaited_once_with(until, reason="cooldown")
    emit.assert_awaited_once()
    assert emit.await_args.kwargs["action"] == "timeout"
    assert emit.await_args.kwargs["until"] == until.isoformat()


@pytest.mark.asyncio
async def test_kick_calls_discord_api_and_logs():
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.kick(member, reason="rule break")

    member.kick.assert_awaited_once_with(reason="rule break")
    log_mod.assert_awaited_once()
    assert emit.await_args.kwargs["action"] == "kick"


@pytest.mark.asyncio
async def test_ban_accepts_user_or_member():
    guild = _make_guild()
    user = _make_user()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.ban(guild, user, reason="evade", actor_id=42)

    guild.ban.assert_awaited_once_with(user, reason="evade")
    assert emit.await_args.kwargs["action"] == "ban"
    assert emit.await_args.kwargs["target_id"] == user.id


@pytest.mark.asyncio
async def test_unban_calls_discord_api_and_logs():
    guild = _make_guild()
    user = _make_user()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.unban(guild, user, reason="appeal accepted")

    guild.unban.assert_awaited_once_with(user, reason="appeal accepted")
    assert emit.await_args.kwargs["action"] == "unban"


@pytest.mark.asyncio
async def test_clear_warnings_deletes_and_logs():
    with (
        patch(
            "services.moderation_service.db.clear_warnings",
            new_callable=AsyncMock,
        ) as clear,
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.clear_warnings(
            guild_id=1,
            user_id=2,
            actor_id=42,
        )

    clear.assert_awaited_once_with(2, 1)
    # New rows align with the de-facto historical token ("clearwarnings")
    # written by every pre-convergence cog/modal surface.
    assert emit.await_args.kwargs["action"] == "clearwarnings"


@pytest.mark.asyncio
async def test_action_emits_audit_companion_with_shared_mutation_id(
    _mute_audit_companion,
):
    """Each action fires the audit.action_recorded companion with a
    mutation_id that matches the EVT_MOD_ACTION payload."""
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ),
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        await moderation_service.warn(member, reason="spam", actor_id=42)

    _mute_audit_companion.assert_awaited_once()
    ckw = _mute_audit_companion.await_args.kwargs
    assert ckw["subsystem"] == "moderation"
    assert ckw["mutation_type"] == "warn"
    assert ckw["target"] == f"user:{member.id}"
    assert ckw["scope"] == "guild"
    assert ckw["guild_id"] == member.guild.id
    assert ckw["actor_id"] == 42
    # Same mutation_id correlates the companion and the domain event.
    assert ckw["mutation_id"] == emit.await_args.kwargs["mutation_id"]


@pytest.mark.asyncio
async def test_audit_companion_failure_does_not_block_action(
    _mute_audit_companion,
):
    """A dropped audit companion must not invalidate the mod_logs write or
    the domain event — mod_logs is authoritative."""
    _mute_audit_companion.return_value = False  # bus dropped the companion
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=2,
        ),
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        outcome = await moderation_service.warn(member, reason="x", actor_id=1)

    assert outcome.count == 2
    log_mod.assert_awaited_once()
    emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_discord_forbidden_propagates_unmodified():
    """If Discord refuses the action, the service must NOT silently swallow."""
    import discord

    member = _make_member()
    member.kick = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "nope"))

    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        with pytest.raises(discord.Forbidden):
            await moderation_service.kick(member, reason="x")

    log_mod.assert_not_awaited()
    emit.assert_not_awaited()


# ---------------------------------------------------------------------------
# PR10 — config-backed behaviour (DM, ban purge, timeout ceiling)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_warn_dms_member_when_enabled(_default_policy):
    _default_policy.return_value = ModerationPolicy(dm_on_action=True)
    member = _make_member()
    member.guild.name = "Guildy"
    member.display_name = "Bob"
    member.send = AsyncMock()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.warn(member, reason="spam", actor_id=1)

    member.send.assert_awaited_once()
    body = member.send.await_args.args[0]
    assert "warned" in body
    assert "Guildy" in body
    assert "spam" in body


@pytest.mark.asyncio
async def test_no_dm_when_dm_on_action_disabled():
    """Default policy (DMs off) never messages the member."""
    member = _make_member()
    member.send = AsyncMock()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.warn(member, reason="spam", actor_id=1)

    member.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_dm_failure_does_not_block_action(_default_policy):
    """A closed-DM member must not stop the warning being recorded."""
    # Escalation off so the single warn is the only recorded action here.
    _default_policy.return_value = ModerationPolicy(
        dm_on_action=True, warn_escalation_action="none"
    )
    member = _make_member()
    member.guild.name = "G"
    member.send = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "dms closed"))
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=4,
        ),
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        outcome = await moderation_service.warn(member, reason="x", actor_id=1)

    assert outcome.count == 4
    log_mod.assert_awaited_once()
    member.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_kick_dms_before_removal(_default_policy):
    """The notify DM is sent before the member is kicked (still reachable)."""
    _default_policy.return_value = ModerationPolicy(dm_on_action=True)
    member = _make_member()
    member.guild.name = "G"
    member.send = AsyncMock()
    member.kick = AsyncMock()
    manager = MagicMock()
    manager.attach_mock(member.send, "send")
    manager.attach_mock(member.kick, "kick")
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.kick(member, reason="x", actor_id=1)

    order = [call[0] for call in manager.mock_calls]
    assert order.index("send") < order.index("kick")


@pytest.mark.asyncio
async def test_ban_dms_target_when_enabled(_default_policy):
    _default_policy.return_value = ModerationPolicy(dm_on_action=True)
    guild = _make_guild()
    guild.name = "G"
    user = _make_user()
    user.send = AsyncMock()
    user.display_name = "Eve"
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.ban(guild, user, reason="raids", actor_id=1)

    user.send.assert_awaited_once()
    assert "banned" in user.send.await_args.args[0]


@pytest.mark.asyncio
async def test_ban_purges_messages_when_configured(_default_policy):
    _default_policy.return_value = ModerationPolicy(ban_delete_message_days=7)
    guild = _make_guild()
    user = _make_user()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.ban(guild, user, reason="raid", actor_id=1)

    guild.ban.assert_awaited_once_with(
        user,
        reason="raid",
        delete_message_seconds=7 * 86400,
    )


@pytest.mark.asyncio
async def test_timeout_clamps_to_configured_ceiling(_default_policy):
    _default_policy.return_value = ModerationPolicy(max_timeout_minutes=60)
    member = _make_member()
    requested = discord.utils.utcnow() + timedelta(days=1)
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.timeout(member, until=requested, reason="x")

    called_until = member.timeout.await_args.args[0]
    assert called_until < requested  # clamped down to the ceiling
    expected_cap = discord.utils.utcnow() + timedelta(minutes=60)
    assert abs((called_until - expected_cap).total_seconds()) < 5


@pytest.mark.asyncio
async def test_timeout_within_ceiling_is_not_clamped(_default_policy):
    _default_policy.return_value = ModerationPolicy(max_timeout_minutes=40320)
    member = _make_member()
    requested = discord.utils.utcnow() + timedelta(minutes=30)
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.timeout(member, until=requested, reason="x")

    member.timeout.assert_awaited_once_with(requested, reason="x")


# ---------------------------------------------------------------------------
# PR10 — require_reason enforcement (warn / kick / ban; timeout exempt)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_warn_requires_reason_raises_before_side_effects(_default_policy):
    _default_policy.return_value = ModerationPolicy(require_reason=True)
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
        ) as add,
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        with pytest.raises(ReasonRequiredError):
            await moderation_service.warn(member, reason="", actor_id=1)

    # Raised at the seam before incrementing the count or writing the log.
    add.assert_not_awaited()
    log_mod.assert_not_awaited()


@pytest.mark.asyncio
async def test_kick_requires_reason_raises_before_removal(_default_policy):
    _default_policy.return_value = ModerationPolicy(require_reason=True)
    member = _make_member()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        with pytest.raises(ReasonRequiredError):
            await moderation_service.kick(member, reason="   ", actor_id=1)

    member.kick.assert_not_awaited()


@pytest.mark.asyncio
async def test_ban_requires_reason_raises_before_ban(_default_policy):
    _default_policy.return_value = ModerationPolicy(require_reason=True)
    guild = _make_guild()
    user = _make_user()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        with pytest.raises(ReasonRequiredError):
            await moderation_service.ban(guild, user, reason="", actor_id=1)

    guild.ban.assert_not_awaited()


@pytest.mark.asyncio
async def test_placeholder_reason_treated_as_missing_when_required(_default_policy):
    """The "No reason provided" placeholder counts as no reason."""
    _default_policy.return_value = ModerationPolicy(require_reason=True)
    member = _make_member()
    with (
        patch("services.moderation_service.db.add_warning", new_callable=AsyncMock),
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        with pytest.raises(ReasonRequiredError):
            await moderation_service.warn(
                member,
                reason="No reason provided",
                actor_id=1,
            )


@pytest.mark.asyncio
async def test_action_with_reason_passes_when_required(_default_policy):
    _default_policy.return_value = ModerationPolicy(require_reason=True)
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        outcome = await moderation_service.warn(member, reason="spam", actor_id=1)

    assert outcome.count == 1
    assert log_mod.await_args.args[4] == "spam"  # reason logged verbatim


@pytest.mark.asyncio
async def test_empty_reason_defaults_to_placeholder_when_not_required():
    """Default policy (require_reason off): an empty reason logs the placeholder."""
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.warn(member, reason="", actor_id=1)

    assert log_mod.await_args.args[4] == "No reason provided"


@pytest.mark.asyncio
async def test_timeout_exempt_from_require_reason(_default_policy):
    """Timeout's reason carries the duration, so require_reason never blocks it."""
    _default_policy.return_value = ModerationPolicy(require_reason=True)
    member = _make_member()
    until = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        await moderation_service.timeout(member, until=until, reason="", actor_id=1)

    member.timeout.assert_awaited_once()


# ---------------------------------------------------------------------------
# PR10 third slice — warn escalation owned at the seam
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_warn_no_escalation_below_threshold(_default_policy):
    _default_policy.return_value = ModerationPolicy()  # timeout at threshold 3
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=2,
        ),
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.db.clear_warnings",
            new_callable=AsyncMock,
        ) as clear,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        outcome = await moderation_service.warn(member, reason="x", actor_id=1)

    member.timeout.assert_not_awaited()
    clear.assert_not_awaited()
    assert outcome.escalated is False
    assert outcome.escalation_action is None
    assert outcome.count == 2
    assert outcome.threshold == 3


@pytest.mark.asyncio
async def test_warn_escalates_timeout_at_threshold(_default_policy):
    """The default ladder auto-timeouts at threshold then resets the count."""
    _default_policy.return_value = ModerationPolicy()  # timeout 10 @ threshold 3
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.db.clear_warnings",
            new_callable=AsyncMock,
        ) as clear,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        outcome = await moderation_service.warn(member, reason="spam", actor_id=1)

    member.timeout.assert_awaited_once()
    clear.assert_awaited_once_with(member.id, member.guild.id)
    assert outcome.escalated is True
    assert outcome.escalation_action == "timeout"
    assert outcome.timeout_minutes == 10
    assert outcome.escalation_blocked is False


@pytest.mark.asyncio
async def test_warn_escalates_kick_at_threshold(_default_policy):
    _default_policy.return_value = ModerationPolicy(warn_escalation_action="kick")
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.db.clear_warnings", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        outcome = await moderation_service.warn(member, reason="spam", actor_id=1)

    member.kick.assert_awaited_once()
    assert outcome.escalated is True
    assert outcome.escalation_action == "kick"
    assert outcome.timeout_minutes is None


@pytest.mark.asyncio
async def test_warn_escalates_ban_at_threshold(_default_policy):
    _default_policy.return_value = ModerationPolicy(warn_escalation_action="ban")
    member = _make_member()
    member.guild.ban = AsyncMock()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.db.clear_warnings", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        outcome = await moderation_service.warn(member, reason="spam", actor_id=1)

    member.guild.ban.assert_awaited_once()
    assert outcome.escalated is True
    assert outcome.escalation_action == "ban"


@pytest.mark.asyncio
async def test_warn_escalation_none_disables_auto_action(_default_policy):
    _default_policy.return_value = ModerationPolicy(warn_escalation_action="none")
    member = _make_member()
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=99,
        ),
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch(
            "services.moderation_service.db.clear_warnings",
            new_callable=AsyncMock,
        ) as clear,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        outcome = await moderation_service.warn(member, reason="x", actor_id=1)

    member.timeout.assert_not_awaited()
    member.kick.assert_not_awaited()
    clear.assert_not_awaited()
    assert outcome.escalated is False


@pytest.mark.asyncio
async def test_warn_escalation_blocked_when_forbidden(_default_policy):
    """A Forbidden on the escalation action is reported, not raised; the warn
    is still recorded and the count is NOT reset."""
    _default_policy.return_value = ModerationPolicy()  # timeout at threshold 3
    member = _make_member()
    member.timeout = AsyncMock(side_effect=discord.Forbidden(MagicMock(), "no perms"))
    with (
        patch(
            "services.moderation_service.db.add_warning",
            new_callable=AsyncMock,
            return_value=3,
        ),
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.db.clear_warnings",
            new_callable=AsyncMock,
        ) as clear,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
    ):
        outcome = await moderation_service.warn(member, reason="spam", actor_id=1)

    assert outcome.escalation_blocked is True
    assert outcome.escalated is False
    assert outcome.escalation_action == "timeout"
    clear.assert_not_awaited()  # count preserved on a blocked escalation
    log_mod.assert_awaited()  # the warn itself was recorded


# ---------------------------------------------------------------------------
# PR10 fourth slice — post-action message cleanup (requested from the
# cleanup service, owned at the kick/ban seam)
# ---------------------------------------------------------------------------


def _cleanup_actions(log_mod) -> list[str]:
    """The action token of every mod_logs row written during the call."""
    return [call.args[1] for call in log_mod.await_args_list]


@pytest.mark.asyncio
async def test_kick_requests_cleanup_when_configured(_default_policy):
    _default_policy.return_value = ModerationPolicy(
        post_action_cleanup="kick", post_action_cleanup_limit=50
    )
    member = _make_member()
    channel = MagicMock()
    plan = HistoryCleanupPlan(scanned=50, matched=[MagicMock(), MagicMock()])
    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
        patch(
            "services.history_cleanup.build_author_cleanup_plan",
            new_callable=AsyncMock,
            return_value=plan,
        ) as build,
        patch(
            "services.history_cleanup.apply_history_cleanup_plan",
            new_callable=AsyncMock,
            return_value=CleanupApplyResult(deleted=2, failed=0),
        ) as apply,
    ):
        outcome = await moderation_service.kick(
            member, reason="spam", actor_id=7, channel=channel
        )

    member.kick.assert_awaited_once()
    build.assert_awaited_once()
    assert build.await_args.args[0] is channel
    assert build.await_args.kwargs["author_id"] == member.id
    assert build.await_args.kwargs["limit"] == 50
    apply.assert_awaited_once_with(plan)
    assert outcome is not None
    assert outcome.requested is True
    assert outcome.deleted == 2
    assert outcome.blocked is False
    # Two mod_logs rows: the kick itself + the cleanup sweep.
    assert _cleanup_actions(log_mod) == ["kick", "post_action_cleanup"]


@pytest.mark.asyncio
async def test_kick_no_cleanup_when_policy_disabled(_default_policy):
    """Default policy (post_action_cleanup="none") never sweeps."""
    member = _make_member()
    channel = MagicMock()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
        patch(
            "services.history_cleanup.build_author_cleanup_plan",
            new_callable=AsyncMock,
        ) as build,
    ):
        outcome = await moderation_service.kick(
            member, reason="x", actor_id=1, channel=channel
        )

    build.assert_not_awaited()
    assert outcome is None


@pytest.mark.asyncio
async def test_kick_no_cleanup_without_channel(_default_policy):
    """Even with the policy on, no channel context means no sweep."""
    _default_policy.return_value = ModerationPolicy(post_action_cleanup="both")
    member = _make_member()
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
        patch(
            "services.history_cleanup.build_author_cleanup_plan",
            new_callable=AsyncMock,
        ) as build,
    ):
        outcome = await moderation_service.kick(member, reason="x", actor_id=1)

    build.assert_not_awaited()
    assert outcome is None


@pytest.mark.asyncio
async def test_ban_requests_cleanup_when_configured(_default_policy):
    _default_policy.return_value = ModerationPolicy(post_action_cleanup="ban")
    guild = _make_guild()
    user = _make_user()
    channel = MagicMock()
    plan = HistoryCleanupPlan(scanned=100, matched=[MagicMock()])
    with (
        patch("services.moderation_service.db.log_mod_action", new_callable=AsyncMock),
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
        patch(
            "services.history_cleanup.build_author_cleanup_plan",
            new_callable=AsyncMock,
            return_value=plan,
        ) as build,
        patch(
            "services.history_cleanup.apply_history_cleanup_plan",
            new_callable=AsyncMock,
            return_value=CleanupApplyResult(deleted=1, failed=0),
        ),
    ):
        outcome = await moderation_service.ban(
            guild, user, reason="raid", actor_id=1, channel=channel
        )

    guild.ban.assert_awaited_once()
    assert build.await_args.kwargs["author_id"] == user.id
    assert outcome is not None and outcome.deleted == 1


@pytest.mark.asyncio
async def test_cleanup_blocked_does_not_break_the_action(_default_policy):
    """A missing Read History / Manage Messages must not undo the kick."""
    _default_policy.return_value = ModerationPolicy(post_action_cleanup="kick")
    member = _make_member()
    channel = MagicMock()
    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
        patch(
            "services.history_cleanup.build_author_cleanup_plan",
            new_callable=AsyncMock,
            side_effect=discord.Forbidden(MagicMock(), "no history"),
        ),
    ):
        outcome = await moderation_service.kick(
            member, reason="x", actor_id=1, channel=channel
        )

    member.kick.assert_awaited_once()  # the action itself still happened
    assert outcome is not None
    assert outcome.blocked is True
    # Only the kick row — a blocked sweep records nothing.
    assert _cleanup_actions(log_mod) == ["kick"]


@pytest.mark.asyncio
async def test_cleanup_zero_deleted_skips_audit_row(_default_policy):
    """An empty sweep (nothing matched) is a silent no-op — no extra row."""
    _default_policy.return_value = ModerationPolicy(post_action_cleanup="kick")
    member = _make_member()
    channel = MagicMock()
    plan = HistoryCleanupPlan(scanned=30, matched=[])
    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch("services.moderation_service.bus.emit", new_callable=AsyncMock),
        patch(
            "services.history_cleanup.build_author_cleanup_plan",
            new_callable=AsyncMock,
            return_value=plan,
        ),
        patch(
            "services.history_cleanup.apply_history_cleanup_plan",
            new_callable=AsyncMock,
            return_value=CleanupApplyResult(deleted=0, failed=0),
        ),
    ):
        outcome = await moderation_service.kick(
            member, reason="x", actor_id=1, channel=channel
        )

    assert _cleanup_actions(log_mod) == ["kick"]
    assert outcome is not None
    assert outcome.requested is True
    assert outcome.deleted == 0


# ---------------------------------------------------------------------------
# auto_delete (§3.2 hook)
# ---------------------------------------------------------------------------


def _make_message(message_id: int = 555, guild_id: int = 99999, author_id: int = 42):
    msg = MagicMock()
    msg.id = message_id
    msg.guild = MagicMock()
    msg.guild.id = guild_id
    msg.guild.name = "test-guild"
    msg.author = MagicMock()
    msg.author.id = author_id
    msg.delete = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_auto_delete_happy_path_logs_and_emits():
    msg = _make_message()

    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        ok = await moderation_service.auto_delete(
            msg,
            reason="prohibited word match",
            rule="cleanup.prohibited_words",
        )

    assert ok is True
    msg.delete.assert_awaited_once()
    log_mod.assert_awaited_once_with(
        99999,
        "auto_delete:cleanup.prohibited_words",
        42,
        0,
        "prohibited word match",
    )
    emit.assert_awaited_once()
    kwargs = emit.call_args.kwargs
    assert kwargs["guild_id"] == 99999
    assert kwargs["target_id"] == 42
    assert kwargs["action"] == "auto_delete:cleanup.prohibited_words"


@pytest.mark.asyncio
async def test_auto_delete_already_gone_still_logs():
    """NotFound shouldn't prevent the audit row — the rule still triggered."""
    import discord

    msg = _make_message()
    msg.delete.side_effect = discord.NotFound(MagicMock(), "gone")

    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        ok = await moderation_service.auto_delete(
            msg,
            reason="x",
            rule="r",
        )

    assert ok is True
    log_mod.assert_awaited_once()
    emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_auto_delete_forbidden_returns_false_and_skips_audit():
    import discord

    msg = _make_message()
    msg.delete.side_effect = discord.Forbidden(MagicMock(), "no perms")

    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        ok = await moderation_service.auto_delete(msg, reason="x", rule="r")

    assert ok is False
    log_mod.assert_not_awaited()
    emit.assert_not_awaited()


@pytest.mark.asyncio
async def test_auto_delete_no_guild_returns_false():
    msg = _make_message()
    msg.guild = None

    with (
        patch(
            "services.moderation_service.db.log_mod_action",
            new_callable=AsyncMock,
        ) as log_mod,
        patch(
            "services.moderation_service.bus.emit",
            new_callable=AsyncMock,
        ) as emit,
    ):
        ok = await moderation_service.auto_delete(msg, reason="x", rule="r")

    assert ok is False
    msg.delete.assert_not_awaited()
    log_mod.assert_not_awaited()
    emit.assert_not_awaited()

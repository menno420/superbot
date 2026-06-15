"""Regression tests for moderation-modal interaction ACK safety.

Pre-fix the six moderation modals (warn / timeout / kick / ban /
modlogs / clearwarnings) did 2–3 DB queries or Discord-API calls
before issuing ``interaction.response.send_message``. Any of those
calls exceeding the 3-second interaction-token window surfaced
"Interaction Failed" on the operator side. ``_UnbanModal`` was
already correct (defer first, then unban, then ``followup.send``);
the fix lifts that shape into the other six.

These tests pin the new contract:

* Cheap validation paths (member-not-found, invalid duration,
  hierarchy denial) still use ``interaction.response.send_message``
  directly — no defer round-trip for sub-millisecond rejections.
* Once a callback reaches the slow path (DB write, Discord-API
  action), ``safe_defer`` is called *before* the slow call and the
  final reply is delivered via ``safe_followup``.
* The warn modal's threshold-followup branch still surfaces a
  follow-up message (now via ``safe_followup``) after the auto-
  timeout fires.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.moderation_service import WarnOutcome


def _interaction() -> MagicMock:
    """Build an interaction mock matching the shape ``modals.py`` uses."""
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 1
    interaction.guild = MagicMock()
    interaction.guild_id = 99
    interaction.client = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.original_response = AsyncMock(return_value=MagicMock())
    return interaction


def _member(member_id: int = 7) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = member_id
    member.mention = f"<@{member_id}>"
    member.display_name = f"User{member_id}"
    member.timeout = AsyncMock()
    member.kick = AsyncMock()
    member.ban = AsyncMock()
    return member


class _OrderTracker:
    """Tracks the order of `safe_defer` / slow-call / `safe_followup`."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def defer(self) -> AsyncMock:
        async def _impl(*_a, **_kw) -> bool:
            self.calls.append("defer")
            return True

        return AsyncMock(side_effect=_impl)

    def slow(self, name: str, return_value=None) -> AsyncMock:
        async def _impl(*_a, **_kw):
            self.calls.append(name)
            return return_value

        return AsyncMock(side_effect=_impl)

    def followup(self) -> AsyncMock:
        async def _impl(*_a, **_kw):
            self.calls.append("followup")
            return MagicMock()

        return AsyncMock(side_effect=_impl)


# ---------------------------------------------------------------------------
# _WarnModal
# ---------------------------------------------------------------------------


async def test_warn_modal_member_not_found_uses_immediate_response():
    from views.moderation.modals import _WarnModal

    modal = _WarnModal()
    modal.member_input = MagicMock(value="ghost")
    modal.reason_input = MagicMock(value="")
    interaction = _interaction()

    with (
        patch("views.moderation.modals._parse_member", return_value=None),
        patch("views.moderation.modals.safe_defer") as defer,
    ):
        await modal.on_submit(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.args[0].startswith("❌")
    defer.assert_not_called()


async def test_warn_modal_hierarchy_denial_uses_immediate_response():
    from views.moderation.modals import _WarnModal

    modal = _WarnModal()
    modal.member_input = MagicMock(value="someone")
    modal.reason_input = MagicMock(value="bad")
    interaction = _interaction()

    with (
        patch("views.moderation.modals._parse_member", return_value=_member()),
        patch(
            "views.moderation.modals._can_act_on_interaction",
            return_value="hierarchy denied",
        ),
        patch("views.moderation.modals.safe_defer") as defer,
    ):
        await modal.on_submit(interaction)

    interaction.response.send_message.assert_awaited_once_with(
        "hierarchy denied",
        ephemeral=True,
    )
    defer.assert_not_called()


async def test_warn_modal_happy_path_defers_before_db_io():
    from views.moderation.modals import _WarnModal

    modal = _WarnModal()
    modal.member_input = MagicMock(value="someone")
    modal.reason_input = MagicMock(value="be nice")
    interaction = _interaction()

    tracker = _OrderTracker()
    with (
        patch("views.moderation.modals._parse_member", return_value=_member()),
        patch(
            "views.moderation.modals._can_act_on_interaction",
            return_value=None,
        ),
        patch("views.moderation.modals.safe_defer", tracker.defer()),
        patch("views.moderation.modals.safe_followup", tracker.followup()),
        patch("views.moderation.modals.moderation_service") as mock_svc,
    ):
        # Below threshold → non-escalated outcome, one followup. Threshold reads
        # + escalation now live in the service, so the modal no longer calls
        # resolve_value here.
        mock_svc.warn = tracker.slow(
            "svc.warn", return_value=WarnOutcome(count=1, threshold=3),
        )
        await modal.on_submit(interaction)

    assert (
        tracker.calls[0] == "defer"
    ), f"defer must come before any service I/O; got {tracker.calls!r}"
    assert "svc.warn" in tracker.calls
    assert "followup" in tracker.calls
    interaction.response.send_message.assert_not_called()


async def test_warn_modal_threshold_branch_uses_followup_after_timeout():
    """Escalation is owned by the service; the modal renders the two-line
    outcome (warn confirmation + auto-timeout announcement).
    """
    from views.moderation.modals import _WarnModal

    modal = _WarnModal()
    modal.member_input = MagicMock(value="repeat-offender")
    modal.reason_input = MagicMock(value="strike three")
    interaction = _interaction()
    target = _member()

    followup_calls: list[tuple] = []

    async def _capture_followup(_inter, content=None, **kw):
        followup_calls.append((content, kw))
        return MagicMock()

    with (
        patch("views.moderation.modals._parse_member", return_value=target),
        patch(
            "views.moderation.modals._can_act_on_interaction",
            return_value=None,
        ),
        patch(
            "views.moderation.modals.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch(
            "views.moderation.modals.safe_followup",
            AsyncMock(side_effect=_capture_followup),
        ),
        patch("views.moderation.modals.moderation_service") as mock_svc,
    ):
        # The service performs the escalation internally and reports it on the
        # outcome — the modal no longer calls timeout / clear_warnings itself.
        mock_svc.warn = AsyncMock(
            return_value=WarnOutcome(
                count=3,
                threshold=3,
                escalated=True,
                escalation_action="timeout",
                timeout_minutes=10,
            ),
        )
        await modal.on_submit(interaction)

    # Two followups: warn-confirmation + auto-timeout announcement.
    assert len(followup_calls) == 2
    assert "warned" in followup_calls[0][0]
    assert "timed out" in followup_calls[1][0]


# ---------------------------------------------------------------------------
# _TimeoutModal
# ---------------------------------------------------------------------------


async def test_timeout_modal_invalid_duration_uses_immediate_response():
    from views.moderation.modals import _TimeoutModal

    modal = _TimeoutModal()
    modal.member_input = MagicMock(value="someone")
    modal.duration_input = MagicMock(value="abc")  # not isdigit
    modal.reason_input = MagicMock(value="")
    interaction = _interaction()

    with (
        patch("views.moderation.modals._parse_member", return_value=_member()),
        patch("views.moderation.modals.safe_defer") as defer,
    ):
        await modal.on_submit(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert "Duration" in interaction.response.send_message.await_args.args[0]
    defer.assert_not_called()


async def test_timeout_modal_happy_path_defers_before_discord_api():
    from views.moderation.modals import _TimeoutModal

    modal = _TimeoutModal()
    modal.member_input = MagicMock(value="someone")
    modal.duration_input = MagicMock(value="15")
    modal.reason_input = MagicMock(value="")
    interaction = _interaction()
    target = _member()
    tracker = _OrderTracker()

    with (
        patch("views.moderation.modals._parse_member", return_value=target),
        patch(
            "views.moderation.modals._can_act_on_interaction",
            return_value=None,
        ),
        patch("views.moderation.modals.safe_defer", tracker.defer()),
        patch("views.moderation.modals.safe_followup", tracker.followup()),
        patch("views.moderation.modals.moderation_service") as mock_svc,
    ):
        mock_svc.timeout = tracker.slow("svc.timeout")
        await modal.on_submit(interaction)

    assert tracker.calls[0] == "defer"
    assert tracker.calls.index("defer") < tracker.calls.index("svc.timeout")
    assert "followup" in tracker.calls
    interaction.response.send_message.assert_not_called()


async def test_timeout_modal_forbidden_replies_via_followup():
    from views.moderation.modals import _TimeoutModal

    modal = _TimeoutModal()
    modal.member_input = MagicMock(value="someone")
    modal.duration_input = MagicMock(value="15")
    modal.reason_input = MagicMock(value="")
    interaction = _interaction()
    target = _member()

    safe_followup = AsyncMock()
    with (
        patch("views.moderation.modals._parse_member", return_value=target),
        patch(
            "views.moderation.modals._can_act_on_interaction",
            return_value=None,
        ),
        patch(
            "views.moderation.modals.safe_defer",
            AsyncMock(return_value=True),
        ),
        patch("views.moderation.modals.safe_followup", safe_followup),
        patch("views.moderation.modals.moderation_service") as mock_svc,
    ):
        mock_svc.timeout = AsyncMock(
            side_effect=discord.Forbidden(MagicMock(), "nope"),
        )
        await modal.on_submit(interaction)

    safe_followup.assert_awaited_once()
    assert "No permission" in safe_followup.await_args.args[1]
    interaction.response.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# _KickModal / _BanModal (same shape — parametrize)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "modal_cls_name,action_attr",
    [("_KickModal", "kick"), ("_BanModal", "ban")],
)
async def test_kick_ban_modals_defer_before_discord_api(
    modal_cls_name: str,
    action_attr: str,
):
    from views.moderation import modals as modals_mod

    cls = getattr(modals_mod, modal_cls_name)
    modal = cls()
    modal.member_input = MagicMock(value="someone")
    modal.reason_input = MagicMock(value="reason")
    interaction = _interaction()
    target = _member()
    tracker = _OrderTracker()

    with (
        patch("views.moderation.modals._parse_member", return_value=target),
        patch(
            "views.moderation.modals._can_act_on_interaction",
            return_value=None,
        ),
        patch("views.moderation.modals.safe_defer", tracker.defer()),
        patch("views.moderation.modals.safe_followup", tracker.followup()),
        patch("views.moderation.modals.moderation_service") as mock_svc,
    ):
        setattr(mock_svc, action_attr, tracker.slow(f"svc.{action_attr}"))
        await modal.on_submit(interaction)

    assert tracker.calls[0] == "defer"
    assert tracker.calls.index("defer") < tracker.calls.index(f"svc.{action_attr}")
    assert "followup" in tracker.calls
    interaction.response.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# _ModLogsModal
# ---------------------------------------------------------------------------


async def test_modlogs_modal_member_not_found_uses_immediate_response():
    from views.moderation.modals import _ModLogsModal

    modal = _ModLogsModal()
    modal.member_input = MagicMock(value="ghost")
    interaction = _interaction()

    with (
        patch("views.moderation.modals._parse_member", return_value=None),
        patch("views.moderation.modals.safe_defer") as defer,
    ):
        await modal.on_submit(interaction)

    interaction.response.send_message.assert_awaited_once()
    defer.assert_not_called()


async def test_modlogs_modal_defers_ephemeral_before_db_read():
    from views.moderation.modals import _ModLogsModal

    modal = _ModLogsModal()
    modal.member_input = MagicMock(value="someone")
    interaction = _interaction()
    tracker = _OrderTracker()

    with (
        patch("views.moderation.modals._parse_member", return_value=_member()),
        patch("views.moderation.modals.safe_defer", tracker.defer()) as defer,
        patch("views.moderation.modals.safe_followup", tracker.followup()),
        patch("views.moderation.modals.db") as mock_db,
    ):
        mock_db.get_mod_logs = tracker.slow("get_mod_logs", return_value=[])
        await modal.on_submit(interaction)

    assert tracker.calls[0] == "defer"
    defer.assert_awaited_once()
    assert defer.await_args.kwargs.get("ephemeral") is True
    assert tracker.calls.index("defer") < tracker.calls.index("get_mod_logs")
    interaction.response.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# _ClearWarningsModal
# ---------------------------------------------------------------------------


async def test_clearwarnings_modal_defers_ephemeral_before_db_write():
    from views.moderation.modals import _ClearWarningsModal

    modal = _ClearWarningsModal()
    modal.member_input = MagicMock(value="someone")
    interaction = _interaction()
    tracker = _OrderTracker()

    with (
        patch("views.moderation.modals._parse_member", return_value=_member()),
        patch("views.moderation.modals.safe_defer", tracker.defer()) as defer,
        patch("views.moderation.modals.safe_followup", tracker.followup()),
        patch("views.moderation.modals.moderation_service") as mock_svc,
    ):
        mock_svc.clear_warnings = tracker.slow("svc.clear_warnings")
        await modal.on_submit(interaction)

    assert tracker.calls[0] == "defer"
    assert defer.await_args.kwargs.get("ephemeral") is True
    assert tracker.calls.index("defer") < tracker.calls.index("svc.clear_warnings")
    assert "followup" in tracker.calls
    interaction.response.send_message.assert_not_called()

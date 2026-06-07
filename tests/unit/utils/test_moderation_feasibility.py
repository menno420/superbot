"""Tests for utils.moderation_feasibility (server-management PR10).

The pure 'can the bot moderate here?' evaluator behind the mod panel's
read-only Bot-readiness line.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from utils.moderation_feasibility import (
    ModerationReadiness,
    evaluate_moderation_readiness,
    render_readiness_line,
)


def _guild(
    *,
    ban: bool = True,
    kick: bool = True,
    timeout: bool = True,
    admin: bool = False,
    top_position: int = 5,
    top_name: str = "Galaxy Bot",
) -> MagicMock:
    guild = MagicMock()
    perms = MagicMock()
    perms.ban_members = ban
    perms.kick_members = kick
    perms.moderate_members = timeout
    perms.administrator = admin
    guild.me.guild_permissions = perms
    guild.me.top_role.position = top_position
    guild.me.top_role.name = top_name
    return guild


# ---------------------------------------------------------------------------
# evaluate_moderation_readiness
# ---------------------------------------------------------------------------


def test_full_capability():
    r = evaluate_moderation_readiness(_guild())
    assert (r.can_ban, r.can_kick, r.can_timeout) == (True, True, True)
    assert r.fully_capable
    assert r.missing_permissions() == ()
    assert r.top_role_name == "Galaxy Bot"
    assert r.top_role_is_lowest is False


def test_missing_single_permission():
    r = evaluate_moderation_readiness(_guild(ban=False))
    assert r.can_ban is False
    assert r.fully_capable is False
    assert r.missing_permissions() == ("Ban Members",)


def test_missing_multiple_permissions_order():
    r = evaluate_moderation_readiness(_guild(ban=False, timeout=False))
    assert r.missing_permissions() == ("Ban Members", "Timeout Members")


def test_administrator_implies_every_capability():
    r = evaluate_moderation_readiness(
        _guild(ban=False, kick=False, timeout=False, admin=True),
    )
    assert (r.can_ban, r.can_kick, r.can_timeout) == (True, True, True)
    assert r.fully_capable
    assert r.missing_permissions() == ()


def test_top_role_at_bottom_is_not_fully_capable():
    r = evaluate_moderation_readiness(_guild(top_position=0))
    assert r.top_role_is_lowest is True
    # Has every permission but can't out-rank anyone → not fully capable.
    assert r.fully_capable is False


# ---------------------------------------------------------------------------
# render_readiness_line
# ---------------------------------------------------------------------------


def test_render_all_ok_mentions_top_role():
    line = render_readiness_line(
        ModerationReadiness(True, True, True, "Galaxy Bot", False),
    )
    assert "🟢" in line
    assert "below my top role" in line
    assert "**Galaxy Bot**" in line


def test_render_missing_permissions_lists_them():
    line = render_readiness_line(
        ModerationReadiness(False, True, False, "Galaxy Bot", False),
    )
    assert "Missing permission(s)" in line
    assert "Ban Members" in line
    assert "Timeout Members" in line


def test_render_top_role_lowest_warns():
    line = render_readiness_line(
        ModerationReadiness(True, True, True, "@everyone", True),
    )
    assert "bottom of the list" in line

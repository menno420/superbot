"""Phase 9e / Track 4 PR 8 — ``services.setup_access`` checks.

Pins the three role classes:

* Server owner → owner of the guild.
* Setup admin → administrator-tier OR delegated admin in the session.
* Anyone else → denied.

And the four permission helpers:

* ``can_view_setup`` / ``can_run_readiness`` — same gate as
  ``is_setup_admin``.
* ``can_apply_setup`` — owner OR delegated admin only.

Tests use plain stand-in member/session objects; no real
``discord.Member`` required.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from services import setup_access
from services.setup_session import SetupSession


def _member(*, user_id: int, guild_owner_id: int, administrator: bool = False):
    guild = SimpleNamespace(owner_id=guild_owner_id)
    perms = SimpleNamespace(administrator=administrator)
    return SimpleNamespace(
        id=user_id,
        guild=guild,
        guild_permissions=perms,
    )


def _session(*, owner_id: int, delegated: tuple[int, ...] = ()) -> SetupSession:
    return SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=owner_id,
        setup_status="pending",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=delegated,
    )


# ---------------------------------------------------------------------------
# is_server_owner / is_administrator
# ---------------------------------------------------------------------------


def test_is_server_owner_true_when_member_id_matches_owner():
    m = _member(user_id=99, guild_owner_id=99)
    assert setup_access.is_server_owner(m) is True


def test_is_server_owner_false_when_member_id_differs():
    m = _member(user_id=42, guild_owner_id=99)
    assert setup_access.is_server_owner(m) is False


def test_is_server_owner_false_when_member_has_no_guild():
    m = SimpleNamespace(id=99)
    assert setup_access.is_server_owner(m) is False


def test_is_administrator_returns_true_for_admin_perm():
    m = _member(user_id=42, guild_owner_id=99, administrator=True)
    assert setup_access.is_administrator(m) is True


def test_is_administrator_returns_false_without_admin_perm():
    m = _member(user_id=42, guild_owner_id=99, administrator=False)
    assert setup_access.is_administrator(m) is False


# ---------------------------------------------------------------------------
# is_setup_admin / can_view_setup / can_run_readiness
# ---------------------------------------------------------------------------


def test_owner_is_setup_admin_even_without_session():
    m = _member(user_id=99, guild_owner_id=99)
    assert setup_access.is_setup_admin(m, session=None) is True


def test_administrator_is_setup_admin():
    m = _member(user_id=42, guild_owner_id=99, administrator=True)
    assert setup_access.is_setup_admin(m, session=None) is True


def test_delegated_admin_is_setup_admin():
    m = _member(user_id=42, guild_owner_id=99)
    session = _session(owner_id=99, delegated=(42,))
    assert setup_access.is_setup_admin(m, session=session) is True


def test_random_member_is_not_setup_admin():
    m = _member(user_id=42, guild_owner_id=99)
    session = _session(owner_id=99)
    assert setup_access.is_setup_admin(m, session=session) is False


def test_can_view_setup_mirrors_is_setup_admin():
    m_admin = _member(user_id=42, guild_owner_id=99, administrator=True)
    m_random = _member(user_id=42, guild_owner_id=99)
    session = _session(owner_id=99)
    assert setup_access.can_view_setup(m_admin, session) is True
    assert setup_access.can_view_setup(m_random, session) is False


def test_can_run_readiness_mirrors_is_setup_admin():
    m_admin = _member(user_id=42, guild_owner_id=99, administrator=True)
    m_random = _member(user_id=42, guild_owner_id=99)
    session = _session(owner_id=99)
    assert setup_access.can_run_readiness(m_admin, session) is True
    assert setup_access.can_run_readiness(m_random, session) is False


# ---------------------------------------------------------------------------
# can_apply_setup — tighter than is_setup_admin
# ---------------------------------------------------------------------------


def test_can_apply_setup_admin_without_delegation_is_denied():
    """Administrator perm alone is NOT enough; the owner must
    explicitly delegate write authority."""
    m_admin = _member(user_id=42, guild_owner_id=99, administrator=True)
    session = _session(owner_id=99)
    assert setup_access.can_apply_setup(m_admin, session) is False


def test_can_apply_setup_owner_is_allowed():
    m_owner = _member(user_id=99, guild_owner_id=99)
    assert setup_access.can_apply_setup(m_owner, None) is True


def test_can_apply_setup_delegated_admin_is_allowed():
    m_admin = _member(user_id=42, guild_owner_id=99)
    session = _session(owner_id=99, delegated=(42,))
    assert setup_access.can_apply_setup(m_admin, session) is True


def test_can_apply_setup_random_member_is_denied():
    m = _member(user_id=42, guild_owner_id=99)
    session = _session(owner_id=99)
    assert setup_access.can_apply_setup(m, session) is False


# ---------------------------------------------------------------------------
# Raw-id variants
# ---------------------------------------------------------------------------


def test_is_server_owner_by_id_matches_owner_id():
    assert setup_access.is_server_owner_by_id(99, 99) is True
    assert setup_access.is_server_owner_by_id(42, 99) is False


def test_can_apply_setup_by_id_accepts_owner():
    assert setup_access.can_apply_setup_by_id(99, 99) is True


def test_can_apply_setup_by_id_accepts_delegated():
    assert (
        setup_access.can_apply_setup_by_id(42, 99, delegated_admins=(42,)) is True
    )


def test_can_apply_setup_by_id_denies_random():
    assert (
        setup_access.can_apply_setup_by_id(42, 99, delegated_admins=()) is False
    )

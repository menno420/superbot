"""Authority tests for the declared-tier read path (Q-0045, option b).

``governance.resolver._resolve_member_tier`` prefers an explicitly declared
``GovernanceContext.member_tier`` verbatim — the read-only audience-simulation
input Help Preview and the ``help_advertises_locked`` drift baseline use to ask
"what does a member of tier X see?" without a real ``discord.Member``.  These
tests pin the security-critical properties of that path:

* **declared wins** — a declared tier is returned verbatim, with or without a
  member, and is never re-derived from permissions;
* **grants skipped** — the configured-role grant readers are not consulted
  (the caller declared the *effective* standing, and a simulated read must not
  depend on live config reads);
* **invalid is ignored, never escalates** — a value outside
  ``VISIBILITY_TIERS`` is ignored and resolution proceeds as if unset
  (member-less contexts floor at ``"user"``; a real member keeps their
  derived tier);
* **end-to-end** — ``resolve_visibility`` with a declared tier filters
  subsystems exactly as a real member of that tier would, and reports the
  declared tier back (one source of truth: same resolver, same cache).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import core.runtime.config_arbitration as cfg
from governance.models import GovernanceContext
from governance.resolver import _resolve_member_tier, resolve_visibility

GUILD_ID = 100
OWNER_ID = 999
MOD_ROLE_ID = 555


def _member(*, administrator: bool = False) -> SimpleNamespace:
    perms = SimpleNamespace(
        administrator=administrator,
        moderate_members=False,
        manage_guild=False,
    )
    return SimpleNamespace(
        id=1,
        guild_permissions=perms,
        guild=SimpleNamespace(owner_id=OWNER_ID),
    )


def _recording_reader(calls: list, value=None):
    """A config getter that records being consulted."""

    async def _read(guild_id: int):
        calls.append(guild_id)
        return SimpleNamespace(value=value)

    return _read


# ---------------------------------------------------------------------------
# Declared tier is preferred verbatim
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_declared_tier_without_member_is_returned_verbatim():
    ctx = GovernanceContext(guild_id=GUILD_ID, member=None, member_tier="staff")
    assert await _resolve_member_tier(ctx) == "staff"


@pytest.mark.asyncio
async def test_declared_tier_wins_over_member_derivation():
    # An administrator simulated as "user" resolves to "user" — the declared
    # tier is the effective standing, not a hint.
    ctx = GovernanceContext(
        guild_id=GUILD_ID,
        member=_member(administrator=True),
        member_tier="user",
    )
    assert await _resolve_member_tier(ctx) == "user"


@pytest.mark.asyncio
async def test_every_known_tier_round_trips():
    from utils.visibility_rules import VISIBILITY_TIERS

    for tier in VISIBILITY_TIERS:
        ctx = GovernanceContext(guild_id=GUILD_ID, member=None, member_tier=tier)
        assert await _resolve_member_tier(ctx) == tier


# ---------------------------------------------------------------------------
# Configured-role grants are skipped on the declared path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_declared_tier_skips_role_grant_reads(monkeypatch):
    calls: list[int] = []
    monkeypatch.setattr(
        cfg,
        "get_moderator_tier_role",
        _recording_reader(calls, MOD_ROLE_ID),
    )
    monkeypatch.setattr(
        cfg,
        "get_trusted_tier_role",
        _recording_reader(calls, MOD_ROLE_ID),
    )
    # role_ids hold the configured moderator role, but the declared tier is
    # the effective standing — no grant read happens, no promotion occurs.
    ctx = GovernanceContext(
        guild_id=GUILD_ID,
        member=None,
        role_ids={MOD_ROLE_ID},
        member_tier="user",
    )
    assert await _resolve_member_tier(ctx) == "user"
    assert calls == []


# ---------------------------------------------------------------------------
# Invalid declared tier — ignored, never escalates or demotes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_declared_tier_floors_at_user_without_member():
    ctx = GovernanceContext(guild_id=GUILD_ID, member=None, member_tier="superadmin")
    assert await _resolve_member_tier(ctx) == "user"


@pytest.mark.asyncio
async def test_invalid_declared_tier_keeps_real_member_tier():
    # Garbage input is ignored entirely: a real administrator stays an
    # administrator (the declared path can neither escalate nor demote on a
    # bad value).
    ctx = GovernanceContext(
        guild_id=GUILD_ID,
        member=_member(administrator=True),
        member_tier="not-a-tier",
    )
    assert await _resolve_member_tier(ctx) == "administrator"


# ---------------------------------------------------------------------------
# End-to-end: resolve_visibility under a declared tier
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_visibility_filters_by_declared_tier(mock_db):
    # Baseline audience: a user-tier subsystem is visible, an
    # administrator-tier subsystem is not.
    base = await resolve_visibility(
        GovernanceContext(
            guild_id=GUILD_ID,
            channel_id=200,
            member=None,
            member_tier="user",
        ),
    )
    assert base.member_tier == "user"
    assert "economy" in base.visible_subsystems
    assert "server_management" not in base.visible_subsystems

    # The same context declared at administrator tier sees it.
    admin = await resolve_visibility(
        GovernanceContext(
            guild_id=GUILD_ID,
            channel_id=200,
            member=None,
            member_tier="administrator",
        ),
    )
    assert admin.member_tier == "administrator"
    assert "server_management" in admin.visible_subsystems


@pytest.mark.asyncio
async def test_declared_tier_matches_real_member_resolution(mock_db):
    """One source of truth: a declared tier and a real member resolving to the
    same tier produce the same visible set (the Q-0045 option-b promise)."""
    declared = await resolve_visibility(
        GovernanceContext(
            guild_id=GUILD_ID,
            channel_id=200,
            member=None,
            member_tier="user",
        ),
    )
    real = await resolve_visibility(
        GovernanceContext(
            guild_id=GUILD_ID,
            channel_id=200,
            member=_member(),  # no permissions → derives "user"
        ),
    )
    assert declared.visible_subsystems == real.visible_subsystems
    assert declared.member_tier == real.member_tier == "user"

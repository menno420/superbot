"""Unit tests for governance.capability — the ADR-005 A1 authority resolver.

Pins the v1 policy: system/backfill bypass, non-member deny, administrator floor
keyed on the declared capability (empty == admin floor, NOT "no auth"), and the
revoke-only per-guild overlay (an explicit disable denies; an explicit enable
never escalates a below-floor actor).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from governance import capability as cap_mod
from governance.capability import actor_holds_capability

_CAP = "xp.settings.configure"


class _FakeGuild:
    def __init__(self, guild_id: int = 1, owner_id: int = 0):
        self.id = guild_id
        self.owner_id = owner_id


class _FakePerms:
    def __init__(self, *, administrator: bool = False, manage_guild: bool = False):
        self.administrator = administrator
        self.moderate_members = False
        self.manage_guild = manage_guild


class _FakeMember:
    def __init__(self, member_id: int = 7, *, guild: _FakeGuild, tier: str = "user"):
        self.id = member_id
        self.guild = guild
        perms = _FakePerms()
        if tier == "administrator":
            perms.administrator = True
        elif tier == "staff":
            perms.manage_guild = True
        self.guild_permissions = perms


@pytest.fixture(autouse=True)
def _no_overlay(monkeypatch):
    """Default: no per-guild override so tests see the pure admin-floor path."""
    monkeypatch.setattr(
        "governance.execution.get_capability_override",
        AsyncMock(return_value=None),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("actor_type", ["system", "backfill"])
async def test_system_and_backfill_bypass(actor_type):
    decision = await actor_holds_capability(None, None, _CAP, actor_type=actor_type)
    assert decision.allowed is True
    assert decision.member_tier is None


@pytest.mark.asyncio
async def test_none_actor_denied():
    decision = await actor_holds_capability(None, None, _CAP)
    assert decision.allowed is False
    assert "guild-member" in decision.reason


@pytest.mark.asyncio
async def test_admin_allowed_for_declared_capability():
    guild = _FakeGuild()
    actor = _FakeMember(guild=guild, tier="administrator")
    decision = await actor_holds_capability(actor, guild, _CAP)
    assert decision.allowed is True
    assert decision.member_tier == "administrator"


@pytest.mark.asyncio
async def test_staff_denied_for_declared_capability():
    guild = _FakeGuild()
    actor = _FakeMember(guild=guild, tier="staff")
    decision = await actor_holds_capability(actor, guild, _CAP)
    assert decision.allowed is False
    assert "administrator" in decision.reason


@pytest.mark.asyncio
async def test_empty_capability_uses_admin_floor():
    guild = _FakeGuild()
    admin = _FakeMember(guild=guild, tier="administrator")
    staff = _FakeMember(guild=guild, tier="staff")
    assert (await actor_holds_capability(admin, guild, "")).allowed is True
    assert (await actor_holds_capability(staff, guild, "")).allowed is False


@pytest.mark.asyncio
async def test_revoke_overlay_denies_otherwise_allowed_admin(monkeypatch):
    monkeypatch.setattr(
        "governance.execution.get_capability_override",
        AsyncMock(return_value=False),
    )
    guild = _FakeGuild()
    admin = _FakeMember(guild=guild, tier="administrator")
    decision = await actor_holds_capability(admin, guild, _CAP)
    assert decision.allowed is False


@pytest.mark.asyncio
async def test_overlay_true_does_not_escalate_below_floor(monkeypatch):
    monkeypatch.setattr(
        "governance.execution.get_capability_override",
        AsyncMock(return_value=True),
    )
    guild = _FakeGuild()
    staff = _FakeMember(guild=guild, tier="staff")
    decision = await actor_holds_capability(staff, guild, _CAP)
    # An explicit enable must never grant a below-floor actor.
    assert decision.allowed is False


@pytest.mark.asyncio
async def test_overlay_not_consulted_for_empty_capability(monkeypatch):
    spy = AsyncMock(return_value=False)
    monkeypatch.setattr("governance.execution.get_capability_override", spy)
    guild = _FakeGuild()
    admin = _FakeMember(guild=guild, tier="administrator")
    decision = await actor_holds_capability(admin, guild, "")
    assert decision.allowed is True
    spy.assert_not_awaited()


@pytest.mark.asyncio
async def test_overlay_read_failure_is_ignored(monkeypatch):
    monkeypatch.setattr(
        "governance.execution.get_capability_override",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    guild = _FakeGuild()
    admin = _FakeMember(guild=guild, tier="administrator")
    decision = await actor_holds_capability(admin, guild, _CAP)
    # An overlay read failure degrades to the base (admin-floor) decision.
    assert decision.allowed is True


def test_default_required_tier_is_administrator():
    # Pins the v1 floor so a future change to a capability->tier matrix is a
    # deliberate, reviewed edit.
    assert cap_mod._DEFAULT_REQUIRED_TIER == "administrator"


@pytest.mark.asyncio
async def test_cross_guild_actor_denied():
    # An admin in guild 1 must NOT be able to authorize a write to guild 2.
    actor = _FakeMember(guild=_FakeGuild(1), tier="administrator")
    target = _FakeGuild(2)
    decision = await actor_holds_capability(actor, target, _CAP)
    assert decision.allowed is False
    assert "target guild" in decision.reason


@pytest.mark.asyncio
async def test_overlay_uses_target_guild_id(monkeypatch):
    # The per-guild revoke overlay is looked up with the TARGET guild's id.
    seen: dict = {}

    async def _spy(guild_id, capability):
        seen["guild_id"] = guild_id
        return None

    monkeypatch.setattr("governance.execution.get_capability_override", _spy)
    guild = _FakeGuild(4242)
    actor = _FakeMember(guild=guild, tier="administrator")
    await actor_holds_capability(actor, guild, _CAP)
    assert seen.get("guild_id") == 4242


# ---------------------------------------------------------------------------
# Q-0098 — Setup-delegate apply authority.
#
# A below-floor (non-administrator) member the server owner delegated apply
# authority to is authorized when, and only when, the write carries
# actor_type="setup_delegate" — which only setup_operations.apply_operations
# mints (re-verifying the live delegation first). Unlike system/backfill it is
# NOT a blind short-circuit: target-guild membership and the revoke overlay
# still apply.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_delegate_authorized_below_floor():
    guild = _FakeGuild()
    # A plain member (below the administrator floor) — denied as a normal user,
    # allowed as a setup_delegate.
    actor = _FakeMember(guild=guild, tier="user")
    assert (await actor_holds_capability(actor, guild, _CAP)).allowed is False
    decision = await actor_holds_capability(
        actor, guild, _CAP, actor_type="setup_delegate"
    )
    assert decision.allowed is True
    assert "delegated setup admin" in decision.reason


@pytest.mark.asyncio
async def test_setup_delegate_still_requires_target_guild_membership():
    # A delegate flag from a member of a DIFFERENT guild is still denied at the
    # membership step — the bypass is not a step-1 short-circuit.
    actor = _FakeMember(guild=_FakeGuild(1), tier="user")
    target = _FakeGuild(2)
    decision = await actor_holds_capability(
        actor, target, _CAP, actor_type="setup_delegate"
    )
    assert decision.allowed is False
    assert "target guild" in decision.reason


@pytest.mark.asyncio
async def test_setup_delegate_subject_to_revoke_overlay(monkeypatch):
    # An explicit per-guild capability disable flips a delegate OFF, same as any
    # actor — the owner can revoke a capability from a delegate.
    monkeypatch.setattr(
        "governance.execution.get_capability_override",
        AsyncMock(return_value=False),
    )
    guild = _FakeGuild()
    actor = _FakeMember(guild=guild, tier="user")
    decision = await actor_holds_capability(
        actor, guild, _CAP, actor_type="setup_delegate"
    )
    assert decision.allowed is False
    assert "REVOKED" in decision.reason

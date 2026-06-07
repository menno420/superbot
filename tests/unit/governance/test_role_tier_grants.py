"""Authority tests for the configured-role tier grants (ADR-008).

``governance.resolver._resolve_member_tier`` promotes a member to the
``moderator`` (or ``trusted``) tier when the guild has the matching role
configured and the member holds it.  These tests pin the security-critical
properties of that grant:

* **grant via role** — a permission-less member with the configured moderator
  role resolves to ``moderator``;
* **no escalation** — the grant only *raises* a tier (never demotes a real
  admin/owner) and a failed config read grants nothing;
* **precedence** — the moderator grant wins over the trusted grant;
* **cross-guild deny** — the role configured for one guild does not grant the
  tier in another;
* **no regression** — a member with real Discord permissions is unaffected.

The moderation surfaces gate on this tier via ``resolve_execution`` (the
moderation subsystem's ``visibility_tier`` is ``"moderator"``), so a correct
tier here is the whole authority story for the role grant.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import core.runtime.config_arbitration as cfg
from governance.resolver import _resolve_member_tier, _role_grants_tier
from services.governance_service import GovernanceContext

MOD_ROLE_ID = 555
TRUSTED_ROLE_ID = 444
GUILD_ID = 100
OWNER_ID = 999


def _member(
    *,
    member_id: int = 1,
    administrator: bool = False,
    moderate_members: bool = False,
    manage_guild: bool = False,
) -> SimpleNamespace:
    """A fake Discord member with just the attributes the tier resolver reads."""
    perms = SimpleNamespace(
        administrator=administrator,
        moderate_members=moderate_members,
        manage_guild=manage_guild,
    )
    return SimpleNamespace(
        id=member_id,
        guild_permissions=perms,
        guild=SimpleNamespace(owner_id=OWNER_ID),
    )


def _ctx(member: SimpleNamespace | None, role_ids: set[int]) -> GovernanceContext:
    return GovernanceContext(guild_id=GUILD_ID, member=member, role_ids=role_ids)


def _reader(value):
    """Build a fake config getter returning a ConfigReadResult-shaped object."""

    async def _read(_guild_id: int):
        return SimpleNamespace(value=value)

    return _read


@pytest.fixture
def _no_roles_configured(monkeypatch):
    """Default: neither role is configured (both readers return value=None)."""
    monkeypatch.setattr(cfg, "get_moderator_tier_role", _reader(None))
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _reader(None))


# ---------------------------------------------------------------------------
# Grant via role
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moderator_role_grants_moderator_tier(monkeypatch):
    monkeypatch.setattr(cfg, "get_moderator_tier_role", _reader(MOD_ROLE_ID))
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _reader(None))
    # A plain member (no mod permissions) who holds the configured moderator role.
    tier = await _resolve_member_tier(_ctx(_member(), {MOD_ROLE_ID}))
    assert tier == "moderator"


@pytest.mark.asyncio
async def test_staff_member_promoted_to_moderator_by_role(monkeypatch):
    monkeypatch.setattr(cfg, "get_moderator_tier_role", _reader(MOD_ROLE_ID))
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _reader(None))
    # manage_guild → base "staff"; the moderator role raises them to "moderator".
    tier = await _resolve_member_tier(
        _ctx(_member(manage_guild=True), {MOD_ROLE_ID}),
    )
    assert tier == "moderator"


@pytest.mark.asyncio
async def test_trusted_role_grants_trusted_tier(monkeypatch):
    monkeypatch.setattr(cfg, "get_moderator_tier_role", _reader(None))
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _reader(TRUSTED_ROLE_ID))
    tier = await _resolve_member_tier(_ctx(_member(), {TRUSTED_ROLE_ID}))
    assert tier == "trusted"


# ---------------------------------------------------------------------------
# No escalation / only-raises
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moderator_role_does_not_demote_administrator(monkeypatch):
    monkeypatch.setattr(cfg, "get_moderator_tier_role", _reader(MOD_ROLE_ID))
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _reader(None))
    # An administrator who also holds the moderator role stays "administrator".
    tier = await _resolve_member_tier(
        _ctx(_member(administrator=True), {MOD_ROLE_ID}),
    )
    assert tier == "administrator"


@pytest.mark.asyncio
async def test_moderator_grant_takes_precedence_over_trusted(monkeypatch):
    monkeypatch.setattr(cfg, "get_moderator_tier_role", _reader(MOD_ROLE_ID))
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _reader(TRUSTED_ROLE_ID))
    # Holding both configured roles resolves to the higher tier.
    tier = await _resolve_member_tier(
        _ctx(_member(), {MOD_ROLE_ID, TRUSTED_ROLE_ID}),
    )
    assert tier == "moderator"


@pytest.mark.asyncio
async def test_member_without_the_role_is_not_granted(monkeypatch):
    monkeypatch.setattr(cfg, "get_moderator_tier_role", _reader(MOD_ROLE_ID))
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _reader(None))
    # Configured role exists, but the member holds a different role.
    tier = await _resolve_member_tier(_ctx(_member(), {12345}))
    assert tier == "user"


@pytest.mark.asyncio
async def test_no_role_configured_stays_user(_no_roles_configured):
    tier = await _resolve_member_tier(_ctx(_member(), {MOD_ROLE_ID, TRUSTED_ROLE_ID}))
    assert tier == "user"


@pytest.mark.asyncio
async def test_failed_read_grants_nothing(monkeypatch):
    async def _boom(_guild_id: int):
        raise RuntimeError("config store down")

    monkeypatch.setattr(cfg, "get_moderator_tier_role", _boom)
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _boom)
    # A read failure must fail toward the LOWER tier — never grant on error.
    tier = await _resolve_member_tier(_ctx(_member(), {MOD_ROLE_ID}))
    assert tier == "user"


# ---------------------------------------------------------------------------
# Cross-guild deny
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_role_configured_for_another_guild_does_not_grant(monkeypatch):
    # The reader returns the moderator role only for GUILD_ID; any other guild
    # gets None — modelling per-guild config.  The member here is in GUILD_ID
    # but we resolve a context for a *different* guild.
    async def _per_guild_reader(guild_id: int):
        return SimpleNamespace(value=MOD_ROLE_ID if guild_id == GUILD_ID else None)

    monkeypatch.setattr(cfg, "get_moderator_tier_role", _per_guild_reader)
    monkeypatch.setattr(cfg, "get_trusted_tier_role", _reader(None))

    other_guild_ctx = GovernanceContext(
        guild_id=GUILD_ID + 1,
        member=_member(),
        role_ids={MOD_ROLE_ID},
    )
    tier = await _resolve_member_tier(other_guild_ctx)
    assert tier == "user"


# ---------------------------------------------------------------------------
# No regression — real Discord permissions are unaffected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_moderate_members_permission_unaffected_by_config(_no_roles_configured):
    # moderate_members → "moderator" with no role configured at all.
    tier = await _resolve_member_tier(_ctx(_member(moderate_members=True), set()))
    assert tier == "moderator"


@pytest.mark.asyncio
async def test_member_none_returns_user(_no_roles_configured):
    tier = await _resolve_member_tier(_ctx(None, {MOD_ROLE_ID}))
    assert tier == "user"


# ---------------------------------------------------------------------------
# _role_grants_tier helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_role_grants_tier_matches_when_held():
    assert await _role_grants_tier(GUILD_ID, _reader(MOD_ROLE_ID), {MOD_ROLE_ID}) is True


@pytest.mark.asyncio
async def test_role_grants_tier_false_when_not_held():
    assert await _role_grants_tier(GUILD_ID, _reader(MOD_ROLE_ID), {7}) is False


@pytest.mark.asyncio
async def test_role_grants_tier_false_when_unset():
    assert await _role_grants_tier(GUILD_ID, _reader(None), {MOD_ROLE_ID}) is False


@pytest.mark.asyncio
async def test_role_grants_tier_false_when_no_role_ids():
    assert await _role_grants_tier(GUILD_ID, _reader(MOD_ROLE_ID), set()) is False


@pytest.mark.asyncio
async def test_role_grants_tier_false_on_read_error():
    async def _boom(_guild_id: int):
        raise RuntimeError("db down")

    assert await _role_grants_tier(GUILD_ID, _boom, {MOD_ROLE_ID}) is False

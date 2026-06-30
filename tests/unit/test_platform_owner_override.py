"""Bot-owner (platform-owner) full-config-authority override.

The configured bot owner (``config.BOT_OWNER_USER_ID``, the
``PermissionTier.PLATFORM_OWNER`` deploy allowlist) holds full
bot-*configuration* authority in any guild they are a member of, even without
Discord permissions there, so they can always set the bot up correctly.

These tests pin that override at every authority seam it was wired into, and
confirm the single-source helper :func:`config.is_platform_owner` is the only
thing each seam keys on.  Every check is **additive** — it only ever GRANTS the
configured owner; a non-owner sees exactly the pre-existing behaviour.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

import config

OWNER_ID = 555_000_111
OTHER_ID = 42

_CAP = "xp.settings.configure"


@pytest.fixture(autouse=True)
def _owner_configured(monkeypatch):
    """Default every test to a known configured platform owner id."""
    monkeypatch.setattr(config, "BOT_OWNER_USER_ID", OWNER_ID)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


def _perms(*, administrator=False, manage_guild=False, moderate_members=False):
    return SimpleNamespace(
        administrator=administrator,
        manage_guild=manage_guild,
        moderate_members=moderate_members,
    )


def _guild(guild_id=1, owner_id=999):
    return SimpleNamespace(id=guild_id, owner_id=owner_id)


def _member(user_id, *, guild=None, **perm_kwargs):
    g = guild if guild is not None else _guild()
    return SimpleNamespace(id=user_id, guild=g, guild_permissions=_perms(**perm_kwargs))


# ---------------------------------------------------------------------------
# config.is_platform_owner — the single source of truth
# ---------------------------------------------------------------------------


def test_is_platform_owner_matches_configured_id():
    assert config.is_platform_owner(OWNER_ID) is True


def test_is_platform_owner_rejects_other_id():
    assert config.is_platform_owner(OTHER_ID) is False


def test_is_platform_owner_rejects_none():
    assert config.is_platform_owner(None) is False


def test_is_platform_owner_false_when_unconfigured(monkeypatch):
    # An unconfigured deployment (no owner id) must grant no one.
    monkeypatch.setattr(config, "BOT_OWNER_USER_ID", None)
    assert config.is_platform_owner(OWNER_ID) is False
    assert config.is_platform_owner(None) is False


# ---------------------------------------------------------------------------
# governance.capability.actor_holds_capability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_capability_owner_allowed_as_plain_member():
    from governance.capability import actor_holds_capability

    guild = _guild(1)
    # A plain member (no Discord perms) who happens to be the bot owner.
    actor = _member(OWNER_ID, guild=guild)
    decision = await actor_holds_capability(actor, guild, _CAP)
    assert decision.allowed is True
    assert decision.member_tier == "owner"
    assert "platform owner" in decision.reason


@pytest.mark.asyncio
async def test_capability_non_owner_plain_member_still_denied():
    from governance.capability import actor_holds_capability

    guild = _guild(1)
    actor = _member(OTHER_ID, guild=guild)
    decision = await actor_holds_capability(actor, guild, _CAP)
    assert decision.allowed is False


@pytest.mark.asyncio
async def test_capability_owner_still_requires_target_guild_membership():
    # The override sits AFTER the membership check, so it cannot authorize a
    # write to a guild the owner is not a member of (cross-guild invariant).
    from governance.capability import actor_holds_capability

    actor = _member(OWNER_ID, guild=_guild(1))
    target = _guild(2)
    decision = await actor_holds_capability(actor, target, _CAP)
    assert decision.allowed is False
    assert "target guild" in decision.reason


@pytest.mark.asyncio
async def test_capability_revoke_overlay_cannot_revoke_owner(monkeypatch):
    # A guild's explicit per-capability disable flips a normal admin OFF, but
    # must NOT be able to revoke the platform owner (owner short-circuits before
    # the overlay is even read).
    from unittest.mock import AsyncMock

    from governance.capability import actor_holds_capability

    spy = AsyncMock(return_value=False)
    monkeypatch.setattr("governance.execution.get_capability_override", spy)
    guild = _guild(1)
    decision = await actor_holds_capability(_member(OWNER_ID, guild=guild), guild, _CAP)
    assert decision.allowed is True
    spy.assert_not_awaited()


# ---------------------------------------------------------------------------
# governance.resolver._resolve_member_tier (visibility + execution)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolver_owner_elevated_to_owner_tier():
    from governance.resolver import _resolve_member_tier

    ctx = SimpleNamespace(
        member_tier=None,
        member=_member(OWNER_ID, guild=_guild(owner_id=999)),
        guild_id=1,
        role_ids=None,
    )
    assert await _resolve_member_tier(ctx) == "owner"


@pytest.mark.asyncio
async def test_resolver_non_owner_user_stays_user():
    from governance.resolver import _resolve_member_tier

    ctx = SimpleNamespace(
        member_tier=None,
        member=_member(OTHER_ID, guild=_guild(owner_id=999)),
        guild_id=1,
        role_ids=None,
    )
    assert await _resolve_member_tier(ctx) == "user"


@pytest.mark.asyncio
async def test_resolver_simulation_tier_not_overridden_for_owner():
    # Audience-simulation (declared member_tier, e.g. Help Preview) must show the
    # declared tier even for the bot owner — the override only elevates the REAL
    # resolution path.
    from governance.resolver import _resolve_member_tier

    ctx = SimpleNamespace(
        member_tier="user",
        member=_member(OWNER_ID, guild=_guild(owner_id=999)),
        guild_id=1,
        role_ids=None,
    )
    assert await _resolve_member_tier(ctx) == "user"


# ---------------------------------------------------------------------------
# governance.writes._validate_authority (governance writes)
# ---------------------------------------------------------------------------


def test_writes_owner_passes_authority():
    from governance.writes import _validate_authority

    ctx = SimpleNamespace(member=_member(OWNER_ID, guild=_guild(owner_id=999)))
    # No raise == authorized.
    _validate_authority(ctx)


def test_writes_non_owner_non_mod_denied():
    from utils.governance_exceptions import UnauthorizedGovernanceWriteError

    from governance.writes import _validate_authority

    ctx = SimpleNamespace(member=_member(OTHER_ID, guild=_guild(owner_id=999)))
    with pytest.raises(UnauthorizedGovernanceWriteError):
        _validate_authority(ctx)


# ---------------------------------------------------------------------------
# services *_mutation._check_admin (AI policy / instruction / orchestration,
# btd6 source, help overlay) — all five share the owner-aware gate.
# ---------------------------------------------------------------------------

_CHECK_ADMIN_SEAMS = [
    ("services.ai_policy_mutation", "UnauthorizedAIPolicyMutationError"),
    ("services.ai_instruction_mutation", "UnauthorizedAIInstructionMutationError"),
    ("services.ai_orchestration_mutation", "UnauthorizedAIOrchestrationMutationError"),
    ("services.btd6_source_mutation", "UnauthorizedSourceMutationError"),
    ("services.help_overlay_mutation", "UnauthorizedHelpOverlayMutationError"),
]


@pytest.mark.parametrize(("module_name", "exc_name"), _CHECK_ADMIN_SEAMS)
def test_check_admin_owner_allowed_without_admin_perm(module_name, exc_name):
    mod = importlib.import_module(module_name)
    actor = _member(OWNER_ID)  # no administrator perm
    assert mod._check_admin(actor) == OWNER_ID


@pytest.mark.parametrize(("module_name", "exc_name"), _CHECK_ADMIN_SEAMS)
def test_check_admin_non_owner_non_admin_denied(module_name, exc_name):
    mod = importlib.import_module(module_name)
    exc = getattr(mod, exc_name)
    actor = _member(OTHER_ID)  # not owner, no administrator perm
    with pytest.raises(exc):
        mod._check_admin(actor)


@pytest.mark.parametrize(("module_name", "exc_name"), _CHECK_ADMIN_SEAMS)
def test_check_admin_admin_still_allowed(module_name, exc_name):
    mod = importlib.import_module(module_name)
    actor = _member(OTHER_ID, administrator=True)
    assert mod._check_admin(actor) == OTHER_ID


# ---------------------------------------------------------------------------
# services.setup_access — owner can view/run/apply setup in any guild
# ---------------------------------------------------------------------------


def test_setup_access_owner_is_setup_admin_as_plain_member():
    from services import setup_access

    # Owner is neither guild owner (owner_id=999) nor administrator.
    m = _member(OWNER_ID, guild=_guild(owner_id=999))
    assert setup_access.is_setup_admin(m, session=None) is True
    assert setup_access.can_view_setup(m, session=None) is True
    assert setup_access.can_run_readiness(m, session=None) is True


def test_setup_access_owner_can_apply_setup_as_plain_member():
    from services import setup_access

    m = _member(OWNER_ID, guild=_guild(owner_id=999))
    assert setup_access.can_apply_setup(m, session=None) is True


def test_setup_access_owner_can_apply_setup_by_id():
    from services import setup_access

    # guild_owner_id is someone else; no delegation — owner still applies.
    assert setup_access.can_apply_setup_by_id(OWNER_ID, 999, ()) is True


def test_setup_access_non_owner_plain_member_denied():
    from services import setup_access

    m = _member(OTHER_ID, guild=_guild(owner_id=999))
    assert setup_access.can_apply_setup(m, session=None) is False
    assert setup_access.can_apply_setup_by_id(OTHER_ID, 999, ()) is False


# ---------------------------------------------------------------------------
# views.base — canonical admin gates honour the owner
# ---------------------------------------------------------------------------


def test_view_interaction_is_admin_owner_without_perms():
    from views.base import interaction_is_admin

    interaction = SimpleNamespace(user=_member(OWNER_ID))
    assert interaction_is_admin(interaction) is True


def test_view_interaction_is_admin_non_owner_non_admin_false():
    from views.base import interaction_is_admin

    interaction = SimpleNamespace(user=_member(OTHER_ID))
    assert interaction_is_admin(interaction) is False


def test_view_member_is_admin_owner_without_perms():
    from views.base import member_is_admin

    assert member_is_admin(_member(OWNER_ID)) is True


def test_view_member_is_admin_admin_still_true():
    from views.base import member_is_admin

    assert member_is_admin(_member(OTHER_ID, administrator=True)) is True


def test_view_member_is_admin_plain_member_false():
    from views.base import member_is_admin

    assert member_is_admin(_member(OTHER_ID)) is False

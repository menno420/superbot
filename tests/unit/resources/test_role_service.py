"""Phase 2a unit tests — role_service operations + template matching."""

from __future__ import annotations

from unittest.mock import MagicMock

import discord
import pytest
from tests.unit.resources.test_discovery import _mk_guild, _mk_role

from core.resources import role_service
from core.resources.types import RoleResource
from governance.permission_tiers import PermissionTier
from governance.role_templates import (
    HELPER_TEMPLATE,
    MODERATOR_TEMPLATE,
)
from governance.scopes import GovernanceScope


def _mk_role_with_perms(role_id: int, name: str, *, perm_names: tuple[str, ...] = ()):
    """Build a Role mock whose .permissions.<name> attrs are True for names in perm_names."""
    role = _mk_role(role_id, name)
    perms = MagicMock(spec=discord.Permissions)
    perms.value = sum(1 << i for i, _ in enumerate(perm_names))
    for attr in (
        "manage_messages",
        "kick_members",
        "moderate_members",
        "view_audit_log",
        "administrator",
        "ban_members",
    ):
        setattr(perms, attr, attr in perm_names)
    role.permissions = perms
    return role


def test_filter_roles_excludes_everyone_automatically():
    everyone = _mk_role(0, "@everyone", is_default=True)
    mod = _mk_role(42, "Mod")
    guild = _mk_guild(roles=[everyone, mod])
    result = role_service.filter_roles(guild, lambda r: True)
    assert len(result) == 1
    assert result[0].id == 42


def test_get_role_present():
    role = _mk_role(42, "Mod")
    guild = _mk_guild(roles=[role])
    found = role_service.get_role(guild, 42)
    assert isinstance(found, RoleResource)
    assert found.id == 42


def test_get_role_missing():
    guild = _mk_guild()
    assert role_service.get_role(guild, 42) is None


def test_resolve_scope_returns_role():
    role = _mk_role(42, "Mod")
    snap = role_service.role_to_snapshot(role)
    assert role_service.resolve_scope(snap) is GovernanceScope.ROLE


def test_has_permission_true():
    role = _mk_role_with_perms(42, "Mod", perm_names=("manage_messages",))
    assert role_service.has_permission(role, "manage_messages") is True


def test_has_permission_false_and_unknown_name():
    role = _mk_role_with_perms(42, "Mod", perm_names=())
    assert role_service.has_permission(role, "manage_messages") is False
    # Unknown attribute returns False (no AttributeError)
    assert role_service.has_permission(role, "not_a_real_permission") is False


# ---------------------------------------------------------------------------
# Template matching
# ---------------------------------------------------------------------------


def test_match_role_template_exact_name_with_no_perms_meets_threshold():
    """Exact normalized name yields score 1.0 alone (>= default 0.5)."""
    role = _mk_role_with_perms(42, "Moderator", perm_names=())
    match = role_service.match_role_template(role)
    assert match is not None
    template, score = match
    assert template.name == MODERATOR_TEMPLATE.name
    assert score >= 0.5


def test_match_role_template_full_match():
    role = _mk_role_with_perms(
        42,
        "Moderator",
        perm_names=(
            "manage_messages",
            "kick_members",
            "moderate_members",
            "view_audit_log",
        ),
    )
    match = role_service.match_role_template(role)
    assert match is not None
    template, score = match
    assert template.name == MODERATOR_TEMPLATE.name
    # Full name match (1.0) + full perm overlap (1.0) = 2.0
    assert score == pytest.approx(2.0)


def test_match_role_template_below_threshold_returns_none():
    role = _mk_role_with_perms(42, "RandomGameRole", perm_names=())
    assert role_service.match_role_template(role, min_score=0.5) is None


def test_match_role_template_substring_match_counts():
    role = _mk_role_with_perms(42, "Senior Moderator", perm_names=())
    match = role_service.match_role_template(role, min_score=0.5)
    assert match is not None
    template, score = match
    assert template.name == MODERATOR_TEMPLATE.name
    assert 0.5 <= score < 1.5


def test_list_roles_by_tier_moderator():
    """A role matching the Moderator template is reported under MODERATOR tier."""
    mod = _mk_role_with_perms(42, "Moderator", perm_names=("manage_messages",))
    everyone = _mk_role(0, "@everyone", is_default=True)
    guild = _mk_guild(roles=[everyone, mod])
    result = role_service.list_roles_by_tier(guild, PermissionTier.MODERATOR)
    assert len(result) == 1
    assert result[0].id == 42


def test_list_roles_by_tier_staff_via_helper_template():
    helper = _mk_role_with_perms(42, "Helper", perm_names=())
    guild = _mk_guild(roles=[helper])
    result = role_service.list_roles_by_tier(guild, PermissionTier.STAFF)
    assert len(result) == 1
    assert result[0].id == 42
    # And the helper template indeed maps to STAFF tier.
    assert HELPER_TEMPLATE.permission_tier is PermissionTier.STAFF


def test_list_roles_by_tier_excludes_everyone():
    everyone = _mk_role(0, "@everyone", is_default=True)
    guild = _mk_guild(roles=[everyone])
    assert role_service.list_roles_by_tier(guild, PermissionTier.MODERATOR) == []

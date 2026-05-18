"""Phase 1d unit tests — governance taxonomy declarations.

Verifies :mod:`governance.scopes`, :mod:`governance.permission_tiers`,
and :mod:`governance.role_templates`.
"""

from __future__ import annotations

import pytest

from governance.permission_tiers import (
    PermissionTier,
    all_tiers_ordered,
    metadata_for,
    tier_at_or_above,
    tier_index,
)
from governance.role_templates import (
    ADMINISTRATION_ROLES,
    MODERATION_ROLES,
    TRUSTED_USER_TIERS,
    RoleTemplate,
    all_collections,
    all_templates,
    get_template,
)
from governance.scopes import LEGACY_SCOPE_TYPES, GovernanceScope, from_string


def test_governance_scope_legacy_strings():
    """Enum values must match the legacy ``_VALID_SCOPE_TYPES`` strings."""
    assert {"guild", "category", "channel", "thread"} <= LEGACY_SCOPE_TYPES


def test_governance_scope_from_string_round_trip():
    for s in GovernanceScope:
        assert from_string(s.value) is s


def test_governance_scope_from_string_invalid():
    with pytest.raises(ValueError, match="unknown governance scope"):
        from_string("not_a_scope")


def test_permission_tier_ordering():
    assert tier_index(PermissionTier.USER) == 0
    assert tier_index(PermissionTier.MODERATOR) > tier_index(PermissionTier.STAFF)
    assert tier_index(PermissionTier.OWNER) > tier_index(PermissionTier.ADMINISTRATOR)
    assert tier_index(PermissionTier.PLATFORM_OWNER) > tier_index(
        PermissionTier.OWNER,
    )


def test_permission_tier_string_lookup():
    assert tier_index("user") == 0
    assert tier_index("moderator") == 3


def test_permission_tier_at_or_above():
    assert tier_at_or_above(PermissionTier.ADMINISTRATOR, PermissionTier.MODERATOR)
    assert not tier_at_or_above(PermissionTier.STAFF, PermissionTier.MODERATOR)
    assert tier_at_or_above("administrator", "moderator")


def test_permission_tier_metadata():
    meta = metadata_for(PermissionTier.MODERATOR)
    assert meta.tier is PermissionTier.MODERATOR
    assert meta.tier_index == 3
    assert meta.inherits_from is PermissionTier.STAFF
    assert "Moderator" in meta.recommended_role_names


def test_all_tiers_ordered():
    tiers = all_tiers_ordered()
    assert tiers[0] is PermissionTier.USER
    assert tiers[-1] is PermissionTier.PLATFORM_OWNER


def test_role_template_builtins_registered():
    """The Phase 1d canonical templates + collections must register at import."""
    templates = all_templates()
    assert "Moderator" in templates
    assert "Administrator" in templates
    assert "Trusted" in templates


def test_role_collection_lookup():
    collections = all_collections()
    assert "moderation_essentials" in collections
    assert "administration_essentials" in collections
    assert "trusted_user_tiers" in collections


def test_moderation_collection_contains_moderator_template():
    assert any(t.name == "Moderator" for t in MODERATION_ROLES.templates)


def test_administration_collection_contains_admin_template():
    assert any(t.name == "Administrator" for t in ADMINISTRATION_ROLES.templates)


def test_trusted_collection_contains_trusted_template():
    assert any(t.name == "Trusted" for t in TRUSTED_USER_TIERS.templates)


def test_role_template_get():
    tpl = get_template("Moderator")
    assert isinstance(tpl, RoleTemplate)
    assert tpl.permission_tier is PermissionTier.MODERATOR

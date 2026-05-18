"""Role-specific resource operations.

Sibling of :mod:`core.resources.channel_service`.  Adds role-specific
predicates, template matching, and governance-scope resolution.

Integrates with Phase 1d:

* :mod:`governance.role_templates` — template matching for the
  Phase 4.5 role-provisioning service.
* :mod:`governance.scopes` — converting a role into a
  :class:`~governance.scopes.GovernanceScope` for the role-scoped
  override path.
"""

from __future__ import annotations

from collections.abc import Callable

import discord

from core.resources.discovery import (
    find_role_by_name,
    list_roles,
    resolve_resource,
    role_to_snapshot,
    validate_resource,
)
from core.resources.status import ResourceStatus
from core.resources.types import ResourceKind, RoleResource
from governance.permission_tiers import PermissionTier
from governance.role_templates import RoleTemplate, all_templates
from governance.scopes import GovernanceScope
from utils.helpers import normalize_name


def filter_roles(
    guild: discord.Guild,
    predicate: Callable[[RoleResource], bool],
) -> list[RoleResource]:
    """Enumerate roles matching ``predicate``."""
    return [r for r in list_roles(guild) if predicate(r)]


def get_role(guild: discord.Guild, role_id: int) -> RoleResource | None:
    """Look up a single role by ID, returning a snapshot."""
    resource = resolve_resource(guild, ResourceKind.ROLE, role_id)
    if isinstance(resource, RoleResource):
        return resource
    return None


def resolve_scope(role: RoleResource | discord.Role) -> GovernanceScope:
    """Return the :class:`GovernanceScope` that a role-scoped override targets.

    Roles always map to :data:`GovernanceScope.ROLE` — the helper exists
    for symmetry with future channel/category scope resolvers and to
    keep the conversion in one place.  Callers should consume this
    instead of writing ``GovernanceScope.ROLE`` inline.
    """
    # ``role`` parameter is accepted purely for type-narrowing at call
    # sites; the value is unused because role scope is uniform.
    del role
    return GovernanceScope.ROLE


def has_permission(
    role: discord.Role,
    permission_name: str,
) -> bool:
    """Return True iff ``role`` grants the named Discord permission.

    ``permission_name`` matches the attribute name on
    :class:`discord.Permissions` (e.g. ``"manage_messages"``,
    ``"administrator"``).  Unknown names return ``False`` rather than
    raising; matchers iterate over many candidates and missing flags
    should be a silent miss.
    """
    perms: discord.Permissions = role.permissions
    return bool(getattr(perms, permission_name, False))


async def status_for(
    guild: discord.Guild,
    role_id: int,
    *,
    persist: bool = True,
) -> ResourceStatus:
    """Validate a single role and return its current status."""
    return await validate_resource(
        guild,
        ResourceKind.ROLE,
        role_id,
        persist=persist,
    )


# ---------------------------------------------------------------------------
# Template matching — consumed by Phase 4.5 role provisioning
# ---------------------------------------------------------------------------


def _name_match_score(role_name: str, template_name: str) -> float:
    """Return a 0..1 name-similarity score.

    The Phase 4.5 matcher will eventually rank candidates by combined
    name + permission overlap; this helper covers the name component.
    Implementation is intentionally simple — exact (normalized) match
    is 1.0, substring is 0.5, neither is 0.0.
    """
    role_key = normalize_name(role_name)
    tpl_key = normalize_name(template_name)
    if role_key == tpl_key:
        return 1.0
    if tpl_key in role_key or role_key in tpl_key:
        return 0.5
    return 0.0


def _permission_overlap_score(role: discord.Role, template: RoleTemplate) -> float:
    """Return a 0..1 score for permission overlap between ``role`` and ``template``.

    Score is the fraction of the template's permissions that the role
    holds.  Empty template permission tuples score 0.0 (no signal).
    """
    if not template.permissions:
        return 0.0
    held = sum(1 for perm in template.permissions if has_permission(role, perm))
    return held / len(template.permissions)


def match_role_template(
    role: discord.Role,
    *,
    min_score: float = 0.5,
) -> tuple[RoleTemplate, float] | None:
    """Return the best-matching :class:`RoleTemplate` for ``role``, or ``None``.

    Combines name similarity + permission overlap into a single score
    in the [0, 2] range; returns the highest-scoring template whose
    score meets ``min_score``.  Phase 4.5's provisioning UI uses the
    returned score to render confidence.
    """
    best: tuple[RoleTemplate, float] | None = None
    for template in all_templates().values():
        score = _name_match_score(role.name, template.name)
        score += _permission_overlap_score(role, template)
        if score >= min_score and (best is None or score > best[1]):
            best = (template, score)
    return best


def list_roles_by_tier(
    guild: discord.Guild,
    tier: PermissionTier,
) -> list[RoleResource]:
    """Return snapshots of roles best matched to ``tier`` by template.

    A role is associated with a tier if :func:`match_role_template`
    finds a template whose ``permission_tier`` equals ``tier``.  The
    Phase 4.5 governance-roles surface uses this to populate the "your
    Moderator role" / "your Administrator role" displays without
    requiring an operator to bind every role explicitly.
    """
    matches: list[RoleResource] = []
    for role in guild.roles:
        if role.is_default():
            continue
        match = match_role_template(role)
        if match is not None and match[0].permission_tier is tier:
            matches.append(role_to_snapshot(role))
    return matches


__all__ = [
    "filter_roles",
    "find_role_by_name",
    "get_role",
    "has_permission",
    "list_roles",
    "list_roles_by_tier",
    "match_role_template",
    "resolve_scope",
    "role_to_snapshot",
    "status_for",
]

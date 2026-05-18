"""Phase 1d — Role template + role collection declarations.

A :class:`RoleTemplate` describes a *recommended* Discord role for a
governance tier — its name, color, permissions hint, intended tier
mapping.  Phase 4.5's role-provisioning service uses these templates
to:

* Detect existing guild roles that match a template (fuzzy by name +
  permissions).
* Recommend a binding from the template to the matched role.
* Provision a new role from the template if the guild has none.

A :class:`RoleCollection` groups templates into a logical bundle (e.g.
``MODERATION_ROLES``, ``TRUSTED_USER_TIERS``).  Phase 7's wizard
applies a collection during setup pack rollout (Phase 7.5).

This module only declares the dataclasses and the canonical built-in
collections.  No runtime — Phase 4.5 builds the matcher / provisioner
on top of these declarations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from governance.permission_tiers import PermissionTier


class RoleColor(Enum):
    """Canonical color hints for :class:`RoleTemplate`.

    The wizard renders these as a fixed palette so role templates
    across collections feel coherent.  Numeric values match
    ``discord.Color.*().value`` so existing code can convert without
    a lookup.
    """

    RED = 0xE74C3C
    ORANGE = 0xE67E22
    YELLOW = 0xF1C40F
    GREEN = 0x2ECC71
    BLUE = 0x3498DB
    PURPLE = 0x9B59B6
    GREY = 0x95A5A6
    WHITE = 0xFFFFFF


@dataclass(frozen=True)
class RoleTemplate:
    """A recommended Discord role declaration.

    Fields:

    name:
        Canonical role name.  Matchers normalize via
        :func:`utils.helpers.normalize_name` so case + spacing variants
        all resolve to the template.
    permission_tier:
        :class:`PermissionTier` this role is intended to map to.
    description:
        Short description rendered by the wizard.
    color:
        Suggested role color.
    mentionable:
        Whether the role should be mentionable.
    permissions:
        Tuple of Discord permission-name strings (e.g.
        ``"manage_messages"``, ``"kick_members"``).  Used by the
        Phase 4.5 matcher's permission-overlap score and by the Phase
        7.5 provisioner's role-creation call.
    """

    name: str
    permission_tier: PermissionTier
    description: str
    color: RoleColor = RoleColor.GREY
    mentionable: bool = False
    permissions: tuple[str, ...] = ()


@dataclass(frozen=True)
class RoleCollection:
    """A named bundle of :class:`RoleTemplate` instances.

    Collections are typically consumed by setup packs (Phase 7.5);
    applying a setup pack offers to detect / provision every template
    in the collection in one atomic flow.

    Fields:

    name:
        Stable identifier (e.g. ``"moderation_essentials"``).
    description:
        Short label for the wizard.
    templates:
        Tuple of role templates in the bundle.
    """

    name: str
    description: str
    templates: tuple[RoleTemplate, ...] = ()


# ---------------------------------------------------------------------------
# Canonical built-in templates + collections
# ---------------------------------------------------------------------------

MODERATOR_TEMPLATE = RoleTemplate(
    name="Moderator",
    permission_tier=PermissionTier.MODERATOR,
    description=(
        "Standard moderation role.  Holders may issue warns, timeouts, "
        "and kicks; minimum tier for governance writes."
    ),
    color=RoleColor.RED,
    mentionable=True,
    permissions=(
        "manage_messages",
        "kick_members",
        "moderate_members",
        "view_audit_log",
    ),
)

HELPER_TEMPLATE = RoleTemplate(
    name="Helper",
    permission_tier=PermissionTier.STAFF,
    description=(
        "Lightweight staff role for trusted helpers who assist with "
        "user questions but do not perform moderation."
    ),
    color=RoleColor.GREEN,
    mentionable=False,
    permissions=(),
)

ADMIN_TEMPLATE = RoleTemplate(
    name="Administrator",
    permission_tier=PermissionTier.ADMINISTRATOR,
    description=(
        "Server administration role.  Holders may configure "
        "subsystems, governance overrides, and channel setup."
    ),
    color=RoleColor.PURPLE,
    mentionable=True,
    permissions=("administrator",),
)

TRUSTED_TEMPLATE = RoleTemplate(
    name="Trusted",
    permission_tier=PermissionTier.TRUSTED,
    description=(
        "Modest-trust role bound to the ``TRUSTED_TIER_ROLE_ID`` "
        "setting.  Holders see surfaces hidden from the general "
        "user tier."
    ),
    color=RoleColor.BLUE,
    mentionable=False,
    permissions=(),
)


MODERATION_ROLES = RoleCollection(
    name="moderation_essentials",
    description="Recommended roles for a moderation-bearing guild.",
    templates=(MODERATOR_TEMPLATE, HELPER_TEMPLATE),
)

ADMINISTRATION_ROLES = RoleCollection(
    name="administration_essentials",
    description="Recommended roles for guild administration.",
    templates=(ADMIN_TEMPLATE,),
)

TRUSTED_USER_TIERS = RoleCollection(
    name="trusted_user_tiers",
    description="Recommended Trusted-tier role for elevated user access.",
    templates=(TRUSTED_TEMPLATE,),
)


# ---------------------------------------------------------------------------
# Registry — collections register themselves at import time so the
# Phase 4.5 / 7.5 services have a discoverable, ordered list.
# ---------------------------------------------------------------------------

_TEMPLATE_REGISTRY: dict[str, RoleTemplate] = {}
_COLLECTION_REGISTRY: dict[str, RoleCollection] = {}


def register_template(template: RoleTemplate) -> None:
    """Register ``template`` under its canonical name.

    Re-registration is allowed (hot-reload-friendly).
    """
    _TEMPLATE_REGISTRY[template.name] = template


def register_collection(collection: RoleCollection) -> None:
    """Register ``collection`` and every template it contains."""
    _COLLECTION_REGISTRY[collection.name] = collection
    for tpl in collection.templates:
        register_template(tpl)


def get_template(name: str) -> RoleTemplate | None:
    """Return the registered template, or ``None``."""
    return _TEMPLATE_REGISTRY.get(name)


def get_collection(name: str) -> RoleCollection | None:
    """Return the registered collection, or ``None``."""
    return _COLLECTION_REGISTRY.get(name)


def all_templates() -> dict[str, RoleTemplate]:
    """Return a copy of the template registry."""
    return dict(_TEMPLATE_REGISTRY)


def all_collections() -> dict[str, RoleCollection]:
    """Return a copy of the collection registry."""
    return dict(_COLLECTION_REGISTRY)


def _reset_for_tests() -> None:
    """Wipe the registries and re-register built-ins."""
    _TEMPLATE_REGISTRY.clear()
    _COLLECTION_REGISTRY.clear()
    _register_builtins()


def _register_builtins() -> None:
    """Register the canonical built-in collections at import time."""
    register_collection(MODERATION_ROLES)
    register_collection(ADMINISTRATION_ROLES)
    register_collection(TRUSTED_USER_TIERS)


_register_builtins()


__all__ = [
    "ADMIN_TEMPLATE",
    "ADMINISTRATION_ROLES",
    "HELPER_TEMPLATE",
    "MODERATION_ROLES",
    "MODERATOR_TEMPLATE",
    "RoleCollection",
    "RoleColor",
    "RoleTemplate",
    "TRUSTED_TEMPLATE",
    "TRUSTED_USER_TIERS",
    "all_collections",
    "all_templates",
    "get_collection",
    "get_template",
    "register_collection",
    "register_template",
]

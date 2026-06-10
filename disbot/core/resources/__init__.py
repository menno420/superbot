"""Unified guild resource runtime (Phase 2a).

The ``core/resources/`` package is the platform substrate for every
guild-side primitive runtime code touches: channels, roles, categories,
threads.  Phase 2a generalizes the existing ad-hoc ``guild.get_*`` call
sites and the channel/role helpers in ``views/selectors/_resource_helpers.py``
into a typed, validated, cached surface.

Package layout:

* :mod:`core.resources.status` — :class:`ResourceStatus` enum + tier
  classification helpers.
* :mod:`core.resources.types` — :class:`GuildResource` base +
  :class:`ChannelResource` / :class:`RoleResource` /
  :class:`CategoryResource` / :class:`ThreadResource` typed snapshots.
* :mod:`core.resources.discovery` — enumeration + validation primitives
  (``list_resources``, ``resolve_resource``, ``validate_resource``).
* :mod:`core.resources.channel_service` — channel-specific operations.
* :mod:`core.resources.role_service` — role-specific operations (consumes
  the Phase 1d :class:`~governance.scopes.GovernanceScope` enum +
  :mod:`governance.role_templates` for template matching).

This package is the **read/validation substrate only** — resource
creation/deletion (mutation) is owned by
:class:`services.resource_provisioning.ResourceProvisioningPipeline`.
(The unimplemented Phase 2a ``core.resources.mutation`` shell was
retired 2026-06-10 once the live pipeline superseded it.)

Public exports below are re-exported for convenience.  Consumers MAY
import directly from the submodule for clarity (e.g.
``from core.resources.channel_service import list_channels``).

The substrate layer this package replaces is :mod:`core.runtime.guild_resources`
(the older "unified resolver"); that module stays in place as a
sync-resolver back-compat path until Phase 2b lands.  No public
function in :mod:`core.runtime.guild_resources` is deleted as part of
Phase 2a.
"""

from __future__ import annotations

from core.resources import (  # noqa: F401 — re-exported
    channel_service,
    discovery,
    role_service,
    status,
    types,
)
from core.resources.status import ResourceStatus  # noqa: F401 — re-exported
from core.resources.types import (  # noqa: F401 — re-exported
    CategoryResource,
    ChannelResource,
    GuildResource,
    ResourceKind,
    RoleResource,
    ThreadResource,
)

__all__ = [
    "CategoryResource",
    "ChannelResource",
    "GuildResource",
    "ResourceKind",
    "ResourceStatus",
    "RoleResource",
    "ThreadResource",
    "channel_service",
    "discovery",
    "role_service",
    "status",
    "types",
]


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _resources_snapshot() -> dict[str, object]:
    """Snapshot provider for ``!platform resources``.

    Phase 2a surfaces only declaration-level state (which submodules
    are registered, which kinds the taxonomy supports).  Phase 4c
    extends this with per-guild cache histograms backed by
    :mod:`utils.db.resource_cache`.
    """
    from core.resources.types import ResourceKind

    return {
        "package": "core.resources",
        "kinds": [k.value for k in ResourceKind],
        "submodules": [
            "status",
            "types",
            "discovery",
            "channel_service",
            "role_service",
        ],
    }


def _register_diagnostics_providers() -> None:
    from services import diagnostics_service

    diagnostics_service.register("resources", _resources_snapshot)


_register_diagnostics_providers()

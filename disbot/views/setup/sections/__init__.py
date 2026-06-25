"""Setup-wizard section modules.

Importing this package triggers each section module's top-level
`REGISTRY.register(...)` call, populating the global
`services.setup_sections.REGISTRY` with the production section set.

`views.setup.hub` imports this package at module load so the hub view's
button layout is always derived from the registry.

PR 3a (2026-06-25) retired the dead/legacy sections — `purpose`,
`identity`, `btd6`, `ai_setup`, `readiness`, `diagnostics`,
`suggestions`, and the `server_scan` button — whose function moved into
the Essential Setup spine (step 0 + "Check my setup"). `server_scan`'s
module survives as a snapshot-cache seam (`channels` imports it directly,
not via this manifest).
"""

from __future__ import annotations

# Order of imports here is not significant — registry ordering is driven by
# each section's `order` field, not import order — but keep this list stable
# so it doubles as a manifest of which sections ship today.
from views.setup.sections import (  # noqa: F401 — import side-effect
    channels,
    cleanup,
    cog_routing,
    final_review,
    logging_presets,
    moderation,
    preset_select,
    role_templates,
    roles,
    ticket,
)

__all__ = [
    "channels",
    "cleanup",
    "cog_routing",
    "final_review",
    "logging_presets",
    "moderation",
    "preset_select",
    "role_templates",
    "roles",
    "ticket",
]

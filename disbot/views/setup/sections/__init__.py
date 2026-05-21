"""Setup-wizard section modules.

Importing this package triggers each section module's top-level
`REGISTRY.register(...)` call, populating the global
`services.setup_sections.REGISTRY` with the production section set.

`views.setup.hub` imports this package at module load so the hub view's
button layout is always derived from the registry.
"""

from __future__ import annotations

# Order of imports here is not significant — registry ordering is driven by
# each section's `order` field, not import order — but keep this list stable
# so it doubles as a manifest of which sections ship today.
from views.setup.sections import (  # noqa: F401 — import side-effect
    channels,
    final_review,
    identity,
    readiness,
    server_scan,
    suggestions,
)

__all__ = [
    "channels",
    "final_review",
    "identity",
    "readiness",
    "server_scan",
    "suggestions",
]

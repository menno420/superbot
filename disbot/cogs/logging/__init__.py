"""Logging subsystem package — S7 of the Settings Manager roadmap.

This package owns the ``logging`` subsystem's customization surface.
Today it carries only the schema declarations (S7a); S7b/S7c will
add the existing-channel-select and create-channel flows that route
through :mod:`services.binding_mutation` and
:mod:`services.resource_provisioning`.

The runtime logging behavior (event subscription, embed posting,
counters) continues to live in :mod:`services.server_logging`.  This
package is intentionally separate so future S7d work can extract a
dedicated ``LoggingCog`` with its own ``build_help_menu_view`` hook
without touching the service.
"""

from __future__ import annotations

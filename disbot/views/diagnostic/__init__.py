"""views.diagnostic — diagnostics hub + paginated views.

Extracted from ``cogs/diagnostic_cog.py`` during S4.4.5.

Modules:
    paginator  — ``_PaginatorView`` (generic prev/next embed paginator)
    hub_panel  — ``_DiagnosticsHubView`` (admin diagnostic dashboard)

Neither view is a PersistentView — both are ephemeral, timeout-based.
The hub view takes a reference to the owning ``DiagnosticCog`` so its
buttons can ``ctx.invoke`` the corresponding text commands rather than
re-implementing each diagnostic flow.
"""

from __future__ import annotations

from views.diagnostic.hub_panel import _DiagnosticsHubView
from views.diagnostic.paginator import _PaginatorView

__all__ = [
    "_DiagnosticsHubView",
    "_PaginatorView",
]

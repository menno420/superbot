"""views.diagnostic — diagnostics hub + paginated views.

Extracted from ``cogs/diagnostic_cog.py`` during S4.4.5; the hub
view's interaction-lifecycle pattern was canonicalised in PR #55
(``fix(diagnostic): align hub panel with canonical subsystem-panel
architecture``).

Modules:
    paginator  — ``_PaginatorView`` (generic prev/next embed paginator;
                 optional ``parent_view`` enables a back button)
    hub_panel  — ``_DiagnosticsHubView`` (admin diagnostic dashboard;
                 each button uses ``safe_defer`` + ``safe_edit`` to
                 update the panel in place, matching the canonical
                 panel pattern used by ``views/economy/main_panel.py``,
                 ``views/moderation/main_panel.py``, etc.)

Neither view is a PersistentView — both are ephemeral, timeout-based.
The hub view takes only the invoking ``author`` and reads ``bot``
from ``interaction.client`` at callback time, so the same view can
be safely instantiated from either ``!diagnostics`` (direct command)
or ``HelpPanelView._on_select`` (help-menu invocation).
"""

from __future__ import annotations

from views.diagnostic.hub_panel import _DiagnosticsHubView
from views.diagnostic.paginator import _PaginatorView

__all__ = [
    "_DiagnosticsHubView",
    "_PaginatorView",
]

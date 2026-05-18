"""views.diagnostic — diagnostics hub + platform hub + paginated views.

Extracted from ``cogs/diagnostic_cog.py`` during S4.4.5; the hub
view's interaction-lifecycle pattern was canonicalised in PR #55
(``fix(diagnostic): align hub panel with canonical subsystem-panel
architecture``).

Modules:
    paginator       — ``_PaginatorView`` (generic prev/next embed
                      paginator; optional ``parent_view`` enables a
                      back button)
    hub_panel       — ``_DiagnosticsHubView`` (admin diagnostic
                      dashboard; each button uses ``safe_defer`` +
                      ``safe_edit`` to update the panel in place,
                      matching the canonical panel pattern used by
                      ``views/economy/main_panel.py``,
                      ``views/moderation/main_panel.py``, etc.)
    platform_panel  — ``_PlatformHubView`` (read-only platform hub
                      opened by ``!platform`` with no subcommand;
                      groups 21 surfaces into four category Selects)

None of these views are PersistentViews — all are ephemeral,
timeout-based.  Each hub view takes only the invoking ``author`` and
reads ``bot`` from ``interaction.client`` at callback time, so the
same view can be safely instantiated from either the typed command
or ``HelpPanelView._on_select``.
"""

from __future__ import annotations

from views.diagnostic.hub_panel import _DiagnosticsHubView
from views.diagnostic.paginator import _PaginatorView
from views.diagnostic.platform_panel import _PlatformHubView, build_platform_hub_embed

__all__ = [
    "_DiagnosticsHubView",
    "_PaginatorView",
    "_PlatformHubView",
    "build_platform_hub_embed",
]

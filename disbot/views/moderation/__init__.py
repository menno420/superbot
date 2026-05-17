"""views.moderation — moderation panel PersistentView + admin modals.

Extracted from ``cogs/moderation_cog.py`` during S4.3.

Modules:
    main_panel  — ``ModPanelView`` (PersistentView, SUBSYSTEM="moderation")
    modals      — 7 admin modals (warn/timeout/kick/ban/unban/logs/clearwarn)

The cog imports ``ModPanelView`` from this package at module-load time
so the ``@register`` decorator fires and the persistent-view registry
is populated before ``on_ready`` runs ``restore_anchors``.  Pattern B
per ``docs/architecture.md`` §"PersistentView placement".
"""

from __future__ import annotations

from views.moderation.main_panel import ModPanelView
from views.moderation.modals import (
    _BanModal,
    _ClearWarningsModal,
    _KickModal,
    _ModLogsModal,
    _TimeoutModal,
    _UnbanModal,
    _WarnModal,
)

__all__ = [
    "ModPanelView",
    "_BanModal",
    "_ClearWarningsModal",
    "_KickModal",
    "_ModLogsModal",
    "_TimeoutModal",
    "_UnbanModal",
    "_WarnModal",
]

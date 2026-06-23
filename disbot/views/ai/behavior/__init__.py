"""AI Behavior preset UI (PR-C).

Usability-first wrapper around the existing AI policy scope modals,
preview/dry-run, and the preset catalog. Operators see "What should
the AI do here?" — pick a scope, pick a preset, preview, save —
rather than the raw mode/min_level/cooldown/profile knobs.

Public entry points:

* :func:`build_behavior_embed` — introductory embed
* :class:`BehaviorChooserView` — top-level workflow dispatcher

Both are imported by ``views.ai.panel`` (Behavior button) and by
``cogs.ai_cog`` (prefix / slash command entry).
"""

from __future__ import annotations

from views.ai.behavior.chooser import (  # noqa: F401
    BehaviorChooserView,
    build_behavior_chooser_page,
    build_behavior_embed,
)

__all__ = [
    "BehaviorChooserView",
    "build_behavior_chooser_page",
    "build_behavior_embed",
]

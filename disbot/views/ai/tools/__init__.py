"""Tools & Workflows admin UI (Phase 3) — AI tool-orchestration profiles.

Reached from the AI panel's ``Tools`` button. See
``docs/ai/ai-complex-request-tool-orchestration-plan.md`` §9.4 and
``docs/ai-config-ownership.md`` (orchestration mutation seam).
"""

from views.ai.tools.chooser import ToolsChooserView, build_tools_embed

__all__ = ["ToolsChooserView", "build_tools_embed"]

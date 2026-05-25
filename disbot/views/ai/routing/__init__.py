"""Operator routing matrix overview (PR-G).

Read-only diagnostic that runs the natural-language resolver in
``dry_run=True`` for representative scopes and renders the
precedence outcomes. Lives alongside the Behavior and Policy UIs
in ``views/ai/`` so the panel button can dispatch directly.
"""

from __future__ import annotations

from views.ai.routing.matrix import (  # noqa: F401
    RoutingMatrixSelectView,
    build_routing_matrix_embed,
)

__all__ = ["RoutingMatrixSelectView", "build_routing_matrix_embed"]

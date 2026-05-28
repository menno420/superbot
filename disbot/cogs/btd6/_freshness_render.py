"""Backwards-compat shim — the real module lives in ``utils.btd6``.

PR 2 moved freshness rendering to ``utils/btd6/freshness_render.py``
so both views and cogs can import it without layer violations. This
module re-exports the public surface so existing cog-side callers
keep working unchanged.
"""

from __future__ import annotations

from utils.btd6.freshness_render import (
    BUCKET_BADGE,
    BUCKET_EMOJI,
    NEVER_FETCHED_COPY,
    STALE_WARNING,
    EmptyStateReason,
    FreshnessBucket,
    render_empty_state,
    render_freshness_warning,
)

__all__ = [
    "BUCKET_BADGE",
    "BUCKET_EMOJI",
    "NEVER_FETCHED_COPY",
    "STALE_WARNING",
    "EmptyStateReason",
    "FreshnessBucket",
    "render_empty_state",
    "render_freshness_warning",
]

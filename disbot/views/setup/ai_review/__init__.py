"""AI review UI — Phase 9f / Track 5 PR 14.

Two panels that surface the :class:`SetupPlanDraft` produced by
:mod:`services.setup_ai_advisor` (or the deterministic fallback) to
the server owner.

* :class:`AIReviewPanelView` — aggregate review: shows counts per
  confidence + subsystem, exposes bulk accept/reject + per-rec drill
  + rerun-deterministic actions.
* :class:`PerRecommendationView` — one-by-one walkthrough.

Both panels are pure orchestration: they accept / reject
recommendations into an in-memory :class:`AcceptedSet`. Nothing
writes to the DB or calls ``guild.create_*``. The accepted set is
handed back to the caller (the wizard hub, Track 8 PR 23) which then
applies recommendations through the existing mutation pipelines.
"""

from views.setup.ai_review.main_panel import (
    AcceptedSet,
    AIReviewPanelView,
    build_ai_review_embed,
)
from views.setup.ai_review.per_recommendation import (
    PerRecommendationView,
    build_per_recommendation_embed,
)

__all__ = [
    "AIReviewPanelView",
    "AcceptedSet",
    "PerRecommendationView",
    "build_ai_review_embed",
    "build_per_recommendation_embed",
]

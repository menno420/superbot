"""Per-user profile surface (``/myprofile``).

PR A ships the **read-only** profile card (``profile_view``): a schema-driven
view over the per-user participation registry. PR B adds the self-service
write controls (``editor`` — the first UI consumer of
``ParticipationMutationPipeline``), reachable from the card's
``⚙️ Manage settings`` button.
"""

from __future__ import annotations

from views.profile.editor import (
    ProfileEditorHomeView,
    ProfileSubsystemEditorView,
)
from views.profile.profile_view import (
    PREFERENCE_KEY_SEP,
    ProfileHomeView,
    build_profile_embed,
    preference_key,
)

__all__ = [
    "PREFERENCE_KEY_SEP",
    "ProfileEditorHomeView",
    "ProfileHomeView",
    "ProfileSubsystemEditorView",
    "build_profile_embed",
    "preference_key",
]

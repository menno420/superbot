"""Per-user profile surface (``/myprofile``).

PR A (this package) ships the **read-only** profile card: a schema-driven
view over the per-user participation registry. PR B adds the self-service
write controls (the first UI consumer of ``ParticipationMutationPipeline``).
"""

from __future__ import annotations

from views.profile.profile_view import (
    PREFERENCE_KEY_SEP,
    ProfileHomeView,
    build_profile_embed,
    preference_key,
)

__all__ = [
    "PREFERENCE_KEY_SEP",
    "ProfileHomeView",
    "build_profile_embed",
    "preference_key",
]

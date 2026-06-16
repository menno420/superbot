"""Settings keys owned by the Image-moderation subsystem (cogs.image_moderation_cog).

image moderation v1 (owner decision Q-0108): scan uploaded images against
OpenAI's free ``omni-moderation-latest`` endpoint.  All keys are ordinary scalar
guild settings (the legacy KV ``guild_settings`` table) — there is **no
migration**.  Prefixed ``image_moderation_*`` to keep the shared KV namespace
collision-free, matching the per-subsystem naming convention.

Every flag defaults OFF so a fresh guild behaves exactly as it does today — no
image is sent to an external API until an operator opts in.  See
``services.image_moderation_config`` for the defaults (the single source of truth
shared with ``cogs.image_moderation.schemas``).
"""

# Master switch — when off, the stage is a no-op and nothing is sent externally.
IMAGE_MODERATION_ENABLED = "image_moderation_enabled"

# Per-category enable flags (the four owner-named v1 buckets).
IMAGE_MODERATION_SEXUAL_ENABLED = "image_moderation_sexual_enabled"
IMAGE_MODERATION_VIOLENCE_ENABLED = "image_moderation_violence_enabled"
IMAGE_MODERATION_HARASSMENT_ENABLED = "image_moderation_harassment_enabled"
IMAGE_MODERATION_HATE_ENABLED = "image_moderation_hate_enabled"

# Confidence threshold (percent) a category score must reach before acting.
IMAGE_MODERATION_THRESHOLD_PERCENT = "image_moderation_threshold_percent"

# Exempt safety valve — CSV of role/channel ids never scanned/acted on.
IMAGE_MODERATION_EXEMPT_ROLES = "image_moderation_exempt_roles"
IMAGE_MODERATION_EXEMPT_CHANNELS = "image_moderation_exempt_channels"

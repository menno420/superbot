"""Settings keys owned by the Moderation subsystem (cogs.moderation_cog)."""

WARN_THRESHOLD = "warn_threshold"
WARN_TIMEOUT_MINS = "warn_timeout_minutes"

# PR10 — first-class moderation configuration.  These back the
# behaviour policy applied at the ``services.moderation_service`` mutation
# seam (DM-on-action, ban message purge, timeout ceiling).  Prefixed
# ``moderation_*`` to match the modern per-subsystem naming convention and
# keep the shared guild-settings KV namespace collision-free.
MOD_DM_ON_ACTION = "moderation_dm_on_action"
MOD_DM_TEMPLATE = "moderation_dm_template"
MOD_REQUIRE_REASON = "moderation_require_reason"
MOD_BAN_DELETE_MESSAGE_DAYS = "moderation_ban_delete_message_days"
MOD_MAX_TIMEOUT_MINUTES = "moderation_max_timeout_minutes"
# The terminal action applied when a member reaches warn_threshold warnings
# (timeout / kick / ban / none).  Consumed at the moderation_service warn seam.
MOD_WARN_ESCALATION_ACTION = "moderation_warn_escalation_action"
# Post-action message cleanup: after a kick/ban, sweep the member's recent
# messages in the invoking channel (none / kick / ban / both) up to a scan
# limit.  Requested from the cleanup subsystem at the moderation_service seam.
MOD_POST_ACTION_CLEANUP = "moderation_post_action_cleanup"
MOD_POST_ACTION_CLEANUP_LIMIT = "moderation_post_action_cleanup_limit"

# Optional PUBLIC moderation log: a separate, operator-opt-in channel that
# announces selected actions (none / bans / removals / all) WITHOUT naming the
# acting moderator.  Delivered by services.server_logging; default OFF.
MOD_PUBLIC_LOG_CHANNEL = "moderation_public_log_channel"
MOD_PUBLIC_LOG_ACTIONS = "moderation_public_log_actions"

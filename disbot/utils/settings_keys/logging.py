"""Settings keys owned by the server-logging service (services.server_logging).

These four keys live in the legacy ``guild_settings`` table.  All
default to OFF / empty so the service is inert on a fresh install
until an operator opts in.
"""

# Per-guild master switch.  String 'true' / 'false' / '1' / '0' — see
# :func:`services.server_logging.is_enabled` for the parse contract.
LOGGING_ENABLED = "logging_enabled"

# Channel id (str-of-int) for moderation action embeds.
LOGGING_MOD_CHANNEL = "logging_mod_channel"

# Channel id (str-of-int) for cleanup auto-delete embeds.  Falls back
# to the mod channel if unset.
LOGGING_CLEANUP_CHANNEL = "logging_cleanup_channel"

# When true and a configured channel id is missing/invalid, the
# service calls ``guild_resources.ensure_channel`` to create a
# fall-back channel named ``DEFAULT_LOG_CHANNEL_NAME``.
LOGGING_AUTO_CREATE_CHANNELS = "logging_auto_create_channels"

# Default channel name used by ``ensure_log_channel`` when
# auto-creation is enabled.
DEFAULT_MOD_CHANNEL_NAME = "bot-mod-log"
DEFAULT_CLEANUP_CHANNEL_NAME = "bot-cleanup-log"

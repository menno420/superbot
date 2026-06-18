"""Settings keys owned by the Security subsystem (cogs.security_cog).

Security tiers 1+2 (owner decision Q-0111): raid detection + account-age filter.
The two DECLINED tiers (alt-detection / VPN blocking) own **no** keys here — they
are deliberately absent. All keys are scalar guild settings (the legacy KV
table); there is no migration.
"""

SECURITY_ENABLED = "security_enabled"  # master switch

# Tier 1 — raid detection.
SECURITY_RAID_ENABLED = "security_raid_enabled"
SECURITY_RAID_JOIN_COUNT = "security_raid_join_count"
SECURITY_RAID_WINDOW_SECONDS = "security_raid_window_seconds"
SECURITY_RAID_SLOWMODE_SECONDS = "security_raid_slowmode_seconds"
SECURITY_RAID_LOCKDOWN_SECONDS = "security_raid_lockdown_seconds"
SECURITY_RAID_SLOWMODE_CHANNEL = "security_raid_slowmode_channel"

# Tier 2 — account-age filter.
SECURITY_AGE_ENABLED = "security_age_enabled"
SECURITY_AGE_MIN_DAYS = "security_age_min_days"
SECURITY_AGE_ACTION = "security_age_action"

# Shared — where staff alerts are posted.
SECURITY_ALERT_CHANNEL = "security_alert_channel"

__all__ = [
    "SECURITY_AGE_ACTION",
    "SECURITY_AGE_ENABLED",
    "SECURITY_AGE_MIN_DAYS",
    "SECURITY_ALERT_CHANNEL",
    "SECURITY_ENABLED",
    "SECURITY_RAID_ENABLED",
    "SECURITY_RAID_JOIN_COUNT",
    "SECURITY_RAID_LOCKDOWN_SECONDS",
    "SECURITY_RAID_SLOWMODE_CHANNEL",
    "SECURITY_RAID_SLOWMODE_SECONDS",
    "SECURITY_RAID_WINDOW_SECONDS",
]

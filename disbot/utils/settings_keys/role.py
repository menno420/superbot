"""Settings keys owned by the Role subsystem (cogs.role_cog)."""

# Legacy, name-based, time-only exemption list. Superseded by the
# role_automation_exemptions table (migration 052); retained as a stable
# key only so historical KV rows do not error. No longer read at runtime.
SKIP_ROLES = "skip_roles"

# When TRUE, time-based (tenure) progression KEEPS previously-earned tier
# roles instead of removing them on promotion. Default FALSE preserves the
# historical single-role behaviour.
TIME_ROLES_STACK = "time_roles_stack"

# When TRUE (default), XP/level roles STACK — every earned level role is
# kept. When FALSE, earning a higher level role removes the lower ones.
XP_ROLES_STACK = "xp_roles_stack"

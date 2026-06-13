"""Settings keys owned by the Counters subsystem (cogs.counters_cog).

Server counters (owner decision Q-0110, the slot-6 quick-win): keep one or more
channel names showing a live server stat (total members / humans / bots) — the
"statdock" pattern (a renamed, join-locked voice channel).  All keys are
ordinary scalar guild settings (the legacy KV ``guild_settings`` table) — there
is **no migration**.  Prefixed ``counters_*`` to keep the shared KV namespace
collision-free.

Every counter defaults unbound and the master flag defaults OFF so a fresh
guild behaves exactly as it does today; an operator opts in by binding a channel
to a counter.  See ``services.counter_config`` for the defaults (the single
source of truth shared with ``cogs.counters.schemas``).
"""

# Master switch — when off, the rename loop is a no-op regardless of bindings.
COUNTERS_ENABLED = "counters_enabled"

# Counter channel bindings — a channel id (str) per stat. Empty = that counter
# is unbound (the loop skips it).
COUNTERS_TOTAL_CHANNEL = "counters_total_channel"  # total members
COUNTERS_HUMANS_CHANNEL = "counters_humans_channel"  # non-bot members
COUNTERS_BOTS_CHANNEL = "counters_bots_channel"  # bots

# Name templates — support the {count} placeholder (rendered with thousands
# separators). Kept short so the rendered name stays within Discord's 100-char
# channel-name limit.
COUNTERS_TOTAL_TEMPLATE = "counters_total_template"
COUNTERS_HUMANS_TEMPLATE = "counters_humans_template"
COUNTERS_BOTS_TEMPLATE = "counters_bots_template"

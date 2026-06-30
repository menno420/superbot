"""Settings keys owned by the Cleanup subsystem (cogs.cleanup_cog).

Cleanup's *real* configuration is domain config — prohibited-word policy and the
per-scope cleanup-level hierarchy live in the governance ``cleanup_policies``
tables (written only through ``governance.writes.GovernanceMutationPipeline``).
This module holds the handful of cleanup behaviours that are genuine **scalar**
guild settings (the legacy KV ``guild_settings`` table) — there is **no
migration**.  Prefixed ``cleanup_*`` to keep the shared KV namespace
collision-free, matching the per-subsystem naming convention.

The default is the safe minimal shape so a fresh guild behaves exactly as it
does today; an operator opts into a different window.  See
``cogs.cleanup.schemas`` for the default + bounds (the single source of truth
shared with the ``CLEANUP_CONFIG_SCHEMA`` spec).
"""

# Duplicate-message detection window (seconds) for the ``!cleanuphistory`` spam
# sweep — two near-identical messages from the same author within this window
# count as a duplicate.  Default 15 (the historical constant); operator-tunable.
CLEANUP_SPAM_WINDOW_SECONDS = "cleanup_spam_window_seconds"

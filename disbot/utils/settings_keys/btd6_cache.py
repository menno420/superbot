"""BTD6 source-cache settings keys — **reserved, not yet wired** (M3B).

These key *names* are declared and re-exported so a future BTD6 cache
cadence feature has a stable vocabulary, but as of today they are
**not consumed by any runtime code and have no SettingSpec**. They are
therefore neither operator-manageable (they never appear in the
``!settings`` hub) nor read anywhere — setting them changes nothing.
When the cache-cadence feature lands it must add the SettingSpec(s) and
the read path together; until then
``tests/unit/invariants/test_reserved_settings_keys.py`` pins their
reserved status so the gap stays explicit rather than implied.

Intended (future) meaning: BTD6 owns its cadence — not AI policy.
Per-source cadence overrides would live in
``btd6_source_registry.cache_policy_key``; these scalars would let
admins shift the global defaults without touching every row.
"""

BTD6_CACHE_DEFAULT_INTERVAL_SECONDS = "btd6_cache_default_interval_seconds"
BTD6_CACHE_CIRCUIT_BREAKER_THRESHOLD = "btd6_cache_circuit_breaker_threshold"
BTD6_CACHE_FRESHNESS_WARNING_HOURS = "btd6_cache_freshness_warning_hours"

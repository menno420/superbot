"""BTD6 source-cache settings keys (M3B).

BTD6 owns its cadence — not AI policy. Per-source cadence overrides
live in ``btd6_source_registry.cache_policy_key``; these scalars
let admins shift the global defaults without touching every row.
"""

BTD6_CACHE_DEFAULT_INTERVAL_SECONDS = "btd6_cache_default_interval_seconds"
BTD6_CACHE_CIRCUIT_BREAKER_THRESHOLD = "btd6_cache_circuit_breaker_threshold"
BTD6_CACHE_FRESHNESS_WARNING_HOURS = "btd6_cache_freshness_warning_hours"

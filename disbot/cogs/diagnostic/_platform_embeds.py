"""Back-compat shim for the diagnostic platform-embed builders.

The implementation moved to :mod:`services.diagnostic_embeds` so the
``views/diagnostic/`` panel can import the builders without a
``views → cogs`` layer-boundary violation (fleet unit A4,
``docs/planning/ultracode-fleet-plan-2026-06-19.md``).

This module is kept as a thin re-export so every existing importer and
every ``unittest.mock.patch("cogs.diagnostic._platform_embeds....")``
test patch site continues to resolve. New code should import from
``services.diagnostic_embeds`` directly.
"""

from __future__ import annotations

from services.diagnostic_embeds import (  # noqa: F401
    _EMBED_SOFT_CAP,
    _FIELD_HARD_CAP,
    _INFORMATIONAL_PREFIX,
    __all__,
    build_access_explainer_embed,
    build_anchors_embed,
    build_backfill_apply_embed,
    build_backfill_dryrun_embed,
    build_bindings_embed,
    build_caches_embed,
    build_cleanup_preview_embed,
    build_command_access_diagnostic_embed,
    build_consistency_embed,
    build_consistency_pages,
    build_counting_health_embed,
    build_customization_embed,
    build_economy_flow_embed,
    build_economy_trend_embed,
    build_findings_embed,
    build_findings_pages,
    build_flags_embed,
    build_health_embed,
    build_identity_embed,
    build_lifecycle_embed,
    build_locks_embed,
    build_media_embed,
    build_migrations_embed,
    build_participation_schemas_embed,
    build_provisioning_embed,
    build_resource_requirements_embed,
    build_resources_embed,
    build_runtime_embed,
    build_schemas_embed,
    build_sessions_embed,
    build_setting_detail_embed,
    build_settings_registry_embed,
    build_setup_readiness_embed,
    build_slow_embed,
    build_startup_health_embed,
    build_status_embed,
    build_tasks_embed,
    build_views_embed,
    governance_context_for,
    read_counting_save_outcomes,
)

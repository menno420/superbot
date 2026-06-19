"""Back-compat shim for the diagnostic embed helpers.

The implementation moved to :mod:`services.diagnostic_helpers` so the
``views/diagnostic/`` panels can import the helpers without a
``views → cogs`` layer-boundary violation (fleet unit A4,
``docs/planning/ultracode-fleet-plan-2026-06-19.md``).

This module is kept as a thin re-export so every existing importer and
every ``unittest.mock.patch("cogs.diagnostic._helpers....")`` test patch
site continues to resolve. New code should import from
``services.diagnostic_helpers`` directly.
"""

from __future__ import annotations

from services.diagnostic_helpers import (  # noqa: F401
    DATA_DIR,
    JSON_DIR,
    _fmt_snapshot_value,
    _format_table_set,
    build_bot_status_embed,
    build_check_database_embed,
    build_command_list_pages,
    build_hub_overview_embed,
    build_latency_embed,
    build_query_logs_embed,
    build_system_info_embed,
    build_test_notification_embed,
    build_validate_json_embed,
)

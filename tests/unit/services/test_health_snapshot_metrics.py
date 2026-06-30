"""Health-collection observability metrics (diagnostic cert punch #5).

The bot-awareness plan §3.6 promised collection-duration / source-failure /
redaction-outcome metrics; these tests pin that they are now wired at the
collection seams in `health_snapshot_service`.
"""

from __future__ import annotations

import pytest

pytest.importorskip("prometheus_client")

from services import health_snapshot_service as hss  # noqa: E402
from services import metrics  # noqa: E402
from services.health_contracts import (  # noqa: F401  (used in the _safe failure-builder return type)
    SubsystemHealth,
)
from services.health_contracts import (  # noqa: E402
    HealthAudience,
    HealthSnapshotRequest,
)


def _counter_value(counter, **labels) -> float:
    return counter.labels(**labels)._value.get()


def _histogram_count(name: str, **labels) -> float:
    """Read a histogram's total observation count from the default registry."""
    from prometheus_client import REGISTRY

    value = REGISTRY.get_sample_value(f"{name}_count", labels)
    return float(value or 0.0)


def test_source_failure_metric_increments_on_safe_failure() -> None:
    before = _counter_value(metrics.health_snapshot_source_failure_total, source="boom")

    def _raises() -> SubsystemHealth:
        raise RuntimeError("kaboom")

    hss._safe(_raises, "boom", required=False)

    after = _counter_value(metrics.health_snapshot_source_failure_total, source="boom")
    assert after == before + 1


def test_redaction_metric_increments_per_projection() -> None:
    snap = hss._finalize((), purpose="test", partial=False)
    before = _counter_value(
        metrics.health_snapshot_redaction_total,
        audience=HealthAudience.GUILD_ADMIN.value,
    )
    hss.project_for_audience(snap, HealthAudience.GUILD_ADMIN)
    after = _counter_value(
        metrics.health_snapshot_redaction_total,
        audience=HealthAudience.GUILD_ADMIN.value,
    )
    assert after == before + 1


def test_sync_collection_records_duration() -> None:
    before = _histogram_count("health_snapshot_collection_seconds", lane="sync")
    hss.collect_cached_snapshot(HealthSnapshotRequest())
    after = _histogram_count("health_snapshot_collection_seconds", lane="sync")
    assert after == before + 1


@pytest.mark.asyncio
async def test_async_collection_records_duration() -> None:
    before = _histogram_count("health_snapshot_collection_seconds", lane="async")
    await hss.collect_snapshot(HealthSnapshotRequest())
    after = _histogram_count("health_snapshot_collection_seconds", lane="async")
    assert after == before + 1

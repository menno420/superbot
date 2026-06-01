"""Tests for ``btd6_ops_readiness_service.evaluate()``.

Pins the verdict classification, with special attention to the
**disabled-env** case: env-off must report a distinct ``"disabled"`` status,
never a generic ``"not_ready"`` (otherwise operators can't tell "switched
off" from "switched on but broken").
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from services import btd6_ops_readiness_service as readiness


def _src(key: str, *, enabled: bool, base_url: str | None = "https://x") -> dict:
    return {"source_key": key, "enabled": enabled, "base_url": base_url}


def _health(bucket: str) -> SimpleNamespace:
    return SimpleNamespace(bucket=bucket)


def _patch(
    monkeypatch,
    *,
    enabled: bool,
    running: bool = True,
    sources=(),
    health=(),
    breakers=(),
    runs=(),
) -> None:
    from services import (
        btd6_fetch_service,
        btd6_ingestion_supervisor,
        btd6_source_registry,
    )
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_ingestion_supervisor, "is_enabled", lambda: enabled)
    monkeypatch.setattr(btd6_ingestion_supervisor, "is_running", lambda: running)

    async def _list_sources(**kwargs):
        return list(sources)

    async def _list_health(**kwargs):
        return list(health)

    async def _list_runs(**kwargs):
        return list(runs)

    monkeypatch.setattr(btd6_db, "list_sources", _list_sources)
    monkeypatch.setattr(btd6_source_registry, "list_health", _list_health)
    monkeypatch.setattr(btd6_db, "list_ingestion_runs", _list_runs)
    monkeypatch.setattr(
        btd6_fetch_service,
        "breaker_status",
        lambda: tuple(SimpleNamespace(source_key=k) for k in breakers),
    )


@pytest.mark.asyncio
async def test_disabled_env_is_distinct_state(monkeypatch) -> None:
    # Even with otherwise-healthy sources, env-off must report "disabled".
    _patch(
        monkeypatch,
        enabled=False,
        running=False,
        sources=[_src("a", enabled=True)],
        health=[_health("fresh")],
    )
    verdict = await readiness.evaluate()
    assert verdict.status == "disabled"
    assert verdict.ingestion_enabled is False


@pytest.mark.asyncio
async def test_no_enabled_sources_is_not_ready(monkeypatch) -> None:
    _patch(
        monkeypatch,
        enabled=True,
        sources=[_src("a", enabled=False)],
        health=[],
    )
    verdict = await readiness.evaluate()
    assert verdict.status == "not_ready"
    assert verdict.sources_enabled == 0
    assert verdict.sources_disabled == 1


@pytest.mark.asyncio
async def test_fresh_and_aging_is_ready(monkeypatch) -> None:
    _patch(
        monkeypatch,
        enabled=True,
        running=True,
        sources=[_src("a", enabled=True), _src("b", enabled=True)],
        health=[_health("fresh"), _health("aging")],
    )
    verdict = await readiness.evaluate()
    assert verdict.status == "ready"
    assert verdict.sources_enabled == 2
    assert (verdict.fresh, verdict.aging) == (1, 1)


@pytest.mark.asyncio
async def test_stale_is_partial(monkeypatch) -> None:
    _patch(
        monkeypatch,
        enabled=True,
        running=True,
        sources=[_src("a", enabled=True)],
        health=[_health("stale")],
    )
    verdict = await readiness.evaluate()
    assert verdict.status == "partial"
    assert verdict.stale == 1


@pytest.mark.asyncio
async def test_open_breaker_is_partial(monkeypatch) -> None:
    _patch(
        monkeypatch,
        enabled=True,
        running=True,
        sources=[_src("a", enabled=True)],
        health=[_health("fresh")],
        breakers=["nk_a"],
    )
    verdict = await readiness.evaluate()
    assert verdict.status == "partial"
    assert verdict.open_breakers == ("nk_a",)


@pytest.mark.asyncio
async def test_supervisor_not_running_is_partial(monkeypatch) -> None:
    _patch(
        monkeypatch,
        enabled=True,
        running=False,
        sources=[_src("a", enabled=True)],
        health=[_health("fresh")],
    )
    verdict = await readiness.evaluate()
    assert verdict.status == "partial"
    assert verdict.supervisor_running is False


@pytest.mark.asyncio
async def test_enabled_missing_base_url_counted_and_partial(monkeypatch) -> None:
    _patch(
        monkeypatch,
        enabled=True,
        running=True,
        sources=[_src("a", enabled=True, base_url=None)],
        health=[_health("fresh")],
    )
    verdict = await readiness.evaluate()
    assert verdict.enabled_missing_base_url == 1
    assert verdict.status == "partial"


@pytest.mark.asyncio
async def test_recent_failures_counted(monkeypatch) -> None:
    now = datetime.now(tz=timezone.utc)
    _patch(
        monkeypatch,
        enabled=True,
        running=True,
        sources=[_src("a", enabled=True)],
        health=[_health("fresh")],
        runs=[
            {"status": "success", "started_at": now},
            {"status": "fetch_error", "started_at": now},
            {"status": "store_error", "started_at": now},
        ],
    )
    verdict = await readiness.evaluate()
    assert verdict.recent_runs_total == 3
    assert verdict.recent_failures == 2
    assert verdict.last_run_at == now


def test_readiness_embed_renders_distinct_disabled_message() -> None:
    from cogs.btd6._builders import build_readiness_embed

    verdict = readiness.ReadinessVerdict(
        status="disabled",
        ingestion_enabled=False,
        supervisor_running=False,
        sources_total=3,
        sources_enabled=0,
        sources_disabled=3,
        enabled_missing_base_url=0,
        open_breakers=(),
        fresh=0,
        aging=0,
        stale=0,
        never=0,
        recent_runs_total=0,
        recent_failures=0,
        last_run_at=None,
    )
    embed = build_readiness_embed(verdict)
    assert "disabled" in (embed.title or "").lower()
    assert "switched off" in (embed.description or "").lower()


def test_ingestion_runs_embed_empty_and_populated() -> None:
    from cogs.btd6._builders import build_ingestion_runs_embed

    empty = build_ingestion_runs_embed([])
    assert "No ingestion runs" in (empty.description or "")

    now = datetime.now(tz=timezone.utc)
    populated = build_ingestion_runs_embed(
        [
            {
                "source_key": "nk_btd6_bosses",
                "status": "success",
                "started_at": now,
                "fact_count": 7,
                "error_code": None,
            },
        ],
    )
    assert "nk_btd6_bosses" in (populated.description or "")
    assert "success" in (populated.description or "")

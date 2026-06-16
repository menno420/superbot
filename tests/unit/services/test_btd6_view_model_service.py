"""Coverage for ``services/btd6_view_model_service.py``.

The VM service is the read sandwich layer between query services and
embed builders. Tests focus on:

* Context-handle construction (``make_context_handle`` regex contract).
* Freshness threading through every VM (state propagation from
  ``btd6_source_registry``).
* Primitive-only inputs (no ``discord`` import in the module).
"""

from __future__ import annotations

import importlib
import re
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

CONTEXT_ID_RE = re.compile(r"^btd6_[a-z_]+:[A-Za-z0-9_-]+$")


# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------


def test_service_does_not_import_discord() -> None:
    # The architecture rule is binding: services/btd6_view_model_service.py
    # must NEVER import ``discord``. Verify by introspecting the cleanly
    # imported module's globals — if ``discord`` were in scope, this fails.
    import services.btd6_view_model_service as vm

    importlib.reload(vm)
    # ``vm`` should not have ``discord`` in its namespace
    assert (
        "discord" not in vm.__dict__
    ), "btd6_view_model_service must not import discord (services→views boundary)"


def test_service_does_not_import_views_or_cogs() -> None:
    import services.btd6_view_model_service as vm

    src = vm.__file__
    assert src is not None
    with open(src) as f:
        text = f.read()
    assert "from views" not in text
    assert "from cogs" not in text
    assert "import views" not in text
    assert "import cogs" not in text


# ---------------------------------------------------------------------------
# Context-handle contract
# ---------------------------------------------------------------------------


def test_make_context_handle_basic() -> None:
    from services.btd6_view_model_service import make_context_handle

    handle = make_context_handle("race", "R123")
    assert handle.context_id == "btd6_race:R123"
    assert handle.context_type == "race"
    assert CONTEXT_ID_RE.match(handle.context_id)


def test_make_context_handle_sanitizes_unsafe_chars() -> None:
    from services.btd6_view_model_service import make_context_handle

    # Slashes, colons, spaces all collapse to underscores.
    handle = make_context_handle("event", "Boss Rush: vol/2")
    assert CONTEXT_ID_RE.match(handle.context_id)
    assert handle.context_id == "btd6_event:Boss_Rush__vol_2"


def test_make_context_handle_rejects_empty_key() -> None:
    from services.btd6_view_model_service import make_context_handle

    with pytest.raises(ValueError, match="empty"):
        make_context_handle("tower", "")


def test_make_context_handle_all_types_valid() -> None:
    from services.btd6_view_model_service import make_context_handle

    for kind in (
        "hub",
        "race",
        "boss",
        "ct",
        "odyssey",
        "event",
        "tower",
        "hero",
        "leaderboard",
        "strategy",
        "source",
        "status",
        "diagnostics",
    ):
        handle = make_context_handle(kind, "main")  # type: ignore[arg-type]
        assert CONTEXT_ID_RE.match(handle.context_id)


# ---------------------------------------------------------------------------
# Hub view-model
# ---------------------------------------------------------------------------


def _stub_knowledge(monkeypatch, **counts) -> None:
    from services import btd6_knowledge_service

    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    for fn, n in {
        "list_towers": counts.get("towers", 0),
        "list_heroes": counts.get("heroes", 0),
        "list_maps": counts.get("maps", 0),
        "list_modes": counts.get("modes", 0),
        "list_rounds": counts.get("rounds", 0),
    }.items():
        monkeypatch.setattr(btd6_knowledge_service, fn, lambda _n=n: [object()] * _n)


@pytest.mark.asyncio
async def test_build_hub_view_model_emits_one_row_per_kind(monkeypatch) -> None:
    """Even with zero facts, the hub VM yields all five kinds."""
    from services.btd6_view_model_service import build_hub_view_model
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(
        btd6_db, "latest_fact_per_entity_kind", AsyncMock(return_value={})
    )
    # No facts → search_facts returns nothing, so get_active_events is empty.
    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))
    _stub_knowledge(monkeypatch, towers=3, heroes=4, maps=5, modes=6, rounds=7)

    vm = await build_hub_view_model()
    assert vm.context.context_id == "btd6_hub:main"
    assert vm.tower_count == 3
    assert vm.hero_count == 4
    assert {a.entity_kind for a in vm.active_events} == {
        "btd6_race",
        "btd6_boss",
        "btd6_ct",
        "btd6_odyssey",
        "btd6_event",
    }
    # No rows → every kind is "never" with name=None.
    for active in vm.active_events:
        assert active.freshness.state == "never"
        assert active.name is None
        assert active.context is None


@pytest.mark.asyncio
async def test_build_hub_view_model_marks_fresh_for_active_event(monkeypatch) -> None:
    """A currently-active event surfaces with its name + fresh badge."""
    from services.btd6_view_model_service import build_hub_view_model
    from utils.db import btd6_sources as btd6_db

    now = datetime.now(tz=timezone.utc)
    future_ms = int((now + timedelta(days=1)).timestamp() * 1000)
    race_row = {
        "entity_kind": "btd6_race",
        "entity_key": "R42",
        "fact_type": "btd6.races_index",
        "body_json": {"name": "Reversed Loop", "end_ms": future_ms},
        "fetched_at": now - timedelta(hours=2),
    }

    async def _search_facts(*, fact_type=None, entity_kind=None, limit=50):
        # get_active_events filters by fact_type per kind; only return the
        # race row for the races_index fact_type, empty for everything else.
        if entity_kind == "btd6_race":
            return [race_row]
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _search_facts)
    monkeypatch.setattr(
        btd6_db, "latest_fact_per_entity_kind",
        AsyncMock(return_value={"btd6_race": race_row}),
    )
    _stub_knowledge(monkeypatch)

    vm = await build_hub_view_model()
    race = next(a for a in vm.active_events if a.entity_kind == "btd6_race")
    assert race.name == "Reversed Loop"
    assert race.freshness.state == "fresh"
    assert race.context is not None
    assert race.context.context_id == "btd6_race:R42"


@pytest.mark.asyncio
async def test_build_hub_view_model_hides_ended_events(monkeypatch) -> None:
    """Regression: an event whose end_ms is in the past must NOT show as active.

    Previously the hub picked an arbitrary tied-fetched_at race fact via
    DISTINCT ON; an ended race would appear with no "ended" suffix because
    the renderer didn't filter for active window. Now the hub only surfaces
    events with explicitly-future end_ms.
    """
    from services.btd6_view_model_service import build_hub_view_model
    from utils.db import btd6_sources as btd6_db

    now = datetime.now(tz=timezone.utc)
    past_ms = int((now - timedelta(days=30)).timestamp() * 1000)
    ended_race = {
        "entity_kind": "btd6_race",
        "entity_key": "Enjoying_the_Hotsprings_mois29mi",
        "fact_type": "btd6.races_index",
        "body_json": {"name": "Enjoying the Hotsprings", "end_ms": past_ms},
        "fetched_at": now - timedelta(hours=2),
    }

    async def _search_facts(*, fact_type=None, entity_kind=None, limit=50):
        if entity_kind == "btd6_race":
            return [ended_race]
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _search_facts)
    monkeypatch.setattr(
        btd6_db, "latest_fact_per_entity_kind",
        AsyncMock(return_value={"btd6_race": ended_race}),
    )
    _stub_knowledge(monkeypatch)

    vm = await build_hub_view_model()
    race = next(a for a in vm.active_events if a.entity_kind == "btd6_race")
    # No active race — name should be None (rendered as "—").
    assert race.name is None
    # But freshness still reflects the stored fact's fetched_at, so the
    # operator can see ingestion is healthy even when no race is running.
    assert race.freshness.state == "fresh"


# ---------------------------------------------------------------------------
# Staff diagnostics view-model
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_staff_diagnostics_context_global_when_no_guild(monkeypatch) -> None:
    from services import btd6_knowledge_service
    from services.btd6_view_model_service import (
        build_staff_diagnostics_view_model,
    )

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        AsyncMock(return_value=()),
    )
    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    monkeypatch.setattr(btd6_knowledge_service, "list_towers", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_heroes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_maps", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_modes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_rounds", lambda: [])

    vm = await build_staff_diagnostics_view_model()
    assert vm.context.context_id == "btd6_status:global"


@pytest.mark.asyncio
async def test_staff_diagnostics_context_guild_id(monkeypatch) -> None:
    from services import btd6_knowledge_service
    from services.btd6_view_model_service import (
        build_staff_diagnostics_view_model,
    )

    monkeypatch.setattr(
        btd6_knowledge_service,
        "fact_summary_by_kind",
        AsyncMock(return_value=()),
    )
    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    monkeypatch.setattr(btd6_knowledge_service, "list_towers", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_heroes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_maps", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_modes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_rounds", lambda: [])

    vm = await build_staff_diagnostics_view_model(guild_id=12345)
    assert vm.context.context_id == "btd6_status:12345"


# ---------------------------------------------------------------------------
# Event list / detail view-models
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_list_view_model_caps_at_25(monkeypatch) -> None:
    """The browser select cap is enforced at the VM layer."""
    from services.btd6_view_model_service import build_event_list_view_model
    from utils.db import btd6_sources as btd6_db

    # 40 mock rows — VM must return ≤25 items and report total_count=40.
    rows = [
        {
            "entity_kind": "btd6_race",
            "entity_key": f"R{i}",
            "body_json": {"name": f"Race {i}"},
            "fetched_at": datetime.now(tz=timezone.utc),
        }
        for i in range(40)
    ]
    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=rows))

    vm = await build_event_list_view_model("race")
    assert len(vm.items) <= 25
    assert vm.total_count == 40
    # Every item carries a valid context handle.
    for item in vm.items:
        assert CONTEXT_ID_RE.match(item.context.context_id)
        assert item.context.context_type == "race"


@pytest.mark.asyncio
async def test_event_list_accepts_short_or_long_kind(monkeypatch) -> None:
    from services.btd6_view_model_service import build_event_list_view_model
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))

    short_vm = await build_event_list_view_model("race")
    long_vm = await build_event_list_view_model("btd6_race")
    assert short_vm.kind == long_vm.kind == "race"
    assert short_vm.entity_kind == long_vm.entity_kind == "btd6_race"


@pytest.mark.asyncio
async def test_event_detail_returns_none_when_no_fact(monkeypatch) -> None:
    from services.btd6_view_model_service import build_event_detail_view_model
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(btd6_db, "get_latest_fact", AsyncMock(return_value=None))

    vm = await build_event_detail_view_model("race", "missing")
    assert vm is None


@pytest.mark.asyncio
async def test_event_detail_builds_full_vm(monkeypatch) -> None:
    from services.btd6_view_model_service import build_event_detail_view_model
    from utils.db import btd6_sources as btd6_db

    now = datetime.now(tz=timezone.utc)
    index_row = {
        "entity_kind": "btd6_race",
        "entity_key": "R42",
        "fact_type": "btd6.races_index",
        "body_json": {
            "name": "Reversed Loop",
            "start_ms": int(now.timestamp() * 1000) - 3_600_000,
            "end_ms": int(now.timestamp() * 1000) + 3_600_000,
        },
        "fetched_at": now,
    }

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        if fact_type == "btd6.races_index":
            return index_row
        return None

    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    vm = await build_event_detail_view_model("race", "R42")
    assert vm is not None
    assert vm.name == "Reversed Loop"
    assert vm.context.context_id == "btd6_race:R42"
    assert vm.window.state == "active"
    assert vm.freshness.state == "fresh"


@pytest.mark.asyncio
async def test_event_detail_does_not_pass_entity_key_to_search_facts(
    monkeypatch,
) -> None:
    """Regression: the drill-down used to call ``search_facts(entity_key=…)``,
    which raises ``TypeError`` (no such kwarg) on EVERY event detail — the
    "race event button does nothing" bug. The detail path must use
    ``get_latest_fact`` (entity-keyed), never ``search_facts`` with an
    ``entity_key`` kwarg.
    """
    import inspect

    from services.btd6_view_model_service import build_event_detail_view_model
    from utils.db import btd6_sources as btd6_db

    # The real signature must not accept entity_key (proves the old call broke).
    assert "entity_key" not in inspect.signature(btd6_db.search_facts).parameters

    boom = AsyncMock(side_effect=AssertionError("detail must not call search_facts"))
    monkeypatch.setattr(btd6_db, "search_facts", boom)
    monkeypatch.setattr(btd6_db, "get_latest_fact", AsyncMock(return_value=None))

    # Must not raise (old code raised TypeError here) and must not touch search_facts.
    vm = await build_event_detail_view_model("race", "R42")
    assert vm is None
    boom.assert_not_called()


@pytest.mark.asyncio
async def test_event_detail_fetches_boss_metadata_with_standard_suffix(
    monkeypatch,
) -> None:
    """Boss metadata lives under ``btd6_boss_difficulty`` keyed
    ``{id}_standard`` (the ingestion fan-out). The detail VM must look it up
    with that suffix so boss rules/restrictions actually render.
    """
    from services.btd6_view_model_service import build_event_detail_view_model
    from utils.db import btd6_sources as btd6_db

    now = datetime.now(tz=timezone.utc)
    calls: list[tuple] = []

    async def _get_latest_fact(fact_type, entity_kind, entity_key):
        calls.append((fact_type, entity_kind, entity_key))
        if fact_type == "btd6.bosses_index":
            return {
                "entity_kind": "btd6_boss",
                "entity_key": "Dreadbloon35",
                "body_json": {"name": "Dreadbloon", "end_ms": 0},
                "fetched_at": now,
            }
        if fact_type == "btd6.boss_metadata":
            return {
                "entity_kind": "btd6_boss_difficulty",
                "entity_key": entity_key,
                "body_json": {"_towers": [{"tower": "Druid", "max": 0}]},
                "fetched_at": now,
            }
        return None

    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)

    vm = await build_event_detail_view_model("boss", "Dreadbloon35")
    assert vm is not None
    # The metadata lookup used the _standard suffix, not _normal.
    assert ("btd6.boss_metadata", "btd6_boss_difficulty", "Dreadbloon35_standard") in calls
    assert vm.metadata_body.get("_towers")


# ---------------------------------------------------------------------------
# Live overview (current-event-first landing)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_live_overview_groups_only_live_events(monkeypatch) -> None:
    from services import btd6_live_query_service
    from services.btd6_live_query_service import ActiveEventHeadline
    from services.btd6_view_model_service import build_live_overview_view_model
    from utils.db import btd6_sources as btd6_db

    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    headlines = (
        ActiveEventHeadline(
            "btd6_ct", "ct1", "Contested Territory", now_ms - 1000, now_ms + 36_000_000, None
        ),
        ActiveEventHeadline(
            "btd6_event", "ev1", "Collab Event", None, now_ms + 72_000_000, None
        ),
        # ended → excluded by the strict future-end filter
        ActiveEventHeadline("btd6_race", "r_old", "Old Race", None, now_ms - 1000, None),
        # missing end_ms → excluded by the strict filter
        ActiveEventHeadline("btd6_boss", "b1", "Boss", None, None, None),
    )
    monkeypatch.setattr(
        btd6_live_query_service,
        "get_active_events",
        AsyncMock(return_value=headlines),
    )
    monkeypatch.setattr(
        btd6_db, "latest_fact_per_entity_kind", AsyncMock(return_value={})
    )

    vm = await build_live_overview_view_model()
    # All 5 kinds always present, in useful-first order.
    assert tuple(k.short_kind for k in vm.kinds) == (
        "race",
        "boss",
        "ct",
        "odyssey",
        "event",
    )
    # Only the two explicit-future events count as live.
    assert vm.total_live == 2
    assert {it.entity_key for it in vm.all_live} == {"ct1", "ev1"}
    by_short = {k.short_kind: k for k in vm.kinds}
    assert by_short["race"].live == ()  # ended excluded
    assert by_short["boss"].live == ()  # missing-end excluded
    assert by_short["ct"].live[0].name == "Contested Territory"
    assert by_short["ct"].live[0].context.context_id == "btd6_ct:ct1"


@pytest.mark.asyncio
async def test_live_overview_empty_when_nothing_live(monkeypatch) -> None:
    from services import btd6_live_query_service
    from services.btd6_view_model_service import build_live_overview_view_model
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(
        btd6_live_query_service, "get_active_events", AsyncMock(return_value=())
    )
    monkeypatch.setattr(
        btd6_db, "latest_fact_per_entity_kind", AsyncMock(return_value={})
    )

    vm = await build_live_overview_view_model()
    assert vm.total_live == 0
    assert vm.all_live == ()
    # No stored facts at all → worst per-kind freshness is "never".
    assert vm.worst_freshness == "never"


# ---------------------------------------------------------------------------
# Leaderboard list / detail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_leaderboard_list_rejects_unknown_kind(monkeypatch) -> None:
    from services.btd6_view_model_service import build_leaderboard_list_view_model

    with pytest.raises(ValueError, match="must be 'race' or 'boss'"):
        await build_leaderboard_list_view_model("odyssey")


@pytest.mark.asyncio
async def test_leaderboard_detail_context_format(monkeypatch) -> None:
    from services import btd6_live_query_service as live
    from services.btd6_view_model_service import build_leaderboard_detail_view_model

    monkeypatch.setattr(live, "get_race_leaderboard", AsyncMock(return_value=()))
    monkeypatch.setattr(live, "get_newest_active_race", AsyncMock(return_value=None))

    vm = await build_leaderboard_detail_view_model("race", "R42")
    assert vm.context.context_id == "btd6_leaderboard:race_R42"
    assert vm.event_kind == "race"
    assert vm.event_id == "R42"


# ---------------------------------------------------------------------------
# Tower / Hero list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tower_list_caps_at_25(monkeypatch) -> None:
    from services import btd6_knowledge_service
    from services.btd6_view_model_service import build_tower_list_view_model

    class _Stub:
        def __init__(self, ident: str) -> None:
            self.id = ident
            self.canonical = ident.title()
            self.base_cost = 100
            self.category = "primary"

    monkeypatch.setattr(
        btd6_knowledge_service,
        "list_towers",
        lambda: [_Stub(f"t{i}") for i in range(40)],
    )

    vm = await build_tower_list_view_model()
    assert len(vm.items) <= 25
    assert vm.total_count == 40
    for item in vm.items:
        assert CONTEXT_ID_RE.match(item.context.context_id)


# ---------------------------------------------------------------------------
# DataFreshness propagation
# ---------------------------------------------------------------------------


def test_data_freshness_default_stale_after_24h() -> None:
    from services.btd6_view_model_service import (
        STALE_AFTER_SECONDS,
        DataFreshness,
    )

    fresh = DataFreshness(
        state="fresh",
        last_success_at=None,
        last_attempt_at=None,
        source_key="nk_btd6_races",
    )
    assert fresh.stale_after_seconds == 86_400
    assert STALE_AFTER_SECONDS == 86_400

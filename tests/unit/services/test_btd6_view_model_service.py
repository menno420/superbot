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


@pytest.mark.asyncio
async def test_build_hub_view_model_emits_one_row_per_kind(monkeypatch) -> None:
    """Even with zero facts, the hub VM yields all five kinds."""
    from services import btd6_knowledge_service
    from services.btd6_view_model_service import build_hub_view_model
    from utils.db import btd6_sources as btd6_db

    monkeypatch.setattr(
        btd6_db, "latest_fact_per_entity_kind", AsyncMock(return_value={})
    )
    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    monkeypatch.setattr(btd6_knowledge_service, "list_towers", lambda: [object()] * 3)
    monkeypatch.setattr(btd6_knowledge_service, "list_heroes", lambda: [object()] * 4)
    monkeypatch.setattr(btd6_knowledge_service, "list_maps", lambda: [object()] * 5)
    monkeypatch.setattr(btd6_knowledge_service, "list_modes", lambda: [object()] * 6)
    monkeypatch.setattr(btd6_knowledge_service, "list_rounds", lambda: [object()] * 7)

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
async def test_build_hub_view_model_marks_fresh_for_recent_fact(monkeypatch) -> None:
    from services import btd6_knowledge_service
    from services.btd6_view_model_service import build_hub_view_model
    from utils.db import btd6_sources as btd6_db

    now = datetime.now(tz=timezone.utc)
    monkeypatch.setattr(
        btd6_db,
        "latest_fact_per_entity_kind",
        AsyncMock(
            return_value={
                "btd6_race": {
                    "entity_kind": "btd6_race",
                    "entity_key": "R42",
                    "body_json": {"name": "Reversed Loop", "end_ms": 999_999_999_999},
                    "fetched_at": now - timedelta(hours=2),
                },
            },
        ),
    )
    monkeypatch.setattr(btd6_knowledge_service, "data_version", lambda: "1.0")
    monkeypatch.setattr(btd6_knowledge_service, "game_version", lambda: "42.0")
    monkeypatch.setattr(btd6_knowledge_service, "list_towers", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_heroes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_maps", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_modes", lambda: [])
    monkeypatch.setattr(btd6_knowledge_service, "list_rounds", lambda: [])

    vm = await build_hub_view_model()
    race = next(a for a in vm.active_events if a.entity_kind == "btd6_race")
    assert race.name == "Reversed Loop"
    assert race.freshness.state == "fresh"
    assert race.context is not None
    assert race.context.context_id == "btd6_race:R42"


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

    monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[]))

    vm = await build_event_detail_view_model("race", "missing")
    assert vm is None


@pytest.mark.asyncio
async def test_event_detail_builds_full_vm(monkeypatch) -> None:
    from services.btd6_view_model_service import build_event_detail_view_model
    from utils.db import btd6_sources as btd6_db

    now = datetime.now(tz=timezone.utc)
    monkeypatch.setattr(
        btd6_db,
        "search_facts",
        AsyncMock(
            return_value=[
                {
                    "entity_kind": "btd6_race",
                    "entity_key": "R42",
                    "fact_type": "btd6.races_index",
                    "body_json": {
                        "name": "Reversed Loop",
                        "start_ms": int(now.timestamp() * 1000) - 3_600_000,
                        "end_ms": int(now.timestamp() * 1000) + 3_600_000,
                    },
                    "fetched_at": now,
                },
            ],
        ),
    )

    vm = await build_event_detail_view_model("race", "R42")
    assert vm is not None
    assert vm.name == "Reversed Loop"
    assert vm.context.context_id == "btd6_race:R42"
    assert vm.window.state == "active"
    assert vm.freshness.state == "fresh"


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

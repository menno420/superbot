"""Recursion + dependency-chain tests for refresh_with_dependencies.

These tests pin the three invariants the revision report flagged:

1. Parent parsers emit the exact keys child sources consume.
2. Recursive refresh executes depth-N leaves, blocks descent FROM depth N.
3. Child runs record ``reason="dependency"`` regardless of parent reason;
   ``started_by_user_id`` is propagated through every depth level.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from services import btd6_ingestion_service


def _ok(source_key: str, *keys: str) -> btd6_ingestion_service.IngestionResult:
    """Build an OK IngestionResult with the given ``written_entity_keys``."""
    return btd6_ingestion_service.IngestionResult(
        source_key=source_key,
        status="ok",
        fact_count=len(keys) or 1,
        duration_ms=1,
        error_code=None,
        run_id=1,
        written_entity_keys=tuple(keys),
    )


def _bad(source_key: str) -> btd6_ingestion_service.IngestionResult:
    return btd6_ingestion_service.IngestionResult(
        source_key=source_key,
        status="fetch_error",
        fact_count=0,
        duration_ms=1,
        error_code="503",
        run_id=2,
        written_entity_keys=(),
    )


# ---------------------------------------------------------------------------
# Chain shape: maps → filter → one (two-level recursion)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_maps_chain_executes_three_levels(monkeypatch):
    """Refreshing nk_btd6_maps should reach nk_btd6_maps_one for every map id."""
    calls: list[tuple[str, dict | None]] = []

    # Per-source canned responses. Each call records the (source_key,
    # path_params) tuple so we can assert exact call counts and the
    # path params each level produced.
    map_ids_per_filter = {
        "newest": [f"map_n_{i}" for i in range(15)],  # > cap of 10
        "trending": ["map_t_a", "map_t_b"],
        "mostLiked": ["map_l_x"],
    }

    async def _refresh_source_stub(source_key, *, path_params=None, **kw):
        calls.append((source_key, path_params))
        if source_key == "nk_btd6_maps":
            return _ok(source_key, "newest", "trending", "mostLiked")
        if source_key == "nk_btd6_maps_filter":
            filter_name = (path_params or {}).get("mapFilter")
            return _ok(source_key, *map_ids_per_filter.get(filter_name, []))
        if source_key == "nk_btd6_maps_one":
            return _ok(source_key, (path_params or {}).get("mapID", ""))
        return _ok(source_key)

    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source",
        _refresh_source_stub,
    )

    results = await btd6_ingestion_service.refresh_with_dependencies(
        "nk_btd6_maps",
        reason="manual",
        started_by_user_id=42,
    )

    # Bucket calls by source_key for exact counting.
    by_source: dict[str, list[dict | None]] = {}
    for src, params in calls:
        by_source.setdefault(src, []).append(params)

    # 1 parent + 3 filter children (one per filter name).
    assert len(by_source["nk_btd6_maps"]) == 1
    assert len(by_source["nk_btd6_maps_filter"]) == 3
    filters_passed = {p["mapFilter"] for p in by_source["nk_btd6_maps_filter"]}
    assert filters_passed == {"newest", "trending", "mostLiked"}

    # maps_one: 10 from newest (cap), 2 from trending, 1 from mostLiked = 13.
    assert len(by_source["nk_btd6_maps_one"]) == 13
    map_ids_called = [p["mapID"] for p in by_source["nk_btd6_maps_one"]]
    # The cap drops map_n_10..14 — only first 10 from "newest".
    assert "map_n_0" in map_ids_called
    assert "map_n_9" in map_ids_called
    assert "map_n_10" not in map_ids_called
    assert "map_t_a" in map_ids_called
    assert "map_l_x" in map_ids_called

    # Results aggregate parent + every successful child.
    assert len(results) == 1 + 3 + 13


# ---------------------------------------------------------------------------
# Chain shape: challenges (same two-level pattern as maps)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_challenges_chain_same_shape(monkeypatch):
    calls: list[tuple[str, dict | None]] = []

    async def _stub(source_key, *, path_params=None, **kw):
        calls.append((source_key, path_params))
        if source_key == "nk_btd6_challenges":
            return _ok(source_key, "daily", "newest")
        if source_key == "nk_btd6_challenges_filter":
            return _ok(source_key, "ch_1", "ch_2")
        return _ok(source_key)

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    await btd6_ingestion_service.refresh_with_dependencies("nk_btd6_challenges")

    by_source: dict[str, list[dict | None]] = {}
    for src, params in calls:
        by_source.setdefault(src, []).append(params)

    assert len(by_source["nk_btd6_challenges"]) == 1
    assert len(by_source["nk_btd6_challenges_filter"]) == 2
    # 2 filters × 2 challenge ids = 4 leaf calls.
    assert len(by_source["nk_btd6_challenges_one"]) == 4


# ---------------------------------------------------------------------------
# Chain shape: races (two children of the same parent: metadata + leaderboard)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_races_fans_into_metadata_and_leaderboard(monkeypatch):
    calls: list[tuple[str, dict | None]] = []

    async def _stub(source_key, *, path_params=None, **kw):
        calls.append((source_key, path_params))
        if source_key == "nk_btd6_races":
            # 8 race ids — caps will trim per child.
            return _ok(source_key, *(f"race_{i}" for i in range(8)))
        return _ok(source_key)

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    await btd6_ingestion_service.refresh_with_dependencies("nk_btd6_races")

    by_source: dict[str, list[dict | None]] = {}
    for src, params in calls:
        by_source.setdefault(src, []).append(params)

    # Caps: metadata=5, leaderboard=3.
    assert len(by_source["nk_btd6_races_metadata"]) == 5
    assert len(by_source["nk_btd6_races_leaderboard"]) == 3


# ---------------------------------------------------------------------------
# Single-source helper uses an intentionally unchained source
# (per second revision report: don't use nk_btd6_maps — it's a chain
# parent now.)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_source_helper_returns_one_result_for_events(monkeypatch):
    """events is parent-only — no child parsers exist in the registry."""
    calls: list[str] = []

    async def _stub(source_key, *, path_params=None, **kw):
        calls.append(source_key)
        return _ok(source_key, "evt_1", "evt_2")

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    results = await btd6_ingestion_service.refresh_source_or_dependencies(
        "nk_btd6_events",
    )

    assert calls == ["nk_btd6_events"]
    assert len(results) == 1
    assert results[0].source_key == "nk_btd6_events"


# ---------------------------------------------------------------------------
# Depth guard: a→b→c→d with _MAX_DEPTH=2 executes a, b, c; blocks d
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_depth_guard_blocks_only_beyond_max_depth(monkeypatch):
    """Synthetic 4-level chain to prove the guard runs depth-2 leaves."""
    fake_chains = {
        "a": [
            btd6_ingestion_service._DependencySpec(
                child_source="b",
                path_param_builder=lambda k: {"k": k},
            )
        ],
        "b": [
            btd6_ingestion_service._DependencySpec(
                child_source="c",
                path_param_builder=lambda k: {"k": k},
            )
        ],
        "c": [
            btd6_ingestion_service._DependencySpec(
                child_source="d",
                path_param_builder=lambda k: {"k": k},
            )
        ],
    }
    monkeypatch.setattr(
        btd6_ingestion_service,
        "_DEPENDENCY_CHAINS",
        fake_chains,
    )

    calls: list[str] = []

    async def _stub(source_key, *, path_params=None, **kw):
        calls.append(source_key)
        return _ok(source_key, "x")

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    await btd6_ingestion_service.refresh_with_dependencies("a")

    # _MAX_DEPTH = 2 means: a (depth 0) → b (depth 1) → c (depth 2) are
    # all executed, but the recursion does NOT descend from c into d.
    assert calls == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Cycle safety: a → b → a self-cycle hits the depth cap, doesn't loop
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cycle_blocked_by_depth_cap(monkeypatch):
    fake_chains = {
        "a": [
            btd6_ingestion_service._DependencySpec(
                child_source="b",
                path_param_builder=lambda k: {"k": k},
            )
        ],
        "b": [
            btd6_ingestion_service._DependencySpec(
                child_source="a",
                path_param_builder=lambda k: {"k": k},
            )
        ],
    }
    monkeypatch.setattr(
        btd6_ingestion_service,
        "_DEPENDENCY_CHAINS",
        fake_chains,
    )

    calls: list[str] = []

    async def _stub(source_key, *, path_params=None, **kw):
        calls.append(source_key)
        return _ok(source_key, "x")

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    await btd6_ingestion_service.refresh_with_dependencies("a")

    # Depth 0: a → depth 1: b → depth 2: a (executed, no descent).
    assert calls == ["a", "b", "a"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parent_failure_blocks_child_calls(monkeypatch):
    calls: list[str] = []

    async def _stub(source_key, *, path_params=None, **kw):
        calls.append(source_key)
        return _bad(source_key) if source_key == "nk_btd6_maps" else _ok(source_key)

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    results = await btd6_ingestion_service.refresh_with_dependencies("nk_btd6_maps")

    assert calls == ["nk_btd6_maps"]
    assert len(results) == 1
    assert results[0].status == "fetch_error"


@pytest.mark.asyncio
async def test_empty_written_keys_means_no_child_calls(monkeypatch):
    calls: list[str] = []

    async def _stub(source_key, *, path_params=None, **kw):
        calls.append(source_key)
        # Parent succeeds but writes nothing.
        return _ok(source_key)  # no extra keys → written_entity_keys=()

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    await btd6_ingestion_service.refresh_with_dependencies("nk_btd6_maps")

    assert calls == ["nk_btd6_maps"]


@pytest.mark.asyncio
async def test_max_child_keys_none_means_no_cap(monkeypatch):
    """nk_btd6_maps spec has max_child_keys=None — all 3 filters expand."""
    spec_under_test = btd6_ingestion_service._DEPENDENCY_CHAINS["nk_btd6_maps"][0]
    assert spec_under_test.max_child_keys is None
    assert spec_under_test.child_source == "nk_btd6_maps_filter"


# ---------------------------------------------------------------------------
# Child run role: reason="dependency" + started_by_user_id propagation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_child_runs_use_dependency_reason_and_inherit_user_id(monkeypatch):
    """Audit semantics: parent role flows to ``triggered_by``; users come
    from ``started_by_user_id``. This is the regression pin against the
    post-#353 ``reason=reason`` inheritance."""
    seen: list[dict] = []

    async def _stub(
        source_key, *, path_params=None, reason="scheduled", started_by_user_id=None
    ):
        seen.append(
            {
                "source_key": source_key,
                "reason": reason,
                "started_by_user_id": started_by_user_id,
            }
        )
        if source_key == "nk_btd6_maps":
            return _ok(source_key, "newest")
        if source_key == "nk_btd6_maps_filter":
            return _ok(source_key, "the_map")
        return _ok(source_key)

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    await btd6_ingestion_service.refresh_with_dependencies(
        "nk_btd6_maps",
        reason="manual",
        started_by_user_id=12345,
    )

    # Parent gets the caller's reason.
    parent_call = next(c for c in seen if c["source_key"] == "nk_btd6_maps")
    assert parent_call["reason"] == "manual"
    assert parent_call["started_by_user_id"] == 12345

    # Children get reason="dependency" but inherit the user id.
    children = [c for c in seen if c["source_key"] != "nk_btd6_maps"]
    assert children, "expected at least one child call"
    for child in children:
        assert child["reason"] == "dependency", (
            f"child {child['source_key']!r} should be 'dependency', "
            f"got {child['reason']!r}"
        )
        assert child["started_by_user_id"] == 12345


@pytest.mark.asyncio
async def test_scheduled_parent_also_produces_dependency_children(monkeypatch):
    """Scheduler path: parent='scheduled', children still get 'dependency'."""
    seen: list[dict] = []

    async def _stub(
        source_key, *, path_params=None, reason="scheduled", started_by_user_id=None
    ):
        seen.append({"source_key": source_key, "reason": reason})
        if source_key == "nk_btd6_ct":
            return _ok(source_key, "tile_1", "tile_2")
        return _ok(source_key)

    monkeypatch.setattr(btd6_ingestion_service, "refresh_source", _stub)

    await btd6_ingestion_service.refresh_with_dependencies(
        "nk_btd6_ct",
        reason="scheduled",
    )

    parent = next(c for c in seen if c["source_key"] == "nk_btd6_ct")
    children = [c for c in seen if c["source_key"] == "nk_btd6_ct_tiles"]
    assert parent["reason"] == "scheduled"
    assert len(children) == 2
    assert all(c["reason"] == "dependency" for c in children)


# ---------------------------------------------------------------------------
# Supervisor pin: scheduler uses the dependency-aware entry point
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_supervisor_calls_dependency_aware_refresh(monkeypatch):
    """Regression pin against accidentally bypassing _DEPENDENCY_CHAINS."""
    from services import btd6_ingestion_supervisor

    # _SOURCE_INTERVALS covers the 7 NK parents plus the Steam patch-notes
    # feed (a standalone parent — no dependency chain).
    assert set(btd6_ingestion_supervisor._SOURCE_INTERVALS) == {
        "nk_btd6_events",
        "nk_btd6_races",
        "nk_btd6_bosses",
        "nk_btd6_odyssey",
        "nk_btd6_ct",
        "nk_btd6_maps",
        "nk_btd6_challenges",
        "steam_btd6_news",
    }

    # The supervisor loop spawns refresh_with_dependencies for each
    # source — not raw refresh_source. We grep here as a structural
    # pin (a regression to refresh_source would still pass type
    # checking but break dependency expansion).
    import inspect

    source = inspect.getsource(btd6_ingestion_supervisor._run_loop)
    assert (
        "refresh_with_dependencies" in source
    ), "supervisor must invoke the dependency-aware refresh helper"


# ---------------------------------------------------------------------------
# Spec registry covers every chain claimed by the plan
# ---------------------------------------------------------------------------


def test_dependency_chains_cover_expected_parents():
    chains = btd6_ingestion_service._DEPENDENCY_CHAINS
    expected_parents = {
        "nk_btd6_ct",
        "nk_btd6_maps",
        "nk_btd6_maps_filter",
        "nk_btd6_challenges",
        "nk_btd6_challenges_filter",
        "nk_btd6_races",
        "nk_btd6_bosses",
        "nk_btd6_odyssey",
    }
    assert expected_parents.issubset(chains.keys())

    # events is intentionally parent-only — no chain.
    assert "nk_btd6_events" not in chains


def test_max_child_keys_caps_match_plan():
    chains = btd6_ingestion_service._DEPENDENCY_CHAINS
    # Plan caps to keep one cycle from chewing through unbounded fan-out.
    caps_by_child = {
        spec.child_source: spec.max_child_keys
        for specs in chains.values()
        for spec in specs
    }
    assert caps_by_child["nk_btd6_maps_one"] == 10
    assert caps_by_child["nk_btd6_challenges_one"] == 10
    assert caps_by_child["nk_btd6_races_metadata"] == 5
    assert caps_by_child["nk_btd6_races_leaderboard"] == 3
    assert caps_by_child["nk_btd6_bosses_metadata"] == 5
    assert caps_by_child["nk_btd6_odyssey_diff"] == 5
    # No-cap entries: filter-level expansions where the parent API
    # itself already bounds the result.
    assert caps_by_child["nk_btd6_ct_tiles"] is None
    assert caps_by_child["nk_btd6_maps_filter"] is None
    assert caps_by_child["nk_btd6_challenges_filter"] is None

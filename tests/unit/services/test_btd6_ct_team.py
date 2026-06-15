"""Per-team Contested Territory standings: config parsing, live bracket fetch,
and the guild-scoped ``btd6_ct_team_status`` AI tool.

The bracket (group) endpoint is event-specific, so the service fetches it on
demand and flags a stale id (one minted for a past event) rather than guessing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_ct_team_service as svc  # noqa: E402
from services import btd6_fetch_service  # noqa: E402
from services import btd6_live_query_service as live  # noqa: E402

_GROUP = "cafb78d69fc3a3f21d168f245d718920895d41e8dd"
_URL = "https://data.ninjakiwi.com/btd6/ct/mpejg5d0/leaderboard/group/" + _GROUP


# ---------------------------------------------------------------------------
# parse_group_id
# ---------------------------------------------------------------------------


def test_parse_group_id_from_full_url():
    assert svc.parse_group_id(_URL) == _GROUP


def test_parse_group_id_from_bare_uppercase_id():
    assert svc.parse_group_id(_GROUP.upper()) == _GROUP


def test_parse_group_id_strips_query_and_trailing_slash():
    assert svc.parse_group_id(_URL + "/?x=1") == _GROUP


def test_parse_group_id_rejects_non_hex_and_empty():
    assert svc.parse_group_id("not a real id!!") is None
    assert svc.parse_group_id("") is None
    assert svc.parse_group_id("   ") is None
    # A short token (< 8 chars) is not a plausible group id.
    assert svc.parse_group_id("abc") is None


# ---------------------------------------------------------------------------
# get_ct_bracket
# ---------------------------------------------------------------------------


def _patch_active_event(monkeypatch, ct_id: str | None = "mpejg5d0"):
    async def _active(kinds=None):
        if ct_id is None:
            return ()
        return (live.ActiveEventHeadline("btd6_ct", ct_id, ct_id, None, None, None),)

    monkeypatch.setattr(live, "get_active_events", _active)


def _patch_fetch(monkeypatch, body):
    async def _fetch(source_key, *, path_params=None, page=1, timeout=0.0):
        assert source_key == "nk_btd6_ct_lb_group"
        assert set(path_params or {}) == {"ctID", "groupID"}
        return btd6_fetch_service.FetchResult(
            source_key=source_key,
            status_code=200,
            raw_body=json.dumps(body),
        )

    monkeypatch.setattr(btd6_fetch_service, "fetch", _fetch)


@pytest.mark.asyncio
async def test_get_ct_bracket_ranks_by_score(monkeypatch):
    _patch_active_event(monkeypatch)
    _patch_fetch(
        monkeypatch,
        {
            "body": [
                {"displayName": "LUCY", "score": 7160},
                {"displayName": "CH3ESE", "score": 267980},
                {"displayName": "MYSTICAL", "score": 500},
            ],
        },
    )
    result = await svc.get_ct_bracket(_GROUP)
    assert result.ct_id == "mpejg5d0"
    assert result.stale is False
    assert [(r.rank, r.display_name, r.score) for r in result.rows] == [
        (1, "CH3ESE", 267980),
        (2, "LUCY", 7160),
        (3, "MYSTICAL", 500),
    ]


@pytest.mark.asyncio
async def test_get_ct_bracket_empty_body_is_stale(monkeypatch):
    _patch_active_event(monkeypatch)
    _patch_fetch(monkeypatch, {"body": []})
    result = await svc.get_ct_bracket(_GROUP)
    assert result.ct_id == "mpejg5d0"
    assert result.stale is True
    assert result.rows == ()


@pytest.mark.asyncio
async def test_get_ct_bracket_no_active_event(monkeypatch):
    _patch_active_event(monkeypatch, ct_id=None)
    result = await svc.get_ct_bracket(_GROUP)
    assert result.ct_id is None
    assert result.stale is False
    assert result.rows == ()


@pytest.mark.asyncio
async def test_get_ct_bracket_blank_group_id_short_circuits(monkeypatch):
    # No fetch / no active-event lookup should be needed for a blank id.
    result = await svc.get_ct_bracket("   ")
    assert result == svc.CTBracketResult(ct_id=None, rows=(), stale=False)


@pytest.mark.asyncio
async def test_get_ct_bracket_fetch_refused_degrades(monkeypatch):
    _patch_active_event(monkeypatch)

    async def _refuse(source_key, *, path_params=None, page=1, timeout=0.0):
        raise btd6_fetch_service.BTD6FetchRefusedError(source_key, "disabled")

    monkeypatch.setattr(btd6_fetch_service, "fetch", _refuse)
    result = await svc.get_ct_bracket(_GROUP)
    # Refusal is not "stale" (we don't know the bracket is empty) — just empty.
    assert result.ct_id == "mpejg5d0"
    assert result.stale is False
    assert result.rows == ()


# ---------------------------------------------------------------------------
# AI tool: btd6_ct_team_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tool_reports_not_configured(monkeypatch):
    from services import ai_tools

    async def _none(_guild_id):
        return ""

    monkeypatch.setattr(svc, "get_team_group_id", _none)
    out = await ai_tools._make_btd6_ct_team_status(123)({})
    assert out["configured"] is False
    assert "ctteam" in out["note"]


@pytest.mark.asyncio
async def test_tool_returns_ranked_bracket(monkeypatch):
    from services import ai_tools

    async def _gid(_guild_id):
        return _GROUP

    _patch_active_event(monkeypatch)
    _patch_fetch(
        monkeypatch,
        {
            "body": [
                {"displayName": "Us", "score": 10},
                {"displayName": "Them", "score": 5},
            ]
        },
    )
    monkeypatch.setattr(svc, "get_team_group_id", _gid)
    out = await ai_tools._make_btd6_ct_team_status(123)({})
    assert out["configured"] is True
    assert out["ct_event_id"] == "mpejg5d0"
    assert out["bracket"][0] == {"rank": 1, "team": "Us", "score": 10}


@pytest.mark.asyncio
async def test_tool_flags_stale(monkeypatch):
    from services import ai_tools

    async def _gid(_guild_id):
        return _GROUP

    _patch_active_event(monkeypatch)
    _patch_fetch(monkeypatch, {"body": []})
    monkeypatch.setattr(svc, "get_team_group_id", _gid)
    out = await ai_tools._make_btd6_ct_team_status(123)({})
    assert out.get("stale") is True
    assert "re-paste" in out["note"]


# ---------------------------------------------------------------------------
# set / get / clear (settings round-trip)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_get_clear_group_id_roundtrip(monkeypatch):
    store: dict[tuple[int, str], str] = {}

    async def _get(guild_id, key, default=""):
        return store.get((guild_id, key), default)

    async def _set(guild_id, key, value):
        store[(guild_id, key)] = value

    monkeypatch.setattr(svc.db, "get_setting", _get)
    monkeypatch.setattr(svc.db, "set_setting", _set)

    # A full URL is normalised to the bare id on the way in.
    stored = await svc.set_team_group_id(42, _URL)
    assert stored == _GROUP
    assert await svc.get_team_group_id(42) == _GROUP

    # Junk is rejected and nothing is written.
    assert await svc.set_team_group_id(42, "garbage") is None
    assert await svc.get_team_group_id(42) == _GROUP

    await svc.clear_team_group_id(42)
    assert await svc.get_team_group_id(42) == ""

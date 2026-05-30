"""Tests for the Paragon service: live parsing, error taxonomy, fallback.

The only network seam is ``paragon_service._http_post``; every test
monkeypatches it, so no real HTTP call is ever made.
"""

from __future__ import annotations

import pytest

from services import paragon_service as ps
from services.paragon_service import ParagonInputs


@pytest.fixture(autouse=True)
def _reset_cache():
    ps._reset_for_tests()
    yield
    ps._reset_for_tests()


def _success(
    *,
    degree: int = 74,
    base_price: int = 150_000,
    paragon_id: str = "apex_plasma_master",
    difficulty: str = "medium",
) -> tuple[int, dict]:
    return (
        200,
        {
            "success": True,
            "api_version": "1.1",
            "result": {
                "degree": degree,
                "total_power": 147_800,
                "power_for_next_degree": 2053,
                "next_degree": min(100, degree + 1),
                "breakdown": {
                    "pops": {
                        "power": 44444,
                        "max_power": 90000,
                        "capped": False,
                        "fill_pct": 49.38,
                    },
                    "upgrades": {
                        "power": 6000,
                        "max_power": 10000,
                        "capped": False,
                        "fill_pct": 60.0,
                    },
                    "cash": {
                        "power": 20000,
                        "max_power": 60000,
                        "capped": False,
                        "fill_pct": 33.33,
                    },
                    "extra_t5s": {
                        "power": 6000,
                        "max_power": 50000,
                        "capped": False,
                        "fill_pct": 12.0,
                    },
                    "totems": {
                        "power": 10000,
                        "max_power": None,
                        "capped": False,
                        "fill_pct": None,
                    },
                },
                "warnings": [],
                "wasted_cash": 0,
                "paragon": {
                    "id": paragon_id,
                    "name": "Apex Plasma Master",
                    "tower": "Dart Monkey",
                    "base_price": base_price,
                    "difficulty": difficulty,
                    "game_mode": "solo",
                },
            },
            "rate_limit": {
                "limit": 60,
                "remaining": 59,
                "reset_in_seconds": 60,
                "window": "60s",
            },
        },
    )


# --- success parsing ---------------------------------------------------------


async def test_calculate_parses_live_success(monkeypatch):
    async def fake_post(_payload):
        return _success()

    monkeypatch.setattr(ps, "_http_post", fake_post)

    res = await ps.calculate(ParagonInputs(tower="Dart Monkey", pops=8_000_000))

    assert res.estimated is False
    assert res.source == "live_api"
    assert res.base_price_source == "api"
    assert res.api_version == "1.1"
    assert res.paragon_id == "apex_plasma_master"
    assert res.breakdown.degree == 74
    assert res.breakdown.totems.max_power is None


async def test_extra_unknown_fields_are_tolerated(monkeypatch):
    status, body = _success()
    body["unexpected_top_level"] = "ignored"
    body["result"]["breakdown"]["pops"]["nonsense"] = 1
    body["result"]["warnings"] = [{"type": "foo", "message": "bar", "extra": 1}]

    async def fake_post(_payload):
        return status, body

    monkeypatch.setattr(ps, "_http_post", fake_post)

    res = await ps.calculate(ParagonInputs(tower="Dart Monkey"))
    assert res.estimated is False
    assert res.warnings[0].type == "foo"
    assert res.warnings[0].message == "bar"


# --- error taxonomy ----------------------------------------------------------


async def test_rate_limit_raises_and_does_not_fall_back(monkeypatch):
    async def fake_post(_payload):
        return 429, {
            "success": False,
            "error": {"code": "RATE_LIMITED", "message": "slow", "retry_after": 7},
        }

    monkeypatch.setattr(ps, "_http_post", fake_post)

    with pytest.raises(ps.ParagonRateLimitError) as exc:
        await ps.calculate(ParagonInputs(tower="Dart Monkey"))
    assert exc.value.retry_after == 7


async def test_unknown_tower_raises_with_valid_towers(monkeypatch):
    async def fake_post(_payload):
        return 400, {
            "success": False,
            "error": {"code": "UNKNOWN_TOWER", "message": "no match"},
            "valid_towers": ["Dart Monkey", "Druid"],
        }

    monkeypatch.setattr(ps, "_http_post", fake_post)

    with pytest.raises(ps.ParagonUnknownTowerError) as exc:
        await ps.calculate(ParagonInputs(tower="zzz"))
    assert "Dart Monkey" in exc.value.valid_towers


async def test_missing_field_raises_service_error(monkeypatch):
    async def fake_post(_payload):
        return 400, {
            "success": False,
            "error": {"code": "MISSING_FIELD", "message": "tower required"},
        }

    monkeypatch.setattr(ps, "_http_post", fake_post)

    with pytest.raises(ps.ParagonServiceError):
        await ps.calculate(ParagonInputs(tower=""))


async def test_method_not_allowed_raises_service_error(monkeypatch):
    async def fake_post(_payload):
        return 405, {
            "success": False,
            "error": {"code": "METHOD_NOT_ALLOWED", "message": "use POST"},
        }

    monkeypatch.setattr(ps, "_http_post", fake_post)

    with pytest.raises(ps.ParagonServiceError):
        await ps.calculate(ParagonInputs(tower="Dart Monkey"))


# --- fallback ----------------------------------------------------------------


async def test_server_error_falls_back_to_local_estimate(monkeypatch):
    async def fake_post(_payload):
        return 503, {"error": "down"}

    monkeypatch.setattr(ps, "_http_post", fake_post)

    res = await ps.calculate(
        ParagonInputs(
            tower="Dart Monkey",
            pops=8_000_000,
            cash_spent=150_000,
            upgrade_count=60,
            tier5_count=1,
            geraldo_totems=5,
        )
    )
    assert res.estimated is True
    assert res.source == "local_formula"
    assert res.base_price_source == "local_table"
    assert res.api_version is None
    assert res.breakdown.degree == 68  # the validated local replica
    assert any(w.type == "api_unavailable" for w in res.warnings)


async def test_network_error_falls_back(monkeypatch):
    async def fake_post(_payload):
        raise ps.ParagonAPIUnavailableError("boom")

    monkeypatch.setattr(ps, "_http_post", fake_post)

    res = await ps.calculate(ParagonInputs(tower="Dart Monkey"))
    assert res.estimated is True
    assert res.source == "local_formula"


async def test_malformed_success_falls_back(monkeypatch):
    async def fake_post(_payload):
        return 200, {"success": True}  # missing result/breakdown

    monkeypatch.setattr(ps, "_http_post", fake_post)

    res = await ps.calculate(ParagonInputs(tower="Dart Monkey"))
    assert res.estimated is True


async def test_fallback_still_raises_for_unknown_tower(monkeypatch):
    async def fake_post(_payload):
        raise ps.ParagonAPIUnavailableError("offline")

    monkeypatch.setattr(ps, "_http_post", fake_post)

    with pytest.raises(ps.ParagonUnknownTowerError):
        await ps.calculate(ParagonInputs(tower="definitely not a tower"))


# --- base-price reconciliation ----------------------------------------------


async def test_base_price_drift_is_logged_but_api_value_used(monkeypatch, caplog):
    async def fake_post(_payload):
        return _success(base_price=999_999)

    monkeypatch.setattr(ps, "_http_post", fake_post)

    with caplog.at_level("WARNING"):
        res = await ps.calculate(ParagonInputs(tower="Dart Monkey"))

    assert res.base_price == 999_999
    assert any("base_price drift" in record.message for record in caplog.records)


# --- caching / coalescing / headers -----------------------------------------


async def test_calculate_caches_repeat_requests(monkeypatch):
    calls = 0

    async def fake_post(_payload):
        nonlocal calls
        calls += 1
        return _success()

    monkeypatch.setattr(ps, "_http_post", fake_post)

    inputs = ParagonInputs(tower="Dart Monkey", pops=8_000_000)
    await ps.calculate(inputs)
    await ps.calculate(inputs)
    assert calls == 1  # second request served from the short-TTL cache


def test_headers_include_key_only_when_configured(monkeypatch):
    monkeypatch.setattr(ps, "_API_KEY", "")
    assert "X-API-Key" not in ps._build_headers()

    monkeypatch.setattr(ps, "_API_KEY", "secret-key")
    assert ps._build_headers()["X-API-Key"] == "secret-key"


# --- reverse solve + single verification ------------------------------------


async def test_requirements_solves_and_verifies_once(monkeypatch):
    calls = 0

    async def fake_post(_payload):
        nonlocal calls
        calls += 1
        return _success(degree=90)

    monkeypatch.setattr(ps, "_http_post", fake_post)

    req = await ps.requirements(
        90, "Dart Monkey", strategy="least_cash", player_count=1
    )

    assert calls == 1  # exactly one verification call
    assert req.verified is True
    assert req.estimated is False
    assert req.confirmed_degree == 90
    assert req.solution.target_degree == 90
    assert req.paragon_id == "apex_plasma_master"


async def test_requirements_unknown_tower_raises():
    with pytest.raises(ps.ParagonUnknownTowerError):
        await ps.requirements(50, "not a real tower")


async def test_requirements_keeps_local_solution_when_verify_unavailable(monkeypatch):
    async def fake_post(_payload):
        raise ps.ParagonAPIUnavailableError("offline")

    monkeypatch.setattr(ps, "_http_post", fake_post)

    req = await ps.requirements(80, "Dart Monkey", strategy="balanced", player_count=1)

    assert req.solution.target_degree == 80
    assert req.solution.breakdown.degree >= 80
    assert req.estimated is True  # not live-confirmed

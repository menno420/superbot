"""BTD6 Paragon Calculator service — live API wrapper + local fallback.

Forward calculations call the public Paragon Calculator API
(``POST {base}/api/paragon/calculate``); when the host cannot reach it the
service falls back to a clearly-labelled local estimate computed from
:mod:`utils.btd6.paragon_math` (which replicates the API's formula exactly).

The inverse problem — "what does it take to reach Degree X for the least cash /
tiers / pops, or balanced" — is solved locally (the API has no reverse endpoint)
and then confirmed with at most one forward call.

Resilience details:

* a short-TTL success cache keyed by the normalised payload, plus in-flight
  coalescing, keep the 60 req/min unauth rate limit from being a problem;
* ``429`` returns a :class:`ParagonRateLimitError` — it never silently degrades
  to a local estimate;
* transport / 5xx / unparseable responses raise :class:`ParagonAPIUnavailableError`
  and fall back to a labelled local estimate;
* the committed ``BASE_PRICES_MEDIUM`` table is the source of truth for the
  fallback; a live ``base_price`` that disagrees is logged and used only for
  that one live calculation.

The only HTTP entry point is :func:`_http_post`; tests monkeypatch it so no
network call is ever made under pytest.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass

from utils.btd6 import paragon_math as pm
from utils.btd6.paragon_math import (
    AxisBreakdown,
    Paragon,
    ParagonBreakdown,
    ParagonInputs,
    ParagonWarning,
    RequirementSolution,
    SolveStrategy,
)

logger = logging.getLogger("bot.services.paragon")

_BASE_URL = os.getenv("PARAGON_API_BASE_URL", "https://paragon-calc.vercel.app")
_API_KEY = os.getenv("PARAGON_API_KEY", "")

# --- public attribution ------------------------------------------------------
# The Paragon Calculator web app and the Discord user who built it. The
# calculator panel (``!paragon`` / the BTD6 hub button) shows a link button +
# credit, and AI answers that used the paragon tools append the same credit, so
# a click-through to the live site and author credit travel with every result.
# Kept here — the service already owns the live-API URL (``_BASE_URL``) and is
# importable by both ``views/`` and the AI ``services/``.
CALCULATOR_PUBLIC_URL = "https://paragon-calc.vercel.app/"
CALCULATOR_AUTHOR_ID = 1407658814668275712
CALCULATOR_AUTHOR_NAME = "notausgang0341"

_TIMEOUT_SECONDS = 10
_CACHE_TTL_SECONDS = 60.0

# Short-TTL forward-result cache + in-flight coalescing (rate-limit hygiene).
_CACHE: dict[str, tuple[float, ParagonResult]] = {}
_INFLIGHT: dict[str, asyncio.Future[ParagonResult]] = {}


# --- error taxonomy ----------------------------------------------------------


class ParagonServiceError(Exception):
    """Base class for paragon-service failures."""


class ParagonUnknownTowerError(ParagonServiceError):
    """The tower/paragon could not be matched."""

    def __init__(self, message: str, *, valid_towers: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.valid_towers = valid_towers


class ParagonRateLimitError(ParagonServiceError):
    """The API rate limit was exceeded (HTTP 429)."""

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ParagonSchemaError(ParagonServiceError):
    """The API responded with a shape we could not parse."""


class ParagonAPIUnavailableError(ParagonServiceError):
    """Transport error / 5xx / non-JSON body — triggers the local fallback."""


# --- result models -----------------------------------------------------------


@dataclass(frozen=True)
class ParagonResult:
    """A forward calculation, from the live API or a labelled local estimate."""

    paragon_id: str
    paragon_name: str
    tower: str
    base_price: int
    difficulty: str
    game_mode: str
    breakdown: ParagonBreakdown
    warnings: tuple[ParagonWarning, ...]
    estimated: bool
    source: str  # "live_api" | "local_formula"
    base_price_source: str  # "api" | "local_table"
    api_version: str | None = None
    rate_limit: dict[str, object] | None = None


@dataclass(frozen=True)
class ParagonRequirementResult:
    """A reverse-solve result plus its (best-effort) live confirmation."""

    solution: RequirementSolution
    paragon_id: str
    paragon_name: str
    tower: str
    verified: bool  # confirmed against the live API
    estimated: bool  # True when not live-confirmed
    confirmed_degree: int | None


# --- public API --------------------------------------------------------------


def local_valid_towers() -> tuple[str, ...]:
    """Player-facing identifiers accepted offline (for error messages)."""
    return tuple(f"{p.name} ({p.tower})" for p in pm.PARAGONS)


def coerce_strategy(value: object) -> SolveStrategy:
    """Map a string / enum to a :class:`SolveStrategy` (defaults to balanced)."""
    if isinstance(value, SolveStrategy):
        return value
    try:
        return SolveStrategy(str(value).strip().lower())
    except ValueError:
        return SolveStrategy.BALANCED


async def calculate(inputs: ParagonInputs) -> ParagonResult:
    """Forward calculation: live API, with a labelled local fallback.

    Cached for a short window and coalesced so concurrent identical requests
    make a single upstream call. Raises :class:`ParagonRateLimitError` and
    :class:`ParagonUnknownTowerError` (these never fall back); transport/5xx/
    schema failures fall back to a local estimate.
    """
    key = _payload_key(inputs)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    inflight = _INFLIGHT.get(key)
    if inflight is not None:
        return await inflight

    loop = asyncio.get_running_loop()
    future: asyncio.Future[ParagonResult] = loop.create_future()
    # Mark any stored exception as retrieved so an uncontended error (no
    # coalesced waiter) does not warn at GC; awaiters still re-raise on await.
    future.add_done_callback(_retrieve_future_exception)
    _INFLIGHT[key] = future
    try:
        result = await _calculate_resolved(inputs)
    except BaseException as exc:  # propagate to coalesced waiters, do not cache
        _INFLIGHT.pop(key, None)
        if not future.done():
            future.set_exception(exc)
        raise
    _INFLIGHT.pop(key, None)
    _cache_put(key, result)
    if not future.done():
        future.set_result(result)
    return result


async def requirements(
    target_degree: int,
    tower: str,
    *,
    strategy: object = SolveStrategy.BALANCED,
    player_count: int = 1,
    difficulty: str = "medium",
) -> ParagonRequirementResult:
    """Reverse-solve the inputs for ``target_degree`` and confirm them once."""
    paragon = pm.resolve_paragon(tower)
    if paragon is None:
        raise ParagonUnknownTowerError(
            f"Unknown tower/paragon: {tower!r}.",
            valid_towers=local_valid_towers(),
        )
    strat = coerce_strategy(strategy)
    solution = pm.solve_requirements(
        paragon,
        target_degree,
        strat,
        player_count=player_count,
        difficulty=difficulty,
    )

    verified = False
    estimated = True
    confirmed_degree: int | None = solution.breakdown.degree
    try:
        confirmation = await calculate(solution.inputs)
        confirmed_degree = confirmation.breakdown.degree
        verified = not confirmation.estimated
        estimated = confirmation.estimated
    except ParagonServiceError as exc:
        logger.info("paragon requirement verification skipped: %s", exc)

    return ParagonRequirementResult(
        solution=solution,
        paragon_id=paragon.paragon_id,
        paragon_name=paragon.name,
        tower=paragon.tower,
        verified=verified,
        estimated=estimated,
        confirmed_degree=confirmed_degree,
    )


# --- internals ---------------------------------------------------------------


async def _calculate_resolved(inputs: ParagonInputs) -> ParagonResult:
    try:
        return await _calculate_via_api(inputs)
    except (ParagonAPIUnavailableError, ParagonSchemaError) as exc:
        logger.warning("paragon live calc unavailable (%s); using local estimate", exc)
        return _local_fallback(inputs)


async def _calculate_via_api(inputs: ParagonInputs) -> ParagonResult:
    status, data = await _http_post(inputs.as_payload())
    if not isinstance(data, dict):
        raise ParagonSchemaError("response body was not a JSON object")
    if status >= 500:
        raise ParagonAPIUnavailableError(f"server error {status}")
    if status == 200 and data.get("success"):
        return _parse_success(data)

    error = data.get("error") if isinstance(data.get("error"), dict) else {}
    code = str(error.get("code") or "")
    if status == 429 or code == "RATE_LIMITED":
        raise ParagonRateLimitError(
            str(error.get("message") or "Rate limit exceeded."),
            retry_after=_retry_after(data, error),
        )
    if code == "UNKNOWN_TOWER":
        raise ParagonUnknownTowerError(
            str(error.get("message") or "Unknown tower."),
            valid_towers=_valid_towers(data, error),
        )
    if status == 400 or code == "MISSING_FIELD":
        raise ParagonServiceError(str(error.get("message") or "Invalid request."))
    if status == 405:
        raise ParagonServiceError("The calculator rejected the request method.")
    raise ParagonSchemaError(
        f"unexpected response (status={status}, success={data.get('success')})",
    )


def _parse_success(data: dict[str, object]) -> ParagonResult:
    result = data.get("result")
    raw_breakdown = result.get("breakdown") if isinstance(result, dict) else None
    paragon_info = result.get("paragon") if isinstance(result, dict) else None
    if not (
        isinstance(result, dict)
        and isinstance(raw_breakdown, dict)
        and isinstance(paragon_info, dict)
    ):
        raise ParagonSchemaError("response missing result/breakdown/paragon")
    try:
        total_power = int(result["total_power"])
        breakdown = ParagonBreakdown(
            degree=int(result["degree"]),
            total_power=total_power,
            power_for_next_degree=int(
                result.get(
                    "power_for_next_degree",
                    pm.power_for_next_degree(total_power),
                ),
            ),
            next_degree=int(result.get("next_degree", pm.next_degree(total_power))),
            pops=_parse_axis(raw_breakdown, "pops"),
            upgrades=_parse_axis(raw_breakdown, "upgrades"),
            cash=_parse_axis(raw_breakdown, "cash"),
            extra_t5s=_parse_axis(raw_breakdown, "extra_t5s"),
            totems=_parse_axis(raw_breakdown, "totems"),
            wasted_cash=int(result.get("wasted_cash", 0)),
        )
        paragon_id = str(paragon_info["id"])
        api_base_price = int(paragon_info["base_price"])
        difficulty = str(paragon_info["difficulty"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ParagonSchemaError(f"could not parse success response: {exc}") from exc

    _reconcile_base_price(paragon_id, difficulty, api_base_price)
    raw_warnings = result.get("warnings")
    warnings = (
        tuple(
            ParagonWarning(str(w.get("type", "")), str(w.get("message", "")))
            for w in raw_warnings
            if isinstance(w, dict)
        )
        if isinstance(raw_warnings, list)
        else ()
    )
    rate_limit = data.get("rate_limit")
    return ParagonResult(
        paragon_id=paragon_id,
        paragon_name=str(paragon_info.get("name", paragon_id)),
        tower=str(paragon_info.get("tower", "")),
        base_price=api_base_price,
        difficulty=difficulty,
        game_mode=str(paragon_info.get("game_mode", "")),
        breakdown=breakdown,
        warnings=warnings,
        estimated=False,
        source="live_api",
        base_price_source="api",
        api_version=(
            str(data["api_version"]) if data.get("api_version") is not None else None
        ),
        rate_limit=rate_limit if isinstance(rate_limit, dict) else None,
    )


def _parse_axis(breakdown: dict[str, object], key: str) -> AxisBreakdown:
    raw = breakdown.get(key)
    axis = raw if isinstance(raw, dict) else {}
    max_power = axis.get("max_power")
    fill_pct = axis.get("fill_pct")
    return AxisBreakdown(
        key=key,
        power=int(axis.get("power", 0)),
        max_power=int(max_power) if max_power is not None else None,
        capped=bool(axis.get("capped", False)),
        fill_pct=float(fill_pct) if fill_pct is not None else None,
        note=str(axis.get("note", "")),
    )


def _reconcile_base_price(
    paragon_id: str,
    difficulty: str,
    api_base_price: int,
) -> None:
    paragon = pm.resolve_paragon(paragon_id)
    if paragon is None:
        return
    table_price = pm.base_price(paragon, difficulty)
    if api_base_price != table_price:
        logger.warning(
            "paragon base_price drift: id=%s difficulty=%s api=%s table=%s "
            "(using API value for this calc; update BASE_PRICES_MEDIUM)",
            paragon_id,
            difficulty,
            api_base_price,
            table_price,
        )


def _local_fallback(inputs: ParagonInputs) -> ParagonResult:
    paragon = pm.resolve_paragon(inputs.tower)
    if paragon is None:
        raise ParagonUnknownTowerError(
            f"Unknown tower/paragon: {inputs.tower!r}.",
            valid_towers=local_valid_towers(),
        )
    base_price_value = pm.base_price(paragon, inputs.difficulty)
    breakdown = pm.compute_breakdown(inputs, base_price_value)
    warnings = (
        *pm.validate_inputs(inputs),
        ParagonWarning(
            "api_unavailable",
            "The live calculator was unreachable — this is a local estimate.",
        ),
    )
    return ParagonResult(
        paragon_id=paragon.paragon_id,
        paragon_name=paragon.name,
        tower=paragon.tower,
        base_price=base_price_value,
        difficulty=inputs.difficulty,
        game_mode=pm.game_mode_for(inputs.player_count),
        breakdown=breakdown,
        warnings=warnings,
        estimated=True,
        source="local_formula",
        base_price_source="local_table",
        api_version=None,
        rate_limit=None,
    )


async def _http_post(payload: dict[str, object]) -> tuple[int, object]:
    """POST ``payload`` to the calculator; return ``(status, parsed_json)``.

    Lazy-imports ``aiohttp`` so importing this module never requires it and so
    tests that monkeypatch this function never touch the network.
    """
    import aiohttp

    url = f"{_BASE_URL.rstrip('/')}/api/paragon/calculate"
    headers = _build_headers()
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=_TIMEOUT_SECONDS),
            ) as resp,
        ):
            status = resp.status
            try:
                data = await resp.json(content_type=None)
            except Exception as exc:  # noqa: BLE001 - any decode failure == unavailable
                raise ParagonAPIUnavailableError(
                    "non-JSON response from calculator",
                ) from exc
            return status, data
    except ParagonAPIUnavailableError:
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
        raise ParagonAPIUnavailableError(str(exc) or "network error") from exc


def _build_headers() -> dict[str, str]:
    """Request headers; the optional API key is attached only when configured."""
    headers = {"Content-Type": "application/json"}
    if _API_KEY:
        headers["X-API-Key"] = _API_KEY
    return headers


def _retry_after(data: dict[str, object], error: dict[str, object]) -> int | None:
    for source in (error, data):
        value = source.get("retry_after")
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    rate = data.get("rate_limit")
    if isinstance(rate, dict) and rate.get("reset_in_seconds") is not None:
        try:
            return int(rate["reset_in_seconds"])
        except (TypeError, ValueError):
            return None
    return None


def _valid_towers(data: dict[str, object], error: dict[str, object]) -> tuple[str, ...]:
    for source in (data, error):
        towers = source.get("valid_towers")
        if isinstance(towers, list):
            return tuple(str(t) for t in towers)
    return local_valid_towers()


def _payload_key(inputs: ParagonInputs) -> str:
    payload = inputs.as_payload()
    return "&".join(f"{k}={payload[k]}" for k in sorted(payload))


def _cache_get(key: str) -> ParagonResult | None:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    stored_at, result = entry
    if time.monotonic() - stored_at > _CACHE_TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return result


def _cache_put(key: str, result: ParagonResult) -> None:
    _CACHE[key] = (time.monotonic(), result)


def _retrieve_future_exception(future: asyncio.Future[ParagonResult]) -> None:
    if not future.cancelled():
        future.exception()  # marks the exception retrieved; await still re-raises


def _reset_for_tests() -> None:
    """Clear the cache and in-flight map (test isolation)."""
    _CACHE.clear()
    _INFLIGHT.clear()


__all__ = [
    "CALCULATOR_AUTHOR_ID",
    "CALCULATOR_AUTHOR_NAME",
    "CALCULATOR_PUBLIC_URL",
    "Paragon",
    "ParagonAPIUnavailableError",
    "ParagonInputs",
    "ParagonRateLimitError",
    "ParagonRequirementResult",
    "ParagonResult",
    "ParagonSchemaError",
    "ParagonServiceError",
    "ParagonUnknownTowerError",
    "SolveStrategy",
    "calculate",
    "coerce_strategy",
    "local_valid_towers",
    "requirements",
]

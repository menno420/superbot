"""AI gateway — the single chokepoint for provider calls.

Responsibilities (in pipeline order):

1. Feature-flag check (:mod:`feature_flags`) — return degraded
   without invoking a provider when AI is disabled or the task is
   gated off.
2. Safety prechecks (:mod:`safety`) — empty prompt / oversized
   payload → degraded.
3. Redaction (:mod:`redaction`) — scrub the payload before any
   external call.
4. Routing (:mod:`routing`) — task → provider, model, timeout.
5. Provider call wrapped in ``asyncio.wait_for`` for the timeout.
6. Metrics observation (counters + histogram).
7. Parse text into :class:`AIResponse` (JSON parse when
   ``AIResponseMode.JSON``).
8. On any exception or timeout: convert to degraded
   :class:`AIResponse` (never raises to caller).

The gateway is the only place a cog or service should ask "talk to
an AI provider". Consumers import via ``services.ai_gateway`` (the
service-layer shim) — never directly from this module — so the
dependency direction stays cogs → services → core/runtime.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from core.runtime.ai import redaction
from core.runtime.ai.contracts import AIRequest, AIResponse, AIResponseMode
from core.runtime.ai.diagnostics import DiagnosticsCollector, get_default_collector
from core.runtime.ai.feature_flags import task_enabled
from core.runtime.ai.providers import (
    DeterministicFallbackError,
    DeterministicProvider,
    OpenAIProvider,
    Provider,
    ProviderUnavailableError,
)
from core.runtime.ai.routing import RoutingTarget, resolve
from core.runtime.ai.safety import precheck
from services import metrics
from utils.db import ai as ai_db

logger = logging.getLogger("bot.runtime.ai.gateway")


def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Redact secrets from every string value in ``payload``."""
    result = redaction.redact_payload(payload)
    return result.value if isinstance(result.value, dict) else dict(result.value)


def _redact_string(value: str) -> str:
    """Run redaction on a plain string and return the scrubbed value."""
    return redaction.redact_text(value).value


def _degraded_response(
    request: AIRequest,
    *,
    provider_name: str,
    reason: str,
    latency_ms: float | None = None,
) -> AIResponse:
    return AIResponse(
        task=request.context.task,
        provider=provider_name,
        model="",
        text=None,
        data=None,
        suggestions=(),
        latency_ms=latency_ms,
        degraded=True,
        fallback_reason=reason,
    )


async def _overlay_guild_policy(
    target: RoutingTarget,
    guild_id: int,
) -> RoutingTarget:
    """Apply per-guild provider/model overrides from ``ai_guild_policy``.

    Resolution precedence:

    1. Typed ``ai_guild_policy.default_provider`` / ``default_model``
       (when non-empty).
    2. Env / task routing target from :func:`resolve` (the input).
    3. Hardcoded :data:`routing._DEFAULT_MODELS` (already baked into
       ``target.model`` by the resolver).

    Missing typed row or DB read failure: keep ``target`` unchanged.
    Failure must never raise — the gateway contract requires that
    ``execute`` cannot raise to callers.
    """
    try:
        policy = await ai_db.get_guild_policy(guild_id)
    except Exception:  # noqa: BLE001 — DB failure is non-fatal here
        logger.warning(
            "ai gateway: ai_guild_policy read failed for guild_id=%s; "
            "keeping env / default routing",
            guild_id,
            exc_info=True,
        )
        return target
    if not policy:
        return target

    provider = (policy.get("default_provider") or "").strip()
    model = (policy.get("default_model") or "").strip()
    if not provider and not model:
        return target
    return RoutingTarget(
        provider=(provider or target.provider).lower(),
        model=model or target.model,
        timeout_seconds=target.timeout_seconds,
    )


class AIGateway:
    """Provider-neutral entry point for AI requests."""

    def __init__(
        self,
        *,
        providers: dict[str, Provider] | None = None,
        collector: DiagnosticsCollector | None = None,
    ) -> None:
        self._providers: dict[str, Provider] = providers or {
            "openai": OpenAIProvider(),
            "deterministic": DeterministicProvider(),
        }
        self._collector = collector or get_default_collector()

    def get_provider(self, name: str) -> Provider | None:
        return self._providers.get(name)

    def register_provider(self, provider: Provider) -> None:
        """Install or replace a provider by ``provider.name``."""
        self._providers[provider.name] = provider

    async def execute(
        self,
        request: AIRequest,
        *,
        provider_override: Provider | None = None,
    ) -> AIResponse:
        """Run a request through the pipeline; never raises."""
        target = resolve(request.context.task)
        if provider_override is None and request.context.guild_id is not None:
            target = await _overlay_guild_policy(target, request.context.guild_id)
        provider_name = provider_override.name if provider_override else target.provider

        if provider_override is None and not task_enabled(request.context.task):
            return _degraded_response(
                request,
                provider_name=provider_name,
                reason=f"feature_flag:disabled:{request.context.task.value}",
            )

        safety_reason = precheck(request)
        if safety_reason is not None:
            self._collector.record_failure(
                provider_active=provider_name,
                error_type="SafetyCheck",
                fallback_reason=safety_reason,
            )
            return _degraded_response(
                request,
                provider_name=provider_name,
                reason=safety_reason,
            )

        redacted_payload = _redact_payload(request.payload)
        redacted_system = _redact_string(request.system_prompt)
        redacted_request = AIRequest(
            context=request.context,
            system_prompt=redacted_system,
            payload=redacted_payload,
            mode=request.mode,
            response_schema=request.response_schema,
            max_output_tokens=request.max_output_tokens,
            timeout_seconds=request.timeout_seconds,
        )

        provider = provider_override or self._providers.get(target.provider)
        if provider is None:
            reason = f"provider_missing:{target.provider}"
            self._collector.record_failure(
                provider_active=target.provider,
                error_type="ProviderMissing",
                fallback_reason=reason,
            )
            return _degraded_response(
                request,
                provider_name=target.provider,
                reason=reason,
            )

        self._collector.record_request(provider_active=provider.name)
        timeout = request.timeout_seconds or target.timeout_seconds
        outcome = "success"
        started = time.perf_counter()
        try:
            raw_text = await asyncio.wait_for(
                provider.execute(redacted_request, model=target.model),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - started) * 1000.0
            outcome = "timeout"
            metrics.ai_request_total.labels(
                task=request.context.task.value,
                outcome=outcome,
            ).inc()
            metrics.ai_request_seconds.labels(
                task=request.context.task.value,
                provider=provider.name,
            ).observe(latency_ms / 1000.0)
            self._collector.record_failure(
                provider_active=provider.name,
                error_type="TimeoutError",
                fallback_reason=f"timeout:{timeout}s",
            )
            return _degraded_response(
                request,
                provider_name=provider.name,
                reason=f"timeout:{timeout}s",
                latency_ms=latency_ms,
            )
        except DeterministicFallbackError as exc:
            latency_ms = (time.perf_counter() - started) * 1000.0
            outcome = "deterministic"
            metrics.ai_request_total.labels(
                task=request.context.task.value,
                outcome=outcome,
            ).inc()
            metrics.ai_request_seconds.labels(
                task=request.context.task.value,
                provider=provider.name,
            ).observe(latency_ms / 1000.0)
            self._collector.record_failure(
                provider_active=provider.name,
                error_type="DeterministicFallbackError",
                fallback_reason=str(exc),
            )
            return _degraded_response(
                request,
                provider_name=provider.name,
                reason=f"provider={provider.name}",
                latency_ms=latency_ms,
            )
        except ProviderUnavailableError as exc:
            latency_ms = (time.perf_counter() - started) * 1000.0
            outcome = "unavailable"
            metrics.ai_request_total.labels(
                task=request.context.task.value,
                outcome=outcome,
            ).inc()
            metrics.ai_request_seconds.labels(
                task=request.context.task.value,
                provider=provider.name,
            ).observe(latency_ms / 1000.0)
            self._collector.record_failure(
                provider_active=provider.name,
                error_type=type(exc).__name__,
                fallback_reason=str(exc),
            )
            return _degraded_response(
                request,
                provider_name=provider.name,
                reason=str(exc),
                latency_ms=latency_ms,
            )
        except Exception as exc:  # noqa: BLE001 — provider exception boundary
            latency_ms = (time.perf_counter() - started) * 1000.0
            outcome = "error"
            metrics.ai_request_total.labels(
                task=request.context.task.value,
                outcome=outcome,
            ).inc()
            metrics.ai_request_seconds.labels(
                task=request.context.task.value,
                provider=provider.name,
            ).observe(latency_ms / 1000.0)
            logger.exception(
                "AI provider %r raised on task %s",
                provider.name,
                request.context.task.value,
            )
            self._collector.record_failure(
                provider_active=provider.name,
                error_type=type(exc).__name__,
                fallback_reason=f"{type(exc).__name__}: {exc}",
            )
            return _degraded_response(
                request,
                provider_name=provider.name,
                reason=f"{type(exc).__name__}: {exc}",
                latency_ms=latency_ms,
            )

        latency_ms = (time.perf_counter() - started) * 1000.0
        metrics.ai_request_total.labels(
            task=request.context.task.value,
            outcome=outcome,
        ).inc()
        metrics.ai_request_seconds.labels(
            task=request.context.task.value,
            provider=provider.name,
        ).observe(latency_ms / 1000.0)

        text: str | None = raw_text
        data: dict[str, Any] | None = None
        degraded = False
        fallback_reason: str | None = None
        if request.mode is AIResponseMode.JSON:
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                degraded = True
                fallback_reason = f"invalid_json:{exc}"
                self._collector.record_failure(
                    provider_active=provider.name,
                    error_type="JSONDecodeError",
                    fallback_reason=fallback_reason,
                )
            else:
                data = parsed if isinstance(parsed, dict) else {"value": parsed}
                self._collector.record_success(provider_active=provider.name)
        else:
            self._collector.record_success(provider_active=provider.name)

        return AIResponse(
            task=request.context.task,
            provider=provider.name,
            model=target.model,
            text=text,
            data=data,
            suggestions=(),
            latency_ms=latency_ms,
            degraded=degraded,
            fallback_reason=fallback_reason,
        )


_DEFAULT_GATEWAY: AIGateway | None = None


def get_default_gateway() -> AIGateway:
    """Process-wide singleton gateway. Lazy-initialised."""
    global _DEFAULT_GATEWAY
    if _DEFAULT_GATEWAY is None:
        _DEFAULT_GATEWAY = AIGateway()
    return _DEFAULT_GATEWAY


def reset_default_gateway() -> None:
    """Test seam — drop the singleton so tests start with a fresh gateway."""
    global _DEFAULT_GATEWAY
    _DEFAULT_GATEWAY = None

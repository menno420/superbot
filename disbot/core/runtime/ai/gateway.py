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
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from core.runtime.ai import redaction
from core.runtime.ai.contracts import AIRequest, AIResponse, AIResponseMode, AITask
from core.runtime.ai.diagnostics import DiagnosticsCollector, get_default_collector
from core.runtime.ai.feature_flags import ai_tools_enabled, task_enabled
from core.runtime.ai.providers import (
    AnthropicProvider,
    DeterministicFallbackError,
    DeterministicProvider,
    OpenAIProvider,
    Provider,
    ProviderUnavailableError,
)
from core.runtime.ai.providers.base import ToolDispatch, ToolHandler
from core.runtime.ai.routing import RoutingTarget, default_model_for, resolve
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


def _model_matches_provider(provider: str, model: str) -> bool:
    """True if ``model`` looks like it belongs to ``provider``'s family.

    A crude prefix check used to catch a stored model that can't work
    with the resolved provider — a stale cross-provider value
    (``gpt-4o-mini`` under ``anthropic``) or a typo'd id (``sonnet-4-6``
    instead of ``claude-sonnet-4-6``). Either 404s at the provider and
    degrades the response.

    Only the two real network providers are constrained; ``deterministic``
    (and any unknown provider) impose no constraint — deterministic
    ignores the model entirely. An empty model is treated as a match;
    "auto-pick" is handled by the caller.
    """
    if not model:
        return True
    if provider == "anthropic":
        return model.startswith("claude")
    if provider == "openai":
        return model.startswith("gpt")
    return True


async def _overlay_guild_policy(
    target: RoutingTarget,
    guild_id: int,
    task: AITask,
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

    provider = (policy.get("default_provider") or "").strip().lower()
    model = (policy.get("default_model") or "").strip()
    if not provider and not model:
        return target
    resolved_provider = provider or target.provider
    if model:
        resolved_model = model
    elif provider:
        # Provider overridden without an explicit model — pick that
        # provider's default for the task so an OpenAI model string never
        # reaches Anthropic (or vice versa).
        resolved_model = default_model_for(resolved_provider, task)
    else:
        resolved_model = target.model
    # Provider-aware safety net: a stored model that doesn't belong to the
    # resolved provider's family (stale cross-provider value, or a typo'd
    # id) would 404 at the provider. Fall back to the per-task default for
    # the resolved provider rather than forwarding a model that can't work.
    if not _model_matches_provider(resolved_provider, resolved_model):
        logger.warning(
            "ai gateway: guild=%s default_model=%r does not match provider "
            "%r; using the per-task default instead",
            guild_id,
            resolved_model,
            resolved_provider,
        )
        resolved_model = default_model_for(resolved_provider, task)
    return RoutingTarget(
        provider=resolved_provider,
        model=resolved_model,
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
            "anthropic": AnthropicProvider(),
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
        tool_handlers: Mapping[str, ToolHandler] | None = None,
        model_override: str | None = None,
    ) -> AIResponse:
        """Run a request through the pipeline; never raises.

        When ``tool_handlers`` is supplied, ``request.tools`` is
        non-empty, and ``feature_flags.ai_tools_enabled()`` is true, the
        gateway hands the provider a redaction-wrapped dispatch callback
        so the model can call those read-only tools. Tool outputs are
        redacted before they re-enter the model context, and tool faults
        are returned to the model as a JSON error string (the gateway's
        never-raise contract still holds).

        ``model_override`` forces a specific model for this call,
        independent of routing — used to pair a forced ``provider_override``
        with a model that provider actually serves (evals, A/B, fallback
        escalation). Defaults to the routed model.
        """
        target = resolve(request.context.task)
        if provider_override is None and request.context.guild_id is not None:
            target = await _overlay_guild_policy(
                target,
                request.context.guild_id,
                request.context.task,
            )
        provider_name = provider_override.name if provider_override else target.provider
        effective_model = model_override or target.model

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
        # Redact only the two free-text fields; ``replace`` carries every other field
        # (tools, tool_choice, tool_budget, and any field added later) through untouched,
        # so a new AIRequest field can never again be silently dropped at the redaction seam.
        redacted_request = replace(
            request,
            system_prompt=redacted_system,
            payload=redacted_payload,
        )

        provider = provider_override or self._providers.get(target.provider)
        if provider is None:
            reason = f"provider_missing:{target.provider}"
            # Surface this loudly: the usual cause is a typo in an
            # ``AI_ROUTING_*`` / ``AI_DEFAULT_PROVIDER`` env var pointing at
            # an unregistered provider, which otherwise silently degrades
            # every reply with no hint as to why.
            logger.warning(
                "ai gateway: resolved provider %r is not registered "
                "(known: %s); degrading. Check AI_DEFAULT_PROVIDER / "
                "AI_ROUTING_* configuration.",
                target.provider,
                ", ".join(sorted(self._providers)),
            )
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

        timeout = request.timeout_seconds or target.timeout_seconds
        response = await self._attempt(
            request,
            redacted_request,
            provider=provider,
            model=effective_model,
            timeout=timeout,
            tool_handlers=tool_handlers,
        )

        # Provider-fault fallback. When no explicit ``provider_override``
        # pins the provider and a distinct ``AI_FALLBACK_PROVIDER`` is
        # configured, retry once on a transport fault (timeout /
        # unavailable / provider exception) so a single-provider outage
        # does not take AI down for the whole guild. A bad-JSON degrade is
        # a model-output problem, not an outage, so it is not retried.
        if (
            provider_override is None
            and response.degraded
            and not (response.fallback_reason or "").startswith("invalid_json")
        ):
            fallback = self._resolve_fallback(target.provider, request.context.task)
            if fallback is not None:
                fb_provider, fb_model = fallback
                fb_response = await self._attempt(
                    request,
                    redacted_request,
                    provider=fb_provider,
                    model=fb_model,
                    timeout=timeout,
                    tool_handlers=tool_handlers,
                )
                if not fb_response.degraded:
                    return fb_response
        return response

    def _resolve_fallback(
        self,
        primary_provider: str,
        task: AITask,
    ) -> tuple[Provider, str] | None:
        """Resolve the configured fallback provider + model, or ``None``.

        Returns ``None`` when no fallback is configured, when it equals the
        primary provider, or when the named provider is not registered.
        """
        from core.runtime.ai.routing import fallback_provider

        name = fallback_provider()
        if not name or name == primary_provider:
            return None
        provider = self._providers.get(name)
        if provider is None:
            logger.warning(
                "ai gateway: AI_FALLBACK_PROVIDER=%r is not a registered "
                "provider; skipping fallback",
                name,
            )
            return None
        return provider, default_model_for(name, task)

    async def _attempt(
        self,
        request: AIRequest,
        redacted_request: AIRequest,
        *,
        provider: Provider,
        model: str,
        timeout: float,
        tool_handlers: Mapping[str, ToolHandler] | None,
    ) -> AIResponse:
        """Run one provider attempt and convert every fault to a degraded
        :class:`AIResponse`. Never raises — this is where the gateway's
        never-raise contract is enforced for a single provider call.
        """
        self._collector.record_request(provider_active=provider.name)
        dispatch: ToolDispatch | None = None
        if tool_handlers is not None and request.tools and ai_tools_enabled():
            dispatch = self._build_dispatch(
                redacted_request,
                tool_handlers,
                provider.name,
            )
        outcome = "success"
        started = time.perf_counter()
        try:
            # Only pass ``dispatch`` when tools are active so the no-tools
            # path stays identical to a provider with the legacy
            # ``execute(request, *, model)`` signature.
            if dispatch is None:
                provider_call = provider.execute(
                    redacted_request,
                    model=model,
                )
            else:
                provider_call = provider.execute(
                    redacted_request,
                    model=model,
                    dispatch=dispatch,
                )
            raw_text = await asyncio.wait_for(provider_call, timeout=timeout)
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
            model=model,
            text=text,
            data=data,
            suggestions=(),
            latency_ms=latency_ms,
            degraded=degraded,
            fallback_reason=fallback_reason,
        )

    def _build_dispatch(
        self,
        request: AIRequest,
        tool_handlers: Mapping[str, ToolHandler],
        provider_name: str,
    ) -> ToolDispatch:
        """Wrap ``tool_handlers`` in a redaction- and fault-safe dispatch.

        Only tools actually offered on ``request.tools`` are callable (a
        model that names an un-offered tool gets an error back). Each
        result is JSON-encoded and run through redaction before it
        re-enters the model context. Handler exceptions are converted to
        a JSON error string so the tool loop never breaks the gateway's
        never-raise contract.
        """
        offered = {spec.name for spec in request.tools}

        async def dispatch(name: str, arguments: dict[str, Any]) -> str:
            if name not in offered or name not in tool_handlers:
                return json.dumps({"error": "tool_not_available", "tool": name})
            try:
                result = await tool_handlers[name](arguments)
            except Exception as exc:  # noqa: BLE001 — tool faults must not break the loop
                logger.warning(
                    "ai gateway: tool %r raised: %s",
                    name,
                    exc,
                    exc_info=True,
                )
                self._collector.record_failure(
                    provider_active=provider_name,
                    error_type="ToolError",
                    fallback_reason=f"tool:{name}",
                )
                return json.dumps({"error": "tool_failed", "tool": name})
            payload = (
                result if isinstance(result, str) else json.dumps(result, default=str)
            )
            return _redact_string(payload)

        return dispatch


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

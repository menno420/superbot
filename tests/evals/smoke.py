"""Offline AI eval **smoke matrix** — the deterministic half of the versioned
eval/smoke record (P1-1).

The golden set (``tests/evals/cases.py``) probes *model quality* and needs live,
paid providers (``scripts/run_evals.py``). This matrix is its counterpart: it
proves the gateway's **deterministic contract** — the parts that must hold with
no model at all — and therefore runs in **normal CI** on every PR.

Each :class:`SmokeCase` drives the *real* :class:`AIGateway` pipeline with
**scripted providers** (no network) and asserts the observable contract across
seven dimensions:

* ``gate``         — global / per-task / tool kill switches degrade or withhold.
* ``fallback``     — a transport fault on the primary recovers on the configured
  fallback; a bad-JSON degrade does **not** (model-output problem, not outage);
  an explicit ``provider_override`` never triggers fallback.
* ``tool_dispatch``— an offered tool dispatches; an un-offered name is rejected;
  a faulting handler is contained (never raises).
* ``audit``        — every call updates the :class:`DiagnosticsCollector`
  snapshot (request/failure counts, last error, degraded flag) — the
  *operator-visibility* dimension the live harness's ``EvalOutcome`` can't see.
* ``safety``       — empty / oversized payloads short-circuit before any call.
* ``redaction``    — secrets are scrubbed **before** the provider boundary.
* ``config``       — an unregistered provider degrades loudly, not silently.

This complements (does not duplicate) ``tests/unit/runtime/ai/test_gateway.py``:
that pins the gateway *functions*; this is the **versioned matrix/record** —
rendered as one scorecard, runnable offline here and live via the golden set,
so a release has a single repeatable "AI contract proven at version X" artifact.

The runner is import-safe and DB-free (every request uses ``guild_id=None`` so
the guild-policy overlay never reads the database), so it works in CI and from
``scripts/run_evals.py --smoke`` with no credentials.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from tests.evals.harness import GradeResult

from core.runtime.ai import routing
from core.runtime.ai.contracts import (
    AIDiagnosticsSnapshot,
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
    AIToolSpec,
)
from core.runtime.ai.diagnostics import DiagnosticsCollector
from core.runtime.ai.gateway import AIGateway
from core.runtime.ai.providers.base import Provider, ProviderUnavailableError

# Date-stamped version of this matrix. Bump when cases are added/removed so a
# rendered scorecard names the contract revision it proves.
SMOKE_MATRIX_VERSION = "2026-06-14.1"

# Env keys the runner owns: cleared per case for hermeticity, then the case's
# own ``env`` is applied. Every ``AI_TASK_*`` / ``AI_ROUTING_*`` key currently
# set is also cleared (a booted bot or a sibling test may have left some).
_MANAGED_KEYS = (
    "AI_ENABLED",
    "AI_DEFAULT_PROVIDER",
    "AI_FALLBACK_PROVIDER",
    "AI_TOOLS_ENABLED",
    "AI_SERVER_MEMBER_LOOKUP_ENABLED",
    "SETUP_ADVISOR_PROVIDER",
)
_MANAGED_PREFIXES = ("AI_TASK_", "AI_ROUTING_")

_DEFAULT_SYSTEM_PROMPT = "You are SuperBot, a concise Discord assistant. Keep replies short."


# A redaction-test tool spec (offered to the model in tool cases).
_PROBE_TOOL = AIToolSpec(
    name="get_user_standing",
    description="Return the caller's level/standing in this guild.",
    parameters={"type": "object", "properties": {}},
)


# --------------------------------------------------------------------------- #
# Scripted provider — deterministic, network-free, introspectable.
# --------------------------------------------------------------------------- #
class ScriptedProvider:
    """Fake provider for the smoke matrix.

    Returns scripted text/JSON, *or* raises a configured exception (to drive the
    fault/fallback path), *or* calls one tool through the gateway-supplied
    ``dispatch`` and echoes the (already-redacted) dispatch result back as its
    text. Records the request and model it was handed so redaction and
    never-called can be asserted at the provider boundary.
    """

    def __init__(
        self,
        name: str,
        *,
        text: str = "ok",
        exc: BaseException | None = None,
        call_tool: str | None = None,
    ) -> None:
        self.name = name
        self._text = text
        self._exc = exc
        self._call_tool = call_tool
        self.received_request: AIRequest | None = None
        self.received_model: str | None = None
        self.dispatch_result: str | None = None

    async def execute(
        self,
        request: AIRequest,
        *,
        model: str,
        dispatch: Callable[[str, dict[str, Any]], Awaitable[str]] | None = None,
    ) -> str:
        self.received_request = request
        self.received_model = model
        if self._exc is not None:
            raise self._exc
        if self._call_tool is not None and dispatch is not None:
            self.dispatch_result = await dispatch(self._call_tool, {})
            return self.dispatch_result
        return self._text


def _recording_handlers(
    results: Mapping[str, Any],
    recorder: list[tuple[str, dict[str, Any]]],
) -> dict[str, Callable[[dict[str, Any]], Awaitable[Any]]]:
    """Build tool handlers that record each call, then return a canned result
    (or raise, when the canned value is an ``Exception`` — the faulting case)."""

    def _make(name: str, result: Any) -> Callable[[dict[str, Any]], Awaitable[Any]]:
        async def handler(arguments: dict[str, Any]) -> Any:
            recorder.append((name, dict(arguments)))
            if isinstance(result, BaseException):
                raise result
            return result

        return handler

    return {name: _make(name, result) for name, result in results.items()}


@contextmanager
def _isolated_ai_env(env: Mapping[str, str]):
    """Apply ``env`` over a cleared managed AI-env namespace; restore on exit."""
    keys = set(_MANAGED_KEYS)
    keys |= {k for k in os.environ if k.startswith(_MANAGED_PREFIXES)}
    keys |= set(env)
    saved = {k: os.environ.get(k) for k in keys}
    try:
        for key in keys:
            os.environ.pop(key, None)
        for key, value in env.items():
            os.environ[key] = value
        routing.clear_overrides()
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        routing.clear_overrides()


# --------------------------------------------------------------------------- #
# Case + result types.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SmokeResult:
    """Everything an expectation may inspect about one deterministic run."""

    response: Any  # AIResponse
    diagnostics: AIDiagnosticsSnapshot
    tool_calls: tuple[tuple[str, dict[str, Any]], ...]
    providers: Mapping[str, Provider]


Expectation = Callable[[SmokeResult], GradeResult]


@dataclass(frozen=True)
class SmokeCase:
    """One deterministic contract probe: env + request + scripted providers + an
    expectation over the observable outcome (response, audit snapshot, tools)."""

    id: str
    category: str
    description: str
    providers: Callable[[], dict[str, Provider]]
    expect: Expectation
    env: Mapping[str, str] = field(default_factory=dict)
    task: AITask = AITask.GENERAL_NL_ANSWER
    mode: AIResponseMode = AIResponseMode.TEXT
    user_text: str = "hello there"
    system_prompt: str = _DEFAULT_SYSTEM_PROMPT
    tools: tuple[AIToolSpec, ...] = ()
    tool_results: Mapping[str, Any] = field(default_factory=dict)
    provider_override: Callable[[], Provider | None] = lambda: None
    payload: Mapping[str, Any] | None = None


async def run_smoke_case(case: SmokeCase) -> tuple[SmokeResult, GradeResult]:
    """Run one case through the real gateway with scripted providers and grade it."""
    recorder: list[tuple[str, dict[str, Any]]] = []
    with _isolated_ai_env(case.env):
        collector = DiagnosticsCollector()
        providers = case.providers()
        gateway = AIGateway(providers=providers, collector=collector)
        handlers = _recording_handlers(case.tool_results, recorder) if case.tools else None
        request = AIRequest(
            context=AIRequestContext(
                task=case.task,
                scope=AIScope.USER,
                guild_id=None,  # skip the DB-backed guild-policy overlay
                actor_id=None,
                source="smoke",
            ),
            system_prompt=case.system_prompt,
            payload=dict(case.payload) if case.payload is not None else {"text": case.user_text},
            mode=case.mode,
            tools=case.tools,
        )
        response = await gateway.execute(
            request,
            tool_handlers=handlers,
            provider_override=case.provider_override(),
        )
        snapshot = collector.snapshot()
    result = SmokeResult(
        response=response,
        diagnostics=snapshot,
        tool_calls=tuple(recorder),
        providers=providers,
    )
    grade = case.expect(result)
    return result, grade


# --------------------------------------------------------------------------- #
# Expectation combinators (declarative, like ``graders.py``).
# --------------------------------------------------------------------------- #
def _ok() -> GradeResult:
    return GradeResult(True)


def all_(*expectations: Expectation) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        for expectation in expectations:
            grade = expectation(result)
            if not grade.passed:
                return grade
        return _ok()

    return check


def degraded_because(substring: str) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        reason = result.response.fallback_reason or ""
        if not result.response.degraded:
            return GradeResult(False, "expected degraded, got an answer")
        if substring not in reason:
            return GradeResult(False, f"reason {reason!r} lacks {substring!r}")
        return _ok()

    return check


def reason_startswith(prefix: str) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        reason = result.response.fallback_reason or ""
        if not reason.startswith(prefix):
            return GradeResult(False, f"reason {reason!r} does not start with {prefix!r}")
        return _ok()

    return check


def answered_by(provider_name: str) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        if result.response.degraded:
            return GradeResult(False, f"degraded: {result.response.fallback_reason}")
        if result.response.provider != provider_name:
            return GradeResult(
                False,
                f"served by {result.response.provider!r}, expected {provider_name!r}",
            )
        return _ok()

    return check


def attributed_to(provider_name: str) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        if result.response.provider != provider_name:
            return GradeResult(
                False,
                f"attributed to {result.response.provider!r}, want {provider_name!r}",
            )
        return _ok()

    return check


def text_contains(substring: str) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        text = result.response.text or ""
        if substring not in text:
            return GradeResult(False, f"text {text!r} lacks {substring!r}")
        return _ok()

    return check


def tool_dispatched(name: str) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        names = [called for called, _ in result.tool_calls]
        if name not in names:
            return GradeResult(False, f"tool {name!r} not dispatched (got {names})")
        return _ok()

    return check


def no_tool_dispatched() -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        if result.tool_calls:
            return GradeResult(False, f"unexpected tool dispatch: {result.tool_calls}")
        return _ok()

    return check


def audit(
    *,
    degraded: bool | None = None,
    min_failures: int | None = None,
    max_failures: int | None = None,
    min_requests: int | None = None,
    error_type: str | None = None,
    provider_active: str | None = None,
) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        snap = result.diagnostics
        if degraded is not None and snap.degraded != degraded:
            return GradeResult(False, f"audit.degraded={snap.degraded}, want {degraded}")
        if min_failures is not None and snap.failures_observed < min_failures:
            return GradeResult(False, f"audit.failures={snap.failures_observed} < {min_failures}")
        if max_failures is not None and snap.failures_observed > max_failures:
            return GradeResult(False, f"audit.failures={snap.failures_observed} > {max_failures}")
        if min_requests is not None and snap.requests_observed < min_requests:
            return GradeResult(False, f"audit.requests={snap.requests_observed} < {min_requests}")
        if error_type is not None and snap.last_error_type != error_type:
            return GradeResult(False, f"audit.error_type={snap.last_error_type!r}, want {error_type!r}")
        if provider_active is not None and snap.provider_active != provider_active:
            return GradeResult(
                False,
                f"audit.provider_active={snap.provider_active!r}, want {provider_active!r}",
            )
        return _ok()

    return check


def provider_untouched(name: str) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        provider = result.providers.get(name)
        received = getattr(provider, "received_request", "<absent>")
        if received is not None:
            return GradeResult(False, f"provider {name!r} was called (received {received!r})")
        return _ok()

    return check


def provider_received_scrubbed(name: str, *secrets: str) -> Expectation:
    def check(result: SmokeResult) -> GradeResult:
        provider = result.providers.get(name)
        received = getattr(provider, "received_request", None)
        if received is None:
            return GradeResult(False, f"provider {name!r} was never called")
        haystack = str(received.payload) + (received.system_prompt or "")
        leaked = [s for s in secrets if s in haystack]
        if leaked:
            return GradeResult(False, f"provider saw un-redacted secret(s): {leaked}")
        return _ok()

    return check


# --------------------------------------------------------------------------- #
# The matrix.
# --------------------------------------------------------------------------- #
def _one(name: str, **kwargs: Any) -> Callable[[], dict[str, Provider]]:
    """Factory that returns a single scripted provider registered under ``name``."""
    return lambda: {name: ScriptedProvider(name, **kwargs)}


_BIG_TEXT = "x" * 300_000  # exceeds the 256 KiB safety payload cap


SMOKE_CASES: list[SmokeCase] = [
    # --- gates: global / per-task / tool kill switches -------------------- #
    SmokeCase(
        id="gate.global_disabled",
        category="gate",
        description="AI_ENABLED off → degraded, provider never called.",
        env={},
        providers=_one("deterministic", text="should not run"),
        expect=all_(
            reason_startswith("feature_flag:disabled"),
            provider_untouched("deterministic"),
        ),
    ),
    SmokeCase(
        id="gate.task_disabled",
        category="gate",
        description="Per-task kill switch off → degraded even with AI_ENABLED on.",
        env={"AI_ENABLED": "1", "AI_TASK_GENERAL_NL_ANSWER_ENABLED": "0"},
        providers=_one("deterministic", text="should not run"),
        expect=all_(
            reason_startswith("feature_flag:disabled:general.nl_answer"),
            provider_untouched("deterministic"),
        ),
    ),
    SmokeCase(
        id="gate.tools_disabled_withholds_dispatch",
        category="gate",
        description="AI_TOOLS_ENABLED off → tools are never offered to the model.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "deterministic"},
        providers=_one("deterministic", text="answered without tools", call_tool="get_user_standing"),
        tools=(_PROBE_TOOL,),
        tool_results={"get_user_standing": {"level": 12}},
        expect=all_(answered_by("deterministic"), no_tool_dispatched()),
    ),
    # --- tool dispatch ---------------------------------------------------- #
    SmokeCase(
        id="tool.offered_tool_dispatches",
        category="tool_dispatch",
        description="With the tool gate on, an offered tool dispatches.",
        env={"AI_ENABLED": "1", "AI_TOOLS_ENABLED": "1", "AI_DEFAULT_PROVIDER": "deterministic"},
        providers=_one("deterministic", call_tool="get_user_standing"),
        tools=(_PROBE_TOOL,),
        tool_results={"get_user_standing": {"level": 12}},
        expect=all_(tool_dispatched("get_user_standing"), audit(degraded=False)),
    ),
    SmokeCase(
        id="tool.unoffered_tool_rejected",
        category="tool_dispatch",
        description="A tool the model names but that wasn't offered is rejected.",
        env={"AI_ENABLED": "1", "AI_TOOLS_ENABLED": "1", "AI_DEFAULT_PROVIDER": "deterministic"},
        providers=_one("deterministic", call_tool="not_offered"),
        tools=(_PROBE_TOOL,),
        tool_results={"get_user_standing": {"level": 12}},
        expect=all_(text_contains("tool_not_available"), no_tool_dispatched()),
    ),
    SmokeCase(
        id="tool.faulting_handler_contained",
        category="tool_dispatch",
        description="A tool handler that raises is contained — the gateway never raises.",
        env={"AI_ENABLED": "1", "AI_TOOLS_ENABLED": "1", "AI_DEFAULT_PROVIDER": "deterministic"},
        providers=_one("deterministic", call_tool="get_user_standing"),
        tools=(_PROBE_TOOL,),
        tool_results={"get_user_standing": RuntimeError("handler boom")},
        expect=all_(
            text_contains("tool_failed"),
            audit(degraded=False, error_type="ToolError", min_failures=1),
        ),
    ),
    # --- fallback cascade ------------------------------------------------- #
    SmokeCase(
        id="fallback.primary_fault_recovers",
        category="fallback",
        description="A transport fault on the primary recovers on the fallback provider.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "anthropic", "AI_FALLBACK_PROVIDER": "openai"},
        providers=lambda: {
            "anthropic": ScriptedProvider("anthropic", exc=ProviderUnavailableError("down")),
            "openai": ScriptedProvider("openai", text="recovered on fallback"),
        },
        expect=all_(
            answered_by("openai"),
            text_contains("recovered on fallback"),
            audit(min_failures=1),
        ),
    ),
    SmokeCase(
        id="fallback.no_env_stands",
        category="fallback",
        description="With no AI_FALLBACK_PROVIDER, the degraded primary response stands.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "anthropic"},
        providers=_one("anthropic", exc=ProviderUnavailableError("primary down")),
        expect=all_(degraded_because("primary down"), audit(degraded=True, min_failures=1)),
    ),
    SmokeCase(
        id="fallback.bad_json_not_retried",
        category="fallback",
        description="A bad-JSON degrade is a model-output problem, not an outage → no fallback.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "anthropic", "AI_FALLBACK_PROVIDER": "openai"},
        mode=AIResponseMode.JSON,
        providers=lambda: {
            "anthropic": ScriptedProvider("anthropic", text="this is not json"),
            "openai": ScriptedProvider("openai", text='{"would":"recover"}'),
        },
        expect=all_(
            degraded_because("invalid_json"),
            attributed_to("anthropic"),
            provider_untouched("openai"),
        ),
    ),
    SmokeCase(
        id="fallback.override_disables",
        category="fallback",
        description="An explicit provider_override never triggers fallback (the injection seam).",
        env={"AI_ENABLED": "1", "AI_FALLBACK_PROVIDER": "openai"},
        providers=_one("openai", text="should not be used"),
        provider_override=lambda: ScriptedProvider("forced", exc=RuntimeError("forced fault")),
        expect=all_(degraded_because("forced fault"), provider_untouched("openai")),
    ),
    # --- audit visibility ------------------------------------------------- #
    SmokeCase(
        id="audit.success_recorded",
        category="audit",
        description="A healthy call records a request, zero failures, not degraded.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "deterministic"},
        providers=_one("deterministic", text="all good"),
        expect=audit(degraded=False, min_requests=1, max_failures=0, provider_active="deterministic"),
    ),
    SmokeCase(
        id="audit.failure_recorded",
        category="audit",
        description="A provider fault is visible in the diagnostics snapshot.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "anthropic"},
        providers=_one("anthropic", exc=RuntimeError("kaboom")),
        expect=all_(
            audit(degraded=True, min_failures=1, error_type="RuntimeError"),
            degraded_because("kaboom"),
        ),
    ),
    # --- safety prechecks ------------------------------------------------- #
    SmokeCase(
        id="safety.empty_payload_degraded",
        category="safety",
        description="An empty user payload short-circuits before any provider call.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "deterministic"},
        providers=_one("deterministic", text="should not run"),
        payload={},
        expect=all_(degraded_because("empty payload"), provider_untouched("deterministic")),
    ),
    SmokeCase(
        id="safety.oversized_payload_degraded",
        category="safety",
        description="An oversized payload short-circuits on the safety cap.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "deterministic"},
        providers=_one("deterministic", text="should not run"),
        payload={"text": _BIG_TEXT},
        expect=all_(degraded_because("safety"), provider_untouched("deterministic")),
    ),
    # --- redaction at the provider boundary ------------------------------- #
    SmokeCase(
        id="redaction.secrets_scrubbed_before_provider",
        category="redaction",
        description="Secrets are scrubbed before the provider ever sees the payload.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "deterministic"},
        providers=_one("deterministic", text="ok"),
        payload={
            "text": "my key is sk-1234567890abcdefghi and email alice@example.com",
            "db": "postgres://user:secret@host/db",
        },
        expect=provider_received_scrubbed(
            "deterministic",
            "sk-1234567890abcdefghi",
            "alice@example.com",
            "postgres://user:secret@host/db",
        ),
    ),
    # --- config: unregistered provider ------------------------------------ #
    SmokeCase(
        id="config.provider_missing_degraded",
        category="config",
        description="A routed-but-unregistered provider degrades loudly, not silently.",
        env={"AI_ENABLED": "1", "AI_DEFAULT_PROVIDER": "nonesuch"},
        providers=_one("deterministic", text="registered but not routed to"),
        expect=all_(
            degraded_because("provider_missing:nonesuch"),
            audit(degraded=True, error_type="ProviderMissing", min_failures=1),
        ),
    ),
]


# --------------------------------------------------------------------------- #
# Report rendering — the versioned record.
# --------------------------------------------------------------------------- #
def render_report(graded: Sequence[tuple[SmokeCase, GradeResult]]) -> str:
    """Render a versioned scorecard for a smoke run."""
    total = len(graded)
    passed = sum(1 for _, grade in graded if grade.passed)
    lines = [
        "",
        f"AI Smoke Matrix (offline)  ·  v{SMOKE_MATRIX_VERSION}",
        "=" * 60,
    ]
    by_cat: dict[str, list[tuple[SmokeCase, GradeResult]]] = {}
    for case, grade in graded:
        by_cat.setdefault(case.category, []).append((case, grade))
    for category in sorted(by_cat):
        runs = by_cat[category]
        cat_pass = sum(1 for _, grade in runs if grade.passed)
        lines.append(f"\n[{category}]  {cat_pass}/{len(runs)} passed")
        for case, grade in runs:
            if not grade.passed:
                lines.append(f"      ✗ {case.id}  {grade.detail[:90]}")
    lines.append("\n" + "-" * 60)
    pct = (100.0 * passed / total) if total else 0.0
    lines.append(f"TOTAL  {passed}/{total}  ({pct:.0f}%)")
    return "\n".join(lines)


async def run_matrix() -> list[tuple[SmokeCase, GradeResult]]:
    """Run every smoke case and return ``(case, grade)`` pairs."""
    graded: list[tuple[SmokeCase, GradeResult]] = []
    for case in SMOKE_CASES:
        _result, grade = await run_smoke_case(case)
        graded.append((case, grade))
    return graded

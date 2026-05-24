"""Merged-main lifecycle-observability contract.

After the close-path PR queue lands, runtime lifecycle observability
lives in a single canonical wiring: lifecycle state in
``core.runtime.lifecycle``, execution in ``bot1.py``, embed
construction in ``services.webhook_reporter``, metrics in
``services.metrics``.  This invariant pins down that wiring so a
future contributor cannot quietly:

* re-introduce a parallel restart-only close driver
  (``restart_close_driver`` / ``_drive_close_on_restart_request`` /
  ``RESTART_CLOSE_TIMEOUT_SECONDS``),
* drop one of the lifecycle-webhook entry points the operator channel
  depends on (beginning / completed / timeout / startup summary),
* remove a Prometheus metric the dashboards rely on
  (``lifecycle_*``, ``runtime_lock_*``, ``webhook_*``),
* move cleanup ownership out of ``main()``'s finalizer into the
  close-driver (which would couple shutdown vs restart cleanup).

The contract is enforced via AST + attribute inspection so it runs in
under a second and surfaces a meaningful failure message at CI time.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

import bot1
from core.runtime import lifecycle
from services import metrics, webhook_reporter

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"
_BOT1_SRC = _DISBOT / "bot1.py"


# ---------------------------------------------------------------------------
# Webhook reporter surface — every lifecycle entry point operators expect.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "method_name",
    [
        "on_lifecycle_close_beginning",
        "on_lifecycle_close_completed",
        "on_lifecycle_close_timeout",
        "on_startup_summary",
    ],
)
def test_webhook_reporter_exposes_required_lifecycle_method(
    method_name: str,
) -> None:
    """Every operator-channel lifecycle signal must have a single
    canonical entry point on :class:`WebhookReporter`.  Removing one
    drops a signal from the operator channel and is a regression."""
    assert hasattr(webhook_reporter.WebhookReporter, method_name), (
        f"WebhookReporter must expose {method_name!r} so the "
        f"close-driver / finalizer have a single canonical entry "
        f"point.  Restore it or this invariant will fail CI."
    )
    method = getattr(webhook_reporter.WebhookReporter, method_name)
    assert inspect.iscoroutinefunction(method), (
        f"WebhookReporter.{method_name} must be an async method."
    )


# ---------------------------------------------------------------------------
# Metrics surface — every dashboard series the runbooks rely on.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "metric_name",
    [
        "lifecycle_phase",
        "lifecycle_event_total",
        "lifecycle_close_driver_total",
        "lifecycle_close_duration_seconds",
        "lifecycle_startup_seconds",
        "runtime_lock_heartbeat_total",
        "runtime_lock_heartbeat_seconds",
        "runtime_lock_boot_handoff_total",
        "runtime_lock_boot_wait_seconds",
        "webhook_dispatch_total",
        "webhook_dispatch_seconds",
    ],
)
def test_metrics_module_exposes_required_metric(metric_name: str) -> None:
    """The dashboards and runbooks reference these names directly.
    Removing one quietly is a contract break — the panel goes blank
    and the runbook step fails at the worst possible time.
    """
    assert hasattr(metrics, metric_name), (
        f"services.metrics.{metric_name} must remain exposed — "
        f"removing it breaks the dashboard / runbook that names it."
    )


# ---------------------------------------------------------------------------
# Production code must not re-introduce the restart-only close driver
# symbols that the generalised driver replaced.
# ---------------------------------------------------------------------------


_FORBIDDEN_LEGACY_SYMBOLS: tuple[str, ...] = (
    "restart_close_driver",
    "_drive_close_on_restart_request",
    "RESTART_CLOSE_TIMEOUT_SECONDS",
)


def test_production_code_does_not_resurrect_legacy_close_symbols() -> None:
    """The pre-merge close-path PRs generalised the restart-only close
    driver into a single shutdown-or-restart driver.  A future refactor
    must not re-introduce the old restart-only names — they would
    create a parallel lifecycle path that diverges from the merged
    contract."""
    offenders: dict[str, list[str]] = {}
    for path in _DISBOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(_REPO_ROOT))
        for symbol in _FORBIDDEN_LEGACY_SYMBOLS:
            if symbol in text:
                offenders.setdefault(rel, []).append(symbol)
    assert not offenders, (
        "Forbidden legacy close-driver symbols re-introduced. Remove "
        "them or migrate to the shared close-driver: "
        f"{offenders!r}"
    )


# ---------------------------------------------------------------------------
# AST-level contract: the close-driver must call the timeout webhook
# before os._exit(1), and must not own cleanup that belongs to main().
# ---------------------------------------------------------------------------


def _close_driver_ast() -> ast.AsyncFunctionDef:
    tree = ast.parse(_BOT1_SRC.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AsyncFunctionDef)
            and node.name == "_drive_close_on_lifecycle_request"
        ):
            return node
    raise AssertionError(
        "bot1._drive_close_on_lifecycle_request is missing — the "
        "close-driver must remain in bot1.py per the merged contract.",
    )


def _calls_in(node: ast.AST) -> list[ast.Call]:
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)]


def _call_dotted_name(call: ast.Call) -> str:
    """Render the called name as ``a.b.c`` if it's an attribute chain
    or a bare name, or ``""`` otherwise.  Sufficient for AST contract
    checks against a small, well-known set of names.
    """
    func = call.func
    parts: list[str] = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    return ".".join(reversed(parts))


def test_close_driver_calls_close_timeout_webhook_before_os_exit() -> None:
    """The timeout branch must post the dedicated timeout webhook
    before force-exiting.  Verified by walking the AST: every
    ``os._exit`` call appears AFTER an ``on_lifecycle_close_timeout``
    call in the source order of the same function body."""
    fn = _close_driver_ast()
    body_text = ast.unparse(fn)
    assert "on_lifecycle_close_timeout" in body_text, (
        "Close-driver must call reporter.on_lifecycle_close_timeout "
        "in the asyncio.TimeoutError branch before os._exit(1)."
    )
    assert "os._exit" in body_text, (
        "Close-driver must still force-exit on timeout — "
        "os._exit(1) is the contract handoff to the orchestrator."
    )
    # Source order: the timeout webhook call must precede the os._exit
    # call in the function body.  Use lineno because both live in the
    # same try/except branch.
    timeout_calls = [
        c for c in _calls_in(fn)
        if _call_dotted_name(c).endswith("on_lifecycle_close_timeout")
    ]
    exit_calls = [
        c for c in _calls_in(fn)
        if _call_dotted_name(c) in {"os._exit", "_exit"}
    ]
    assert timeout_calls, "expected on_lifecycle_close_timeout call"
    assert exit_calls, "expected os._exit call"
    assert min(c.lineno for c in timeout_calls) < min(
        c.lineno for c in exit_calls
    ), "on_lifecycle_close_timeout must be called before os._exit(1)"


# ---------------------------------------------------------------------------
# Cleanup ownership: the close-driver must NOT own finalizer cleanup.
# Those belong in main()'s finally block so shutdown vs restart share
# the same cleanup path without duplicating responsibility.
# ---------------------------------------------------------------------------


_DRIVER_FORBIDDEN_CALLS: tuple[str, ...] = (
    "db.close",
    "reporter.close",
    "release_lock_best_effort",
    "sys.exit",
    "os.execv",
)


def test_close_driver_does_not_own_finalizer_cleanup() -> None:
    """``main()``'s ``finally`` block is the canonical owner of:
      - the runtime-lock release (``release_lock_best_effort``),
      - the DB pool close (``db.close``),
      - the reporter HTTP teardown (``reporter.close``),
      - any process-exit primitive other than the timeout-branch
        ``os._exit`` (no ``sys.exit`` / ``os.execv`` in the driver).

    A driver that owns any of these forks shutdown vs restart cleanup,
    which is what the close-path PRs generalised away.  This invariant
    catches any reversal.
    """
    fn = _close_driver_ast()
    offenders: list[str] = []
    for call in _calls_in(fn):
        name = _call_dotted_name(call)
        for forbidden in _DRIVER_FORBIDDEN_CALLS:
            if name == forbidden or name.endswith(f".{forbidden}"):
                offenders.append(name)
    assert not offenders, (
        "Close-driver must not own finalizer cleanup. The merged "
        "contract reserves these for main()'s finally block: "
        f"{sorted(set(offenders))!r}"
    )


# ---------------------------------------------------------------------------
# Lifecycle module surface: startup-duration one-shot + metadata in
# diagnostics_snapshot.
# ---------------------------------------------------------------------------


def test_lifecycle_observes_startup_duration_one_shot() -> None:
    """The first STARTING → RUNNING transition observes the histogram
    exactly once per process.  A second RUNNING transition (e.g. after
    a gateway reconnect-driven on_ready) must not re-observe."""
    lifecycle.reset_for_tests()
    samples = list(metrics.lifecycle_startup_seconds.collect())[0].samples
    before_count = next(s.value for s in samples if s.name.endswith("_count"))

    lifecycle.set_phase(lifecycle.Phase.RUNNING, reason="on_ready")
    samples = list(metrics.lifecycle_startup_seconds.collect())[0].samples
    after_first = next(s.value for s in samples if s.name.endswith("_count"))
    assert after_first == before_count + 1, (
        "First STARTING → RUNNING must observe lifecycle_startup_seconds"
    )

    # Simulate a second on_ready: go DRAINING and back to RUNNING; the
    # observation must NOT increment again.
    lifecycle.set_phase(lifecycle.Phase.DRAINING)
    lifecycle.set_phase(lifecycle.Phase.RUNNING, reason="reconnect")
    samples = list(metrics.lifecycle_startup_seconds.collect())[0].samples
    after_second = next(s.value for s in samples if s.name.endswith("_count"))
    assert after_second == after_first, (
        "Second RUNNING transition must not re-observe the histogram — "
        "the startup metric is cold-boot health, not connection churn."
    )


def test_diagnostics_snapshot_includes_event_metadata_and_startup_state() -> None:
    """``diagnostics_snapshot`` is the single source of truth for the
    lifecycle embed + /lifecycle HTTP endpoint.  It must expose:
      - per-event ``metadata`` so the embed can render close-outcome
        kind / duration / timeout,
      - ``startup_duration_observed`` so operators can confirm the
        one-shot observation fired,
      - ``module_load_age_seconds`` for diagnosing late-RUNNING boots.
    """
    lifecycle.reset_for_tests()
    lifecycle.set_phase(lifecycle.Phase.RUNNING)
    lifecycle.request_shutdown("sigterm", actor="signal_handler")
    pending = lifecycle.get_pending()
    assert pending is not None
    lifecycle.record_close_executing(pending)
    lifecycle.record_close_completed(pending, duration_seconds=1.25)

    snap = lifecycle.diagnostics_snapshot()
    assert "startup_duration_observed" in snap
    assert snap["startup_duration_observed"] is True
    assert isinstance(snap.get("module_load_age_seconds"), float)
    completed = next(
        e for e in snap["recent_events"] if e["name"] == "close_completed"
    )
    assert completed["metadata"]["kind"] == "shutdown"
    assert completed["metadata"]["duration_seconds"] == pytest.approx(1.25)


def test_lifecycle_module_exposes_close_outcome_recorders() -> None:
    """Both outcome recorders must remain on the module surface — they
    are the canonical writers for the close_completed / close_timeout
    ring-buffer events."""
    assert hasattr(lifecycle, "record_close_completed")
    assert hasattr(lifecycle, "record_close_timeout")
    assert "record_close_completed" in lifecycle.__all__
    assert "record_close_timeout" in lifecycle.__all__


# ---------------------------------------------------------------------------
# Wiring: bot1 close-driver imports lifecycle helpers (smoke).
# ---------------------------------------------------------------------------


def test_bot1_module_uses_lifecycle_record_close_helpers() -> None:
    """The close-driver imports lifecycle as ``_lifecycle`` and must
    call the new outcome recorders.  This is a smoke check that the
    wiring did not regress to "metric-only, no ring-buffer event" or
    vice-versa."""
    body = _BOT1_SRC.read_text(encoding="utf-8")
    assert "_lifecycle.record_close_executing" in body
    assert "_lifecycle.record_close_completed" in body
    assert "_lifecycle.record_close_timeout" in body

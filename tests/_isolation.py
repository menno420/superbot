"""Central test-isolation registry for process-global state.

**Why this exists.** The bot has ~30 modules with module-level mutable state —
caches, registries, ledgers, the lifecycle phase, the event bus's subscriber
list. Each ships a ``_reset_for_tests`` / ``reset_for_tests`` hook, but
historically each hook was wired *ad hoc* in only the individual test files that
exercised it. That left gaps: a module mutated by test A (which never resets it)
and read by test B leaks across them. Serial collection hid the leak by accident
of ordering; under ``pytest -n auto`` it surfaced as **non-deterministic** failures
(a different subset failed each run — PR #815).

This module is the single place that classifies *every* such hook as either:

* **GLOBAL** (:data:`GLOBAL_RESET_HOOKS` + :data:`FEATURE_FLAGS_MODULE`) — reset
  before and after every test by the ``tests/conftest.py`` autouse fixture via
  :func:`apply_global_resets`. Only truly process-global, cheap-to-import,
  *baseline-safe* singletons go here: lazy ``_CACHED = None`` caches, empty-at-import
  maps, or proper reset-to-default hooks. Resetting these per test makes a test's
  starting state independent of execution order, and thus of xdist worker scheduling.

* **PER_FILE** (:data:`PER_FILE_RESET_HOOKS`) — deliberately *not* global. Two
  kinds: (1) import-populated registries, where a blanket wipe would drop the
  registrations made at import time and break readers (``feature_flags`` is the
  cautionary tale — its ``_reset_for_tests`` wipes the import-time default flag
  declarations, which is why it is handled by snapshot/restore below, not by a
  plain hook call); (2) heavier service-layer singletons whose state is localized
  to their own feature tests. These stay wired in the specific test files that
  need them.

**The guardrail.** ``tests/unit/invariants/test_global_state_isolation.py`` asserts
that every reset hook found in ``disbot/`` is classified here. A *new* hook fails
that test until it is added to one bucket or the other — so the #815 class ("a
module has a reset hook but nobody wired it suite-wide") cannot silently recur.

Promotion path: if a PER_FILE service singleton ever proves leak-prone under
parallel runs, move it into ``GLOBAL_RESET_HOOKS`` (and confirm its hook restores
the correct baseline rather than wiping import-time state).
"""

from __future__ import annotations

import importlib
from typing import Any

# ---------------------------------------------------------------------------
# GLOBAL — reset before/after every test (see apply_global_resets)
# ---------------------------------------------------------------------------

# (module dotted path under disbot/, reset attribute name). Each reset here is a
# *baseline-safe* operation: it restores the module to its import-time state
# (lazy caches → None, empty maps → empty, lifecycle → STARTING), so calling it
# per test never destroys legitimate import-time data.
GLOBAL_RESET_HOOKS: tuple[tuple[str, str], ...] = (
    ("core.runtime.lifecycle", "reset_for_tests"),
    ("core.runtime.startup_outcome", "reset_for_tests"),
    ("core.runtime.command_descriptions", "_reset_for_tests"),
    ("core.runtime.settings_registry", "_reset_for_tests"),
    ("core.runtime.command_surface_ledger", "_reset_for_tests"),
    ("core.runtime.command_manifest", "_reset_for_tests"),
    ("core.runtime.panel_manifest", "_reset_for_tests"),
    ("core.runtime.guild_config", "_reset_for_tests"),
    ("core.runtime.user_config", "_reset_for_tests"),
    ("core.runtime.scope_locks", "_reset_for_tests"),
    ("core.runtime.slow_path_log", "_reset_for_tests"),
    ("core.runtime.participation_capabilities", "_reset_for_tests"),
    ("core.runtime.subsystem_capabilities", "_reset_for_tests"),
    # Process-local media (YouTube) diagnostics counters + last-purge state.
    # No import-time registration — wiping to zero each test is baseline-safe
    # and prevents cross-file counter leakage under parallel runs.
    ("services.youtube_diagnostics", "_reset_for_tests"),
    # AI review-log answer registry (reply_message_id → remembered Q&A for
    # correction matching). Empty-at-import map, no import-time registration —
    # wiping each test is baseline-safe and prevents a remembered answer in one
    # test from matching a correction in another under parallel runs.
    ("services.ai_review_log_service", "_reset_for_tests"),
)

# feature_flags is global too, but its _reset_for_tests() *wipes* an
# import-populated registry (the Phase-1d default flag declarations), so it gets
# snapshot/restore handling in apply_global_resets rather than a hook call. Named
# here so the guardrail counts it as classified-GLOBAL.
FEATURE_FLAGS_MODULE = "core.runtime.feature_flags"


# ---------------------------------------------------------------------------
# PER_FILE — deliberately NOT reset globally (wired in their own test files)
# ---------------------------------------------------------------------------

# module dotted path -> reason. Kept so the guardrail can assert full coverage
# and so a future maintainer sees *why* each hook was excluded from the global
# fixture (and whether it is a promotion candidate).
PER_FILE_RESET_HOOKS: dict[str, str] = {
    # Import-populated registries: subsystem/feature modules register into these
    # at import time, so a per-test global wipe would drop those registrations
    # and break every reader. Their own tests clear+repopulate deliberately.
    "core.runtime.subsystem_schema": "import-populated schema registry; global wipe drops import-time schemas",
    "core.runtime.participation_schema": "import-populated schema registry; global wipe drops import-time schemas",
    "core.runtime.cleanup_registry": "import-populated provider registry",
    "core.runtime.ai.response_renderer_registry": "import-populated renderer registry",
    # Service-layer singletons: state localized to their own feature tests, and
    # heavier to import suite-wide. Wired per-file. Promote to GLOBAL only if one
    # ever leaks across files under a parallel run.
    "services.ai_conversation_service": "conversation cache; wired in AI conversation tests",
    "services.ai_natural_language_policy": "policy cache; wired in NL policy tests",
    "services.ai_orchestration_policy": "policy cache; wired in orchestration tests",
    "services.ai_permission_service": "permission cache; wired in AI permission tests",
    "services.btd6_fetch_service": "fetch cache; wired in BTD6 fetch tests",
    "services.btd6_grounding_service": "grounding cache; wired in BTD6 grounding tests",
    "services.btd6_source_parser": "parser cache; wired in BTD6 parser tests",
    "services.btd6_version_announce": "bus subscriber; wired in announce tests",
    "services.projmoon_grounding_service": "name-index cache; wired in projmoon grounding tests",
    "services.customization_catalogue": "catalogue cache; wired in customization tests",
    "services.diagnostics_service": "import-populated provider registry; wired in diagnostics tests",
    "services.paragon_service": "paragon cache; wired in paragon tests",
    "services.resource_provisioning_catalogue": "catalogue cache; wired in provisioning tests",
    # server_logging subscribes to the global EventBus in setup(); its
    # _reset_for_tests() now also detaches that subscription (PR #815) so the
    # leak dies at its source — wired in the server_logging tests.
    "services.server_logging": "bus subscriber + counters; wired in server_logging tests",
    "governance.role_templates": "import-populated template registry",
    "cogs.diagnostic._log_buffer": "diagnostic log buffer; wired in diagnostic panel tests",
}


def globally_reset_modules() -> set[str]:
    """Module dotted paths reset by :func:`apply_global_resets`."""
    return {module for module, _ in GLOBAL_RESET_HOOKS} | {FEATURE_FLAGS_MODULE}


def classified_modules() -> set[str]:
    """Every module classified here (GLOBAL ∪ PER_FILE) — used by the guardrail."""
    return globally_reset_modules() | set(PER_FILE_RESET_HOOKS)


def apply_global_resets(feature_flag_baseline: dict[str, Any] | None = None) -> None:
    """Reset every GLOBAL process-global singleton to its import-time baseline.

    Called before *and* after each test by the conftest autouse fixture so a
    test's starting state is independent of execution order (and therefore of
    xdist worker scheduling).

    ``feature_flag_baseline`` is the session-captured snapshot of
    ``feature_flags._REGISTRY`` (the import-time default declarations); it is
    restored rather than wiped. Pass ``None`` to skip the registry restore (still
    clears the evaluation cache + counter).
    """
    for module_path, attr in GLOBAL_RESET_HOOKS:
        module = importlib.import_module(module_path)
        getattr(module, attr)()

    from core.runtime import feature_flags

    if feature_flag_baseline is not None:
        feature_flags._REGISTRY.clear()
        feature_flags._REGISTRY.update(feature_flag_baseline)
    feature_flags._CACHE.clear()
    feature_flags._reset_metrics_for_tests()

"""Guardrail: every process-global reset hook in ``disbot/`` is classified.

The bot keeps module-level mutable state in many modules; each ships a
``_reset_for_tests`` / ``reset_for_tests`` hook for test isolation. PR #815 showed
that when such a hook is wired only in *some* test files, the underlying global can
leak across tests and break non-deterministically under ``pytest -n auto``.

``tests/_isolation.py`` is the single source of truth that classifies every hook as
GLOBAL (reset suite-wide by the conftest autouse fixture) or PER_FILE (wired in its
own tests). This test fails the moment a hook in ``disbot/`` is *not* classified —
forcing whoever adds new process-global state to make a deliberate decision instead
of silently reintroducing the #815 leak class.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests._isolation import (
    FEATURE_FLAGS_MODULE,
    GLOBAL_RESET_HOOKS,
    apply_global_resets,
    classified_modules,
    globally_reset_modules,
)

_DISBOT = Path(__file__).resolve().parents[3] / "disbot"
_HOOK_RE = re.compile(r"^def (?:_reset_for_tests|reset_for_tests)\b", re.MULTILINE)


def _module_path(py_file: Path) -> str:
    """``disbot/core/runtime/lifecycle.py`` -> ``core.runtime.lifecycle``."""
    rel = py_file.relative_to(_DISBOT).with_suffix("")
    return ".".join(rel.parts)


def _discover_reset_hooks() -> set[str]:
    """Every disbot module that defines a module-level test-reset hook."""
    found: set[str] = set()
    for py_file in _DISBOT.rglob("*.py"):
        if _HOOK_RE.search(py_file.read_text(encoding="utf-8")):
            found.add(_module_path(py_file))
    return found


def test_every_reset_hook_is_classified() -> None:
    """No reset hook may be unclassified — a new one forces a GLOBAL/PER_FILE call."""
    discovered = _discover_reset_hooks()
    classified = classified_modules()

    unclassified = discovered - classified
    assert not unclassified, (
        "These disbot modules define a test-reset hook but are not classified in "
        "tests/_isolation.py. Add each to GLOBAL_RESET_HOOKS (if it is a "
        "process-global, baseline-safe singleton) or PER_FILE_RESET_HOOKS (with a "
        f"reason): {sorted(unclassified)}"
    )


def test_no_stale_classification() -> None:
    """Every classified module must still exist + define a hook (catch typos/removals)."""
    discovered = _discover_reset_hooks()
    classified = classified_modules()

    stale = classified - discovered
    assert not stale, (
        "These modules are classified in tests/_isolation.py but no longer define a "
        f"reset hook in disbot/ — remove or fix the entry: {sorted(stale)}"
    )


def test_global_reset_hooks_resolve() -> None:
    """Each GLOBAL hook must import + expose its named reset attribute."""
    import importlib

    for module_path, attr in GLOBAL_RESET_HOOKS:
        module = importlib.import_module(module_path)
        assert callable(
            getattr(module, attr, None)
        ), f"{module_path}.{attr} is not callable — GLOBAL_RESET_HOOKS is stale"

    # feature_flags is handled specially (snapshot/restore) — pin the attributes
    # apply_global_resets relies on so a rename can't silently break isolation.
    ff = importlib.import_module(FEATURE_FLAGS_MODULE)
    assert hasattr(ff, "_REGISTRY") and hasattr(ff, "_CACHE")
    assert callable(getattr(ff, "_reset_metrics_for_tests", None))


def test_apply_global_resets_is_idempotent_and_safe() -> None:
    """Smoke: applying the global resets twice runs cleanly and clears state.

    Mirrors what the conftest autouse fixture does before/after every test.
    """
    from core.runtime import feature_flags

    baseline = dict(feature_flags._REGISTRY)
    # Pollute a couple of globals, then confirm a reset restores the baseline.
    feature_flags._CACHE[("x", None)] = ("on", "test", 0.0)

    apply_global_resets(baseline)
    apply_global_resets(baseline)  # idempotent

    assert feature_flags._CACHE == {}
    assert feature_flags._REGISTRY == baseline


def test_feature_flags_baseline_is_restored_not_wiped() -> None:
    """The #815 trap: feature_flags must keep its import-time defaults after reset.

    A naive ``feature_flags._reset_for_tests()`` wipes the registry empty; the
    global fixture must instead restore the baseline so flag-reading tests still
    see the declared defaults.
    """
    from core.runtime import feature_flags

    assert FEATURE_FLAGS_MODULE in globally_reset_modules()
    baseline = dict(feature_flags._REGISTRY)
    assert baseline, "expected import-time default flag declarations to be present"

    apply_global_resets(baseline)
    # The declared defaults survive the reset (not wiped to empty).
    assert feature_flags._REGISTRY == baseline

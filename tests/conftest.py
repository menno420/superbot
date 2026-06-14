"""Top-level test configuration.

Sets required environment variables before any disbot imports happen,
then validates and freezes the subsystem registry once per session.
All test subdirectories inherit this setup automatically.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Must be set before importing config.py, which validates at import time.
os.environ.setdefault("DISCORD_BOT_TOKEN_PRODUCTION", "TEST_TOKEN_PLACEHOLDER")

# conftest.py lives in tests/, so disbot/ is one level up.
_DISBOT = Path(__file__).parent.parent / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


@pytest.fixture(scope="session", autouse=True)
def validated_registry():
    """Validate and deep-freeze the real subsystem registry once per session."""
    from utils.subsystem_registry import validate_registry

    validate_registry()


@pytest.fixture(scope="session")
def _feature_flag_registry_baseline():
    """Snapshot the import-time feature-flag declarations once per session.

    ``feature_flags._REGISTRY`` is populated at module import (the Phase-1d
    default declarations), so the per-test reset must *restore* this
    baseline rather than wipe the registry empty — wiping would drop the
    defaults and break every test that reads a declared flag.
    """
    from core.runtime import feature_flags

    return dict(feature_flags._REGISTRY)


@pytest.fixture(autouse=True)
def _isolate_global_runtime_state(_feature_flag_registry_baseline):
    """Reset process-global runtime singletons before/after every test.

    The bot keeps several module-level singletons — the lifecycle phase,
    the startup-outcome ledger, and the feature-flag registry/cache — that
    one test can mutate and the next can read. Under serial collection the
    deterministic ordering happens to hide the leakage; under ``pytest-xdist``
    parallel scheduling a polluting test can land on the same worker *before*
    a reader with no reset between them, so the suite was not parallel-safe
    (a different subset failed each parallel run). Each of these modules
    already ships a test-reset hook — ``startup_outcome.reset_for_tests``'s
    docstring even asks for exactly this autouse fixture — they were just
    never wired suite-wide. Resetting before *and* after each test makes the
    starting state independent of execution order.
    """
    from core.runtime import feature_flags, lifecycle, startup_outcome

    def _restore() -> None:
        lifecycle.reset_for_tests()
        startup_outcome.reset_for_tests()
        # Restore the registry to its import-time baseline (not empty),
        # then clear the per-evaluation cache + bootstrap-fallback counter.
        feature_flags._REGISTRY.clear()
        feature_flags._REGISTRY.update(_feature_flag_registry_baseline)
        feature_flags._CACHE.clear()
        feature_flags._reset_metrics_for_tests()

    _restore()
    yield
    _restore()

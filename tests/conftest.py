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

    The bot keeps many module-level singletons — the lifecycle phase, the
    startup-outcome ledger, the feature-flag registry/cache, and a handful of
    runtime caches/ledgers — that one test can mutate and the next can read.
    Under serial collection the deterministic ordering happens to hide the
    leakage; under ``pytest-xdist`` parallel scheduling a polluting test can land
    on the same worker *before* a reader with no reset between them, so the suite
    was not parallel-safe (a different subset failed each parallel run — PR #815).

    The set of globally-reset modules is the single source of truth in
    ``tests/_isolation.py`` (``GLOBAL_RESET_HOOKS``); a guardrail test
    (``tests/unit/invariants/test_global_state_isolation.py``) ensures every
    reset hook in ``disbot/`` is classified there, so a new global-state module
    cannot silently go unwired. Resetting before *and* after each test makes a
    test's starting state independent of execution order.
    """
    from tests._isolation import apply_global_resets

    apply_global_resets(_feature_flag_registry_baseline)
    yield
    apply_global_resets(_feature_flag_registry_baseline)

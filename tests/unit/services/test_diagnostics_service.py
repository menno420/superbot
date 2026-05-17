"""Tests for services.diagnostics_service — O-1 registry scaffold."""

from __future__ import annotations

import pytest

from services import diagnostics_service


@pytest.fixture(autouse=True, scope="module")
def _ensure_primitives_imported():
    """Trigger import of every primitive so its self-registration runs.

    Primitives register their diagnostics provider at module-load time.
    pytest's test collection order is alphabetical and does not guarantee
    that any particular primitive has been imported by the time the first
    test runs.  This module-scoped fixture forces the imports once before
    any test in this file executes.
    """
    import core.runtime.guild_config  # noqa: F401
    import core.runtime.navigation_stack  # noqa: F401
    import core.runtime.persistent_views  # noqa: F401
    import core.runtime.scope_locks  # noqa: F401
    import core.runtime.tasks  # noqa: F401
    import governance.cache  # noqa: F401


@pytest.fixture(autouse=True)
def _isolated_registry():
    """Remove test-introduced entries after each test.

    Pre-existing entries (real primitive self-registrations) are
    preserved across tests so the self-registration assertions still
    see them.
    """
    names_before = set(diagnostics_service._PROVIDERS)
    yield
    for name in list(diagnostics_service._PROVIDERS):
        if name not in names_before:
            del diagnostics_service._PROVIDERS[name]


# ---------------------------------------------------------------------------
# register / unregister / snapshot
# ---------------------------------------------------------------------------


def test_register_and_snapshot_returns_provider_result():
    diagnostics_service.register("test_simple", lambda: {"hello": "world"})
    assert diagnostics_service.snapshot("test_simple") == {"hello": "world"}


def test_snapshot_unknown_name_raises_key_error_with_known_names_listed():
    with pytest.raises(KeyError) as excinfo:
        diagnostics_service.snapshot("does_not_exist")
    msg = str(excinfo.value)
    assert "does_not_exist" in msg
    assert "Known:" in msg


def test_register_can_be_called_twice_to_overwrite():
    diagnostics_service.register("test_overwrite", lambda: 1)
    diagnostics_service.register("test_overwrite", lambda: 2)
    assert diagnostics_service.snapshot("test_overwrite") == 2


def test_unregister_removes_provider():
    diagnostics_service.register("test_unreg", lambda: 42)
    diagnostics_service.unregister("test_unreg")
    with pytest.raises(KeyError):
        diagnostics_service.snapshot("test_unreg")


def test_unregister_unknown_name_is_noop():
    # No exception.
    diagnostics_service.unregister("never_was")


# ---------------------------------------------------------------------------
# snapshot_all
# ---------------------------------------------------------------------------


def test_snapshot_all_includes_registered_provider():
    diagnostics_service.register("test_all", lambda: "value")
    result = diagnostics_service.snapshot_all()
    assert result["test_all"] == "value"


def test_snapshot_all_isolates_provider_failures():
    """One broken provider must not blank the rest of the snapshot."""

    def bad() -> dict:
        raise RuntimeError("provider crashed")

    diagnostics_service.register("test_bad", bad)
    diagnostics_service.register("test_good", lambda: {"ok": True})
    result = diagnostics_service.snapshot_all()
    assert result["test_good"] == {"ok": True}
    assert "_error" in result["test_bad"]
    assert "RuntimeError" in result["test_bad"]["_error"]
    assert "provider crashed" in result["test_bad"]["_error"]


def test_registered_names_is_sorted():
    diagnostics_service.register("test_zzz", lambda: 0)
    diagnostics_service.register("test_aaa", lambda: 0)
    names = diagnostics_service.registered_names()
    test_names = [n for n in names if n.startswith("test_")]
    assert test_names == sorted(test_names)


# ---------------------------------------------------------------------------
# Self-registration sanity checks (primitives register at import time)
# ---------------------------------------------------------------------------


def test_guild_config_self_registered():
    # Importing the primitive triggers self-registration.
    from core.runtime import guild_config  # noqa: F401

    snap = diagnostics_service.snapshot("guild_config")
    assert "size" in snap
    assert "versions_tracked" in snap


def test_scope_locks_self_registered():
    from core.runtime import scope_locks  # noqa: F401

    snap = diagnostics_service.snapshot("scope_locks")
    assert "total" in snap
    assert "held" in snap
    assert "by_prefix" in snap


def test_navigation_stack_self_registered():
    from core.runtime import navigation_stack  # noqa: F401

    snap = diagnostics_service.snapshot("navigation_stack")
    assert "active_locks" in snap


def test_tasks_self_registered():
    from core.runtime import tasks  # noqa: F401

    snap = diagnostics_service.snapshot("tasks")
    assert "active_count" in snap
    assert "names" in snap


def test_persistent_views_self_registered():
    from core.runtime import persistent_views  # noqa: F401

    snap = diagnostics_service.snapshot("persistent_views")
    assert "registered_count" in snap
    assert "subsystems" in snap


def test_governance_cache_self_registered():
    from governance import cache  # noqa: F401

    snap = diagnostics_service.snapshot("governance_cache")
    assert "size" in snap
    assert "guilds_versioned" in snap


def test_all_six_primitives_appear_in_registered_names():
    # Ensure imports have happened.
    import core.runtime.guild_config  # noqa: F401
    import core.runtime.navigation_stack  # noqa: F401
    import core.runtime.persistent_views  # noqa: F401
    import core.runtime.scope_locks  # noqa: F401
    import core.runtime.tasks  # noqa: F401
    import governance.cache  # noqa: F401

    names = set(diagnostics_service.registered_names())
    expected = {
        "guild_config",
        "scope_locks",
        "navigation_stack",
        "tasks",
        "persistent_views",
        "governance_cache",
    }
    assert expected.issubset(names), f"Missing: {expected - names}"

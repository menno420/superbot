"""Phase 1a + 1b unit tests — capability decorator metadata semantics.

The decorators in :mod:`core.runtime.subsystem_capabilities` and
:mod:`core.runtime.participation_capabilities` are metadata-only —
verifying they preserve call semantics, record qualnames, and keep the
guild-level vs user-level namespaces strictly separate.
"""

from __future__ import annotations

import pytest

from core.runtime import participation_capabilities, subsystem_capabilities


@pytest.fixture
def _clean_caps():
    subsystem_capabilities._reset_for_tests()
    participation_capabilities._reset_for_tests()
    try:
        yield
    finally:
        subsystem_capabilities._reset_for_tests()
        participation_capabilities._reset_for_tests()


def test_capability_decorator_preserves_call(_clean_caps):
    @subsystem_capabilities.capability("alpha.resource.act")
    def f(x: int) -> int:
        return x + 1

    assert f(1) == 2
    assert f.__capability__ == "alpha.resource.act"


def test_user_capability_decorator_preserves_call(_clean_caps):
    @participation_capabilities.user_capability("user.alpha.toggle")
    def g(x: int) -> int:
        return x * 2

    assert g(3) == 6
    assert g.__user_capability__ == "user.alpha.toggle"


def test_capability_records_usage(_clean_caps):
    @subsystem_capabilities.capability("alpha.resource.act")
    def f():
        pass

    usages = subsystem_capabilities.get_capability_usages()
    assert "alpha.resource.act" in usages
    assert len(usages["alpha.resource.act"]) == 1
    qualname = usages["alpha.resource.act"][0]
    assert "test_capability_decorators" in qualname
    assert qualname.endswith(".f")


def test_capability_namespace_is_separate_from_user(_clean_caps):
    @subsystem_capabilities.capability("alpha.resource.act")
    def f():
        pass

    @participation_capabilities.user_capability("user.alpha.toggle")
    def g():
        pass

    sub_usages = subsystem_capabilities.get_capability_usages()
    user_usages = participation_capabilities.get_user_capability_usages()

    assert "alpha.resource.act" in sub_usages
    assert "alpha.resource.act" not in user_usages
    assert "user.alpha.toggle" in user_usages
    assert "user.alpha.toggle" not in sub_usages


def test_capability_re_application_dedupes(_clean_caps):
    @subsystem_capabilities.capability("alpha.resource.act")
    @subsystem_capabilities.capability("alpha.resource.act")
    def f():
        pass

    usages = subsystem_capabilities.get_capability_usages()
    # Re-applying the same capability on the same callable records once.
    matching = [q for q in usages.get("alpha.resource.act", []) if q.endswith(".f")]
    assert len(matching) == 1

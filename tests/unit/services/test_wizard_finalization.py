"""Setup-wizard finalization readiness rollup — setup-wizard PR1/PR3."""

from __future__ import annotations

import pytest

from services import wizard_finalization


def test_statuses_returns_every_item():
    states = wizard_finalization.statuses()
    ids = {s.id for s in states}
    assert ids == {
        "fallback_attribution",
        "ai_advisor_review",
        "preflight_gate_visible",
        "provisioning_availability_gate",
    }
    assert len(states) == len(wizard_finalization.ITEMS)


def test_fallback_attribution_is_resolved():
    """PR1 ships the attribution capability, so this item is resolved."""
    states = {s.id: s for s in wizard_finalization.statuses()}
    assert states["fallback_attribution"].status == "resolved"


def test_provisioning_gate_is_deferred():
    states = {s.id: s for s in wizard_finalization.statuses()}
    assert states["provisioning_availability_gate"].status == "deferred"


# ---------------------------------------------------------------------------
# PR3 capability detection (find_spec / hasattr — house style)
# ---------------------------------------------------------------------------


def test_ai_advisor_review_resolved_when_module_present():
    """PR3 adds services.setup_advisor_review.review_draft, so the item
    resolves via the capability seam."""
    states = {s.id: s for s in wizard_finalization.statuses()}
    assert states["ai_advisor_review"].status == "resolved"


def test_preflight_gate_resolved_when_capability_present():
    """PR3 adds services.setup_operations.preflight_gate_state, so the item
    resolves via hasattr."""
    states = {s.id: s for s in wizard_finalization.statuses()}
    assert states["preflight_gate_visible"].status == "resolved"


def test_ai_advisor_in_progress_when_capability_missing(monkeypatch):
    """If the review module loses its review_draft symbol, the detector
    degrades to in_progress rather than claiming resolved."""
    import services.setup_advisor_review as sar

    monkeypatch.delattr(sar, "review_draft", raising=False)
    states = {s.id: s for s in wizard_finalization.statuses()}
    assert states["ai_advisor_review"].status == "in_progress"


def test_preflight_in_progress_when_capability_missing(monkeypatch):
    import services.setup_operations as so

    monkeypatch.delattr(so, "preflight_gate_state", raising=False)
    states = {s.id: s for s in wizard_finalization.statuses()}
    assert states["preflight_gate_visible"].status == "in_progress"


def test_status_for_is_failsafe_on_raising_provider():
    def boom() -> wizard_finalization.ItemStatus:
        raise RuntimeError("provider exploded")

    bad = wizard_finalization.FinalizationItem(
        id="bad",
        summary="",
        pr="PRX",
        status_provider=boom,
    )
    assert wizard_finalization.status_for(bad) == "unknown"


# ---------------------------------------------------------------------------
# Collector integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collector_section_is_informational():
    from services import platform_consistency as pc

    result = await pc._collect_wizard_finalization()
    assert result.name == "Wizard finalization"
    assert result.informational is True
    # Never a FATAL — informational rollups must not block rollout.
    assert result.status in (pc.SectionStatus.CLEAN, pc.SectionStatus.WARNING)


@pytest.mark.asyncio
async def test_collector_lists_every_item_in_details():
    from services import platform_consistency as pc

    result = await pc._collect_wizard_finalization()
    joined = "\n".join(result.details)
    for item in wizard_finalization.ITEMS:
        assert item.id in joined

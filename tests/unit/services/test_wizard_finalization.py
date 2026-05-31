"""Setup-wizard finalization readiness rollup — setup-wizard PR1."""

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


def test_cross_pr_items_pending_until_provider_registered():
    """ai_advisor_review and preflight_gate_visible resolve only once PR3
    registers their diagnostics providers — pending by default."""
    from services import diagnostics_service

    # Ensure a clean baseline (another test may have registered these).
    diagnostics_service.unregister("setup_ai_advisor")
    diagnostics_service.unregister("setup_preflight")
    states = {s.id: s for s in wizard_finalization.statuses()}
    assert states["ai_advisor_review"].status == "pending"
    assert states["preflight_gate_visible"].status == "pending"


def test_ai_advisor_resolves_when_provider_registered():
    from services import diagnostics_service

    diagnostics_service.register("setup_ai_advisor", lambda: {})
    try:
        states = {s.id: s for s in wizard_finalization.statuses()}
        assert states["ai_advisor_review"].status == "resolved"
    finally:
        diagnostics_service.unregister("setup_ai_advisor")


def test_preflight_resolves_when_provider_registered():
    from services import diagnostics_service

    diagnostics_service.register("setup_preflight", lambda: {})
    try:
        states = {s.id: s for s in wizard_finalization.statuses()}
        assert states["preflight_gate_visible"].status == "resolved"
    finally:
        diagnostics_service.unregister("setup_preflight")


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

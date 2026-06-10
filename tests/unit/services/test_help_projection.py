"""Contract tests for the Help projection seam (HLP-2 Phase 2).

These pin the projection contract the five Help render paths consume:

* the audit §9 state vocabulary, exactly;
* hiding semantics — only ``display_hidden`` / ``governance_hidden`` hide;
  the lock states (``routed_off`` / ``command_locked`` / ``unavailable``)
  stay advertised (HLP-4: display-only hiding is never execution denial);
* ``from_visibility`` — governance is the one hiding owner;
* ``registry_defaults`` — byte-equivalent to the legacy tier-only Home rule
  when governance has no overrides (the compatibility pin);
* the shared command display filter (one policy for every command surface);
* the execution-axes enrichment over ``project_access_map``.
"""

from __future__ import annotations

import pytest
from discord.ext import commands

from governance.models import VisibilityResult
from services.access_projection import (
    AccessAxis,
    AccessContext,
    AccessDecision,
    AxisOutcome,
    LockedReason,
)
from services.help_projection import (
    HelpEntryState,
    HelpProjection,
    command_display_state,
    is_command_displayable,
    project_help_with_execution,
)
from utils.hub_registry import HUBS, hubs_for_tier
from utils.subsystem_registry import SUBSYSTEMS, all_subsystems_sorted

_ALL = set(SUBSYSTEMS)


def _vis(visible: set[str], tier: str = "user") -> VisibilityResult:
    return VisibilityResult(
        visible_subsystems=visible,
        member_tier=tier,
        resolved_from={},
        traces={},
    )


def _command(name: str, **kwargs) -> commands.Command:
    async def _cb(ctx):  # pragma: no cover — never invoked
        return None

    return commands.Command(_cb, name=name, **kwargs)


# ---------------------------------------------------------------------------
# Contract vocabulary
# ---------------------------------------------------------------------------


def test_state_vocabulary_is_exactly_the_audit_set():
    assert {s.value for s in HelpEntryState} == {
        "shown",
        "display_hidden",
        "governance_hidden",
        "routed_off",
        "command_locked",
        "unavailable",
        "orphaned_override",
    }


def test_only_display_and_governance_states_hide():
    hiding = {state for state in HelpEntryState if not _decision_with(state).advertised}
    assert hiding == {
        HelpEntryState.DISPLAY_HIDDEN,
        HelpEntryState.GOVERNANCE_HIDDEN,
    }


def _decision_with(state: HelpEntryState):
    from services.help_projection import HelpDecision

    return HelpDecision(key="x", kind="subsystem", state=state)


# ---------------------------------------------------------------------------
# from_visibility — governance is the hiding owner
# ---------------------------------------------------------------------------


def test_full_visibility_shows_every_subsystem():
    projection = HelpProjection.from_visibility(_vis(_ALL, "administrator"))
    assert all(d.state is HelpEntryState.SHOWN for d in projection.subsystems)
    assert projection.source == "governance"


def test_governance_hidden_subsystem_carries_reason_and_hides():
    projection = HelpProjection.from_visibility(_vis(_ALL - {"ai"}, "administrator"))
    decision = projection.subsystem_decision("ai")
    assert decision is not None
    assert decision.state is HelpEntryState.GOVERNANCE_HIDDEN
    assert decision.reason_code == "subsystem_hidden"
    assert not decision.advertised
    assert not projection.is_subsystem_advertised("ai")


def test_hub_hides_when_host_subsystem_is_governance_hidden():
    """The Home unification: a hub whose same-key host subsystem is hidden
    in this scope disappears from Home (pre-seam Home ignored the resolved
    set entirely — audit §3)."""
    projection = HelpProjection.from_visibility(_vis(_ALL - {"games"}, "user"))
    decision = projection.hub_decision("games")
    assert decision is not None
    assert decision.state is HelpEntryState.GOVERNANCE_HIDDEN
    assert decision.reason_code == "subsystem_hidden"
    assert "games" not in {h.key for h in projection.visible_hubs()}
    # Other user hubs are unaffected.
    assert projection.is_hub_advertised("economy")


def test_hub_tier_floor_still_applies():
    projection = HelpProjection.from_visibility(_vis(_ALL, "user"))
    decision = projection.hub_decision("settings")
    assert decision is not None
    assert decision.state is HelpEntryState.GOVERNANCE_HIDDEN
    assert decision.reason_code == "tier_floor"


def test_unknown_tier_string_degrades_to_user_floor():
    projection = HelpProjection.from_visibility(_vis(_ALL, "everyone"))
    visible = {h.key for h in projection.visible_hubs()}
    assert visible == {h.key for h in hubs_for_tier("user")}


def test_advanced_list_matches_the_legacy_expression():
    """advanced_subsystems() == the exact list Advanced derived before the
    seam: governance-visible, top-level, ui_priority order."""
    narrowed = _ALL - {"ai", "blackjack"}
    projection = HelpProjection.from_visibility(_vis(narrowed, "administrator"))
    legacy = [
        name
        for name, meta in all_subsystems_sorted()
        if name in narrowed and not meta.get("parent_hub")
    ]
    assert projection.advanced_subsystems() == legacy
    # Children never appear even when governance-visible.
    assert "blackjack" not in projection.advanced_subsystems()


# ---------------------------------------------------------------------------
# registry_defaults — the legacy Home rule equivalence (compatibility pin)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tier", ["user", "moderator", "administrator", "owner"])
def test_registry_defaults_home_equals_legacy_hubs_for_tier(tier):
    """With no governance overrides, the projection's Home output is
    byte-equivalent to the pre-seam ``hubs_for_tier`` rule at every tier."""
    projection = HelpProjection.registry_defaults(tier)
    assert projection.source == "registry_defaults"
    assert [h.key for h in projection.visible_hubs()] == [
        h.key for h in hubs_for_tier(tier)
    ]


def test_registry_defaults_admin_tier_shows_all_hubs():
    """Q-0074: the Admin hub (administrator placement, administrator host
    tier) renders for administrators — registry defaults and governance
    can no longer disagree about it."""
    projection = HelpProjection.registry_defaults("administrator")
    assert {h.key for h in projection.visible_hubs()} == {h.key for h in HUBS}


# ---------------------------------------------------------------------------
# Command display decision — one filter for every command surface
# ---------------------------------------------------------------------------


def test_command_display_matrix():
    shown = _command("normal")
    assert command_display_state(shown).state is HelpEntryState.SHOWN
    assert is_command_displayable(shown)

    hidden = _command("ghost", hidden=True)
    decision = command_display_state(hidden)
    assert decision.state is HelpEntryState.DISPLAY_HIDDEN
    assert decision.reason_code == "discord_hidden"

    disabled = _command("off")
    disabled.enabled = False
    assert command_display_state(disabled).reason_code == "disabled"

    legacy = _command("old", extras={"classification": "legacy_duplicate"})
    assert command_display_state(legacy).reason_code == "classification_hidden"

    ledger_hidden = _command("internal", extras={"classification": "hidden"})
    assert not is_command_displayable(ledger_hidden)

    # Deprecated commands stay visible (they render with a badge — the
    # ledger's documented policy).
    deprecated = _command("olde", extras={"classification": "deprecated"})
    assert is_command_displayable(deprecated)


# ---------------------------------------------------------------------------
# Execution enrichment — lock states stay advertised
# ---------------------------------------------------------------------------


def _access_decision(
    feature: str,
    effective: str,
    axis: AccessAxis | None = None,
    reason_code: str | None = None,
) -> AccessDecision:
    return AccessDecision(
        feature=feature,
        command_name=None,
        effective=effective,  # type: ignore[arg-type]
        deciding_axis=axis,
        reason=(
            LockedReason(code=reason_code, safe_text="x", source="t")
            if reason_code
            else None
        ),
        source_chain=(AxisOutcome(AccessAxis.GOVERNANCE, "allow"),),
    )


async def test_enrichment_maps_axis_denials_to_lock_states(monkeypatch):
    fake = {
        "games": _access_decision(
            "games",
            "deny",
            AccessAxis.ROUTING,
            "routing_disabled",
        ),
        "economy": _access_decision(
            "economy",
            "deny",
            AccessAxis.COMMAND_ACCESS,
            "channel_not_allowed",
        ),
        "moderation": _access_decision(
            "moderation",
            "deny",
            AccessAxis.GOVERNANCE,
            "subsystem_hidden",
        ),
        "utility": _access_decision(
            "utility",
            "deny",
            AccessAxis.AVAILABILITY,
            "quiet_mode",
        ),
    }

    async def fake_map(ctx):
        return tuple(
            fake.get(name, _access_decision(name, "allow")) for name in SUBSYSTEMS
        )

    import services.access_projection as ap

    monkeypatch.setattr(ap, "project_access_map", fake_map)

    projection = await project_help_with_execution(
        AccessContext(guild_id=1, channel_id=2, member_tier="user"),
    )
    assert projection.source == "access_projection"

    by_key = {d.key: d for d in projection.subsystems}
    assert by_key["games"].state is HelpEntryState.ROUTED_OFF
    assert by_key["games"].reason_code == "routing_disabled"
    assert by_key["economy"].state is HelpEntryState.COMMAND_LOCKED
    assert by_key["moderation"].state is HelpEntryState.GOVERNANCE_HIDDEN
    assert by_key["utility"].state is HelpEntryState.UNAVAILABLE

    # Lock states stay advertised; only the governance denial hides.
    assert by_key["games"].advertised
    assert by_key["economy"].advertised
    assert by_key["utility"].advertised
    assert not by_key["moderation"].advertised

    # The routed-off Games hub still shows on Home (advertise-locked);
    # a governance-denied host would hide its hub.
    assert projection.is_hub_advertised("games")
    assert not projection.is_hub_advertised("moderation")


async def test_enrichment_unknown_projects_as_shown(monkeypatch):
    async def fake_map(ctx):
        return tuple(
            _access_decision(name, "unknown" if name == "xp" else "allow")
            for name in SUBSYSTEMS
        )

    import services.access_projection as ap

    monkeypatch.setattr(ap, "project_access_map", fake_map)

    projection = await project_help_with_execution(
        AccessContext(guild_id=1, member_tier="user"),
    )
    decision = projection.subsystem_decision("xp")
    assert decision is not None
    assert decision.state is HelpEntryState.SHOWN
    assert decision.detail == "effective=unknown"


async def test_enrichment_requires_declared_tier():
    with pytest.raises(ValueError, match="member_tier"):
        await project_help_with_execution(AccessContext(guild_id=1))

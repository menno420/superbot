"""Access Map + Help Preview subpanels (Adaptive P1C, Batch 5).

Pins the P1C contract: staff-only authority re-checked at **callback**
time, display-only (zero writes — the module may not even import a
mutation seam), the §16.4 simulation-limit label on every rendering, and
honest help buckets (advertised / shown-as-locked / hidden).
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.access_projection import (
    AccessAxis,
    AccessDecision,
    AxisOutcome,
    LockedReason,
)
from services.help_projection import HelpDecision, HelpEntryState
from views.server_management.access_map import (
    SIMULATION_LIMIT_NOTE,
    AccessMapView,
    HelpPreviewView,
    build_access_map_embed,
    build_help_preview_embed,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _decision(
    feature: str,
    effective: str = "allow",
    *,
    help_state: str = "shown",
    reason_code: str | None = None,
    safe_text: str = "This feature is turned off here.",
) -> AccessDecision:
    reason = None
    deciding = None
    if effective == "deny":
        deciding = AccessAxis.ROUTING
        reason = LockedReason(
            code=reason_code or "feature_routed_off",
            safe_text=safe_text,
            source="routing",
        )
    return AccessDecision(
        feature=feature,
        command_name=feature,
        effective=effective,  # type: ignore[arg-type]
        deciding_axis=deciding,
        reason=reason,
        source_chain=(
            AxisOutcome(
                axis=AccessAxis.ROUTING,
                state="allow" if effective != "deny" else "deny",
                detail="routing detail",
            ),
            AxisOutcome(axis=AccessAxis.HELP, state=help_state),  # type: ignore[arg-type]
        ),
        remediation="Server Management → Setup" if effective == "deny" else None,
    )


def _interaction(*, admin: bool = True) -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.channel = MagicMock()
    interaction.channel.id = 5
    interaction.user = MagicMock()
    interaction.user.id = 1
    interaction.user.guild_permissions = MagicMock(administrator=admin)
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    return interaction


# ---------------------------------------------------------------------------
# Display-only: the module never imports a mutation seam
# ---------------------------------------------------------------------------


def test_module_imports_no_mutation_seam():
    """P1C stop-rule pin: zero mutation affordances — the panel module may
    not import any ``*_mutation`` module or the setup-operations dispatcher.
    """
    src = (
        _REPO_ROOT / "disbot" / "views" / "server_management" / "access_map.py"
    ).read_text()
    tree = ast.parse(src)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    offenders = {
        m for m in imported if "_mutation" in m or m.endswith("setup_operations")
    }
    assert not offenders, f"display-only panel imports mutation seams: {offenders}"


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_access_map_embed_buckets_and_labels():
    decisions = (
        _decision("economy"),
        _decision("ai", "deny"),
        _decision("counting", "unknown"),
    )
    with patch(
        "views.server_management.access_map.project_access_map",
        AsyncMock(return_value=decisions),
    ) as proj:
        embed, returned = await build_access_map_embed(99, 5, "user")

    ctx = proj.await_args.args[0]
    assert ctx.member is None and ctx.member_tier == "user"  # Q-0045 path
    assert returned == decisions
    names = [f.name for f in embed.fields]
    assert any(n.startswith("✅ Allowed (1)") for n in names)
    assert any(n.startswith("❌ Denied (1)") for n in names)
    assert any(n.startswith("❓ Unresolved (1)") for n in names)
    denied = next(f for f in embed.fields if f.name.startswith("❌"))
    assert "This feature is turned off here." in denied.value  # safe_text only
    sim = next(f for f in embed.fields if f.name == "Simulation limits")
    assert sim.value == SIMULATION_LIMIT_NOTE


def _help_decision(
    key: str,
    state: HelpEntryState,
    *,
    reason_code: str | None = None,
) -> HelpDecision:
    return HelpDecision(key=key, kind="subsystem", state=state, reason_code=reason_code)


def _projection(
    subsystems: tuple[HelpDecision, ...],
    *,
    presentations: dict[str, object] | None = None,
    orphans: tuple[HelpDecision, ...] = (),
) -> MagicMock:
    """A HelpProjection stand-in exposing what the preview consumes."""
    projection = MagicMock()
    projection.subsystems = subsystems
    projection.orphaned_overrides = orphans
    projection.subsystem_presentation = lambda key: (presentations or {}).get(key)
    return projection


@pytest.mark.asyncio
async def test_help_preview_buckets_advertised_locked_hidden():
    """The preview consumes the Help projection seam (Tier-2 fix,
    2026-06-10): buckets come from reason-coded ``HelpEntryState``, not
    re-derived access axes — and the projection runs on the Q-0045
    declared-tier context.
    """
    projection = _projection(
        (
            _help_decision("economy", HelpEntryState.SHOWN),
            _help_decision(
                "ai",
                HelpEntryState.ROUTED_OFF,
                reason_code="routing_disabled",
            ),
            _help_decision(
                "admin",
                HelpEntryState.GOVERNANCE_HIDDEN,
                reason_code="subsystem_hidden",
            ),
        ),
    )
    with patch(
        "views.server_management.access_map.project_help_with_execution",
        AsyncMock(return_value=projection),
    ) as proj:
        embed = await build_help_preview_embed(99, 5, "trusted")

    ctx = proj.await_args.args[0]
    assert ctx.member is None and ctx.member_tier == "trusted"  # Q-0045 path
    names = [f.name for f in embed.fields]
    assert any(n.startswith("📣 Advertised (1)") for n in names)
    assert any(n.startswith("🔒 Shown as locked (1)") for n in names)
    assert any(n.startswith("🙈 Hidden (1)") for n in names)
    locked = next(f for f in embed.fields if f.name.startswith("🔒"))
    assert "This feature is turned off here." in locked.value  # safe_text only
    assert "Trusted user" in embed.description
    assert any(f.value == SIMULATION_LIMIT_NOTE for f in embed.fields)


@pytest.mark.asyncio
async def test_help_preview_governance_deny_is_hidden_not_locked():
    """THE Tier-2 case: a governance-denied subsystem must render in the
    Hidden bucket (live Help hides it) — the pre-seam panel showed it as
    "Shown as locked".
    """
    projection = _projection(
        (
            _help_decision(
                "admin",
                HelpEntryState.GOVERNANCE_HIDDEN,
                reason_code="subsystem_hidden",
            ),
        ),
    )
    with patch(
        "views.server_management.access_map.project_help_with_execution",
        AsyncMock(return_value=projection),
    ):
        embed = await build_help_preview_embed(99, 5, "user")

    locked_fields = [f for f in embed.fields if f.name.startswith("🔒")]
    assert not any("admin" in f.value for f in locked_fields)
    hidden = next(f for f in embed.fields if f.name.startswith("🙈"))
    assert "admin" in hidden.value and "(governance)" in hidden.value


@pytest.mark.asyncio
async def test_help_preview_renders_overlay_hide_and_rename():
    """HLP-3 overlay state renders: a display-hidden subsystem lands in
    Hidden annotated *(overlay)*, and a renamed one shows its custom name
    beside the stable key (the pre-seam panel ignored the overlay).
    """
    presentation = MagicMock()
    presentation.display_name = "Bank"
    presentation.default_display_name = "Economy"
    projection = _projection(
        (
            _help_decision("economy", HelpEntryState.SHOWN),
            _help_decision(
                "counting",
                HelpEntryState.DISPLAY_HIDDEN,
                reason_code="overlay_hidden",
            ),
        ),
        presentations={"economy": presentation},
    )
    with patch(
        "views.server_management.access_map.project_help_with_execution",
        AsyncMock(return_value=projection),
    ):
        embed = await build_help_preview_embed(99, 5, "user")

    advertised = next(f for f in embed.fields if f.name.startswith("📣"))
    assert "economy →“Bank”" in advertised.value
    hidden = next(f for f in embed.fields if f.name.startswith("🙈"))
    assert "counting" in hidden.value and "(overlay)" in hidden.value


@pytest.mark.asyncio
async def test_help_preview_reports_orphaned_overlay_rows():
    """The preview is the operator surface the HLP-3 orphan contract
    names: rows for retired catalogue keys are reported, never rendered
    as entries.
    """
    orphan = HelpDecision(
        key="retired_subsystem",
        kind="subsystem",
        state=HelpEntryState.ORPHANED_OVERRIDE,
        reason_code="unknown_key",
    )
    projection = _projection(
        (_help_decision("economy", HelpEntryState.SHOWN),),
        orphans=(orphan,),
    )
    with patch(
        "views.server_management.access_map.project_help_with_execution",
        AsyncMock(return_value=projection),
    ):
        embed = await build_help_preview_embed(99, 5, "user")

    orphan_field = next(f for f in embed.fields if f.name.startswith("⚠️ Orphaned"))
    assert "retired_subsystem" in orphan_field.value
    advertised = next(f for f in embed.fields if f.name.startswith("📣"))
    assert "retired_subsystem" not in advertised.value


# ---------------------------------------------------------------------------
# Authority — re-checked at callback time, not at open time
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_panels_deny_non_admin_at_interaction_time():
    for view in (
        AccessMapView(MagicMock(id=1), (_decision("economy"),)),
        HelpPreviewView(MagicMock(id=1)),
    ):
        interaction = _interaction(admin=False)
        allowed = await view.interaction_check(interaction)
        assert allowed is False
        msg = interaction.response.send_message.await_args.args[0]
        assert "Administrator" in msg


@pytest.mark.asyncio
async def test_panels_admit_admin_at_interaction_time():
    view = AccessMapView(MagicMock(id=1), (_decision("economy"),))
    assert await view.interaction_check(_interaction(admin=True)) is True


@pytest.mark.asyncio
async def test_panels_are_not_ownership_locked():
    """Authority-gated, not ownership-gated: a *different* admin may use the
    shared panel (the hub edits one message in place).
    """
    view = AccessMapView(MagicMock(id=1), (_decision("economy"),))
    other_admin = _interaction(admin=True)
    other_admin.user.id = 42  # not the opener
    assert await view.interaction_check(other_admin) is True


# ---------------------------------------------------------------------------
# Tier switching + drill-down
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tier_select_rerenders_with_chosen_tier():
    """Driving the unbound callback with a mock select (journal pattern —
    the decorator-less Select subclass stores the coroutine on the class).
    """
    from views.server_management.access_map import _AudienceTierSelect

    rerender = AsyncMock()
    select = MagicMock()
    select.values = ["moderator"]
    select.view = MagicMock(rerender=rerender)
    interaction = _interaction()

    await _AudienceTierSelect.callback(select, interaction)

    rerender.assert_awaited_once()
    assert rerender.await_args.kwargs["tier"] == "moderator"


@pytest.mark.asyncio
async def test_feature_detail_select_sends_ephemeral_chain():
    from views.server_management.access_map import _FeatureDetailSelect

    decision = _decision("ai", "deny")
    select = MagicMock()
    select.values = ["ai"]
    select._by_feature = {"ai": decision}
    interaction = _interaction()

    await _FeatureDetailSelect.callback(select, interaction)

    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs["ephemeral"] is True
    embed = kwargs["embed"]
    assert "Source chain — ai" in embed.title
    assert "routing" in embed.description
    assert embed.footer.text == SIMULATION_LIMIT_NOTE

"""Unit tests for services.access_projection — Access Map projection (P1A).

Exercises the composition contract from
``docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md`` §16:

* feature inventory is registry-driven (snake_case keys, first entry_point);
* axes compose in precedence order and **short-circuit on the first deny**;
* the deciding axis + a user-safe ``LockedReason`` are reported;
* the help axis is **informational** — it never flips an ``allow`` to ``deny``;
* an unresolved gating axis yields ``unknown`` (never a false ``allow``);
* ``LockedReason.safe_text`` leaks no context (ids / roles / tiers);
* the §16.7 negative-architecture guardrails hold (no writes / mutation / UI
  imports; the projection composes existing owners only).

Axis resolvers are patched at their source modules (the projection imports them
function-locally, so the patched attribute is what each call resolves to) — the
tests drive composition, not the live resolvers.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime.command_access import (
    AccessMode,
    CommandAccessDecision,
    DecisionReason,
    DecisionSource,
)
from services import access_projection as ap
from services.access_projection import (
    AccessAxis,
    AccessContext,
    AccessDecision,
    AxisOutcome,
    FeatureEntry,
    LockedReason,
    feature_inventory,
    resolve_feature_access,
)

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

_FEATURE = FeatureEntry(
    subsystem="economy",
    command_name="economymenu",
    visibility_tier="user",
)


def _ctx(**overrides) -> AccessContext:
    base = dict(
        guild_id=900111,
        channel_id=900222,
        category_id=900333,
        user_id=900444,
        member=MagicMock(name="member"),
        member_role_ids=(900555, 900666),
        is_guild_operator=False,
        is_bot_owner=False,
        is_dm=False,
    )
    base.update(overrides)
    return AccessContext(**base)


def _ca_allow(
    source: DecisionSource = DecisionSource.DEFAULT_UNCONFIGURED,
) -> CommandAccessDecision:
    return CommandAccessDecision(
        allowed=True,
        reason=DecisionReason.ALLOWED,
        source=source,
        mode=AccessMode.ALL_CHANNELS,
        feedback=None,
    )


def _ca_deny(
    reason: DecisionReason = DecisionReason.CHANNEL_NOT_ALLOWED,
) -> CommandAccessDecision:
    return CommandAccessDecision(
        allowed=False,
        reason=reason,
        source=DecisionSource.DB_POLICY,
        mode=AccessMode.SELECTED_CHANNELS,
        feedback="leak: channel 900222 not allowed",  # internal — must NOT surface
    )


def _patch_axes(
    *,
    ca: CommandAccessDecision | None = None,
    routing: bool | Exception = True,
    visible: set[str] | None = None,
):
    """Patch all three live axis resolvers at their source modules."""
    ca = ca if ca is not None else _ca_allow()
    visible = visible if visible is not None else {"economy"}
    routing_mock = (
        AsyncMock(side_effect=routing)
        if isinstance(routing, Exception)
        else AsyncMock(return_value=routing)
    )
    return (
        patch(
            "core.runtime.command_access.resolve_command_access",
            new=AsyncMock(return_value=ca),
        ),
        patch("services.command_routing.is_cog_enabled", new=routing_mock),
        patch("governance.get_visible_subsystems", new=AsyncMock(return_value=visible)),
    )


async def _resolve(
    feature: FeatureEntry = _FEATURE,
    ctx: AccessContext | None = None,
    **axes,
):
    p_ca, p_rt, p_gv = _patch_axes(**axes)
    with p_ca, p_rt, p_gv:
        return await resolve_feature_access(feature, ctx or _ctx())


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


def test_public_types_are_frozen():
    for obj in (
        LockedReason(code="x", safe_text="y", source="z"),
        AxisOutcome(AccessAxis.ROUTING, "deny"),
        FeatureEntry("economy", "economymenu", "user"),
        AccessContext(guild_id=1),
    ):
        with pytest.raises(Exception):
            obj.code = "mutated"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Feature inventory
# ---------------------------------------------------------------------------


def test_feature_inventory_covers_every_subsystem():
    from utils.subsystem_registry import SUBSYSTEMS

    inv = feature_inventory()
    assert {f.subsystem for f in inv} == set(SUBSYSTEMS)


def test_feature_inventory_uses_first_entry_point_and_tier():
    inv = {f.subsystem: f for f in feature_inventory()}
    # economy declares entry_points = ["economymenu", "daily", ...]; tier "user".
    assert inv["economy"].command_name == "economymenu"
    assert inv["economy"].visibility_tier == "user"
    # server_management (Q-0026 snake_case key) resolves and is administrator-tier.
    assert "server_management" in inv
    assert inv["server_management"].visibility_tier == "administrator"


# ---------------------------------------------------------------------------
# Precedence / short-circuit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_command_access_deny_short_circuits_first():
    decision = await _resolve(ca=_ca_deny(DecisionReason.CHANNEL_NOT_ALLOWED))
    assert decision.effective == "deny"
    assert decision.deciding_axis is AccessAxis.COMMAND_ACCESS
    assert decision.reason is not None
    assert decision.reason.code == "channel_not_allowed"
    # short-circuit: routing/governance were not appended to the chain
    axes = [o.axis for o in decision.source_chain]
    assert axes == [AccessAxis.COMMAND_ACCESS]


@pytest.mark.asyncio
async def test_routing_deny_when_command_access_allows():
    decision = await _resolve(ca=_ca_allow(), routing=False)
    assert decision.effective == "deny"
    assert decision.deciding_axis is AccessAxis.ROUTING
    assert decision.reason.code == "routing_disabled"
    axes = [o.axis for o in decision.source_chain]
    assert axes == [AccessAxis.COMMAND_ACCESS, AccessAxis.ROUTING]


@pytest.mark.asyncio
async def test_governance_deny_when_upstream_allows():
    # economy not in the visible set => governance denies with subsystem_hidden.
    decision = await _resolve(ca=_ca_allow(), routing=True, visible=set())
    assert decision.effective == "deny"
    assert decision.deciding_axis is AccessAxis.GOVERNANCE
    assert decision.reason.code == "subsystem_hidden"


@pytest.mark.asyncio
async def test_all_axes_allow_yields_allow_with_full_chain():
    decision = await _resolve(ca=_ca_allow(), routing=True, visible={"economy"})
    assert decision.effective == "allow"
    assert decision.deciding_axis is None
    assert decision.reason is None
    axes = [o.axis for o in decision.source_chain]
    # gating axes 1-4 plus the informational help axis (availability is skipped-recorded)
    assert AccessAxis.COMMAND_ACCESS in axes
    assert AccessAxis.ROUTING in axes
    assert AccessAxis.GOVERNANCE in axes
    assert AccessAxis.AVAILABILITY in axes
    assert AccessAxis.HELP in axes


@pytest.mark.asyncio
async def test_bootstrap_bypass_is_allow_and_recorded():
    decision = await _resolve(ca=_ca_allow(source=DecisionSource.BOOTSTRAP_BYPASS))
    assert decision.effective == "allow"
    ca_outcome = next(
        o for o in decision.source_chain if o.axis is AccessAxis.COMMAND_ACCESS
    )
    assert ca_outcome.state == "allow"
    assert ca_outcome.detail == "bootstrap_bypass"


@pytest.mark.asyncio
async def test_feature_without_command_skips_command_access_axis():
    feature = FeatureEntry(
        subsystem="economy",
        command_name=None,
        visibility_tier="user",
    )
    decision = await _resolve(
        feature=feature,
        ca=_ca_allow(),
        routing=True,
        visible={"economy"},
    )
    ca_outcome = next(
        o for o in decision.source_chain if o.axis is AccessAxis.COMMAND_ACCESS
    )
    assert ca_outcome.state == "skipped"
    # routing + governance still evaluate, so an allow is still reachable.
    assert decision.effective == "allow"


# ---------------------------------------------------------------------------
# Unknown handling — never a false allow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_routing_resolver_error_yields_unknown_not_allow():
    decision = await _resolve(
        ca=_ca_allow(),
        routing=RuntimeError("db down"),
        visible={"economy"},
    )
    assert decision.effective == "unknown"
    assert decision.reason is None  # unknown is not a denial
    rt = next(o for o in decision.source_chain if o.axis is AccessAxis.ROUTING)
    assert rt.state == "unknown"


@pytest.mark.asyncio
async def test_governance_unknown_when_no_member():
    decision = await _resolve(ctx=_ctx(member=None), ca=_ca_allow(), routing=True)
    assert decision.effective == "unknown"
    gv = next(o for o in decision.source_chain if o.axis is AccessAxis.GOVERNANCE)
    assert gv.state == "unknown"


# ---------------------------------------------------------------------------
# Audience simulation — the declared-tier governance input (Q-0045 option b)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_declared_tier_evaluates_governance_without_member():
    """member=None + member_tier set → the axis evaluates instead of unknown,
    and the declared tier is passed through to the governance context."""
    captured: list = []

    async def _capture(gctx):
        captured.append(gctx)
        return {"economy"}

    p_ca, p_rt, _ = _patch_axes(ca=_ca_allow(), routing=True)
    with p_ca, p_rt, patch("governance.get_visible_subsystems", new=_capture):
        decision = await resolve_feature_access(
            _FEATURE,
            _ctx(member=None, member_tier="user"),
        )
    assert decision.effective == "allow"
    gv = next(o for o in decision.source_chain if o.axis is AccessAxis.GOVERNANCE)
    assert gv.state == "allow"
    assert len(captured) == 1
    assert captured[0].member is None
    assert captured[0].member_tier == "user"


@pytest.mark.asyncio
async def test_simulated_governance_outcome_labels_its_limits():
    """§16.4: a simulated evaluation must label what it cannot model — the
    label rides the (internal-only) outcome detail on allow AND deny."""
    allow = await _resolve(
        ctx=_ctx(member=None, member_tier="user"),
        ca=_ca_allow(),
        routing=True,
        visible={"economy"},
    )
    gv = next(o for o in allow.source_chain if o.axis is AccessAxis.GOVERNANCE)
    assert "simulated tier=user" in (gv.detail or "")
    assert "overrides not modeled" in (gv.detail or "")

    deny = await _resolve(
        ctx=_ctx(member=None, member_tier="user"),
        ca=_ca_allow(),
        routing=True,
        visible=set(),
    )
    assert deny.effective == "deny"
    assert deny.deciding_axis is AccessAxis.GOVERNANCE
    assert deny.reason is not None
    assert deny.reason.code == "subsystem_hidden"
    gv = next(o for o in deny.source_chain if o.axis is AccessAxis.GOVERNANCE)
    assert "simulated tier=user" in (gv.detail or "")
    # ...while the user-facing safe_text stays static and label-free.
    assert "simulated" not in deny.reason.safe_text


@pytest.mark.asyncio
async def test_live_member_outcome_carries_no_simulation_label():
    decision = await _resolve(ca=_ca_allow(), routing=True, visible={"economy"})
    gv = next(o for o in decision.source_chain if o.axis is AccessAxis.GOVERNANCE)
    assert gv.state == "allow"
    assert gv.detail is None


# ---------------------------------------------------------------------------
# Help axis is informational — never gates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_hidden_does_not_flip_allow_to_deny():
    fake_ledger = MagicMock()
    fake_ledger.find.return_value = MagicMock(name="entry")
    p_ca, p_rt, p_gv = _patch_axes(ca=_ca_allow(), routing=True, visible={"economy"})
    with (
        p_ca,
        p_rt,
        p_gv,
        patch(
            "core.runtime.command_surface_ledger.get_cached_ledger",
            return_value=fake_ledger,
        ),
        patch(
            "core.runtime.command_surface_ledger.is_hidden_from_help",
            return_value=True,
        ),
    ):
        decision = await resolve_feature_access(_FEATURE, _ctx())
    assert decision.effective == "allow"  # help never gates execution
    help_outcome = next(o for o in decision.source_chain if o.axis is AccessAxis.HELP)
    assert help_outcome.state == "hidden"


@pytest.mark.asyncio
async def test_help_axis_unknown_when_ledger_not_built():
    with patch(
        "core.runtime.command_surface_ledger.get_cached_ledger",
        return_value=None,
    ):
        decision = await _resolve(ca=_ca_allow(), routing=True, visible={"economy"})
    help_outcome = next(o for o in decision.source_chain if o.axis is AccessAxis.HELP)
    assert help_outcome.state == "unknown"
    # ...and an unknown HELP axis must NOT make the effective result unknown.
    assert decision.effective == "allow"


# ---------------------------------------------------------------------------
# Reason safety — safe_text leaks no context (the §16.7 redaction guard)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_locked_reason_safe_text_leaks_no_context():
    ctx = _ctx()  # distinctive ids 900xxx
    sensitive = {
        str(ctx.guild_id),
        str(ctx.channel_id),
        str(ctx.category_id),
        *(str(r) for r in ctx.member_role_ids),
        "tier",
        "900",
    }
    for ca in (
        _ca_deny(DecisionReason.CHANNEL_NOT_ALLOWED),
        _ca_deny(DecisionReason.COMMANDS_DISABLED),
    ):
        decision = await _resolve(ctx=ctx, ca=ca)
        assert decision.reason is not None
        text = decision.reason.safe_text
        for token in sensitive:
            assert token not in text, f"safe_text leaked {token!r}: {text!r}"


def test_every_reason_code_maps_to_leak_free_static_text():
    for code, (text, source, _hint, _rem) in ap._SAFE_TEXT.items():
        assert text and isinstance(text, str)
        assert source
        # static template: no interpolation markers, no obvious identifier leak.
        for marker in ("{", "}", "id=", "tier=", "role", "channel id"):
            assert (
                marker not in text
            ), f"{code}: suspicious token {marker!r} in {text!r}"


def test_safe_text_covers_the_full_reason_code_union():
    """Q-0036: the drafted denial-copy set covers the entire §16.3 code union
    (DecisionReason deny values + the axis 3-5/bootstrap codes), each with a
    source from the §16.3 vocabulary. Draft only — not wired into live denial
    paths (the live command-access feedback strings are separate)."""
    expected = {
        "lifecycle_draining",
        "dm_not_supported",
        "channel_not_allowed",
        "commands_disabled",
        "routing_disabled",
        "capability_insufficient",
        "subsystem_hidden",
        "availability_window",
        "quiet_mode",
        "setup_stage_required",
    }
    assert expected <= set(ap._SAFE_TEXT)
    allowed_sources = {
        "command_access",
        "routing",
        "governance",
        "availability",
        "bootstrap",
        "help",
    }
    for code, (_text, source, _hint, _rem) in ap._SAFE_TEXT.items():
        assert source in allowed_sources, f"{code}: unknown source {source!r}"


# ---------------------------------------------------------------------------
# Negative architecture — composes owners; no writes / mutation / UI imports
# ---------------------------------------------------------------------------

_FORBIDDEN_IMPORT_SUBSTRINGS = (
    "_mutation",
    "setup_draft",
    "setup_operations",
    "views.",
    "cogs.",
)


def _all_imported_modules() -> set[str]:
    src = Path(inspect.getfile(ap)).read_text(encoding="utf-8")
    tree = ast.parse(src)
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
        elif isinstance(node, ast.Import):
            mods.update(alias.name for alias in node.names)
    return mods


def test_projection_imports_no_mutation_or_ui_module():
    mods = _all_imported_modules()
    for mod in mods:
        for bad in _FORBIDDEN_IMPORT_SUBSTRINGS:
            assert bad not in mod, f"forbidden import {mod!r} (matches {bad!r})"


def test_projection_does_not_import_discord():
    """A pure read model needs no Discord API — member is typed ``Any``."""
    mods = _all_imported_modules()
    assert "discord" not in mods
    assert not any(m.startswith("discord.") for m in mods)


def test_projection_only_calls_read_resolvers():
    """Every axis must delegate to a *read* owner — assert the known read
    resolvers are referenced and no write seam (set_policy/set_setting/etc.)
    appears in the source.
    """
    src = Path(inspect.getfile(ap)).read_text(encoding="utf-8")
    assert "resolve_command_access" in src
    assert "is_cog_enabled" in src
    assert "get_visible_subsystems" in src
    for write in (
        "set_policy",
        "set_setting",
        "set_one",
        ".execute(",
        "MutationPipeline",
    ):
        assert write not in src, f"projection references a write seam: {write!r}"


def test_resolve_feature_access_returns_decision_shape():
    """Smoke: the public surface returns the documented dataclass."""
    assert AccessDecision.__dataclass_fields__.keys() >= {
        "feature",
        "command_name",
        "effective",
        "deciding_axis",
        "reason",
        "source_chain",
        "remediation",
    }

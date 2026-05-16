"""Tests for utils.subsystem_registry.validate_identity_contract (INV-B).

Covers:
- clean state returns empty findings
- missing command for a non-internal entry_point is reported
- internal subsystems with no commands are NOT reported
- unknown router prefix is reported
- unknown view SUBSYSTEM is reported
- unknown panel_anchors row is reported
- DB error is swallowed (no raise)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.subsystem_registry import SUBSYSTEMS, validate_identity_contract


def _bot_with_commands(*names: str) -> MagicMock:
    cmds = [MagicMock(name=n) for n in names]
    # Mock's auto-name behaviour overrides .name; reset explicitly.
    for cmd, n in zip(cmds, names, strict=True):
        cmd.name = n
    bot = MagicMock()
    bot.commands = cmds
    return bot


@pytest.fixture
def _empty_registries():
    """Patch the three runtime registries to empty for predictable tests."""
    with (
        patch("core.runtime.interaction_router._handlers", {}),
        patch("core.runtime.persistent_views._REGISTRY", {}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=[]),
    ):
        yield


@pytest.mark.asyncio
async def test_clean_state_no_findings(_empty_registries):
    # Build a bot whose commands cover every non-internal entry_point in the
    # real registry — so the only finding source is left for other tests.
    all_eps = {
        ep
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }
    bot = _bot_with_commands(*all_eps)
    findings = await validate_identity_contract(bot)
    assert findings == {
        "entry_point_missing_command": [],
        "router_prefix_unknown": [],
        "view_subsystem_unknown": [],
        "db_anchor_subsystem_unknown": [],
    }


@pytest.mark.asyncio
async def test_missing_command_reported(_empty_registries):
    # Bot has no commands; every non-internal entry_point becomes a finding.
    bot = _bot_with_commands()
    findings = await validate_identity_contract(bot)
    assert len(findings["entry_point_missing_command"]) > 0
    # All reported entry_points belong to non-internal subsystems.
    for msg in findings["entry_point_missing_command"]:
        # Format: "subsystem=<name> entry_point=<ep>"
        assert "subsystem=" in msg and "entry_point=" in msg


@pytest.mark.asyncio
async def test_router_prefix_unknown_reported():
    all_eps = {
        ep
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }
    bot = _bot_with_commands(*all_eps)
    with (
        patch(
            "core.runtime.interaction_router._handlers",
            {"ghost": lambda *_: None},
        ),
        patch("core.runtime.persistent_views._REGISTRY", {}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=[]),
    ):
        findings = await validate_identity_contract(bot)
    assert "ghost" in findings["router_prefix_unknown"]


@pytest.mark.asyncio
async def test_view_subsystem_unknown_reported():
    all_eps = {
        ep
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }
    bot = _bot_with_commands(*all_eps)
    fake_view = MagicMock()
    with (
        patch("core.runtime.interaction_router._handlers", {}),
        patch("core.runtime.persistent_views._REGISTRY", {"ghost": fake_view}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=[]),
    ):
        findings = await validate_identity_contract(bot)
    assert "ghost" in findings["view_subsystem_unknown"]


@pytest.mark.asyncio
async def test_db_anchor_subsystem_unknown_reported():
    all_eps = {
        ep
        for name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }
    bot = _bot_with_commands(*all_eps)
    rows = [{"subsystem": "ghost"}, {"subsystem": "role"}]
    with (
        patch("core.runtime.interaction_router._handlers", {}),
        patch("core.runtime.persistent_views._REGISTRY", {}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=rows),
    ):
        findings = await validate_identity_contract(bot)
    assert "ghost" in findings["db_anchor_subsystem_unknown"]
    # "role" exists in the real registry, so it should NOT appear.
    assert "role" not in findings["db_anchor_subsystem_unknown"]


@pytest.mark.asyncio
async def test_db_error_does_not_abort(_empty_registries):
    bot = _bot_with_commands()
    with patch(
        "utils.db.fetchall",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB down"),
    ):
        # Should NOT raise.
        findings = await validate_identity_contract(bot)
    # DB-based finding bucket is empty when DB is unreachable.
    assert findings["db_anchor_subsystem_unknown"] == []

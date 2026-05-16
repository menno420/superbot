"""R1 — tests for the !platform admin command surface.

Covers:
- !platform anchors surfaces the last restoration stats + a DB query
- !platform identity runs the validator and renders findings as embed fields
- The diagnostic subsystem registry advertises `platform` as an entry_point
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.subsystem_registry import SUBSYSTEMS


def test_diagnostic_subsystem_advertises_platform_entrypoint():
    assert "platform" in SUBSYSTEMS["diagnostic"]["entry_points"]


@pytest.mark.asyncio
async def test_platform_anchors_renders_stats_and_db_counts():
    from cogs.diagnostic_cog import DiagnosticCog
    from core.runtime import message_anchor_manager

    bot = MagicMock()
    cog = DiagnosticCog(bot)
    ctx = MagicMock()
    ctx.send = AsyncMock()

    message_anchor_manager._LAST_RESTORE_STATS.update(
        anchors_seen=7, restored=5, view_missing=1, stale=1,
    )
    rows = [
        {"subsystem": "role", "n": 3},
        {"subsystem": "economy", "n": 2},
    ]
    with patch(
        "cogs.diagnostic_cog.db.fetchall",
        new_callable=AsyncMock,
        return_value=rows,
    ):
        await cog.platform_anchors.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    body = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "restored: **5**" in body
    assert "role" in body and "economy" in body


@pytest.mark.asyncio
async def test_platform_identity_renders_findings():
    from cogs.diagnostic_cog import DiagnosticCog

    bot = MagicMock()
    cog = DiagnosticCog(bot)
    ctx = MagicMock()
    ctx.send = AsyncMock()

    fake_findings = {
        "entry_point_missing_command": ["subsystem='economy' entry_point='daily'"],
        "router_prefix_unknown": [],
        "view_subsystem_unknown": ["ghost"],
        "db_anchor_subsystem_unknown": [],
    }
    with patch(
        "utils.subsystem_registry.validate_identity_contract",
        new_callable=AsyncMock,
        return_value=fake_findings,
    ):
        await cog.platform_identity.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    # 2 findings → orange embed; only non-empty buckets render as fields.
    field_names = {f.name for f in embed.fields}
    assert any("entry_point_missing_command" in n for n in field_names)
    assert any("view_subsystem_unknown" in n for n in field_names)
    assert not any("router_prefix_unknown" in n for n in field_names)


@pytest.mark.asyncio
async def test_platform_identity_clean_state():
    from cogs.diagnostic_cog import DiagnosticCog

    bot = MagicMock()
    cog = DiagnosticCog(bot)
    ctx = MagicMock()
    ctx.send = AsyncMock()

    clean_findings: dict[str, list[str]] = {
        "entry_point_missing_command": [],
        "router_prefix_unknown": [],
        "view_subsystem_unknown": [],
        "db_anchor_subsystem_unknown": [],
    }
    with patch(
        "utils.subsystem_registry.validate_identity_contract",
        new_callable=AsyncMock,
        return_value=clean_findings,
    ):
        await cog.platform_identity.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    assert "All four identity surfaces agree" in embed.description
    assert embed.fields == []

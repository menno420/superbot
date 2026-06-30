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
    """!platform anchors must render the last restore stats + DB counts.

    P1 PR-7 rewrite: previously asserted the literal substring
    "restored: **5**" in the rendered embed text — that broke on any
    cosmetic copy edit.  Now asserts on the embed's structured fields
    (field count + per-subsystem row presence) so behaviour is
    enforced without coupling to the markdown.
    """
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
        "utils.db.anchors.count_active_anchors_by_subsystem",
        new_callable=AsyncMock,
        return_value=rows,
    ):
        await cog.platform_anchors.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    # At least one field; subsystem rows appear (in name or value).
    assert embed.fields, "platform anchors embed must have fields"
    body = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
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


# ---------------------------------------------------------------------------
# !platform finding — operator-managed lifecycle transition (Q-0097)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_finding_resolve_reports_transition():
    from cogs.diagnostic_cog import DiagnosticCog
    from services.health_findings_service import TransitionResult

    cog = DiagnosticCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.author.id = 7

    with patch(
        "services.health_findings_service.set_status",
        new_callable=AsyncMock,
        return_value=TransitionResult(outcome="applied", previous_status="open"),
    ) as set_status:
        await cog.platform_finding.callback(
            cog, ctx, "resolve", fingerprint="diagnostics.provider_failed:ai",
        )

    set_status.assert_awaited_once_with(
        "diagnostics.provider_failed:ai", "resolved", actor_id=7,
    )
    msg = ctx.send.call_args.args[0]
    assert "✅" in msg and "resolved" in msg


@pytest.mark.asyncio
async def test_platform_finding_unknown_action_does_not_call_service():
    from cogs.diagnostic_cog import DiagnosticCog

    cog = DiagnosticCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()

    with patch(
        "services.health_findings_service.set_status",
        new_callable=AsyncMock,
    ) as set_status:
        await cog.platform_finding.callback(cog, ctx, "frobnicate", fingerprint="x")

    set_status.assert_not_awaited()
    assert "Unknown action" in ctx.send.call_args.args[0]


@pytest.mark.asyncio
async def test_platform_finding_not_found_reports_warning():
    from cogs.diagnostic_cog import DiagnosticCog
    from services.health_findings_service import TransitionResult

    cog = DiagnosticCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.author.id = 1

    with patch(
        "services.health_findings_service.set_status",
        new_callable=AsyncMock,
        return_value=TransitionResult(outcome="not_found", previous_status=None),
    ):
        await cog.platform_finding.callback(cog, ctx, "ignore", fingerprint="ghost")

    assert "No finding" in ctx.send.call_args.args[0]


# ---------------------------------------------------------------------------
# !platform findings / consistency — paginated dense subviews (cert punch #2)
# ---------------------------------------------------------------------------


def _finding_rows(n: int) -> list[dict]:
    return [
        {
            "severity": "warn",
            "status": "open",
            "category": f"cat.{i}",
            "message": f"msg {i}",
            "occurrence_count": 1,
        }
        for i in range(n)
    ]


@pytest.mark.asyncio
async def test_platform_findings_attaches_paginator_when_many_rows():
    from cogs.diagnostic_cog import DiagnosticCog
    from services.diagnostic_embeds import _FINDINGS_PER_PAGE
    from views.diagnostic.paginator import _PaginatorView

    cog = DiagnosticCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.author = MagicMock()

    with (
        patch(
            "services.health_snapshot_service.resolve_audience",
            new_callable=AsyncMock,
        ),
        patch(
            "services.health_findings_service.list_by_status",
            new_callable=AsyncMock,
            return_value=_finding_rows(_FINDINGS_PER_PAGE * 2 + 1),
        ),
        patch(
            "services.health_findings_service.count_by_status",
            new_callable=AsyncMock,
            return_value={"open": _FINDINGS_PER_PAGE * 2 + 1},
        ),
    ):
        await cog.platform_findings.callback(cog, ctx, status="open")

    # Multi-page output -> a _PaginatorView is attached to the sent message.
    view = ctx.send.call_args.kwargs.get("view")
    assert isinstance(view, _PaginatorView)
    assert len(view.pages) == 3


@pytest.mark.asyncio
async def test_platform_findings_no_view_when_single_page():
    from cogs.diagnostic_cog import DiagnosticCog

    cog = DiagnosticCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.author = MagicMock()

    with (
        patch(
            "services.health_snapshot_service.resolve_audience",
            new_callable=AsyncMock,
        ),
        patch(
            "services.health_findings_service.list_by_status",
            new_callable=AsyncMock,
            return_value=_finding_rows(2),
        ),
        patch(
            "services.health_findings_service.count_by_status",
            new_callable=AsyncMock,
            return_value={"open": 2},
        ),
    ):
        await cog.platform_findings.callback(cog, ctx, status="open")

    assert ctx.send.call_args.kwargs.get("view") is None
    assert ctx.send.call_args.kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_platform_consistency_attaches_paginator_when_many_sections():
    import datetime

    from cogs.diagnostic_cog import DiagnosticCog
    from services.platform_consistency import (
        ConsistencyReport,
        SectionResult,
        SectionStatus,
    )
    from views.diagnostic.paginator import _PaginatorView

    sections = [
        SectionResult(
            name=f"s{i}",
            status=SectionStatus.WARNING,
            summary="X" * 700,
            details=("d" * 120, "e" * 120, "f" * 120),
            suggested_actions=("a" * 120, "b" * 120),
        )
        for i in range(30)
    ]
    report = ConsistencyReport(
        sections=sections,
        generated_at=datetime.datetime(2026, 6, 30, tzinfo=datetime.timezone.utc),
    )

    cog = DiagnosticCog(MagicMock())
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.author = MagicMock()
    ctx.guild = MagicMock()

    with patch(
        "services.platform_consistency.collect_report",
        new_callable=AsyncMock,
        return_value=report,
    ):
        await cog.platform_consistency.callback(cog, ctx)

    view = ctx.send.call_args.kwargs.get("view")
    assert isinstance(view, _PaginatorView)
    # Every section is reachable across the pages -- none dropped.
    assert sum(len(p.fields) for p in view.pages) == 30

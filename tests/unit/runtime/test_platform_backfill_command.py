"""Tests for ``!platform backfill`` — the legacy-pointer → binding migration command.

Wires the already-built, tested ``services.binding_backfill`` (dry_run /
apply_backfill) to an admin-gated command so the migration can be completed in
production (P0-3 convergence plan §8). These tests cover the dry-run default, the
explicit ``apply`` path (including the advisory-lock-held case), and the two
embed builders.
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cogs.diagnostic._platform_embeds import (
    build_backfill_apply_embed,
    build_backfill_dryrun_embed,
)
from services import binding_backfill
from services.binding_backfill import (
    ApplyResult,
    CandidateResult,
    DryRunSummary,
    WriteResult,
)

_NOW = datetime.datetime(2026, 6, 14, tzinfo=datetime.timezone.utc)


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.send = AsyncMock()
    ctx.guild = MagicMock()
    ctx.author.id = 4242
    return ctx


def _make_cog():
    from cogs.diagnostic_cog import DiagnosticCog

    return DiagnosticCog(bot=MagicMock())


def _candidate(classification: str) -> CandidateResult:
    return CandidateResult(
        legacy_key="xp_announce_channel",
        subsystem="xp",
        binding_name="announce_channel",
        kind="channel",
        legacy_target_id=111,
        legacy_raw="111",
        binding_target_id=None,
        binding_status=None,
        classification=classification,
        reason="legacy present, no binding",
    )


def _dryrun(*, writable: int = 1) -> DryRunSummary:
    return DryRunSummary(
        guild_id=1,
        started_at=_NOW,
        completed_at=_NOW,
        summary_version=1,
        candidates=(_candidate("candidate_valid"),) if writable else (),
        counts={"candidate_valid": writable} if writable else {"both_absent": 1},
    )


def _apply(*, failed: bool = False) -> ApplyResult:
    writes = (
        WriteResult(
            legacy_key="xp_announce_channel",
            subsystem="xp",
            binding_name="announce_channel",
            target_id=111,
            write_status="failed" if failed else "written",
            classification="candidate_valid",
            mutation_id="" if failed else "mut-1",
            error="boom" if failed else None,
        ),
    )
    return ApplyResult(
        guild_id=1,
        started_at=_NOW,
        completed_at=_NOW,
        actor_id=4242,
        summary_version=1,
        pre_counts={"candidate_valid": 1},
        post_counts={"match": 1},
        writes=writes,
        write_status_counts={"failed": 1} if failed else {"written": 1},
        error="boom" if failed else None,
    )


# --- command: dry-run default ----------------------------------------------


@pytest.mark.asyncio
async def test_backfill_default_is_dry_run():
    cog, ctx = _make_cog(), _make_ctx()
    with (
        patch.object(
            binding_backfill,
            "dry_run",
            AsyncMock(return_value=_dryrun()),
        ) as dr,
        patch.object(binding_backfill, "apply_backfill", AsyncMock()) as ap,
    ):
        await cog.platform_backfill.callback(cog, ctx, "")
    dr.assert_awaited_once()
    ap.assert_not_awaited()  # default must never mutate
    embed = ctx.send.call_args.kwargs["embed"]
    assert "dry run" in (embed.title or "").lower()


# --- command: apply --------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_apply_writes_with_actor_id():
    cog, ctx = _make_cog(), _make_ctx()
    with patch.object(
        binding_backfill,
        "apply_backfill",
        AsyncMock(return_value=_apply()),
    ) as ap:
        await cog.platform_backfill.callback(cog, ctx, "apply")
    ap.assert_awaited_once()
    assert ap.call_args.kwargs["actor_id"] == 4242
    embed = ctx.send.call_args.kwargs["embed"]
    assert "applied" in (embed.title or "").lower()


@pytest.mark.asyncio
async def test_backfill_apply_reports_lock_held():
    cog, ctx = _make_cog(), _make_ctx()
    with patch.object(
        binding_backfill,
        "apply_backfill",
        AsyncMock(side_effect=binding_backfill.BackfillLockHeldError("held")),
    ):
        await cog.platform_backfill.callback(cog, ctx, "apply")
    sent = ctx.send.call_args.args[0] if ctx.send.call_args.args else ""
    assert "already running" in sent.lower()


# --- embed builders --------------------------------------------------------


def test_dryrun_embed_flags_writable_candidates():
    embed = build_backfill_dryrun_embed(_dryrun(writable=2))
    assert "2" in (embed.description or "")
    assert "apply" in (embed.footer.text or "").lower()


def test_dryrun_embed_nothing_to_do():
    embed = build_backfill_dryrun_embed(_dryrun(writable=0))
    assert "nothing to migrate" in (embed.description or "").lower()


def test_apply_embed_success_vs_failure():
    ok = build_backfill_apply_embed(_apply(failed=False))
    assert "applied" in (ok.title or "").lower()
    bad = build_backfill_apply_embed(_apply(failed=True))
    assert "failed" in (bad.title or "").lower()
    # the per-write error is surfaced
    assert any("boom" in (f.value or "") for f in bad.fields)

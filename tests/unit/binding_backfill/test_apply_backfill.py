"""Phase 2 PR-6 — services.binding_backfill.apply_backfill end-to-end.

Verifies the write phase:

* Calls dry_run() to get fresh classification.
* Writes only CANDIDATE_VALID candidates through
  utils.db.bindings.upsert_with_audit with actor_type='backfill'.
* Pre-check: skips writes when the binding already matches
  (idempotent re-run).
* Records per-candidate WriteResult.
* Re-classifies after write for the operator's review.
* Updates the checkpoint to 'complete' or 'failed' depending on
  whether any write raised.
* Acquires + releases the advisory lock (when enabled).
* Refuses to run if the advisory lock is held.
* NEVER calls BindingMutationPipeline (the backfill bypasses
  user-facing authority by using a dedicated 'backfill' actor_type
  recorded in the audit log; the operator's actor_id is required).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.resources.status import ResourceStatus
from core.runtime.bindings import BindingValue
from core.runtime.subsystem_schema import BindingKind
from services import binding_backfill
from services.binding_backfill import (
    WRITE_STATUS_FAILED,
    WRITE_STATUS_SKIPPED_IDEMPOTENT,
    WRITE_STATUS_SKIPPED_NOT_CANDIDATE,
    WRITE_STATUS_WRITTEN,
    BackfillLockHeldError,
    apply_backfill,
)


def _bv(*, target_id, status, last_updated_at=None):
    return BindingValue(
        guild_id=42,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
        target_id=target_id,
        status=status,
        last_validated_at=last_updated_at,
        last_updated_at=last_updated_at,
        version=1 if last_updated_at is not None else 0,
    )


@pytest.fixture
def _mock_guild():
    guild = MagicMock()
    guild.id = 42
    return guild


@pytest.fixture
def _patches(_mock_guild):
    """Patch every external touchpoint the write phase relies on.

    Three layers:
      * dry_run() — patched at the binding_backfill module level to
        give the test full control over the classification.
      * utils.db.bindings primitives — get_one (pre-check) and
        upsert_with_audit (the actual write).
      * utils.db.platform_migration_checkpoints.upsert_checkpoint —
        called at in_progress + terminal phases.
      * Advisory lock is disabled by default (advisory_lock=False in
        tests); a separate fixture exercises it.
    """
    with (
        patch.object(
            binding_backfill,
            "dry_run",
            new_callable=AsyncMock,
        ) as mock_dry_run,
        patch(
            "utils.db.bindings.get_one",
            new_callable=AsyncMock,
        ) as mock_get_one,
        patch(
            "utils.db.bindings.upsert_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch(
            "utils.db.platform_migration_checkpoints.upsert_checkpoint",
            new_callable=AsyncMock,
        ) as mock_checkpoint,
    ):
        yield {
            "dry_run": mock_dry_run,
            "get_one": mock_get_one,
            "upsert": mock_upsert,
            "checkpoint": mock_checkpoint,
            "guild": _mock_guild,
        }


def _summary_with(candidates):
    """Build a DryRunSummary stand-in returned by the mocked dry_run."""
    counts: dict[str, int] = {}
    for c in candidates:
        counts[c.classification] = counts.get(c.classification, 0) + 1
    return binding_backfill.DryRunSummary(
        guild_id=42,
        started_at=datetime.now(),
        completed_at=datetime.now(),
        summary_version=binding_backfill.SUMMARY_VERSION,
        candidates=tuple(candidates),
        counts=counts,
    )


def _candidate(
    *,
    legacy_key="xp_announce_channel",
    subsystem="xp",
    binding_name="announce_channel",
    kind="channel",
    legacy_target_id=999,
    binding_target_id=None,
    binding_status=None,
    classification=binding_backfill.Classification.CANDIDATE_VALID.value,
):
    return binding_backfill.CandidateResult(
        legacy_key=legacy_key,
        subsystem=subsystem,
        binding_name=binding_name,
        kind=kind,
        legacy_target_id=legacy_target_id,
        legacy_raw=str(legacy_target_id) if legacy_target_id else None,
        binding_target_id=binding_target_id,
        binding_status=binding_status,
        classification=classification,
        reason="test",
    )


# ---------------------------------------------------------------------------
# Happy path: one CANDIDATE_VALID written, others skipped
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_writes_only_candidate_valid(_patches):
    p = _patches
    # Three candidates: one valid, one already-bound, one blocked
    candidates = [
        _candidate(legacy_target_id=999),  # CANDIDATE_VALID
        _candidate(
            subsystem="economy",
            binding_name="log_channel",
            legacy_target_id=111,
            classification=binding_backfill.Classification.MATCH.value,
        ),
        _candidate(
            subsystem="governance",
            binding_name="trusted_role",
            kind="role",
            legacy_target_id=222,
            classification=binding_backfill.Classification.BLOCKED_NO_SCHEMA.value,
        ),
    ]
    p["dry_run"].return_value = _summary_with(candidates)
    p["get_one"].return_value = None  # no binding row yet

    result = await apply_backfill(p["guild"], actor_id=7777, advisory_lock=False)

    # Exactly one upsert call (the CANDIDATE_VALID candidate)
    p["upsert"].assert_awaited_once()
    upsert_call = p["upsert"].await_args
    assert upsert_call.kwargs["subsystem"] == "xp"
    assert upsert_call.kwargs["binding_name"] == "announce_channel"
    assert upsert_call.kwargs["target_id"] == 999
    assert upsert_call.kwargs["actor_type"] == "backfill"
    assert upsert_call.kwargs["actor_id"] == 7777
    # mutation_id is a valid UUID (36 chars)
    assert len(upsert_call.kwargs["mutation_id"]) == 36
    # WriteResult shape
    assert len(result.writes) == 3
    statuses = {w.write_status for w in result.writes}
    assert statuses == {
        WRITE_STATUS_WRITTEN,
        WRITE_STATUS_SKIPPED_NOT_CANDIDATE,
    }
    assert result.write_status_counts[WRITE_STATUS_WRITTEN] == 1
    assert result.write_status_counts[WRITE_STATUS_SKIPPED_NOT_CANDIDATE] == 2
    assert result.actor_id == 7777
    assert result.error is None


# ---------------------------------------------------------------------------
# Idempotency: re-running on an already-correct binding skips the write
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_idempotent_skips_already_matching_binding(_patches):
    """A second apply_backfill run on an already-backfilled guild produces no writes."""
    p = _patches
    p["dry_run"].return_value = _summary_with(
        [_candidate(legacy_target_id=999)],
    )
    # Existing row already matches what backfill wants to write
    p["get_one"].return_value = {
        "guild_id": 42,
        "subsystem": "xp",
        "binding_name": "announce_channel",
        "kind": "channel",
        "target_id": 999,
        "status": ResourceStatus.BOUND.value,
        "last_validated_at": None,
        "last_updated_at": None,
        "version": 1,
    }

    result = await apply_backfill(p["guild"], actor_id=7777, advisory_lock=False)

    p["upsert"].assert_not_awaited()
    assert result.write_status_counts[WRITE_STATUS_SKIPPED_IDEMPOTENT] == 1


# ---------------------------------------------------------------------------
# Re-binds when target changed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_rebinds_when_existing_row_has_different_target(_patches):
    p = _patches
    p["dry_run"].return_value = _summary_with(
        [_candidate(legacy_target_id=999)],
    )
    # Existing row has the SAME slot but a DIFFERENT target_id
    p["get_one"].return_value = {
        "guild_id": 42,
        "subsystem": "xp",
        "binding_name": "announce_channel",
        "kind": "channel",
        "target_id": 111,
        "status": ResourceStatus.BOUND.value,
        "last_validated_at": None,
        "last_updated_at": None,
        "version": 1,
    }

    await apply_backfill(p["guild"], actor_id=7777, advisory_lock=False)

    p["upsert"].assert_awaited_once()
    call = p["upsert"].await_args
    # Old target captured in the audit
    assert call.kwargs["old_target_id"] == 111
    assert call.kwargs["target_id"] == 999


# ---------------------------------------------------------------------------
# Apply records pre/post counts via two dry_run calls
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_calls_dry_run_twice_for_pre_and_post(_patches):
    p = _patches
    p["dry_run"].side_effect = [
        _summary_with([_candidate(legacy_target_id=999)]),
        _summary_with(
            [
                _candidate(
                    legacy_target_id=999,
                    binding_target_id=999,
                    binding_status="bound",
                    classification=binding_backfill.Classification.MATCH.value,
                )
            ],
        ),
    ]
    p["get_one"].return_value = None

    result = await apply_backfill(p["guild"], actor_id=7777, advisory_lock=False)

    assert p["dry_run"].await_count == 2
    assert result.pre_counts == {
        binding_backfill.Classification.CANDIDATE_VALID.value: 1,
    }
    assert result.post_counts == {
        binding_backfill.Classification.MATCH.value: 1,
    }


# ---------------------------------------------------------------------------
# Checkpoint lifecycle: in_progress → terminal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_writes_in_progress_then_complete_checkpoints(_patches):
    p = _patches
    p["dry_run"].return_value = _summary_with(
        [_candidate(legacy_target_id=999)],
    )
    p["get_one"].return_value = None

    await apply_backfill(p["guild"], actor_id=7777, advisory_lock=False)

    # Two checkpoint upsert calls: 'in_progress' and 'complete'
    statuses = [call.kwargs["status"] for call in p["checkpoint"].await_args_list]
    assert statuses[0] == "in_progress"
    assert statuses[-1] == "complete"
    # Terminal checkpoint carries the full result summary
    final_call = p["checkpoint"].await_args_list[-1]
    assert final_call.kwargs["mark_completed"] is True
    summary = final_call.kwargs["summary_json"]
    assert summary["pre_counts"]
    assert summary["post_counts"]
    assert summary["actor_id"] == 7777


# ---------------------------------------------------------------------------
# Failure path: upsert raises → terminal status='failed' + per-write error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_marks_failed_when_upsert_raises(_patches):
    p = _patches
    p["dry_run"].return_value = _summary_with(
        [_candidate(legacy_target_id=999)],
    )
    p["get_one"].return_value = None
    p["upsert"].side_effect = RuntimeError("DB blip")

    result = await apply_backfill(p["guild"], actor_id=7777, advisory_lock=False)

    assert result.write_status_counts[WRITE_STATUS_FAILED] == 1
    write = result.writes[0]
    assert write.write_status == WRITE_STATUS_FAILED
    assert "RuntimeError" in write.error
    # Terminal checkpoint marked failed
    final_call = p["checkpoint"].await_args_list[-1]
    assert final_call.kwargs["status"] == "failed"


# ---------------------------------------------------------------------------
# Backfill does NOT call BindingMutationPipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_does_not_use_binding_mutation_pipeline(_patches):
    """Backfill bypasses the user-facing pipeline.

    Discord-actor authority does not apply: backfill uses a dedicated
    'backfill' actor_type recorded in the audit, with the operator's
    actor_id.  This test pins the contract by asserting the user-facing
    pipeline's primitive is never invoked.
    """
    p = _patches
    p["dry_run"].return_value = _summary_with(
        [_candidate(legacy_target_id=999)],
    )
    p["get_one"].return_value = None

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
    ) as mock_pipeline_cls:
        await apply_backfill(p["guild"], actor_id=7777, advisory_lock=False)
    mock_pipeline_cls.assert_not_called()


# ---------------------------------------------------------------------------
# Advisory lock: refuses to run when held
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_raises_when_advisory_lock_held(_mock_guild):
    """A concurrent backfill on the same guild must fail loudly."""
    # Mock the pool: pg_try_advisory_lock returns False
    conn = MagicMock()
    conn.fetchval = AsyncMock(return_value=False)
    conn.execute = AsyncMock()

    pool_mock = MagicMock()
    pool_mock.acquire = AsyncMock(return_value=conn)
    pool_mock.release = AsyncMock()

    with patch("utils.db.pool.get", return_value=pool_mock):
        with pytest.raises(BackfillLockHeldError):
            await apply_backfill(_mock_guild, actor_id=7777, advisory_lock=True)


# ---------------------------------------------------------------------------
# Advisory lock key is deterministic and per-guild
# ---------------------------------------------------------------------------


def test_advisory_lock_key_deterministic():
    a1 = binding_backfill._advisory_lock_key(42)
    a2 = binding_backfill._advisory_lock_key(42)
    assert a1 == a2


def test_advisory_lock_key_differs_per_guild():
    a = binding_backfill._advisory_lock_key(42)
    b = binding_backfill._advisory_lock_key(43)
    assert a != b


def test_advisory_lock_key_fits_signed_int64():
    """pg_advisory_lock(int8) takes a signed 64-bit integer."""
    key = binding_backfill._advisory_lock_key(2**62)
    assert -(2**63) <= key < 2**63

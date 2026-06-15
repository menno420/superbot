"""Phase 2 PR-5 — services.binding_backfill.dry_run end-to-end behaviour.

Verifies the dry-run wrapper:

* iterates every entry in :data:`MIGRATED_KEYS`,
* reads legacy via ``utils.db.settings.get_setting``,
* reads binding via ``core.runtime.bindings.get_binding``,
* validates the legacy target via
  ``core.runtime.bindings.validate_binding_target``,
* writes a single ``platform_migration_checkpoints`` row with the
  structured summary,
* never writes to ``subsystem_bindings``.

Discord ``Guild`` is mocked because the dry-run only reads guild.id;
the actual validation calls are mocked so we can drive each
classification deterministically.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.resources.status import ResourceStatus
from core.runtime.bindings import BindingValue
from core.runtime.subsystem_schema import BindingKind
from services import binding_backfill
from services.binding_backfill import Classification, dry_run


def _bv(*, target_id, status, last_updated_at=None):
    """Construct a BindingValue with the shape ``get_binding`` returns."""
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
def _patched_dry_run(_mock_guild):
    """Patch the three DB/Discord touchpoints + the checkpoint writer."""
    with (
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
        ) as mock_legacy,
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
        ) as mock_binding,
        patch(
            "core.runtime.bindings.validate_binding_target",
            new_callable=AsyncMock,
        ) as mock_validate,
        patch(
            "utils.db.platform_migration_checkpoints.upsert_checkpoint",
            new_callable=AsyncMock,
        ) as mock_checkpoint,
        patch.object(
            binding_backfill,
            "_schema_declares",
            return_value=True,
        ),
    ):
        yield {
            "legacy": mock_legacy,
            "binding": mock_binding,
            "validate": mock_validate,
            "checkpoint": mock_checkpoint,
            "guild": _mock_guild,
        }


@pytest.mark.asyncio
async def test_dry_run_iterates_every_migrated_key(_patched_dry_run):
    """Every :data:`MIGRATED_KEYS` entry is classified — never short-circuit."""
    p = _patched_dry_run
    p["legacy"].return_value = ""  # all legacy values empty
    p["binding"].side_effect = lambda gid, sub, name: _bv(
        target_id=None,
        status=ResourceStatus.UNRESOLVED,
    )

    summary = await dry_run(p["guild"])

    # Two homed migrated keys today (governance role pointers are DEFERRED —
    # no clean binding schema home yet — so dry_run never touches them).
    assert len(summary.candidates) == 2
    assert {c.subsystem for c in summary.candidates} == {"xp", "economy"}
    # All classified BOTH_ABSENT because legacy is empty + no binding row
    assert all(
        c.classification == Classification.BOTH_ABSENT.value for c in summary.candidates
    )
    assert summary.counts == {Classification.BOTH_ABSENT.value: 2}


@pytest.mark.asyncio
async def test_dry_run_records_checkpoint(_patched_dry_run):
    """One ``upsert_checkpoint`` call with status='dry_run_complete'."""
    p = _patched_dry_run
    p["legacy"].return_value = ""
    p["binding"].side_effect = lambda gid, sub, name: _bv(
        target_id=None,
        status=ResourceStatus.UNRESOLVED,
    )

    await dry_run(p["guild"])

    p["checkpoint"].assert_awaited_once()
    call = p["checkpoint"].await_args
    assert call.kwargs["name"] == "binding_backfill"
    assert call.kwargs["guild_id"] == 42
    assert call.kwargs["status"] == "dry_run_complete"
    assert call.kwargs["mark_completed"] is True
    # summary_json carries counts + candidates
    summary = call.kwargs["summary_json"]
    assert summary["counts"] == {Classification.BOTH_ABSENT.value: 2}
    assert len(summary["candidates"]) == 2


@pytest.mark.asyncio
async def test_dry_run_legacy_only_candidate_valid(_patched_dry_run):
    """A legacy-only XP announce channel with a valid target → CANDIDATE_VALID."""
    p = _patched_dry_run

    async def legacy_lookup(guild_id, key, default=""):
        if key == "xp_announce_channel":
            return "999"
        return ""

    p["legacy"].side_effect = legacy_lookup
    p["binding"].side_effect = lambda gid, sub, name: _bv(
        target_id=None,
        status=ResourceStatus.UNRESOLVED,
    )
    p["validate"].return_value = ResourceStatus.BOUND

    summary = await dry_run(p["guild"])
    xp = next(c for c in summary.candidates if c.subsystem == "xp")
    assert xp.classification == Classification.CANDIDATE_VALID.value
    assert xp.legacy_target_id == 999
    assert xp.binding_target_id is None


@pytest.mark.asyncio
async def test_dry_run_legacy_with_missing_target(_patched_dry_run):
    """Legacy points at a deleted channel → CANDIDATE_INVALID_TARGET_MISSING."""
    p = _patched_dry_run

    async def legacy_lookup(guild_id, key, default=""):
        if key == "xp_announce_channel":
            return "999"
        return ""

    p["legacy"].side_effect = legacy_lookup
    p["binding"].side_effect = lambda gid, sub, name: _bv(
        target_id=None,
        status=ResourceStatus.UNRESOLVED,
    )
    p["validate"].return_value = ResourceStatus.MISSING

    summary = await dry_run(p["guild"])
    xp = next(c for c in summary.candidates if c.subsystem == "xp")
    assert xp.classification == Classification.CANDIDATE_INVALID_TARGET_MISSING.value


@pytest.mark.asyncio
async def test_dry_run_both_present_match(_patched_dry_run):
    """Legacy + binding agree → MATCH."""
    p = _patched_dry_run
    now = datetime.now()

    async def legacy_lookup(guild_id, key, default=""):
        if key == "xp_announce_channel":
            return "999"
        return ""

    p["legacy"].side_effect = legacy_lookup
    p["binding"].side_effect = lambda gid, sub, name: _bv(
        target_id=999 if sub == "xp" else None,
        status=ResourceStatus.BOUND if sub == "xp" else ResourceStatus.UNRESOLVED,
        last_updated_at=now if sub == "xp" else None,
    )
    p["validate"].return_value = ResourceStatus.BOUND

    summary = await dry_run(p["guild"])
    xp = next(c for c in summary.candidates if c.subsystem == "xp")
    assert xp.classification == Classification.MATCH.value


@pytest.mark.asyncio
async def test_dry_run_both_present_disagree(_patched_dry_run):
    p = _patched_dry_run
    now = datetime.now()

    async def legacy_lookup(guild_id, key, default=""):
        if key == "xp_announce_channel":
            return "999"
        return ""

    p["legacy"].side_effect = legacy_lookup
    p["binding"].side_effect = lambda gid, sub, name: _bv(
        target_id=111 if sub == "xp" else None,
        status=ResourceStatus.BOUND if sub == "xp" else ResourceStatus.UNRESOLVED,
        last_updated_at=now if sub == "xp" else None,
    )
    p["validate"].return_value = ResourceStatus.BOUND

    summary = await dry_run(p["guild"])
    xp = next(c for c in summary.candidates if c.subsystem == "xp")
    assert xp.classification == Classification.DISAGREE.value


@pytest.mark.asyncio
async def test_dry_run_excludes_deferred_keys(_mock_guild):
    """dry_run never classifies a :data:`DEFERRED_KEYS` pointer.

    The governance trusted/moderator role pointers have no clean binding
    schema home yet (the reserved ``governance`` namespace), so they live in
    ``DEFERRED_KEYS`` and dry_run must not touch them — otherwise every guild
    would get a permanent ``BLOCKED_NO_SCHEMA`` finding (not production-ready
    machinery).  The ``BLOCKED_NO_SCHEMA`` classifier path itself is still
    covered synthetically in ``test_classification.py``.
    """
    with (
        patch(
            "utils.db.settings.get_setting",
            new_callable=AsyncMock,
            return_value="999",
        ),
        patch(
            "core.runtime.bindings.get_binding",
            new_callable=AsyncMock,
            side_effect=lambda gid, sub, name: _bv(
                target_id=None,
                status=ResourceStatus.UNRESOLVED,
            ),
        ),
        patch(
            "core.runtime.bindings.validate_binding_target",
            new_callable=AsyncMock,
            return_value=ResourceStatus.BOUND,
        ),
        patch(
            "utils.db.platform_migration_checkpoints.upsert_checkpoint",
            new_callable=AsyncMock,
        ),
        patch.object(binding_backfill, "_schema_declares", return_value=True),
    ):
        summary = await dry_run(_mock_guild)

    classified_keys = {c.legacy_key for c in summary.candidates}
    deferred_keys = {k.legacy_key for k in binding_backfill.DEFERRED_KEYS}
    assert (
        deferred_keys
    ), "DEFERRED_KEYS should be non-empty while governance is unhomed"
    assert classified_keys.isdisjoint(deferred_keys)
    # No governance subsystem candidate is produced.
    assert all(c.subsystem != "governance" for c in summary.candidates)


@pytest.mark.asyncio
async def test_dry_run_does_not_write_to_subsystem_bindings(_patched_dry_run):
    """Dry-run is read-only against ``subsystem_bindings``.

    Pin the contract by patching the two mutation primitives — they
    must never be awaited during a dry-run.
    """
    p = _patched_dry_run
    p["legacy"].return_value = "999"
    p["binding"].side_effect = lambda gid, sub, name: _bv(
        target_id=None,
        status=ResourceStatus.UNRESOLVED,
    )
    p["validate"].return_value = ResourceStatus.BOUND

    with (
        patch(
            "utils.db.bindings.upsert_with_audit",
            new_callable=AsyncMock,
        ) as mock_upsert,
        patch(
            "utils.db.bindings.clear_with_audit",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await dry_run(p["guild"])
    mock_upsert.assert_not_awaited()
    mock_clear.assert_not_awaited()


@pytest.mark.asyncio
async def test_dry_run_idempotent_upsert_uses_same_key(_patched_dry_run):
    """Re-running dry-run for the same guild upserts the same checkpoint row."""
    p = _patched_dry_run
    p["legacy"].return_value = ""
    p["binding"].side_effect = lambda gid, sub, name: _bv(
        target_id=None,
        status=ResourceStatus.UNRESOLVED,
    )

    await dry_run(p["guild"])
    await dry_run(p["guild"])

    assert p["checkpoint"].await_count == 2
    # Both calls used the same (name, guild_id)
    for call in p["checkpoint"].await_args_list:
        assert call.kwargs["name"] == "binding_backfill"
        assert call.kwargs["guild_id"] == 42

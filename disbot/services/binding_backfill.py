"""Binding backfill — dry-run + reconciliation (Phase 2, PR-5).

Read-only planner for the legacy → ``subsystem_bindings`` migration.
This module **does not write** to ``subsystem_bindings``; PR-6 adds the
write path through a dedicated ``BindingBackfillPipeline``.  PR-5
exists so the operator can review what a real backfill would do
*before* any rows are touched, and so the diagnostics surface can
surface drift / disagreement / missing-target cases.

Migrated key registry:

The :data:`MIGRATED_KEYS` constant declares every legacy key the
backfill plan covers, paired with the typed ``(subsystem,
binding_name, kind)`` it should land at.  Initial set (per the Phase 2
plan):

* ``xp_announce_channel`` → ``(xp, announce_channel, CHANNEL)``
* ``economy_log_channel`` → ``(economy, log_channel, CHANNEL)``
* ``trusted_tier_role_id`` → ``(governance, trusted_role, ROLE)``

XP threshold roles are intentionally excluded — the 1:N (level → role)
shape does not fit ``subsystem_bindings``' 1:1 schema; a dedicated
``xp_threshold_roles`` table is the right shape and will land in a
future PR.

Classifications:

Every ``(guild, migrated_key)`` pair is classified into exactly one
:class:`Classification` value.  The operator inspects the per-key
results before authorising the PR-6 write phase.

Dry-run output:

The per-guild dry-run writes one row to
``platform_migration_checkpoints`` with::

    name        = "binding_backfill"
    guild_id    = <guild>
    status      = "dry_run_complete"
    version     = 1
    summary_json = {
        "candidates": [...],
        "counts": {<classification>: N, ...},
    }

Re-running a dry-run for the same guild upserts the row.  An operator
can then ``SELECT summary_json FROM platform_migration_checkpoints
WHERE name='binding_backfill' AND guild_id = X`` to review.

The module also exposes the same primitives synchronously
(``classify_candidate``) so unit tests can exercise the matrix
without touching DB or Discord.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import discord

from core.resources.status import ResourceStatus
from core.runtime.subsystem_schema import BindingKind, get_schema
from utils.settings_keys.economy import ECONOMY_LOG_CHANNEL
from utils.settings_keys.governance import TRUSTED_TIER_ROLE_ID
from utils.settings_keys.xp import XP_ANNOUNCE_CHANNEL

logger = logging.getLogger("bot.services.binding_backfill")

# Migration name written to ``platform_migration_checkpoints.name``.
MIGRATION_NAME = "binding_backfill"

# Schema version of ``summary_json``.  Bump when the dict shape
# changes so the operator can detect mixed runs.
SUMMARY_VERSION = 1


# ---------------------------------------------------------------------------
# Migrated key registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MigratedKey:
    """Declarative mapping from a legacy KV key to a typed binding slot."""

    legacy_key: str
    subsystem: str
    binding_name: str
    kind: BindingKind


MIGRATED_KEYS: tuple[MigratedKey, ...] = (
    MigratedKey(
        legacy_key=XP_ANNOUNCE_CHANNEL,
        subsystem="xp",
        binding_name="announce_channel",
        kind=BindingKind.CHANNEL,
    ),
    MigratedKey(
        legacy_key=ECONOMY_LOG_CHANNEL,
        subsystem="economy",
        binding_name="log_channel",
        kind=BindingKind.CHANNEL,
    ),
    MigratedKey(
        legacy_key=TRUSTED_TIER_ROLE_ID,
        subsystem="governance",
        binding_name="trusted_role",
        kind=BindingKind.ROLE,
    ),
)


# ---------------------------------------------------------------------------
# Classification taxonomy
# ---------------------------------------------------------------------------


class Classification(str, Enum):
    """Outcome of classifying a single ``(guild, migrated_key)`` pair.

    String-valued so the literal is JSON-friendly inside
    ``summary_json``.
    """

    # Nothing to do — neither side has a value.
    BOTH_ABSENT = "both_absent"

    # Legacy has a value, no binding row yet, target validates.
    # This is the primary backfill candidate.
    CANDIDATE_VALID = "candidate_valid"

    # Legacy has a value but the target is missing (channel/role
    # deleted, or numeric junk).  Skip — operator must investigate.
    CANDIDATE_INVALID_TARGET_MISSING = "candidate_invalid_target_missing"

    # Legacy has a value but it's not a valid integer or otherwise
    # cannot be parsed.
    CANDIDATE_INVALID_UNPARSEABLE = "candidate_invalid_unparseable"

    # Legacy has a value but its kind is wrong (e.g. legacy
    # XP_ANNOUNCE_CHANNEL points at a role ID).  Skip — operator
    # must investigate.
    CANDIDATE_INVALID_WRONG_KIND = "candidate_invalid_wrong_kind"

    # Binding row exists, legacy missing.  Rare; usually means a
    # previous backfill already ran or the operator wrote bindings
    # directly.
    BINDING_ONLY = "binding_only"

    # Both sides present and the target IDs match.
    MATCH = "match"

    # Both sides present but they disagree — operator must reconcile.
    DISAGREE = "disagree"

    # Binding row exists with status != BOUND (MISSING / INVALID /
    # UNRESOLVED).  Recorded as a finding even when legacy is also
    # present; the operator may decide to re-bind via the wizard.
    BINDING_STATUS_NOT_BOUND = "binding_status_not_bound"

    # Subsystem has no declared SubsystemSchema or no matching
    # BindingSpec.  Backfill is blocked until the schema is declared.
    BLOCKED_NO_SCHEMA = "blocked_no_schema"


# Classifications that are safe candidates for the PR-6 write phase.
WRITABLE_CLASSIFICATIONS: frozenset[Classification] = frozenset(
    {Classification.CANDIDATE_VALID},
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateResult:
    """One ``(guild, migrated_key)`` classification result.

    Carries enough provenance that ``summary_json`` is operator-readable
    without consulting source.
    """

    legacy_key: str
    subsystem: str
    binding_name: str
    kind: str  # BindingKind.value
    legacy_target_id: int | None
    legacy_raw: str | None
    binding_target_id: int | None
    binding_status: str | None  # ResourceStatus.value or None
    classification: str  # Classification.value
    reason: str

    def to_summary_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DryRunSummary:
    """Outcome of :func:`dry_run` for one guild."""

    guild_id: int
    started_at: datetime
    completed_at: datetime
    summary_version: int
    candidates: tuple[CandidateResult, ...]
    counts: dict[str, int]

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "summary_version": self.summary_version,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "candidates": [c.to_summary_dict() for c in self.candidates],
            "counts": dict(self.counts),
        }


# ---------------------------------------------------------------------------
# Pure classification (synchronous; testable without DB or Discord)
# ---------------------------------------------------------------------------


def _parse_legacy_id(raw: str | None) -> tuple[int | None, str]:
    """Best-effort parse of a legacy KV value into a snowflake.

    Returns ``(parsed_id, reason)``.  ``parsed_id`` is ``None`` when
    the value is missing, empty, or unparseable.
    """
    if raw is None or raw == "":
        return None, "legacy value empty"
    try:
        return int(raw), "legacy value parsed"
    except (TypeError, ValueError):
        return None, f"legacy value {raw!r} is not a snowflake"


def classify_candidate(
    *,
    migrated_key: MigratedKey,
    legacy_raw: str | None,
    legacy_validated_status: ResourceStatus | None,
    binding_target_id: int | None,
    binding_status: ResourceStatus | None,
    schema_declared: bool,
) -> tuple[Classification, str]:
    """Pure classifier — no DB, no Discord.  Returns (classification, reason).

    Inputs:

    * ``migrated_key`` — declarative mapping for the key being checked.
    * ``legacy_raw`` — the raw KV value (or ``None`` for missing).
    * ``legacy_validated_status`` — the result of validating the
      parsed legacy ID against the live guild.  ``None`` when no
      legacy value exists or parsing failed.
    * ``binding_target_id`` — current ``subsystem_bindings.target_id``
      (``None`` when no row exists OR row exists with NULL target).
    * ``binding_status`` — current ``subsystem_bindings.status``
      (``None`` when no row exists).
    * ``schema_declared`` — whether ``get_schema(subsystem)`` returns
      a schema that declares this ``binding_name``.

    Returns a ``(Classification, human-readable reason)`` tuple.
    """
    legacy_id, parse_reason = _parse_legacy_id(legacy_raw)

    # Schema gate (applies regardless of side presence — backfill
    # cannot proceed without a declared BindingSpec).
    if not schema_declared:
        return (
            Classification.BLOCKED_NO_SCHEMA,
            (
                f"subsystem {migrated_key.subsystem!r} has no registered "
                f"SubsystemSchema with binding {migrated_key.binding_name!r}; "
                "register one before backfill"
            ),
        )

    # Categorise the two sides.
    legacy_present = legacy_raw is not None and legacy_raw != ""
    binding_present = binding_target_id is not None or binding_status is not None

    # 1) Both absent.
    if not legacy_present and not binding_present:
        return Classification.BOTH_ABSENT, "neither legacy nor binding has a value"

    # 2) Binding only.
    if not legacy_present and binding_present:
        if binding_status is not None and binding_status is not ResourceStatus.BOUND:
            return (
                Classification.BINDING_STATUS_NOT_BOUND,
                f"binding row present with status={binding_status.value!r}",
            )
        return (
            Classification.BINDING_ONLY,
            "binding row present, legacy missing (no backfill needed)",
        )

    # 3) Legacy only.
    if legacy_present and not binding_present:
        if legacy_id is None:
            return (
                Classification.CANDIDATE_INVALID_UNPARSEABLE,
                parse_reason,
            )
        if legacy_validated_status is ResourceStatus.MISSING:
            return (
                Classification.CANDIDATE_INVALID_TARGET_MISSING,
                f"legacy target id={legacy_id} does not exist in the guild",
            )
        if legacy_validated_status is ResourceStatus.INVALID:
            return (
                Classification.CANDIDATE_INVALID_WRONG_KIND,
                (
                    f"legacy target id={legacy_id} exists but does not match "
                    f"declared kind={migrated_key.kind.value!r}"
                ),
            )
        if legacy_validated_status is ResourceStatus.BOUND:
            return (
                Classification.CANDIDATE_VALID,
                f"legacy id={legacy_id} validates; safe to backfill",
            )
        # UNRESOLVED — treat as missing for safety.
        return (
            Classification.CANDIDATE_INVALID_TARGET_MISSING,
            f"legacy target id={legacy_id} could not be resolved",
        )

    # 4) Both present.  Reconcile.
    if binding_status is not None and binding_status is not ResourceStatus.BOUND:
        return (
            Classification.BINDING_STATUS_NOT_BOUND,
            (
                f"both sides present; binding status={binding_status.value!r} "
                f"(operator may want to re-bind via the wizard)"
            ),
        )
    if legacy_id is None:
        # Legacy unparseable but a binding exists — trust the binding.
        return (
            Classification.BINDING_ONLY,
            f"legacy value unparseable ({parse_reason}); binding has a value",
        )
    if legacy_id == binding_target_id:
        return Classification.MATCH, "legacy and binding agree"
    return (
        Classification.DISAGREE,
        (
            f"legacy id={legacy_id} disagrees with binding "
            f"target_id={binding_target_id}; operator must reconcile"
        ),
    )


# ---------------------------------------------------------------------------
# Async dry-run (reads DB + Discord; never writes to subsystem_bindings)
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _schema_declares(subsystem: str, binding_name: str) -> bool:
    schema = get_schema(subsystem)
    if schema is None:
        return False
    return any(spec.name == binding_name for spec in schema.bindings)


async def dry_run(guild: discord.Guild) -> DryRunSummary:
    """Classify every migrated key for ``guild`` and persist a checkpoint.

    Reads:

    * Legacy KV via :func:`utils.db.settings.get_setting`.
    * Current binding row via :func:`core.runtime.bindings.get_binding`.
    * Live target validation via
      :func:`core.runtime.bindings.validate_binding_target`.

    Writes:

    * One row to ``platform_migration_checkpoints`` with
      ``name="binding_backfill"``, ``guild_id=<guild.id>``,
      ``status="dry_run_complete"``, and the structured summary.

    Does NOT write to ``subsystem_bindings``.  The PR-6 write phase
    consumes the candidates with classification ``CANDIDATE_VALID``
    from this summary.
    """
    # Local imports to keep this module out of any module-load cycles.
    from core.runtime.bindings import get_binding, validate_binding_target
    from utils.db import platform_migration_checkpoints as checkpoint_db
    from utils.db import settings as settings_db

    started_at = _now_utc()
    candidates: list[CandidateResult] = []

    for key in MIGRATED_KEYS:
        legacy_raw = await settings_db.get_setting(
            guild.id,
            key.legacy_key,
            default="",
        )
        legacy_raw_norm = legacy_raw or None
        legacy_id, _ = _parse_legacy_id(legacy_raw_norm)

        # Validate the legacy target (if parseable) so the classifier
        # has the live-resource status.  Skip validation when the
        # legacy value is empty/unparseable.
        legacy_validated_status: ResourceStatus | None = None
        if legacy_id is not None:
            try:
                legacy_validated_status = await validate_binding_target(
                    guild,
                    key.kind,
                    legacy_id,
                )
            except Exception as exc:  # noqa: BLE001 — dry-run must not raise
                logger.warning(
                    "binding_backfill.dry_run: validate_binding_target raised "
                    "for guild=%d key=%r (%r); treating as UNRESOLVED",
                    guild.id,
                    key.legacy_key,
                    exc,
                )
                legacy_validated_status = ResourceStatus.UNRESOLVED

        # Read the binding row.  ``get_binding`` returns a fresh
        # ``BindingValue`` even when no DB row exists (with status
        # UNRESOLVED + target_id None); the classifier distinguishes
        # "no row" from "row with NULL target" via the presence of a
        # ``last_updated_at``.
        try:
            bv = await get_binding(guild.id, key.subsystem, key.binding_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "binding_backfill.dry_run: get_binding raised for "
                "guild=%d subsystem=%r binding=%r (%r); skipping",
                guild.id,
                key.subsystem,
                key.binding_name,
                exc,
            )
            classification, reason = (
                Classification.BLOCKED_NO_SCHEMA,
                f"get_binding raised: {type(exc).__name__}",
            )
            candidates.append(
                CandidateResult(
                    legacy_key=key.legacy_key,
                    subsystem=key.subsystem,
                    binding_name=key.binding_name,
                    kind=key.kind.value,
                    legacy_target_id=legacy_id,
                    legacy_raw=legacy_raw_norm,
                    binding_target_id=None,
                    binding_status=None,
                    classification=classification.value,
                    reason=reason,
                ),
            )
            continue

        # Treat "row present" as "we have a last_updated_at OR a
        # non-null target_id".  A row with NULL target_id is still a
        # declared slot; in classify_candidate we treat it as
        # binding_present so the operator sees BINDING_STATUS_NOT_BOUND.
        binding_row_present = bv.last_updated_at is not None
        classification, reason = classify_candidate(
            migrated_key=key,
            legacy_raw=legacy_raw_norm,
            legacy_validated_status=legacy_validated_status,
            binding_target_id=bv.target_id if binding_row_present else None,
            binding_status=bv.status if binding_row_present else None,
            schema_declared=_schema_declares(key.subsystem, key.binding_name),
        )

        candidates.append(
            CandidateResult(
                legacy_key=key.legacy_key,
                subsystem=key.subsystem,
                binding_name=key.binding_name,
                kind=key.kind.value,
                legacy_target_id=legacy_id,
                legacy_raw=legacy_raw_norm,
                binding_target_id=bv.target_id if binding_row_present else None,
                binding_status=(bv.status.value if binding_row_present else None),
                classification=classification.value,
                reason=reason,
            ),
        )

    completed_at = _now_utc()
    counts: dict[str, int] = {}
    for c in candidates:
        counts[c.classification] = counts.get(c.classification, 0) + 1

    summary = DryRunSummary(
        guild_id=guild.id,
        started_at=started_at,
        completed_at=completed_at,
        summary_version=SUMMARY_VERSION,
        candidates=tuple(candidates),
        counts=counts,
    )

    # Persist the checkpoint — idempotent upsert by (name, guild_id).
    await checkpoint_db.upsert_checkpoint(
        name=MIGRATION_NAME,
        guild_id=guild.id,
        status="dry_run_complete",
        version=SUMMARY_VERSION,
        summary_json=summary.to_summary_dict(),
        mark_completed=True,
    )

    return summary


# ---------------------------------------------------------------------------
# Apply phase — PR-6.  Writes CANDIDATE_VALID candidates from a fresh
# dry-run through ``utils.db.bindings.upsert_with_audit`` with
# ``actor_type='backfill'``.  Legacy reads remain authoritative.
# ---------------------------------------------------------------------------


class BindingBackfillError(Exception):
    """Base class for binding-backfill write-phase failures."""


class BackfillLockHeldError(BindingBackfillError):
    """Raised when another session holds the advisory lock for this guild."""


# Result statuses recorded per candidate during the write phase.
WRITE_STATUS_WRITTEN = "written"
WRITE_STATUS_SKIPPED_IDEMPOTENT = "skipped_idempotent"
WRITE_STATUS_SKIPPED_NOT_CANDIDATE = "skipped_not_candidate"
WRITE_STATUS_FAILED = "failed"


@dataclass(frozen=True)
class WriteResult:
    """One candidate's write outcome.

    ``mutation_id`` is non-empty for ``written`` rows (the UUID that
    was passed to ``upsert_with_audit``).  For skipped/failed rows it
    is empty so the operator can immediately tell which audit rows
    are theirs.
    """

    legacy_key: str
    subsystem: str
    binding_name: str
    target_id: int | None
    write_status: str
    classification: str
    mutation_id: str
    error: str | None

    def to_summary_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ApplyResult:
    """Aggregate write-phase outcome for one guild."""

    guild_id: int
    started_at: datetime
    completed_at: datetime
    actor_id: int
    summary_version: int
    pre_counts: dict[str, int]
    post_counts: dict[str, int]
    writes: tuple[WriteResult, ...]
    write_status_counts: dict[str, int]
    error: str | None  # populated for status='failed' runs

    @property
    def is_failure(self) -> bool:
        return self.error is not None or self.write_status_counts.get(
            WRITE_STATUS_FAILED,
            0,
        )

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "summary_version": self.summary_version,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "actor_id": self.actor_id,
            "pre_counts": dict(self.pre_counts),
            "post_counts": dict(self.post_counts),
            "writes": [w.to_summary_dict() for w in self.writes],
            "write_status_counts": dict(self.write_status_counts),
            "error": self.error,
        }


def _advisory_lock_key(guild_id: int) -> int:
    """Stable signed-int64 advisory-lock key for ``(MIGRATION_NAME, guild_id)``.

    PostgreSQL's ``pg_try_advisory_lock(int8)`` takes one signed 64-bit
    integer.  We derive a stable key from a sha256 of
    ``"binding_backfill:<guild_id>"`` so concurrent runs across the
    same (migration, guild) collide deterministically, while different
    guilds never collide with each other.
    """
    import hashlib

    digest = hashlib.sha256(
        f"{MIGRATION_NAME}:{guild_id}".encode(),
    ).digest()
    return int.from_bytes(digest[:8], "big", signed=True)


async def apply_backfill(
    guild: discord.Guild,
    *,
    actor_id: int,
    advisory_lock: bool = True,
) -> ApplyResult:
    """Write every ``CANDIDATE_VALID`` candidate for ``guild``.

    Steps:

    1. If ``advisory_lock`` is True, acquire a session-scoped
       ``pg_try_advisory_lock`` keyed on ``(MIGRATION_NAME, guild_id)``.
       Refuse to run if another session holds the lock.
    2. Mark the per-guild checkpoint as ``in_progress``.
    3. Run :func:`dry_run` (fresh classification — the operator's
       previous dry-run may be stale).
    4. For each ``CANDIDATE_VALID`` candidate:
         - **Pre-check**: read the current binding row.  If the row
           already matches the intended ``target_id`` AND is BOUND,
           record ``skipped_idempotent`` and continue.  This makes
           re-running ``apply_backfill`` truly idempotent — no extra
           audit rows on a no-op re-run.
         - Otherwise call ``utils.db.bindings.upsert_with_audit`` with
           ``actor_type='backfill'`` and ``action='backfill'`` (the
           DB primitive picks the action from actor_type).
         - Record ``written`` with the new mutation_id.
       Other classifications are recorded as
       ``skipped_not_candidate``.
    5. Re-run :func:`dry_run` to compute ``post_counts``.
    6. Upsert the checkpoint with status ``complete`` (or ``failed``
       if any write raised).  ``failed`` rows record their exception
       in the per-write ``error`` field; the operator can re-run
       after investigating.
    7. Release the advisory lock.

    Args:
        guild: target guild.
        actor_id: snowflake of the operator authorising the backfill.
            REQUIRED — the schema enforces ``actor_id NOT NULL`` on
            ``binding_audit_log``, so the operator's identity is
            recorded against every audit row.
        advisory_lock: set False only for tests that drive
            ``pool.get()`` themselves.  Production callers leave the
            default ``True``.

    Raises:
        BackfillLockHeldError: another session is mid-backfill for
            this guild.  Wait and retry, or investigate the stalled
            session.
    """
    # Local imports keep this module out of any module-load cycles.
    from utils.db import bindings as bindings_db
    from utils.db import platform_migration_checkpoints as checkpoint_db
    from utils.db import pool

    started_at = _now_utc()
    error_message: str | None = None
    writes: list[WriteResult] = []
    lock_acquired = False
    lock_conn = None

    try:
        # 1) Advisory lock.
        if advisory_lock:
            lock_key = _advisory_lock_key(guild.id)
            lock_conn = await pool.get().acquire()
            acquired = await lock_conn.fetchval(
                "SELECT pg_try_advisory_lock($1)",
                lock_key,
            )
            if not acquired:
                await pool.get().release(lock_conn)
                msg = (
                    f"another session holds the binding_backfill advisory "
                    f"lock for guild_id={guild.id}; wait and retry"
                )
                raise BackfillLockHeldError(msg)
            lock_acquired = True

        # 2) Mark in_progress so observers can see a backfill is live.
        await checkpoint_db.upsert_checkpoint(
            name=MIGRATION_NAME,
            guild_id=guild.id,
            status="in_progress",
            version=SUMMARY_VERSION,
            summary_json={"phase": "in_progress", "actor_id": actor_id},
        )

        # 3) Fresh dry-run.
        pre = await dry_run(guild)
        pre_counts = dict(pre.counts)

        # 4) Write each CANDIDATE_VALID candidate.
        for candidate in pre.candidates:
            if candidate.classification != Classification.CANDIDATE_VALID.value:
                writes.append(
                    WriteResult(
                        legacy_key=candidate.legacy_key,
                        subsystem=candidate.subsystem,
                        binding_name=candidate.binding_name,
                        target_id=candidate.legacy_target_id,
                        write_status=WRITE_STATUS_SKIPPED_NOT_CANDIDATE,
                        classification=candidate.classification,
                        mutation_id="",
                        error=None,
                    ),
                )
                continue

            target_id = candidate.legacy_target_id
            if target_id is None:
                # Belt-and-braces: CANDIDATE_VALID implies a parseable
                # legacy id, but defend against a future classifier
                # change.
                writes.append(
                    WriteResult(
                        legacy_key=candidate.legacy_key,
                        subsystem=candidate.subsystem,
                        binding_name=candidate.binding_name,
                        target_id=None,
                        write_status=WRITE_STATUS_FAILED,
                        classification=candidate.classification,
                        mutation_id="",
                        error="legacy_target_id missing on CANDIDATE_VALID",
                    ),
                )
                continue

            # Pre-check idempotency.
            current = await bindings_db.get_one(
                guild.id,
                candidate.subsystem,
                candidate.binding_name,
            )
            if (
                current is not None
                and current.get("target_id") == target_id
                and current.get("status") == ResourceStatus.BOUND.value
            ):
                writes.append(
                    WriteResult(
                        legacy_key=candidate.legacy_key,
                        subsystem=candidate.subsystem,
                        binding_name=candidate.binding_name,
                        target_id=target_id,
                        write_status=WRITE_STATUS_SKIPPED_IDEMPOTENT,
                        classification=candidate.classification,
                        mutation_id="",
                        error=None,
                    ),
                )
                continue

            mutation_id = str(uuid.uuid4())
            try:
                await bindings_db.upsert_with_audit(
                    guild_id=guild.id,
                    subsystem=candidate.subsystem,
                    binding_name=candidate.binding_name,
                    kind=candidate.kind,
                    target_id=target_id,
                    status=ResourceStatus.BOUND.value,
                    actor_id=actor_id,
                    actor_type="backfill",
                    mutation_id=mutation_id,
                    old_target_id=(current.get("target_id") if current else None),
                    old_status=(current.get("status") if current else None),
                )
            except Exception as exc:  # noqa: BLE001 — record per-candidate
                logger.exception(
                    "binding_backfill.apply_backfill: write failed "
                    "for guild=%d subsystem=%r binding=%r",
                    guild.id,
                    candidate.subsystem,
                    candidate.binding_name,
                )
                writes.append(
                    WriteResult(
                        legacy_key=candidate.legacy_key,
                        subsystem=candidate.subsystem,
                        binding_name=candidate.binding_name,
                        target_id=target_id,
                        write_status=WRITE_STATUS_FAILED,
                        classification=candidate.classification,
                        mutation_id="",
                        error=f"{type(exc).__name__}: {exc}",
                    ),
                )
                continue
            writes.append(
                WriteResult(
                    legacy_key=candidate.legacy_key,
                    subsystem=candidate.subsystem,
                    binding_name=candidate.binding_name,
                    target_id=target_id,
                    write_status=WRITE_STATUS_WRITTEN,
                    classification=candidate.classification,
                    mutation_id=mutation_id,
                    error=None,
                ),
            )

        # 5) Re-classify post-write.
        post = await dry_run(guild)
        post_counts = dict(post.counts)

    except BindingBackfillError:
        raise
    except Exception as exc:  # noqa: BLE001 — top-level safety net
        logger.exception(
            "binding_backfill.apply_backfill: unexpected failure for guild=%d",
            guild.id,
        )
        error_message = f"{type(exc).__name__}: {exc}"
        pre_counts = {}
        post_counts = {}

    completed_at = _now_utc()
    write_status_counts: dict[str, int] = {}
    for w in writes:
        write_status_counts[w.write_status] = (
            write_status_counts.get(w.write_status, 0) + 1
        )

    result = ApplyResult(
        guild_id=guild.id,
        started_at=started_at,
        completed_at=completed_at,
        actor_id=actor_id,
        summary_version=SUMMARY_VERSION,
        pre_counts=pre_counts,
        post_counts=post_counts,
        writes=tuple(writes),
        write_status_counts=write_status_counts,
        error=error_message,
    )

    # 6) Terminal checkpoint upsert.  Failed if any write raised OR
    #    the top-level safety-net fired.
    terminal_status = (
        "failed"
        if error_message or write_status_counts.get(WRITE_STATUS_FAILED, 0) > 0
        else "complete"
    )
    try:
        await checkpoint_db.upsert_checkpoint(
            name=MIGRATION_NAME,
            guild_id=guild.id,
            status=terminal_status,
            version=SUMMARY_VERSION,
            summary_json=result.to_summary_dict(),
            mark_completed=True,
        )
    except Exception:
        logger.exception(
            "binding_backfill.apply_backfill: terminal checkpoint "
            "upsert failed for guild=%d (write phase already %s)",
            guild.id,
            terminal_status,
        )

    # 7) Release advisory lock.
    if lock_acquired and lock_conn is not None:
        try:
            await lock_conn.execute(
                "SELECT pg_advisory_unlock($1)",
                _advisory_lock_key(guild.id),
            )
        finally:
            await pool.get().release(lock_conn)

    return result


__all__ = [
    "MIGRATED_KEYS",
    "MIGRATION_NAME",
    "SUMMARY_VERSION",
    "WRITABLE_CLASSIFICATIONS",
    "WRITE_STATUS_FAILED",
    "WRITE_STATUS_SKIPPED_IDEMPOTENT",
    "WRITE_STATUS_SKIPPED_NOT_CANDIDATE",
    "WRITE_STATUS_WRITTEN",
    "ApplyResult",
    "BackfillLockHeldError",
    "BindingBackfillError",
    "CandidateResult",
    "Classification",
    "DryRunSummary",
    "MigratedKey",
    "WriteResult",
    "apply_backfill",
    "classify_candidate",
    "dry_run",
]

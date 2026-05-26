"""Setup session lifecycle service — Phase 9e / Track 4 PR 8.

Wraps :mod:`utils.db.setup_session` with the four lifecycle
transitions the launcher cog uses:

* :func:`start_session` — bot just joined or owner clicked Start;
  upserts the row in ``pending``.
* :func:`resume_session` — fetch the row on ``on_ready`` so the
  launcher can re-render in the correct state.
* :func:`mark_in_progress` — owner clicked the wizard's first step.
* :func:`mark_complete` — owner finished a full setup walkthrough.
* :func:`dismiss` — owner deferred the launcher.

All functions are best-effort: a DB error is logged and surfaced via
the return value so the caller can decide whether to retry. None of
them perform Discord-side I/O; the launcher cog (Track 4 PR 9) owns
the embed / view orchestration.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from utils.db import setup_session as db

logger = logging.getLogger("bot.services.setup_session")


@dataclass(frozen=True)
class SetupSession:
    """Snapshot of one row of ``setup_session``."""

    guild_id: int
    guild_name: str
    owner_id: int
    setup_status: str
    setup_channel_id: int | None
    setup_message_id: int | None
    last_readiness_score: int | None
    current_step: str | None
    delegated_admins: tuple[int, ...]
    skipped_sections: frozenset[str] = frozenset()
    acknowledged_sections: frozenset[str] = frozenset()
    depth: str | None = None
    purpose: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> SetupSession:
        return cls(
            guild_id=row["guild_id"],
            guild_name=row["guild_name"],
            owner_id=row["owner_id"],
            setup_status=row["setup_status"],
            setup_channel_id=row.get("setup_channel_id"),
            setup_message_id=row.get("setup_message_id"),
            last_readiness_score=row.get("last_readiness_score"),
            current_step=row.get("current_step"),
            delegated_admins=tuple(row.get("delegated_admins") or ()),
            skipped_sections=frozenset(row.get("skipped_sections") or ()),
            acknowledged_sections=frozenset(
                row.get("acknowledged_sections") or (),
            ),
            depth=row.get("depth"),
            purpose=row.get("purpose"),
        )


async def start_session(
    *,
    guild_id: int,
    guild_name: str,
    owner_id: int,
    setup_channel_id: int | None = None,
    setup_message_id: int | None = None,
) -> SetupSession:
    """Create or refresh the row in ``pending``.

    Idempotent: if a row already exists, this only updates the
    cached guild_name / owner_id / channel-message ids and leaves
    the existing ``setup_status`` untouched.
    """
    await db.upsert(
        guild_id=guild_id,
        guild_name=guild_name,
        owner_id=owner_id,
        setup_status="pending",
        setup_channel_id=setup_channel_id,
        setup_message_id=setup_message_id,
    )
    row = await db.get(guild_id)
    if row is None:
        # Should never happen — we just upserted. Surface defensively.
        raise RuntimeError(
            f"setup_session.start_session: row for guild_id={guild_id} "
            "missing immediately after upsert.",
        )
    await _emit_session_audit(
        guild_id=guild_id,
        mutation_type="setup.session.started",
        new_value="pending",
        actor_id=owner_id,
        actor_type="user",
    )
    return SetupSession.from_row(row)


async def resume_session(guild_id: int) -> SetupSession | None:
    """Return the existing row, or ``None`` if the bot never joined."""
    row = await db.get(guild_id)
    if row is None:
        return None
    return SetupSession.from_row(row)


async def mark_in_progress(guild_id: int, *, step: str | None = None) -> None:
    """Move the row to ``in_progress`` and optionally record a step."""
    await db.set_status(guild_id, "in_progress")
    if step is not None:
        await db.set_step(guild_id, step)


async def mark_complete(guild_id: int) -> None:
    """Move the row to ``complete``; clears any in-flight step token,
    drops pending draft operations, and clears the skipped- and
    acknowledged-section sets.

    Final Review calls this after a successful apply, so the draft
    is empty by that point.  Clearing here is defence-in-depth — if
    something staged a draft after Final Review somehow, the next
    setup run starts clean.
    """
    await db.set_status(guild_id, "complete")
    await db.set_step(guild_id, None)
    await db.clear_skipped_sections(guild_id)
    await db.clear_acknowledged_sections(guild_id)
    await _clear_draft(guild_id)
    await _emit_session_audit(
        guild_id=guild_id,
        mutation_type="setup.session.completed",
        new_value="complete",
        actor_id=None,
        actor_type="system",
    )


async def dismiss(guild_id: int) -> None:
    """Move the row to ``dismissed``; clears any in-flight step token,
    drops pending draft operations, and clears the skipped- and
    acknowledged-section sets.

    Note: this only flips the launcher state and discards staged
    drafts.  It does **not** delete the guild's already-applied
    bindings, settings, or resources — those persist so the owner
    can re-run setup later.
    """
    await db.set_status(guild_id, "dismissed")
    await db.set_step(guild_id, None)
    await db.clear_skipped_sections(guild_id)
    await db.clear_acknowledged_sections(guild_id)
    await _clear_draft(guild_id)
    await _emit_session_audit(
        guild_id=guild_id,
        mutation_type="setup.session.dismissed",
        new_value="dismissed",
        actor_id=None,
        actor_type="system",
    )


async def _emit_session_audit(
    *,
    guild_id: int,
    mutation_type: str,
    new_value: str,
    actor_id: int | None,
    actor_type: str,
) -> None:
    """Best-effort ``audit.action_recorded`` emission for setup session lifecycle.

    Lazy-imported to avoid a circular dependency (same pattern as _clear_draft).
    Failure is logged at WARNING and swallowed — the DB transition is authoritative.
    """
    try:
        from services import audit_events

        await audit_events.emit_audit_action(
            mutation_id=str(uuid.uuid4()),
            subsystem="setup",
            mutation_type=mutation_type,
            target=f"setup_session:{guild_id}",
            scope="guild",
            guild_id=guild_id,
            prev_value=None,
            new_value=new_value,
            actor_id=actor_id,
            actor_type=actor_type,
            occurred_at=datetime.now(timezone.utc),
        )
    except Exception:
        logger.warning(
            "setup_session: audit emission failed for guild_id=%s mutation_type=%s",
            guild_id,
            mutation_type,
        )


async def _clear_draft(guild_id: int) -> None:
    """Best-effort draft clear.  Lazy import to avoid an import cycle
    between :mod:`services.setup_session` and :mod:`services.setup_draft`
    (the draft service imports :mod:`services.setup_operations`, which
    is independent of this module).
    """
    try:
        from services import setup_draft

        await setup_draft.clear(guild_id)
    except Exception:
        logger.exception(
            "setup_session: setup_draft.clear failed for guild_id=%s",
            guild_id,
        )


async def record_readiness_score(guild_id: int, score: int | None) -> None:
    """Cache the latest readiness % so drift can be detected on re-runs."""
    await db.set_readiness_score(guild_id, score)


async def set_setup_channel_id(guild_id: int, channel_id: int | None) -> None:
    """Persist (or clear) the workspace's setup channel id (Phase 8).

    Used by :func:`services.setup_channel.cleanup_setup_channel_after_completion`
    after a successful Discord-side delete to null
    ``session.setup_channel_id`` so the next ``/setup`` re-creates the
    channel cleanly.  Service-layer wrapper around
    :func:`utils.db.setup_session.set_setup_channel_id`.
    """
    await db.set_setup_channel_id(guild_id, channel_id)


async def set_setup_message_id(guild_id: int, message_id: int | None) -> None:
    """Persist (or clear) the wizard's anchor message id for ``guild_id``.

    The setup wizard's workspace flow (Phase 3) posts a single message
    in ``#superbot-setup`` and re-edits it across the session lifetime;
    ``message_id`` is the Discord snowflake of that anchor.  Passing
    ``None`` clears the pointer — used when the launcher cog's resume
    sweep can't refetch the message and the next ``/setup`` reposts.

    Idempotent.  Side-effect-free above the DB layer.
    """
    await db.set_setup_message_id(guild_id, message_id)


async def mark_section_skipped(guild_id: int, slug: str) -> None:
    """Record that ``slug`` was explicitly skipped during the current run.

    Idempotent — the underlying primitive uses set semantics, so calling
    twice with the same slug leaves the set unchanged.
    """
    await db.add_skipped_section(guild_id, slug)


async def unmark_section_skipped(guild_id: int, slug: str) -> None:
    """Drop ``slug`` from the skipped-sections set."""
    await db.remove_skipped_section(guild_id, slug)


async def ack_section(guild_id: int, slug: str) -> None:
    """Record that ``slug`` was acknowledged complete.

    Used by metadata-only / link-only setup sections (Purpose, AI
    link-only in Phases 4 and 6) that emit zero draft operations.
    The hub's :mod:`services.setup_progress` read model surfaces
    acknowledged slugs as APPLIED so the section doesn't show as
    NOT_STARTED forever.

    Acknowledging also drops the slug from ``skipped_sections`` so
    an operator who skipped and then changed their mind sees the
    correct state on the next hub render.

    Idempotent — set semantics at the DB layer.
    """
    await db.add_acknowledged_section(guild_id, slug)
    # If the slug was skipped earlier, acknowledging supersedes that.
    await db.remove_skipped_section(guild_id, slug)


async def unack_section(guild_id: int, slug: str) -> None:
    """Drop ``slug`` from the acknowledged-sections set."""
    await db.remove_acknowledged_section(guild_id, slug)


async def set_depth(guild_id: int, depth: str | None) -> None:
    """Persist the operator's depth choice (quick / standard / advanced).

    Passing ``None`` clears the choice, which makes the hub re-prompt
    on the next open.
    """
    await db.set_depth(guild_id, depth)


async def set_purpose(guild_id: int, purpose: str | None) -> None:
    """Persist the operator's server-purpose choice (Phase 4).

    Allowed values are in :data:`utils.db.setup_session.KNOWN_PURPOSES`;
    ``None`` clears the pick.  Purpose is session metadata only — it
    does not stage any setup operation.  Section builders that read
    ``session.purpose`` should treat unknown / NULL values as
    "unspecified" and fall back to neutral defaults.
    """
    await db.set_purpose(guild_id, purpose)


# ---------------------------------------------------------------------------
# Delegated-admin lifecycle
# ---------------------------------------------------------------------------
#
# DB primitives ``utils.db.setup_session.add_delegated_admin`` and
# ``remove_delegated_admin`` already exist (PostgreSQL set semantics on
# the ``setup_session.delegated_admins`` TEXT[] column).  These
# service-level wrappers add the canonical audit emission and the
# uniform call signature the setup cog's ``/setup-delegate`` /
# ``/setup-undelegate`` slash commands consume.


async def add_delegated_admin(
    guild_id: int,
    user_id: int,
    *,
    actor_id: int | None,
) -> None:
    """Append ``user_id`` to the guild's ``delegated_admins`` set.

    Idempotent — repeated calls leave the set unchanged.  Emits
    ``setup.delegated_admin.added`` so the audit pipeline sees the
    promotion.  ``actor_id`` is the user who performed the grant
    (typically the server owner via ``/setup-delegate``).
    """
    await db.add_delegated_admin(guild_id, user_id)
    await _emit_session_audit(
        guild_id=guild_id,
        mutation_type="setup.delegated_admin.added",
        new_value=str(user_id),
        actor_id=actor_id,
        actor_type="user",
    )


async def remove_delegated_admin(
    guild_id: int,
    user_id: int,
    *,
    actor_id: int | None,
) -> None:
    """Drop ``user_id`` from the guild's ``delegated_admins`` set.

    Idempotent.  Emits ``setup.delegated_admin.removed``.  The
    private setup channel's overwrites should be recomputed by the
    caller (see :func:`services.setup_channel.recompute_setup_channel_overwrites`)
    so the revoked admin loses explicit channel access too.
    """
    await db.remove_delegated_admin(guild_id, user_id)
    await _emit_session_audit(
        guild_id=guild_id,
        mutation_type="setup.delegated_admin.removed",
        new_value=str(user_id),
        actor_id=actor_id,
        actor_type="user",
    )


# ---------------------------------------------------------------------------
# Drift detection (Phase 9i / Track 8 PR 24)
# ---------------------------------------------------------------------------


from dataclasses import dataclass  # noqa: E402 — local symbol


@dataclass(frozen=True)
class DriftReport:
    """Diff between the last accepted state and a fresh readiness scan."""

    has_drift: bool
    score_delta: int | None
    prev_score: int | None
    current_score: int | None
    new_error_findings: tuple[str, ...] = ()
    new_warn_findings: tuple[str, ...] = ()
    summary: str = ""


_DRIFT_SCORE_THRESHOLD = 5


def detect_drift(
    *,
    previous_score: int | None,
    current_score: int | None,
    current_health_summary: dict[str, int] | None = None,
    new_findings: tuple[object, ...] = (),
) -> DriftReport:
    """Compute the drift between a previous readiness snapshot and a
    fresh ``ReadinessReport``.

    ``has_drift`` is True when:

    * The readiness score moved by more than
      ``_DRIFT_SCORE_THRESHOLD`` (5 points).
    * The fresh health summary surfaces at least one ``error``
      severity finding (a regression).
    * One or more ``new_findings`` are passed in (the caller
      already filtered).

    The summary string is a one-liner the wizard renders in the
    launcher / summary view.
    """
    score_delta: int | None = None
    if previous_score is not None and current_score is not None:
        score_delta = current_score - previous_score

    new_errors = tuple(
        f"{getattr(f, 'subsystem', '?')}.{getattr(f, 'binding_name', '?')}"
        for f in new_findings
        if getattr(f, "severity", None) == "error"
    )
    new_warns = tuple(
        f"{getattr(f, 'subsystem', '?')}.{getattr(f, 'binding_name', '?')}"
        for f in new_findings
        if getattr(f, "severity", None) == "warn"
    )
    summary_health_errors = (current_health_summary or {}).get("error", 0)

    score_moved = score_delta is not None and abs(score_delta) >= _DRIFT_SCORE_THRESHOLD
    has_drift = bool(
        score_moved or new_errors or new_warns or summary_health_errors > 0,
    )

    if not has_drift:
        summary = "No drift detected. Configuration matches the accepted plan."
    else:
        bits = []
        if score_moved and score_delta is not None:
            direction = "improved" if score_delta > 0 else "regressed"
            bits.append(f"readiness {direction} by {abs(score_delta)}%")
        if new_errors:
            bits.append(f"{len(new_errors)} new error finding(s)")
        if new_warns:
            bits.append(f"{len(new_warns)} new warning finding(s)")
        if summary_health_errors and "error finding" not in " ".join(bits):
            bits.append(
                f"{summary_health_errors} health error(s) outstanding",
            )
        summary = "Drift detected: " + "; ".join(bits) + "."

    return DriftReport(
        has_drift=has_drift,
        score_delta=score_delta,
        prev_score=previous_score,
        current_score=current_score,
        new_error_findings=new_errors,
        new_warn_findings=new_warns,
        summary=summary,
    )


__all__ = [
    "DriftReport",
    "SetupSession",
    "ack_section",
    "add_delegated_admin",
    "detect_drift",
    "dismiss",
    "mark_complete",
    "mark_in_progress",
    "mark_section_skipped",
    "record_readiness_score",
    "remove_delegated_admin",
    "resume_session",
    "set_depth",
    "set_purpose",
    "set_setup_channel_id",
    "set_setup_message_id",
    "start_session",
    "unack_section",
    "unmark_section_skipped",
]

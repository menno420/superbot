"""Setup wizard progress + per-section status computation.

Pure, read-only helpers that decide which status badge each section in
the registry should render on the hub.  No DB writes and no Discord
I/O — callers pass in the resolved :class:`SetupSession` snapshot and
either the list of staged :class:`SetupOperation` rows from
:func:`services.setup_draft.list_ops` OR the typed
:class:`services.setup_draft.DraftOperationRow` wrappers from
:func:`services.setup_draft.list_rows`.

Matching strategy
-----------------

Each entry in ``draft_ops`` is matched against a section by the first
of:

1. ``row.section_slug == section.slug`` — preferred when the entry is
   a :class:`DraftOperationRow` (Phase 0 provenance).  Section
   ownership is recorded explicitly so legacy ``op_kinds`` heuristics
   are unnecessary.
2. ``op.kind in section.op_kinds`` — fallback for bare
   :class:`SetupOperation` entries and for rows whose ``section_slug``
   is NULL (pre-Phase-0 legacy rows).

Recommended-vs-customised distinction is also row-aware: when row
provenance is present, ``staging_kind == "recommended"`` wins over
the legacy ``metadata.source == "setup_ux:recommended"`` heuristic.

Status vocabulary
-----------------

``NOT_STARTED``
    No staged draft entry matches AND the section is not in
    :attr:`SetupSession.skipped_sections` AND the session has not been
    acknowledged via :func:`services.setup_session.ack_section` AND
    the session is not yet ``complete``.

``CUSTOMIZED``
    At least one matching draft entry exists AND not every match is
    recommended-source.

``RECOMMENDED``
    Every matching draft entry was staged as recommended (typed row's
    ``staging_kind`` or legacy ``metadata.source``).

``SKIPPED``
    The slug appears in :attr:`SetupSession.skipped_sections`, regardless
    of whether entries are also staged.  Skipping is an explicit operator
    declaration; the badge wins over staging state.

``APPLIED``
    The session is ``complete`` and either entries have already been
    applied OR the section is read-only.  Final Review clears the
    draft, so "complete + no matching draft" is the post-apply state.
    ``ack_section`` writes (Purpose, AI link-only) also surface as
    APPLIED for sections with no staging path.

``NEEDS_ATTENTION``
    Reserved for future use (PR 4+ when readiness findings can flag a
    section as warranting re-visit).  Currently never returned by
    :func:`compute_section_status`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.setup_draft import DraftOperationRow
    from services.setup_operations import SetupOperation
    from services.setup_sections import SetupSection
    from services.setup_session import SetupSession


class SectionStatus(str, Enum):
    """One-of status for a setup section relative to the current session.

    String-valued so it can be JSON-serialised, compared with literals,
    and used directly in embed text via :attr:`SectionStatus.value`.
    """

    NOT_STARTED = "not_started"
    RECOMMENDED = "recommended"
    CUSTOMIZED = "customized"
    SKIPPED = "skipped"
    NEEDS_ATTENTION = "needs_attention"
    APPLIED = "applied"


@dataclass(frozen=True)
class SectionProgress:
    """Per-section progress snapshot rendered by the hub."""

    slug: str
    status: SectionStatus
    pending_ops: int


_BADGE_BY_STATUS: dict[SectionStatus, str] = {
    SectionStatus.NOT_STARTED: "⬜",
    SectionStatus.RECOMMENDED: "✅",
    SectionStatus.CUSTOMIZED: "🟡",
    SectionStatus.SKIPPED: "⚠️",
    SectionStatus.NEEDS_ATTENTION: "❗",
    SectionStatus.APPLIED: "✅",
}


def badge_for(status: SectionStatus) -> str:
    """Return the emoji glyph shown next to a section label on the hub."""
    return _BADGE_BY_STATUS.get(status, "⬜")


_RECOMMENDED_SOURCE = "setup_ux:recommended"


def _is_typed_row(entry: object) -> bool:
    """True iff ``entry`` exposes the :class:`DraftOperationRow` shape.

    Duck-typed so the progress helpers accept both bare
    :class:`SetupOperation` (legacy) and the typed wrapper without
    importing the wrapper class (which would invert the dependency
    direction).
    """
    return (
        hasattr(entry, "section_slug")
        and hasattr(entry, "staging_kind")
        and hasattr(entry, "op")
    )


def _entry_matches_section(
    entry: SetupOperation | DraftOperationRow,
    section: SetupSection,
) -> bool:
    """True iff ``entry`` belongs to ``section``.

    Prefers row provenance (``section_slug``) when available; falls
    back to the legacy ``op.kind in section.op_kinds`` matching for
    null-provenance rows and bare :class:`SetupOperation` entries.

    Read-only sections (empty ``op_kinds`` AND no provenance match)
    never match an entry, so they fall through to NOT_STARTED /
    APPLIED purely based on session state.
    """
    if _is_typed_row(entry):
        if entry.section_slug is not None:
            return entry.section_slug == section.slug
        # Null-provenance row → fall back to op_kinds matching on
        # the wrapped SetupOperation.
        if not section.op_kinds:
            return False
        return entry.op.kind in section.op_kinds

    # Bare SetupOperation — op_kinds matching only.
    if not section.op_kinds:
        return False
    return entry.kind in section.op_kinds


def _entry_is_recommended(entry: SetupOperation | DraftOperationRow) -> bool:
    """True iff ``entry`` was staged as recommended.

    Prefers typed-row provenance (``staging_kind == "recommended"``);
    falls back to the legacy ``metadata.source == "setup_ux:recommended"``
    heuristic for bare ops and rows whose ``staging_kind`` is null
    (pre-Phase-0 legacy).
    """
    if _is_typed_row(entry):
        if entry.staging_kind is not None:
            return entry.staging_kind == "recommended"
        # Null-staging row → fall back to op metadata.
        metadata = entry.op.metadata or {}
        return metadata.get("source") == _RECOMMENDED_SOURCE

    metadata = (entry.metadata or {}) if entry.metadata else {}
    return metadata.get("source") == _RECOMMENDED_SOURCE


def compute_section_status(
    section: SetupSection,
    *,
    session: SetupSession | None,
    draft_ops: Iterable[SetupOperation | DraftOperationRow],
) -> SectionProgress:
    """Compute the status badge for ``section`` in the current session.

    The function is deterministic and side-effect-free; ``draft_ops``
    is iterated once.  Each entry may be a :class:`SetupOperation`
    (legacy) or a :class:`services.setup_draft.DraftOperationRow`
    (typed wrapper carrying ``section_slug`` provenance).  Mixed
    iterables work too.

    Decision order (first match wins):

    1. ``SKIPPED`` if the section slug is in
       :attr:`SetupSession.skipped_sections`.
    2. ``APPLIED`` if the session is ``complete``, or if the section
       has no staging path and the session has acknowledged the
       section's slug via :func:`services.setup_session.ack_section`.
    3. ``RECOMMENDED`` if every matching entry was staged as
       recommended.
    4. ``CUSTOMIZED`` if any matching entry exists.
    5. ``NOT_STARTED`` otherwise.
    """
    if session is not None and section.slug in session.skipped_sections:
        return SectionProgress(
            slug=section.slug,
            status=SectionStatus.SKIPPED,
            pending_ops=0,
        )

    matching = [entry for entry in draft_ops if _entry_matches_section(entry, section)]
    pending = len(matching)

    if session is not None and session.setup_status == "complete":
        return SectionProgress(
            slug=section.slug,
            status=SectionStatus.APPLIED,
            pending_ops=pending,
        )

    # Metadata-only / link-only sections (Purpose, AI link-only) emit
    # zero draft ops; their progress comes from
    # setup_session.ack_section, surfaced here as APPLIED once the
    # acknowledgement is recorded.  Sections with staging paths
    # continue through the normal draft-based flow.
    if (
        not matching
        and session is not None
        and section.slug in getattr(session, "acknowledged_sections", frozenset())
    ):
        return SectionProgress(
            slug=section.slug,
            status=SectionStatus.APPLIED,
            pending_ops=0,
        )

    if not matching:
        return SectionProgress(
            slug=section.slug,
            status=SectionStatus.NOT_STARTED,
            pending_ops=0,
        )

    if all(_entry_is_recommended(entry) for entry in matching):
        return SectionProgress(
            slug=section.slug,
            status=SectionStatus.RECOMMENDED,
            pending_ops=pending,
        )
    return SectionProgress(
        slug=section.slug,
        status=SectionStatus.CUSTOMIZED,
        pending_ops=pending,
    )


def compute_all(
    sections: Iterable[SetupSection],
    *,
    session: SetupSession | None,
    draft_ops: Iterable[SetupOperation | DraftOperationRow],
) -> list[SectionProgress]:
    """Compute :class:`SectionProgress` for every section in ``sections``.

    The draft op iterable is materialised once and reused, so passing a
    generator is safe.  Entries may be a mix of :class:`SetupOperation`
    and :class:`services.setup_draft.DraftOperationRow`.
    """
    op_list = list(draft_ops)
    return [
        compute_section_status(s, session=session, draft_ops=op_list) for s in sections
    ]


__all__ = [
    "SectionProgress",
    "SectionStatus",
    "badge_for",
    "compute_all",
    "compute_section_status",
]

"""Setup wizard progress + per-section status computation.

Pure, read-only helpers that decide which status badge each section in
the registry should render on the hub.  No DB writes and no Discord
I/O — callers pass in the resolved :class:`SetupSession` snapshot and
the list of staged :class:`SetupOperation` rows from
:mod:`services.setup_draft`.

Status vocabulary
-----------------

``NOT_STARTED``
    No staged draft ops match the section's :attr:`SetupSection.op_kinds`
    AND the section is not in :attr:`SetupSession.skipped_sections` AND
    the session is not yet ``complete``.

``CUSTOMIZED``
    At least one draft op matches the section's :attr:`SetupSection.op_kinds`
    AND those ops did not come from ``setup_ux:recommended`` staging.
    (PR 3 introduces the recommended source; until then any matched op
    is treated as customised.)

``RECOMMENDED``
    Every matching draft op was staged with metadata
    ``source == "setup_ux:recommended"``.  Distinguishes the "I clicked
    Apply Recommended" path from the "I customised this" path.

``SKIPPED``
    The slug appears in :attr:`SetupSession.skipped_sections`, regardless
    of whether ops are also staged.  Skipping is an explicit operator
    declaration; the badge wins over staging state.

``APPLIED``
    The session is ``complete`` and either ops have already been applied
    OR the section is read-only.  Final Review clears the draft, so
    "complete + no matching draft" is the post-apply state.

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


def _matches_section(op: SetupOperation, section: SetupSection) -> bool:
    """True iff ``op`` belongs to ``section`` per its declared op_kinds.

    Read-only sections (empty ``op_kinds``) never match a draft op, so
    they fall through to NOT_STARTED / APPLIED purely based on session
    state.
    """
    if not section.op_kinds:
        return False
    return op.kind in section.op_kinds


def compute_section_status(
    section: SetupSection,
    *,
    session: SetupSession | None,
    draft_ops: Iterable[SetupOperation],
) -> SectionProgress:
    """Compute the status badge for ``section`` in the current session.

    The function is deterministic and side-effect-free; ``draft_ops``
    is iterated once.

    Decision order (first match wins):

    1. ``SKIPPED`` if the section slug is in
       :attr:`SetupSession.skipped_sections`.
    2. ``APPLIED`` if the session is ``complete``.
    3. ``RECOMMENDED`` if every matching draft op has
       ``metadata.source == "setup_ux:recommended"``.
    4. ``CUSTOMIZED`` if any matching draft op exists.
    5. ``NOT_STARTED`` otherwise.
    """
    if session is not None and section.slug in session.skipped_sections:
        return SectionProgress(
            slug=section.slug,
            status=SectionStatus.SKIPPED,
            pending_ops=0,
        )

    matching = [op for op in draft_ops if _matches_section(op, section)]
    pending = len(matching)

    if session is not None and session.setup_status == "complete":
        return SectionProgress(
            slug=section.slug,
            status=SectionStatus.APPLIED,
            pending_ops=pending,
        )

    if not matching:
        return SectionProgress(
            slug=section.slug,
            status=SectionStatus.NOT_STARTED,
            pending_ops=0,
        )

    sources = {
        (op.metadata or {}).get("source", "") if op.metadata else "" for op in matching
    }
    if sources == {_RECOMMENDED_SOURCE}:
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
    draft_ops: Iterable[SetupOperation],
) -> list[SectionProgress]:
    """Compute :class:`SectionProgress` for every section in ``sections``.

    The draft op iterable is materialised once and reused, so passing a
    generator is safe.
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

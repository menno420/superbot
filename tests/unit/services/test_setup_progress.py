"""Tests for ``services.setup_progress`` — section status computation."""

from __future__ import annotations

import pytest

from services.setup_operations import SetupOperation
from services.setup_progress import (
    SectionStatus,
    badge_for,
    compute_all,
    compute_section_status,
)
from services.setup_sections import SetupSection
from services.setup_session import SetupSession

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _noop(_interaction, _hub):  # pragma: no cover — never invoked here
    return None


def _section(slug, op_kinds=()):
    return SetupSection(
        slug=slug,
        label=slug.replace("_", " ").title(),
        style=None,
        run=_noop,
        op_kinds=frozenset(op_kinds),
    )


def _session(
    *,
    status="pending",
    skipped=(),
    guild_id=1,
):
    return SetupSession(
        guild_id=guild_id,
        guild_name="Test",
        owner_id=99,
        setup_status=status,
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        skipped_sections=frozenset(skipped),
    )


def _op(kind, subsystem="mod", *, source=None):
    metadata = None
    if source is not None:
        metadata = {"source": source}
    return SetupOperation(
        kind=kind,
        subsystem=subsystem,
        binding_name="log",
        target_id=42,
        target_name="logs",
        target_kind="channel",
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# compute_section_status
# ---------------------------------------------------------------------------


def test_not_started_when_no_session_and_no_ops():
    section = _section("channels", op_kinds={"bind_channel"})
    progress = compute_section_status(section, session=None, draft_ops=[])
    assert progress.status is SectionStatus.NOT_STARTED
    assert progress.pending_ops == 0


def test_not_started_when_no_matching_op():
    section = _section("channels", op_kinds={"bind_channel"})
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[_op("set_cleanup_policy")],
    )
    assert progress.status is SectionStatus.NOT_STARTED


def test_customized_when_matching_op_with_non_recommended_source():
    section = _section("channels", op_kinds={"bind_channel"})
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[_op("bind_channel", source="manual")],
    )
    assert progress.status is SectionStatus.CUSTOMIZED
    assert progress.pending_ops == 1


def test_recommended_when_every_matching_op_is_recommended():
    section = _section("cleanup", op_kinds={"set_cleanup_policy"})
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[
            _op("set_cleanup_policy", source="setup_ux:recommended"),
            _op("set_cleanup_policy", source="setup_ux:recommended"),
        ],
    )
    assert progress.status is SectionStatus.RECOMMENDED
    assert progress.pending_ops == 2


def test_mixed_sources_falls_back_to_customized():
    section = _section("cleanup", op_kinds={"set_cleanup_policy"})
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[
            _op("set_cleanup_policy", source="setup_ux:recommended"),
            _op("set_cleanup_policy", source="manual"),
        ],
    )
    assert progress.status is SectionStatus.CUSTOMIZED


def test_skipped_wins_over_staged_ops():
    section = _section("cleanup", op_kinds={"set_cleanup_policy"})
    progress = compute_section_status(
        section,
        session=_session(skipped=["cleanup"]),
        draft_ops=[_op("set_cleanup_policy")],
    )
    assert progress.status is SectionStatus.SKIPPED


def test_applied_when_session_complete():
    section = _section("channels", op_kinds={"bind_channel"})
    # Draft is empty post-apply; complete session should render as APPLIED.
    progress = compute_section_status(
        section,
        session=_session(status="complete"),
        draft_ops=[],
    )
    assert progress.status is SectionStatus.APPLIED


def test_applied_session_with_skipped_slug_still_skipped():
    """Skipped is the explicit operator declaration; APPLIED is the implicit
    'session done' state. Skipped should win even after completion."""
    section = _section("cleanup", op_kinds={"set_cleanup_policy"})
    progress = compute_section_status(
        section,
        session=_session(status="complete", skipped=["cleanup"]),
        draft_ops=[],
    )
    assert progress.status is SectionStatus.SKIPPED


def test_read_only_section_falls_to_not_started():
    """Sections with empty op_kinds never match a draft op; they default
    to NOT_STARTED unless skipped or applied."""
    section = _section("server_scan", op_kinds=())
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[_op("bind_channel")],
    )
    assert progress.status is SectionStatus.NOT_STARTED


# ---------------------------------------------------------------------------
# compute_all + badge_for
# ---------------------------------------------------------------------------


def test_compute_all_returns_one_progress_per_section():
    sections = [
        _section("channels", op_kinds={"bind_channel"}),
        _section("cleanup", op_kinds={"set_cleanup_policy"}),
    ]
    progresses = compute_all(
        sections,
        session=_session(),
        draft_ops=[_op("set_cleanup_policy", source="setup_ux:recommended")],
    )
    by_slug = {p.slug: p.status for p in progresses}
    assert by_slug == {
        "channels": SectionStatus.NOT_STARTED,
        "cleanup": SectionStatus.RECOMMENDED,
    }


def test_compute_all_materialises_generator_once():
    """A single-pass generator must be consumable across all sections."""

    def gen():
        yield _op("bind_channel")

    sections = [
        _section("channels", op_kinds={"bind_channel"}),
        _section("cleanup", op_kinds={"set_cleanup_policy"}),
    ]
    progresses = compute_all(sections, session=_session(), draft_ops=gen())
    assert progresses[0].status is SectionStatus.CUSTOMIZED
    assert progresses[1].status is SectionStatus.NOT_STARTED


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (SectionStatus.NOT_STARTED, "⬜"),
        (SectionStatus.RECOMMENDED, "✅"),
        (SectionStatus.CUSTOMIZED, "🟡"),
        (SectionStatus.SKIPPED, "⚠️"),
        (SectionStatus.APPLIED, "✅"),
        (SectionStatus.NEEDS_ATTENTION, "❗"),
    ],
)
def test_badge_for_returns_expected_glyph(status, expected):
    assert badge_for(status) == expected


# ---------------------------------------------------------------------------
# Phase 2 — provenance-preferred matching via DraftOperationRow
# ---------------------------------------------------------------------------


def _row(
    *,
    section_slug=None,
    staging_kind=None,
    op_kind="bind_channel",
    subsystem="logging",
    source=None,
):
    """Build a DraftOperationRow shaped object for the duck-typed
    progress helpers.  Uses the real dataclass when available."""
    from services.setup_draft import DraftOperationRow
    from services.setup_operations import SetupOperation as _SetupOperation

    metadata = None
    if source is not None:
        metadata = {"source": source}
    return DraftOperationRow(
        id=1,
        seq=1,
        section_slug=section_slug,
        staging_kind=staging_kind,
        group_id=None,
        parent_seq=None,
        label="label",
        op=_SetupOperation(
            kind=op_kind,
            subsystem=subsystem,
            metadata=metadata,
        ),
    )


def test_progress_prefers_section_slug_over_op_kinds():
    """A row whose section_slug matches the section is counted EVEN
    when its op.kind is not in section.op_kinds.  This is the key
    Phase 2 behaviour: provenance wins.
    """
    section = _section("channels", op_kinds={"bind_channel"})
    # Row staged by the channels section but using a non-channels op
    # kind (a contrived case to prove provenance wins, not op_kinds).
    row = _row(
        section_slug="channels",
        staging_kind="recommended",
        op_kind="set_setting",  # not in op_kinds, but still owned by channels
        subsystem="logging",
    )
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[row],
    )
    assert progress.status is SectionStatus.RECOMMENDED
    assert progress.pending_ops == 1


def test_progress_rejects_section_slug_mismatch_even_when_op_kinds_match():
    """Provenance wins both ways: a row owned by a DIFFERENT section
    is not counted for ``section`` even when its op.kind matches
    section.op_kinds.  Prevents cross-section bleed.
    """
    section = _section("channels", op_kinds={"bind_channel"})
    row = _row(
        section_slug="other_section",  # owned by a different section
        staging_kind="recommended",
        op_kind="bind_channel",  # op_kind matches but provenance says no
    )
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[row],
    )
    assert progress.status is SectionStatus.NOT_STARTED
    assert progress.pending_ops == 0


def test_progress_falls_back_to_op_kinds_when_section_slug_null():
    """Pre-Phase-0 / legacy rows have ``section_slug=None``; the
    matcher falls back to the op_kinds heuristic so legacy drafts
    aren't silently lost.
    """
    section = _section("channels", op_kinds={"bind_channel"})
    row = _row(
        section_slug=None,
        staging_kind=None,
        op_kind="bind_channel",
    )
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[row],
    )
    # Counts via fallback.
    assert progress.pending_ops == 1


def test_progress_recommended_from_staging_kind_wins_over_metadata():
    """When the typed row says ``staging_kind="recommended"``, the
    progress is RECOMMENDED even if metadata source is something
    else.  Phase 0 made staging_kind the canonical signal.
    """
    section = _section("channels", op_kinds={"bind_channel"})
    row = _row(
        section_slug="channels",
        staging_kind="recommended",
        op_kind="bind_channel",
        source="manual",  # metadata disagrees
    )
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[row],
    )
    assert progress.status is SectionStatus.RECOMMENDED


def test_progress_recommended_falls_back_to_metadata_when_staging_kind_null():
    """Null staging_kind falls back to the legacy metadata heuristic
    so pre-Phase-0 rows still get the RECOMMENDED badge when their
    metadata.source matches.
    """
    section = _section("channels", op_kinds={"bind_channel"})
    row = _row(
        section_slug=None,  # null provenance → fall back to op_kinds
        staging_kind=None,  # null staging → fall back to metadata
        op_kind="bind_channel",
        source="setup_ux:recommended",
    )
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[row],
    )
    assert progress.status is SectionStatus.RECOMMENDED


def test_progress_customised_when_mix_of_recommended_and_custom():
    """Mixed rows (one recommended, one custom) bump the section out
    of RECOMMENDED into CUSTOMIZED.
    """
    section = _section("channels", op_kinds={"bind_channel"})
    rows = [
        _row(
            section_slug="channels",
            staging_kind="recommended",
            op_kind="bind_channel",
        ),
        _row(
            section_slug="channels",
            staging_kind="custom",
            op_kind="bind_channel",
        ),
    ]
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=rows,
    )
    assert progress.status is SectionStatus.CUSTOMIZED
    assert progress.pending_ops == 2


def test_progress_acknowledged_section_renders_as_applied():
    """Metadata-only / link-only sections (Purpose, AI link-only) emit
    zero draft ops; their progress comes from
    setup_session.ack_section.  Acknowledged slugs render as APPLIED.
    """
    # Section has no op_kinds (read-only / metadata-only).
    section = _section("purpose", op_kinds=())
    session = SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        acknowledged_sections=frozenset({"purpose"}),
    )
    progress = compute_section_status(
        section,
        session=session,
        draft_ops=[],
    )
    assert progress.status is SectionStatus.APPLIED


def test_progress_not_acknowledged_section_still_renders_not_started():
    """Same metadata-only section, but NOT acknowledged → NOT_STARTED."""
    section = _section("purpose", op_kinds=())
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[],
    )
    assert progress.status is SectionStatus.NOT_STARTED


def test_progress_skipped_wins_over_acknowledged():
    """If a section is both skipped and acknowledged (operator changed
    their mind back), the skipped badge wins for display.  In
    practice ``ack_section`` clears skipped at write time, so this
    is just defence-in-depth.
    """
    section = _section("purpose", op_kinds=())
    session = SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        skipped_sections=frozenset({"purpose"}),
        acknowledged_sections=frozenset({"purpose"}),
    )
    progress = compute_section_status(
        section,
        session=session,
        draft_ops=[],
    )
    assert progress.status is SectionStatus.SKIPPED


def test_progress_mixed_legacy_and_typed_rows():
    """compute_section_status accepts a mixed iterable — bare
    SetupOperation entries and DraftOperationRow wrappers — and
    matches each via the right strategy.
    """
    section = _section("channels", op_kinds={"bind_channel"})
    typed = _row(
        section_slug="channels",
        staging_kind="recommended",
        op_kind="bind_channel",
    )
    legacy = SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        metadata={"source": "setup_ux:recommended"},
    )
    progress = compute_section_status(
        section,
        session=_session(),
        draft_ops=[typed, legacy],
    )
    assert progress.status is SectionStatus.RECOMMENDED
    assert progress.pending_ops == 2

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

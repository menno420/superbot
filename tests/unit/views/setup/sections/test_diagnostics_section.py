"""Tests for the Diagnose & repair setup section (server-management PR12).

Pins:

* Registration: slug, order, emoji, style, depth, empty op_kinds, and that
  it declares **no** recommended builder (repairs are explicit, never part
  of an "apply all recommended" sweep).
* The embed groups findings by severity and renders a healthy state.
* "Stage safe repairs" drafts the auto-repairable findings' ops with
  ``staging_kind="repair"`` / ``section_slug="diagnostics"`` and skips
  advisory-only findings.
* DM-context rejection; the section never calls ``apply_operations``
  (Final Review remains the only apply gate).
* The detail view stays within rows 0–3.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import setup_diagnostics
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY
from views.setup.sections import diagnostics


def _interaction(guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild_id = guild_id
    interaction.guild = SimpleNamespace(id=guild_id, name="Test")
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


def _finding(code, severity, repairability, *, ops=(), repair_label="", note=""):
    return setup_diagnostics.SetupDiagnosticFinding(
        code=code,
        severity=severity,
        subsystem="logging",
        section_slug="diagnostics",
        resource_type="channel",
        resource_id=1,
        summary=f"summary-{code}",
        detail="detail",
        repairability=repairability,
        repair_label=repair_label,
        repair_ops=tuple(ops),
        advisory_note=note,
    )


def _report(findings):
    return setup_diagnostics.SetupDiagnosticsReport(
        guild_id=1, findings=tuple(findings)
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_diagnostics_section_registered_with_expected_metadata():
    section = REGISTRY.get("diagnostics")
    assert section is not None
    assert section.slug == "diagnostics"
    assert section.order == 85
    assert section.emoji == "🩺"
    assert section.style == discord.ButtonStyle.secondary
    assert section.op_kinds == frozenset()
    assert "quick" not in section.depths
    # Repairs must never ride the blanket "apply all recommended" sweep.
    assert section.recommended_ops_builder is None


def test_diagnostics_section_label_fits_button():
    section = REGISTRY.get("diagnostics")
    assert section is not None
    assert 1 <= len(section.label) <= 80


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_embed_healthy_state():
    embed = diagnostics.build_diagnostics_embed(_report([]))
    blob = (embed.description or "").lower()
    assert "no issues" in blob


def test_embed_groups_by_severity_and_shows_repair_label():
    op = SetupOperation(kind="clear_binding", subsystem="logging", binding_name="x")
    findings = [
        _finding(
            "stale_binding",
            setup_diagnostics.SEV_WARNING,
            setup_diagnostics.REPAIR_AUTO,
            ops=[op],
            repair_label="Clear the dead binding",
        ),
        _finding(
            "missing_required_binding",
            setup_diagnostics.SEV_WARNING,
            setup_diagnostics.REPAIR_ADVISORY,
            note="Bind it in Channels",
        ),
    ]
    embed = diagnostics.build_diagnostics_embed(_report(findings))
    text = " ".join(f.value for f in embed.fields)
    assert "Clear the dead binding" in text
    assert "Bind it in Channels" in text
    # A safe-repair count appears in the Summary.
    summary = next(f.value for f in embed.fields if f.name == "Summary")
    assert "1 safe repair" in summary


# ---------------------------------------------------------------------------
# Stage safe repairs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_repairs_drafts_only_auto_repairable():
    op = SetupOperation(
        kind="clear_binding",
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
    )
    report = _report(
        [
            _finding(
                "stale_binding",
                setup_diagnostics.SEV_WARNING,
                setup_diagnostics.REPAIR_AUTO,
                ops=[op],
                repair_label="Clear the dead `logging.mod_channel` binding",
            ),
            _finding(
                "missing_required_binding",
                setup_diagnostics.SEV_WARNING,
                setup_diagnostics.REPAIR_ADVISORY,
                note="Bind it",
            ),
        ],
    )
    interaction = _interaction()
    button = diagnostics._StageRepairsButton()
    with (
        patch(
            "services.setup_diagnostics.collect_setup_diagnostics",
            new=AsyncMock(return_value=report),
        ),
        patch(
            "services.setup_draft.append", new=AsyncMock(return_value=1)
        ) as append_mock,
        patch("services.setup_draft.count", new=AsyncMock(return_value=1)),
        patch("services.setup_session.mark_in_progress", new=AsyncMock()),
    ):
        await button.callback(interaction)
    append_mock.assert_awaited_once()
    staged_op = append_mock.await_args.args[0]
    assert staged_op.kind == "clear_binding"
    assert append_mock.await_args.kwargs.get("staging_kind") == "repair"
    assert append_mock.await_args.kwargs.get("section_slug") == "diagnostics"


@pytest.mark.asyncio
async def test_stage_repairs_when_none_available():
    report = _report(
        [
            _finding(
                "missing_required_binding",
                setup_diagnostics.SEV_WARNING,
                setup_diagnostics.REPAIR_ADVISORY,
                note="Bind it",
            ),
        ],
    )
    interaction = _interaction()
    button = diagnostics._StageRepairsButton()
    with (
        patch(
            "services.setup_diagnostics.collect_setup_diagnostics",
            new=AsyncMock(return_value=report),
        ),
        patch("services.setup_draft.append", new=AsyncMock()) as append_mock,
    ):
        await button.callback(interaction)
    append_mock.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    assert "nothing to stage" in (
        interaction.response.send_message.await_args.args[0].lower()
    )


@pytest.mark.asyncio
async def test_stage_repairs_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    button = diagnostics._StageRepairsButton()
    with patch("services.setup_draft.append", new=AsyncMock()) as append_mock:
        await button.callback(interaction)
    append_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_repairs_does_not_apply():
    op = SetupOperation(kind="clear_binding", subsystem="logging", binding_name="x")
    report = _report(
        [
            _finding(
                "stale_binding",
                setup_diagnostics.SEV_WARNING,
                setup_diagnostics.REPAIR_AUTO,
                ops=[op],
                repair_label="Clear",
            ),
        ],
    )
    interaction = _interaction()
    button = diagnostics._StageRepairsButton()
    with (
        patch(
            "services.setup_diagnostics.collect_setup_diagnostics",
            new=AsyncMock(return_value=report),
        ),
        patch("services.setup_draft.append", new=AsyncMock(return_value=1)),
        patch("services.setup_draft.count", new=AsyncMock(return_value=1)),
        patch("services.setup_session.mark_in_progress", new=AsyncMock()),
        patch(
            "services.setup_operations.apply_operations",
            new=AsyncMock(),
        ) as apply_mock,
    ):
        await button.callback(interaction)
    apply_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Re-scan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rescan_edits_message():
    interaction = _interaction()
    button = diagnostics._RescanButton()
    with patch(
        "services.setup_diagnostics.collect_setup_diagnostics",
        new=AsyncMock(return_value=_report([])),
    ):
        await button.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# View shape + run()
# ---------------------------------------------------------------------------


def test_detail_view_buttons_in_rows_0_3():
    view = diagnostics.DiagnosticsSectionView(SimpleNamespace(id=99))
    assert {c.row for c in view.children} <= {0, 1, 2, 3}
    assert len(view.children) == 2


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.guild_id = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    await diagnostics.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_customize_opens_findings_view():
    interaction = _interaction()
    op = SetupOperation(kind="clear_binding", subsystem="logging", binding_name="x")
    report = _report(
        [
            _finding(
                "stale_binding",
                setup_diagnostics.SEV_WARNING,
                setup_diagnostics.REPAIR_AUTO,
                ops=[op],
                repair_label="Clear",
            ),
        ],
    )
    with patch(
        "services.setup_diagnostics.collect_setup_diagnostics",
        new=AsyncMock(return_value=report),
    ):
        await diagnostics._customize_run(interaction, None)
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert isinstance(kwargs["view"], diagnostics.DiagnosticsSectionView)

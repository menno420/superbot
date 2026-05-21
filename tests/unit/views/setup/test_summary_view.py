"""Phase 9i / Track 8 PR 24 — setup summary view tests.

Pins:

* ``build_summary_embed`` handles 3 documented states (no applied
  + clean, applied + clean, applied + drift).
* The Close button disables both buttons and edits the message.
* ``build_summary_snapshot`` swallows a failing
  ``setup_readiness.collect`` and still returns a SummarySnapshot.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.setup_session import DriftReport, SetupSession
from views.setup.summary import (
    AppliedRecord,
    SummarySnapshot,
    SummaryView,
    build_summary_embed,
    build_summary_snapshot,
)


def _author():
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = 99
    return m


def _interaction():
    interaction = MagicMock()
    interaction.user = _author()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


def _session(*, score=85):
    return SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="complete",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=score,
        current_step=None,
        delegated_admins=(),
    )


def _drift(has_drift: bool = False):
    return DriftReport(
        has_drift=has_drift,
        score_delta=0,
        prev_score=85,
        current_score=85,
        summary="No drift" if not has_drift else "Drift detected: x.",
    )


# ---------------------------------------------------------------------------
# build_summary_embed states
# ---------------------------------------------------------------------------


def test_summary_embed_no_applied_no_drift_renders_dark_grey():
    embed = build_summary_embed(SummarySnapshot())
    assert "without recording" in (embed.description or "").lower()


def test_summary_embed_no_applied_with_drift_renders_yellow():
    snap = SummarySnapshot(drift=_drift(has_drift=True))
    embed = build_summary_embed(snap)
    drift_field = next((f for f in embed.fields if f.name == "Drift"), None)
    assert drift_field is not None
    assert "Drift detected" in (drift_field.value or "")


def test_summary_embed_applied_and_clean_renders_applied_section():
    snap = SummarySnapshot(
        applied=(
            AppliedRecord(
                subsystem="logging",
                binding_name="mod_channel",
                target_name="mod-log",
                mutation_id="abc123def",
                audit_id=42,
            ),
        ),
        drift=_drift(has_drift=False),
    )
    embed = build_summary_embed(snap)
    applied_field = next(
        (f for f in embed.fields if f.name == "Applied"), None,
    )
    assert applied_field is not None
    rendered = applied_field.value or ""
    assert "mod_channel" in rendered
    assert "abc123de" in rendered  # mutation id prefix
    assert "42" in rendered  # audit id


def test_summary_embed_applied_and_drift_keeps_both_sections():
    snap = SummarySnapshot(
        applied=(
            AppliedRecord(
                subsystem="logging",
                binding_name="mod_channel",
                target_name="mod-log",
            ),
        ),
        drift=_drift(has_drift=True),
        extra_notes=("operator overrode default name",),
    )
    embed = build_summary_embed(snap)
    names = {f.name for f in embed.fields}
    assert "Applied" in names
    assert "Drift" in names
    assert "Notes" in names


# ---------------------------------------------------------------------------
# SummaryView
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_view_close_button_disables_and_edits():
    view = SummaryView(_author(), snapshot=SummarySnapshot())
    interaction = _interaction()
    await view._close.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    for child in view.children:
        assert getattr(child, "disabled", False) is True


@pytest.mark.asyncio
async def test_summary_view_open_settings_swaps_to_settings_hub():
    """The new handoff button replaces the summary embed/view with the
    Settings Manager hub in place — operators stay anchored to one
    message across the cog transition."""
    from views.settings.hub import SettingsHubView

    view = SummaryView(_author(), snapshot=SummarySnapshot())
    interaction = _interaction()
    await view._open_settings.callback(interaction)
    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert isinstance(kwargs.get("view"), SettingsHubView)
    assert kwargs.get("embed") is not None


@pytest.mark.asyncio
async def test_summary_view_open_settings_falls_back_when_hub_unavailable():
    """If SettingsHubView construction blows up the user sees an
    ephemeral fallback pointing at ``!settings`` instead of a crash."""
    view = SummaryView(_author(), snapshot=SummarySnapshot())
    interaction = _interaction()
    interaction.response.send_message = AsyncMock()

    with patch(
        "views.settings.hub.SettingsHubView",
        side_effect=RuntimeError("hub down"),
    ):
        await view._open_settings.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "!settings" in msg.lower()


def test_summary_view_has_open_settings_button():
    view = SummaryView(_author(), snapshot=SummarySnapshot())
    labels = {getattr(c, "label", None) for c in view.children}
    assert "Open Settings Manager" in labels
    assert "Close" in labels


# ---------------------------------------------------------------------------
# build_summary_snapshot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_snapshot_swallows_readiness_failure():
    session = _session(score=85)
    guild = MagicMock()
    with patch(
        "services.setup_readiness.collect",
        new_callable=AsyncMock,
        side_effect=RuntimeError("db down"),
    ):
        snap = await build_summary_snapshot(session=session, guild=guild)
    assert isinstance(snap, SummarySnapshot)
    assert snap.drift is not None
    # Drift should default to "no drift" since current_score is None.
    assert snap.drift.has_drift is False


@pytest.mark.asyncio
async def test_build_snapshot_without_guild_skips_collect():
    session = _session(score=85)
    snap = await build_summary_snapshot(session=session, guild=None)
    assert snap.drift is not None
    assert snap.drift.current_score is None


@pytest.mark.asyncio
async def test_build_snapshot_with_guild_uses_collected_score():
    session = _session(score=85)
    guild = MagicMock()
    fake_report = SimpleNamespace(
        percentage=90,
        health_summary={"error": 0, "warn": 0, "info": 0},
        health_findings=(),
    )
    with patch(
        "services.setup_readiness.collect",
        new_callable=AsyncMock,
        return_value=fake_report,
    ):
        snap = await build_summary_snapshot(session=session, guild=guild)
    assert snap.drift is not None
    assert snap.drift.current_score == 90
    assert snap.drift.score_delta == 5
    assert snap.drift.has_drift is True

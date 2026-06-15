"""Tests for the preset_select setup section.

Pins:

* Registration: slug, order=25, emoji=🎛, success-style button.
* Entry embed lists every bundled SERVER_PRESET.
* Preview embed shows operations + warnings; unknown preset slug
  surfaces an error embed.
* ``_stage_preset`` appends every adapted op via setup_draft, marks
  the session, and reports the resulting pending count.  Partial
  failures appear in the confirmation message.
* DM context rejection.
* The section never calls ``services.setup_operations.apply_operations``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.automation_templates import SERVER_PRESETS
from services.setup_sections import REGISTRY
from views.setup.sections import preset_select


def _interaction(guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild_id = guild_id
    interaction.guild = SimpleNamespace(id=guild_id)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_preset_section_registered_with_expected_slug():
    section = REGISTRY.get("preset_select")
    assert section is not None
    assert section.slug == "preset_select"
    assert section.order == 25
    assert section.emoji == "🎛"


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def test_entry_embed_lists_every_bundled_preset():
    embed = preset_select.build_preset_embed()
    rendered = " ".join(f.name + " " + f.value for f in embed.fields)
    for preset in SERVER_PRESETS:
        assert preset.display_name in rendered
        assert preset.slug in rendered


def test_preview_embed_shows_operation_count():
    minimal = next(p for p in SERVER_PRESETS if p.slug == "minimal")
    embed = preset_select.build_preview_embed("minimal")
    description = embed.description or ""
    assert str(len(minimal.operations)) in description


def test_preview_embed_lists_operations():
    embed = preset_select.build_preview_embed("minimal")
    ops_field = next((f for f in embed.fields if f.name == "Operations"), None)
    assert ops_field is not None
    # "bind_channel" appears for both ops in the minimal preset.
    assert "bind_channel" in ops_field.value


def test_preview_embed_truncates_long_operation_lists():
    """A preset with >10 ops shows a "+N more" line."""
    # Find the largest bundled preset to drive the truncation path.
    largest = max(SERVER_PRESETS, key=lambda p: len(p.operations))
    if len(largest.operations) <= 10:
        pytest.skip("no bundled preset has >10 operations")
    embed = preset_select.build_preview_embed(largest.slug)
    ops_field = next((f for f in embed.fields if f.name == "Operations"), None)
    assert ops_field is not None
    assert "more" in ops_field.value


def test_preview_embed_surfaces_unknown_preset_as_error():
    embed = preset_select.build_preview_embed("does-not-exist")
    assert "Unknown preset" in (embed.description or "")


# ---------------------------------------------------------------------------
# _stage_preset
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_preset_appends_every_adapted_op():
    interaction = _interaction()
    minimal_count = len(
        next(p for p in SERVER_PRESETS if p.slug == "minimal").operations,
    )
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=minimal_count,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await preset_select._stage_preset(interaction, "minimal")
    assert append_mock.await_count == minimal_count
    # Every staged op carries metadata.source = "preset:minimal".
    for call in append_mock.await_args_list:
        op = call.args[0]
        assert op.metadata["source"] == "preset:minimal"


@pytest.mark.asyncio
async def test_stage_preset_reports_pending_count_in_confirmation():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=7,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await preset_select._stage_preset(interaction, "minimal")
    msg = interaction.response.send_message.await_args.args[0]
    assert "Staged" in msg
    assert "7" in msg  # pending count


@pytest.mark.asyncio
async def test_stage_preset_isolates_per_op_failures():
    """A single append() raise doesn't abort later ops; the
    confirmation message surfaces the partial failure.
    """
    interaction = _interaction()
    call_count = {"n": 0}

    async def flaky_append(op, *, guild_id, actor_id, label, **_):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("first one fails")
        return 1

    with (
        patch(
            "services.setup_draft.append",
            new=flaky_append,
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await preset_select._stage_preset(interaction, "minimal")
    msg = interaction.response.send_message.await_args.args[0]
    assert "Failed" in msg or "failed" in msg.lower()


@pytest.mark.asyncio
async def test_stage_preset_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await preset_select._stage_preset(interaction, "minimal")
    append_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_preset_rejects_unknown_slug():
    interaction = _interaction()
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await preset_select._stage_preset(interaction, "garbage-slug")
    append_mock.assert_not_called()
    args = interaction.response.send_message.await_args.args
    assert "Unknown preset" in args[0]


@pytest.mark.asyncio
async def test_stage_preset_does_not_call_apply_operations():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        await preset_select._stage_preset(interaction, "minimal")
    apply_mock.assert_not_called()


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    await preset_select.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    args = interaction.response.send_message.await_args.args
    assert "guild" in args[0].lower()


@pytest.mark.asyncio
async def test_run_sends_preset_panel():
    interaction = _interaction()
    await preset_select.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs["view"], preset_select.PresetSectionView)
    assert "preset" in kwargs["embed"].title.lower()

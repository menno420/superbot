"""Tests for the channels & log routing setup section.

Pins:

* The section is registered with the expected slug, order, emoji, and
  style.
* The embed lists declared channel bindings grouped by subsystem and
  surfaces a "likely match" hint when the scan classifier matches.
* The binding picker select is built from every declared
  ``BindingSpec(kind=CHANNEL)`` across all subsystems.
* ``_stage_channel_binding`` drafts a ``bind_channel`` op with
  canonical metadata; source flips to ``"scan"`` when the operator
  picks the scan-suggested channel.
* The section never calls ``services.setup_operations.apply_operations``.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.guild_snapshot import (
    ChannelMeta,
    GuildSnapshot,
)
from services.setup_sections import REGISTRY
from views.setup.sections import channels


def _load_all_schemas() -> None:
    """Ensure subsystem schemas are registered before discovery."""
    for module_path in (
        "cogs.moderation.schemas",
        "cogs.logging.schemas",
        "cogs.economy.schemas",
        "cogs.xp.schemas",
        "cogs.blackjack.schemas",
        "cogs.deathmatch.schemas",
        "cogs.rps_tournament.schemas",
    ):
        mod = importlib.import_module(module_path)
        register = getattr(mod, "register_schemas", None)
        if register is None:
            continue
        try:
            register()
        except ValueError:
            pass


# Trigger registration at module import time.
_load_all_schemas()


@pytest.fixture(autouse=True)
def _ensure_schemas_loaded():
    """Re-register schemas defensively in case a sibling test reset the
    registry between collection and execution.
    """
    _load_all_schemas()
    return


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ch(name: str, *, ch_id: int = 1) -> ChannelMeta:
    return ChannelMeta(
        id=ch_id,
        name=name,
        type="text",
        topic=None,
        parent_category=None,
        position=0,
        bot_can_view=True,
        bot_can_send=True,
        bot_can_embed=True,
    )


def _snap(channels_list=(), categories=(), roles=()):
    return GuildSnapshot(
        guild_id=1,
        guild_name="Test",
        owner_id=0,
        channels=tuple(channels_list),
        categories=tuple(categories),
        roles=tuple(roles),
    )


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


def test_channels_section_registered_with_expected_slug():
    section = REGISTRY.get("channels")
    assert section is not None
    assert section.slug == "channels"
    assert section.order == 40
    assert section.emoji == "📡"


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_embed_lists_declared_channel_bindings_grouped_by_subsystem():
    embed = channels.build_channels_embed(_snap())
    field_names = {f.name for f in embed.fields}
    # Logging declares 7 channel bindings — must be one of the groups.
    assert "logging" in field_names


def test_embed_surfaces_scan_match_hint_when_snapshot_matches_name():
    # A mod-log channel in the snapshot should hint for mod_channel.
    snapshot = _snap(channels_list=[_ch("mod-log", ch_id=42)])
    embed = channels.build_channels_embed(snapshot)
    logging_field = next((f for f in embed.fields if f.name == "logging"), None)
    assert logging_field is not None
    # `mod_channel` should show "likely `#mod-log`".
    assert "mod_channel" in logging_field.value
    assert "mod-log" in logging_field.value


def test_embed_renders_no_match_hint_when_snapshot_unavailable():
    embed = channels.build_channels_embed(None)
    logging_field = next((f for f in embed.fields if f.name == "logging"), None)
    assert logging_field is not None
    # No "likely #" hint when there's no snapshot.
    assert "likely" not in logging_field.value


def test_embed_renders_empty_state_when_no_bindings(monkeypatch):
    monkeypatch.setattr(channels, "_all_channel_bindings", lambda: [])
    embed = channels.build_channels_embed(_snap())
    assert any("No channel bindings declared" in f.name for f in embed.fields)


# ---------------------------------------------------------------------------
# _all_channel_bindings
# ---------------------------------------------------------------------------


def test_all_channel_bindings_returns_known_logging_bindings():
    items = channels._all_channel_bindings()
    names = {name for _, b in items for name in [b.name]}
    # Logging declares these channel bindings.
    assert "mod_channel" in names
    assert "audit_channel" in names


# ---------------------------------------------------------------------------
# _stage_channel_binding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_channel_binding_drafts_bind_channel_op():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
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
        await channels._stage_channel_binding(
            interaction,
            subsystem="logging",
            binding_name="mod_channel",
            target_id=42,
            target_name="#mod-log",
            scan_match_id=None,
        )

    append_mock.assert_awaited_once()
    op = append_mock.await_args.args[0]
    assert op.kind == "bind_channel"
    assert op.subsystem == "logging"
    assert op.binding_name == "mod_channel"
    assert op.target_id == 42
    assert op.target_name == "#mod-log"
    assert op.target_kind == "channel"
    kwargs = append_mock.await_args.kwargs
    assert kwargs["guild_id"] == 1
    assert kwargs["actor_id"] == 99
    assert "logging.mod_channel → #mod-log" in kwargs["label"]


@pytest.mark.asyncio
async def test_stage_channel_binding_tags_source_manual_for_off_match_pick():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
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
        await channels._stage_channel_binding(
            interaction,
            subsystem="logging",
            binding_name="mod_channel",
            target_id=42,
            target_name="#general",
            scan_match_id=99,  # operator picked a different channel
        )
    md = append_mock.await_args.kwargs["metadata"]
    assert md["source"] == "manual"
    assert md["confidence"] == "high"
    assert md["risk"] == "low"
    assert "Operator picked" in md["reason"]


@pytest.mark.asyncio
async def test_stage_channel_binding_tags_source_scan_when_operator_picks_match():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
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
        await channels._stage_channel_binding(
            interaction,
            subsystem="logging",
            binding_name="mod_channel",
            target_id=42,
            target_name="#mod-log",
            scan_match_id=42,  # operator picked the scan-suggested channel
        )
    md = append_mock.await_args.kwargs["metadata"]
    assert md["source"] == "scan"
    assert md["confidence"] == "high"
    assert "Scan classifier matched" in md["reason"]


@pytest.mark.asyncio
async def test_stage_channel_binding_does_not_call_apply_operations():
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
        await channels._stage_channel_binding(
            interaction,
            subsystem="logging",
            binding_name="mod_channel",
            target_id=42,
            target_name="#mod-log",
            scan_match_id=None,
        )
    apply_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_channel_binding_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await channels._stage_channel_binding(
            interaction,
            subsystem="logging",
            binding_name="mod_channel",
            target_id=42,
            target_name="#mod-log",
            scan_match_id=None,
        )
    append_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_channel_binding_surfaces_append_failure():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB exploded"),
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await channels._stage_channel_binding(
            interaction,
            subsystem="logging",
            binding_name="mod_channel",
            target_id=42,
            target_name="#mod-log",
            scan_match_id=None,
        )
    msg = interaction.response.send_message.await_args.args[0]
    assert "stage" in msg.lower()
    mark_mock.assert_not_called()


# ---------------------------------------------------------------------------
# run() — entry point
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    """``run`` routes through the section card, which rejects DMs with
    a 'server'/'guild' phrasing.
    """
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    await channels.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    args = interaction.response.send_message.await_args.args
    assert "server" in args[0].lower() or "guild" in args[0].lower()


@pytest.mark.asyncio
async def test_run_opens_section_card_in_guild():
    """``run`` now shows the shared section card; the detailed channel
    picker is reachable via the card's Customize button.
    """
    from views.setup.section_card import SectionCardView

    interaction = _interaction()
    interaction.guild = MagicMock(id=1, name="Test", owner_id=99)
    hub = SimpleNamespace()

    with (
        patch(
            "views.setup.section_card.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "views.setup.section_card.setup_draft.list_ops",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.section_card.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await channels.run(interaction, hub)

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs["view"], SectionCardView)


@pytest.mark.asyncio
async def test_customize_run_uses_cached_snapshot_when_present():
    """The detailed picker (Customize target) still surfaces the
    cached snapshot's classifier hints in the embed.
    """
    interaction = _interaction()
    hub = SimpleNamespace()
    snap = _snap(channels_list=[_ch("mod-log", ch_id=42)])

    with patch(
        "views.setup.sections.server_scan.get_cached_snapshot",
        return_value=snap,
    ):
        await channels._customize_run(interaction, hub)

    interaction.response.send_message.assert_awaited_once()
    embed = interaction.response.send_message.await_args.kwargs["embed"]
    logging_field = next((f for f in embed.fields if f.name == "logging"), None)
    assert logging_field is not None
    assert "mod-log" in logging_field.value


@pytest.mark.asyncio
async def test_recommended_channel_ops_stages_high_confidence_picks():
    """``_recommended_channel_ops`` walks the binding catalogue, asks
    the recommender for a top pick per intent, and stages bind_channel
    ops only for high-confidence matches.
    """
    from services.channel_recommender import ChannelRecommendation

    guild = MagicMock()
    guild.id = 1
    guild.name = "Test"

    high = ChannelRecommendation(
        channel_id=42,
        channel_name="mod-log",
        intent="mod_logs",
        score=70,
        confidence="high",
        reasons=("Name match",),
        action="bind",
    )
    medium = ChannelRecommendation(
        channel_id=43,
        channel_name="random-log",
        intent="logs",
        score=45,
        confidence="medium",
        reasons=("Keyword hint",),
        action="bind",
    )

    def fake_top_pick(intent_slug, _snapshot):
        if intent_slug == "mod_logs":
            return high
        if intent_slug == "logs":
            return medium
        return None

    with (
        patch(
            "services.guild_snapshot.collect",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ),
        patch(
            "services.channel_recommender.top_pick",
            side_effect=fake_top_pick,
        ),
    ):
        ops = await channels._recommended_channel_ops(guild)

    # Only the high-confidence mod_logs pick should be staged.
    assert len(ops) == 1
    op = ops[0]
    assert op.kind == "bind_channel"
    assert op.target_id == 42
    assert op.binding_name == "mod_channel"


@pytest.mark.asyncio
async def test_recommended_channel_ops_returns_empty_when_snapshot_fails():
    guild = MagicMock()
    guild.id = 1
    guild.name = "Test"
    with patch(
        "services.guild_snapshot.collect",
        new_callable=AsyncMock,
        side_effect=RuntimeError("snapshot down"),
    ):
        ops = await channels._recommended_channel_ops(guild)
    assert ops == []


# ---------------------------------------------------------------------------
# Recommender wiring (channel_recommender)
# ---------------------------------------------------------------------------


def test_embed_surfaces_recommender_confidence_for_recognised_binding():
    """When the snapshot contains a channel that matches a binding's
    intent in ``channel_recommender``, the embed renders the confidence
    glyph + a one-line reason alongside the legacy 'likely #...' hint.
    """
    snapshot = _snap(channels_list=[_ch("mod-log", ch_id=42)])
    embed = channels.build_channels_embed(snapshot)
    logging_field = next((f for f in embed.fields if f.name == "logging"), None)
    assert logging_field is not None
    value = logging_field.value
    # The mod_channel row gets the high-confidence glyph and the
    # recommender's reason summary (name-match pattern).
    assert "✅" in value or "🟡" in value
    assert "high" in value.lower() or "medium" in value.lower()
    assert "mod-log" in value


def test_embed_falls_back_to_legacy_match_when_no_recommender_intent():
    """Bindings without a registered intent slug still show the legacy
    tag-based 'likely #channel' hint via ``_scan_match_for``.
    """
    # Construct a snapshot the recommender wouldn't know how to score
    # for a binding without an intent entry — the legacy path still fires.
    snapshot = _snap(channels_list=[_ch("info-feed", ch_id=42)])
    embed = channels.build_channels_embed(snapshot)
    # Pure regression: embed builds; some logging row is rendered.
    logging_field = next((f for f in embed.fields if f.name == "logging"), None)
    assert logging_field is not None


def test_recommendation_for_known_binding_returns_top_pick():
    """``_recommendation_for`` plumbs the binding name through to the
    recommender's ``top_pick`` and returns the resulting object.
    """
    snapshot = _snap(channels_list=[_ch("mod-log", ch_id=42)])
    rec = channels._recommendation_for(snapshot, "mod_channel")
    assert rec is not None
    assert rec.channel_id == 42
    assert rec.intent == "mod_logs"
    assert rec.confidence in ("high", "medium", "low")


def test_recommendation_for_unknown_binding_returns_none():
    snapshot = _snap(channels_list=[_ch("anything", ch_id=42)])
    assert channels._recommendation_for(snapshot, "binding_with_no_intent") is None


def test_recommendation_for_returns_none_without_snapshot():
    assert channels._recommendation_for(None, "mod_channel") is None

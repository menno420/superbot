"""Tests for the server scan presenter (``views.setup.scan_panel``).

Covers:

* The name classifier — every documented pattern matches the names
  it's supposed to match and rejects look-alikes.
* The aggregator helpers (``classify_snapshot``, ``first_match``).
* The missing-permissions probe.
* The embed builder shape — field set, footer guild_id, colour
  changes when blockers exist.
"""

from __future__ import annotations

from typing import Iterable

import discord
import pytest

from services.guild_snapshot import (
    CategoryMeta,
    ChannelMeta,
    GuildSnapshot,
    RoleMeta,
)
from views.setup.scan_panel import (
    ClassifiedChannel,
    build_scan_embed,
    classify_channel_name,
    classify_snapshot,
    first_match,
    missing_permissions,
)


def _ch(name: str, *, ch_id: int = 1, kind: str = "text") -> ChannelMeta:
    return ChannelMeta(
        id=ch_id,
        name=name,
        type=kind,
        topic=None,
        parent_category=None,
        position=0,
        bot_can_view=True,
        bot_can_send=True,
        bot_can_embed=True,
    )


def _snapshot(
    *,
    channels: Iterable[ChannelMeta] = (),
    categories: Iterable[CategoryMeta] = (),
    roles: Iterable[RoleMeta] = (),
) -> GuildSnapshot:
    return GuildSnapshot(
        guild_id=1,
        guild_name="Test Guild",
        owner_id=99,
        channels=tuple(channels),
        categories=tuple(categories),
        roles=tuple(roles),
    )


# ---------------------------------------------------------------------------
# classify_channel_name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected_tag"),
    [
        ("mod-log", "likely_log"),
        ("mod-log", "likely_mod_log"),
        ("audit-log", "likely_log"),
        ("bot-logs", "likely_log"),
        ("bot-commands", "likely_bot_cmd"),
        ("bot-cmd", "likely_bot_cmd"),
        ("bot-spam", "likely_bot_cmd"),
        ("admin-only", "likely_admin"),
        ("owner", "likely_admin"),
        ("staff", "likely_mod"),
        ("moderation", "likely_mod"),
        ("counting", "likely_counting"),
        ("mining", "likely_mining"),
        ("games", "likely_game"),
        ("casino", "likely_game"),
        ("blackjack", "likely_game"),
        ("general", "likely_general"),
        ("lobby", "likely_general"),
        ("welcome", "likely_welcome"),
        ("proofs", "likely_proof"),
    ],
)
def test_classifier_matches_documented_patterns(name: str, expected_tag: str):
    assert expected_tag in classify_channel_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "off-topic",
        "introductions",
        "random",
        "deals",
        "art",
    ],
)
def test_classifier_returns_empty_for_unmatched_names(name: str):
    assert classify_channel_name(name) == ()


def test_classifier_returns_empty_for_empty_name():
    assert classify_channel_name("") == ()


def test_classifier_is_case_insensitive():
    assert "likely_log" in classify_channel_name("MOD-LOG")
    assert "likely_general" in classify_channel_name("General")


def test_classifier_returns_tags_sorted():
    """Sort guarantees deterministic embed output."""
    tags = classify_channel_name("mod-log")
    assert list(tags) == sorted(tags)


# ---------------------------------------------------------------------------
# classify_snapshot / first_match
# ---------------------------------------------------------------------------


def test_classify_snapshot_returns_one_classified_per_channel():
    snap = _snapshot(channels=[_ch("general"), _ch("random")])
    result = classify_snapshot(snap)
    assert len(result) == 2
    assert {c.channel.name for c in result} == {"general", "random"}


def test_classify_snapshot_preserves_channel_object():
    ch = _ch("bot-cmd")
    snap = _snapshot(channels=[ch])
    result = classify_snapshot(snap)
    assert result[0].channel is ch
    assert "likely_bot_cmd" in result[0].tags


def test_first_match_returns_channel_with_tag():
    classified = (
        ClassifiedChannel(channel=_ch("random"), tags=()),
        ClassifiedChannel(channel=_ch("mod-log", ch_id=42), tags=("likely_log",)),
    )
    match = first_match(classified, "likely_log")
    assert match is not None
    assert match.id == 42


def test_first_match_returns_none_when_no_match():
    classified = (
        ClassifiedChannel(channel=_ch("random"), tags=()),
    )
    assert first_match(classified, "likely_log") is None


# ---------------------------------------------------------------------------
# missing_permissions
# ---------------------------------------------------------------------------


def test_missing_permissions_flags_unmanageable_categories():
    snap = _snapshot(
        categories=[
            CategoryMeta(id=1, name="Top", position=0, bot_can_manage=False),
            CategoryMeta(id=2, name="Mid", position=1, bot_can_manage=False),
        ],
    )
    findings = missing_permissions(snap)
    names = [f.name for f in findings]
    assert "manage_channels" in names


def test_missing_permissions_skips_categories_when_one_is_manageable():
    snap = _snapshot(
        categories=[
            CategoryMeta(id=1, name="Top", position=0, bot_can_manage=False),
            CategoryMeta(id=2, name="Mid", position=1, bot_can_manage=True),
        ],
    )
    findings = missing_permissions(snap)
    assert "manage_channels" not in [f.name for f in findings]


def test_missing_permissions_flags_unmanageable_roles():
    snap = _snapshot(
        roles=[
            RoleMeta(id=1, name="@everyone", position=0, bot_can_manage=False),
            RoleMeta(id=2, name="moderator", position=5, bot_can_manage=False),
        ],
    )
    findings = missing_permissions(snap)
    assert "manage_roles" in [f.name for f in findings]


def test_missing_permissions_flags_no_send_in_any_text_channel():
    snap = _snapshot(
        channels=[
            ChannelMeta(
                id=1, name="general", type="text", topic=None,
                parent_category=None, position=0,
                bot_can_view=True, bot_can_send=False, bot_can_embed=False,
            ),
            ChannelMeta(
                id=2, name="off-topic", type="text", topic=None,
                parent_category=None, position=1,
                bot_can_view=True, bot_can_send=False, bot_can_embed=False,
            ),
        ],
    )
    findings = missing_permissions(snap)
    assert "send_messages" in [f.name for f in findings]


def test_missing_permissions_skips_send_when_any_text_channel_works():
    snap = _snapshot(
        channels=[
            ChannelMeta(
                id=1, name="general", type="text", topic=None,
                parent_category=None, position=0,
                bot_can_view=True, bot_can_send=False, bot_can_embed=False,
            ),
            ChannelMeta(
                id=2, name="bot-cmd", type="text", topic=None,
                parent_category=None, position=1,
                bot_can_view=True, bot_can_send=True, bot_can_embed=True,
            ),
        ],
    )
    findings = missing_permissions(snap)
    assert "send_messages" not in [f.name for f in findings]


def test_missing_permissions_returns_empty_when_no_resources():
    snap = _snapshot()  # no channels, categories, roles
    assert missing_permissions(snap) == ()


# ---------------------------------------------------------------------------
# build_scan_embed
# ---------------------------------------------------------------------------


def test_embed_includes_guild_name_in_title():
    snap = _snapshot()
    snap = GuildSnapshot(
        guild_id=42,
        guild_name="My Test Server",
        owner_id=99,
    )
    embed = build_scan_embed(snap)
    assert "My Test Server" in embed.title


def test_embed_inventory_field_lists_counts():
    snap = _snapshot(
        channels=[
            _ch("general", kind="text"),
            _ch("voice-chat", kind="voice"),
        ],
        categories=[CategoryMeta(id=1, name="Top", position=0, bot_can_manage=True)],
        roles=[RoleMeta(id=1, name="@everyone", position=0, bot_can_manage=False)],
    )
    embed = build_scan_embed(snap)
    inventory_field = next(
        (f for f in embed.fields if f.name == "Inventory"),
        None,
    )
    assert inventory_field is not None
    assert "text=1" in inventory_field.value
    assert "voice=1" in inventory_field.value
    assert "categories`: 1" in inventory_field.value
    assert "roles`: 1" in inventory_field.value


def test_embed_likely_matches_lists_classified_channels():
    snap = _snapshot(
        channels=[
            _ch("general", ch_id=10),
            _ch("mod-log", ch_id=11),
            _ch("bot-cmd", ch_id=12),
        ],
    )
    embed = build_scan_embed(snap)
    likely_field = next(
        (f for f in embed.fields if f.name == "Likely matches"),
        None,
    )
    assert likely_field is not None
    assert "#general" in likely_field.value
    assert "#mod-log" in likely_field.value
    assert "#bot-cmd" in likely_field.value


def test_embed_likely_matches_field_skipped_when_no_matches():
    snap = _snapshot(channels=[_ch("random")])
    embed = build_scan_embed(snap)
    field_names = [f.name for f in embed.fields]
    assert "Likely matches" not in field_names


def test_embed_blockers_field_appears_when_permissions_missing():
    snap = _snapshot(
        categories=[CategoryMeta(id=1, name="Top", position=0, bot_can_manage=False)],
    )
    embed = build_scan_embed(snap)
    block_field = next(
        (f for f in embed.fields if "blockers" in f.name.lower()),
        None,
    )
    assert block_field is not None
    assert "manage_channels" in block_field.value


def test_embed_blockers_field_skipped_when_no_permissions_missing():
    snap = _snapshot(
        categories=[CategoryMeta(id=1, name="Top", position=0, bot_can_manage=True)],
        roles=[RoleMeta(id=1, name="@everyone", position=0, bot_can_manage=True)],
    )
    embed = build_scan_embed(snap)
    field_names = [f.name for f in embed.fields]
    assert all("blockers" not in n.lower() for n in field_names)


def test_embed_colour_red_when_blockers_present():
    snap = _snapshot(
        categories=[CategoryMeta(id=1, name="Top", position=0, bot_can_manage=False)],
    )
    embed = build_scan_embed(snap)
    assert embed.color == discord.Color.red()


def test_embed_colour_blurple_when_clean():
    snap = _snapshot()
    embed = build_scan_embed(snap)
    assert embed.color == discord.Color.blurple()


def test_embed_footer_includes_guild_id():
    snap = GuildSnapshot(guild_id=42, guild_name="x", owner_id=0)
    embed = build_scan_embed(snap)
    assert "42" in embed.footer.text

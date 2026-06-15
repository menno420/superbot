"""PR4A — override list aggregates the three typed-policy tables, paged."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from utils.db import ai as ai_db  # noqa: E402
from views.ai.policy.list_view import (  # noqa: E402
    PolicyEntry,
    PolicyListView,
    build_list_embed,
    collect_entries,
)

# ---------------------------------------------------------------------------
# collect_entries
# ---------------------------------------------------------------------------


async def test_collect_entries_aggregates_all_three_scopes(monkeypatch):
    channel_rows = [
        {"channel_id": 100, "mode": "disabled", "min_level": None,
         "cooldown_seconds": None},
        {"channel_id": 101, "mode": "always_reply", "min_level": 3,
         "cooldown_seconds": 60},
    ]
    category_rows = [
        {"category_id": 200, "mode": "mention_only", "min_level": None,
         "cooldown_seconds": None},
    ]
    role_rows = [
        {"role_id": 300, "decision": "deny", "min_level_override": None,
         "bypass_cooldown": False},
        {"role_id": 301, "decision": "allow", "min_level_override": 10,
         "bypass_cooldown": True},
    ]

    async def _ch(guild_id):
        return channel_rows

    async def _cat(guild_id):
        return category_rows

    async def _role(guild_id):
        return role_rows

    monkeypatch.setattr(ai_db, "list_channel_policies", _ch)
    monkeypatch.setattr(ai_db, "list_category_policies", _cat)
    monkeypatch.setattr(ai_db, "list_role_policies", _role)

    entries = await collect_entries(guild_id=42)
    # Ordering: channel → category → role.
    scopes = [e.scope for e in entries]
    assert scopes == ["channel", "channel", "category", "role", "role"]
    by_target = {e.target_id: e for e in entries}
    assert "disabled" in by_target[100].summary
    assert "min_level=`3`" in by_target[101].summary
    assert "cooldown=`60s`" in by_target[101].summary
    assert "mention_only" in by_target[200].summary
    assert "deny" in by_target[300].summary
    assert "min_level_override=`10`" in by_target[301].summary
    assert "bypass_cooldown=`yes`" in by_target[301].summary


async def test_collect_entries_returns_empty_when_no_overrides(monkeypatch):
    async def _empty(guild_id):
        return []

    monkeypatch.setattr(ai_db, "list_channel_policies", _empty)
    monkeypatch.setattr(ai_db, "list_category_policies", _empty)
    monkeypatch.setattr(ai_db, "list_role_policies", _empty)
    entries = await collect_entries(guild_id=42)
    assert entries == []


# ---------------------------------------------------------------------------
# build_list_embed
# ---------------------------------------------------------------------------


def _make_entries(n: int) -> list[PolicyEntry]:
    return [
        PolicyEntry(scope="channel", target_id=1000 + i, summary=f"mode=`m{i}`")
        for i in range(n)
    ]


def test_empty_list_embed_explains_no_overrides():
    embed, total_pages = build_list_embed([], page=1)
    assert total_pages == 1
    fields = {f.name: f.value for f in embed.fields}
    assert "No overrides" in fields
    assert "baseline `ai_guild_policy`" in fields["No overrides"]


def test_embed_paginates_at_ten_per_page():
    entries = _make_entries(25)
    embed_p1, total = build_list_embed(entries, page=1)
    assert total == 3
    # Page 1 has 10 fields.
    assert len(embed_p1.fields) == 10
    embed_p3, _ = build_list_embed(entries, page=3)
    # Last page has the remainder.
    assert len(embed_p3.fields) == 5


def test_page_number_is_clamped_to_valid_range():
    entries = _make_entries(5)  # one page only
    embed_high, total = build_list_embed(entries, page=99)
    assert total == 1
    assert "Page 1 / 1" in embed_high.footer.text
    embed_zero, _ = build_list_embed(entries, page=0)
    assert "Page 1 / 1" in embed_zero.footer.text


def test_footer_carries_page_and_total():
    entries = _make_entries(15)
    embed, _ = build_list_embed(entries, page=2)
    assert "Page 2 / 2" in embed.footer.text
    assert "administrator-only" in embed.footer.text


def test_total_count_in_description():
    entries = _make_entries(17)
    embed, _ = build_list_embed(entries, page=1)
    assert "17 total override" in (embed.description or "")


# ---------------------------------------------------------------------------
# PolicyListView pagination buttons
# ---------------------------------------------------------------------------


def _admin_interaction_for_edit() -> MagicMock:
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def test_view_disables_prev_on_first_page():
    entries = _make_entries(25)
    view = PolicyListView(entries, page=1)
    assert view.prev_btn.disabled is True
    assert view.next_btn.disabled is False


def test_view_disables_next_on_last_page():
    entries = _make_entries(25)
    view = PolicyListView(entries, page=3)
    assert view.prev_btn.disabled is False
    assert view.next_btn.disabled is True


def test_view_disables_both_buttons_with_single_page():
    entries = _make_entries(3)
    view = PolicyListView(entries, page=1)
    assert view.prev_btn.disabled is True
    assert view.next_btn.disabled is True


async def test_next_button_advances_page_and_refreshes_embed():
    entries = _make_entries(25)
    view = PolicyListView(entries, page=1)
    interaction = _admin_interaction_for_edit()
    await view.next_btn.callback(interaction)
    assert view.page == 2
    assert view.prev_btn.disabled is False
    assert view.next_btn.disabled is False
    interaction.response.edit_message.assert_awaited_once()
    _, kwargs = interaction.response.edit_message.call_args
    embed = kwargs["embed"]
    assert "Page 2 / 3" in embed.footer.text


async def test_prev_button_decrements_and_clamps_at_one():
    entries = _make_entries(25)
    view = PolicyListView(entries, page=2)
    interaction = _admin_interaction_for_edit()
    await view.prev_btn.callback(interaction)
    assert view.page == 1
    assert view.prev_btn.disabled is True
    # Click again at page 1: stays at 1.
    interaction = _admin_interaction_for_edit()
    await view.prev_btn.callback(interaction)
    assert view.page == 1


async def test_view_rejects_non_admin():
    entries = _make_entries(5)
    view = PolicyListView(entries, page=1)
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response.send_message = AsyncMock()
    allowed = await view.interaction_check(interaction)
    assert allowed is False


# ---------------------------------------------------------------------------
# Chooser button now opens the real list view.
# ---------------------------------------------------------------------------


async def test_chooser_list_button_opens_real_list_view(monkeypatch):
    """The list button now calls collect_entries + ships
    PolicyListView, replacing the placeholder follow-up that
    test_policy_chooser exercised in commits 1–3.
    """
    from views.ai.policy.chooser import PolicyChooserView

    async def _entries(_guild):
        return []

    monkeypatch.setattr(
        "views.ai.policy.list_view.collect_entries",
        _entries,
    )

    view = PolicyChooserView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.guild = MagicMock()
    interaction.guild.id = 999
    interaction.response.send_message = AsyncMock()
    await view.list_btn.callback(interaction)

    _, kwargs = interaction.response.send_message.call_args
    assert isinstance(kwargs["view"], PolicyListView)
    assert kwargs.get("ephemeral") is True
    embed = kwargs["embed"]
    assert "AI policy overrides" in (embed.title or "")


async def test_chooser_list_button_requires_guild_context(monkeypatch):
    from views.ai.policy.chooser import PolicyChooserView

    called = {"hit": False}

    async def _explode(_guild):
        called["hit"] = True
        return []

    monkeypatch.setattr(
        "views.ai.policy.list_view.collect_entries",
        _explode,
    )

    view = PolicyChooserView()
    interaction = MagicMock()
    interaction.user.guild_permissions.administrator = True
    interaction.guild = None
    interaction.response.send_message = AsyncMock()
    await view.list_btn.callback(interaction)
    assert called["hit"] is False
    args, _ = interaction.response.send_message.call_args
    assert "guild context" in args[0]

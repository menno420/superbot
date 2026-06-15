"""Guided CT-team flow (Settings Phase 2, Q-0064): parse → preview → confirm.

Pins the decided shape: a pasted URL/id is never written immediately — the
commit lives in the Confirm callback, which re-checks Manage Server at
execution time; the typed ``btd6_ct_team_service`` stays the mutation owner.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.btd6._builders import handle_ctteam
from views.btd6.ct_group_flow import (
    CTGroupConfirmView,
    CTGroupEntryView,
    build_ct_preview_embed,
)


def _ctx(*, manage_guild: bool = True, guild_id: int = 99):
    ctx = MagicMock()
    ctx.guild = MagicMock()
    ctx.guild.id = guild_id
    ctx.author = MagicMock()
    ctx.author.id = 1
    ctx.author.guild_permissions = MagicMock(manage_guild=manage_guild)
    return ctx


def _interaction(*, manage_guild: bool = True, guild_id: int = 99):
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.user = MagicMock()
    interaction.user.id = 1
    interaction.user.guild_permissions = MagicMock(manage_guild=manage_guild)
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


@pytest.fixture
def _service(monkeypatch):
    """Patch the typed CT service the flow composes."""
    svc = MagicMock()
    svc.parse_group_id = MagicMock(return_value="abc123")
    svc.get_team_group_id = AsyncMock(return_value="")
    svc.get_ct_bracket = AsyncMock(return_value=MagicMock(ct_id=None))
    svc.set_team_group_id = AsyncMock(return_value="abc123")
    svc.clear_team_group_id = AsyncMock()
    monkeypatch.setattr(
        "services.btd6_ct_team_service.parse_group_id", svc.parse_group_id,
    )
    monkeypatch.setattr(
        "services.btd6_ct_team_service.get_team_group_id", svc.get_team_group_id,
    )
    monkeypatch.setattr(
        "services.btd6_ct_team_service.get_ct_bracket", svc.get_ct_bracket,
    )
    monkeypatch.setattr(
        "services.btd6_ct_team_service.set_team_group_id", svc.set_team_group_id,
    )
    monkeypatch.setattr(
        "services.btd6_ct_team_service.clear_team_group_id", svc.clear_team_group_id,
    )
    return svc


# ---------------------------------------------------------------------------
# handle_ctteam — the command entry routes through the guided flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_path_previews_without_writing(_service):
    embed, view = await handle_ctteam(_ctx(), "https://x/leaderboard/group/abc123")

    _service.set_team_group_id.assert_not_awaited()  # commit waits for Confirm
    assert isinstance(view, CTGroupConfirmView)
    assert "Confirm" in embed.title


@pytest.mark.asyncio
async def test_unparseable_input_returns_notice(_service):
    _service.parse_group_id.return_value = None

    embed, view = await handle_ctteam(_ctx(), "garbage")

    assert view is None
    assert "doesn't look like" in embed.description
    _service.set_team_group_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_clear_stays_immediate(_service):
    embed, view = await handle_ctteam(_ctx(), "clear")

    _service.clear_team_group_id.assert_awaited_once_with(99)
    assert view is None


@pytest.mark.asyncio
async def test_no_arg_offers_entry_button_to_managers(_service):
    _embed, view = await handle_ctteam(_ctx(manage_guild=True), "")
    assert isinstance(view, CTGroupEntryView)

    _embed, view = await handle_ctteam(_ctx(manage_guild=False), "")
    assert view is None


@pytest.mark.asyncio
async def test_set_path_denied_without_manage_guild(_service):
    embed, view = await handle_ctteam(_ctx(manage_guild=False), "abc123")

    assert view is None
    assert "Manage Server" in embed.description
    _service.set_team_group_id.assert_not_awaited()


# ---------------------------------------------------------------------------
# Confirm/Cancel — authority re-check + service-owned commit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_commits_through_the_typed_service(_service):
    view = CTGroupConfirmView(MagicMock(id=1), "abc123")
    interaction = _interaction()

    await type(view).confirm(view, interaction, MagicMock())

    _service.set_team_group_id.assert_awaited_once_with(99, "abc123")
    interaction.response.edit_message.assert_awaited_once()
    assert "✅" in interaction.response.edit_message.await_args.kwargs["content"]


@pytest.mark.asyncio
async def test_confirm_rechecks_authority_at_callback_time(_service):
    """Opening the preview never authorizes the commit (views rule)."""
    view = CTGroupConfirmView(MagicMock(id=1), "abc123")
    interaction = _interaction(manage_guild=False)

    await type(view).confirm(view, interaction, MagicMock())

    _service.set_team_group_id.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Manage Server" in msg


@pytest.mark.asyncio
async def test_cancel_discards_without_writing(_service):
    view = CTGroupConfirmView(MagicMock(id=1), "abc123")
    interaction = _interaction()

    await type(view).cancel(view, interaction, MagicMock())

    _service.set_team_group_id.assert_not_awaited()
    assert (
        "unchanged"
        in interaction.response.edit_message.await_args.kwargs["content"]
    )


# ---------------------------------------------------------------------------
# Preview embed — best-effort live standing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_shows_change_from_current(_service):
    _service.get_team_group_id.return_value = "old999"

    embed = await build_ct_preview_embed(99, "abc123")

    change = next(f for f in embed.fields if f.name == "Change")
    assert "old999" in change.value and "abc123" in change.value


@pytest.mark.asyncio
async def test_preview_survives_live_fetch_failure(_service):
    _service.get_ct_bracket.side_effect = RuntimeError("api down")

    embed = await build_ct_preview_embed(99, "abc123")

    preview = next(f for f in embed.fields if f.name == "Preview")
    assert "still confirm" in preview.value

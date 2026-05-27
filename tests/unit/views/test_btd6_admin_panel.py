"""Tests for the new ephemeral admin sub-view."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.btd6.admin_panel import (
    _PARENT_SOURCES,
    BTD6AdminView,
    build_admin_embed,
)

# ---------------------------------------------------------------------------
# build_admin_embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_embed_lists_parent_sources():
    embed = await build_admin_embed()
    assert isinstance(embed, discord.Embed)
    blob = " ".join(f.value or "" for f in embed.fields)
    for src in _PARENT_SOURCES:
        assert src in blob


# ---------------------------------------------------------------------------
# BTD6AdminView.create — async factory + multi-select population
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_populates_multiselect_from_registry(monkeypatch):
    from services import btd6_source_registry

    async def _list_enabled(*, limit=100):
        return [
            {"source_key": "nk_btd6_events"},
            {"source_key": "nk_btd6_races"},
            {"source_key": "nk_btd6_maps"},
        ]

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _list_enabled)

    view = await BTD6AdminView.create(opener_user_id=42)
    option_values = [o.value for o in view.source_select.options]
    assert set(option_values) == {
        "nk_btd6_events",
        "nk_btd6_races",
        "nk_btd6_maps",
    }


@pytest.mark.asyncio
async def test_create_handles_registry_failure_gracefully(monkeypatch):
    from services import btd6_source_registry

    async def _boom(*, limit=100):
        raise RuntimeError("DB down")

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _boom)

    # No exception escapes; the view still builds with a placeholder.
    view = await BTD6AdminView.create(opener_user_id=42)
    assert isinstance(view, BTD6AdminView)
    # The multi-select must have at least one option to satisfy discord.py.
    assert view.source_select.options


@pytest.mark.asyncio
async def test_create_caps_options_at_discord_max_25(monkeypatch):
    from services import btd6_source_registry

    async def _many(*, limit=100):
        return [{"source_key": f"nk_btd6_src_{i:02d}"} for i in range(40)]

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _many)

    view = await BTD6AdminView.create(opener_user_id=42)
    assert len(view.source_select.options) == 25


# ---------------------------------------------------------------------------
# interaction_check — non-opener / non-staff are rejected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_interaction_check_rejects_non_opener(monkeypatch):
    from services import btd6_source_registry

    async def _list_enabled(*, limit=100):
        return [{"source_key": "nk_btd6_events"}]

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _list_enabled)

    view = await BTD6AdminView.create(opener_user_id=42)

    interaction = MagicMock()
    interaction.user.id = 999  # not the opener
    interaction.response.send_message = AsyncMock()

    allowed = await view.interaction_check(interaction)
    assert allowed is False
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "isn't yours" in msg


@pytest.mark.asyncio
async def test_interaction_check_rejects_non_staff(monkeypatch):
    from services import btd6_source_registry

    async def _list_enabled(*, limit=100):
        return [{"source_key": "nk_btd6_events"}]

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _list_enabled)

    view = await BTD6AdminView.create(opener_user_id=42)

    interaction = MagicMock()
    interaction.user.id = 42  # the opener
    interaction.user.guild_permissions.administrator = False
    interaction.user.guild_permissions.manage_guild = False
    interaction.response.send_message = AsyncMock()

    allowed = await view.interaction_check(interaction)
    assert allowed is False
    msg = interaction.response.send_message.await_args.args[0]
    assert "Staff" in msg


@pytest.mark.asyncio
async def test_interaction_check_accepts_staff_opener(monkeypatch):
    from services import btd6_source_registry

    async def _list_enabled(*, limit=100):
        return [{"source_key": "nk_btd6_events"}]

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _list_enabled)

    view = await BTD6AdminView.create(opener_user_id=42)

    interaction = MagicMock()
    interaction.user.id = 42
    interaction.user.guild_permissions.administrator = False
    interaction.user.guild_permissions.manage_guild = True
    interaction.response.send_message = AsyncMock()

    allowed = await view.interaction_check(interaction)
    assert allowed is True
    interaction.response.send_message.assert_not_awaited()


# ---------------------------------------------------------------------------
# Fetch buttons — calls per source, progress edits, summary
# ---------------------------------------------------------------------------


def _make_result(source_key: str, *, ok: bool = True):
    from services import btd6_ingestion_service

    return btd6_ingestion_service.IngestionResult(
        source_key=source_key,
        status="ok" if ok else "fetch_error",
        fact_count=3 if ok else 0,
        duration_ms=1,
        error_code=None if ok else "503",
        run_id=1,
        written_entity_keys=("a", "b", "c") if ok else (),
    )


@pytest.mark.asyncio
async def test_fetch_all_button_runs_each_parent_source(monkeypatch):
    from services import btd6_ingestion_service, btd6_source_registry
    from views.btd6 import admin_panel

    async def _list_enabled(*, limit=100):
        return [{"source_key": "nk_btd6_events"}]

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _list_enabled)

    calls: list[str] = []

    async def _stub(source_key, *, reason, started_by_user_id):
        calls.append(source_key)
        return [_make_result(source_key)]

    monkeypatch.setattr(
        btd6_ingestion_service, "refresh_source_or_dependencies", _stub,
    )

    view = await BTD6AdminView.create(opener_user_id=42)

    interaction = MagicMock()
    interaction.user.id = 42
    interaction.user.guild_permissions.manage_guild = True
    interaction.response.is_done = lambda: False
    interaction.response.defer = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.followup.send = AsyncMock()

    # Find the Fetch All button instance and invoke its callback directly.
    fetch_all = next(
        c for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Fetch All"
    )
    # discord.py binds the parent view via Item._view; emulate that.
    fetch_all._view = view

    await fetch_all.callback(interaction)

    # One service call per parent source.
    assert calls == list(_PARENT_SOURCES)


@pytest.mark.asyncio
async def test_fetch_selected_button_uses_dropdown_values(monkeypatch):
    from services import btd6_ingestion_service, btd6_source_registry

    async def _list_enabled(*, limit=100):
        return [
            {"source_key": "nk_btd6_events"},
            {"source_key": "nk_btd6_races"},
            {"source_key": "nk_btd6_maps"},
        ]

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _list_enabled)

    calls: list[str] = []

    async def _stub(source_key, *, reason, started_by_user_id):
        calls.append(source_key)
        return [_make_result(source_key)]

    monkeypatch.setattr(
        btd6_ingestion_service, "refresh_source_or_dependencies", _stub,
    )

    view = await BTD6AdminView.create(opener_user_id=42)
    # Simulate the operator picking two from the dropdown.
    view.source_select._values = ["nk_btd6_races", "nk_btd6_maps"]
    # discord.py reads `Select.values` from the underlying data; mock it
    # directly since we're not going through the gateway.
    type(view.source_select).values = property(lambda self: self._values)

    interaction = MagicMock()
    interaction.user.id = 42
    interaction.user.guild_permissions.manage_guild = True
    interaction.response.is_done = lambda: False
    interaction.response.defer = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.response.send_message = AsyncMock()

    fetch_sel = next(
        c for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Fetch Selected"
    )
    fetch_sel._view = view

    await fetch_sel.callback(interaction)

    assert calls == ["nk_btd6_races", "nk_btd6_maps"]


@pytest.mark.asyncio
async def test_fetch_selected_button_with_no_picks_complains(monkeypatch):
    from services import btd6_source_registry

    async def _list_enabled(*, limit=100):
        return [{"source_key": "nk_btd6_events"}]

    monkeypatch.setattr(btd6_source_registry, "list_enabled_sources", _list_enabled)

    view = await BTD6AdminView.create(opener_user_id=42)
    view.source_select._values = []
    type(view.source_select).values = property(lambda self: self._values)

    interaction = MagicMock()
    interaction.user.id = 42
    interaction.user.guild_permissions.manage_guild = True
    interaction.response.send_message = AsyncMock()

    fetch_sel = next(
        c for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Fetch Selected"
    )
    fetch_sel._view = view

    await fetch_sel.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Pick at least one" in msg

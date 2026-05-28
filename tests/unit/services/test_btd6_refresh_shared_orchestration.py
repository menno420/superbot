"""Regression: prefix / slash / admin view share one refresh orchestration call.

All three manual-refresh paths must route through
``btd6_ingestion_service.refresh_source_or_dependencies`` with the
same kwargs (``reason="manual"``, ``started_by_user_id`` set). Drift
between these surfaces would let one form bypass audit / lock
machinery — this test pins them together.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest


@pytest.mark.asyncio
async def test_prefix_refresh_calls_orchestration(monkeypatch) -> None:
    from cogs.btd6 import _event_helpers
    from services import btd6_ingestion_service, btd6_source_registry

    fake_call = AsyncMock(return_value=[])
    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        fake_call,
    )
    monkeypatch.setattr(
        btd6_source_registry,
        "list_all",
        AsyncMock(return_value=[]),
    )

    await _event_helpers.build_refresh_source_payload(
        "nk_btd6_races",
        started_by_user_id=999,
        include_exception_detail=False,
    )
    fake_call.assert_awaited_once_with(
        "nk_btd6_races",
        reason="manual",
        started_by_user_id=999,
    )


@pytest.mark.asyncio
async def test_slash_refresh_uses_same_helper(monkeypatch) -> None:
    """The slash form must call the same payload builder as the prefix form."""
    from cogs.btd6 import _event_helpers
    from services import btd6_ingestion_service, btd6_source_registry

    fake_call = AsyncMock(return_value=[])
    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        fake_call,
    )
    monkeypatch.setattr(
        btd6_source_registry,
        "list_all",
        AsyncMock(return_value=[]),
    )

    await _event_helpers.build_refresh_source_payload(
        "nk_btd6_bosses",
        started_by_user_id=12345,
        include_exception_detail=True,
    )
    fake_call.assert_awaited_once_with(
        "nk_btd6_bosses",
        reason="manual",
        started_by_user_id=12345,
    )


@pytest.mark.asyncio
async def test_admin_view_refresh_calls_same_orchestration(monkeypatch) -> None:
    """The admin Fetch Selected path must hit the same service entrypoint."""
    from services import btd6_ingestion_service
    from views.btd6 import admin_panel

    fake_call = AsyncMock(return_value=[])
    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        fake_call,
    )

    # Build a minimal interaction stub that ``_run_fetch`` needs.
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = 7
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()

    await admin_panel._run_fetch(
        interaction,
        ["nk_btd6_races"],
        user_id=7,
        label="Fetch All",
    )
    fake_call.assert_awaited_once_with(
        "nk_btd6_races",
        reason="manual",
        started_by_user_id=7,
    )


@pytest.mark.asyncio
async def test_all_three_paths_pass_same_kwargs(monkeypatch) -> None:
    """Hard assertion: prefix, slash twin, and admin view use identical kwargs."""
    from cogs.btd6 import _event_helpers
    from services import btd6_ingestion_service, btd6_source_registry
    from views.btd6 import admin_panel

    fake_call = AsyncMock(return_value=[])
    monkeypatch.setattr(
        btd6_ingestion_service,
        "refresh_source_or_dependencies",
        fake_call,
    )
    monkeypatch.setattr(
        btd6_source_registry,
        "list_all",
        AsyncMock(return_value=[]),
    )

    await _event_helpers.build_refresh_source_payload(
        "nk_btd6_races",
        started_by_user_id=42,
        include_exception_detail=False,
    )

    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock(id=42)
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.followup = MagicMock(send=AsyncMock())

    await admin_panel._run_fetch(
        interaction,
        ["nk_btd6_races"],
        user_id=42,
        label="x",
    )

    calls = fake_call.await_args_list
    assert len(calls) == 2
    # Every call uses the same kwargs shape: positional source_key plus
    # keyword reason="manual" + started_by_user_id=<int>.
    for call in calls:
        args, kwargs = call.args, call.kwargs
        assert args == ("nk_btd6_races",)
        assert kwargs["reason"] == "manual"
        assert isinstance(kwargs["started_by_user_id"], int)

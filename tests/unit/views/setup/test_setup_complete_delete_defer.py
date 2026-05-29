"""Regression test for ``SetupCompleteView._on_delete`` (final_review).

Pre-fix, ``_on_delete`` deleted the setup channel (where the view's
message lives) *before* acknowledging the interaction, then tried
``response.edit_message`` (message gone) with a ``followup`` fallback.
Because the interaction was never ACKed, the followup 404'd with
"Unknown Webhook" (10015) and the click crashed.

The fix defers the interaction (ACK) BEFORE the destructive delete, then
replies via ``followup``.  These pin: defer happens before cleanup, and
the success reply uses ``followup.send`` (never ``response.*``, since the
message's channel is gone).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from views.setup import final_review
from views.setup.final_review import ApplySummary, SetupCompleteView


def _interaction() -> MagicMock:
    i = MagicMock()
    i.user = MagicMock(spec=discord.Member)
    i.user.id = 1
    i.guild = MagicMock()
    i.guild.id = 99
    i.response = MagicMock()
    i.response.is_done = MagicMock(return_value=False)
    i.response.defer = AsyncMock()
    i.response.send_message = AsyncMock()
    i.response.edit_message = AsyncMock()
    i.followup = MagicMock()
    i.followup.send = AsyncMock()
    return i


@pytest.mark.asyncio
async def test_delete_defers_before_destructive_delete(monkeypatch):
    order: list[str] = []

    async def fake_gate(_interaction):
        return True

    async def fake_defer(interaction, **_kw):
        order.append("defer")
        interaction.response.is_done = MagicMock(return_value=True)
        return True

    async def fake_resume(_gid):
        return SimpleNamespace()

    async def fake_cleanup(_guild, _session, *, actor):
        order.append("cleanup")
        return SimpleNamespace(reason="ok", detail="")

    monkeypatch.setattr(final_review, "_gate_apply", fake_gate)
    monkeypatch.setattr("core.runtime.interaction_helpers.safe_defer", fake_defer)
    monkeypatch.setattr("services.setup_session.resume_session", fake_resume)
    monkeypatch.setattr(
        "services.setup_channel.cleanup_setup_channel_after_completion",
        fake_cleanup,
    )

    view = SetupCompleteView(
        MagicMock(spec=discord.Member),
        summary=ApplySummary(applied=["x"]),
    )
    interaction = _interaction()

    await view._on_delete(interaction)

    # The ACK (defer) MUST precede the channel delete.
    assert order == ["defer", "cleanup"]
    # Success confirmation goes via followup (the message's channel is
    # gone); response.* must not be used on the success path.
    interaction.followup.send.assert_awaited_once()
    interaction.response.send_message.assert_not_awaited()
    interaction.response.edit_message.assert_not_awaited()

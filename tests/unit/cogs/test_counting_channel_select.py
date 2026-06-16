"""Counting panel: enable/disable an EXISTING channel + per-channel mutate.

Guards the live-tested "where to change whitelisted channels" gap — the panel
can now register an existing channel as a counting channel (no new channel
created) and disable it again without deleting it.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import cogs.counting_cog as counting_cog
from cogs.counting_cog import CountingCog


def _cog() -> CountingCog:
    return CountingCog(bot=MagicMock())


@pytest.mark.asyncio
async def test_enable_then_disable_existing_channel(monkeypatch) -> None:
    monkeypatch.setattr(counting_cog.db, "set_counting_state", AsyncMock(return_value=None))
    cog = _cog()
    assert await cog.enable_channel("1", "100", "normal") is True
    assert cog.count_data["1"]["channels"]["100"]["mode"] == "normal"
    # idempotent: already active
    assert await cog.enable_channel("1", "100", "normal") is False
    # disable removes membership without touching any Discord channel
    assert await cog.disable_channel("1", "100") is True
    assert "100" not in cog.count_data["1"]["channels"]
    assert await cog.disable_channel("1", "100") is False


@pytest.mark.asyncio
async def test_enable_rejects_arg_modes() -> None:
    cog = _cog()
    assert await cog.enable_channel("1", "100", "multiples") is False
    assert await cog.enable_channel("1", "100", "custom") is False


@pytest.mark.asyncio
async def test_toggle_and_reset_channel(monkeypatch) -> None:
    monkeypatch.setattr(counting_cog.db, "set_counting_state", AsyncMock(return_value=None))
    cog = _cog()
    await cog.enable_channel("1", "100", "normal")
    assert await cog.toggle_channel_flag("1", "100", "taking_turns") is True
    assert cog.count_data["1"]["channels"]["100"]["taking_turns"] is True
    cog.count_data["1"]["channels"]["100"]["current_count"] = 42
    assert await cog.reset_channel_count("1", "100") is True
    assert cog.count_data["1"]["channels"]["100"]["current_count"] == 0
    # missing channel → False, no crash
    assert await cog.toggle_channel_flag("1", "999", "taking_turns") is False

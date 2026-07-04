"""Contribute-modal parse tests for the Treasury panel.

Completion-first deepening (Q-0209) — clears Treasury completion-cert punch **#2**
(`docs/planning/feature-completion/units/treasury.md`): the `_ContributeModal.on_submit`
amount-parse edge cases (non-integer / negative / zero → ephemeral error, no write;
valid → the audited `treasury_service.contribute` + in-place redraw).

Pure test coverage — no runtime change.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from views.treasury.menu import _ContributeModal


def _panel(*, guild_id: int = 55, author_id: int = 7) -> MagicMock:
    panel = MagicMock()
    panel.guild_id = guild_id
    panel._author = MagicMock()
    panel._author.id = author_id
    panel._redraw = AsyncMock()
    return panel


def _modal(raw: str) -> _ContributeModal:
    panel = _panel()
    modal = _ContributeModal(panel)
    modal.amount_input = MagicMock()
    modal.amount_input.value = raw
    return modal


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", ["abc", "10.5", "", "  "])
async def test_non_integer_amount_errors_without_write(raw):
    modal = _modal(raw)
    interaction = _interaction()
    with patch("views.treasury.menu.treasury_service.contribute") as contribute:
        await modal.on_submit(interaction)
    contribute.assert_not_called()
    modal._panel._redraw.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs["ephemeral"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", ["0", "-100"])
async def test_non_positive_amount_errors_without_write(raw):
    modal = _modal(raw)
    interaction = _interaction()
    with patch("views.treasury.menu.treasury_service.contribute") as contribute:
        await modal.on_submit(interaction)
    contribute.assert_not_called()
    modal._panel._redraw.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    assert "positive" in interaction.response.send_message.await_args.args[0]


@pytest.mark.asyncio
async def test_valid_amount_contributes_and_redraws():
    modal = _modal("100000000")  # a large but valid amount (12-char cap)
    interaction = _interaction()
    result = MagicMock()
    result.message = "Contributed 100000000."
    with patch(
        "views.treasury.menu.treasury_service.contribute",
        AsyncMock(return_value=result),
    ) as contribute:
        await modal.on_submit(interaction)
    contribute.assert_awaited_once_with(55, 7, 100000000)
    modal._panel._redraw.assert_awaited_once_with(interaction, "Contributed 100000000.")
    # success path never sends its own ephemeral — the redraw is the feedback
    interaction.response.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_whitespace_is_stripped_before_parse():
    modal = _modal("  42  ")
    interaction = _interaction()
    with patch(
        "views.treasury.menu.treasury_service.contribute",
        AsyncMock(return_value=MagicMock(message="ok")),
    ) as contribute:
        await modal.on_submit(interaction)
    contribute.assert_awaited_once_with(55, 7, 42)

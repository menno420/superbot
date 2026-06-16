"""Regression — the 1v1 ``_ChallengeView`` 30s timer must stop on accept/decline.

Owner-reported via Hermes (2026-06-16): the deathmatch "challenge a player" view's
30-second timeout kept running after the challenge was accepted, so when it fired
it overwrote the live (or already-finished) duel message with
``"⚔️ Challenge Expired — did not respond in time"``.

Root cause: ``btn_accept``/``btn_decline`` never called ``self.stop()`` and
``on_timeout`` had no guard, so the stale challenge view lived on in the
background. Fix: accept/decline set ``_resolved`` + call ``self.stop()``, and
``on_timeout`` returns early when ``_resolved``. ``_DuelView`` was never the
problem (it guards on ``duel.is_over``).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


def _player(id_: int = 100, name: str = "Player") -> SimpleNamespace:
    return SimpleNamespace(id=id_, display_name=name, mention=f"<@{id_}>", bot=False)


def _challenge_view():
    from cogs.deathmatch_cog import _ChallengeView

    cog = MagicMock()
    cog.active_duels = {}
    challenger = _player(100, "Challenger")
    opponent = _player(200, "Opponent")
    ctx = MagicMock()
    ctx.guild = SimpleNamespace(id=1)
    view = _ChallengeView(cog, challenger, opponent, (1, 100, 200), ctx)
    view.message = AsyncMock()  # the original challenge message
    return view, cog, opponent


def _button(view: discord.ui.View, prefix: str) -> discord.ui.Button:
    return next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and (c.label or "").startswith(prefix)
    )


def _stub_interaction(user: SimpleNamespace) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = user
    interaction.guild_id = 0
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.original_response = AsyncMock(return_value=AsyncMock())
    return interaction


@pytest.mark.asyncio
async def test_decline_stops_view_and_guards_timeout():
    view, _cog, opponent = _challenge_view()

    await _button(view, "❌").callback(_stub_interaction(opponent))  # type: ignore[union-attr]

    assert view._resolved is True
    assert view.is_finished(), "decline must stop the view so the timeout is cancelled"

    # A timeout that races through anyway must NOT overwrite the declined message.
    view.message.reset_mock()
    await view.on_timeout()
    view.message.edit.assert_not_called()


@pytest.mark.asyncio
async def test_accept_stops_view_and_guards_timeout():
    view, cog, opponent = _challenge_view()

    from utils import equipment

    with (
        patch(
            "cogs.deathmatch_cog.db.get_equipment",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(
            "cogs.deathmatch_cog.equipment.compute_stats",
            return_value=equipment.EffectiveStats(),
        ),
        patch(
            "services.settings_resolution.resolve_value",
            new_callable=AsyncMock,
            return_value=60,
        ),
    ):
        await _button(view, "✅").callback(_stub_interaction(opponent))  # type: ignore[union-attr]

    assert view._resolved is True
    assert view.is_finished(), "accept must stop the view so the timeout is cancelled"
    assert view.duel_key in cog.active_duels, "accept registers the active duel"

    # The exact reported bug: the stale challenge timer must NOT clobber the
    # live duel message with an "expired" notice.
    view.message.reset_mock()
    await view.on_timeout()
    view.message.edit.assert_not_called()


@pytest.mark.asyncio
async def test_timeout_still_expires_when_unresolved():
    """No regression: an un-answered challenge still expires after 30s."""
    view, _cog, _opponent = _challenge_view()

    await view.on_timeout()

    view.message.edit.assert_called_once()
    embed = view.message.edit.call_args.kwargs["embed"]
    assert embed.title == "⚔️ Challenge Expired"

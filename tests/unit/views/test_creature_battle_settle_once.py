"""creature_battle challenge view — settle-once guard (completion cert #5, Q-0209).

The accept/decline buttons settle the challenge (resolve + record a battle, or close
it). ``SettleOnceMixin`` must give that transition one atomic claim so a double-click
on Accept can't resolve + record the battle twice. Discord I/O + the service mocked.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from views.creature_battle.challenge import CreatureBattleChallengeView


def _member(uid: int, name: str):
    return SimpleNamespace(id=uid, mention=f"<@{uid}>", display_name=name)


def _interaction():
    interaction = SimpleNamespace()
    interaction.response = SimpleNamespace(edit_message=AsyncMock())
    interaction.followup = SimpleNamespace(send=AsyncMock())
    interaction.message = SimpleNamespace(id=1)
    return interaction


def _view() -> CreatureBattleChallengeView:
    view = CreatureBattleChallengeView(_member(1, "Ada"), _member(2, "Bo"), 99)
    view.message = SimpleNamespace(edit=AsyncMock(), id=123)
    return view


@pytest.mark.asyncio
async def test_double_accept_resolves_the_battle_only_once():
    view = _view()
    with patch(
        "views.creature_battle.challenge.creature_battle_service"
    ) as svc:
        # None → "needs a creature" branch; keeps the test off the render path.
        svc.resolve_and_record_pvp = AsyncMock(return_value=None)
        await CreatureBattleChallengeView.accept(view, _interaction(), None)
        # A second click (e.g. a fast double-tap) must short-circuit.
        await CreatureBattleChallengeView.accept(view, _interaction(), None)
    svc.resolve_and_record_pvp.assert_awaited_once()


@pytest.mark.asyncio
async def test_accept_then_decline_settles_once():
    view = _view()
    with patch(
        "views.creature_battle.challenge.creature_battle_service"
    ) as svc:
        svc.resolve_and_record_pvp = AsyncMock(return_value=None)
        await CreatureBattleChallengeView.accept(view, _interaction(), None)
        decline_interaction = _interaction()
        await CreatureBattleChallengeView.decline(view, decline_interaction, None)
    # The decline lost the claim race → it must not edit the message.
    decline_interaction.response.edit_message.assert_not_awaited()

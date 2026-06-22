"""fishing cast minigame view — reel resolution + lifecycle (owner design Q-0175).

Pins the ``cast → wait → BITE → reel`` contract that the design sim recommends
and the owner ratified (2026-06-22): reel before the bite or too late = the fish
gets away (no write); reel within the window = the catch is committed. Discord
timing is driven directly (no real sleeps); the writes are mocked.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow
from utils.fishing.fish import Catch, FishSpecies
from views.fishing import active_casts
from views.fishing.cast_view import FishingCastView

_SPECIES = FishSpecies("trout", 8, "🐠")
_CAST = fishing_workflow.Cast(catch=Catch(species=_SPECIES), level_before=3)


def _interaction(user_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.message = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _make_view() -> FishingCastView:
    view = FishingCastView(user_id=1, guild_id=99, cast=_CAST)
    view.message = MagicMock()
    return view


def _reel(view: FishingCastView, interaction: MagicMock):
    # @discord.ui.button stores the original coroutine on the class; call it
    # with self=view explicitly (mirrors the blackjack view tests).
    return type(view).reel_btn(view, interaction, MagicMock())


@pytest.fixture(autouse=True)
def _clear_active():
    active_casts.clear()
    yield
    active_casts.clear()


@pytest.mark.asyncio
async def test_reel_before_bite_spooks_the_fish_and_never_writes():
    view = _make_view()
    active_casts.add((1, 99))  # start() would have added this
    interaction = _interaction()
    assert view._armed is False

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()  # premature → the fish got away, no catch
    assert view._resolved is True
    assert (1, 99) not in active_casts  # guard released


@pytest.mark.asyncio
async def test_reel_within_window_commits_the_catch():
    view = _make_view()
    active_casts.add((1, 99))
    view._armed = True
    view._bite_at = time.monotonic()  # elapsed ≈ 0 → comfortably in time
    interaction = _interaction()

    result = fishing_workflow.FishResult(
        catch=_CAST.catch,
        fishing_level=3,
        unlocked_bigger=False,
    )
    with (
        patch.object(
            fishing_workflow,
            "commit_catch",
            AsyncMock(return_value=result),
        ) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)) as edit,
    ):
        await _reel(view, interaction)

    commit.assert_awaited_once_with(1, 99, _CAST)  # the rolled cast is committed
    edit.assert_awaited()  # the success embed is rendered
    assert view._resolved is True
    assert (1, 99) not in active_casts


@pytest.mark.asyncio
async def test_reel_too_late_lets_the_fish_get_away():
    view = _make_view()
    active_casts.add((1, 99))
    view._armed = True
    # Bite happened well past the window → too slow.
    view._bite_at = time.monotonic() - 99.0
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()  # missed the window → no catch
    assert view._resolved is True
    assert (1, 99) not in active_casts


@pytest.mark.asyncio
async def test_a_second_reel_after_resolution_is_a_noop():
    view = _make_view()
    view._resolved = True
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_only_the_caster_can_reel():
    view = _make_view()
    intruder = _interaction(user_id=2)

    allowed = await view.interaction_check(intruder)

    assert allowed is False
    intruder.response.send_message.assert_awaited_once()

"""fishing cast minigame view — reel resolution, trophy reel-fight, lifecycle.

Pins the ``cast → wait → BITE → reel`` contract the design sim recommends and the
owner ratified (2026-06-22): reel before the bite or too late = the fish gets away
(no write); an *ordinary* fish lands on the first reel; a *trophy* hooks into a
reel-fight (extra timed taps, each able to snap free) and only commits once every
tap lands. Discord timing is driven directly (no real sleeps / no real background
tasks); the writes are mocked.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow
from utils.fishing.fish import Catch, FishSpecies
from views.fishing import active_casts
from views.fishing.cast_view import _PHASE_FIGHT, FishingCastView

# An *ordinary* fish: size 2, far below the level-7 trophy threshold (cap 21).
_ORDINARY = fishing_workflow.Cast(
    catch=Catch(species=FishSpecies("minnow", 2, "🐟")),
    level_before=7,
)
# A *trophy*: size 8 at level 3 (cap 9, threshold 6) → 3-tap reel-fight.
_TROPHY = fishing_workflow.Cast(
    catch=Catch(species=FishSpecies("trout", 8, "🐠")),
    level_before=3,
)


def _interaction(user_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.message = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _make_view(cast: fishing_workflow.Cast = _ORDINARY) -> FishingCastView:
    view = FishingCastView(user_id=1, guild_id=99, cast=cast)
    view.message = MagicMock()
    return view


def _reel(view: FishingCastView, interaction: MagicMock):
    # @discord.ui.button stores the original coroutine on the class; call it with
    # self=view explicitly (mirrors the blackjack view tests).
    return type(view).reel_btn(view, interaction, MagicMock())


def _spawn_stub() -> MagicMock:
    """A ``tasks.spawn`` stand-in that closes the coroutine it's handed (the real
    spawn would schedule it) so no 'coroutine never awaited' warning leaks."""

    def _consume(name, coro, **_):  # noqa: ANN001
        coro.close()

    return MagicMock(side_effect=_consume)


def _arm(view: FishingCastView) -> None:
    view._armed = True
    view._armed_at = time.monotonic()  # elapsed ≈ 0 → comfortably in time


@pytest.fixture(autouse=True)
def _clear_active():
    active_casts.clear()
    yield
    active_casts.clear()


# ---------------------------------------------------------------------------
# Bite phase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reel_before_bite_spooks_the_fish_and_never_writes():
    view = _make_view()
    active_casts.add((1, 99))
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
async def test_ordinary_fish_commits_on_the_first_reel():
    view = _make_view(_ORDINARY)
    active_casts.add((1, 99))
    _arm(view)
    interaction = _interaction()

    result = fishing_workflow.FishResult(
        catch=_ORDINARY.catch,
        fishing_level=7,
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

    commit.assert_awaited_once_with(1, 99, _ORDINARY)
    edit.assert_awaited()
    assert view._resolved is True
    assert (1, 99) not in active_casts


@pytest.mark.asyncio
async def test_reel_too_late_lets_the_fish_get_away():
    view = _make_view()
    active_casts.add((1, 99))
    view._armed = True
    view._armed_at = time.monotonic() - 99.0  # bite well past the window
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()
    assert view._resolved is True
    assert (1, 99) not in active_casts


# ---------------------------------------------------------------------------
# Trophy reel-fight
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trophy_hook_starts_the_fight_without_committing():
    view = _make_view(_TROPHY)
    active_casts.add((1, 99))
    _arm(view)
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.tasks.spawn", _spawn_stub()) as spawn,
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()  # the trophy isn't landed until the fight ends
    assert view._phase == _PHASE_FIGHT
    assert view._taps_total == 3 and view._taps_left == 3
    spawn.assert_called_once()  # a fight round was scheduled
    assert view._resolved is False
    assert (1, 99) in active_casts  # still fighting → guard held


@pytest.mark.asyncio
async def test_landing_the_final_fight_tap_commits_the_trophy():
    view = _make_view(_TROPHY)
    active_casts.add((1, 99))
    view._phase = _PHASE_FIGHT
    view._taps_total = 3
    view._taps_left = 1  # the last tap
    _arm(view)
    interaction = _interaction()

    result = fishing_workflow.FishResult(
        catch=_TROPHY.catch,
        fishing_level=3,
        unlocked_bigger=False,
    )
    with (
        patch.object(
            fishing_workflow,
            "commit_catch",
            AsyncMock(return_value=result),
        ) as commit,
        patch("views.fishing.cast_view.minigame.roll_escape", return_value=False),
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
    ):
        await _reel(view, interaction)

    commit.assert_awaited_once_with(1, 99, _TROPHY)
    assert view._resolved is True
    assert (1, 99) not in active_casts


@pytest.mark.asyncio
async def test_a_non_final_fight_tap_advances_without_committing():
    view = _make_view(_TROPHY)
    active_casts.add((1, 99))
    view._phase = _PHASE_FIGHT
    view._taps_total = 3
    view._taps_left = 3
    _arm(view)
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.minigame.roll_escape", return_value=False),
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.tasks.spawn", _spawn_stub()) as spawn,
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()
    assert view._taps_left == 2  # one tap landed
    spawn.assert_called_once()  # next round scheduled
    assert view._resolved is False


@pytest.mark.asyncio
async def test_a_snapped_line_loses_the_trophy():
    view = _make_view(_TROPHY)
    active_casts.add((1, 99))
    view._phase = _PHASE_FIGHT
    view._taps_total = 3
    view._taps_left = 2
    _arm(view)
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.minigame.roll_escape", return_value=True),
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()  # it snapped free → no catch
    assert view._resolved is True
    assert (1, 99) not in active_casts


@pytest.mark.asyncio
async def test_extra_taps_between_fight_rounds_are_ignored():
    view = _make_view(_TROPHY)
    view._phase = _PHASE_FIGHT
    view._armed = False  # between rounds — no window open
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)) as defer,
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()
    defer.assert_awaited()  # the mash is swallowed, not a terminal
    assert view._resolved is False


# ---------------------------------------------------------------------------
# Lifecycle guards
# ---------------------------------------------------------------------------


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


def test_a_better_rod_widens_the_reaction_window():
    from utils.fishing import rods

    starter_view = FishingCastView(1, 99, _ORDINARY, rod=rods.STARTER)
    diamond_view = FishingCastView(1, 99, _ORDINARY, rod=rods.rod_for_tier(4))

    # the rod's window_bonus is added to every reaction window (the fairness knob)
    assert starter_view._window == minigame_window()
    assert diamond_view._window > starter_view._window


def minigame_window():
    from utils.fishing import minigame

    return minigame.REACTION_WINDOW


# ---------------------------------------------------------------------------
# prepare_cast — the shared cast-launch helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_prepare_cast_blocks_a_second_concurrent_cast():
    from views.fishing.cast_view import prepare_cast

    active_casts.add((1, 99))
    result = await prepare_cast(1, 99)
    assert isinstance(result, str)  # busy → a player-facing message, not a view


@pytest.mark.asyncio
async def test_prepare_cast_returns_an_embed_and_view_on_success():
    from views.fishing.cast_view import prepare_cast

    with (
        patch("views.fishing.cast_view.fishing_workflow.get_rod", AsyncMock()),
        patch(
            "views.fishing.cast_view.fishing_workflow.roll_cast",
            AsyncMock(return_value=_ORDINARY),
        ),
    ):
        result = await prepare_cast(1, 99)

    assert not isinstance(result, str)
    embed, view = result
    assert isinstance(view, FishingCastView)


@pytest.mark.asyncio
async def test_prepare_cast_reports_an_empty_catalog():
    from views.fishing.cast_view import prepare_cast

    empty = fishing_workflow.Cast(catch=None, level_before=1)
    with (
        patch("views.fishing.cast_view.fishing_workflow.get_rod", AsyncMock()),
        patch(
            "views.fishing.cast_view.fishing_workflow.roll_cast",
            AsyncMock(return_value=empty),
        ),
    ):
        result = await prepare_cast(1, 99)

    assert isinstance(result, str)  # honest "unavailable" message

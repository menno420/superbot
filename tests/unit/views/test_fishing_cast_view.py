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
from utils.fishing import minigame, rods
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
async def test_premature_reel_is_forgiven_once_by_the_rods_grace():
    # a rod with full premature_grace forgives the first early reel: the cast
    # survives (not resolved, guard still held) so the real bite can still come.
    view = FishingCastView(
        user_id=1,
        guild_id=99,
        cast=_ORDINARY,
        rod=rods.rod_for_tier(4),  # diamond — best grace
    )
    view.message = MagicMock()
    view.message.edit = AsyncMock()  # the "steadies it" anchor edit
    active_casts.add((1, 99))
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch.object(minigame, "roll_premature_grace", return_value=True),
    ):
        await _reel(view, interaction)

    commit.assert_not_awaited()
    view.message.edit.assert_awaited()  # showed the reassuring "still in the water"
    assert view._grace_used is True
    assert view._resolved is False  # the line is still in the water
    assert (1, 99) in active_casts  # cast not torn down


@pytest.mark.asyncio
async def test_grace_is_spent_once_a_second_early_reel_spooks_the_fish():
    view = FishingCastView(
        user_id=1,
        guild_id=99,
        cast=_ORDINARY,
        rod=rods.rod_for_tier(4),
    )
    view.message = MagicMock()
    view._grace_used = True  # already forgiven once this cast
    active_casts.add((1, 99))
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()) as commit,
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
        # grace should NOT even be rolled when already used; assert by never patching
        # it to True — if it were rolled the bare default would still spook anyway.
        patch.object(minigame, "roll_premature_grace", return_value=True) as grace,
    ):
        await _reel(view, interaction)

    grace.assert_not_called()  # the flag short-circuits before the roll
    commit.assert_not_awaited()
    assert view._resolved is True  # spooked for good
    assert (1, 99) not in active_casts


@pytest.mark.asyncio
async def test_bare_rod_never_forgives_a_premature_reel():
    # the default _make_view uses the bare rod (grace 0); an early reel always spooks
    view = _make_view()
    active_casts.add((1, 99))
    interaction = _interaction()

    with (
        patch.object(fishing_workflow, "commit_catch", AsyncMock()),
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch("views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)),
    ):
        await _reel(view, interaction)

    assert view._grace_used is False  # nothing to spend
    assert view._resolved is True  # spooked


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
        patch(
            "views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)
        ) as edit,
    ):
        await _reel(view, interaction)

    commit.assert_awaited_once_with(1, 99, _ORDINARY)
    edit.assert_awaited()
    assert view._resolved is True
    assert (1, 99) not in active_casts


@pytest.mark.asyncio
async def test_caught_embed_shows_weight_and_personal_best():
    view = _make_view(_ORDINARY)
    active_casts.add((1, 99))
    _arm(view)
    interaction = _interaction()

    result = fishing_workflow.FishResult(
        catch=_ORDINARY.catch,
        fishing_level=7,
        unlocked_bigger=False,
        weight=3.7,
        new_personal_best=True,
    )
    with (
        patch.object(
            fishing_workflow,
            "commit_catch",
            AsyncMock(return_value=result),
        ),
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch(
            "views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)
        ) as edit,
    ):
        await _reel(view, interaction)

    # The catch embed reports the weight and celebrates the new record.
    _, kwargs = edit.await_args
    desc = kwargs["embed"].description
    assert "3.7 kg" in desc
    assert "personal best" in desc.lower()


@pytest.mark.asyncio
async def test_caught_embed_announces_a_lucky_double_catch():
    view = _make_view(_ORDINARY)
    active_casts.add((1, 99))
    _arm(view)
    interaction = _interaction()

    result = fishing_workflow.FishResult(
        catch=_ORDINARY.catch,
        fishing_level=7,
        unlocked_bigger=False,
        weight=1.2,
        bonus_catch=True,
    )
    with (
        patch.object(
            fishing_workflow,
            "commit_catch",
            AsyncMock(return_value=result),
        ),
        patch("views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)),
        patch(
            "views.fishing.cast_view.safe_edit", AsyncMock(return_value=True)
        ) as edit,
    ):
        await _reel(view, interaction)

    _, kwargs = edit.await_args
    desc = kwargs["embed"].description
    assert "double catch" in desc.lower()


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


def test_got_away_appends_a_clue_for_a_trophy_but_not_an_ordinary_fish():
    base = "🌊 *...the fish got away.*"
    # A trophy that escapes leaves a teasing, species-named clue (soft-fail UX).
    trophy_text = _make_view(_TROPHY)._got_away(base)
    assert base in trophy_text
    assert "Trout" in trophy_text
    # An ordinary fish keeps the plain line — no story for a lost minnow.
    assert _make_view(_ORDINARY)._got_away(base) == base


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
        patch(
            "views.fishing.cast_view.safe_defer", AsyncMock(return_value=True)
        ) as defer,
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
# Bite-speed knob — the bait/rod compounded pacing threaded into the view
# ---------------------------------------------------------------------------


def test_view_bite_speed_defaults_to_the_rod_when_unset():
    # The direct !fish/test path passes no bite_speed → falls back to the rod's.
    diamond = rods.rod_for_tier(4)
    view = FishingCastView(1, 99, _ORDINARY, rod=diamond)
    assert view._bite_speed == diamond.bite_speed


def test_view_bite_speed_takes_the_threaded_value_over_the_rod():
    view = FishingCastView(1, 99, _ORDINARY, rod=rods.STARTER, bite_speed=0.42)
    assert view._bite_speed == 0.42  # the compounded rod×bait value from begin_cast


@pytest.mark.asyncio
async def test_run_bite_paces_on_the_threaded_bite_speed():
    view = FishingCastView(1, 99, _ORDINARY, rod=rods.STARTER, bite_speed=0.5)
    view.message = MagicMock()
    view._resolved = True  # return right after the first sleep, before arming
    seen: dict[str, float] = {}

    def _delay(rng=None, *, speed=1.0, lo=0.0, hi=0.0, floor=0.0):  # noqa: ANN001
        seen["speed"] = speed
        return 0.0

    with (
        patch("views.fishing.cast_view.minigame.roll_bite_delay", _delay),
        patch("views.fishing.cast_view.minigame.roll_fakeout", return_value=False),
        patch("views.fishing.cast_view.asyncio.sleep", AsyncMock()),
    ):
        await view._run_bite()

    assert seen["speed"] == 0.5  # the bite wait uses the compounded speed, not the rod


@pytest.mark.asyncio
async def test_prepare_cast_threads_effective_bite_speed_into_the_view():
    from views.fishing.cast_view import prepare_cast

    start = fishing_workflow.CastStart(
        ok=True,
        cast=_ORDINARY,
        rod=rods.STARTER,
        energy_current=9,
        effective_bite_speed=0.36,
    )
    with patch(
        "views.fishing.cast_view.fishing_workflow.begin_cast",
        AsyncMock(return_value=start),
    ):
        result = await prepare_cast(1, 99)

    assert not isinstance(result, str)
    _, view = result
    assert view._bite_speed == 0.36


@pytest.mark.asyncio
async def test_prepare_cast_shows_a_fishing_gear_footer_note_when_geared():
    from views.fishing.cast_view import prepare_cast

    start = fishing_workflow.CastStart(
        ok=True,
        cast=_ORDINARY,
        rod=rods.STARTER,
        energy_current=9,
        fishing_gear_bonus=True,
    )
    with patch(
        "views.fishing.cast_view.fishing_workflow.begin_cast",
        AsyncMock(return_value=start),
    ):
        embed, _ = await prepare_cast(1, 99)
    assert "fishing gear" in (embed.footer.text or "")


@pytest.mark.asyncio
async def test_prepare_cast_omits_the_gear_note_without_fishing_gear():
    from views.fishing.cast_view import prepare_cast

    start = fishing_workflow.CastStart(
        ok=True, cast=_ORDINARY, rod=rods.STARTER, energy_current=9
    )
    with patch(
        "views.fishing.cast_view.fishing_workflow.begin_cast",
        AsyncMock(return_value=start),
    ):
        embed, _ = await prepare_cast(1, 99)
    assert "fishing gear" not in (embed.footer.text or "")


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

    start = fishing_workflow.CastStart(
        ok=True, cast=_ORDINARY, rod=rods.STARTER, energy_current=9
    )
    with patch(
        "views.fishing.cast_view.fishing_workflow.begin_cast",
        AsyncMock(return_value=start),
    ):
        result = await prepare_cast(1, 99)

    assert not isinstance(result, str)
    embed, view = result
    assert isinstance(view, FishingCastView)


@pytest.mark.asyncio
async def test_prepare_cast_reports_an_empty_catalog():
    from views.fishing.cast_view import prepare_cast

    start = fishing_workflow.CastStart(ok=False, message="🎣 unavailable")
    with patch(
        "views.fishing.cast_view.fishing_workflow.begin_cast",
        AsyncMock(return_value=start),
    ):
        result = await prepare_cast(1, 99)

    assert isinstance(result, str)  # honest failure message


# ---------------------------------------------------------------------------
# Venue threading (Q-0175 §5) — the deepwater profile drives the view's tuning
# ---------------------------------------------------------------------------


def test_deepwater_profile_widens_the_window_and_raises_base_escape():
    from utils.fishing import minigame
    from utils.fishing import venue as venue_mod

    deep_cast = fishing_workflow.Cast(
        catch=Catch(species=FishSpecies("colossal squid", 20, "🦑", venue="deepwater")),
        level_before=7,
        venue="deepwater",
    )
    view = FishingCastView(
        1,
        99,
        deep_cast,
        rod=rods.STARTER,
        profile=venue_mod.DEEPWATER_PROFILE,
    )
    # The base window is the venue's (deepwater) + the rod bonus (starter = 0).
    assert view._window == venue_mod.DEEPWATER_PROFILE.reaction_window
    # A deepwater fight uses the deepwater base escape, far above shore's.
    species = deep_cast.catch.species
    deep_chance = minigame.fight_escape_chance(
        species,
        base_escape=venue_mod.DEEPWATER_PROFILE.base_escape,
    )
    shore_chance = minigame.fight_escape_chance(species)
    assert deep_chance > shore_chance


def test_view_falls_back_to_the_casts_venue_profile_when_unset():
    from utils.fishing import venue as venue_mod

    deep_cast = fishing_workflow.Cast(
        catch=Catch(species=FishSpecies("oarfish", 14, "🎏", venue="deepwater")),
        level_before=7,
        venue="deepwater",
    )
    view = FishingCastView(1, 99, deep_cast, rod=rods.STARTER)  # no profile passed
    assert view._profile is venue_mod.DEEPWATER_PROFILE

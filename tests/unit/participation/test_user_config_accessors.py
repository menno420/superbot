"""Phase 2c PR-8 — utils.user_config_accessors typed accessors.

Each accessor:
* Reads through ``core.runtime.user_config`` (so the cache layer is
  exercised).
* Returns a typed value (ParticipationState / bool / PreferenceResult
  / VisibilityState).
* Returns the documented default when no row exists.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.runtime import user_config
from utils.user_config_accessors import (
    ParticipationState,
    PreferenceResult,
    VisibilityState,
    get_participation,
    get_preference,
    get_visibility,
    is_subscribed,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    user_config._reset_for_tests()
    yield
    user_config._reset_for_tests()


def _bundle(**kwargs):
    base = {
        "participation": [],
        "subscriptions": [],
        "preferences": [],
        "visibility_overrides": [],
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# get_participation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_participation_returns_not_set_when_no_row():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(),
    ):
        result = await get_participation(1, 2, "xp")
    assert result is ParticipationState.NOT_SET


@pytest.mark.asyncio
async def test_get_participation_returns_opted_in():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(
            participation=[{"subsystem": "xp", "state": "opted_in"}],
        ),
    ):
        result = await get_participation(1, 2, "xp")
    assert result is ParticipationState.OPTED_IN


@pytest.mark.asyncio
async def test_get_participation_returns_opted_out():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(
            participation=[{"subsystem": "xp", "state": "opted_out"}],
        ),
    ):
        result = await get_participation(1, 2, "xp")
    assert result is ParticipationState.OPTED_OUT


@pytest.mark.asyncio
async def test_get_participation_subsystem_isolation():
    """Participation in ``economy`` is separate from ``xp``."""
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(
            participation=[{"subsystem": "economy", "state": "opted_in"}],
        ),
    ):
        result = await get_participation(1, 2, "xp")
    assert result is ParticipationState.NOT_SET


# ---------------------------------------------------------------------------
# is_subscribed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_subscribed_returns_default_when_no_row():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(),
    ):
        result = await is_subscribed(1, 2, "economy", "daily", default=True)
    assert result is True


@pytest.mark.asyncio
async def test_is_subscribed_returns_stored_value():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(
            subscriptions=[
                {"subsystem": "economy", "topic": "daily", "enabled": False},
            ],
        ),
    ):
        result = await is_subscribed(1, 2, "economy", "daily", default=True)
    assert result is False


# ---------------------------------------------------------------------------
# get_preference
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_preference_returns_default_when_missing():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(),
    ):
        result = await get_preference(1, 2, "digest_freq", default="hourly")
    assert isinstance(result, PreferenceResult)
    assert result.value == "hourly"
    assert result.found is False


@pytest.mark.asyncio
async def test_get_preference_returns_stored_value():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(
            preferences=[
                {"key": "digest_freq", "value": {"unit": "hours", "interval": 6}},
            ],
        ),
    ):
        result = await get_preference(1, 2, "digest_freq", default="hourly")
    assert result.value == {"unit": "hours", "interval": 6}
    assert result.found is True


# ---------------------------------------------------------------------------
# get_visibility
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_visibility_returns_default_when_missing():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(),
    ):
        result = await get_visibility(1, 2, "xp")
    assert result is VisibilityState.DEFAULT


@pytest.mark.asyncio
async def test_get_visibility_returns_public_or_hidden():
    with patch(
        "utils.db.user_participation.list_for_user",
        new_callable=AsyncMock,
        return_value=_bundle(
            visibility_overrides=[
                {"subsystem": "xp", "visibility": "hidden"},
            ],
        ),
    ):
        result = await get_visibility(1, 2, "xp")
    assert result is VisibilityState.HIDDEN

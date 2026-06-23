"""utils.fishing.weather — the date-seeded daily fishing bias (owner "Other ideas")."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone

from utils.fishing import weather


def test_weather_is_deterministic_for_a_date():
    d = date(2026, 6, 23)
    assert weather.weather_for_date(d) is weather.weather_for_date(d)


def test_different_dates_can_yield_different_weather():
    # Across a month at least two distinct conditions appear (not a constant).
    seen = {weather.weather_for_date(date(2026, 6, day)).key for day in range(1, 29)}
    assert len(seen) >= 2


def test_every_condition_is_reachable_over_a_long_horizon():
    seen = {
        weather.weather_for_date(date.fromordinal(o)).key
        for o in range(739000, 739000 + 365 * 3)  # ~3 years
    }
    assert seen == {c.key for c in weather.CONDITIONS}


def test_distribution_roughly_tracks_the_weights():
    # Clear is the most common day; storm is the rarest — the weighted pick holds.
    counts = Counter(
        weather.weather_for_date(date.fromordinal(o)).key
        for o in range(739000, 739000 + 365 * 5)  # 5 years of days
    )
    assert counts["clear"] > counts["rain"] > counts["storm"]
    # Storm should be genuinely rare (its weight is 8/100).
    total = sum(counts.values())
    assert counts["storm"] / total < 0.15


def test_current_weather_uses_the_injected_now():
    moment = datetime(2026, 6, 23, 14, 30, tzinfo=timezone.utc)
    assert weather.current_weather(moment) is weather.weather_for_date(date(2026, 6, 23))


def test_weights_sum_to_one_hundred_and_clear_dominates():
    assert sum(c.weight for c in weather.CONDITIONS) == 100
    clear = next(c for c in weather.CONDITIONS if c.key == "clear")
    assert clear.weight == max(c.weight for c in weather.CONDITIONS)


def test_multipliers_are_in_sane_ranges():
    for c in weather.CONDITIONS:
        # bite speed within ±20%, rarity never below neutral, both finite.
        assert 0.8 <= c.bite_speed_mult <= 1.2
        assert c.rarity_mult >= 1.0
        assert c.rarity_mult <= 1.4


def test_clear_is_a_true_no_op():
    clear = next(c for c in weather.CONDITIONS if c.key == "clear")
    assert clear.bite_speed_mult == 1.0
    assert clear.rarity_mult == 1.0
    assert weather.effect_text(clear) == "no effect — a fair, ordinary day"


def test_storm_is_the_high_risk_high_reward_day():
    storm = next(c for c in weather.CONDITIONS if c.key == "storm")
    assert storm.rarity_mult > 1.0  # the rare fish run
    assert storm.bite_speed_mult > 1.0  # ...but the bites are slower
    assert "rarer fish" in weather.effect_text(storm)
    assert "slower bites" in weather.effect_text(storm)


def test_effect_text_names_only_the_knobs_that_move():
    rain = next(c for c in weather.CONDITIONS if c.key == "rain")  # faster bites only
    assert weather.effect_text(rain) == "faster bites"

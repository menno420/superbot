"""utils.fishing.venue — the shore vs deepwater venue model (owner Q-0175 §5)."""

from __future__ import annotations

from utils.fishing import fish, minigame, venue


def test_two_known_venues_with_distinct_profiles():
    assert venue.SHORE_PROFILE.key == venue.SHORE
    assert venue.DEEPWATER_PROFILE.key == venue.DEEPWATER
    assert venue.SHORE_PROFILE is not venue.DEEPWATER_PROFILE


def test_shore_profile_reuses_the_tuned_minigame_constants():
    # One source of truth for shore — the profile must not drift from minigame.py.
    p = venue.SHORE_PROFILE
    assert p.bite_delay_min == minigame.BITE_DELAY_MIN
    assert p.bite_delay_max == minigame.BITE_DELAY_MAX
    assert p.bite_delay_floor == minigame.BITE_DELAY_FLOOR
    assert p.reaction_window == minigame.REACTION_WINDOW
    assert p.base_escape == minigame.SHORE_ESCAPE_CHANCE


def test_deepwater_is_tougher_than_shore():
    shore, deep = venue.SHORE_PROFILE, venue.DEEPWATER_PROFILE
    # The deep bites slower and fights free far more often — that is what makes a
    # good rod's escape-resist pay off (the sim §5 "optimization, not a gate").
    assert deep.bite_delay_min > shore.bite_delay_min
    assert deep.bite_delay_max > shore.bite_delay_max
    assert deep.bite_delay_floor > shore.bite_delay_floor
    assert deep.base_escape > shore.base_escape


def test_normalize_coerces_unknown_to_shore():
    assert venue.normalize(None) == venue.SHORE
    assert venue.normalize("") == venue.SHORE
    assert venue.normalize("nonsense") == venue.SHORE
    assert venue.normalize("  DEEPWATER ") == venue.DEEPWATER
    assert venue.normalize("Shore") == venue.SHORE


def test_profile_for_returns_the_matching_profile():
    assert venue.profile_for("deepwater") is venue.DEEPWATER_PROFILE
    assert venue.profile_for("shore") is venue.SHORE_PROFILE
    assert venue.profile_for("garbage") is venue.SHORE_PROFILE


def test_toggle_flips_between_the_two_venues():
    assert venue.toggle(venue.SHORE) == venue.DEEPWATER
    assert venue.toggle(venue.DEEPWATER) == venue.SHORE
    assert venue.toggle(None) == venue.DEEPWATER  # unknown reads as shore → flips out


def test_each_venue_profile_points_at_a_non_empty_species_pool():
    for profile in (venue.SHORE_PROFILE, venue.DEEPWATER_PROFILE):
        pool = fish.species_for_venue(profile.species_venue)
        assert pool, f"{profile.key} has no fish"
        assert all(s.venue == profile.species_venue for s in pool)

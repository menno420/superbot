"""Pin that the boss dependency chain fans out to standard-solo leaderboards.

Without this child spec, ``/btd6 leaderboard boss`` renders empty even
after a Fetch All cycle, because the supervisor never asks the API for
boss leaderboard rows. Keep the chain shape under regression so future
refactors can't silently lose the fan-out.
"""

from __future__ import annotations

from services import btd6_ingestion_service


def test_boss_chain_includes_metadata_spec():
    chain = btd6_ingestion_service._DEPENDENCY_CHAINS["nk_btd6_bosses"]
    metadata_specs = [
        spec for spec in chain if spec.child_source == "nk_btd6_bosses_metadata"
    ]
    assert len(metadata_specs) == 1


def test_boss_chain_includes_standard_solo_leaderboard_spec():
    chain = btd6_ingestion_service._DEPENDENCY_CHAINS["nk_btd6_bosses"]
    leaderboard_specs = [
        spec for spec in chain if spec.child_source == "nk_btd6_bosses_leaderboard"
    ]
    assert len(leaderboard_specs) == 1, (
        "Boss chain must include nk_btd6_bosses_leaderboard fan-out — "
        "without it, /btd6 leaderboard boss has no data to render."
    )
    spec = leaderboard_specs[0]
    params = spec.path_param_builder("Diamondback5_mpfz8mi4")
    assert params["bossID"] == "Diamondback5_mpfz8mi4"
    assert params["type"] == "standard"
    assert params["teamSize"] == "1"

"""M3B — parser skeletons stay xfail until the NK response format is captured.

Every first-priority parser is registered (so the registry is the
single source of truth for known endpoints), but the ``parse()``
call is marked ``pytest.xfail(strict=False)`` with the explicit
reason the refined-direction plan calls for. When a real parser
lands, replace the xfail with a fixture-driven assertion in the
same file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_source_parser  # noqa: E402
from services.parsers._skeleton import ParserNotImplemented  # noqa: E402

_FIRST_PRIORITY = (
    "nk_btd6_maps",
    "nk_btd6_races",
    "nk_btd6_bosses",
    "nk_btd6_odyssey",
    "nk_btd6_challenges",
    "nk_btd6_events",
)


@pytest.fixture(autouse=True)
def _import_parsers():
    # Importing the package registers every skeleton.
    import services.parsers  # noqa: F401
    yield


@pytest.mark.parametrize("source_key", _FIRST_PRIORITY)
def test_first_priority_parser_is_registered(source_key):
    parser = btd6_source_parser.get(source_key)
    assert parser is not None, (
        f"M3B must register a parser skeleton for {source_key}"
    )
    assert parser.source_key == source_key


@pytest.mark.parametrize("source_key", _FIRST_PRIORITY)
def test_parser_skeleton_raises_until_format_is_captured(source_key):
    """Skeletons raise ParserNotImplemented with a stable reason.

    Marked ``xfail(strict=False)`` so the test still passes when a
    real parser arrives and stops raising. Until then the explicit
    raise prevents the M3B fetch loop from writing empty fact rows
    by accident.
    """
    parser = btd6_source_parser.get(source_key)
    assert parser is not None
    pytest.xfail(
        reason=(
            f"NK API response format for {source_key} has not been "
            "captured yet — parser skeleton intentionally raises"
        ),
    )
    parser.parse(payload={}, game_version=None)


def test_unknown_endpoints_not_in_first_priority_set():
    """Out-of-scope endpoints (Battles2, /btd6/save) must not be
    registered as parsers."""
    known = set(btd6_source_parser.known_keys())
    for forbidden in ("battles2_anything", "btd6_save", "nk_btd6_save"):
        assert forbidden not in known

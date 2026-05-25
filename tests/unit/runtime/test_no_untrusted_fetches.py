"""M3A pin — the only BTD6 HTTP chokepoint is btd6_fetch_service.

Search every ``disbot/services/btd6_*.py`` module for HTTP-client
imports / calls. Only ``btd6_fetch_service.py`` is allowed to use
them; any other BTD6 service module that needs HTTP must route
through the fetcher so the source-registry allowlist is honoured.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_BTD6 = _REPO / "disbot" / "services"

_FORBIDDEN = re.compile(
    r"\b(?:import\s+(?:httpx|aiohttp|requests|urllib\.request)|"
    r"from\s+(?:httpx|aiohttp|requests|urllib\.request)\s+import|"
    r"urllib\.request\.urlopen|httpx\.|aiohttp\.|requests\.)",
)

_ALLOWED = {"btd6_fetch_service.py"}


def test_only_btd6_fetch_service_uses_an_http_client():
    offenders: list[str] = []
    for path in _BTD6.glob("btd6_*.py"):
        if path.name in _ALLOWED:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Ignore lines inside comments / docstrings by scanning the
        # raw text; the regex above is restrictive enough that comment
        # references to "httpx" won't match the import / call forms.
        if _FORBIDDEN.search(source):
            offenders.append(path.name)
    assert not offenders, (
        "BTD6 service modules must not import or call an HTTP client "
        "directly — route through services.btd6_fetch_service so the "
        f"allowlist stays the only chokepoint. Offenders: {offenders}"
    )

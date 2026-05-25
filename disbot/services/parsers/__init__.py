"""BTD6 source-parser package (M3B).

One module per first-priority NK API endpoint. Each parser exposes a
``Parser`` instance that satisfies :class:`services.btd6_source_parser.BTD6Parser`
and registers itself via :func:`services.btd6_source_parser.register`.

M3B ships skeletons: the ``parse`` methods are stubs that raise so a
real fetch loop won't silently write empty fact rows. Implementations
land once the user confirms each endpoint's response format. Tests
mark the skeletons as ``pytest.xfail(strict=False)`` with explicit
reasons.
"""

from __future__ import annotations

from services.parsers import (  # noqa: F401 — register-on-import side effects
    ninjakiwi_bosses,
    ninjakiwi_challenges,
    ninjakiwi_events,
    ninjakiwi_maps,
    ninjakiwi_odyssey,
    ninjakiwi_races,
)

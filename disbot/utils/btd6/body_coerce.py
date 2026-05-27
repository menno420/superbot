"""Coerce ``body_json`` to a dict.

Promoted from duplicate definitions in ``cogs/btd6/_builders.py`` and
``services/btd6_live_query_service.py``. Per ``docs/helper-policy.md``,
a helper used by both ``services/`` and ``cogs/`` belongs in ``utils/``.
"""

from __future__ import annotations

import json
from typing import Any


def coerce_body(value: Any) -> dict[str, Any]:
    """Normalise ``body_json`` to a dict.

    Defensive shim for rows written by the legacy double-encoded
    ``json.dumps`` path: those round-trip as a JSON string instead of a
    dict, so we ``json.loads`` them on read. Returns ``{}`` for anything
    we can't decode (e.g. malformed text, non-mapping JSON).
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            return {}
        return decoded if isinstance(decoded, dict) else {}
    return {}


__all__ = ["coerce_body"]

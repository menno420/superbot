"""Parser protocol + registry for BTD6 sources (M3A seam).

M3A ships the Protocol so callers (the fetcher, the fact store,
tests) have a stable type; concrete parsers for the NK API land in
M3B once response formats are confirmed.

Parsers should:

* live under ``disbot/services/parsers/`` and import lazily.
* be registered by their owning module so the registry stays small.
* accept the raw fetch payload and return a list of normalised fact
  dicts that :func:`services.btd6_fact_store.store_facts` can write.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("bot.services.btd6_source_parser")


@runtime_checkable
class BTD6Parser(Protocol):
    """A parser converts one raw fetch payload into normalised facts.

    ``path_params`` carries the substituted URL placeholders that the
    fetcher used (e.g. ``{"raceID": "Reversed_Loop_mpbd7tcu"}``). Some
    NK endpoints — most notably race / boss / odyssey metadata — return
    a body whose ``id`` field is ``"n/a"``; for those endpoints the
    parser needs ``path_params`` to compose a stable ``entity_key``.
    Parsers whose body always carries the id may ignore the argument.
    """

    source_key: str

    def parse(
        self,
        payload: Any,
        *,
        game_version: str | None,
        path_params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]: ...


_REGISTRY: dict[str, BTD6Parser] = {}


def register(parser: BTD6Parser) -> None:
    if not getattr(parser, "source_key", None):
        raise ValueError("parser must declare a non-empty source_key")
    _REGISTRY[parser.source_key] = parser
    logger.debug("btd6 parser registered: %s", parser.source_key)


def get(source_key: str) -> BTD6Parser | None:
    return _REGISTRY.get(source_key)


def known_keys() -> list[str]:
    return sorted(_REGISTRY)


def _reset_for_tests() -> None:
    _REGISTRY.clear()


__all__ = ["BTD6Parser", "get", "known_keys", "register"]

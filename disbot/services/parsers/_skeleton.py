"""Shared parser-skeleton helper (M3B).

Each first-priority NK API parser is a thin wrapper around
:class:`NinjaKiwiParserSkeleton`. The skeleton raises a stable
:class:`ParserNotImplemented` until the response format is captured
so a real fetch loop cannot accidentally write empty fact rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ParserNotImplemented(NotImplementedError):
    """Raised by every M3B parser skeleton until the format is captured."""

    def __init__(self, source_key: str) -> None:
        super().__init__(
            f"parser for {source_key!r} is a skeleton — capture the NK API "
            "response format before enabling this source",
        )
        self.source_key = source_key


@dataclass(frozen=True)
class NinjaKiwiParserSkeleton:
    source_key: str

    def parse(
        self,
        payload: Any,
        *,
        game_version: str | None = None,
    ) -> list[dict[str, Any]]:
        raise ParserNotImplemented(self.source_key)


__all__ = ["NinjaKiwiParserSkeleton", "ParserNotImplemented"]

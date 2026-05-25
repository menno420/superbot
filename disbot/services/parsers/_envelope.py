"""Shared envelope helpers for Ninja Kiwi parsers (M3B).

Every official Ninja Kiwi BTD6 endpoint returns the same outer JSON
envelope::

    {"success": bool, "error": str | None, "body": Any,
     "model": dict, "next": str | None, "prev": str | None,
     "maxPages": int | None}

:func:`unwrap` validates the envelope and returns the body wrapped in
:class:`Envelope` so each parser can focus on body-shape normalisation.

:class:`ParserAdapter` lets a domain module register multiple
``parse_*`` functions through :func:`services.btd6_source_parser.register`
without writing one wrapper class per endpoint.

Parsers never branch on the model name. The same ``_btd6challengedocument``
is reused across races, bosses, odyssey maps, and challenges — fact_type
classifies each endpoint, not the upstream model field.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class EnvelopeError(Exception):
    """Raised when the NK API envelope is not the expected success shape."""

    def __init__(self, source_key: str, reason: str) -> None:
        super().__init__(f"NK envelope rejected for {source_key!r}: {reason}")
        self.source_key = source_key
        self.reason = reason


@dataclass(frozen=True)
class Envelope:
    success: bool
    error: str | None
    body: Any
    model: Any
    next: str | None
    prev: str | None
    max_pages: int | None


def unwrap(payload: Any, source_key: str) -> Envelope:
    """Validate the NK envelope and return its body wrapped in :class:`Envelope`.

    Raises :class:`EnvelopeError` for any non-success / error-present
    payload. ``body`` may be a list or a dict; the caller decides which
    based on fact_type. ``next``/``prev`` are kept verbatim; they are
    never auto-followed by the fetcher (page-1-only policy).
    """
    if not isinstance(payload, dict):
        raise EnvelopeError(source_key, "payload_not_a_dict")
    if payload.get("success") is not True:
        raise EnvelopeError(source_key, "success_not_true")
    if payload.get("error") is not None:
        raise EnvelopeError(source_key, "error_present")
    return Envelope(
        success=True,
        error=None,
        body=payload.get("body"),
        model=payload.get("model"),
        next=payload.get("next"),
        prev=payload.get("prev"),
        max_pages=payload.get("maxPages"),
    )


ParseFn = Callable[..., list[dict[str, Any]]]


@dataclass(frozen=True)
class ParserAdapter:
    """Adapts a plain parse function to the ``BTD6Parser`` protocol.

    Each domain module exposes one ``parse_*`` function per source_key
    and wraps each in :class:`ParserAdapter` before calling
    :func:`services.btd6_source_parser.register`. The registry stays
    keyed by source_key while domain modules expose plain functions
    for direct use in tests and renderers.

    ``path_params`` is forwarded so parsers that need URL context (race
    / boss / odyssey metadata, whose body ``id`` is ``"n/a"``) can
    compose a stable entity_key. Parsers that ignore it accept the
    keyword and discard.
    """

    source_key: str
    fn: ParseFn

    def parse(
        self,
        payload: Any,
        *,
        game_version: str | None = None,
        path_params: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        return self.fn(
            payload,
            game_version=game_version,
            path_params=path_params,
        )


__all__ = ["Envelope", "EnvelopeError", "ParseFn", "ParserAdapter", "unwrap"]

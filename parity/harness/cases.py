"""The golden-case model — typed, declarative, like tests/evals' EvalCase."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

__all__ = ["Step", "GoldenCase"]


@dataclass(frozen=True)
class Step:
    """One driven input. ``kind`` selects the gateway path.

    * ``command`` — a member message (prefix commands and plain messages)
    * ``slash``   — an application-command interaction
    * ``click``   — a component interaction on a bot message minted earlier
      in this case (``target_message`` = the ``<msg:N>`` ordinal)
    """

    kind: Literal["command", "slash", "click"]
    content: str = ""
    name: str = ""
    options: tuple[dict[str, Any], ...] = ()
    custom_id: str = ""
    #: alternative to custom_id for session-dynamic ids: click the Nth
    #: component (flattened row-major) of the target message
    component_index: int = -1
    target_message: int = 0
    component_type: int = 2
    values: tuple[str, ...] | None = None
    persona: str = "member"
    channel: str = "general"
    mentions: tuple[str, ...] = ()  # persona keys, resolved to ids at run time


@dataclass(frozen=True)
class GoldenCase:
    """One golden scenario: fixture → steps → observed outputs + DB delta."""

    id: str
    subsystem: str
    steps: tuple[Step, ...]
    fixture_sql: tuple[str, ...] = ()
    seed: int = 42
    notes: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

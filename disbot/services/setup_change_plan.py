"""Setup operation change plan — PR-04a.

The :func:`services.setup_operations.preflight_operations` function
returns a list of :class:`ChangePlanEntry` records describing what a
batch of :class:`SetupOperation` items would change.  The Final
Review embed renders this diff before apply (behind feature flag
``SETUP_PREFLIGHT_DIFF``); the apply path is unchanged.

**Read-only contract.**  Every read adapter that contributes to a
``ChangePlanEntry`` is forbidden from writing to the DB or calling a
mutation pipeline.  The invariant test
``tests/unit/invariants/test_setup_preflight_readonly.py`` enforces
this with AST checks.  A heavy read (>10 ms) should populate
``read_error`` with the ``"preflight: skipped (heavy)"`` sentinel
rather than blocking the preflight.

Sentinels are spelled out as module-level constants so the
ChangePlanEntry instances can be serialised to a diagnostics dict
view without serialising raw Python objects.

Public surface::

    RiskLevel        — Literal: low | medium | high | unknown
    ChangeValueKind  — Literal: value | absent | unknown
    ChangeValue      — frozen dataclass wrapping a value + kind
    ChangePlanEntry  — frozen dataclass per operation
    ABSENT           — convenience sentinel ChangeValue(kind="absent")
    UNKNOWN          — convenience sentinel ChangeValue(kind="unknown")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

RiskLevel = Literal["low", "medium", "high", "unknown"]
ChangeValueKind = Literal["value", "absent", "unknown"]


@dataclass(frozen=True)
class ChangeValue:
    """A sum type over (concrete value, absent, unknown).

    Using a small wrapper instead of bare ``Any`` keeps the rendered
    diff legible — "absent" and "unknown" are common signals for
    create_* and unsupported preflight kinds.
    """

    kind: ChangeValueKind = "value"
    value: Any = None

    def __repr__(self) -> str:  # noqa: D401 — short form for embeds
        if self.kind == "value":
            return repr(self.value)
        return self.kind.upper()


ABSENT: ChangeValue = ChangeValue(kind="absent")
UNKNOWN: ChangeValue = ChangeValue(kind="unknown")


@dataclass(frozen=True)
class ChangePlanEntry:
    """Per-operation preflight result.

    Fields:

    * ``op`` — the :class:`services.setup_operations.SetupOperation`
      this entry describes (the dispatcher does not consume this
      back; it is here so a Final Review embed can render the op
      summary alongside the diff).
    * ``current`` — the current value read from the DB / canonical
      service.  ``ABSENT`` when no current value exists (e.g. a
      ``create_*`` op or an unbound slot); ``UNKNOWN`` when the read
      adapter could not determine the current state (and likely set
      ``read_error``).
    * ``proposed`` — the value the op would produce.  Always set;
      ``ABSENT`` only for ``clear_binding`` (the op explicitly
      removes the slot).
    * ``would_change`` — ``True`` if applying the op would change
      observable state, ``False`` if the proposed value matches
      ``current``.  Conservative: when the current value is
      ``UNKNOWN``, ``would_change`` is set to ``True``.
    * ``risk`` — best-effort severity from
      ``op.metadata["risk"]`` if present, else ``"unknown"``.
    * ``rollback_note`` — human-readable rollback hint from
      ``op.metadata["rollback_note"]`` if present, else the empty
      string.
    * ``affected`` — string identifiers of additional state that
      would be touched (e.g. cleanup policy scope).  Populated by
      adapters; defaults to empty.
    * ``read_error`` — short ``type:message`` string when the read
      adapter raised or skipped.  ``None`` means the read succeeded
      (or never ran, for op kinds without a v1 adapter).
    * ``preflight_skipped_reason`` — ``None`` by default; set to
      ``"heavy"`` / ``"no_adapter"`` / etc. when this op kind has no
      read adapter or the read was deliberately skipped.
    """

    op: Any  # SetupOperation (typed via forward ref in setup_operations)
    label: str
    current: ChangeValue
    proposed: ChangeValue
    would_change: bool
    risk: RiskLevel = "unknown"
    rollback_note: str = ""
    affected: tuple[str, ...] = field(default_factory=tuple)
    read_error: str | None = None
    preflight_skipped_reason: str | None = None


__all__ = [
    "ABSENT",
    "UNKNOWN",
    "ChangePlanEntry",
    "ChangeValue",
    "ChangeValueKind",
    "RiskLevel",
]

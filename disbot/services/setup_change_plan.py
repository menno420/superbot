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


# ---------------------------------------------------------------------------
# PR-04a — Normalized preflight comparison
# ---------------------------------------------------------------------------


# Strings that ``utils.db.get_setting`` may return for a "no value
# stored" cell, in addition to ``None``.  Treated as equivalent to
# ``None`` so a freshly-set value to "" or an unset row to "" is not
# rendered as a misleading diff.  Aligns with the convention used by
# the settings mutation pipeline (see ``services.settings_resolution``
# canonical accessors).
_NORMALIZED_EMPTY: frozenset[str] = frozenset({"", "None", "null"})

# Strings that normalize to ``True`` / ``False`` for boolean settings.
# Settings stored as canonical strings ("true"/"false", "yes"/"no",
# "on"/"off") should compare equal to the boolean form an operator
# stages from the wizard.
#
# Note: ``"0"`` / ``"1"`` are deliberately **not** in these sets — they
# parse as ints below.  Mixing numeric and boolean equivalence here
# would let a stored ``"1"`` collapse to a staged ``True`` via Python's
# ``True == 1`` semantics, which would hide a real type-mismatch bug
# from the operator (false no-op).  See ``values_equivalent`` for the
# strict-bool guard that complements this.
_TRUTHY_TOKENS: frozenset[str] = frozenset({"true", "yes", "on"})
_FALSY_TOKENS: frozenset[str] = frozenset({"false", "no", "off"})


def _normalize_for_compare(value: Any) -> Any:
    """Return a canonical form of ``value`` for the preflight diff.

    The settings layer stores everything as TEXT, so naive string
    comparison would either hide real type mismatches (``int 1`` vs
    string ``"1"``) or surface false positives (``bool True`` vs
    string ``"true"``).  The normalizer collapses common equivalent
    forms so the preflight diff only flags **observable** changes.

    Rules (deliberately small — bigger normalization is the settings
    layer's job):

    * ``None`` → ``None``.
    * Strings ``""`` / ``"None"`` / ``"null"`` → ``None`` (DB layer
      sometimes stores the empty form for "unset").
    * Booleans → ``True`` / ``False`` directly.
    * Strings matching ``_TRUTHY_TOKENS`` → ``True``.
    * Strings matching ``_FALSY_TOKENS`` → ``False``.
    * Numeric strings → ``int`` if exactly parseable, else stripped
      string.
    * Other strings → stripped + lowercased so trailing whitespace
      / case drift does not show as a diff.
    * Everything else: returned unchanged.

    The normalizer is deterministic and side-effect-free.  Adding a
    new equivalence here costs one entry; the comparison itself
    remains a single ``==``.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s in _NORMALIZED_EMPTY:
            return None
        lowered = s.lower()
        if lowered in _TRUTHY_TOKENS:
            return True
        if lowered in _FALSY_TOKENS:
            return False
        # Numeric coercion — only exact int parse so we don't
        # accidentally collapse "1.0" with "1" for non-numeric keys.
        try:
            return int(s)
        except ValueError:
            pass
        return lowered
    return value


def values_equivalent(current: Any, proposed: Any) -> bool:
    """Return ``True`` when the preflight should treat the two values
    as the same observable state.

    Use this in every preflight adapter that needs to decide
    ``would_change``.  Centralising the rule here means a new
    equivalence (e.g. canonical channel-ID string vs int) is one edit
    rather than a sweep of adapters.

    **Strict bool/int separation.**  Python's ``True == 1`` and
    ``False == 0`` would otherwise let a stored numeric setting
    collapse with a staged boolean (and vice versa), which would hide
    a real type mismatch from the operator as a misleading "no
    change" render.  This guard makes the equivalence asymmetric on
    bool-ness: if exactly one side normalizes to a ``bool`` and the
    other to a non-``bool``, they are **not** equivalent.

    Operator-safe rule of thumb: when in doubt, render the diff.
    A false diff is noise; a false no-op is the operator clicking
    "Apply" thinking nothing changes when something does.
    """
    nc = _normalize_for_compare(current)
    np = _normalize_for_compare(proposed)
    # bool is a subclass of int in Python, so plain ``nc == np`` would
    # report ``True == 1`` as equivalent.  Block that by checking
    # bool-ness on both sides before deferring to ``==``.
    if isinstance(nc, bool) != isinstance(np, bool):
        return False
    return nc == np


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


# ---------------------------------------------------------------------------
# PR-04b — Rendering helper (text only; embed-agnostic)
# ---------------------------------------------------------------------------


# Discord's per-field value limit.  An embed.add_field(value=...) call
# with more than this many characters is rejected by the API.  We cap
# the rendered diff to this size so render helpers stay safe to drop
# into an embed field without the caller doing their own truncation.
DISCORD_FIELD_VALUE_LIMIT: int = 1024

# Single-line ceiling.  Even when ``max_lines`` would admit more
# entries, we hard-cap an individual line so one pathological label
# can't blow the whole budget on its own.  Slightly below the field
# limit so we always have room for a truncation suffix.
_SINGLE_LINE_CAP: int = 256

# Suffix appended when the rendered output had to be truncated to fit
# the field cap.  Counts against the cap so the visible body shrinks
# accordingly.
_TRUNCATION_SUFFIX: str = "… (truncated, see logs for full diff)"


@dataclass(frozen=True)
class RenderedChangePlan:
    """Result of :func:`format_change_plan_lines`.

    Holds the lines plus enough metadata for tests / operator output
    to detect truncation without re-running the renderer.

    * ``lines`` — the truncated, embed-safe lines, joined with a
      newline character to total at most
      :data:`DISCORD_FIELD_VALUE_LIMIT` chars.
    * ``rendered_count`` — how many entries were rendered.
    * ``truncated`` — ``True`` when at least one entry was dropped or a
      line was clipped to fit the field cap.
    * ``dropped_count`` — number of entries omitted entirely.
    """

    lines: tuple[str, ...]
    rendered_count: int
    truncated: bool
    dropped_count: int

    @property
    def body(self) -> str:
        """Newline-joined string suitable for ``embed.add_field``."""
        return "\n".join(self.lines)


def _truncate_line(line: str) -> tuple[str, bool]:
    """Cap a single line at ``_SINGLE_LINE_CAP`` so one entry cannot
    monopolise the field budget.  Returns ``(line, was_truncated)``.
    """
    if len(line) <= _SINGLE_LINE_CAP:
        return line, False
    return line[: _SINGLE_LINE_CAP - 1] + "…", True


def _format_entry(entry: ChangePlanEntry) -> str:
    """Return the canonical single-line render for one entry."""
    if entry.preflight_skipped_reason:
        return (
            f"⚠ {entry.label} · preflight unavailable "
            f"({entry.preflight_skipped_reason})"
        )
    if entry.read_error:
        return f"⚠ {entry.label} · read error: {entry.read_error}"
    if not entry.would_change:
        return f"✅ {entry.label} · no change (current matches proposed)"
    marker = "✏"
    if entry.risk in ("medium", "high"):
        marker = "⚠"
    risk_suffix = (
        f"   [risk={entry.risk}]" if entry.risk and entry.risk != "unknown" else ""
    )
    return (
        f"{marker} {entry.label} · current={entry.current!r} → "
        f"{entry.proposed!r}{risk_suffix}"
    )


def render_change_plan(
    entries: list[ChangePlanEntry],
    *,
    max_lines: int = 10,
    field_limit: int = DISCORD_FIELD_VALUE_LIMIT,
) -> RenderedChangePlan:
    """Render a preflight diff into an embed-safe block.

    PR-04b helper that **owns the Discord embed field budget**.  The
    caller passes the entries it wants surfaced; this helper:

    1. Renders up to ``max_lines`` entries (line-count cap).
    2. Hard-caps any single line at :data:`_SINGLE_LINE_CAP` chars so
       one pathological label cannot consume the whole budget.
    3. Packs the lines into a body whose total newline-joined length
       stays under ``field_limit`` (default
       :data:`DISCORD_FIELD_VALUE_LIMIT`).
    4. Appends :data:`_TRUNCATION_SUFFIX` as the last line when any
       content was clipped, so operators see the truncation signal
       directly in the embed.

    Returns a :class:`RenderedChangePlan` carrying both the lines
    and truncation metadata, so tests and ``!platform`` diagnostics
    can detect "we dropped N entries" without re-running the renderer.

    Backwards compat: :func:`format_change_plan_lines` returns just
    the lines (the original PR-04b shape).
    """
    if not entries:
        return RenderedChangePlan(
            lines=(),
            rendered_count=0,
            truncated=False,
            dropped_count=0,
        )

    rendered: list[str] = []
    truncated = False
    rendered_count = 0
    total_len = 0

    # First, line-count cap.
    candidates = entries[:max_lines]
    line_cap_dropped = len(entries) - len(candidates)
    if line_cap_dropped:
        truncated = True

    for entry in candidates:
        raw = _format_entry(entry)
        line, line_was_clipped = _truncate_line(raw)
        if line_was_clipped:
            truncated = True

        # +1 for the separator between this line and the previous.
        sep_cost = 1 if rendered else 0
        # Reserve room for the truncation suffix if we end up needing
        # one.  This is a conservative budget — if every line fits we
        # never use it.
        suffix_budget = len(_TRUNCATION_SUFFIX) + 1  # +1 for "\n"
        if total_len + sep_cost + len(line) + suffix_budget > field_limit:
            # Adding this line would push us into the suffix budget;
            # stop and mark truncated.
            truncated = True
            break
        rendered.append(line)
        total_len += sep_cost + len(line)
        rendered_count += 1

    dropped = (len(entries) - rendered_count) if truncated else 0
    if truncated:
        # Only append the suffix if it actually fits in the remaining
        # budget.  In the degenerate case where ``field_limit`` is
        # smaller than the suffix itself, appending would push the
        # body over the cap — better to silently drop the suffix and
        # still report ``truncated=True`` via the dataclass field so
        # callers can detect the situation programmatically.
        suffix_sep_cost = 1 if rendered else 0
        if total_len + suffix_sep_cost + len(_TRUNCATION_SUFFIX) <= field_limit:
            rendered.append(_TRUNCATION_SUFFIX)

    return RenderedChangePlan(
        lines=tuple(rendered),
        rendered_count=rendered_count,
        truncated=truncated,
        dropped_count=dropped,
    )


def format_change_plan_lines(
    entries: list[ChangePlanEntry],
    *,
    max_lines: int = 10,
) -> list[str]:
    """Backwards-compat shim — returns just the rendered lines.

    PR-04b shipped this as the original surface; PR-04b (review)
    upgraded the helper to enforce Discord's 1024-char field limit
    through :func:`render_change_plan`, which returns a richer
    :class:`RenderedChangePlan`.  Callers that only need the lines
    keep working unchanged.
    """
    return list(render_change_plan(entries, max_lines=max_lines).lines)


__all__ = [
    "ABSENT",
    "DISCORD_FIELD_VALUE_LIMIT",
    "RenderedChangePlan",
    "UNKNOWN",
    "ChangePlanEntry",
    "ChangeValue",
    "ChangeValueKind",
    "RiskLevel",
    "format_change_plan_lines",
    "render_change_plan",
    "values_equivalent",
]

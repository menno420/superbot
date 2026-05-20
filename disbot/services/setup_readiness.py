"""Per-guild setup-readiness inventory (PR H).

Aggregates the bot's declared configuration surface — :class:`SettingSpec`,
:class:`BindingSpec`, :class:`ResourceRequirement` from
:mod:`core.runtime.subsystem_schema` — and reports how much of it the
operator has actually populated for a given guild.

The output is read-only: this service does NOT mutate anything. It
exists as the substrate for a future setup wizard and, immediately, as
the data backing ``!platform setup-readiness`` (PR H).

Score model
-----------
Per subsystem we count three buckets:

* **Bindings** — declared in the schema's ``bindings`` list; bound when
  there is a row in ``subsystem_bindings`` for ``(guild_id, subsystem,
  binding_name)`` with non-empty status (any non-error status).
* **Settings** — declared in the schema's ``settings`` list; configured
  when ``db.get_setting(guild_id, settings_key, "")`` is non-empty AND
  differs from the spec's default. Settings with an empty
  ``settings_key`` (not yet migrated off the legacy KV) count as
  declared but never as configured — surfaces them as known gaps.
* **Resource requirements** — declared in the schema's
  ``resource_requirements``. These are descriptive — they tell the
  wizard what platform resources the subsystem consumes — and don't
  carry their own "configured" signal independent of bindings, so
  they show as declared counts only.

Per-subsystem score = (bound + configured) / (declared bindings +
declared settings) — clamped to [0, 1.0]; subsystems with no declared
config evaluate to ``None`` so they don't drag down the average.

Aggregate score = unweighted mean of per-subsystem scores that are
not ``None``.

Public API
----------
* :func:`collect` — build a :class:`ReadinessReport` for a guild.
* :class:`ReadinessReport` — frozen dataclass returned by :func:`collect`.
* :class:`SubsystemReadiness` — per-subsystem entry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from core.runtime.subsystem_schema import all_schemas
from utils import db
from utils.db import bindings as db_bindings

logger = logging.getLogger("bot.setup_readiness")


@dataclass(frozen=True)
class SubsystemReadiness:
    """Per-subsystem readiness counts.

    ``score`` is ``None`` when the subsystem declares no bindings or
    settings — there's nothing to be ready about, so it should not be
    averaged into the aggregate.
    """

    subsystem: str
    bindings_declared: int
    bindings_bound: int
    settings_declared: int
    settings_configured: int
    resources_declared: int
    score: float | None

    @property
    def has_config(self) -> bool:
        """True when the subsystem has anything operator-configurable."""
        return self.bindings_declared > 0 or self.settings_declared > 0


@dataclass(frozen=True)
class ReadinessReport:
    """Aggregate readiness snapshot for a guild."""

    guild_id: int
    per_subsystem: tuple[SubsystemReadiness, ...]
    bindings_declared: int
    bindings_bound: int
    settings_declared: int
    settings_configured: int
    resources_declared: int
    aggregate_score: float | None

    @property
    def percentage(self) -> int:
        """Aggregate score as an integer 0–100 (``0`` when no config)."""
        if self.aggregate_score is None:
            return 0
        return round(self.aggregate_score * 100)


async def _is_setting_configured(
    guild_id: int,
    settings_key: str,
    default_repr: str,
) -> bool:
    """Return True if the stored value differs from the spec's default.

    Settings without a ``settings_key`` (not migrated off the legacy
    KV) cannot be looked up here; they count as un-configured.
    """
    if not settings_key:
        return False
    try:
        stored = await db.get_setting(guild_id, settings_key, "")
    except Exception as exc:  # noqa: BLE001 — diagnostic surface, fail closed
        logger.warning(
            "setup_readiness: get_setting failed for %s/%s: %s",
            guild_id,
            settings_key,
            exc,
        )
        return False
    if not stored:
        return False
    # ``default_repr`` is ``repr(spec.default)``; the stored value is
    # always a string. Compare by repr to handle int/bool defaults
    # (``"42"`` should not match ``repr(42)`` of ``'42'``, but stored
    # "True" matches repr(True) = "True"). A configured non-default
    # value satisfies the readiness check.
    return repr(stored) != default_repr and stored != default_repr


def _compute_score(
    *,
    bindings_declared: int,
    bindings_bound: int,
    settings_declared: int,
    settings_configured: int,
) -> float | None:
    """Per-subsystem score in [0, 1] — or ``None`` when nothing to score."""
    total = bindings_declared + settings_declared
    if total == 0:
        return None
    filled = bindings_bound + settings_configured
    return max(0.0, min(1.0, filled / total))


async def collect(guild_id: int) -> ReadinessReport:
    """Build the per-guild readiness report.

    Walks :func:`core.runtime.subsystem_schema.all_schemas` and, for each
    declared subsystem, joins the schema against:

    * :func:`utils.db.bindings.list_for_guild` for binding fill state.
    * :func:`utils.db.get_setting` for setting fill state.

    Subsystems with no declared bindings or settings appear with
    ``score=None`` so they're surfaced in the report but don't drag the
    aggregate.
    """
    schemas = all_schemas()
    binding_rows = await db_bindings.list_for_guild(guild_id)
    # Group bound bindings by (subsystem, binding_name) for O(1) lookup.
    bound_keys: set[tuple[str, str]] = set()
    for row in binding_rows:
        status = (row.get("status") or "").lower()
        # Skip rows in failed/cleared states — they exist as audit
        # rows but don't represent a satisfied binding slot.
        if status in {"cleared", "error", ""}:
            continue
        bound_keys.add((row["subsystem"], row["binding_name"]))

    per_subsystem: list[SubsystemReadiness] = []
    total_b_declared = 0
    total_b_bound = 0
    total_s_declared = 0
    total_s_configured = 0
    total_r_declared = 0

    for subsystem in sorted(schemas):
        schema = schemas[subsystem]
        b_decl = len(schema.bindings)
        b_bound = sum(
            1 for spec in schema.bindings if (subsystem, spec.name) in bound_keys
        )
        s_decl = len(schema.settings)
        s_configured = 0
        for spec in schema.settings:
            if await _is_setting_configured(
                guild_id,
                spec.settings_key,
                repr(spec.default),
            ):
                s_configured += 1
        r_decl = len(schema.resource_requirements)

        score = _compute_score(
            bindings_declared=b_decl,
            bindings_bound=b_bound,
            settings_declared=s_decl,
            settings_configured=s_configured,
        )
        per_subsystem.append(
            SubsystemReadiness(
                subsystem=subsystem,
                bindings_declared=b_decl,
                bindings_bound=b_bound,
                settings_declared=s_decl,
                settings_configured=s_configured,
                resources_declared=r_decl,
                score=score,
            ),
        )
        total_b_declared += b_decl
        total_b_bound += b_bound
        total_s_declared += s_decl
        total_s_configured += s_configured
        total_r_declared += r_decl

    scored = [r for r in per_subsystem if r.score is not None]
    aggregate: float | None = None
    if scored:
        aggregate = sum(r.score for r in scored) / len(scored)  # type: ignore[misc]

    return ReadinessReport(
        guild_id=guild_id,
        per_subsystem=tuple(per_subsystem),
        bindings_declared=total_b_declared,
        bindings_bound=total_b_bound,
        settings_declared=total_s_declared,
        settings_configured=total_s_configured,
        resources_declared=total_r_declared,
        aggregate_score=aggregate,
    )


__all__ = [
    "ReadinessReport",
    "SubsystemReadiness",
    "collect",
]

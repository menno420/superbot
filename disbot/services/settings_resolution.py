"""Settings resolution — S3 of the Global Settings & Customization Manager.

Single scalar-only read path for typed :class:`SettingSpec` values,
returning a frozen :class:`SettingResolution` that carries the resolved
value, its provenance, the declared default, and a validity flag.

Sources composed (all read-only):

* :func:`core.runtime.subsystem_schema.get_schema` — the authoritative
  :class:`SettingSpec` (carries ``value_type``, ``default``,
  ``validator``).
* :func:`core.runtime.guild_config.get` — per-key TTL cache.
* :func:`utils.db.settings.get_setting` — the legacy KV table.

Scope (per the v1 amendment):

* This resolver is **scalar-only**. It returns ``int``, ``str``,
  ``bool``, or ``float`` values.
* It does **NOT** resolve :class:`BindingSpec` slots into Discord
  resource handles. That stays in
  :func:`core.runtime.bindings.get_binding`.
* The ``provenance`` enum is restricted to ``"default" | "legacy_kv"``
  in v1. ``"binding"`` (scalar in binding-shaped storage) and
  ``"scope_override"`` (scope-chained scalar) are reserved for future
  milestones and will widen the enum then.

Public surface:

* :class:`SettingResolution` — frozen result type.
* :func:`resolve_setting` — single-key resolution.
* :func:`resolve_batch` — every scalar in a subsystem's schema.
* :func:`counters_snapshot` — provenance / validity counters used by
  the diagnostics provider (mirrors
  :func:`core.runtime.config_arbitration.counters_snapshot`).

Diagnostics provider name: ``"settings_resolution"``.

Cycle discipline (mirrors :mod:`services.platform_consistency` and
:mod:`services.customization_catalogue`): all cross-package imports
are function-local. Top-level imports are stdlib only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger("bot.services.settings_resolution")


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


Provenance = Literal["default", "legacy_kv"]


@dataclass(frozen=True)
class SettingResolution:
    """Typed snapshot of a single scalar setting read.

    Fields:

    subsystem:
        Owning subsystem name.
    name:
        Setting name within the subsystem.
    value:
        The resolved value, coerced to the spec's declared type. Falls
        back to ``default`` when no KV row exists OR the coerced value
        failed validation; ``valid`` distinguishes the two.
    provenance:
        ``"default"`` when no KV row is present or the spec has no
        ``settings_key`` declared. ``"legacy_kv"`` when a KV row drove
        the value (even if coercion/validation failed — that's
        signalled by ``valid``).
    default:
        The declared default from the :class:`SettingSpec`.
    valid:
        ``True`` when the value was either the default or a
        successfully coerced + validated KV row. ``False`` when a KV
        row existed but failed coercion or validation; the resolver
        falls back to ``default`` in that case.
    raw:
        The raw string read from the KV table, or ``None`` when the
        provenance is ``"default"``.
    diagnostics:
        Short free-form strings describing notable transitions (e.g.
        ``"int coerce failed: 'abc'"`` or
        ``"validator rejected value: out of range"``).
    """

    subsystem: str
    name: str
    value: Any
    provenance: Provenance
    default: Any
    valid: bool
    raw: str | None
    diagnostics: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Counters — used by the diagnostics provider
# ---------------------------------------------------------------------------


_BY_PROVENANCE: dict[str, int] = {"default": 0, "legacy_kv": 0}
_BY_VALID: dict[str, int] = {"true": 0, "false": 0}
_BY_UNKNOWN_SPEC: int = 0
_CALLS_TOTAL = 0


def _bump_counters(resolution: SettingResolution | None) -> None:
    global _CALLS_TOTAL, _BY_UNKNOWN_SPEC
    _CALLS_TOTAL += 1
    if resolution is None:
        _BY_UNKNOWN_SPEC += 1
        return
    _BY_PROVENANCE[resolution.provenance] = (
        _BY_PROVENANCE.get(resolution.provenance, 0) + 1
    )
    key = "true" if resolution.valid else "false"
    _BY_VALID[key] = _BY_VALID.get(key, 0) + 1


def _reset_counters_for_tests() -> None:
    """Test helper — zero every counter."""
    global _CALLS_TOTAL, _BY_UNKNOWN_SPEC
    _CALLS_TOTAL = 0
    _BY_UNKNOWN_SPEC = 0
    for d in (_BY_PROVENANCE, _BY_VALID):
        for k in list(d):
            d[k] = 0


def counters_snapshot() -> dict[str, Any]:
    """Snapshot of resolution counters; called by the diagnostics provider."""
    return {
        "calls_total": _CALLS_TOTAL,
        "unknown_spec": _BY_UNKNOWN_SPEC,
        "by_provenance": dict(_BY_PROVENANCE),
        "by_valid": dict(_BY_VALID),
    }


# ---------------------------------------------------------------------------
# Coercion
# ---------------------------------------------------------------------------


_BOOL_TRUTHY = frozenset({"true", "yes", "on", "1"})
_BOOL_FALSY = frozenset({"false", "no", "off", "0", ""})


def _coerce(raw: str, value_type: type) -> tuple[Any, bool, str]:
    """Coerce ``raw`` to ``value_type``.

    Returns ``(value, valid, diagnostic)`` — when ``valid`` is ``False``
    ``value`` is ``None`` and ``diagnostic`` describes the failure.
    Supported types: ``str``, ``int``, ``float``, ``bool``. Any other
    type is treated as unsupported and returns ``valid=False``.
    """
    if value_type is str:
        return raw, True, ""
    if value_type is bool:
        lo = raw.strip().lower()
        if lo in _BOOL_TRUTHY:
            return True, True, ""
        if lo in _BOOL_FALSY:
            return False, True, ""
        return None, False, f"bool coerce failed: {raw!r}"
    if value_type is int:
        try:
            return int(raw), True, ""
        except (ValueError, TypeError):
            return None, False, f"int coerce failed: {raw!r}"
    if value_type is float:
        try:
            return float(raw), True, ""
        except (ValueError, TypeError):
            return None, False, f"float coerce failed: {raw!r}"
    return None, False, f"unsupported value_type: {value_type!r}"


# ---------------------------------------------------------------------------
# Spec lookup
# ---------------------------------------------------------------------------


def _find_spec(subsystem: str, name: str) -> Any:
    """Return the :class:`SettingSpec` for ``(subsystem, name)`` or ``None``."""
    from core.runtime.subsystem_schema import get_schema

    schema = get_schema(subsystem)
    if schema is None:
        return None
    for spec in schema.settings:
        if spec.name == name:
            return spec
    return None


def _all_specs(subsystem: str) -> tuple[Any, ...]:
    """Return every :class:`SettingSpec` declared by ``subsystem``."""
    from core.runtime.subsystem_schema import get_schema

    schema = get_schema(subsystem)
    if schema is None:
        return ()
    return tuple(schema.settings)


# ---------------------------------------------------------------------------
# Cached legacy-KV read
# ---------------------------------------------------------------------------


async def _read_legacy(guild_id: int, settings_key: str) -> str:
    """Read a legacy KV row via the typed-accessor lane.

    Routes through :func:`utils.guild_config_accessors.get_setting_value`
    so the F-1 invariant test (``test_guild_config_typed_accessors``)
    sees a single typed-accessor owner for the ``"setting:"`` cache
    namespace.
    """
    from utils.guild_config_accessors import get_setting_value

    return await get_setting_value(guild_id, settings_key)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


async def resolve_setting(
    guild_id: int,
    subsystem: str,
    name: str,
) -> SettingResolution | None:
    """Resolve a single scalar :class:`SettingSpec` to a typed value.

    Returns ``None`` when ``(subsystem, name)`` is not a declared
    :class:`SettingSpec` — callers should treat that as "no such
    setting" rather than as a missing value.

    Provenance and validity:

    * ``provenance="default"`` is returned when the spec has no
      ``settings_key`` declared OR the KV row is empty.
    * ``provenance="legacy_kv"`` is returned whenever a non-empty KV
      row drove the value (even when coercion or validation failed —
      that's signalled by ``valid=False`` and the value still falls
      back to the declared default).
    """
    spec = _find_spec(subsystem, name)
    if spec is None:
        _bump_counters(None)
        return None

    # No canonical key yet — the only legal source is the spec default.
    if not spec.settings_key:
        resolution = SettingResolution(
            subsystem=subsystem,
            name=name,
            value=spec.default,
            provenance="default",
            default=spec.default,
            valid=True,
            raw=None,
            diagnostics=("settings_key unset — returning declared default",),
        )
        _bump_counters(resolution)
        return resolution

    raw = await _read_legacy(guild_id, spec.settings_key)
    if raw == "":
        resolution = SettingResolution(
            subsystem=subsystem,
            name=name,
            value=spec.default,
            provenance="default",
            default=spec.default,
            valid=True,
            raw=raw,
            diagnostics=(),
        )
        _bump_counters(resolution)
        return resolution

    coerced, ok, diag = _coerce(raw, spec.value_type)
    diagnostics: list[str] = []
    if diag:
        diagnostics.append(diag)
    if not ok:
        resolution = SettingResolution(
            subsystem=subsystem,
            name=name,
            value=spec.default,
            provenance="legacy_kv",
            default=spec.default,
            valid=False,
            raw=raw,
            diagnostics=tuple(diagnostics),
        )
        _bump_counters(resolution)
        return resolution

    if spec.validator is not None:
        try:
            spec.validator(coerced)
        except (ValueError, TypeError) as exc:
            diagnostics.append(f"validator rejected value: {exc}")
            resolution = SettingResolution(
                subsystem=subsystem,
                name=name,
                value=spec.default,
                provenance="legacy_kv",
                default=spec.default,
                valid=False,
                raw=raw,
                diagnostics=tuple(diagnostics),
            )
            _bump_counters(resolution)
            return resolution

    resolution = SettingResolution(
        subsystem=subsystem,
        name=name,
        value=coerced,
        provenance="legacy_kv",
        default=spec.default,
        valid=True,
        raw=raw,
        diagnostics=tuple(diagnostics),
    )
    _bump_counters(resolution)
    return resolution


async def resolve_batch(
    guild_id: int,
    subsystem: str,
) -> tuple[SettingResolution, ...]:
    """Resolve every scalar :class:`SettingSpec` declared by ``subsystem``.

    Returns ``()`` when the subsystem has no registered schema. The
    returned tuple is ordered the same way the schema declares the
    settings (declaration order is stable across a process lifetime
    because the schema is frozen post-registration).
    """
    specs = _all_specs(subsystem)
    results: list[SettingResolution] = []
    for spec in specs:
        resolution = await resolve_setting(guild_id, subsystem, spec.name)
        if resolution is not None:
            results.append(resolution)
    return tuple(results)


# ---------------------------------------------------------------------------
# Diagnostics provider — registers at import time
# ---------------------------------------------------------------------------


def _snapshot() -> dict[str, Any]:
    """Stable diagnostics snapshot for ``!platform settings-resolution`` /
    a future ``!platform consistency`` section.
    """
    return {"counters": counters_snapshot()}


def _register_diagnostics() -> None:
    from services import diagnostics_service

    diagnostics_service.register("settings_resolution", _snapshot)


_register_diagnostics()


__all__ = [
    "Provenance",
    "SettingResolution",
    "counters_snapshot",
    "resolve_batch",
    "resolve_setting",
]

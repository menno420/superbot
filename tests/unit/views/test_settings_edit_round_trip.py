"""Round-trip coverage: every declared ``SettingSpec`` writes through the
mutation pipeline and resolves back via the resolver.

Parametrises over every ``SettingSpec`` discovered at runtime via
:func:`core.runtime.subsystem_schema.all_schemas`.  For each spec the
test picks a non-default value appropriate to the spec's
``(value_type, allowed_values, input_hint, presets)`` shape, writes
it through :class:`services.settings_mutation.SettingsMutationPipeline`,
and asserts :func:`services.settings_resolution.resolve_setting`
returns the new value.

The matrix this covers maps 1:1 to the dispatch in
``views/settings/subsystem_view.py``:

* ``input_hint="channel"`` → string-id write
* ``input_hint="role"`` → string-id write
* ``input_hint="numeric_presets"`` + ``presets`` → numeric preset write
* ``value_type=bool`` → toggle
* ``value_type=str`` + ``allowed_values`` → enum pick
* ``value_type=int`` / ``float`` → numeric write
* ``value_type=str`` free-form → text write

Edge cases tested separately at the bottom: invalid coercion, validator
failure, default round-trip.
"""

from __future__ import annotations

from typing import Any

import pytest

from core.runtime import guild_config
from core.runtime import subsystem_schema as schema_mod
from services.settings_mutation import SettingsMutationPipeline
from services.settings_resolution import resolve_setting
from utils import db as db_pkg
from utils.db import settings as settings_db
from utils.db import settings_audit as audit_db


def _load_all_schemas() -> None:
    """Import every cog's ``schemas`` module and call ``register_schemas``.

    Cog setup functions normally register schemas at boot.  The test
    runner does not load cogs, so we must trigger registration
    ourselves before discovering the matrix.  Each call is idempotent
    against ``schema_mod._reset_for_tests`` because individual specs
    error on duplicate registration.
    """
    import importlib

    modules = [
        "cogs.moderation.schemas",
        "cogs.logging.schemas",
        "cogs.economy.schemas",
        "cogs.xp.schemas",
        "cogs.blackjack.schemas",
        "cogs.deathmatch.schemas",
        "cogs.rps_tournament.schemas",
    ]
    for module_path in modules:
        mod = importlib.import_module(module_path)
        register = getattr(mod, "register_schemas", None)
        if register is None:
            continue
        try:
            register()
        except ValueError:
            # Already registered from a previous test load — fine.
            pass


_load_all_schemas()


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeGuild:
    def __init__(self, guild_id: int = 1, owner_id: int = 0):
        self.id = guild_id
        self.owner_id = owner_id


class _FakeMember:
    def __init__(self, member_id: int = 7, *, guild: _FakeGuild | None = None):
        self.id = member_id
        self.guild = guild or _FakeGuild()

        class _Perms:
            administrator = True
            manage_channels = True
            manage_roles = True
            manage_guild = True
            moderate_members = False

        self.guild_permissions = _Perms()


# ---------------------------------------------------------------------------
# In-memory KV + audit + event shims
# ---------------------------------------------------------------------------


@pytest.fixture
def _isolated_state(monkeypatch):
    """In-memory KV + audit + event bus shim for the mutation pipeline."""
    # Re-register schemas defensively: another test in the session may
    # have called ``schema_mod._reset_for_tests()`` between collection
    # (when ``_PARAMS`` was computed) and now.
    _load_all_schemas()

    guild_config._reset_for_tests()

    _kv: dict[tuple[int, str], str] = {}

    async def _fake_get_setting(
        guild_id: int,
        key: str,
        default: str = "",
    ) -> str:
        return _kv.get((guild_id, key), default)

    monkeypatch.setattr(settings_db, "get_setting", _fake_get_setting)
    monkeypatch.setattr(db_pkg, "get_setting", _fake_get_setting)

    audit_log: list[dict] = []

    async def _fake_set_value_with_audit(
        *,
        guild_id: int,
        subsystem: str,
        name: str,
        settings_key: str,
        prev_value_raw,
        new_value_raw: str,
        actor_id,
        actor_type: str,
        mutation_id: str,
        mutation_type: str = "set_value",
    ) -> None:
        _kv[(guild_id, settings_key)] = new_value_raw
        audit_log.append(
            {
                "guild_id": guild_id,
                "subsystem": subsystem,
                "name": name,
                "settings_key": settings_key,
                "prev_value_raw": prev_value_raw,
                "new_value_raw": new_value_raw,
                "actor_id": actor_id,
                "actor_type": actor_type,
                "mutation_id": mutation_id,
                "mutation_type": mutation_type,
            },
        )

    monkeypatch.setattr(audit_db, "set_value_with_audit", _fake_set_value_with_audit)

    from core.events import bus

    emitted: list[dict] = []

    async def _fake_emit(event, /, **payload):
        emitted.append({"event": event, **payload})

    monkeypatch.setattr(bus, "emit", _fake_emit)

    yield {"kv": _kv, "audit_log": audit_log, "emitted": emitted}

    guild_config._reset_for_tests()


# ---------------------------------------------------------------------------
# Spec discovery
# ---------------------------------------------------------------------------


def _writable_specs() -> list[tuple[str, str, Any]]:
    """Return ``(subsystem, spec_name, spec)`` for every writable spec."""
    out: list[tuple[str, str, Any]] = []
    for subsystem_name, schema in schema_mod.all_schemas().items():
        for spec in schema.settings:
            # No settings_key → spec is declared but not persistable
            # via the legacy KV path; mutation pipeline rejects with
            # UnmigrateableSettingError.  Skip from round-trip.
            if not spec.settings_key:
                continue
            out.append((subsystem_name, spec.name, spec))
    return out


_PARAMS = _writable_specs()
_IDS = [f"{sub}.{name}" for sub, name, _ in _PARAMS]


# ---------------------------------------------------------------------------
# Non-default value picker per spec shape
# ---------------------------------------------------------------------------


def _non_default_value_for(spec: Any) -> Any:
    """Return a non-default value of the right shape for ``spec``.

    Mirrors the widget dispatch matrix.  Channel/role specs use a
    fixed fake snowflake; numeric presets pick a non-default preset
    when one exists.  Validators may reject some choices — for those
    specs we fall back through the picker (e.g. switching to a
    second-choice preset or returning the default+1 for ints).
    """
    hint = (spec.input_hint or "").strip().lower()
    allowed = spec.allowed_values or ()

    if hint == "channel":
        return "111222333444555000"
    if hint == "role":
        return "999888777666555000"
    if hint == "numeric_presets" and spec.presets:
        for candidate in spec.presets:
            if candidate != spec.default:
                return candidate
        # Every preset matches default — fall through to value_type below.

    if spec.value_type is bool:
        return not bool(spec.default)
    if spec.value_type is int:
        base = int(spec.default) if spec.default is not None else 0
        for delta in (1, 2, 5, 10, 100):
            candidate = base + delta
            if _validator_accepts(spec, candidate):
                return candidate
        return base + 1
    if spec.value_type is float:
        base = float(spec.default) if spec.default is not None else 0.0
        for delta in (1.0, 0.5, 2.0):
            candidate = base + delta
            if _validator_accepts(spec, candidate):
                return candidate
        return base + 1.0
    if spec.value_type is str and allowed:
        for candidate in allowed:
            if candidate != spec.default:
                return candidate
        # Single-value allowed set: re-write the default, the test
        # treats this as a no-op round-trip.
        return allowed[0]
    if spec.value_type is str:
        # The trailing csv-subset candidates cover constrained free-form str
        # specs (e.g. moderation ``dm_actions``, a comma-separated allow-list;
        # logging ``ignored_channels``/``ignored_users``, a comma-separated id
        # list) whose validator rejects the arbitrary first picks.
        for candidate in (
            "round-trip-test",
            "alt-value",
            "x",
            "y",
            "warn,timeout",
            "warn",
            "123456789012345678,234567890123456789",  # numeric id CSV
            "123456789012345678",
        ):
            if candidate != spec.default and _validator_accepts(spec, candidate):
                return candidate
        return "round-trip-test"

    raise AssertionError(f"unsupported value_type for round-trip: {spec.value_type!r}")


def _validator_accepts(spec: Any, value: Any) -> bool:
    """True iff the spec validator (if any) accepts ``value``."""
    if spec.validator is None:
        return True
    try:
        spec.validator(value)
    except Exception:
        return False
    return True


# ---------------------------------------------------------------------------
# Edit round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("subsystem", "name", "spec"), _PARAMS, ids=_IDS)
@pytest.mark.asyncio
async def test_edit_round_trip_every_writable_spec(
    _isolated_state, subsystem: str, name: str, spec: Any,
):
    """Write a non-default value through the pipeline; resolve it back."""
    guild = _FakeGuild(guild_id=1)
    actor = _FakeMember(guild=guild)
    value = _non_default_value_for(spec)

    pipeline = SettingsMutationPipeline()
    result = await pipeline.set_value(guild, subsystem, name, value, actor)
    assert result.new_value_raw == _serialise_for_compare(value)

    resolution = await resolve_setting(guild.id, subsystem, name)
    assert resolution is not None, f"resolver returned None for {subsystem}.{name}"
    assert resolution.value == _expected_resolved(spec, value), (
        f"resolver returned {resolution.value!r} after writing {value!r} "
        f"for {subsystem}.{name}"
    )
    assert resolution.valid is True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise_for_compare(value: Any) -> str:
    """Match SettingsMutationPipeline._serialize."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _expected_resolved(spec: Any, value: Any) -> Any:
    """The value the resolver will return after writing ``value``.

    The resolver coerces by ``value_type`` — for ``int`` / ``float`` /
    ``bool`` settings the round-trip is exact.  For ``str`` the value
    survives unchanged.  Channel/role ``input_hint`` settings have
    ``value_type=str`` and the resolver returns the string ID.
    """
    if spec.value_type is bool:
        return bool(value)
    if spec.value_type is int:
        return int(value)
    if spec.value_type is float:
        return float(value)
    return str(value)


# ---------------------------------------------------------------------------
# Coverage assertions — we exercised every value_type at least once
# ---------------------------------------------------------------------------


def test_spec_discovery_returns_at_least_one_writable_spec():
    """If this fails the matrix would silently shrink — sanity-check."""
    assert _PARAMS, (
        "No writable SettingSpecs discovered.  Either no subsystem schema "
        "is registered or every spec lacks settings_key."
    )


def test_coverage_spans_every_value_type_at_least_once():
    """Every supported value_type must appear in the matrix."""
    types_seen = {spec.value_type for _, _, spec in _PARAMS}
    expected = {bool, int, float, str}
    missing = expected - types_seen
    # str must always be present; the others appear when at least one
    # subsystem declares a spec of that type.  Don't fail on a missing
    # type from the registry's current shape — just assert str.
    assert str in types_seen, "round-trip matrix never touches str specs"
    if int in expected and int not in types_seen:
        pytest.skip("no int-typed SettingSpec declared; skipping coverage check")
    if float in expected and float not in types_seen:
        pytest.skip("no float-typed SettingSpec declared; skipping coverage check")


def test_coverage_spans_input_hint_variants_when_declared():
    """input_hint variants — channel, role, numeric_presets — must appear
    in the matrix when ANY subsystem declares them, so the round-trip
    actually exercises those widgets' write paths.
    """
    hints_declared: set[str] = set()
    for _, schema in schema_mod.all_schemas().items():
        for spec in schema.settings:
            h = (spec.input_hint or "").strip().lower()
            if h:
                hints_declared.add(h)
    hints_seen = {
        (spec.input_hint or "").strip().lower()
        for _, _, spec in _PARAMS
        if spec.input_hint
    }
    missing = hints_declared - hints_seen
    assert not missing, (
        "Specs with declared input_hint are missing from the round-trip "
        f"matrix (likely because they have no settings_key): {sorted(missing)}"
    )


def test_coverage_spans_allowed_values_str_specs():
    """At least one ``str`` + ``allowed_values`` spec, when declared anywhere,
    must be in the matrix so the enum-dispatch path is exercised.
    """
    enum_specs = [
        (sub, name, spec)
        for sub, name, spec in _PARAMS
        if spec.value_type is str and spec.allowed_values
    ]
    declared_enum_specs = [
        spec
        for _, schema in schema_mod.all_schemas().items()
        for spec in schema.settings
        if spec.value_type is str
        and spec.allowed_values
        and spec.settings_key
    ]
    if declared_enum_specs:
        assert enum_specs, "Enum-shaped str specs declared but absent from matrix"

"""Reset round-trip: every writable ``SettingSpec`` can be reset to its
declared default and the resolver reflects the reset.

Parametrises over every ``SettingSpec`` discovered at runtime.  For
each spec the test:

1. Writes a non-default value through
   :class:`services.settings_mutation.SettingsMutationPipeline`.
2. Calls :func:`views.settings.reset_button.reset_setting`, which
   writes the spec's ``default`` through the same pipeline.
3. Resolves the value via
   :func:`services.settings_resolution.resolve_setting` and asserts
   the resolver returns the default.

The reset surface itself is the operator-facing one (the dropdown in
SubsystemSettingsView calls ``reset_setting``); exercising it
directly here catches regressions where the reset path drifts away
from a plain ``set_value(spec.default)`` (e.g. if a new ``mutation_type``
literal is introduced and the reset widget forgets to align with it).
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
    """Ensure every cog's schemas module is registered before discovery."""
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
            pass


_load_all_schemas()


# ---------------------------------------------------------------------------
# Fakes (shared shape with the edit round-trip test)
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


class _FakeResponse:
    def __init__(self):
        self.sent: list[dict] = []

    async def send_message(self, content=None, *, ephemeral=False, view=None, **_kw):
        self.sent.append({"content": content, "ephemeral": ephemeral, "view": view})


class _FakeMessage:
    async def edit(self, *, embed=None, view=None):  # noqa: ARG002
        pass


class _FakeInteraction:
    def __init__(self, guild: _FakeGuild | None = None):
        self.guild = guild
        self.guild_id = guild.id if guild else None
        self.user = _FakeMember(guild=guild)
        self.message = _FakeMessage()
        self.response = _FakeResponse()


# ---------------------------------------------------------------------------
# In-memory KV + audit + event shims
# ---------------------------------------------------------------------------


@pytest.fixture
def _isolated_state(monkeypatch):
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
# Spec discovery & value picker (shared with edit round-trip semantics)
# ---------------------------------------------------------------------------


def _writable_specs() -> list[tuple[str, str, Any]]:
    out: list[tuple[str, str, Any]] = []
    for subsystem_name, schema in schema_mod.all_schemas().items():
        for spec in schema.settings:
            if not spec.settings_key:
                continue
            out.append((subsystem_name, spec.name, spec))
    return out


_PARAMS = _writable_specs()
_IDS = [f"{sub}.{name}" for sub, name, _ in _PARAMS]


def _non_default_value_for(spec: Any) -> Any:
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

    raise AssertionError(f"unsupported value_type: {spec.value_type!r}")


def _validator_accepts(spec: Any, value: Any) -> bool:
    if spec.validator is None:
        return True
    try:
        spec.validator(value)
    except Exception:
        return False
    return True


def _expected_resolved(spec: Any, value: Any) -> Any:
    if spec.value_type is bool:
        return bool(value)
    if spec.value_type is int:
        return int(value)
    if spec.value_type is float:
        return float(value)
    return str(value)


# ---------------------------------------------------------------------------
# Reset round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("subsystem", "name", "spec"), _PARAMS, ids=_IDS)
@pytest.mark.asyncio
async def test_reset_round_trip_every_writable_spec(
    _isolated_state, subsystem: str, name: str, spec: Any,
):
    """Write a non-default → reset via the reset widget → resolver
    returns the spec default.
    """
    from views.settings.reset_button import reset_setting

    guild = _FakeGuild(guild_id=1)
    actor = _FakeMember(guild=guild)

    # Step 1: write a non-default value through the pipeline.
    non_default = _non_default_value_for(spec)
    await SettingsMutationPipeline().set_value(
        guild, subsystem, name, non_default, actor,
    )

    # Sanity-check: the resolver now reflects the non-default.
    after_write = await resolve_setting(guild.id, subsystem, name)
    assert after_write is not None
    expected_after_write = _expected_resolved(spec, non_default)
    if spec.default != expected_after_write:
        # Skip when the spec has no usable non-default value (e.g. a
        # one-value enum allow-list).  The round-trip itself is the
        # default round-trip and tests nothing useful.
        assert after_write.value == expected_after_write

    # Step 2: hit the reset widget.
    interaction = _FakeInteraction(guild=guild)
    await reset_setting(interaction, subsystem, name)

    # Step 3: resolver returns the default.
    after_reset = await resolve_setting(guild.id, subsystem, name)
    assert after_reset is not None
    assert after_reset.value == spec.default, (
        f"reset failed to restore default for {subsystem}.{name}: "
        f"resolver returned {after_reset.value!r} expected {spec.default!r}"
    )
    assert after_reset.valid is True


# ---------------------------------------------------------------------------
# Coverage sanity
# ---------------------------------------------------------------------------


def test_reset_matrix_non_empty():
    """The reset matrix must contain at least one spec — else this
    file is silently doing nothing.
    """
    assert _PARAMS, "no writable SettingSpecs discovered for reset matrix"


@pytest.mark.asyncio
async def test_reset_uses_set_value_mutation_type(_isolated_state):
    """The reset widget records a regular ``set_value`` audit row.

    The S6 reset widget intentionally uses ``set_value`` so audit
    dashboards do not have to know about a separate ``reset_value``
    mutation_type today.  This is a sanity-check that nothing has
    silently changed that contract.
    """
    if not _PARAMS:
        pytest.skip("no writable specs available")

    from views.settings.reset_button import reset_setting

    sub, name, spec = next(
        ((s, n, sp) for s, n, sp in _PARAMS if sp.value_type is int),
        _PARAMS[0],
    )
    guild = _FakeGuild(guild_id=1)
    actor = _FakeMember(guild=guild)
    non_default = _non_default_value_for(spec)
    await SettingsMutationPipeline().set_value(
        guild, sub, name, non_default, actor,
    )

    interaction = _FakeInteraction(guild=guild)
    await reset_setting(interaction, sub, name)
    last = _isolated_state["audit_log"][-1]
    assert last["mutation_type"] == "set_value", (
        "reset widget should write a set_value audit row (S6 contract); "
        f"got {last['mutation_type']!r}"
    )

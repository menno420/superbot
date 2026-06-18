"""Unit tests for the S6 scalar edit / reset widgets.

Covers each widget's mutation-pipeline path independently of the
SubsystemSettingsView dispatch (which is tested separately by
test_settings_cog_edit_routes.py): bool toggle, int / float modal,
free-form text modal, enum-select view, reset button.
"""

from __future__ import annotations

import pytest

from core.runtime import guild_config
from core.runtime import subsystem_schema as schema_mod
from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema
from services import settings_mutation as sm_mod
from utils import db as db_pkg
from utils.db import settings as settings_db
from utils.db import settings_audit as audit_db
from views.settings.edit_boolean import toggle_setting
from views.settings.edit_enum import build_enum_select_view
from views.settings.edit_number import NumberSettingModal
from views.settings.edit_text import TextSettingModal
from views.settings.reset_button import reset_setting

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


class _FakeResponse:
    def __init__(self):
        self.sent: list[dict] = []

    async def send_message(self, content=None, *, ephemeral=False, view=None, **_kw):
        self.sent.append(
            {"content": content, "ephemeral": ephemeral, "view": view},
        )

    async def send_modal(self, modal):
        self.sent.append({"modal": modal})


class _FakeMessage:
    def __init__(self):
        self.edited: list[dict] = []

    async def edit(self, *, embed=None, view=None):
        self.edited.append({"embed": embed, "view": view})


class _FakeInteraction:
    def __init__(self, guild: _FakeGuild | None = None):
        self.guild = guild
        self.guild_id = guild.id if guild else None
        self.user = _FakeMember(guild=guild)
        self.message = _FakeMessage()
        self.response = _FakeResponse()


# ---------------------------------------------------------------------------
# Fixtures — shared in-memory KV + audit stubs across all edit widgets
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch):
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    guild_config._reset_for_tests()
    sm_mod._reset_for_tests = getattr(sm_mod, "_reset_for_tests", lambda: None)

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

    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    guild_config._reset_for_tests()


# ---------------------------------------------------------------------------
# Boolean toggle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_boolean_toggle_inverts_value(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="dm_on_action",
                    value_type=bool,
                    default=False,
                    settings_key="MOD_DM_ON_ACTION",
                ),
            ),
        ),
    )
    interaction = _FakeInteraction(guild=_FakeGuild())
    await toggle_setting(interaction, "moderation", "dm_on_action")
    assert _isolated_state["audit_log"][-1]["new_value_raw"] == "true"
    # Confirmation sent.
    assert any("Toggled" in (s.get("content") or "") for s in interaction.response.sent)


@pytest.mark.asyncio
async def test_boolean_toggle_dm_invocation_rejected():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="dm_on_action",
                    value_type=bool,
                    default=False,
                    settings_key="MOD_DM_ON_ACTION",
                ),
            ),
        ),
    )
    interaction = _FakeInteraction(guild=None)
    await toggle_setting(interaction, "moderation", "dm_on_action")
    assert any(
        "guild" in (s.get("content") or "").lower() for s in interaction.response.sent
    )


# ---------------------------------------------------------------------------
# Number modal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_number_modal_writes_via_pipeline(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    modal = NumberSettingModal(
        subsystem="moderation",
        setting_name="warn_threshold",
        value_type=int,
        current_value=3,
        default_value=3,
    )
    modal.input = type("Stub", (), {"value": "5"})()
    interaction = _FakeInteraction(guild=_FakeGuild())
    await modal.on_submit(interaction)
    assert _isolated_state["audit_log"][-1]["new_value_raw"] == "5"
    assert _isolated_state["audit_log"][-1]["prev_value_raw"] is None
    assert any("Updated" in (s.get("content") or "") for s in interaction.response.sent)


@pytest.mark.asyncio
async def test_number_modal_handles_coercion_failure_gracefully():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    modal = NumberSettingModal(
        subsystem="moderation",
        setting_name="warn_threshold",
        value_type=int,
        current_value=3,
        default_value=3,
    )
    modal.input = type("Stub", (), {"value": "abc"})()  # not coercible
    interaction = _FakeInteraction(guild=_FakeGuild())
    await modal.on_submit(interaction)
    # No audit row written.
    # Pipeline raises SettingsCoercionError → modal surfaces it ephemerally.
    last = interaction.response.sent[-1]
    assert "SettingsCoercionError" in (last.get("content") or "")


# ---------------------------------------------------------------------------
# Text modal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_text_modal_writes_string_value(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="dm_template",
                    value_type=str,
                    default="Hello",
                    settings_key="DM_TEMPLATE",
                ),
            ),
        ),
    )
    modal = TextSettingModal(
        subsystem="moderation",
        setting_name="dm_template",
        current_value="Hello",
        default_value="Hello",
    )
    modal.input = type("Stub", (), {"value": "Greetings, please review."})()
    interaction = _FakeInteraction(guild=_FakeGuild())
    await modal.on_submit(interaction)
    assert (
        _isolated_state["audit_log"][-1]["new_value_raw"] == "Greetings, please review."
    )


# ---------------------------------------------------------------------------
# Enum select view
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enum_select_view_writes_chosen_value(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="cleanup",
            settings=(
                SettingSpec(
                    name="strictness",
                    value_type=str,
                    default="normal",
                    settings_key="CLEANUP_STRICTNESS",
                    allowed_values=("off", "light", "normal", "strict"),
                ),
            ),
        ),
    )
    view = build_enum_select_view(
        _FakeMember(guild=_FakeGuild()),
        "cleanup",
        "strictness",
        ("off", "light", "normal", "strict"),
        "normal",
    )
    import discord

    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    select._values = ["strict"]
    interaction = _FakeInteraction(guild=_FakeGuild())
    await select.callback(interaction)
    assert _isolated_state["audit_log"][-1]["new_value_raw"] == "strict"


def test_enum_select_view_marks_current_value():
    view = build_enum_select_view(
        _FakeMember(guild=_FakeGuild()),
        "cleanup",
        "strictness",
        ("off", "light", "normal", "strict"),
        "normal",
    )
    import discord

    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    defaults = [opt for opt in select.options if opt.default]
    assert len(defaults) == 1
    assert defaults[0].value == "normal"


# ---------------------------------------------------------------------------
# Reset button
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reset_button_writes_default_value(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    _isolated_state["kv"][(1, "WARN_THRESHOLD")] = "9"
    interaction = _FakeInteraction(guild=_FakeGuild())
    await reset_setting(interaction, "moderation", "warn_threshold")
    last_audit = _isolated_state["audit_log"][-1]
    assert last_audit["new_value_raw"] == "3"
    assert last_audit["prev_value_raw"] == "9"
    assert any("Reset" in (s.get("content") or "") for s in interaction.response.sent)


@pytest.mark.asyncio
async def test_reset_button_dm_invocation_rejected():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    interaction = _FakeInteraction(guild=None)
    await reset_setting(interaction, "moderation", "warn_threshold")
    assert any(
        "guild" in (s.get("content") or "").lower() for s in interaction.response.sent
    )


@pytest.mark.asyncio
async def test_reset_button_unknown_setting_rejected():
    interaction = _FakeInteraction(guild=_FakeGuild())
    await reset_setting(interaction, "moderation", "no_such_setting")
    last = interaction.response.sent[-1]
    assert "Unknown setting" in (last.get("content") or "")


# ---------------------------------------------------------------------------
# Event + cache invalidation observable end-to-end
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_smoke_warn_threshold_3_to_5_observable(_isolated_state):
    """User's smoke goal: flip moderation.warn_threshold 3→5 via modal;
    audit row + event + cache invalidation observable.
    """
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    modal = NumberSettingModal(
        subsystem="moderation",
        setting_name="warn_threshold",
        value_type=int,
        current_value=3,
        default_value=3,
    )
    modal.input = type("Stub", (), {"value": "5"})()
    interaction = _FakeInteraction(guild=_FakeGuild())
    await modal.on_submit(interaction)
    # Audit row observable.
    assert _isolated_state["audit_log"][-1] == {
        "guild_id": 1,
        "subsystem": "moderation",
        "name": "warn_threshold",
        "settings_key": "WARN_THRESHOLD",
        "prev_value_raw": None,
        "new_value_raw": "5",
        "actor_id": 7,
        "actor_type": "user",
        "mutation_id": _isolated_state["audit_log"][-1]["mutation_id"],
        "mutation_type": "set_value",
    }
    # Event observable.
    assert any(
        ev["event"] == "settings.changed" and ev["new_value_raw"] == "5"
        for ev in _isolated_state["emitted"]
    )
    # Cache invalidation observable (subsequent resolve sees 5).
    from services.settings_resolution import resolve_setting

    res = await resolve_setting(1, "moderation", "warn_threshold")
    assert res.value == 5
    assert res.provenance == "legacy_kv"

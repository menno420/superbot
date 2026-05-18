"""Unit tests for the four read-only diagnostic sub-panels — S5.

Covers NeedsSetupView / InvalidSettingsView / MissingBindingsView /
RecentChangesView: their embed shape, empty-state behaviour, and
the "Back to Hub" navigation button.
"""

from __future__ import annotations

import discord
import pytest

from core.runtime import settings_registry
from core.runtime import subsystem_schema as schema_mod
from core.runtime.resource_specs import (
    ProvisioningHint,
    ProvisioningPriority,
    ResourceKind,
    ResourceRequirement,
)
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SettingSpec,
    SubsystemSchema,
)
from utils.db import settings as settings_db
from views.settings.audit_view import RecentChangesView, build_audit_embed
from views.settings.invalid_settings import (
    InvalidSettingsView,
    build_invalid_embed,
)
from views.settings.missing_bindings import (
    MissingBindingsView,
    build_missing_bindings_embed,
)
from views.settings.needs_setup import NeedsSetupView, build_needs_setup_embed


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch):
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    settings_registry._reset_for_tests()
    from core.runtime import guild_config

    guild_config._reset_for_tests()
    _kv: dict[tuple[int, str], str] = {}

    async def _fake_get_setting(
        guild_id: int,
        key: str,
        default: str = "",
    ) -> str:
        return _kv.get((guild_id, key), default)

    monkeypatch.setattr(settings_db, "get_setting", _fake_get_setting)
    from utils import db as db_pkg

    monkeypatch.setattr(db_pkg, "get_setting", _fake_get_setting)
    yield {"kv": _kv}
    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    settings_registry._reset_for_tests()
    guild_config._reset_for_tests()


class _FakeInteraction:
    def __init__(self, guild_id: int | None = 1):
        self.guild_id = guild_id


def _author():
    class _M:
        id = 1

    return _M()


# ---------------------------------------------------------------------------
# Needs setup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_needs_setup_empty_state():
    embed = await build_needs_setup_embed(_FakeInteraction())
    assert "Needs setup" in (embed.title or "")
    result = next(f.value for f in embed.fields if f.name == "Result")
    assert "no subsystem" in result.lower()


@pytest.mark.asyncio
async def test_needs_setup_lists_required_bindings_and_resources():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            bindings=(
                BindingSpec(
                    name="mod_log",
                    kind=BindingKind.CHANNEL,
                    required=True,
                    hint="x",
                    capability_required="moderation.log.view",
                ),
            ),
            resource_requirements=(
                ResourceRequirement(
                    kind=ResourceKind.CHANNEL,
                    intent="mod_log",
                    provisioning=ProvisioningHint(
                        priority=ProvisioningPriority.REQUIRED,
                        suggested_name="mod-logs",
                    ),
                    binding_name="mod_log",
                ),
            ),
        ),
    )
    embed = await build_needs_setup_embed(_FakeInteraction())
    field_names = [f.name for f in embed.fields]
    binding_field = next(n for n in field_names if "Required bindings" in n)
    resource_field = next(n for n in field_names if "Required resources" in n)
    assert "moderation" in next(
        f.value for f in embed.fields if f.name == binding_field
    )
    assert "moderation" in next(
        f.value for f in embed.fields if f.name == resource_field
    )


def test_needs_setup_view_has_back_button():
    view = NeedsSetupView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 1
    assert "Back" in (buttons[0].label or "")


# ---------------------------------------------------------------------------
# Invalid settings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_settings_dm_invocation_shows_helpful_message():
    embed = await build_invalid_embed(_FakeInteraction(guild_id=None))
    result = next(f.value for f in embed.fields if f.name == "Result")
    assert "guild" in result.lower()


@pytest.mark.asyncio
async def test_invalid_settings_no_violations():
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(
                SettingSpec(
                    name="xp_min",
                    value_type=int,
                    default=1,
                    settings_key="XP_MIN",
                ),
            ),
        ),
    )
    embed = await build_invalid_embed(_FakeInteraction(guild_id=1))
    result = next(f.value for f in embed.fields if f.name == "Result")
    assert "no invalid" in result.lower()


@pytest.mark.asyncio
async def test_invalid_settings_flags_uncoerced_kv_row(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(
                SettingSpec(
                    name="xp_min",
                    value_type=int,
                    default=1,
                    settings_key="XP_MIN",
                ),
            ),
        ),
    )
    _isolated_state["kv"][(1, "XP_MIN")] = "garbage"
    embed = await build_invalid_embed(_FakeInteraction(guild_id=1))
    field_names = [f.name for f in embed.fields]
    invalid_field = next(n for n in field_names if "Invalid settings" in n)
    block = next(f.value for f in embed.fields if f.name == invalid_field)
    assert "xp.xp_min" in block
    assert "garbage" in block


def test_invalid_view_has_back_button():
    view = InvalidSettingsView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 1


# ---------------------------------------------------------------------------
# Missing bindings — DM and no-bindings paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_bindings_dm_invocation_shows_helpful_message():
    embed = await build_missing_bindings_embed(_FakeInteraction(guild_id=None))
    result = next(f.value for f in embed.fields if f.name == "Result")
    assert "guild" in result.lower()


def test_missing_bindings_view_has_back_button():
    view = MissingBindingsView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 1


# ---------------------------------------------------------------------------
# Recent changes (audit view)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_view_dm_invocation_shows_helpful_message():
    embed = await build_audit_embed(_FakeInteraction(guild_id=None))
    result = next(f.value for f in embed.fields if f.name == "Result")
    assert "guild" in result.lower()


@pytest.mark.asyncio
async def test_audit_view_handles_missing_table_gracefully(monkeypatch):
    """When the audit table query raises (e.g. migration not applied
    yet), the embed surfaces a helpful message rather than blowing up.
    """
    from utils.db import settings_audit

    async def _raises(*_a, **_kw):
        raise RuntimeError('relation "settings_mutation_audit" does not exist')

    monkeypatch.setattr(settings_audit, "list_recent_for_guild", _raises)
    embed = await build_audit_embed(_FakeInteraction(guild_id=1))
    block = next(f.value for f in embed.fields if f.name == "Audit table")
    assert "Could not read" in block


@pytest.mark.asyncio
async def test_audit_view_empty_result(monkeypatch):
    from utils.db import settings_audit

    async def _empty(*_a, **_kw):
        return []

    monkeypatch.setattr(settings_audit, "list_recent_for_guild", _empty)
    embed = await build_audit_embed(_FakeInteraction(guild_id=1))
    result = next(f.value for f in embed.fields if f.name == "Result")
    assert "no audit" in result.lower()


@pytest.mark.asyncio
async def test_audit_view_renders_recent_rows(monkeypatch):
    from datetime import datetime, timezone

    from utils.db import settings_audit

    async def _two_rows(*_a, **_kw):
        return [
            {
                "id": 2,
                "mutation_id": "abc",
                "guild_id": 1,
                "subsystem": "xp",
                "name": "xp_min",
                "settings_key": "XP_MIN",
                "prev_value_raw": "5",
                "new_value_raw": "10",
                "actor_id": 99,
                "actor_type": "user",
                "mutation_type": "set_value",
                "at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            },
        ]

    monkeypatch.setattr(settings_audit, "list_recent_for_guild", _two_rows)
    embed = await build_audit_embed(_FakeInteraction(guild_id=1))
    field = next(f for f in embed.fields if "change" in f.name.lower())
    assert "xp.xp_min" in field.value
    assert "`'10'`" in field.value or "10" in field.value


def test_recent_changes_view_has_back_button():
    view = RecentChangesView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 1

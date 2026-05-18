"""Unit tests for the per-subsystem read-only drill-down view — S5."""

from __future__ import annotations

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
from views.settings.subsystem_view import (
    SubsystemSettingsView,
    build_subsystem_embed,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch):
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    settings_registry._reset_for_tests()

    # In-memory KV.  Tests pre-populate to drive resolver output.
    _kv: dict[tuple[int, str], str] = {}

    async def _fake_get_setting(
        guild_id: int,
        key: str,
        default: str = "",
    ) -> str:
        return _kv.get((guild_id, key), default)

    monkeypatch.setattr(settings_db, "get_setting", _fake_get_setting)
    # Also patch the re-export at utils.db so the typed accessor sees it.
    from utils import db as db_pkg

    monkeypatch.setattr(db_pkg, "get_setting", _fake_get_setting)

    # Reset guild_config cache between tests so resolutions reflect _kv.
    from core.runtime import guild_config

    guild_config._reset_for_tests()

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
# Embed shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embed_titles_with_subsystem_emoji_and_display_name():
    embed = await build_subsystem_embed(_FakeInteraction(), "moderation")
    # The moderation subsystem's emoji is 🔨 per SUBSYSTEMS.
    assert "🔨" in (embed.title or "")
    assert "Moderation" in (embed.title or "")


@pytest.mark.asyncio
async def test_embed_shows_visibility_tier_in_description():
    embed = await build_subsystem_embed(_FakeInteraction(), "moderation")
    assert "moderator" in (embed.description or "")


@pytest.mark.asyncio
async def test_embed_lists_scalar_settings_with_provenance(_isolated_state):
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
    _isolated_state["kv"][(1, "WARN_THRESHOLD")] = "5"
    embed = await build_subsystem_embed(_FakeInteraction(guild_id=1), "moderation")
    field_names = [f.name for f in embed.fields]
    assert "Scalar settings" in field_names
    block = next(f.value for f in embed.fields if f.name == "Scalar settings")
    # legacy_kv provenance + the coerced value 5 should appear.
    assert "warn_threshold" in block
    assert "legacy_kv" in block
    assert "valid" in block.lower()


@pytest.mark.asyncio
async def test_embed_lists_bindings_with_kind_and_required(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="logging",
            bindings=(
                BindingSpec(
                    name="mod_channel",
                    kind=BindingKind.CHANNEL,
                    required=False,
                    hint="The mod log channel.",
                    capability_required="logging.settings.configure",
                ),
            ),
        ),
    )
    embed = await build_subsystem_embed(_FakeInteraction(), "moderation")
    # "logging" subsystem has the binding; but if we use "moderation" no field
    # is shown.  Re-run with logging subsystem:
    embed = await build_subsystem_embed(_FakeInteraction(), "logging")
    # logging isn't in SUBSYSTEMS so the embed will still render — bindings
    # field should still appear because the schema is registered for the key
    # "logging".  This validates the binding renderer is data-driven.
    field_names = [f.name for f in embed.fields]
    assert "Bindings" in field_names
    block = next(f.value for f in embed.fields if f.name == "Bindings")
    assert "mod_channel" in block
    assert "channel" in block
    assert "optional" in block


@pytest.mark.asyncio
async def test_embed_lists_provisionable_resources(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            bindings=(
                BindingSpec(
                    name="mod_log",
                    kind=BindingKind.CHANNEL,
                    required=False,
                    hint="x",
                    capability_required="moderation.log.view",
                ),
            ),
            resource_requirements=(
                ResourceRequirement(
                    kind=ResourceKind.CHANNEL,
                    intent="mod_log",
                    provisioning=ProvisioningHint(
                        priority=ProvisioningPriority.RECOMMENDED,
                        suggested_name="mod-logs",
                    ),
                    binding_name="mod_log",
                ),
            ),
        ),
    )
    embed = await build_subsystem_embed(_FakeInteraction(), "moderation")
    field_names = [f.name for f in embed.fields]
    assert "Provisionable resources" in field_names
    block = next(f.value for f in embed.fields if f.name == "Provisionable resources")
    assert "mod_log" in block
    assert "mod-logs" in block
    assert "recommended" in block


@pytest.mark.asyncio
async def test_embed_lists_existing_command_panels():
    embed = await build_subsystem_embed(_FakeInteraction(), "moderation")
    field_names = [f.name for f in embed.fields]
    assert "Existing command panels" in field_names
    block = next(f.value for f in embed.fields if f.name == "Existing command panels")
    # SUBSYSTEMS["moderation"].entry_points includes "modmenu".
    assert "modmenu" in block


@pytest.mark.asyncio
async def test_embed_dm_invocation_shows_no_guild_context():
    """guild_id=None (DM) renders schema-declaration shape without
    attempting to resolve per-guild values."""
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(SettingSpec(name="x", value_type=int, default=42),),
        ),
    )
    embed = await build_subsystem_embed(_FakeInteraction(guild_id=None), "moderation")
    block = next(f.value for f in embed.fields if f.name == "Scalar settings")
    assert "no guild context" in block.lower()


@pytest.mark.asyncio
async def test_embed_for_subsystem_with_no_schema_is_sparse():
    """A subsystem that exists in SUBSYSTEMS but has no schema renders
    an empty-state embed with the title and no scalar-settings rows."""
    embed = await build_subsystem_embed(_FakeInteraction(), "blackjack")
    title = embed.title or ""
    assert "Blackjack" in title
    block = next(f.value for f in embed.fields if f.name == "Scalar settings")
    assert "none declared" in block.lower()


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_subsystem_view_has_back_button():
    view = SubsystemSettingsView(_author(), "moderation")
    import discord

    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(buttons) == 1
    assert "Back" in (buttons[0].label or "")


def test_subsystem_view_carries_subsystem_key():
    view = SubsystemSettingsView(_author(), "moderation")
    assert view.subsystem == "moderation"


# ---------------------------------------------------------------------------
# Read-only invariant — view module surface has no mutation imports
# ---------------------------------------------------------------------------


def test_subsystem_view_does_not_import_mutation_pipelines():
    """The view module must not import any mutation surface.  Pinned
    here as a fast sanity check; the broader AST invariant lives in
    tests/unit/invariants/test_settings_cog_read_only.py."""
    import ast
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[3]
        / "disbot"
        / "views"
        / "settings"
        / "subsystem_view.py"
    )
    text = path.read_text()
    tree = ast.parse(text)
    forbidden = (
        "settings_mutation",
        "binding_mutation",
        "resource_provisioning",
        "governance.writes",
        "participation_mutation",
    )
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for needle in forbidden:
                if needle in node.module:
                    offenders.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                for needle in forbidden:
                    if needle in alias.name:
                        offenders.append(alias.name)
    assert not offenders, f"subsystem_view imports mutation surfaces: {offenders}"

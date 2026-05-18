"""Unit tests for services.customization_catalogue — S2.

Covers builder behavior, panel detection priority, findings buckets,
immutability, query API, the diagnostics provider, and the
``@panel_command`` decorator.
"""

from __future__ import annotations

import datetime

import pytest

from core.runtime import command_surface_ledger as ledger_mod
from core.runtime import settings_registry as registry_mod
from core.runtime import subsystem_schema as schema_mod
from core.runtime.command_surface_ledger import (
    CommandSurfaceEntry,
    CommandSurfaceLedger,
    LedgerFindings,
)
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SettingSpec,
    SubsystemSchema,
)
from services import customization_catalogue as cat_mod
from services.customization_catalogue import (
    KNOWN_PANEL_COMMANDS,
    CustomizationCatalogue,
    CustomizationEntry,
    CustomizationFindings,
    PanelDeclaration,
    build_catalogue,
    get_cached_catalogue,
    panel_command,
)


# ---------------------------------------------------------------------------
# Fixtures — snapshot live module state around each test to stay isolated.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_state():
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    registry_mod._reset_for_tests()
    ledger_mod._reset_for_tests()
    cat_mod._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    registry_mod._reset_for_tests()
    ledger_mod._reset_for_tests()
    cat_mod._reset_for_tests()


def _make_ledger(*entries: CommandSurfaceEntry) -> CommandSurfaceLedger:
    return CommandSurfaceLedger(
        version=1,
        built_at=datetime.datetime.now(tz=datetime.timezone.utc),
        entries=tuple(entries),
        router_prefixes=(),
        findings=LedgerFindings(),
    )


def _entry(name: str, cog_name: str, subsystem: str | None) -> CommandSurfaceEntry:
    """Build a CommandSurfaceEntry with the visibility_tier required field."""
    return CommandSurfaceEntry(
        name=name,
        cog_name=cog_name,
        subsystem=subsystem,
        visibility_tier=None,
    )


def _inject_ledger(ledger: CommandSurfaceLedger) -> None:
    ledger_mod._CACHED = ledger


class _FakeCog:
    """Minimal stand-in for a Discord cog with optional help-hook + commands."""

    def __init__(
        self,
        class_name: str,
        *,
        has_help_hook: bool = False,
        commands_: tuple[object, ...] = (),
    ) -> None:
        self.__class__ = type(class_name, (object,), {})
        if has_help_hook:
            async def build_help_menu_view(_self, _interaction):  # noqa: ARG001
                return None, None

            self.build_help_menu_view = build_help_menu_view.__get__(  # type: ignore[attr-defined]
                self,
                self.__class__,
            )
        self._commands = commands_

    def get_commands(self):  # pragma: no cover - parity with discord.py
        return self._commands


class _FakeCommand:
    """Minimal stand-in for a discord.py Command."""

    def __init__(self, name: str, *, extras: dict | None = None, cog=None) -> None:
        self.name = name
        self.qualified_name = name
        self.extras = extras if extras is not None else {}
        self.cog = cog
        self.aliases: tuple[str, ...] = ()


class _FakeBot:
    """Minimal stand-in for a commands.Bot with .cogs and .walk_commands."""

    def __init__(
        self,
        cogs: dict[str, _FakeCog] | None = None,
        commands_: tuple[_FakeCommand, ...] = (),
    ) -> None:
        self.cogs = cogs or {}
        self._commands = commands_

    def walk_commands(self):
        yield from self._commands


# ---------------------------------------------------------------------------
# Empty inputs
# ---------------------------------------------------------------------------


def test_build_catalogue_returns_frozen_snapshot():
    cat = build_catalogue()
    assert isinstance(cat, CustomizationCatalogue)
    assert cat.version == 1
    assert isinstance(cat.built_at, datetime.datetime)


def test_build_catalogue_covers_every_subsystem():
    """Even with no ledger/registry/schemas, every subsystem gets an entry."""
    from utils.subsystem_registry import SUBSYSTEMS

    cat = build_catalogue()
    assert {e.subsystem for e in cat.entries} == set(SUBSYSTEMS)


def test_get_cached_catalogue_returns_none_before_first_build():
    assert get_cached_catalogue() is None


def test_get_cached_catalogue_returns_last_built():
    cat = build_catalogue()
    assert get_cached_catalogue() is cat


# ---------------------------------------------------------------------------
# Composition with the existing primitives
# ---------------------------------------------------------------------------


def test_entries_carry_schema_signal_from_subsystem_schema():
    schema_mod.register(
        SubsystemSchema(
            subsystem="economy",
            settings=(SettingSpec(name="daily", value_type=int, default=86400),),
        ),
    )
    cat = build_catalogue()
    entry = cat.get("economy")
    assert entry is not None
    assert entry.has_schema is True
    assert entry.setting_names == ("daily",)
    # Subsystems without schemas keep has_schema=False.
    assert cat.get("blackjack").has_schema is False  # type: ignore[union-attr]


def test_setting_names_prefer_registry_over_schema_when_built():
    """When SettingsRegistry has been built, the catalogue uses it as the
    authoritative source for setting names."""
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(
                SettingSpec(name="xp_min", value_type=int, default=1),
                SettingSpec(name="xp_max", value_type=int, default=10),
            ),
        ),
    )
    registry_mod.build_registry()
    cat = build_catalogue()
    entry = cat.get("xp")
    assert entry is not None
    assert set(entry.setting_names) == {"xp_min", "xp_max"}


def test_bindings_and_resource_intents_carried_from_schema():
    from core.runtime.resource_specs import (
        ProvisioningHint,
        ProvisioningPriority,
        ResourceKind,
        ResourceRequirement,
    )

    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            bindings=(
                BindingSpec(
                    name="mod_log",
                    kind=BindingKind.CHANNEL,
                    required=False,
                    hint="mod log target",
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
    cat = build_catalogue()
    entry = cat.get("moderation")
    assert entry is not None
    assert entry.binding_names == ("mod_log",)
    assert entry.resource_intents == ("mod_log",)


def test_command_count_reflects_ledger():
    _inject_ledger(
        _make_ledger(
            _entry("warn", "ModerationCog", "moderation"),
            _entry("modmenu", "ModerationCog", "moderation"),
            _entry("kick", "ModerationCog", "moderation"),
        ),
    )
    cat = build_catalogue()
    entry = cat.get("moderation")
    assert entry is not None
    assert entry.command_count == 3


# ---------------------------------------------------------------------------
# Panel detection — priority order and source labels
# ---------------------------------------------------------------------------


def test_known_list_panel_detected_when_command_exists_in_ledger():
    _inject_ledger(
        _make_ledger(
            _entry("modmenu", "ModerationCog", "moderation"),
        ),
    )
    cat = build_catalogue()
    entry = cat.get("moderation")
    assert entry is not None
    sources = [p.source for p in entry.panels]
    assert "known_list" in sources
    assert any(p.command == "modmenu" for p in entry.panels)


def test_known_list_panel_skipped_when_command_absent_from_ledger():
    _inject_ledger(_make_ledger())  # empty ledger
    cat = build_catalogue()
    entry = cat.get("moderation")
    assert entry is not None
    # No known list match since "modmenu" isn't in the ledger.
    assert not any(p.source == "known_list" for p in entry.panels)


def test_help_hook_synthetic_panel_added_when_cog_implements_hook():
    cog = _FakeCog("ModerationCog", has_help_hook=True)
    bot = _FakeBot(cogs={"ModerationCog": cog})
    cat = build_catalogue(bot=bot)
    entry = cat.get("moderation")
    assert entry is not None
    assert entry.has_help_hook is True
    assert any(
        p.source == "help_hook" and p.command == "<build_help_menu_view>"
        for p in entry.panels
    )


def test_help_hook_skipped_when_cog_lacks_hook():
    cog = _FakeCog("ModerationCog", has_help_hook=False)
    bot = _FakeBot(cogs={"ModerationCog": cog})
    cat = build_catalogue(bot=bot)
    entry = cat.get("moderation")
    assert entry is not None
    assert entry.has_help_hook is False


def test_ledger_extras_detected_for_panel_command_decorated_command():
    cog = _FakeCog("ModerationCog")
    cmd = _FakeCommand("modmenu", extras={"panel": True}, cog=cog)
    bot = _FakeBot(cogs={"ModerationCog": cog}, commands_=(cmd,))
    _inject_ledger(
        _make_ledger(
            _entry("modmenu", "ModerationCog", "moderation"),
        ),
    )
    cat = build_catalogue(bot=bot)
    entry = cat.get("moderation")
    assert entry is not None
    # Ledger_extras outranks the known_list — same command, higher priority.
    panel_for_cmd = [p for p in entry.panels if p.command == "modmenu"]
    assert len(panel_for_cmd) == 1
    assert panel_for_cmd[0].source == "ledger_extras"


def test_regex_fallback_for_menu_commands_not_in_known_list():
    """A *menu command not in KNOWN_PANEL_COMMANDS triggers regex_fallback
    and is recorded in regex_inferred_panels findings."""
    _inject_ledger(
        _make_ledger(
            # mining is in known list but use a different name to exercise regex
            _entry("oremenu", "MiningCog", "mining"),
        ),
    )
    cat = build_catalogue()
    entry = cat.get("mining")
    assert entry is not None
    sources = [p.source for p in entry.panels]
    assert "regex_fallback" in sources
    assert "mining.oremenu" in cat.findings.regex_inferred_panels


def test_detection_priority_orders_sources_correctly():
    """When the same command is eligible under multiple sources, the
    higher-priority source wins and is recorded only once."""
    cog = _FakeCog("ModerationCog", has_help_hook=True)
    # Decorated panel command — ledger_extras source
    cmd = _FakeCommand("modmenu", extras={"panel": True}, cog=cog)
    bot = _FakeBot(cogs={"ModerationCog": cog}, commands_=(cmd,))
    _inject_ledger(
        _make_ledger(
            _entry("modmenu", "ModerationCog", "moderation"),
        ),
    )
    cat = build_catalogue(bot=bot)
    entry = cat.get("moderation")
    assert entry is not None
    # modmenu should appear exactly once with the highest-priority source.
    same_cmd_panels = [p for p in entry.panels if p.command == "modmenu"]
    assert len(same_cmd_panels) == 1
    assert same_cmd_panels[0].source == "ledger_extras"
    # The help_hook synthetic panel is a different command name and still
    # appears alongside.
    assert any(
        p.source == "help_hook" and p.command == "<build_help_menu_view>"
        for p in entry.panels
    )


def test_regex_fallback_does_not_override_known_list():
    """A *menu command that also appears in KNOWN_PANEL_COMMANDS is
    classified as known_list, not regex_fallback."""
    _inject_ledger(
        _make_ledger(
            _entry("xpmenu", "XPCog", "xp"),
        ),
    )
    cat = build_catalogue()
    entry = cat.get("xp")
    assert entry is not None
    panel_for_cmd = [p for p in entry.panels if p.command == "xpmenu"]
    assert len(panel_for_cmd) == 1
    assert panel_for_cmd[0].source == "known_list"
    assert "xp.xpmenu" not in cat.findings.regex_inferred_panels


def test_bot_none_skips_help_hook_signal():
    """When bot is None, missing_help_hook stays empty (no information)."""
    cat = build_catalogue(bot=None)
    assert cat.findings.subsystems_missing_help_hook == ()
    assert all(e.has_help_hook is False for e in cat.entries)


def test_bot_with_help_hook_populates_missing_help_hook_finding():
    """When some cogs have the hook and others don't, the missing-hook
    finding lists the ones without it."""
    cog_with = _FakeCog("ModerationCog", has_help_hook=True)
    cog_without = _FakeCog("EconomyCog", has_help_hook=False)
    bot = _FakeBot(cogs={"ModerationCog": cog_with, "EconomyCog": cog_without})
    cat = build_catalogue(bot=bot)
    missing = cat.findings.subsystems_missing_help_hook
    assert "moderation" not in missing
    assert "economy" in missing


# ---------------------------------------------------------------------------
# Findings buckets
# ---------------------------------------------------------------------------


def test_subsystems_missing_panel_finding_populated():
    """No ledger entries + no help hooks → every subsystem missing a panel."""
    from utils.subsystem_registry import SUBSYSTEMS

    cat = build_catalogue(bot=None)
    assert set(cat.findings.subsystems_missing_panel) == set(SUBSYSTEMS)


def test_subsystems_missing_schema_finding_populated():
    """No schemas registered → every subsystem missing a schema."""
    from utils.subsystem_registry import SUBSYSTEMS

    cat = build_catalogue()
    assert set(cat.findings.subsystems_missing_schema) == set(SUBSYSTEMS)


def test_panels_without_settings_finding_populated():
    """A subsystem with a panel but no settings/bindings/resources is
    surfaced — its panel doesn't link to any customization data."""
    _inject_ledger(
        _make_ledger(
            _entry("adminmenu", "AdminCog", "admin"),
        ),
    )
    cat = build_catalogue()
    # admin has no schema → panels_without_settings flagged.
    assert any(
        s.startswith("admin.") for s in cat.findings.panels_without_settings
    )


def test_settings_without_panel_finding_populated():
    """A subsystem with settings but no detected panels is surfaced."""
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(SettingSpec(name="xp_min", value_type=int, default=1),),
        ),
    )
    # No ledger, no bot — XP has no panel detected.
    cat = build_catalogue(bot=None)
    assert "xp.xp_min" in cat.findings.settings_without_panel


def test_settings_without_panel_cleared_when_panel_detected():
    """When a known panel is detected, settings_without_panel does NOT
    list the subsystem's settings."""
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(SettingSpec(name="xp_min", value_type=int, default=1),),
        ),
    )
    _inject_ledger(
        _make_ledger(
            _entry("xpmenu", "XPCog", "xp"),
        ),
    )
    cat = build_catalogue()
    assert "xp.xp_min" not in cat.findings.settings_without_panel


def test_regex_inferred_panels_finding_populated():
    _inject_ledger(
        _make_ledger(
            _entry("ghostmenu", "MiningCog", "mining"),
        ),
    )
    cat = build_catalogue()
    assert "mining.ghostmenu" in cat.findings.regex_inferred_panels


def test_undiscoverable_surfaces_finding_populated():
    """A settings/config/policy command in a subsystem without a panel
    AND without a help_hook is flagged as undiscoverable."""
    _inject_ledger(
        _make_ledger(
            _entry("weirdsettings", "BlackjackCog", "blackjack"),
        ),
    )
    cat = build_catalogue(bot=None)
    assert "blackjack.weirdsettings" in cat.findings.undiscoverable_surfaces


def test_undiscoverable_surfaces_excluded_when_help_hook_present():
    cog = _FakeCog("BlackjackCog", has_help_hook=True)
    bot = _FakeBot(cogs={"BlackjackCog": cog})
    _inject_ledger(
        _make_ledger(
            _entry("weirdsettings", "BlackjackCog", "blackjack"),
        ),
    )
    cat = build_catalogue(bot=bot)
    assert "blackjack.weirdsettings" not in cat.findings.undiscoverable_surfaces


def test_findings_total_sums_all_buckets():
    findings = CustomizationFindings(
        subsystems_missing_panel=("a",),
        subsystems_missing_help_hook=("b", "c"),
        subsystems_missing_schema=("d",),
        panels_without_settings=("e",),
        settings_without_panel=("f",),
        regex_inferred_panels=("g",),
        undiscoverable_surfaces=("h", "i"),
    )
    assert findings.total == 9


# ---------------------------------------------------------------------------
# Query API
# ---------------------------------------------------------------------------


def test_get_returns_entry_for_known_subsystem():
    cat = build_catalogue()
    entry = cat.get("admin")
    assert entry is not None
    assert entry.subsystem == "admin"


def test_get_returns_none_for_unknown_subsystem():
    cat = build_catalogue()
    assert cat.get("no_such_subsystem") is None


def test_panels_returns_all_panels_across_subsystems():
    cog_a = _FakeCog("ModerationCog", has_help_hook=True)
    cog_b = _FakeCog("EconomyCog", has_help_hook=True)
    bot = _FakeBot(cogs={"ModerationCog": cog_a, "EconomyCog": cog_b})
    cat = build_catalogue(bot=bot)
    panels = cat.panels()
    sources = {p.source for p in panels}
    assert "help_hook" in sources
    assert len(panels) >= 2


def test_by_panel_count_returns_subsystem_keyed_counts():
    cog = _FakeCog("ModerationCog", has_help_hook=True)
    bot = _FakeBot(cogs={"ModerationCog": cog})
    cat = build_catalogue(bot=bot)
    counts = cat.by_panel_count()
    assert counts["moderation"] >= 1
    assert counts["admin"] == 0


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_panel_declaration_is_frozen():
    panel = PanelDeclaration(command="modmenu", source="known_list")
    with pytest.raises(Exception):
        panel.command = "other"  # type: ignore[misc]


def test_customization_entry_is_frozen():
    cat = build_catalogue()
    entry = cat.entries[0]
    with pytest.raises(Exception):
        entry.subsystem = "other"  # type: ignore[misc]


def test_customization_catalogue_is_frozen():
    cat = build_catalogue()
    with pytest.raises(Exception):
        cat.version = 99  # type: ignore[misc]


def test_customization_findings_is_frozen():
    cat = build_catalogue()
    with pytest.raises(Exception):
        cat.findings.subsystems_missing_panel = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


def test_rebuild_replaces_cached_snapshot():
    first = build_catalogue()
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(SettingSpec(name="xp_min", value_type=int, default=1),),
        ),
    )
    second = build_catalogue()
    assert second is not first
    assert get_cached_catalogue() is second
    assert second.get("xp").has_schema is True  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Diagnostics provider
# ---------------------------------------------------------------------------


def test_diagnostics_provider_returns_not_built_before_first_build():
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("customization_catalogue")
    assert snap["status"] == "not_built"
    assert "hint" in snap


def test_diagnostics_provider_returns_counts_after_build():
    from services import diagnostics_service

    cog = _FakeCog("ModerationCog", has_help_hook=True)
    bot = _FakeBot(cogs={"ModerationCog": cog})
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(SettingSpec(name="warn_threshold", value_type=int, default=3),),
        ),
    )
    build_catalogue(bot=bot)
    snap = diagnostics_service.snapshot("customization_catalogue")
    assert snap["status"] == "built"
    assert snap["version"] == 1
    assert snap["subsystem_count"] >= 1
    assert "panels_by_source" in snap
    assert snap["subsystems_with_help_hook"] >= 1
    assert snap["subsystems_with_schema"] >= 1
    assert "findings" in snap


def test_diagnostics_provider_is_registered_at_import_time():
    from services import diagnostics_service

    assert "customization_catalogue" in diagnostics_service.registered_names()


# ---------------------------------------------------------------------------
# @panel_command decorator
# ---------------------------------------------------------------------------


def test_panel_command_sets_extras_on_command_like_object():
    class _Cmd:
        extras: dict = {}

    cmd = _Cmd()
    cmd.extras = {}
    decorated = panel_command(cmd)
    assert decorated is cmd
    assert cmd.extras["panel"] is True


def test_panel_command_initializes_extras_when_absent():
    class _Cmd:
        pass

    cmd = _Cmd()
    decorated = panel_command(cmd)
    assert decorated is cmd
    assert getattr(cmd, "extras", None) == {"panel": True}


def test_panel_command_preserves_existing_extras():
    class _Cmd:
        pass

    cmd = _Cmd()
    cmd.extras = {"other": "value"}
    panel_command(cmd)
    assert cmd.extras == {"other": "value", "panel": True}


# ---------------------------------------------------------------------------
# KNOWN_PANEL_COMMANDS sanity
# ---------------------------------------------------------------------------


def test_known_panel_commands_subsystems_all_exist_in_registry():
    from utils.subsystem_registry import SUBSYSTEMS

    for sub, _cmd in KNOWN_PANEL_COMMANDS:
        assert sub in SUBSYSTEMS, f"known panel sub {sub!r} not in SUBSYSTEMS"


def test_known_panel_commands_have_no_duplicates():
    seen: set[tuple[str, str]] = set()
    for entry in KNOWN_PANEL_COMMANDS:
        assert entry not in seen, f"duplicate KNOWN_PANEL_COMMANDS entry {entry!r}"
        seen.add(entry)

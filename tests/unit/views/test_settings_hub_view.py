"""Unit tests for the Settings Manager hub view — S5 + Lane 7 display correctness.

The hub is the read-only navigation root: header counters + an
**actionable-groups** dropdown (settings audit §6 inclusion rule) + four
diagnostic-panel buttons + the command-access shortcut. These pin the
Lane 7 contract:

* only actionable groups appear (editable scalar / binding / resource /
  registered domain panel) — router-only, internal, and empty subsystems
  are excluded;
* every group is reachable past Discord's 25-option cap (page nav, no
  silent truncation);
* per-guild availability ("routed off") renders as a label while the
  group stays reachable;
* discovery is read-only and deterministic — no mutation-service
  ownership moves into the hub (see also
  ``tests/unit/invariants/test_settings_cog_read_only.py``).
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import discord
import pytest

from core.runtime import settings_registry
from core.runtime import subsystem_schema as schema_mod
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SettingSpec,
    SubsystemSchema,
)
from services import command_routing
from services.customization_catalogue import (
    actionable_settings_groups,
    group_availability,
)
from views.settings.hub import SettingsHubView


@pytest.fixture(autouse=True)
def _isolated_state():
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    settings_registry._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    settings_registry._reset_for_tests()


def _author():
    class _M:
        id = 1

    return _M()


def _editable_spec(name: str = "knob") -> SettingSpec:
    return SettingSpec(
        name=name,
        value_type=int,
        default=1,
        settings_key=f"TEST_{name.upper()}",
    )


def _select(view: SettingsHubView) -> discord.ui.Select:
    return next(c for c in view.children if isinstance(c, discord.ui.Select))


# ---------------------------------------------------------------------------
# Dropdown ordering — server-config groups first (settings_order_sim)
# ---------------------------------------------------------------------------


def test_settings_dropdown_sorts_server_config_groups_first(monkeypatch):
    """`!settings` is an admin surface, so a server-config group (moderation)
    sorts ABOVE a fun group (economy) even when the fun group has a lower
    (earlier) *global* ``ui_priority``. Regression guard for the settings-order
    sim's ~28→~8 find-cost win; the global ``ui_priority`` (Help / hubs) is
    untouched because only this dropdown reads ``actionable_settings_groups``.
    """
    import utils.subsystem_registry as registry_mod

    fake = {
        # Fun group — LOW global ui_priority (would lead the old order).
        "econ_fun": {
            "display_name": "Economy",
            "description": "coins",
            "visibility_mode": "normal",
            "category": "economy",
            "visibility_tier": "user",
            "ui_priority": 10,
        },
        # Server-config group — HIGH global ui_priority (buried in the old
        # order); must lead the settings dropdown now.
        "mod_cfg": {
            "display_name": "Moderation",
            "description": "warns, bans",
            "visibility_mode": "normal",
            "category": "moderation",
            "visibility_tier": "moderator",
            "ui_priority": 80,
        },
    }
    monkeypatch.setattr(registry_mod, "SUBSYSTEMS", fake)
    for name in fake:
        schema_mod.register(
            SubsystemSchema(subsystem=name, settings=(_editable_spec(),)),
        )
    order = [g.subsystem for g in actionable_settings_groups()]
    assert order.index("mod_cfg") < order.index("econ_fun")


# ---------------------------------------------------------------------------
# Actionable-group discovery (audit §6 inclusion rule)
# ---------------------------------------------------------------------------


def test_groups_exclude_subsystems_with_no_actionable_surface():
    """A subsystem with no schema (router-only / empty) is not a group —
    the old hub listed all 28 non-internal subsystems and rendered empty
    pages; the inclusion rule kills that class.
    """
    names = {g.subsystem for g in actionable_settings_groups()}
    # Real manifest entries with no configurable surface (audit §4).
    assert "games_hub" not in names
    assert "inventory" not in names
    assert "leaderboard" not in names
    assert "help" not in names


def test_groups_include_editable_scalar_bearing_subsystem():
    schema_mod.register(
        SubsystemSchema(subsystem="xp", settings=(_editable_spec("xp_min"),)),
    )
    groups = {g.subsystem: g for g in actionable_settings_groups()}
    assert "xp" in groups
    assert groups["xp"].editable_setting_count == 1
    assert groups["xp"].surfaces == ("settings",)


def test_groups_exclude_schema_whose_settings_are_not_editable():
    """A declared setting without a ``settings_key`` cannot be edited by the
    scalar pipeline — a schema carrying only those is not actionable.
    """
    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(SettingSpec(name="xp_min", value_type=int, default=1),),
        ),
    )
    assert "xp" not in {g.subsystem for g in actionable_settings_groups()}


def test_groups_include_bindings_only_subsystem():
    """BTD6's real shape: a binding, no scalar settings (audit §4)."""
    schema_mod.register(
        SubsystemSchema(
            subsystem="btd6",
            bindings=(
                BindingSpec(
                    name="strategy_submissions",
                    kind=BindingKind.CHANNEL,
                    required=False,
                    hint="strategy submissions channel",
                    capability_required="btd6.strategy.submit",
                ),
            ),
        ),
    )
    groups = {g.subsystem: g for g in actionable_settings_groups()}
    assert "btd6" in groups
    assert groups["btd6"].surfaces == ("bindings",)


def test_groups_include_declared_domain_config_subsystem():
    """Cleanup appears via its schema's ``domain_panels`` declaration (Settings
    Phase 2; audit §4: domain group linked to its canonical panel).  Since the
    completion-cert punch #4 it *also* declares one scalar ``SettingSpec`` (the
    ``!cleanuphistory`` spam-duplicate window) with a config-input widget, so it
    surfaces **both** a scalar settings page and the domain panel.  Registers
    the REAL cleanup schema so the test pins the shipped declaration.
    """
    from cogs.cleanup.schemas import CLEANUP_CONFIG_SCHEMA

    assert CLEANUP_CONFIG_SCHEMA.domain_panels  # the real declaration exists
    schema_mod.register(CLEANUP_CONFIG_SCHEMA)
    groups = {g.subsystem: g for g in actionable_settings_groups()}
    assert "cleanup" in groups
    assert groups["cleanup"].has_domain_panel is True
    assert groups["cleanup"].editable_setting_count == 1
    assert groups["cleanup"].surfaces == ("settings", "panel")


def test_groups_exclude_internal_subsystems(monkeypatch):
    import utils.subsystem_registry as registry_mod

    fake = {
        "secret": {"display_name": "Secret", "visibility_mode": "internal"},
        "open": {"display_name": "Open", "visibility_mode": "normal"},
    }
    monkeypatch.setattr(registry_mod, "SUBSYSTEMS", fake)
    schema_mod.register(
        SubsystemSchema(subsystem="secret", settings=(_editable_spec(),)),
    )
    schema_mod.register(
        SubsystemSchema(subsystem="open", settings=(_editable_spec(),)),
    )
    names = {g.subsystem for g in actionable_settings_groups()}
    assert names == {"open"}


def test_groups_are_deterministic_and_read_only():
    schema_mod.register(
        SubsystemSchema(subsystem="xp", settings=(_editable_spec(),)),
    )
    assert actionable_settings_groups() == actionable_settings_groups()


# ---------------------------------------------------------------------------
# Hub view structure + >25 reachability (no silent truncation)
# ---------------------------------------------------------------------------


def test_hub_view_contains_dropdown_and_diagnostic_buttons():
    """Subsystem dropdown + four S5 diagnostic buttons + the command-access
    button; no page nav while the group count fits one select page.
    """
    view = SettingsHubView(_author())
    assert len(view.children) == 6
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert len(buttons) == 5


def test_button_labels_match_directive():
    view = SettingsHubView(_author())
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    labels = {b.label for b in buttons}
    assert labels == {
        "Needs setup",
        "Invalid settings",
        "Missing bindings",
        "Recent changes",
        "Command access",
    }


def _register_many(monkeypatch, count: int) -> list[str]:
    """Patch the manifest with ``count`` actionable synthetic subsystems."""
    import utils.subsystem_registry as registry_mod

    names = [f"fake_{i:02d}" for i in range(count)]
    fake = {
        name: {
            "display_name": f"Fake {i:02d}",
            "description": f"synthetic subsystem {i}",
            "visibility_mode": "normal",
            "ui_priority": i,
        }
        for i, name in enumerate(names)
    }
    monkeypatch.setattr(registry_mod, "SUBSYSTEMS", fake)
    for name in names:
        schema_mod.register(
            SubsystemSchema(subsystem=name, settings=(_editable_spec(),)),
        )
    return names


def test_every_group_is_reachable_past_the_25_option_cap(monkeypatch):
    """30 actionable groups → two pages whose option values union to all 30;
    the old behaviour silently dropped everything past the first 25.
    """
    names = _register_many(monkeypatch, 30)

    page0 = SettingsHubView(_author(), page=0)
    page1 = SettingsHubView(_author(), page=1)
    options0 = {o.value for o in _select(page0).options}
    options1 = {o.value for o in _select(page1).options}

    assert len(options0) == 25  # Discord's hard cap per select
    assert len(options1) == 5
    assert options0 | options1 == set(names)
    assert options0.isdisjoint(options1)
    # The page indicator is visible so the operator knows more pages exist.
    assert "(page 1/2)" in (_select(page0).placeholder or "")
    assert "(page 2/2)" in (_select(page1).placeholder or "")


def test_page_nav_buttons_appear_only_when_needed(monkeypatch):
    _register_many(monkeypatch, 30)
    paged = SettingsHubView(_author())
    nav = [
        c
        for c in paged.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id in ("settings_hub.page_prev", "settings_hub.page_next")
    ]
    assert len(nav) == 2
    prev, nxt = sorted(nav, key=lambda b: b.custom_id != "settings_hub.page_prev")
    assert prev.disabled is True  # already at the first page
    assert nxt.disabled is False

    last = SettingsHubView(_author(), page=1)
    nav_last = {
        c.custom_id: c
        for c in last.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id in ("settings_hub.page_prev", "settings_hub.page_next")
    }
    assert nav_last["settings_hub.page_prev"].disabled is False
    assert nav_last["settings_hub.page_next"].disabled is True


def test_page_index_is_clamped(monkeypatch):
    _register_many(monkeypatch, 30)
    view = SettingsHubView(_author(), page=99)
    assert view._page == 1  # clamped to the last page, never an empty select


def test_no_empty_pages_by_construction(monkeypatch):
    """25 groups → exactly one full page and no nav buttons (an empty page 2
    can't exist).
    """
    _register_many(monkeypatch, 25)
    view = SettingsHubView(_author())
    assert len(_select(view).options) == 25
    assert all(
        c.custom_id not in ("settings_hub.page_prev", "settings_hub.page_next")
        for c in view.children
        if isinstance(c, discord.ui.Button)
    )


def test_hub_dropdown_options_capped_to_discord_limit(monkeypatch):
    _register_many(monkeypatch, 60)
    for page in range(3):
        view = SettingsHubView(_author(), page=page)
        assert len(_select(view).options) <= 25


# ---------------------------------------------------------------------------
# Actor-aware availability rendering
# ---------------------------------------------------------------------------


def test_unavailable_group_renders_marker_but_stays_reachable():
    schema_mod.register(
        SubsystemSchema(subsystem="xp", settings=(_editable_spec(),)),
    )
    view = SettingsHubView(_author(), availability={"xp": "routed off"})
    option = next(o for o in _select(view).options if o.value == "xp")
    assert "⛔ routed off" in (option.description or "")
    # Reachable: the option exists; only the description is marked.


async def test_create_reads_guild_routing_for_labels(monkeypatch):
    from cogs.cleanup.schemas import CLEANUP_CONFIG_SCHEMA

    schema_mod.register(
        SubsystemSchema(subsystem="xp", settings=(_editable_spec(),)),
    )
    # Phase 2: cleanup is a group via its domain-panel declaration.
    schema_mod.register(CLEANUP_CONFIG_SCHEMA)
    monkeypatch.setattr(
        command_routing,
        "list_for_guild",
        AsyncMock(
            return_value=[
                {
                    "scope_type": "guild",
                    "scope_id": None,
                    "cog_name": "xp",
                    "enabled": False,
                },
                # Channel-scope restrictions are not a group-level state.
                {
                    "scope_type": "channel",
                    "scope_id": 5,
                    "cog_name": "cleanup",
                    "enabled": False,
                },
            ],
        ),
    )
    view = await SettingsHubView.create(_author(), guild_id=42)
    select = _select(view)
    xp = next(o for o in select.options if o.value == "xp")
    cleanup = next(o for o in select.options if o.value == "cleanup")
    assert "routed off" in (xp.description or "")
    assert "routed off" not in (cleanup.description or "")


async def test_group_availability_degrades_on_routing_failure(monkeypatch):
    monkeypatch.setattr(
        command_routing,
        "list_for_guild",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    assert await group_availability(42, ["xp"]) == {}


async def test_create_without_guild_renders_plain_hub():
    schema_mod.register(
        SubsystemSchema(subsystem="xp", settings=(_editable_spec(),)),
    )
    view = await SettingsHubView.create(_author(), guild_id=None)
    option = next(o for o in _select(view).options if o.value == "xp")
    assert "routed off" not in (option.description or "")


# ---------------------------------------------------------------------------
# Header embed
# ---------------------------------------------------------------------------


def test_hub_embed_has_title_and_inventory_field():
    embed = SettingsHubView.build_embed()
    assert "Settings Manager" in (embed.title or "")
    field_names = [f.name for f in embed.fields]
    assert "Inventory" in field_names
    assert "Customization findings" in field_names


def test_hub_inventory_reflects_registered_settings_and_groups():
    from cogs.cleanup.schemas import CLEANUP_CONFIG_SCHEMA

    schema_mod.register(
        SubsystemSchema(
            subsystem="xp",
            settings=(_editable_spec("xp_min"), _editable_spec("xp_max")),
        ),
    )
    # Phase 2: cleanup is a group via its domain-panel declaration.
    schema_mod.register(CLEANUP_CONFIG_SCHEMA)
    settings_registry.build_registry()
    embed = SettingsHubView.build_embed()
    inventory = next(f.value for f in embed.fields if f.name == "Inventory")
    # xp's 2 scalars + cleanup's 1 scalar (spam-window, punch #4) = 3.
    assert "`settings`: 3" in inventory
    # xp (scalar) + cleanup (scalar + declared domain group) are the actionable groups.
    assert "`groups`: 2" in inventory


def test_hub_inventory_reflects_registered_bindings():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            bindings=(
                BindingSpec(
                    name="mod_log",
                    kind=BindingKind.CHANNEL,
                    required=True,
                    hint="mod log target",
                    capability_required="moderation.log.view",
                ),
            ),
        ),
    )
    embed = SettingsHubView.build_embed()
    inventory = next(f.value for f in embed.fields if f.name == "Inventory")
    assert "`bindings`: 1" in inventory


def test_hub_handles_no_settings_registry_built():
    """When SettingsRegistry has not been built, settings count is 0."""
    embed = SettingsHubView.build_embed()
    inventory = next(f.value for f in embed.fields if f.name == "Inventory")
    assert "`settings`: 0" in inventory

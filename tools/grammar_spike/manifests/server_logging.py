"""Server logging — the OPERATOR spike subsystem (richest config surface).

Source of truth (verified 2026-07-02):
    cogs/logging_cog.py       — !logging group (313–445), 8 gateway listeners
                                (170–311)
    cogs/logging/panel.py     — LoggingPanelView, 8 static custom_ids
                                (logging_panel.*)
    cogs/logging/schemas.py   — 12 SettingSpecs / 11 BindingSpecs /
                                11 ResourceRequirements (register_schemas)
    services/server_logging.py — bus subscriptions (:1854–1856), embed
                                 rendering, route resolution
    services/server_logging_config.py — DEFAULT_ENABLED=False (:85) — the
                                 safe-default-ON showcase reverses this

This is the subsystem the generated-panel thesis lives or dies on: its
entire panel is config choreography (set binding / provision resource /
show status / test) — the §2 kernel workflows cover every button except
`test`. Its listeners are the G-1 evidence. Its per-category toggles are
the `on_when_bound` showcase (§4.4, decision 5).
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    Activation,
    BindingSpec,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSubscription,
    GatewayListenerSpec,
    HandlerRef,
    HelpEntrySpec,
    LayoutSpec,
    PanelActionSpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    ResourceRequirement,
    SettingSpec,
    SubsystemManifest,
)

_CAP = "logging.settings.configure"

_CATEGORY_TOGGLES = (
    ("messages_enabled", "logging_messages_enabled", "message_channel"),
    ("members_enabled", "logging_members_enabled", "member_channel"),
    ("roles_enabled", "logging_roles_enabled", "role_channel"),
    ("moderation_enabled", "logging_moderation_enabled", "mod_channel"),
    ("channels_enabled", "logging_channels_enabled", "events_channel"),
    ("server_enabled", "logging_server_enabled", "events_channel"),
    ("voice_enabled", "logging_voice_enabled", "events_channel"),
)

_BINDING_NAMES = (
    "mod_channel",
    "cleanup_channel",
    "debug_channel",
    "info_channel",
    "warning_channel",
    "error_channel",
    "audit_channel",
    "events_channel",
    "message_channel",
    "member_channel",
    "role_channel",
)

#: the 8 raw gateway listeners logging consumes (logging_cog.py:170–311) —
#: the G-1 evidence: none of these is expressible in the design spec today.
_GATEWAY_LISTENERS = (
    "on_message_delete",
    "on_message_edit",
    "on_raw_message_delete",
    "on_member_join",
    "on_member_remove",
    "on_member_update",
    "on_audit_log_entry_create",
    "on_voice_state_update",
)

LOGGING_MANIFEST = SubsystemManifest(
    key="logging",
    display_name="Server Logging",
    description="Structured event logging to configured channels.",
    emoji="📝",
    category="server",
    visibility_tier="staff",
    capabilities=(_CAP,),
    parent_hub="server_management",  # [A]
    commands=(
        # cogs/logging_cog.py:313 — the group opens the panel (route default)
        CommandSpec(
            name="logging",
            kind=CommandKind.PREFIX,
            summary="Open the logging control panel.",
            route=PanelRef("logging.panel"),
            capability_required=_CAP,
        ),
        # :331 status — a read-model panel body, no code
        CommandSpec(
            name="logging status",
            kind=CommandKind.PREFIX,
            summary="Show logging status.",
            route=PanelRef("logging.panel"),
            capability_required=_CAP,
        ),
        # :337 set — TIER 1: the kernel binding-set workflow (channel picker)
        CommandSpec(
            name="logging set",
            kind=CommandKind.PREFIX,
            summary="Bind a log category to a channel.",
            route=PanelRef("logging.pick_channel"),
            capability_required=_CAP,
        ),
        # :374 create — TIER 1: the provisioning lane (preview + confirm)
        CommandSpec(
            name="logging create",
            kind=CommandKind.PREFIX,
            summary="Create + bind a log channel (preview first).",
            route=PanelRef("logging.provision"),
            capability_required=_CAP,
        ),
        # :403 routes — read-model panel over the routing table
        CommandSpec(
            name="logging routes",
            kind=CommandKind.PREFIX,
            summary="Show event → channel routing.",
            route=PanelRef("logging.routes"),
            capability_required=_CAP,
        ),
        # :423 test — TIER 3 (thin): fires a real test embed down the pipe
        CommandSpec(
            name="logging test",
            kind=CommandKind.PREFIX,
            summary="Send a test log embed.",
            route=HandlerRef(
                "logging.fire_test",
                justification="exercises the live posting path end-to-end",
            ),
            capability_required=_CAP,
        ),
    ),
    panels=(
        # cogs/logging/panel.py — 8 static ids, all logging_panel.* verbatim
        PanelSpec(
            panel_id="logging.panel",
            subsystem="logging",
            title="📝 Server Logging",
            audience="invoker",
            body=(BlockSpec(kind="fields", provider=ProviderRef("logging.status")),),
            actions=(
                PanelActionSpec(
                    action_id="status",
                    custom_id_override="logging_panel.status",
                    label="📝 Refresh Status",
                    handler=PanelRef("logging.panel"),  # re-render: TIER 1
                ),
                PanelActionSpec(
                    action_id="set_mod",
                    custom_id_override="logging_panel.set_mod",
                    label="🔗 Set Mod Channel",
                    handler=PanelRef("logging.pick_channel"),  # TIER 1
                ),
                PanelActionSpec(
                    action_id="set_cleanup",
                    custom_id_override="logging_panel.set_cleanup",
                    label="🔗 Set Cleanup Channel",
                    handler=PanelRef("logging.pick_channel"),
                ),
                PanelActionSpec(
                    action_id="create_mod",
                    custom_id_override="logging_panel.create_mod",
                    label="🆕 Create Mod Channel",
                    handler=PanelRef("logging.provision"),  # TIER 1
                ),
                PanelActionSpec(
                    action_id="create_cleanup",
                    custom_id_override="logging_panel.create_cleanup",
                    label="🆕 Create Cleanup Channel",
                    handler=PanelRef("logging.provision"),
                ),
                PanelActionSpec(
                    action_id="test",
                    custom_id_override="logging_panel.test",
                    label="🔔 Test",
                    handler=HandlerRef(
                        "logging.fire_test",
                        justification="live posting-path exercise",
                    ),
                ),
                PanelActionSpec(
                    action_id="routes",
                    custom_id_override="logging_panel.routes",
                    label="🗺️ Routes",
                    handler=PanelRef("logging.routes"),
                ),
                PanelActionSpec(
                    action_id="overview",
                    custom_id_override="logging_panel.overview",
                    label="↩ Overview",
                    handler=PanelRef("logging.panel"),
                ),
            ),
            layout=LayoutSpec(  # [A] — seeded from the shipped arrangement
                pages=(
                    (
                        ("status", "set_mod", "set_cleanup"),
                        ("create_mod", "create_cleanup", "test"),
                        ("routes", "overview"),
                    ),
                ),
            ),
        ),
        PanelSpec(
            panel_id="logging.pick_channel",
            subsystem="logging",
            title="Bind a log channel",
            body=(BlockSpec(kind="text", text="Pick the destination channel."),),
            # the channel selector itself is the kernel's binding-set widget
        ),
        PanelSpec(
            panel_id="logging.provision",
            subsystem="logging",
            title="Create a log channel",
            body=(BlockSpec(kind="text", text="Provisioning preview + confirm."),),
        ),
        PanelSpec(
            panel_id="logging.routes",
            subsystem="logging",
            title="🗺️ Event routing",
            body=(BlockSpec(kind="fields", provider=ProviderRef("logging.routes")),),
        ),
    ),
    settings=(
        # the safe-default-ON showcase: master switch flips to on_when_bound
        # (design decision 5) — today's DEFAULT_ENABLED=False is the verified
        # discoverability failure this reverses.
        SettingSpec(
            name="enabled",
            value_type="bool",
            default=False,  # shipped default — port script pre-fills this
            settings_key="logging_enabled",
            capability_required=_CAP,
            activation=Activation.ON_WHEN_BOUND,
            hint="Logging runs once a destination is bound.",
        ),
        SettingSpec(
            name="auto_create_channels",
            value_type="bool",
            default=False,
            settings_key="logging_auto_create_channels",
            capability_required=_CAP,
            activation=Activation.OFF_UNTIL_OPT_IN,
            hint="Let provisioning create missing log channels (opt-in).",
        ),
        *(
            SettingSpec(
                name=name,
                value_type="bool",
                default=True,
                settings_key=key,
                capability_required=_CAP,
                activation=Activation.ON_WHEN_BOUND,
                group="categories",  # [A] seed; sim regroups
            )
            for name, key, _binding in _CATEGORY_TOGGLES
        ),
        SettingSpec(
            name="event_routing",
            value_type="str",
            default="combined",
            settings_key="logging_event_routing",
            capability_required=_CAP,
            allowed_values=("combined", "split"),
        ),
        # G-2 (SPIKE-FINDING): list-valued settings. The shipped exclusion
        # lists (#1594) are JSON-list KV values with add/remove UI — §2.5's
        # scalar SettingSpec has no list shape; these two force value_type
        # "list[int]" plus kernel add/remove workflows, or they are tier-3.
        SettingSpec(
            name="ignored_channels",
            value_type="list[int]",
            default=(),
            settings_key="logging_ignored_channels",
            capability_required=_CAP,
            hint="Channels excluded from logging.",
        ),
        SettingSpec(
            name="ignored_users",
            value_type="list[int]",
            default=(),
            settings_key="logging_ignored_users",
            capability_required=_CAP,
            hint="Users excluded from logging.",
        ),
    ),
    bindings=tuple(
        BindingSpec(
            name=name,
            kind="channel",
            required=False,
            capability_required=_CAP,
            resource_link=name,
            # decision 3: the legacy KV pointer keys become read-aliases
            legacy_settings_key_aliases=(f"logging_{name}",),
        )
        for name in _BINDING_NAMES
    ),
    resources=tuple(
        ResourceRequirement(
            kind="channel",
            intent=f"logging.{name}",
            provisioning="recommended",
            binding_name=name,
            offer_on_enable=True,
            audit_intent="logging_provision",
        )
        for name in _BINDING_NAMES
    ),
    subscriptions=(
        # services/server_logging.py:1854–1856 — the import-invisible wiring
        # the manifest makes declared (§1.6)
        EventSubscription(
            event="moderation.action_taken",
            handler=HandlerRef("logging.on_moderation_action"),
        ),
        EventSubscription(
            event="moderation.action_taken",
            handler=HandlerRef("logging.on_moderation_action_public"),
        ),
        EventSubscription(
            event="audit.action_recorded",
            handler=HandlerRef("logging.on_audit_action"),
        ),
    ),
    gateway_listeners=tuple(
        GatewayListenerSpec(
            gateway_event=event,
            handler=HandlerRef(
                f"logging.{event}",
                justification="gateway payload → routed log embed",
            ),
            gate="setting:logging_enabled",
        )
        for event in _GATEWAY_LISTENERS
    ),
    stores=(),  # logging owns no tables — it writes config via the lanes
    help=HelpEntrySpec(
        summary="Structured server logging with per-category destinations.",
        examples=("!logging", "!logging set mod #mod-log", "!logging test"),
    ),
)

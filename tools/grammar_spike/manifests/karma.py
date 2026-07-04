"""Karma — the SIMPLE spike subsystem, expressed in the §2 grammar.

Source of truth (verified 2026-07-02):
    cogs/karma_cog.py            — commands (207–265), react-to-thank (95–150)
    cogs/karma/schemas.py        — the 4 shipped SettingSpecs
    services/karma_service.py    — audited seam, EVT_KARMA_GRANTED (:178),
                                   typed errors, karma/karma_audit_log tables
    migrations/093_karma.sql     — the two stores
    utils/settings_keys/karma.py — key strings (compat item 5)

Tier verdict for karma (measured by measure.py): the config surface and
identities are pure declaration; the domain behavior is ONE thin seam
(`karma.give`) plus a card renderer — the grammar fits it with almost no
strain. The one addition it forced: `CommandSpec.cooldown` (G-4) and the
`GatewayListenerSpec` family (G-1) for react-to-thank.
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    Activation,
    BindingSpec,
    BlockSpec,
    CommandKind,
    CommandSpec,
    EventSpec,
    FieldSpec,
    GatewayListenerSpec,
    HandlerRef,
    HelpEntrySpec,
    LeaderboardSpec,
    PanelRef,
    PanelSpec,
    ProviderRef,
    SettingSpec,
    StoreSpec,
    SubsystemManifest,
    WorkflowRef,
)

_ = BindingSpec  # karma has no pointer-lane config — deliberate, not omitted

KARMA_MANIFEST = SubsystemManifest(
    key="karma",  # persisted subsystem key, verbatim (compat item 1)
    display_name="Karma",
    description="Peer reputation — thank helpful members.",
    emoji="✨",
    category="community",
    visibility_tier="user",
    capabilities=("karma.settings.configure",),
    dependencies=(),
    parent_hub="community",  # [A] — sim-owned
    commands=(
        # cogs/karma_cog.py:209 — @commands.command(name="thanks", aliases=…)
        CommandSpec(
            name="thanks",
            aliases=("rep", "thank"),
            kind=CommandKind.PREFIX,
            summary="Give a karma point to a helpful member.",
            usage="!thanks @user [reason]",
            # TIER 3 (thin): domain mutation through the audited seam —
            # typed-error rendering is behavior the grammar can't declare.
            route=HandlerRef(
                "karma.grant",
                justification="domain mutation + typed-error copy (5 error shapes)",
            ),
            cooldown=(5, 10, "user"),  # G-4: @commands.cooldown, :208
        ),
        # cogs/karma_cog.py:224 — the karma group (card when no subcommand)
        CommandSpec(
            name="karma",
            kind=CommandKind.PREFIX,
            summary="Show a member's karma standing.",
            usage="!karma [@user]",
            route=PanelRef("karma.card"),
            cooldown=(5, 10, "user"),
        ),
        # cogs/karma_cog.py:235 — `!karma add` shares the grant path
        CommandSpec(
            name="karma add",
            kind=CommandKind.PREFIX,
            summary="Give a karma point (alias surface of !thanks).",
            route=HandlerRef("karma.grant", justification="same seam as thanks"),
        ),
        # cogs/karma_cog.py:248 — /karma (ephemeral card)
        CommandSpec(
            name="karma",
            kind=CommandKind.SLASH,
            summary="Show your karma — or another member's.",
            route=PanelRef("karma.card"),
        ),
    ),
    panels=(
        # The karma card (cogs/karma_cog.py:40 _karma_card) is a read-only
        # embed: TIER 2 — a FieldsBlock over a read-model provider. No
        # buttons today, so no actions/layout.
        PanelSpec(
            panel_id="karma.card",
            subsystem="karma",
            title="✨ Karma — {member}",
            audience="invoker",
            body=(BlockSpec(kind="fields", provider=ProviderRef("karma.record")),),
        ),
    ),
    settings=(
        # cogs/karma/schemas.py — all four shipped specs, keys verbatim
        SettingSpec(
            name="enabled",
            value_type="bool",
            default=True,
            settings_key="karma_enabled",
            capability_required="karma.settings.configure",
            hint="Master switch for karma grants.",
            activation=Activation.ON_BY_DEFAULT,
        ),
        SettingSpec(
            name="cooldown_seconds",
            value_type="int",
            default=3600,
            settings_key="karma_cooldown",
            capability_required="karma.settings.configure",
            validator=HandlerRef("karma.validate_cooldown"),
            hint="Per-(giver→receiver) grant cooldown.",
        ),
        SettingSpec(
            name="daily_cap",
            value_type="int",
            default=10,
            settings_key="karma_daily_cap",
            capability_required="karma.settings.configure",
            validator=HandlerRef("karma.validate_daily_cap"),
            hint="Max grants one giver can make per day.",
        ),
        SettingSpec(
            name="reaction_emoji",
            value_type="str",
            default="",
            settings_key="karma_reaction_emoji",
            capability_required="karma.settings.configure",
            hint="React-to-thank trigger emoji (empty = off).",
        ),
    ),
    events=(
        # services/karma_service.py:178 — emit kwargs, verbatim payload
        EventSpec(
            name="karma.granted",
            payload_schema=(
                FieldSpec("guild_id", "int"),
                FieldSpec("from_user", "int"),
                FieldSpec("to_user", "int"),
                FieldSpec("delta", "int"),
                FieldSpec("new_total", "int"),
                FieldSpec("source", "str"),
            ),
            owner_subsystem="karma",
            expected_subscribers=(HandlerRef("server_logging.on_audit_fanout"),),
            audited=True,
        ),
    ),
    gateway_listeners=(
        # cogs/karma_cog.py:95 — react-to-thank. G-1: without the proposed
        # GatewayListenerSpec this whole feature is invisible to the
        # manifest. The gate mirrors the shipped fast-gate (policy.enabled
        # AND reaction_emoji set) the kernel would check before dispatch.
        GatewayListenerSpec(
            gateway_event="on_raw_reaction_add",
            handler=HandlerRef(
                "karma.react_to_thank",
                justification="message fetch + author checks before the seam",
            ),
            gate="setting:karma_enabled AND setting:karma_reaction_emoji",
        ),
    ),
    stores=(
        # migrations/093_karma.sql:15/:32; sole writer = karma_service (INV-K)
        StoreSpec(
            table="karma",
            sole_writer="karma.service",
            checkpoint_class="aggregate",
            invariant_tag="INV-K",
            reader_domains=("leaderboard", "community"),
        ),
        StoreSpec(
            table="karma_audit_log",
            sole_writer="karma.service",
            checkpoint_class="ledger",
            invariant_tag="INV-K",
        ),
    ),
    game=None,
    help=HelpEntrySpec(
        summary="Thank helpful members with !thanks — karma is peer reputation.",
        examples=("!thanks @user for the fix", "!karma", "/karma"),
    ),
)

#: TIER-1 kernel workflows karma's settings surface rides on (no code):
KARMA_SETTINGS_WORKFLOWS = (
    WorkflowRef("setting_edit", (("subsystem", "karma"),)),
    WorkflowRef("setting_reset", (("subsystem", "karma"),)),
)

#: Decision-10 note: `!karma` shows a rank — the rebuild declares it:
KARMA_LEADERBOARD = LeaderboardSpec(
    board_id="karma.top",
    stat_key="karma.points",
    metric="max",
)

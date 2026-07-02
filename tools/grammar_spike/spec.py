"""SPIKE prototype of the design-spec §2 manifest grammar.

Faithful to `docs/planning/rebuild-design-spec-2026-07-02.md` §2: frozen
dataclasses, S/A/O field roles in metadata, no logic in declarations,
handler refs for everything behavioral, intra-manifest validation in
``__post_init__`` (§3.2 phase 1). Where this file diverges from the spec it
says so inline with a ``SPIKE-FINDING`` marker — those divergences are the
spike's product, promoted into the go/no-go report.

NOT the kernel: no engines, no runtime, nothing imported by disbot/.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any

# --------------------------------------------------------------------------
# Field-role tagging (§2.0): every field is semantic / arrangement / objective
# --------------------------------------------------------------------------

S = {"role": "semantic"}
A = {"role": "arrangement"}
O = {"role": "objective"}  # noqa: E741 - the spec's own letter


def field_roles(spec_type: type) -> dict[str, str]:
    """Role per field — the simulator's write-surface derivation (§2.10.1)."""
    return {f.name: str(f.metadata.get("role", "UNTAGGED")) for f in fields(spec_type)}


def untagged_fields(spec_type: type) -> list[str]:
    """§2.0's red-check: an untagged new field fails the classification test."""
    return [name for name, role in field_roles(spec_type).items() if role == "UNTAGGED"]


# --------------------------------------------------------------------------
# Refs — behavior lives behind registered names, never inline (§2.9)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class HandlerRef:
    """A registered domain handler (tier-3 when it carries logic)."""

    ref: str = field(metadata=S)
    justification: str = field(default="", metadata=S)


@dataclass(frozen=True)
class WorkflowRef:
    """A parameterized KERNEL workflow — tier-1, zero domain code (§2.9)."""

    workflow: str = field(metadata=S)  # e.g. "setting_edit", "binding_set"
    params: tuple[tuple[str, str], ...] = field(default=(), metadata=S)


@dataclass(frozen=True)
class ProviderRef:
    """A registered read-model provider (panel body data)."""

    ref: str = field(metadata=S)


@dataclass(frozen=True)
class PanelRef:
    panel_id: str = field(metadata=S)


@dataclass(frozen=True)
class ViewRef:
    """§2.9 legacy_view contingency lane — tier-3, justification-required."""

    ref: str = field(metadata=S)
    justification: str = field(default="", metadata=S)


Route = PanelRef | HandlerRef | WorkflowRef


# --------------------------------------------------------------------------
# Command / panel / action / selector / navigation (§2.2–§2.6)
# --------------------------------------------------------------------------


class CommandKind(str, Enum):
    PREFIX = "prefix"
    SLASH = "slash"
    BOTH = "both"


@dataclass(frozen=True)
class CommandSpec:
    name: str = field(metadata=S)
    kind: CommandKind = field(metadata=S)
    summary: str = field(metadata=S)
    route: Route = field(metadata=S)
    aliases: tuple[str, ...] = field(default=(), metadata=S)
    usage: str = field(default="", metadata=S)
    capability_required: str = field(default="", metadata=S)
    audience_tier: str = field(default="user", metadata=S)
    # SPIKE-FINDING G-4: the shipped surface rate-limits at the command layer
    # (`@commands.cooldown(rate, per, bucket)` — karma_cog.py:208, and widely).
    # §2.2 has no cooldown field, which would silently DROP shipped
    # anti-abuse behavior at port time. Proposed tier-2 addition:
    cooldown: tuple[int, int, str] | None = field(default=None, metadata=S)
    help_section_order: int = field(default=0, metadata=A)
    usage_weight: float = field(default=1.0, metadata=O)

    def __post_init__(self) -> None:
        # §2.2 two-lane exclusivity: a config/governance route resolves
        # capability; a domain-lane surface declares audience_tier only.
        if self.capability_required and self.audience_tier != "user":
            raise ValueError(
                f"command {self.name!r}: declare capability_required OR "
                "audience_tier, never both (§2.2 two-lane model)",
            )


@dataclass(frozen=True)
class PanelActionSpec:
    action_id: str = field(metadata=S)
    label: str = field(metadata=S)
    handler: Route = field(metadata=S)
    emoji: str = field(default="", metadata=S)
    style: str = field(default="secondary", metadata=S)
    capability_required: str = field(default="", metadata=S)
    audience_tier: str = field(default="user", metadata=S)
    defer_mode: str = field(default="auto", metadata=S)
    confirm: bool = field(default=False, metadata=S)
    result_render: str = field(default="toast", metadata=S)
    audit: str = field(default="", metadata=S)
    visible_when: str = field(default="", metadata=S)
    custom_id_override: str = field(default="", metadata=S)  # legacy verbatim ids
    destructive: bool = field(default=False, metadata=O)
    usage_weight: float = field(default=1.0, metadata=O)
    co_use_group: str = field(default="", metadata=O)
    flow_stage: int = field(default=0, metadata=O)

    def __post_init__(self) -> None:
        if self.destructive and self.style != "danger":
            raise ValueError(
                f"action {self.action_id!r}: destructive ⇒ style='danger' (§2.6)",
            )


@dataclass(frozen=True)
class SelectorSpec:
    selector_id: str = field(metadata=S)
    kind: str = field(metadata=S)  # channel|role|member|subsystem|enum|entity
    on_select: Route = field(metadata=S)
    options_source: ProviderRef | tuple[str, ...] = field(default=(), metadata=S)
    placeholder: str = field(default="", metadata=S)
    min_values: int = field(default=1, metadata=S)
    max_values: int = field(default=1, metadata=S)
    page_size: int = field(default=25, metadata=S)
    empty_state: str = field(default="", metadata=S)
    capability_required: str = field(default="", metadata=S)
    audience_tier: str = field(default="user", metadata=S)
    custom_id_override: str = field(default="", metadata=S)
    usage_weight: float = field(default=1.0, metadata=O)


@dataclass(frozen=True)
class NavigationSpec:
    parent: PanelRef | None = field(default=None, metadata=S)
    home_hub: str = field(default="FOLLOW_PARENT", metadata=S)
    show_help: bool = field(default=True, metadata=S)
    show_home: bool = field(default=True, metadata=S)
    show_rules: bool = field(default=False, metadata=S)


@dataclass(frozen=True)
class BlockSpec:
    """Typed content block: text / fields / table / list (§2.3)."""

    kind: str = field(metadata=S)  # text|fields|table|list
    provider: ProviderRef | None = field(default=None, metadata=S)
    text: str = field(default="", metadata=S)


@dataclass(frozen=True)
class LayoutSpec:
    """Rows of component refs by id — the sim's one write surface (§2.3)."""

    pages: tuple[tuple[tuple[str, ...], ...], ...] = field(default=(), metadata=A)


@dataclass(frozen=True)
class PanelSpec:
    panel_id: str = field(metadata=S)
    subsystem: str = field(metadata=S)
    title: str = field(metadata=S)
    audience: str = field(default="invoker", metadata=S)  # invoker|public|persistent
    anchor_policy: str = field(default="reply", metadata=S)
    timeout_s: int | None = field(default=180, metadata=S)
    body: tuple[BlockSpec, ...] = field(default=(), metadata=S)
    actions: tuple[PanelActionSpec, ...] = field(default=(), metadata=S)
    selectors: tuple[SelectorSpec, ...] = field(default=(), metadata=S)
    navigation: NavigationSpec = field(default=NavigationSpec(), metadata=S)
    layout: LayoutSpec = field(default=LayoutSpec(), metadata=A)
    renderer_override: HandlerRef | None = field(default=None, metadata=S)
    legacy_view: ViewRef | None = field(default=None, metadata=S)
    usage_weight: float = field(default=1.0, metadata=O)
    co_open_group: str = field(default="", metadata=O)

    def __post_init__(self) -> None:
        if self.audience == "persistent" and self.timeout_s is not None:
            raise ValueError(
                f"panel {self.panel_id!r}: persistent ⇒ timeout_s=None (§2.3)",
            )
        ids = [a.action_id for a in self.actions] + [
            s.selector_id for s in self.selectors
        ]
        if len(ids) != len(set(ids)):
            raise ValueError(f"panel {self.panel_id!r}: duplicate component ids")
        if self.layout.pages:
            placed = [ref for page in self.layout.pages for row in page for ref in row]
            if sorted(placed) != sorted(ids):
                raise ValueError(
                    f"panel {self.panel_id!r}: layout must place every declared "
                    "component exactly once (§2.3 coverage rule)",
                )


# --------------------------------------------------------------------------
# Config lanes — the extended shipped types (§2.5)
# --------------------------------------------------------------------------


class Activation(str, Enum):
    ON_BY_DEFAULT = "on_by_default"
    ON_WHEN_BOUND = "on_when_bound"
    ON_WHEN_KEYED = "on_when_keyed"
    OFF_UNTIL_OPT_IN = "off_until_opt_in"


@dataclass(frozen=True)
class SettingSpec:
    """Shipped fields verbatim (subsystem_schema.py:109) + §2.5 additions."""

    name: str = field(metadata=S)
    value_type: str = field(metadata=S)
    default: Any = field(metadata=S)
    settings_key: str = field(metadata=S)  # legacy key string — compat item 5
    capability_required: str = field(default="", metadata=S)  # empty = ADMIN floor
    hint: str = field(default="", metadata=S)
    validator: HandlerRef | None = field(default=None, metadata=S)
    allowed_values: tuple[Any, ...] = field(default=(), metadata=S)
    input_hint: str = field(default="", metadata=S)
    presets: tuple[Any, ...] = field(default=(), metadata=S)
    activation: Activation | None = field(default=None, metadata=S)
    external_side_effects: bool = field(default=False, metadata=S)
    storage: str = field(default="kv", metadata=S)
    scope_default: str = field(default="guild", metadata=S)
    legacy_keys: tuple[str, ...] = field(default=(), metadata=S)
    group: str = field(default="", metadata=A)
    advanced: bool = field(default=False, metadata=A)
    panel_order: int = field(default=0, metadata=A)
    edit_weight: float = field(default=1.0, metadata=O)
    co_edit_group: str = field(default="", metadata=O)
    depends_on: tuple[str, ...] = field(default=(), metadata=O)

    def __post_init__(self) -> None:
        if self.value_type == "bool" and self.activation is None:
            raise ValueError(
                f"setting {self.name!r}: bool specs must consciously choose "
                "an activation posture (§4.4)",
            )
        if (
            self.external_side_effects
            and self.activation is not Activation.OFF_UNTIL_OPT_IN
        ):
            raise ValueError(
                f"setting {self.name!r}: external_side_effects ⇒ "
                "off_until_opt_in (§4.4 privacy gate)",
            )


@dataclass(frozen=True)
class BindingSpec:
    """Shipped fields verbatim (subsystem_schema.py:75) + §2.5 additions."""

    name: str = field(metadata=S)
    kind: str = field(metadata=S)  # channel|role|category|message
    required: bool = field(default=False, metadata=S)
    hint: str = field(default="", metadata=S)
    capability_required: str = field(default="", metadata=S)
    legacy_settings_key_aliases: tuple[str, ...] = field(default=(), metadata=S)
    resource_link: str = field(default="", metadata=S)
    multiplicity: int = field(default=1, metadata=S)
    group: str = field(default="", metadata=A)
    bind_weight: float = field(default=1.0, metadata=O)


@dataclass(frozen=True)
class ResourceRequirement:
    """Shipped fields verbatim (resource_specs.py:79) + §2.5 additions."""

    kind: str = field(metadata=S)
    intent: str = field(metadata=S)
    provisioning: str = field(metadata=S)  # ProvisioningHint semantics
    binding_name: str = field(default="", metadata=S)
    description: str = field(default="", metadata=S)
    offer_on_enable: bool = field(default=False, metadata=S)
    teardown_policy: str = field(default="keep", metadata=S)
    shareable: bool = field(default=True, metadata=S)
    audit_intent: str = field(default="", metadata=S)


# --------------------------------------------------------------------------
# Events / stores / tasks / diagnostics / listeners (§2.8)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldSpec:
    name: str = field(metadata=S)
    type: str = field(metadata=S)


@dataclass(frozen=True)
class EventSpec:
    name: str = field(metadata=S)  # legacy names verbatim — compat item 3
    payload_schema: tuple[FieldSpec, ...] = field(metadata=S)
    owner_subsystem: str = field(metadata=S)
    expected_subscribers: tuple[HandlerRef, ...] = field(default=(), metadata=S)
    observability_only: bool = field(default=False, metadata=S)
    audited: bool = field(default=False, metadata=S)

    def __post_init__(self) -> None:
        if not self.expected_subscribers and not self.observability_only:
            raise ValueError(
                f"event {self.name!r}: subscriber-less events must declare "
                "observability_only=True (§2.8)",
            )


@dataclass(frozen=True)
class EventSubscription:
    event: str = field(metadata=S)
    handler: HandlerRef = field(metadata=S)


@dataclass(frozen=True)
class GatewayListenerSpec:
    """SPIKE-FINDING G-1 (proposed tier-2 family, NOT in the design spec).

    §2 covers bus events (`EventSpec`/`EventSubscription`) but has NO
    primitive for raw Discord gateway listeners — and the operator band
    lives on them: server logging alone consumes 8 (`on_message_delete`,
    `on_member_join`, `on_voice_state_update`, …, logging_cog.py:170–311),
    karma's react-to-thank consumes `on_raw_reaction_add`
    (karma_cog.py:95), blackjack reaction-joins another. Without this
    family every gateway-driven feature is tier-3 by definition and the
    wiring map goes blind exactly where the current repo's is. Fields:
    gate = the settings predicate the kernel checks BEFORE dispatching
    (the shipped fast-gate pattern); handler = the domain behavior.
    """

    gateway_event: str = field(metadata=S)  # discord.py listener name
    handler: HandlerRef = field(metadata=S)
    gate: str = field(default="", metadata=S)  # e.g. "setting:logging.enabled"


@dataclass(frozen=True)
class StoreSpec:
    table: str = field(metadata=S)
    sole_writer: str = field(metadata=S)  # handler/engine ref name
    checkpoint_class: str = field(metadata=S)  # ledger|aggregate|session
    retention: str = field(default="", metadata=S)
    invariant_tag: str = field(default="", metadata=S)
    reader_domains: tuple[str, ...] = field(default=(), metadata=S)


@dataclass(frozen=True)
class ManagedTaskSpec:
    name: str = field(metadata=S)  # "<subsystem>:<purpose>" prefix-reserved
    trigger: str = field(metadata=S)  # interval:<s>|cron:<expr>|event:<name>
    handler: HandlerRef = field(metadata=S)
    error_policy: str = field(default="log", metadata=S)


@dataclass(frozen=True)
class DiagnosticProviderSpec:
    name: str = field(metadata=S)
    provider: HandlerRef = field(metadata=S)
    lane: str = field(default="sync", metadata=S)
    audience: str = field(default="admin", metadata=S)


@dataclass(frozen=True)
class HelpEntrySpec:
    summary: str = field(metadata=S)
    examples: tuple[str, ...] = field(default=(), metadata=S)
    rules_text: str = field(default="", metadata=S)


# --------------------------------------------------------------------------
# Game facet (§2.8)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CostVector:
    currency: str = field(metadata=S)
    amount_source: str = field(metadata=S)  # "arg"|"setting:<key>"|fixed int str


@dataclass(frozen=True)
class ChallengeSessionSpec:
    game_key: str = field(metadata=S)
    accept_timeout_s: int = field(metadata=S)
    turn_timeout_s: int = field(metadata=S)
    stale_after_s: int = field(metadata=S)
    settle_once: bool = field(metadata=S)  # Literal[True] in the real kernel
    persistence: str = field(metadata=S)  # ephemeral|checkpointed|authoritative
    custom_id_scheme: str = field(default="g1", metadata=S)
    escrow: CostVector | None = field(default=None, metadata=S)
    stat_writes: tuple[str, ...] = field(default=(), metadata=S)
    refund_policy: HandlerRef | None = field(default=None, metadata=S)


@dataclass(frozen=True)
class LeaderboardSpec:
    board_id: str = field(metadata=S)
    stat_key: str = field(metadata=S)
    metric: str = field(metadata=S)
    scope: str = field(default="guild", metadata=S)
    empty_state: str = field(default="No entries yet.", metadata=S)
    display_order: int = field(default=0, metadata=A)


@dataclass(frozen=True)
class GameFacet:
    sessions: tuple[ChallengeSessionSpec, ...] = field(default=(), metadata=S)
    leaderboards: tuple[LeaderboardSpec, ...] = field(default=(), metadata=S)


# --------------------------------------------------------------------------
# The root record (§2.1)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SubsystemManifest:
    key: str = field(metadata=S)
    display_name: str = field(metadata=S)
    description: str = field(metadata=S)
    emoji: str = field(default="", metadata=S)
    color_token: str = field(default="default", metadata=S)
    category: str = field(default="", metadata=S)
    visibility_tier: str = field(default="user", metadata=S)
    capabilities: tuple[str, ...] = field(default=(), metadata=S)
    dependencies: tuple[str, ...] = field(default=(), metadata=S)
    commands: tuple[CommandSpec, ...] = field(default=(), metadata=S)
    panels: tuple[PanelSpec, ...] = field(default=(), metadata=S)
    settings: tuple[SettingSpec, ...] = field(default=(), metadata=S)
    bindings: tuple[BindingSpec, ...] = field(default=(), metadata=S)
    resources: tuple[ResourceRequirement, ...] = field(default=(), metadata=S)
    events: tuple[EventSpec, ...] = field(default=(), metadata=S)
    subscriptions: tuple[EventSubscription, ...] = field(default=(), metadata=S)
    gateway_listeners: tuple[GatewayListenerSpec, ...] = field(
        default=(),
        metadata=S,
    )  # SPIKE-FINDING G-1 — proposed family
    tasks: tuple[ManagedTaskSpec, ...] = field(default=(), metadata=S)
    diagnostics: tuple[DiagnosticProviderSpec, ...] = field(default=(), metadata=S)
    stores: tuple[StoreSpec, ...] = field(default=(), metadata=S)
    help: HelpEntrySpec | None = field(default=None, metadata=S)
    game: GameFacet | None = field(default=None, metadata=S)
    version: int = field(default=1, metadata=S)
    parent_hub: str | None = field(default=None, metadata=A)
    hub_group: str | None = field(default=None, metadata=A)
    ui_priority: int = field(default=0, metadata=A)

    def __post_init__(self) -> None:
        # §3.2 phase 1: intra-manifest identity duplicates die at import.
        # SPIKE-FINDING G-6: the pool is scoped BY KIND — Discord's prefix
        # and slash namespaces are disjoint (shipped `!karma` and `/karma`
        # coexist), so §3.1's "one shared pool" must be per-kind or every
        # dual-surface command is a false collision.
        seen: set[tuple[str, str]] = set()
        for cmd in self.commands:
            pools = (
                ("prefix", "slash")
                if cmd.kind is CommandKind.BOTH
                else (cmd.kind.value,)
            )
            for pool in pools:
                for name in (cmd.name, *cmd.aliases):
                    token = (pool, name.lower())
                    if token in seen:
                        raise ValueError(
                            f"{self.key}: duplicate {pool} command token {name!r}",
                        )
                    seen.add(token)
        for panel in self.panels:
            token = ("panel", panel.panel_id)
            if token in seen:
                raise ValueError(f"{self.key}: duplicate panel id {panel.panel_id!r}")
            seen.add(token)
        for setting in self.settings:
            token = ("setting", setting.settings_key)
            if token in seen:
                raise ValueError(
                    f"{self.key}: duplicate settings key {setting.settings_key!r}",
                )
            seen.add(token)


ALL_SPEC_TYPES: tuple[type, ...] = (
    CommandSpec,
    PanelSpec,
    PanelActionSpec,
    SelectorSpec,
    NavigationSpec,
    BlockSpec,
    LayoutSpec,
    SettingSpec,
    BindingSpec,
    ResourceRequirement,
    EventSpec,
    EventSubscription,
    GatewayListenerSpec,
    StoreSpec,
    ManagedTaskSpec,
    DiagnosticProviderSpec,
    HelpEntrySpec,
    ChallengeSessionSpec,
    LeaderboardSpec,
    GameFacet,
    CostVector,
    SubsystemManifest,
)

"""Read-only AI introspection read model — answerability Phase 2.

One bounded, audience-filtered composition over the *existing* AI owners, so the bot
can later answer "what can you do / what do you know / which settings affect this
channel / why didn't you reply" from a single faithful source instead of per-question
patches that disagree about what the bot "knows".

It **composes, never replaces** its owners:

* tool catalogue → :mod:`services.ai_tool_catalogue` (metadata) + :func:`services.ai_tools.all_tool_specs`
  (names / purpose / authoritative ``min_scope``);
* BTD6 answerability → :mod:`services.btd6_data_service` (loaded fixtures + the data source);
* effective AI settings → :func:`services.ai_config_projection_service.build_snapshot`;
* policy / recent-decision explanation → :func:`services.ai_natural_language_policy.resolve`
  (dry-run precedence trace) + :func:`services.ai_decision_audit_service.query`.

Hard boundaries (answerability roadmap §6, ``docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md``):

* **Read-only.** Every builder is a pure read; nothing here mutates settings, policy,
  cooldown, or audit state, and no new write-capable tool is introduced.
* **No AI exposure, no UI.** This is the read *model* only. Registering it as an AI tool
  (Phase 3) and any settings UI (Phase 4) stay behind the AI/BTD6 expansion gate and are
  out of scope here.
* **Audience filtering happens here, before any data could reach a model.** ``min_scope``
  stays the authority for tools; sensitive settings / cross-user audit / precedence traces
  are gated to admin+ (and provider diagnostics to platform-owner) at construction time —
  never by prompt wording alone.
* **No new registry.** Tool, command, and settings ownership stay where they are; this only
  reads them.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.runtime.ai.contracts import AIScope
from services import (
    ai_config_projection_service,
    ai_decision_audit_service,
    ai_natural_language_policy,
    ai_tool_catalogue,
    ai_tools,
)
from services.ai_natural_language_policy import MessageContext

# ---------------------------------------------------------------------------
# Audience helpers — one scope model (AIScope), tiered per roadmap §5.6
# ---------------------------------------------------------------------------


def _is_admin(scope: AIScope) -> bool:
    """True for ADMIN / SERVER_OWNER / PLATFORM_OWNER / SYSTEM — the tier that may see
    effective config, precedence traces, and cross-user audit.
    """
    return ai_tool_catalogue.scope_allows(scope, AIScope.ADMIN)


def _is_platform_owner(scope: AIScope) -> bool:
    """True for PLATFORM_OWNER / SYSTEM — the only tier that may see provider/runtime
    diagnostics (degraded state, error types, request counters).
    """
    return ai_tool_catalogue.scope_allows(scope, AIScope.PLATFORM_OWNER)


# ---------------------------------------------------------------------------
# 1. Tool catalogue snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolDescriptor:
    """One audience-visible AI tool — the catalogue half joined to its spec.

    ``read_only`` is always True in this lane (every registered tool is a read query);
    it is stated explicitly so a future answer can promise the bot cannot *act*.
    """

    name: str
    purpose: str
    min_scope: str
    toolsets: tuple[str, ...]
    grounds_btd6: bool
    cost_class: str
    freshness: str
    read_only: bool = True


@dataclass(frozen=True)
class ToolCatalogSnapshot:
    """The tools an ``audience`` scope may be offered, plus a count of those it may not.

    ``hidden_above_scope`` is a *count only* — names of higher-privilege tools are never
    revealed to a lower audience (roadmap §5.6: no hidden admin tooling leaks downward).
    """

    audience: str
    tools: tuple[ToolDescriptor, ...]
    toolsets_present: tuple[str, ...]
    total_visible: int
    hidden_above_scope: int


def build_tool_catalog(scope: AIScope) -> ToolCatalogSnapshot:
    """Audience-filtered descriptors for every registered AI tool.

    Joins the runtime-independent specs (``ai_tools.all_tool_specs`` — authoritative
    ``min_scope`` + purpose) with the canonical catalogue metadata
    (``ai_tool_catalogue.CATALOGUE`` — toolsets / grounding / cost / freshness). A tool is
    *visible* only when the caller's ``scope`` satisfies its ``min_scope``; higher-scope
    tools are counted but not named. Deterministic and side-effect-free.
    """
    specs = ai_tools.all_tool_specs()
    catalogue = ai_tool_catalogue.CATALOGUE

    visible: list[ToolDescriptor] = []
    hidden = 0
    for name in sorted(specs):
        spec = specs[name]
        if not ai_tool_catalogue.scope_allows(scope, spec.min_scope):
            hidden += 1
            continue
        meta = catalogue.get(name)
        toolsets = tuple(sorted(meta.toolsets)) if meta is not None else ()
        grounds = bool(meta is not None and meta.grounding_domain == "btd6")
        visible.append(
            ToolDescriptor(
                name=name,
                purpose=spec.description,
                min_scope=spec.min_scope.value,
                toolsets=toolsets,
                grounds_btd6=grounds,
                cost_class=meta.cost_class if meta is not None else "normal",
                freshness=meta.freshness if meta is not None else "static",
            ),
        )

    toolsets_present = tuple(
        sorted({ts for desc in visible for ts in desc.toolsets}),
    )
    return ToolCatalogSnapshot(
        audience=scope.value,
        tools=tuple(visible),
        toolsets_present=toolsets_present,
        total_visible=len(visible),
        hidden_above_scope=hidden,
    )


# ---------------------------------------------------------------------------
# 2. BTD6 answerability snapshot
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AnswerabilityDomain:
    """One BTD6 knowledge area and how the bot can answer about it.

    ``kind`` is ``"deterministic_fixture"`` (loaded repo data), ``"calculation"`` (a
    deterministic derived answer over that data), ``"live"`` (Ninja-Kiwi-backed, freshness
    sensitive), or ``"unsupported"`` (a known gap named explicitly so the bot never
    overclaims). ``item_count`` is ``None`` for non-fixture kinds.
    """

    name: str
    kind: str
    item_count: int | None = None
    note: str = ""


@dataclass(frozen=True)
class BTD6AnswerabilitySnapshot:
    """Bounded, truthful inventory of what BTD6 the bot can answer — domain-level only.

    Distinguishes deterministic fixtures, deterministic calculations, live data, and
    explicit unsupported areas (roadmap §4.2). It deliberately does **not** imply that a
    fixture's existence means tool/context/UI exposure — the per-tool surface lives in the
    tool catalogue snapshot.
    """

    available: bool
    data_version: str
    game_version: str
    source_label: str
    domains: tuple[AnswerabilityDomain, ...]


# Known gaps, named so an answer can say "I don't cover that" instead of guessing
# (roadmap §10 / §4.2). Curated on purpose — a small, low-drift list of areas with no
# verified owner/data path.
_UNSUPPORTED_DOMAINS: tuple[AnswerabilityDomain, ...] = (
    AnswerabilityDomain(
        "alternate_round_sets",
        "unsupported",
        note="ABR / alternate round sets are not modelled; only the standard round set.",
    ),
    AnswerabilityDomain(
        "achievements",
        "unsupported",
        note="No achievements dataset is loaded.",
    ),
    AnswerabilityDomain(
        "rogue_legends_frontier",
        "unsupported",
        note="Rogue Legends / Frontier content has no verified data path.",
    ),
    AnswerabilityDomain(
        "modified_economy",
        "calculation",
        note=(
            "Cash math is standard/Medium only; Double Cash, Half Cash, other "
            "difficulties, and farm income are NOT applied (returned as unsupported, "
            "never a guessed number)."
        ),
    ),
)


def build_btd6_answerability() -> BTD6AnswerabilitySnapshot:
    """Compose the BTD6 answerability inventory from the deterministic data owner.

    Public for every audience — BTD6 facts are not server-private. Reads loaded fixture
    counts plus the active data source; lists the deterministic calculations and the one
    live domain; ends with the explicit unsupported gaps. No model arithmetic, no scraping.
    """
    # Lazy: keep the BTD6 data layer off this module's import path until asked.
    from services import btd6_data_service

    available = btd6_data_service.data_available()
    source_label = btd6_data_service.data_source_label()
    if not available:
        return BTD6AnswerabilitySnapshot(
            available=False,
            data_version="",
            game_version="",
            source_label=source_label,
            domains=(),
        )

    ds = btd6_data_service.get_dataset()
    fixtures = (
        AnswerabilityDomain("towers", "deterministic_fixture", len(ds.towers)),
        AnswerabilityDomain("heroes", "deterministic_fixture", len(ds.heroes)),
        AnswerabilityDomain("maps", "deterministic_fixture", len(ds.maps)),
        AnswerabilityDomain("modes", "deterministic_fixture", len(ds.modes)),
        AnswerabilityDomain("rounds", "deterministic_fixture", len(ds.rounds)),
        AnswerabilityDomain("bloons", "deterministic_fixture", len(ds.bloons)),
        AnswerabilityDomain("ct_relics", "deterministic_fixture", len(ds.ct_relics)),
        AnswerabilityDomain("powers", "deterministic_fixture", len(ds.powers)),
        AnswerabilityDomain(
            "monkey_knowledge",
            "deterministic_fixture",
            len(ds.monkey_knowledge),
        ),
        AnswerabilityDomain(
            "geraldo_items",
            "deterministic_fixture",
            len(ds.geraldo_items),
        ),
        AnswerabilityDomain("bosses", "deterministic_fixture", len(ds.bosses)),
    )
    calculations = (
        AnswerabilityDomain(
            "round_cash",
            "calculation",
            note="Standard/Medium per-round and inclusive-range cash earned (rounds 1-140).",
        ),
        AnswerabilityDomain(
            "difficulty_cost",
            "calculation",
            note="Convert a Medium cost to Easy/Medium/Hard/Impoppable.",
        ),
        AnswerabilityDomain(
            "cumulative_upgrade_cost",
            "calculation",
            note="Running cost to reach a tower upgrade tier on a path, per difficulty.",
        ),
        AnswerabilityDomain(
            "paragon",
            "calculation",
            note="Degree from sacrifices, requirements for a target degree, and stats at a degree.",
        ),
    )
    live = (
        AnswerabilityDomain(
            "ct_team_status",
            "live",
            note="This server's Contested Territory bracket standing (Ninja Kiwi, freshness-sensitive).",
        ),
    )
    return BTD6AnswerabilitySnapshot(
        available=True,
        data_version=ds.data_version,
        game_version=ds.game_version,
        source_label=source_label,
        domains=fixtures + calculations + live + _UNSUPPORTED_DOMAINS,
    )


# ---------------------------------------------------------------------------
# 3. AI settings / effective-config view
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AISettingsView:
    """Audience-filtered slice of :class:`ai_config_projection_service.AIConfigSnapshot`.

    Every audience sees whether AI / natural-language replies are enabled. Admin+ also see
    effective configuration (provider, model, level/cooldown floors, override counts,
    projection drift, bound instruction profile). Platform-owner additionally sees provider
    runtime diagnostics. Fields the audience may not see stay ``None`` (never blanked at the
    prompt — withheld at construction).
    """

    guild_id: int
    audience: str
    # Visible to all
    ai_enabled: bool | None
    natural_language_enabled: bool | None
    # Admin+ only
    provider: str | None = None
    model: str | None = None
    minimum_level_default: int | None = None
    cooldown_seconds: int | None = None
    memory_window_minutes: int | None = None
    channel_override_count: int | None = None
    category_override_count: int | None = None
    role_override_count: int | None = None
    projection_drift_count: int | None = None
    instruction_profile_name: str | None = None
    # Platform-owner only
    provider_degraded: bool | None = None
    provider_last_error_type: str | None = None
    requests_observed: int | None = None
    failures_observed: int | None = None


async def build_ai_settings_view(
    guild_id: int,
    *,
    scope: AIScope,
) -> AISettingsView:
    """Compose the audience-filtered AI settings view for ``guild_id``.

    Reuses ``ai_config_projection_service.build_snapshot`` (the existing composed read
    model) and redacts by ``scope``. Guild-level today; per-channel effective settings are
    a later refinement (roadmap §2.4 / §5.5). Side-effect-free.
    """
    snap = await ai_config_projection_service.build_snapshot(guild_id)
    policy = snap.policy

    view = AISettingsView(
        guild_id=guild_id,
        audience=scope.value,
        ai_enabled=policy.enabled,
        natural_language_enabled=policy.natural_language_enabled,
    )
    if not _is_admin(scope):
        return view

    admin_fields = {
        "provider": policy.default_provider or snap.provider.provider_active,
        "model": policy.default_model,
        "minimum_level_default": policy.minimum_level_default,
        "cooldown_seconds": policy.cooldown_seconds,
        "memory_window_minutes": snap.memory.window_minutes,
        "channel_override_count": policy.channel_override_count,
        "category_override_count": policy.category_override_count,
        "role_override_count": policy.role_override_count,
        "projection_drift_count": snap.projection.drift_count,
        "instruction_profile_name": snap.instruction.profile_name,
    }
    owner_fields = {}
    if _is_platform_owner(scope):
        owner_fields = {
            "provider_degraded": snap.provider.degraded,
            "provider_last_error_type": snap.provider.last_error_type,
            "requests_observed": snap.provider.requests_observed,
            "failures_observed": snap.provider.failures_observed,
        }
    # Frozen dataclass → rebuild with the now-authorised fields populated.
    return AISettingsView(
        guild_id=view.guild_id,
        audience=view.audience,
        ai_enabled=view.ai_enabled,
        natural_language_enabled=view.natural_language_enabled,
        **admin_fields,
        **owner_fields,
    )


# ---------------------------------------------------------------------------
# 4. Policy / recent-decision explanation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecentDecision:
    """One bounded, user-safe AI decision-audit row (no raw message content)."""

    decision: str | None
    reason_code: str | None
    task: str | None
    at: str | None


@dataclass(frozen=True)
class PolicyExplanation:
    """Why the bot would (not) reply for a given message context, faithfully.

    ``reason_code`` is a documented user-safe code (``PolicyDenialReason``). The
    ``precedence_trace`` (which guild/category/channel/role layer won) and
    ``recent_decisions`` (cross-user audit history) are gated to admin+ — a regular user
    gets the outcome and reason for their own context, not the server's policy internals.
    """

    audience: str
    allowed: bool
    reason_code: str
    effective_mode: str
    effective_source: str
    effective_min_level: int
    effective_cooldown: int
    precedence_trace: tuple[str, ...] = ()
    recent_decisions: tuple[RecentDecision, ...] = ()


async def build_policy_explanation(
    ctx: MessageContext,
    *,
    scope: AIScope,
) -> PolicyExplanation:
    """Explain the reply decision for ``ctx`` by composing the policy resolver + audit.

    Calls ``ai_natural_language_policy.resolve`` (a pure read; ``dry_run`` populates the
    precedence trace only for admin+). For admin+ it also attaches a bounded recent-decision
    history. Never mutates cooldown/audit state — safe to call from a preview.
    """
    admin = _is_admin(scope)
    decision = await ai_natural_language_policy.resolve(ctx, dry_run=admin)

    recent: tuple[RecentDecision, ...] = ()
    trace: tuple[str, ...] = ()
    if admin:
        trace = decision.precedence_trace
        try:
            rows = await ai_decision_audit_service.query(
                ctx.guild_id,
                channel_id=ctx.channel_id,
                limit=5,
            )
            recent = tuple(
                RecentDecision(
                    decision=row.get("decision"),
                    reason_code=row.get("reason_code"),
                    task=row.get("task"),
                    at=_iso(row.get("created_at")),
                )
                for row in rows
            )
        except Exception:
            # Audit history is supplementary — a read failure must not sink the
            # explanation; the resolved decision above is the authoritative answer.
            recent = ()

    return PolicyExplanation(
        audience=scope.value,
        allowed=decision.allowed,
        reason_code=decision.reason_code.value,
        effective_mode=decision.effective_mode,
        effective_source=decision.effective_source,
        effective_min_level=decision.effective_min_level,
        effective_cooldown=decision.effective_cooldown,
        precedence_trace=trace,
        recent_decisions=recent,
    )


def _iso(value: object) -> str | None:
    """Best-effort ISO timestamp for an audit row's ``created_at`` (datetime or str)."""
    if value is None:
        return None
    iso = getattr(value, "isoformat", None)
    return iso() if callable(iso) else str(value)


__all__ = [
    "AISettingsView",
    "AnswerabilityDomain",
    "BTD6AnswerabilitySnapshot",
    "PolicyExplanation",
    "RecentDecision",
    "ToolCatalogSnapshot",
    "ToolDescriptor",
    "build_ai_settings_view",
    "build_btd6_answerability",
    "build_policy_explanation",
    "build_tool_catalog",
]

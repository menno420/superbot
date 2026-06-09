"""Central catalogue of every EventBus event the platform emits.

The catalogue exists so that:

1. Every ``bus.emit(event_name, ...)`` and ``bus.on(event_name, ...)``
   callsite has a single place to verify the event name against — no more
   accidental drift between emitter and listener strings.
2. ``bus`` itself can warn (and surface a metric) when production code
   touches an event name not in the catalogue, catching typos and
   leftovers from removed cogs at runtime.
3. A future migration to typed event payloads can extend this module
   without changing emit/on signatures.

Naming convention
-----------------
``<domain>.<noun_phrase>``, dots only, lowercase, no underscores in the
domain portion.  Examples:

    governance.visibility.changed
    governance.cache.invalidated
    economy.daily_claimed       (future)

Adding an event
---------------
Add the literal string to ``KNOWN_EVENTS`` below and emit it from a cog
or service.  Subscribers listen via ``bus.on("…", handler)`` or via the
``EVT_*`` constants exported from the governance package.

Implements INV-A from the platform-hardening plan.
"""

from __future__ import annotations

from governance.events import (
    EVT_CACHE_INVALIDATED,
    EVT_CLEANUP_CHANGED,
    EVT_EXECUTION_ALLOWED,
    EVT_EXECUTION_DENIED,
    EVT_VISIBILITY_CHANGED,
)

# Every event name the platform may emit.  Adding an event without
# adding it here triggers a "unknown_event_total" metric increment and
# a one-shot WARNING in the bus.
KNOWN_EVENTS: frozenset[str] = frozenset(
    {
        # ── Governance (governance/events.py) ────────────────────────────
        EVT_VISIBILITY_CHANGED,
        EVT_CACHE_INVALIDATED,
        EVT_CLEANUP_CHANGED,
        EVT_EXECUTION_ALLOWED,
        EVT_EXECUTION_DENIED,
        # ── Economy (services/economy_service.py) ────────────────────────
        "economy.balance_changed",
        # ── XP (services/xp_service.py) ──────────────────────────────────
        "xp.awarded",
        "xp.level_up",
        "xp.reset",
        # ── Moderation (services/moderation_service.py) ──────────────────
        "moderation.action_taken",
        # ── Bindings (services/binding_mutation.py, Phase 2b) ─────────────
        "bindings.changed",
        # ── Settings (services/settings_mutation.py, S4) ──────────────────
        # Advisory. Cache invalidation is inline (the pipeline calls
        # utils.guild_config_accessors.invalidate_setting_value synchronously
        # w.r.t. the mutation result), NOT event-driven — this event is
        # for downstream consumers (audit dashboards, future
        # platform_consistency collector) and never for cache consistency.
        # Subscriber failure logged + swallowed.
        "settings.changed",
        # ── Resource provisioning (services/resource_provisioning.py, S4.5)
        # Advisory.  Emitted after the pipeline writes the binding via
        # BindingMutationPipeline.  The companion "bindings.changed"
        # event continues to fire from BindingMutationPipeline (the
        # pipeline composes, not replaces).  Nothing in this event
        # drives cache consistency; subscriber failure is logged and
        # swallowed.
        "resource.provisioned",
        # ── Channel lifecycle (services/channel_lifecycle_service.py, SM PR4/PR7)
        # Advisory.  Emitted after a rename / move / delete / reorder apply
        # (single or batch).  Payload: mutation_id, guild_id, operation, outcome,
        # applied[], failed[], occurred_at.  Subscriber failure logged +
        # swallowed; Discord state is authoritative.
        "channel.lifecycle_changed",
        # ── Role lifecycle (services/role_lifecycle_service.py, SM PR5) ───
        # Advisory.  Emitted after a role create / edit / delete apply.
        # Payload: mutation_id, guild_id, operation, outcome, applied[],
        # failed[], occurred_at.  Subscriber failure logged + swallowed;
        # Discord state is authoritative.
        "role.lifecycle_changed",
        # ── Feature flags (services/rollout_mutation.py, Phase 2d PR-3) ───
        # Advisory events emitted after the DB commit + audit row land.
        # Subscriber failure is logged with mutation_id and never raised
        # — DB state is authoritative.  Payload contract is documented in
        # docs/health/platform-consistency-ledger.md §4.
        "feature_flags.changed",
        "rollout.advanced",
        "environment_tier.changed",
        # ── Audit (Phase 9c.1 — server_logging consumer) ──────────────────
        # Generic per-mutation audit signal emitted alongside each
        # pipeline's domain-specific event. Payload contract: see
        # ``services.server_logging._on_audit_action`` docstring.
        # Server_logging subscribes and routes to ``logging.audit_channel``
        # (falls back to ``mod_channel`` via the Phase 9a route table).
        # Other consumers (future audit dashboards, AI explainers) are
        # welcome to subscribe; subscriber failure is logged + swallowed.
        "audit.action_recorded",
        # ── Automation (services/automation_mutation.py, Phase 9g PR 16) ─
        # Advisory. Emitted after every automation_rules CRUD mutation.
        # The Track 6 PR 18 scheduler subscribes for cache invalidation;
        # the wizard hub (Track 8) subscribes to refresh its panel.
        "automation.rule_changed",
        # ── Participation (services/participation_mutation.py, Phase 2c PR-9) ─
        # Advisory.  Cache invalidation is inline (synchronous w.r.t. the
        # mutation result), NOT event-driven — these events are for
        # downstream consumers (audit dashboards, future notification
        # router) and never for cache consistency.  Subscriber failure
        # logged + swallowed.
        "participation.changed",
        "subscription.changed",
        "user_preference.changed",
        "user_visibility.changed",
        # ── AI policy (services/ai_policy_mutation.py, services/
        # ai_instruction_mutation.py, post-PR-#310 hardening) ─────────────
        # Advisory.  Emitted after every typed AI policy / instruction
        # write commits + the resolver cache is invalidated.  Cache
        # consistency is NOT event-driven — invalidate() runs inline
        # inside the service.  Subscriber failure logged + swallowed.
        # The "projection_failed" variant is emitted by
        # ai_policy_mutation.project_from_legacy_settings when the
        # legacy → typed projection cannot complete; payload carries
        # guild_id, settings_key, mutation_id, exc_type — never the
        # raw setting value.  See docs/ownership.md § Event ownership.
        "ai.policy.guild_changed",
        "ai.policy.channel_changed",
        "ai.policy.category_changed",
        "ai.policy.role_changed",
        "ai.policy.projection_failed",
        "ai.instruction.profile_changed",
        # Tool-orchestration profile writes (services/ai_orchestration_mutation.py,
        # Phase 3). Advisory: emitted after the orchestration_profile column is
        # written + the resolver cache is invalidated. Payload: guild_id,
        # mutation_id. Same swallow-on-subscriber-failure contract as ai.policy.*.
        "ai.orchestration.guild_changed",
        "ai.orchestration.channel_changed",
        "ai.orchestration.category_changed",
        # ── BTD6 (services/btd6_patch_service.py) ────────────────────────
        # Advisory. Emitted when patch-notes ingestion writes a BTD6
        # version strictly newer than the previously-stored latest (never
        # on the first/baseline ingest). services.btd6_version_announce
        # subscribes and posts to each guild's configured announcement
        # channel; subscriber failure is logged + swallowed. Payload:
        # version, previous_version, title, url, published_at.
        "btd6.version_detected",
        # ── Future cog-emitted facts (uncomment when first emitter lands):
        # "economy.daily_claimed",
        # "mining.harvested",
    },
)


def is_known(event_name: str) -> bool:
    """True if *event_name* appears in :data:`KNOWN_EVENTS`."""
    return event_name in KNOWN_EVENTS

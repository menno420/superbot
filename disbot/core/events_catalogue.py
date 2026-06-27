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
        # ── Game XP (services/game_xp_service.py — the shared cross-game
        # progression track, separate from chat XP by design) ─────────────
        "game_xp.awarded",
        "game_xp.level_up",
        # ── Karma (services/karma_service.py) ────────────────────────────
        # Emitted after a peer karma grant commits + audits. Payload:
        # guild_id, from_user, to_user, delta, new_total, source. Subscribers
        # (panel refresh, future analytics) react without touching the DB;
        # subscriber failure is logged + swallowed — the grant is authoritative.
        "karma.granted",
        # ── Moderation (services/moderation_service.py) ──────────────────
        "moderation.action_taken",
        # ── Automod (cogs/automod/listener.py, Q-0108) ───────────────────
        # Advisory.  Emitted after an automod rule deletes + warns (the action
        # itself audits via moderation_service).  Payload: guild_id, user_id,
        # rule, channel_id.  Subscriber failure logged + swallowed; the action
        # is authoritative either way.  See docs/ownership.md § Event ownership.
        "automod.rule_triggered",
        # ── Image moderation (cogs/image_moderation/listener.py, Q-0108) ──
        # Advisory.  Emitted after a flagged image is deleted + warned (the
        # action itself audits via moderation_service, so this is *not* a second
        # audit path).  Payload: guild_id, user_id, category (sexual/violence/
        # harassment/hate), channel_id.  Subscriber failure logged + swallowed;
        # the action is authoritative either way.
        "image_moderation.flagged",
        # ── Welcome (services/welcome_service.py, Q-0110) ─────────────────
        # Advisory.  Emitted after a join greeting is successfully posted.
        # Payload: guild_id, user_id.  The optional entry-role grant audits
        # via role_automation (so this is *not* a second audit path).
        # Subscriber failure logged + swallowed.
        "welcome.member_greeted",
        # ── Counters (services/counter_service.py, Q-0110) ────────────────
        # Advisory.  Emitted after a periodic sync renames >= 1 counter
        # channel.  Payload: guild_id, renamed (count).  No DB writes; the
        # rename is a channel edit.  Subscriber failure logged + swallowed.
        "counters.updated",
        # ── Security (services/security_service.py, Q-0111) ───────────────
        # Advisory. `raid_detected` fires when a join-rate raid is detected (the
        # staff alert + slowmode are the action); `account_flagged` fires when a
        # too-young account joins (a kick, if configured, audits via
        # moderation_service — so these are *not* a second audit path). Payloads:
        # raid_detected → guild_id, user_id, join_count; account_flagged →
        # guild_id, user_id, age_days, action. Subscriber failure logged +
        # swallowed; the detection/action is authoritative either way.
        "security.raid_detected",
        "security.account_flagged",
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
        # ── Support tickets (services/ticket_mutation.py) ─────────────────
        # Advisory. ``ticket.opened`` is emitted after a ticket row + its
        # private channel are committed; TicketCog subscribes to post the
        # welcome embed + control panel (Claim/Close) into the new channel
        # — the single UI seam that serves the command, panel-button, and
        # AI-natural-language open paths uniformly (a service must not import
        # views). ``ticket.closed`` fires after a close commits (transcript
        # already posted by the closer). Payload: guild_id, ticket_id,
        # channel_id, opener_id, subject, source (opened) / closed_by (closed).
        # Subscriber failure logged + swallowed; the DB + channel are
        # authoritative.
        #
        # ``ticket.open_requested`` is emitted by the read-only AI tool
        # ``open_support_ticket`` when a user asks the AI in natural language to
        # open a ticket: the tool validates eligibility but does NOT write —
        # TicketCog subscribes and posts a one-click [Open ticket]/[Cancel]
        # confirmation into the channel, so the actual open stays behind an
        # explicit human click (the audited mutation runs only then). Payload:
        # guild_id, channel_id, user_id, subject.
        "ticket.open_requested",
        "ticket.opened",
        "ticket.closed",
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
        # ── AI answer review log (services/ai_review_log_service.py) ──────
        # Emitted after a review entry is recorded — a "didn't-know" outcome
        # (the natural-language stage could not answer) or a user correction
        # (👎 / correction-reply on a bot AI answer). cogs/ai_review_cog.py
        # subscribes to post the entry to the guild's configured review
        # channel. Payload: entry_id, guild_id, channel_id, user_id, kind,
        # reason_code, task, route, question, answer, correction, corrected_by,
        # provider, model — all text already redacted. Subscriber failure is
        # logged + swallowed; the DB row is authoritative.
        "ai.review_logged",
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

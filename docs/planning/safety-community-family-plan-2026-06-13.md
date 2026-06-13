# Safety & community platform — family plan (2026-06-13)

> **Status:** `plan` — the lane entry doc the roadmap's *"🚨 Server safety &
> community platform"* section calls for (it had "no folio yet — the **family
> plan** below becomes the lane's entry doc"). Owner scope decisions are
> **already made** (Q-0108–Q-0112, recorded in the router + both idea docs);
> this plan turns those decisions into a **shared architecture + a sliced
> build order**, not new product direction. **Not binding** — source + merged
> PRs win.
>
> **Reviewable by clicking:** every surface below cites a `pattern_id` from
> [`../ux/pattern-library.md`](../ux/pattern-library.md) (rendered live in
> `!uxlab`) instead of describing UI in prose — the lab was built (#758/#760/#762)
> precisely so these UX choices are reviewed on pressable panels.

---

## 1. Why one family plan (not five separate plans)

The five approved features — **automod**, **server logging**, **welcome +
counters**, **image moderation**, **security tiers 1+2** — are *one platform*
with one shared shape:

- They are all **per-guild operator config**, off by default, surfaced through
  the **same settings seam** (`SettingSpec` schemas → the `!settings` widget,
  the moderation/server-management hubs, and the setup wizard).
- They are all **the automated layer beneath manual moderation** — every action
  any of them takes routes through the **existing** `services.moderation_service`
  (so escalation, audit, and DM-on-action stay one authority) and is observed by
  the **existing** `services.server_logging` subscriber. None of them is allowed
  to open a parallel action/audit/logging path.
- The reactive ones (automod, image moderation) plug into the **one**
  `core.runtime.message_pipeline` `MessageStage` chain — never a second
  `on_message` listener (the pipeline exists *because* five racing listeners was
  the bug it replaced).
- The join/leave ones (welcome, security) share `on_member_join` /
  `on_member_remove`, which today only `guild_lifecycle` touches.

Planning them together fixes the **shared config read-model shape, the shared
exempt-roles/channels safety valve, and the shared "route through
moderation_service" rule once**, so each slice is a thin, low-risk addition
rather than five re-derivations of the same seams.

## 2. The seams every slice reuses (verified 2026-06-13)

| Seam | Path | What the lane uses it for |
|---|---|---|
| Manual-moderation authority | `services/moderation_service.py` — `warn()` (escalation ladder built in), `auto_delete(message, *, reason, rule)` (`actor_type="system"`), `timeout/kick/ban` | Every automated action calls these; escalation + audit + DM stay one authority |
| Reactive message chain | `core/runtime/message_pipeline.py` — `MessageStage` Protocol, `register()/unregister()`, the canonical order table | automod + image-mod register a stage in the **auto-mod tier (10–20)**; never a raw listener |
| Event logging | `services/server_logging.py` — already subscribes `moderation.action_taken` + `audit.action_recorded` | logging v1 **extends this module** with the passive-event handlers; automod/security actions appear here for free (they go through moderation_service) |
| Per-guild config read-model | `services/moderation_config.py` pattern — defaults + frozen `*Policy` dataclass + `load_policy()` over `settings_resolution.resolve_value` | each feature gets a `*_config.py` mirroring this; **no migration** (KV `guild_settings`) |
| Config UI | `core/runtime/subsystem_schema.SettingSpec` + `register()`; `views/setup/sections/*`; the moderation/server-management hubs | declaring a `SubsystemSchema` surfaces config in `!settings`; richer panels reuse `mock_*` shapes |
| Audit / domain events | `services/audit_events.emit_audit_action`, `core/events.bus`, `core/events_catalogue.KNOWN_EVENTS` | actions audit via moderation_service; each feature emits one advisory `<domain>.*` event for observability |
| Join/leave | `on_member_join` / `on_member_remove` (today only `guild_lifecycle`) | welcome + security tier-1/2 subscribe here |

Platform-limit numbers (mass-mention/caps thresholds, the 8 MiB image cap for
image-mod, embed budgets for log/welcome embeds):
[`../operations/discord-platform-limits.md`](../operations/discord-platform-limits.md).

## 3. Shared design rules (apply to every slice)

1. **Off by default.** A fresh guild behaves exactly as today. A master
   `<feature>_enabled` flag gates each feature; individual rules/categories have
   their own enable flags under it.
2. **One exempt safety valve.** Every reactive feature reads the same
   *exempt roles* + *exempt channels* shape so an operator configures
   "staff/announcements are never touched" once per feature. (v1: CSV of IDs via
   a `str` setting parsed by the read-model; a multi-select picker is the
   phase-2 UX polish — `mock_automod_rules` shows the target.)
3. **Route through `moderation_service`, never around it.** Deletions →
   `auto_delete`; member discipline → `warn` (which owns the escalation ladder).
   No feature writes `mod_logs` or emits `audit.action_recorded` itself.
4. **Fail open.** A config-read fault, a flag-evaluator error, or a detector
   exception must let the message/join through (logged), never block legitimate
   activity. (Mirror `xp.listener._xp_participation_allowed`'s fall-open guard.)
5. **Privacy disclosed at the seam.** Deleted-message logging and image-mod's
   external API call are surfaced in the setup wizard copy (Q-0109/Q-0108).
6. **Config UI is the `mock_*` shape made real**, not a new invention — cite the
   `pattern_id` in the slice PR.
7. **Extend an existing subsystem before minting a new one.** Before registering a
   new `SubsystemSchema`, ask whether the feature *extends an existing subsystem's
   domain*. If so, add settings/bindings to that subsystem's schema — a new subsystem
   trips the whole pinned-surface cascade (hub roster · help-surface-map ·
   discoverability hook · settings-customization `###` section), an extension trips
   **none** of it. Mint a new subsystem only when the feature has its own
   identity/pipeline/lifecycle. *(Proof from the lane: automod = new subsystem, yes —
   own pipeline stage; server event logging = extension of `logging`, no — it added
   4 settings + 4 bindings to the existing schema and touched zero pinned surfaces.)*

## 4. Build order (the band-queue slots 4–9, each one session)

| Slice | Q | New surface | `pattern_id` | Notes |
|---|---|---|---|---|
| **automod v1** *(this PR)* | Q-0108 | `AutomodStage` (pipeline) + `services/automod_service.py` + `services/automod_config.py` + `cogs/automod/` | `mock_automod_rules` | 4 rule types (spam burst · invite links · excessive caps · mass mentions); delete + `warn`; exempt roles/channels; **no migration** |
| **server logging v1** ✅ *(shipped — slot 5)* | Q-0109 | extended `services/server_logging.py` with the five passive handlers + `services/server_logging_config.py`; listeners on `LoggingCog`; four event routes on the shared route table | `mock_logging_routing` | edits/deletes · join/leave · role changes; owner-configurable single-vs-per-category channel (`logging.event_routing`); privacy disclosed in the `messages_enabled` hint + the wizard logging section |
| **welcome v1 + counters** | Q-0110 | `services/welcome_service.py` (embed-only) + `services/counter_service.py` | `mock_welcome_ab`, `mock_counters` | join/leave embed + entry-role; counters = scheduled channel-rename quick-win (respect the 2/10-min rate cap) |
| **image moderation** | Q-0108 | `services/image_moderation_service.py` + an image-mod `MessageStage` | (reuse automod panel) | OpenAI `omni-moderation-latest` **only** (free, existing key); paid tiers declined; threshold ≥0.80; sends image externally → disclose |
| **security tiers 1+2** | Q-0111 | `services/security_service.py` (raid detection + account-age filter) | `mock_security_alerts` | tiers 3+4 (alt-detection / VPN) **declined** — keep absent; self-contained, no external API |

**Deliberately later / declined** (do not build in this lane without an owner
steer): welcome **phase 2** PIL cards (after phase-1 stable); the **NL event
scheduler** (Q-0112 — own AI-cost design under the Q-0082 ceiling; check existing
scheduler infra first); image-mod **paid** providers, security **tiers 3+4**
(GDPR — declined).

## 5. automod v1 — the slice shipped in this PR

**Design (settings-only, no migration — mirrors `moderation_config`):**

- `utils/settings_keys/automod.py` — the `automod_*` KV keys.
- `services/automod_config.py` — `DEFAULT_*` constants (one source of truth,
  shared with the schema), the frozen `AutomodPolicy`, and `load_policy(guild_id)`
  over `resolve_value`; plus exempt-list parsing.
- `services/automod_service.py` — the **pure** detectors (`exceeds_caps`,
  `count_mentions`, `find_invite`) + a stateful in-memory `SpamTracker`
  (per guild/user/channel sliding window) + `evaluate(message, policy)` returning
  an `AutomodVerdict | None`. No Discord I/O, fully unit-testable.
- `cogs/automod/` — `schemas.py` (the `SettingSpec`s + `SubsystemSchema` +
  `register_schemas`), `listener.py` (`process_message(bot, message) -> StageResult`:
  load policy → fail-open if disabled → `evaluate` → on a verdict, `auto_delete`
  + `warn` + emit `automod.rule_triggered` → return delete/short-circuit).
- `cogs/automod_cog.py` — `AutomodStage` (name `"automod"`, order **5**, first in
  the auto-mod tier) + the `Automod` cog (`cog_load` registers schema + stage;
  `cog_unload` unregisters; an admin `!automod` status command renders the policy).
- `core/events_catalogue.py` — `"automod.rule_triggered"` (advisory; payload
  `guild_id, user_id, rule, channel_id`).
- `config.py` — `cogs.automod_cog` added to `INITIAL_EXTENSIONS`.
- `docs/ownership.md` — the new event + service + settings keys documented.

**Rule defaults** (match the owner-reviewed `mock_automod_rules`): spam = 5
messages / 7 s; excessive caps = 70 % uppercase on messages ≥ 10 chars; mass
mentions = 4; invite links = any `discord.gg/` (binary). Every rule and the
master flag default **off** (a fresh guild is unchanged). On a hit: delete the
message + `warn` the member (moderation's own warn→timeout escalation then
handles repeat offenders — automod adds no second ladder).

**Tests:** detector unit tests (caps/mentions/invite edge cases), `SpamTracker`
window behaviour, `evaluate` exemptions + disabled-flag fall-open, the
`process_message` orchestration (mock `moderation_service` — asserts
`auto_delete` + `warn` called and the event emitted), and the
schema/defaults-alignment test (mirrors the moderation schema test).

## 5b. server logging v1 — the slice shipped as band slot 5 (Q-0109)

The passive twin of automod: where automod *acts* on messages, logging
*observes* server events. It deliberately **reuses the existing logging
subsystem** rather than registering a new one — so it trips none of the
new-subsystem pinned-surface cascade (the friction the automod slice
flagged).

**Design (settings-only, no migration — mirrors `automod_config`):**

- `utils/settings_keys/logging.py` — the new `logging_*` KV keys
  (`messages_enabled`/`members_enabled`/`roles_enabled`/`event_routing`)
  + the event-route default channel names.
- `services/server_logging_config.py` — `DEFAULT_*` constants (one source
  of truth shared with the schema), the frozen `EventLoggingPolicy`, and
  `load_policy(guild_id)`. The master switch is the **existing**
  `logging.enabled`, so one switch governs moderation + audit + event
  logging.
- `services/server_logging.py` — the five `format_*_embed` builders, the
  five `log_*` handlers (gate → resolve → send, all fail-safe + counted),
  `resolve_event_channel`, and four new entries in the shared route table
  (`events` + `message_log`/`member_log`/`role_log`, falling back to
  `events`, never `mod`).
- `cogs/logging_cog.py` — the five `@commands.Cog.listener()` methods
  (cheap structural filters → delegate) + the `!logging status` event
  summary.
- `cogs/logging/schemas.py` — schema v3: four `SettingSpec`s + four
  `BindingSpec`s + four `ResourceRequirement`s; the routing setting uses
  `allowed_values=("combined", "per_category")` for an enum picker.
- The channel routing reuses the **existing Routes panel** + the
  `BindingMutationPipeline` (the route table is generic); the
  `provision_view`/`select_view` route tables gained the four routes too.

**Privacy (Q-0109):** the `messages_enabled` hint carries the
deleted-message disclosure, and the setup wizard's logging-presets section
states it.

**Tests:** `tests/unit/services/test_server_logging_events.py` — policy
gating/routing, `load_policy` resolution, the embed builders (+ truncation),
`resolve_event_channel` mode selection, the handlers (disabled-skip / send /
missing-channel / fail-safe counters), and the cog-listener filters
(skip-bot / no-op-edit / role-diff). Subsystem doc:
[`../server-logging.md`](../server-logging.md) § "Server event logging v1".

## 6. Verification

```
python3.10 scripts/check_architecture.py --mode strict   # 0 errors
python3.10 scripts/check_quality.py --full                # CI mirror
python3.10 disbot/bot1.py                                 # boot — confirm the cog loads + stage registers
```

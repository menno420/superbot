# `/myprofile` foundation — implementation plan (wizard plan PR4)

> **Status:** `plan` — ready to execute (no open gates for PR A/PR B; PR C is
> explicitly gated). Produced by the 2026-06-10 PR4 planning session that
> Batch 10 / DT09 selected ([wizard plan](../setup-platform/setup_wizard_finalization_plan.md)
> §6 + §10 PR4; source re-verified this session — §6's backend inventory is
> still exact). Two PRs now, one gated follow-up; PR A has **zero writes** and
> rides entirely on shipped seams.

## 1. Goal

Give members a self-service **profile hub**: see and control their own
per-guild participation, subscriptions, notification preferences, and
visibility — the UI the per-user backend (migrations 027/028) has waited on
since it shipped with **zero UI callers**. Strictly self-scoped (Q-0080
stranger-grade posture: a public-bot member surface, ephemeral, rate-limited,
no other-user data, no trusted-guild assumptions).

## 2. What already exists — duplicate nothing (re-verified 2026-06-10)

| Piece | Where | State |
|---|---|---|
| Storage | `user_participation` / `user_subscriptions` / `user_preferences` / `user_visibility_overrides` (migrations 027/028, audit table included) | shipped, live |
| Audited writes | `services/participation_mutation.py` — `ParticipationMutationPipeline.set_participation / set_subscription / set_preference / set_visibility` (7-step contract: validate → write → cache-invalidate → audit → events; typed errors incl. `UnauthorizedParticipationMutationError`) | shipped; **zero UI callers** |
| Typed reads | `utils/user_config_accessors.py` — `get_participation` / `is_subscribed` / `get_preference` / `get_visibility` | shipped |
| Cache | `core/runtime/user_config.py` — per-(user,guild), TTL+size eviction, diagnostics provider | shipped |
| Declaration registry | `core/runtime/participation_schema.py` — per-subsystem `ParticipationSchema` (SubscriptionSpec / VisibilityIntent / NotificationIntent / PreferenceSpec), registered in `cog_load`; `all_schemas()` enumerates | shipped; **XP is the only registrant** |
| Feature gate | `participation.enabled` flag (declared, default **OFF**); sole consumer = the XP listener gate | shipped |
| UI idioms | the Help-editor stack (`views/help/editor.py`): ephemeral BaseView shell, picker pagination, one-service-call-per-action, re-render-from-read-model | shipped #677 |

**Entirely absent (this plan builds):** any profile UI; `on_member_join`
onboarding (PR C, gated). **Out of scope by hard rule:** the channel/command
**visibility bridge** (wizard plan PR5 — needs its own scalability/rollback
design; nothing here may touch `PermissionOverwrite`); collapsing the four
tables (ledger hard rule); command/help filtering by participation.

## 3. Decisions already made — the design envelope

- **Q-0080 (public bot):** stranger-grade — ephemeral-only, self-scoped (the
  viewer IS the subject; no member parameter), command cooldown, per-guild
  keys everywhere (already table-shaped). No new abuse surface: reads are
  cached; writes ride the existing audited pipeline.
- **Q-0081 (RPG solo core):** the profile hub is the *platform* seam future
  RPG/per-user features extend (a new subsystem registers a
  `ParticipationSchema` and appears — zero hub changes). Relationship only;
  no RPG scope here.
- **Wizard plan §6 template note, applied by lane shape:** single-field
  self-service toggles are **direct-lane** (focused, reversible,
  single-domain → the audited pipeline, per `ownership.md`); §6's
  draft→preview→commit template applies only if a *compound* profile editor
  ever exists (none planned). Deviation reasoned here, not silent.
- **Entry point:** the `/myprofile` slash (ephemeral by construction) + a
  `!myprofile` prefix alias — PR4's own naming; mirrors the
  `/server-management` ephemeral-slash precedent. No other new command names.
- **`participation.enabled` stays the runtime gate** for *behavior* (the XP
  listener); the profile hub itself is **not** gated by it — members may
  always view/set their state; the hub *labels* gated subsystems "not active
  in this server yet" so stored preferences are never silently lying.

## 4. Design

### 4.1 PR A — read-only profile card (zero writes)

`views/profile/` (new package) + a thin cog command:

- **`build_profile_embed(member, guild_id)`** — composes the typed accessors
  over `participation_schema.all_schemas()`: one section per registered
  subsystem showing participation state, subscriptions (spec label +
  subscribed?), preferences (current vs default), visibility — every value
  labeled with its default per the Q-0058 idiom. Schema-driven: a new
  subsystem registration appears with zero hub changes.
- **`ProfileHomeView(BaseView)`** — owner-locked ephemeral (the Help-editor
  shell minus the admin gate: self-service authority = being yourself;
  the pipeline re-validates on every write in PR B anyway).
- Cog: `/myprofile` (ephemeral interaction response) + `!myprofile`
  (sends the panel via `send_panel`, view owner-locked) with a
  `@commands.cooldown` (Q-0080 rate-limit floor). Lives in a new
  `cogs/profile_cog.py` (~120 LOC — far under the ceiling) registering a
  `profile` SUBSYSTEMS entry? **No** — reuse the existing `utility`
  subsystem registration to avoid a new identity-surface ripple; classify
  the command in the surface ledger (Batch 2 invariant will demand it).
- **Tests:** embed composes per-schema sections; unknown/empty schemas render
  the empty state; ownership lock; ledger classification present; zero
  mutation imports (AST pin, the access-map pattern).

### 4.2 PR B — self-service writes (the pipeline's first UI consumer)

- **Subscription toggles** (per SubscriptionSpec): button/select →
  `pipeline.set_subscription(...)` → re-render from accessors (cache
  invalidation makes the re-read truthful — the editor-stack pattern).
- **Participation opt-in/out** (per subsystem with a declared state machine):
  select → `set_participation`.
- **Preference editors:** PreferenceSpec-typed — bool → toggle; enum →
  select; int/str → modal (bounds from the spec; the seam re-validates).
- **Visibility:** per VisibilityIntent toggle → `set_visibility`.
- Every action = exactly one pipeline call (mock-spy test); typed
  `ParticipationMutationError`s render as ephemeral copy (never a crash).
- **Tests:** one-call-per-action; error-copy; unauthorized (actor≠subject)
  impossible by construction but pinned anyway (the pipeline's
  `UnauthorizedParticipationMutationError` path); live round-trip recipe.

### 4.3 PR C — `on_member_join` onboarding (GATED — do not build yet)

Needs an owner decision first (route when PR B lands): DM vs in-guild
welcome, copy, and whether a public bot may DM strangers at all (Q-0080
abuse posture). Until decided, the profile hub is discoverable via Help
(the command registers normally) — no join-time trigger.

## 5. PR slicing

| PR | Content | Risk | Migration |
|---|---|---|---|
| **A** | `views/profile/` read-only card + `/myprofile` + `!myprofile` + ledger classification + tests | Low — zero writes | none |
| **B** | write controls through `ParticipationMutationPipeline` (first UI consumer), per-spec editors, tests + live round-trip | Medium — first UI writes on a shipped-but-unexercised pipeline | none |
| **C** | join-time onboarding | **gated** (owner decision) | none |

## 6. Tests & invariants to keep green

The Batch 2 surface-classification invariant (new commands must be
classified); `test_cog_size`; `test_no_raw_sql_in_cogs` (views compose
accessors only); views-may-not-import-cogs; the participation pipeline's
existing suite (first real consumer may surface latent assumptions — treat
failures as pipeline findings, not test blockers).

**Live round-trip recipe (PR B):** boot → `/myprofile` → toggle a
subscription → accessor reflects it + audit row present → flip a preference →
reset → re-render matches defaults; second account cannot interact with the
first's panel.

## 7. Verification

`python3.10 scripts/check_quality.py --full` · `check_architecture --mode
strict` (0 errors) · `check_docs` · the live recipe on the sandbox bot.

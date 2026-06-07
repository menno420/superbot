# ADR-008: Capability-native moderator/trusted roles (role → tier grant)

**Status:** Accepted (2026-06-07)
**Supersedes:** none
**Superseded by:** none
**Relates to:** [ADR-005](005-capability-native-authority-and-flag-semantics.md)
(capability-native authority) · [`docs/capability-authority.md`](../capability-authority.md)
· owner decision Q-0006 in
[`docs/owner/maintainer-question-router.md`](../owner/maintainer-question-router.md) §19

> **Accepted.** This ADR is ratified; the implementing change lands in the same
> session (the governance tier resolver + the moderation surfaces + the
> Settings-hub role pickers). When this doc and source disagree, source wins
> (`disbot/governance/resolver.py`).

## Context

This is the final item of the server-management **PR10** moderation workstream:
let a guild grant moderation authority to **non-administrators**. Today moderation
is gated entirely by Discord permissions checked at the cog/view layer
(`@commands.has_permissions(...)` and the panel's `interaction_check`), so the only
way to let someone ban members is to give them a near-admin Discord permission.

Two pieces of existing infrastructure already point at the answer:

1. **The moderation subsystem already requires the `moderator` tier.** Its
   `visibility_tier` is `"moderator"` (`utils/subsystem_registry.py`), and
   `governance.execution.resolve_execution(ctx, "moderation.*.apply")` already
   gates on that tier via the visibility resolver. The `moderation.*.apply`
   capabilities already exist.
2. **The tier resolver is already role-aware.** `governance.resolver._resolve_member_tier`
   already promotes a `user` to `trusted` when the guild has a configured
   `trusted_tier_role_id` and the member holds it (ISSUE-015). But the `trusted`
   tier unlocks nothing today (no subsystem requires exactly `trusted`, and there
   was **no operator surface** to set the role), so it was inert.

ADR-005 §"Re-evaluation criteria" deferred a general **per-capability authorization
matrix** (capability → required tier). The owner decision (Q-0006) deliberately did
**not** ask for that matrix — it asked for a **role → existing-tier grant**, which is
a narrower, lower-risk mechanism that reuses the tier system already in place.

This is the single highest-stakes change in the server-management plan — it changes
**who can ban members** — so it warrants this ADR and a thorough authority test
matrix.

## Options

- **A (chosen): role → `moderator` tier (capability-native).** A configured role
  resolves to the existing `moderator` tier in the governance tier resolver. The
  moderation surfaces (cog commands + panel) authorize through the capability
  resolver, so they admit anyone at `moderator` tier — whether that tier came from
  a Discord permission or the configured role. Reuses the tier system + the existing
  `moderation.*.apply` capabilities, scoped to moderation.
- **B: a general per-capability tier matrix** (capability → required tier). Rejected
  for now — it is the broad mechanism ADR-005 §5 deferred, far larger than the goal,
  and the owner explicitly chose A over it. It stays deferred.
- **C: a cog-level role allowlist beside Discord perms.** Rejected — a parallel
  authority system divorced from the tier/capability model; every future surface
  would have to learn about it.

## Decision

**ACCEPTED — A** (owner-ratified 2026-06-07, Q-0006).

1. **Tier grant in the governance tier resolver.** `_resolve_member_tier` gains a
   **moderator-role** grant symmetric to the existing trusted-role grant: a member
   holding the guild's configured `moderator_tier_role_id` resolves to the
   `moderator` tier. Both grants only **raise** a member's tier — never lower one
   computed from real Discord permissions — and compose (the higher wins). A
   config-read failure fails toward the **lower** tier, so a configured role can
   only ever *add* standing, never remove it or escalate on error.
2. **Behaviour-preserving OR-gate on the surfaces.** The moderation cog commands and
   the moderation panel authorize on `Discord permission` **OR** the governance
   capability. The Discord-permission path is unchanged and evaluated first, so
   **no one who can moderate today loses access**; the capability path only adds the
   configured-role grant. On denial the cog raises `commands.MissingPermissions` so
   the existing error UX is preserved.
3. **Configured via the Settings hub (administrator floor).** The `moderator_role`
   and `trusted_role` are role-typed `SettingSpec`s on the moderation schema
   (`input_hint="role"`), written through the audited `SettingsMutationPipeline` and
   gated by `moderation.settings.configure` — which resolves to the **administrator
   floor** via `actor_holds_capability`. **Only administrators decide who
   moderates.** This also finally makes the previously inert trusted role
   configurable.
4. **The trusted role is wired symmetrically.** Same read path
   (`config_arbitration.get_*_tier_role`), same grant shape, same Settings-hub
   surface.

### Scope / boundaries (deliberate, v1)

- **Moderation *settings* configuration stays at the administrator floor.** A
  role-granted moderator can take moderation *actions* but cannot change moderation
  *config* (warn threshold, escalation, the role settings themselves) — those route
  through `actor_holds_capability`, which is untouched here.
- **The general per-capability tier matrix (ADR-005 §5) remains deferred.** This ADR
  introduces a role→tier *grant*, not a capability→tier *matrix*.
- **Slash-command UI gating is unchanged.** `/moderation` keeps its
  `default_permissions(moderate_members=True)` (a Discord-side UI default). A
  role-granted moderator reaches the moderation panel via `!modmenu` or the Help
  menu (both honour the grant), not necessarily the slash entry. Loosening the
  slash UI default for everyone was out of scope.

## Consequences

- A guild can grant moderation authority by assigning a role — no near-admin Discord
  permission required — set from the existing Settings hub with a native role picker.
- The grant is one tier promotion, so it is consistent everywhere the tier is read:
  the role-granted moderator also *sees* Moderation in their Help menu and passes the
  panel gate, with no per-surface special-casing.
- The previously inert trusted role becomes configurable and behaves symmetrically.
- No regression: every member who could moderate before still can (the OR keeps the
  Discord-permission path intact).

## Security properties (pinned by tests)

- **Grant via role:** a member with the configured moderator role (and no mod
  permission) resolves to the `moderator` tier and is admitted.
- **No escalation:** the grant only raises a tier; a member at `staff`/`user` is not
  pushed above `moderator`, an administrator/owner is never demoted, and a
  config-read failure yields no grant. An explicit DB capability revoke still wins
  (it is checked downstream in `resolve_execution`).
- **No regression:** a member with the Discord permission is admitted via the
  permission path regardless of the role config.
- **Cross-guild deny:** the configured role id is read for the **target** guild and
  matched against the member's roles **in that guild**; a role configured in guild A
  cannot grant the tier in guild B.
- **Admin-only configuration:** setting the role requires the administrator floor
  (`moderation.settings.configure`).

## Re-evaluation criteria

Revisit if a general per-capability authorization matrix (ADR-005 §5) is genuinely
needed (this ADR intentionally does not introduce one), if a tier grant is wanted for
a surface other than moderation, or if the "grant only ever raises" / "fail toward
the lower tier" posture proves wrong in practice.

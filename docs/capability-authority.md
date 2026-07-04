# Capability-native authority + mutation kill-switches

> **Status:** `binding` — (reference for the implemented system). Decision of record:

[`docs/decisions/005-capability-native-authority-and-flag-semantics.md`](decisions/005-capability-native-authority-and-flag-semantics.md)
(Accepted, implemented in PR #518). When this doc and source disagree, source wins
(`disbot/governance/capability.py`).

This is the contract for **how a settings / binding / provisioning mutation is
authorized**, and for the two operator **kill-switches**. It replaced the old
placeholder "are you an administrator?" floor (ADR-005 A1) and wired the previously
inert `*_PRIMARY` flags as real kill-switches (ADR-005 F1).

---

## 1. The resolver

```python
# disbot/governance/capability.py
async def actor_holds_capability(
    actor, guild, capability: str, *, actor_type: str = "user",
) -> CapabilityDecision
```

`CapabilityDecision` is a frozen dataclass: `allowed`, `capability`,
`required_tier`, `member_tier`, `reason` (the `reason` becomes the raised error's
message at the call site).

**Layer:** lives in `governance/` and imports only `utils` / `core`
(`utils.visibility_rules`, and `governance.execution` for the override read). It is
called from the service pipelines via a **function-local import** — the established
cycle-avoidance pattern.

### v1 policy (in order)

1. **`system` / `backfill` bypass.** Scripted ops and migrations are allowed without
   a member context (never dereferences `actor`/`guild`).
2. **Target-guild membership.** A non-system actor is **denied** unless it is a
   member of the **target** `guild` (`actor.guild.id == guild.id`). Authority is
   bound to the write target, so being privileged in guild A cannot authorize a
   write to guild B.
3. **Platform-owner override (Q-0212).** If the actor is the configured bot owner
   (`config.is_platform_owner` / `config.BOT_OWNER_USER_ID` — the
   `PermissionTier.PLATFORM_OWNER` deploy allowlist), the mutation is **allowed**
   regardless of Discord tier (`member_tier` reported as `"owner"`), so the bot
   owner can configure the bot in **any guild they are a member of** even without
   Discord permissions there. Placed **after** step 2 (so it composes with the
   target-guild membership invariant — no cross-guild escalation) and **before** the
   revoke overlay (so a guild cannot revoke the platform owner). Single source:
   `config.is_platform_owner`, the same helper every other authority seam keys on.
4. **Administrator floor, keyed on the declared capability.** The required tier is
   `administrator` (`_DEFAULT_REQUIRED_TIER`), computed against the **target**
   guild's owner via `utils.visibility_rules.get_member_visibility_tier`. An
   **empty** `capability_required` resolves to this same floor — it does **not**
   mean "no auth" (the misleading `SettingSpec` docstring was corrected).
   - **`setup_delegate` exception (Q-0098, P0-3 arc PR 3).** When the write carries
     `actor_type="setup_delegate"`, this floor is satisfied **by the delegation
     itself** — the server owner delegated *apply* authority to a (possibly
     non-administrator) member via `/setup-delegate`. It is authorized here like
     `system` / `backfill`, but deliberately **not** at step 1: a delegate must
     still pass step 2 (target-guild membership) and **stays subject to** the
     step-5 revoke overlay. The token is minted **only** by
     `services.setup_operations.apply_operations`, which re-verifies the live
     `setup_access.can_apply_setup` against a fresh `SetupSession` before doing so
     (a stale view gate is never trusted), and the delegated write is **audited as
     `setup_delegate`** so it stays distinguishable from an administrator write. An
     AST fence (`tests/unit/invariants/test_setup_delegate_actor_boundary.py`)
     confines the token to that minter, the resolver here, and the three pipelines'
     allow-sets.
5. **Revoke-only per-guild overlay.** For a declared (non-empty) capability, an
   explicit `allowed = False` row in `capability_execution_overrides` (read via
   `governance.execution.get_capability_override`, which reuses the existing cache —
   no new SQL path) turns an otherwise-allowed actor **off**. An explicit
   `True` is **never** used to grant a below-floor actor (no privilege escalation via
   a guild-config row). Overlay read failures degrade to the base (admin-floor)
   decision.

> **v1 keeps a single administrator floor for every capability.** The
> `CapabilityDecision.required_tier` field is shaped so a future per-capability
> tier matrix (capability → required tier) can replace the constant without
> touching the pipelines. That is the documented next step (see §5).

> **Platform-owner override spans more than this resolver (Q-0212).** Step 3 covers the
> *capability resolver* (settings / binding / provisioning mutations). The same
> `config.is_platform_owner` check also gates the **command decorators**
> (`core.runtime.permission_checks.admin_or_owner` / `app_admin_or_owner`, replacing
> `has_permissions(administrator=True)` bot-wide) and the **view** authority gates
> (`views.base.interaction_is_admin` / `member_is_admin`), so the bot owner passes every
> `administrator`-tier gate in any guild they are a member of. Two CI guards
> (`tests/unit/invariants/test_owner_override_guards.py`) keep a raw admin gate from
> re-locking the owner out (the #1573 → #1577 miss-class). Full record: router Q-0212.

---

## 2. Who consumes it

The three mutation pipelines delegate their authority check to the resolver, each
passing **its target guild** and the declared capability:

| Pipeline | Entry | Capability source |
|---|---|---|
| `services.settings_mutation.SettingsMutationPipeline.set_value` | `_validate_authority(spec, guild, actor, actor_type)` | `SettingSpec.capability_required` |
| `services.binding_mutation.BindingMutationPipeline.set_binding` / `clear_binding` | `_validate_authority(spec, guild, actor)` | `BindingSpec.capability_required` |
| `services.resource_provisioning.ResourceProvisioningPipeline.provision` | `_validate_actor_authority(capability, guild, actor, actor_type)` | the catalogue `ProvisioningOption.capability_required` |

Each raises its own `Unauthorized*Error(decision.reason)` on deny. Audit emission
and cache invalidation still fire on success exactly as before.

---

## 3. The kill-switches (F1)

Two operator flags become **real** emergency off-switches:

| Flag | Gates | Consulted at |
|---|---|---|
| `settings.mutation.primary` (`SETTINGS_MUTATION_PRIMARY`) | all scalar settings writes | `set_value` entry (`_check_mutation_enabled`) |
| `resource_provisioning.primary` (`RESOURCE_PROVISIONING_PRIMARY`) | all resource provisioning | `provision` entry (`_check_provisioning_enabled`) |

Both go through one helper:

```python
# disbot/core/runtime/feature_flags.py
async def is_operator_disabled(flag_name, guild_id=None) -> bool
```

**Safety contract — the important part:**

- **Default = ALLOW.** `is_operator_disabled` returns `True` **only** when the flag
  resolves to `False` from an *explicit operator override* (source `env`,
  `db_guild`, or `db_global`). The declared default (`default_value=False`) and the
  bootstrap fallback do **not** count as disabled — so untouched guilds keep working.
- **Fail OPEN.** The pipelines wrap the check in `try/except` and **allow** on error:
  a flag-store outage must never brick writes. (This is the opposite of
  `config_arbitration`, which fails toward the legacy-read path — each surface fails
  to *its* safe state.)
- The disabled path raises a typed `SettingsMutationDisabledError` /
  `ResourceProvisioningDisabledError` **before** any DB write, audit row, or Discord
  call — a disabled pipeline has zero side effects.

Operators disable a pipeline by setting the flag OFF via the usual `SUPERBOT_FF_…`
env override or a DB flag override; they re-enable by clearing it.

> **Amendment recorded at ratification:** ADR-005's draft placed F1 in
> `core/runtime/config_arbitration.py`. That file is a read-only config seam, so the
> kill-switches were wired at the mutation-pipeline entry points instead.

---

## 4. Panel callbacks must re-check authority

`BaseView` only locks a panel to its **invoker** — it does not enforce an authority.
A mutating panel may be reachable through an entry point that is **not** admin-gated
(notably the Help menu via `build_help_menu_view`), so its callbacks must re-check.

Use the shared helper:

```python
# disbot/views/base.py
def interaction_is_admin(interaction) -> bool   # matches @has_permissions(administrator=True)
```

Applied so far:

- `cogs.chain_cog._ChainMenuView.interaction_check` — gates **all** chain buttons
  (create / delete / set / clear), every entry path.
- `views.games.rps_panel._RpsTournamentMatchupButton` + `_RpsMatchupSelect` — re-check
  admin before dispatching `!rpsmatchup`.

**Rule for new mutating panels:** if a panel mutates state and is (or could become)
reachable without an admin-gated entry point, re-check authority in `interaction_check`
(whole panel) or at the callback (single action) with `interaction_is_admin`. Match
the authority of the equivalent typed command.

---

## 5. What's v1 vs follow-on

- **Now (v1):** authority is capability-*routed* but the policy is a single
  administrator floor + per-guild revoke. Behaviour for the common case is identical
  to the old admin floor; the seam is what changed.
- **Unblocked follow-on:** the capability-native **settings/bindings UI** (Ideas-Lab
  §4.5) — RC-4 no longer "spreads placeholder authority."
- **Shipped (ADR-008) — role → tier *grant*, not the matrix.** Moderation authority is
  now capability-native via a **tier grant**: a configured `moderator_role` (and the
  symmetric `trusted_role`) promotes a member's tier in the governance tier resolver
  (`governance.resolver._resolve_member_tier`), so the moderation surfaces — which gate
  on `resolve_execution` (the moderation subsystem's `visibility_tier` is `moderator`),
  not on `actor_holds_capability` — admit role-granted moderators. This is a narrower
  mechanism than the per-capability matrix below and does **not** change this
  resolver's single-floor policy. See
  [`docs/decisions/008-moderator-role-capability-native-authority.md`](decisions/008-moderator-role-capability-native-authority.md).
- **Shipped (Q-0045, option b) — the declared-tier *read* path, not a grant.**
  `GovernanceContext.member_tier`, when set, is preferred **verbatim** by the same tier
  resolver: member derivation *and* the ADR-008 role grants are skipped (the caller
  declared the *effective* standing to evaluate), and a value outside
  `VISIBILITY_TIERS` is ignored with a warning — so the input can never escalate or
  demote anyone. It exists **only** for read-only audience simulation (Help Preview,
  the `help_advertises_locked` drift baseline, via
  `services.access_projection.AccessContext.member_tier`); no execution or mutation
  path constructs a declared-tier context, and simulated reads must label their limits
  (adaptive plan §16.4). Pinned by
  `tests/unit/governance/test_declared_tier_input.py`.
- **Future policy (still deferred):** a per-capability tier matrix (e.g. some settings
  need only `moderator`) replaces `_DEFAULT_REQUIRED_TIER` *here*, in
  `actor_holds_capability`. ADR-008 deliberately did **not** introduce this — it stays
  deferred per the ADR-005 re-evaluation criteria.
- **Broaden the guard:** audit other Help-reachable mutating panels and apply the
  `interaction_is_admin` pattern where missing.

---

## 6. Where the coverage lives

| Guarantee | Pinned by |
|---|---|
| Resolver policy (bypass, target-guild deny, admin/staff, empty-cap floor, revoke overlay, no-escalation, overlay-uses-target-id) | `tests/unit/governance/test_capability.py` |
| `setup_delegate` authority (below-floor allow, still needs target-guild membership, still revocable) — Q-0098 | `tests/unit/governance/test_capability.py` |
| `setup_delegate` minted only by `apply_operations` + live re-verification + threaded to the binding pipeline | `tests/unit/services/test_setup_delegate_apply.py`, `tests/unit/invariants/test_setup_delegate_actor_boundary.py` |
| Settings: authorized/denied, revoke overlay, kill-switch default/disabled/fail-open, cross-guild deny | `tests/unit/services/test_settings_mutation_pipeline.py` |
| Provisioning: authorized, below-admin deny, system bypass, kill-switch trio | `tests/unit/services/test_resource_provisioning_pipeline.py` |
| Bindings: capability deny/allow (actor must be a member of the target guild) | `tests/unit/bindings/test_binding_mutation_pipeline.py` |
| `is_operator_disabled` source discrimination (explicit-OFF only) | `tests/unit/schema/test_feature_flags_declarations.py` |
| Panel guards: non-admin blocked on chain panel + RPS matchup | `tests/unit/views/test_panel_command_gaps.py` |
| Moderator/trusted role tier grant (grant-via-role, no-escalation, no-regression, precedence, cross-guild deny, fail-toward-lower) — ADR-008 | `tests/unit/governance/test_role_tier_grants.py` |
| Moderation surfaces OR-gate (cog `_require_mod` + panel `interaction_check`: permission path, capability path, denial) — ADR-008 | `tests/unit/cogs/test_moderation_role_authority.py` |

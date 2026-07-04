# Strand 1 · Kernel Spine — ⑨ The Authority Engine (`authority_ref` + owner override)

> **Status:** `design` — Phase-B foundational design, buildable depth. DOCS-ONLY (changes no
> `disbot/` code; old repo stays frozen). This is **K6** in the design-spec §9.1 kernel order —
> `authority` (`actor_holds_capability` + `CapabilityDecision` ported field-for-field; capability
> strings namespace-validated). It designs the ONE thing the frozen upstream leaves open: the
> `authority_ref → lane` resolution, owner-override-once-at-top across permission+capability+
> channel-access, and the transparency-audit contract.
> **Design INTO:** design-spec §4.1/§4.2/§4.3 (settings authority field), §1.3 (ownership / workflow
> "resolve authority" first step), §2.2 (the two-lane model, now folded behind ONE ref).
> **Design AGAINST, never reverse:** router Q-0219…Q-0237, esp. **Q-0237(d) ONE `authority_ref`**.
> **Buildable-depth test:** a fresh agent builds K6 from this spec + the frozen upstream contracts
> making zero further design decisions; every unclosable fork is in §8 (owner-gated ones as
> options+recommendation, never decided).
>
> **Source-wins carry (Q-0120):** there is **no `WorkflowResult` class** and **no
> `disbot/core/contracts.py:48-52`** in shipped source (audit A's cite fabricated, FJ L-4/L-25). An
> authority denial maps to the frozen §2.7 outcome vocab built on the **real** shipped constants —
> `BLOCKED` (`services/lifecycle/contracts.py:50`) — and the resolver's dispatch analogue is
> `StageResult` (`message_pipeline.py:181`). This engine returns `allowed: bool` + a `DenialReason`;
> the K8 resolver maps a denial to `BLOCKED`/`error_class=denied`. No new outcome constant.
>
> **Hardening pass (design-closer, 2026-07-04).** This revision closes the seam-consistency review:
> (1) the authority kernel is now **discord-free** — the discord `Member`→tier read is pre-computed
> by the surface adapter and threaded on `ActorRef.member_tier` (spec 02 seam correction), so
> `AuthorityRequest` carries no discord object; (2) the `TransparencyAudit` is **not** routed through
> the 11-field mutation `emit_audit_action` seam — it rides the `TransparencySink` port (this engine)
> + the `override_applied` flag on the resolver's `command.dispatched` observability trace (spec 02),
> reconciling the two siblings; (3) `AccessMode` keeps the **shipped name-stable value strings**;
> (4) `classify_authority_ref` is pinned to an exact total predicate (dotted ⇒ CAPABILITY lane, tier
> tokens case-sensitive); (5) `ChannelAccessDecision` gains a `detail` field so `COMMANDS_DISABLED`
> and `CHANNEL_NOT_ALLOWED` are distinguishable; (6) `lane_would_deny` / `denial_message` /
> `is_bootstrap` provenance / `owner_override_holds` body / `is_owner`-vs-`owner_override` are each
> pinned. Two mis-cites corrected (`visibility_rules.py` line numbers + `is_tier_sufficient`
> signature). Verified against shipped source this session: `capability.py:71/85/98-113/125/48-51/27/
> 157-171/174-193`, `command_access.py:71/184-186/256-414/351`, `config.py:40/46-73`,
> `visibility_rules.py:21/44/61`, `services/lifecycle/contracts.py:48-52/77`.

---

## 1. Summary + the exact undesigned gap

**What already exists (anti-pad — not restated).** The shipped `actor_holds_capability`
(`governance/capability.py:71`) already implements the config/governance lane field-for-field:
system/backfill bypass (`:85`), target-guild membership binding (`:98-113`), platform-owner override
(`:125`), ADMINISTRATOR floor (`:48-51 _DEFAULT_REQUIRED_TIER`), setup_delegate, revoke-only overlay
(`:157-171`). The tier lane already exists as `get_member_visibility_tier` (`utils/visibility_rules.
py:44`) + `is_tier_sufficient` (`:61`), over `VISIBILITY_TIERS` (`:21`). The design-spec §2.2 already
frames the two lanes; §4.4 already states "empty `capability_required` ⇒ ADMINISTRATOR floor governs
*who may change*, orthogonal to `activation`." The sibling **C-1 resolver**
(`02-resolver-error-envelope.md`) already owns the fixed order and calls this engine at its step 1.
The sibling **compiler** (`01-compiler-snapshot-amendments.md` P4) already declared it will call
`authority.validate(ref)`. **This design does not re-specify those.**

**The genuinely-undesigned gap this closes:**

| Gap (verified) | Shipped / upstream reality | This design (K6) |
|---|---|---|
| **Two author-facing fields, not one** | design-spec §2.2 still declares `capability_required` **and** `audience_tier`; Q-0237(d) collapses them to ONE `authority_ref`, but nobody designed the classification/resolution | `authority_ref: str` → a **total, non-overlapping lane classifier** (§3.2) + `validate_authority_ref` (compile) + `resolve_authority` (runtime). One string, one lane, always |
| **Owner-override is copy-pasted ~11-16× and channel-blind** | `is_platform_owner` re-checked in 6 mutation services (5 via a duplicated `_check_admin`), 5 views, `governance/writes.py:96`, `governance/resolver.py:223`, `capability.py:125`; **`command_access.py:351` bypasses only *bootstrap* commands** → owner denied a non-bootstrap command in a `SELECTED_CHANNELS`/`DISABLED_EXCEPT_BOOTSTRAP` guild (L-12) | ONE `owner_override_holds(user_id, is_member)` predicate, computed **once at the top** of `resolve_authority`, its verdict threaded into the channel-access lane so owner bypasses **any** command's channel restriction (the L-12 non-bootstrap-deny fix) |
| **Channel-access is a second, owner-blind gate** | `resolve_command_access` (`command_access.py:256-414`) is a standalone channel/lifecycle/DM/bootstrap gate that never consults owner tier | **folded in** as `resolve_channel_access` (§3.4) — sheds lifecycle/DM (→ K5 admission), keeps mode + allowed-channels + bootstrap bypass, **honors the once-computed `owner_override`** |
| **Transparency audit unimplemented** | grep finds **zero** transparency emit anywhere (L-12); Q-0227's promise that an owner sees when the bot-owner used elevated authority in their guild has no code | the `TransparencyAudit` contract (§3.5): trigger = would-not-otherwise-authorize, dual sink via the `TransparencySink` port + the `command.dispatched` `override_applied` flag, no-log-channel fallback (owner-gated policy, §8-c) |

**Where this sits in the spine everyone consumes** (the K8 resolver's fixed order, spec 02 §3.2):
`admission → **authority (K6, this engine)** → validate (incl. channel-access lane, this engine) →
cooldown → [ack] → audit (incl. transparency emit, this engine's contract) → dispatch → render`.

---

## 2. Files/modules it becomes

New `sb/` paths (layer table design-spec §1.1 — `kernel/authority/` imports `spec`, `namespace`,
`observability`, and adapter ports it defines; it is now **discord-free** — the discord `Member`→tier
read moved to the adapter (§7); **must NOT** import `domain`, `manifest`, `adapters` internals,
`kernel/interaction`):

| Path | Owns |
|---|---|
| `sb/spec/authority.py` | **Frozen leaf** (dependency-free, stdlib only): `Lane` enum, `TIERS` (ported `visibility_rules.py:21`), `ADMIN_FLOOR_TIER = "administrator"`, `classify_authority_ref(ref) -> Lane` (pure syntactic, pinned §3.2), `validate_authority_ref(ref, reserved_capabilities) -> None` (compile-time; raises `BadAuthorityError`), `is_tier_sufficient(member_tier: str, required_tier: str) -> bool` (pure order compare over TIER STRINGS — ported `visibility_rules.py:61`; takes tier tokens, **not** a member object). Importable by the compiler (P4) and the namespace with no cycle. |
| `sb/kernel/authority/owner.py` | `owner_override_holds(user_id: int \| None, is_member: bool) -> bool` — the SINGLE owner-override predicate (`:= is_platform_owner(user_id) and is_member`, §3.3 step 4); `is_platform_owner(user_id)` ported from `config.py:46-73` (deploy-config leaf). |
| `sb/kernel/authority/decision.py` | `AuthorityRequest`, `AuthorityDecision`, `ChannelAccessDecision`, `CapabilityDecision` (ported), `TransparencyAudit` dataclasses. |
| `sb/kernel/authority/resolve.py` | `resolve_authority(req: AuthorityRequest) -> AuthorityDecision` (the two-lane resolver + owner-override-once). **Discord-free**: consumes the pre-computed `req.member_tier` string; never dereferences a discord object. |
| `sb/kernel/authority/channel_access.py` | `resolve_channel_access(policy, channel_id, *, owner_override, is_bootstrap, is_operator, is_owner) -> ChannelAccessDecision` — the folded-in channel-access lane. |
| `sb/kernel/authority/transparency.py` | `build_transparency_audit(auth, channel, *, actor_id, guild_id, target_key, surface, clock) -> TransparencyAudit \| None` (the trigger predicate + payload build) + the `TransparencySink` **port**. |
| `sb/adapters/discord/member_tier.py` | `member_tier_from_member(member, guild_owner_id: int) -> str` — the **discord-aware** tier read (ported `get_member_visibility_tier`, `visibility_rules.py:44`; reads `member.guild_permissions` / `member.id == guild_owner_id`). Called by each surface adapter when it builds `ActorRef.member_tier` (§3.3). This is the ONLY module that reads discord permissions for authority. |
| `sb/adapters/discord/transparency_sink.py` | concrete `TransparencySink`: bot-log send, server-log send, owner-DM-digest fallback (the only module that touches Discord channels for this). |

Shipped paths it **retires** (fold-in, not delete-in-place — old repo stays frozen):

| Shipped path | Fate |
|---|---|
| `governance/capability.py` `actor_holds_capability` / `CapabilityDecision` | ported field-for-field as the **CAPABILITY lane** inside `resolve_authority` (§3.3) |
| `utils/visibility_rules.py` `get_member_visibility_tier` (`:44`) / `is_tier_sufficient` (`:61`) | split: pure order compare over tier strings → `sb/spec/authority.py` (leaf); discord-aware tier read → `sb/adapters/discord/member_tier.py` (`member_tier_from_member`) — the **TIER lane** input, pre-computed by the adapter |
| `core/runtime/command_access.py` `resolve_command_access` (`:256-414`) | **folded in** → `resolve_channel_access` (§3.4); lifecycle/DM legs move to K5 admission (spec 02 step 0); the `:351` bootstrap-only bypass generalizes |
| `core/runtime/command_access.py` `is_bootstrap_command` (`:71`) | ported as the **K1/registry** bootstrap oracle (§3.4 CONSUMED) — the caller computes `is_bootstrap = is_bootstrap_command(target.key)` before `resolve_channel_access`; the classification is a name/registry property, not owned here |
| the **5 duplicated** `_check_admin` (`ai_instruction_mutation.py:51`, `ai_orchestration_mutation.py:66`, `help_overlay_mutation.py:79`, `btd6_source_mutation.py:48`, `ai_policy_mutation.py:108`) | deleted; each becomes the owning spec's `authority_ref=""` (ADMIN floor) resolved through this engine |
| the ~11-16 authorization `is_platform_owner` call sites (settings/ai_*/bot_knowledge/setup_access mutations; `views/base.py:109,124`; `views/{btd6,settings,tickets,starboard}/*`; `governance/writes.py:96`; `governance/resolver.py:223`) | collapse to ONE `owner_override_holds` at the top of `resolve_authority`; downstream axes read the flag, never re-derive it |

---

## 3. The complete public contract

`[S]` marks the one manifest **spec** field this engine reads — **`authority_ref` only**. All
runtime-request fields and every decision field carry no S/A/O tag (not authored, not simulated). In
particular **`denial_message` is engine-generated generic copy, not a spec field** (§3.3) — corrects
the earlier "`[S]`-derived" tag.

### 3.1 The declared field — ONE `authority_ref`

```python
# on CommandSpec / PanelActionSpec / SelectorSpec / SettingSpec / BindingSpec / ResourceRequirement
authority_ref: str = ""      # [S] — replaces §2.2's capability_required + audience_tier (Q-0237d)
```

One string per surface/spec. **Supersedes** the design-spec §2.2 two-field pair (L-13/X-8, stale vs
Q-0237). Mutual exclusivity is now **structural** (one string classifies to exactly one lane — no
"leave the other empty" rule to violate).

### 3.2 The `authority_ref → lane` resolution table (canonical, owned)

`classify_authority_ref(ref)` is a **pure syntactic** function. The exact predicate (pinned — total,
deterministic, no ambiguous inputs):

```python
def classify_authority_ref(ref: str) -> Lane:
    if ref == "":                 return Lane.CAPABILITY   # empty ⇒ ADMIN floor
    if "." in ref:                return Lane.CAPABILITY   # ANY dotted string ⇒ capability lane
    if ref in TIERS:              return Lane.TIER         # exact, case-sensitive match (TIERS are lowercase)
    raise BadAuthorityError(ref)  # a non-dotted, non-tier token — unclassifiable
```

- **"contains a dot" ⇒ CAPABILITY lane, always.** A malformed dotted string (`"a.b"`, `"a.b.c.d"`)
  classifies to CAPABILITY, then **fails the 3-part format check** inside `validate_authority_ref`
  with `FormatError("capability_not_3_part")` (aligns with the compiler 01 P4 `bad_authority` →
  `COMPILE_ERROR`). Classification and format-validation are two steps: classify never raises on
  arity, only on "neither dotted nor a tier token."
- **Tier tokens are matched case-sensitively** against `TIERS` (all lowercase). `"Administrator"`
  ≠ `"administrator"` — the former is not in `TIERS`, so it raises `BadAuthorityError` at compile
  time (an author must write the lowercase token). No silent case-folding.

The three lane cases are total and non-overlapping — a dotted capability and a single-word tier token
can never collide:

| `authority_ref` value | `Lane` | Runtime resolution | Compile check (`validate_authority_ref`) |
|---|---|---|---|
| `""` (empty) | `CAPABILITY` (**ADMIN floor**) | ADMIN floor (`member_tier ≥ administrator`), **no** revoke overlay (ports `capability.py:27` "empty resolves to the floor, NOT no-auth") | always valid |
| `"{subsystem}.{resource}.{action}"` (dotted, 3 parts) | `CAPABILITY` | ADMIN floor **+** revoke overlay keyed on `ref` (`capability_execution_overrides`) | ref namespace-reserved (K1 P3); 3-part format + reserved-prefix rule `subsystem_registry.py:7` |
| `"user" \| "trusted" \| "staff" \| "moderator" \| "administrator" \| "owner"` | `TIER` | `is_tier_sufficient(member_tier, ref)` — the shipped visibility-tier check | `ref ∈ TIERS` (case-sensitive) |
| dotted but not 3-part (`"a.b"`, `"a.b.c.d"`) | `CAPABILITY` (classifier) | — (never runs; rejected at compile) | **`FormatError("capability_not_3_part")`** → `bad_authority` |
| anything else (no dot, not a tier) | — | — | **`BadAuthorityError`** (compiler `bad_authority` → `COMPILE_ERROR`, spec 01 P4) |

**ADMIN-floor semantics (owned).** Empty `authority_ref` ⇒ CAPABILITY lane at the administrator
floor — the shipped mutation-pipeline invariant, verbatim, at its shipped scope. Under v1 policy
**every** CAPABILITY-lane ref resolves to the administrator tier (`capability.py:48-51`); the
dotted string differs from `""` only in that it carries a per-guild **revoke** key. A future
capability→tier matrix replaces the constant with a lookup **without touching this table** (the
shipped forward-compat note ported).

### 3.3 `resolve_authority` — the runtime resolver (owner-override once at top, discord-free)

```python
@dataclass(frozen=True)
class AuthorityRequest:
    authority_ref: str            # [S] from target.spec
    actor_type: str = "user"      # "user" | "system" | "backfill" | "setup_delegate" (ported)
    user_id: int | None = None    # actor identity — for the owner predicate; None for scripted actors
    guild_id: int | None = None   # the TARGET guild id (the write target); None only for scripted bypass
    is_member: bool = False       # actor is a member of the TARGET guild — asserted by the caller
                                  #   (adapter: `guild_id is not None and not actor.is_dm`; K7 cross-guild: real check)
    member_tier: str | None = None  # PRE-COMPUTED tier string in the target guild (adapter, §2); None for scripted / non-member

@dataclass(frozen=True)
class AuthorityDecision:           # the frozen 10-field shape (shared-vocab §2.3; 02 imports it — RC-2)
    allowed: bool
    authority_ref: str
    lane: Lane                    # CAPABILITY | TIER
    required_tier: str            # "administrator" (capability lane) | the tier token (tier lane)
    member_tier: str | None       # the resolved tier; None for scripted-bypass / non-member
    owner_override: bool          # the ONCE-computed override verdict — threaded to channel-access
    lane_would_deny: bool         # would the LANE (incl. revoke) have denied? (transparency input; see rule)
    reason: DenialReason          # ALLOWED on allow; AUTHORITY on deny (from sb/spec/outcomes.py)
    detail: str                   # ported rich audit reason (capability.py:174-193 strings)
    denial_message: str | None    # engine-generated generic user copy on deny (§ below); None on allow

async def resolve_authority(req: AuthorityRequest) -> AuthorityDecision: ...
```

**Why discord-free (seam correction to spec 02).** The upstream `ResolveRequest.actor` is an
`ActorRef` — discord-free by spec-02 design (kernel decision logic sees no discord objects). The
6-tier ladder (`user/trusted/staff/moderator/administrator/owner`) cannot be recovered from
`ActorRef.is_guild_operator: bool` (which collapses staff/moderator/administrator/owner into one
flag). **Resolution:** the surface adapter — the discord-touching layer that already builds
`ActorRef` from the raw `discord.Member` — pre-computes `member_tier` via
`member_tier_from_member(member, guild.owner_id)` (§2) and puts it on `ActorRef.member_tier`. The
resolver reads `req.member_tier` and never dereferences a discord object. **Spec 02 must add
`member_tier: str | None` to `ActorRef`** (and keep `is_guild_operator` / `is_bot_owner` verbatim for
the channel-access bootstrap legs — those are NOT a clean tier threshold, so they are not derived
from `member_tier`). See §seam-1.

**Fixed internal order** (ports `capability.py` step order; owner-override stays *after* membership so
it composes with the no-cross-guild-escalation invariant):

| # | Step | Rule |
|---|---|---|
| 0 | classify | `lane = classify_authority_ref(ref)` — **pure syntactic; does not touch actor/guild/tier**. (Nothing tier-dependent computes here.) |
| 1 | scripted bypass | `actor_type ∈ {system, backfill}` ⇒ `allowed=True`, `owner_override=False`, `member_tier=None`, `lane_would_deny=False`, `reason=ALLOWED`; never dereferences `user_id`/`guild_id` (`capability.py:85`). **Return.** |
| 2 | **membership gate** | non-scripted actor must have `is_member` (of `target_guild`, `capability.py:98-113`); else `allowed=False`, `reason=AUTHORITY`, `member_tier=None`, `owner_override=False`, `lane_would_deny=False`. **Owner is not exempt — member-guilds-only** (§8-a). **Return.** |
| 3 | **compute tier + lane result** | `member_tier = req.member_tier` (pre-computed). Compute `lane_allows`: CAPABILITY ⇒ `is_tier_sufficient(member_tier, ADMIN_FLOOR_TIER)`, and if `ref` non-empty read the revoke overlay — an explicit `False` sets `lane_allows=False` (`capability.py:157-171`); TIER ⇒ `is_tier_sufficient(member_tier, ref)`. Set **`lane_would_deny = not lane_allows`** (unconditional for every member path — closes the "always populated" gap). |
| 4 | **owner-override (ONCE, top)** | `owner_override = owner_override_holds(req.user_id, req.is_member)`. If `True` ⇒ `allowed=True` regardless of `lane_allows` (composes with membership from step 2; placed before the revoke result decides the final allow so a guild cannot revoke the owner). |
| 5 | setup_delegate | not overridden **and** `actor_type=="setup_delegate"` ⇒ `allowed = not revoked` (ported Q-0098: delegated authority at the floor, still membership-gated at step 2, still revoke-subject). |
| 6 | lane check | not overridden, not delegate ⇒ `allowed = lane_allows`. |

`allowed = scripted OR (member AND (owner_override OR (setup_delegate AND not revoked) OR lane_allows))`.

**`lane_would_deny` — the precise rule (closes M6).** `lane_would_deny = False` on the scripted
(step 1) and non-member (step 2) return paths; `lane_would_deny = not lane_allows` on **every**
member path (steps 3-6), computed unconditionally at step 3. It is *read* by the transparency builder
only when `owner_override` is `True` (§3.5), and by spec 02 to derive `base_allowed = not
lane_would_deny` and `override_applied = owner_override AND lane_would_deny` (RC-2). A setup_delegate
has `owner_override=False`, so its `lane_would_deny` (typically `True`, since a delegate is below the
tier floor) never fires a transparency notice — correct: a delegate is not the owner.

**`denial_message` — the source (closes D5/M5).** It is **engine-generated generic copy**, selected
by `(lane, reason)`, **not** a spec field (there is no second `[S]` field; the sole `[S]` field is
`authority_ref`). Spec 02's `from_exception` table already reads it: `denied → user_message =
AuthorityDecision.denial_message, else "You don't have permission…"`. The generic table (v1):

| Deny cause | `denial_message` |
|---|---|
| TIER lane, tier floor not met | `"You need the **{required_tier}** role (or higher) to use this."` |
| CAPABILITY lane, admin floor not met | `"You need administrator permission to use this."` |
| revoke overlay (`ref` disabled for the guild) | `"This action has been turned off for your role in this server."` |
| membership gate (non-member) | `"You must be a member of this server to use this."` |

A future per-spec `denial_copy` override is a labeled deferral (§9); v1 uses this generic table so no
subsystem must author denial copy. `None` on allow.

### 3.4 `resolve_channel_access` — the folded-in channel lane (honors owner-override)

Ports `command_access.py` **minus** lifecycle/DM (those become K5 admission, spec 02 step 0), plus
the owner-override fix. **`AccessMode` keeps the shipped, name-stable value strings verbatim**
(`command_access.py:184-186`; the docstring says it "mirrors the DB CHECK constraint") — the
command-access policy imports name-stable (§5), so `AccessMode(snapshot.mode)` on a stored
`"all_channels"` must resolve. No redefinition, no data migration.

```python
class AccessMode(enum.Enum):                          # shipped values, verbatim (command_access.py:184-186)
    ALL_CHANNELS = "all_channels"
    SELECTED_CHANNELS = "selected_channels"
    DISABLED_EXCEPT_BOOTSTRAP = "disabled_except_bootstrap"

@dataclass(frozen=True)
class ChannelAccessDecision:
    allowed: bool
    mode: AccessMode | None                 # None = unconfigured (default-allow)
    reason: DenialReason                    # ALLOWED | CHANNEL
    detail: str                             # "" on allow | "commands_disabled" | "channel_not_allowed"
                                            #   (distinguishes the two CHANNEL denials — closes S5/M3)
    owner_override: bool                    # short-circuited by the once-computed owner_override
    bootstrap_bypass: bool                  # short-circuited by the shipped operator/owner bootstrap path
    would_deny_without_override: bool       # transparency input
    denial_message: str | None

async def resolve_channel_access(
    policy,                                 # CommandAccessSnapshot (mode + allowed_channels), via db port
    channel_id: int | None,
    *, owner_override: bool,                # threaded from AuthorityDecision.owner_override (member-gated)
    is_bootstrap: bool,                     # = is_bootstrap_command(target.key), a K1/registry lookup (CONSUMED §4)
    is_operator: bool,                      # = actor.is_guild_operator (shipped _is_guild_operator, verbatim)
    is_owner: bool,                         # = actor.is_bot_owner (is_platform_owner, MEMBERSHIP-BLIND — see below)
) -> ChannelAccessDecision: ...
```

**`detail` disambiguates the two CHANNEL denials.** Shared-vocab §7.1 states `DenialReason.CHANNEL`
covers both `CHANNEL_NOT_ALLOWED` and `COMMANDS_DISABLED`, "distinguished by `detail`". This engine
carries that `detail` on `ChannelAccessDecision` (mirroring `AuthorityDecision.detail`): `reason`
stays `CHANNEL`, and `detail` is `"commands_disabled"` (DISABLED_EXCEPT_BOOTSTRAP) or
`"channel_not_allowed"` (SELECTED_CHANNELS miss) — porting the shipped `DecisionReason.
COMMANDS_DISABLED`/`CHANNEL_NOT_ALLOWED` (`command_access.py:206`). A distinct
`DenialReason.COMMANDS_DISABLED` member stays optional-additive (§9). **Shared-vocab §2.4's
7-field `ChannelAccessDecision` list should gain `detail`** — this engine owns the shape (shared-vocab
§10 leaf inventory), so its 8-field form is canonical; §seam-2 flags it.

**`is_bootstrap` provenance (closes D2/M4).** `is_bootstrap` is **not** a spec field and **not** owned
here. It is computed by the caller (the resolver, at its step-2 channel call) via the ported K1
oracle `is_bootstrap_command(key)` (`command_access.py:71` → K1/registry) over `target.key`.
Bootstrap-ness is a naming/registry property (the shipped roster is name-pattern based:
`setup-*`/`settings-*`/`admin-*`/`platform-*`/`help-*`/`diagnostics-*`), so K1 owns the classifier;
this engine consumes the bool. (A future explicit `CommandSpec.is_bootstrap` `[S]` field is a labeled
deferral, §9.)

**`is_owner` vs `owner_override` — the two owner semantics (closes D6).**
- **`owner_override`** (channel-access leg 1) `= owner_override_holds(user_id, is_member)` — the
  **member-gated** verdict computed once in `resolve_authority` step 4 (bot-owner **AND** member).
  This is the **L-12 fix**: a member owner bypasses **any** command's channel restriction.
- **`is_owner`** (channel-access leg 2, bootstrap) `= actor.is_bot_owner` (`is_platform_owner`,
  **membership-blind**) — preserved **verbatim** from the shipped `:351` bootstrap path, which admits
  `is_guild_operator OR is_bot_owner` for a bootstrap command **without** a membership check.

**Interaction with the authority membership gate (X-7 narrowing, stated explicitly).** In the composed
resolver order, authority (step 1) runs **before** channel-access (step 2). A **non-member** bot-owner
is therefore denied at `resolve_authority` step 2 (member-guilds-only, X-7) and never reaches
channel-access — so the shipped `:351` bypass's membership-blind `is_owner` leg is **narrowed**: it can
no longer admit a non-member owner. This is intended (X-7 supersedes Q-0227's "any server"). For a
**member** owner, `owner_override` is already `True`, so channel-access leg 1 short-circuits ALLOW
before leg 2 is reached — making the `is_owner` leg effectively pre-empted on the composed path. It is
kept **verbatim** so (a) `resolve_channel_access` is correct when called standalone and (b) the
shipped contract is preserved literally; the **guild-operator** (`is_operator`) bootstrap leg is the
one that stays live (an operator who is not the owner running a bootstrap command in a restricted
guild). Practically, a non-member cannot invoke a command in a guild they are not in, so this narrows
a theoretical edge, not a live path.

**Order (buildable):**
1. `owner_override` ⇒ **ALLOW** for *any* command (the **L-12 fix** — was bootstrap-only at `:351`);
   `bootstrap_bypass=False`; `would_deny_without_override` = what steps 3-4 would return.
2. `is_bootstrap AND (is_operator OR is_owner)` ⇒ ALLOW, `bootstrap_bypass=True` (shipped `:351`
   verbatim — preserves the **guild-operator** bootstrap path, not just owner).
3. `mode is None OR ALL_CHANNELS` ⇒ ALLOW.
4. `DISABLED_EXCEPT_BOOTSTRAP` ⇒ DENY (`reason=CHANNEL`, `detail="commands_disabled"`);
   `SELECTED_CHANNELS` ⇒ ALLOW iff `channel_id ∈ policy.allowed_channels` else DENY
   (`reason=CHANNEL`, `detail="channel_not_allowed"`).

### 3.5 The transparency-audit contract (owned; policy owner-gated §8-c)

```python
@dataclass(frozen=True)
class TransparencyAudit:
    actor_id: int                 # the platform owner (passed in — see build signature)
    guild_id: int
    authority_ref: str
    target_key: str               # command name | "<panel_id>.<action_id>"
    surface: str                  # Surface value
    would_deny_reason: DenialReason   # AUTHORITY (lane) | CHANNEL (channel-access)
    timestamp: datetime

def build_transparency_audit(auth: AuthorityDecision, channel: ChannelAccessDecision | None,
                             *, actor_id: int, guild_id: int, target_key: str, surface: str,
                             clock) -> TransparencyAudit | None: ...
```

- **`actor_id` source (closes M2).** `AuthorityDecision` carries **no** `actor_id` (it stays the
  frozen 10-field shape). The resolver passes `actor_id = req.actor.user_id` as a keyword to
  `build_transparency_audit`. It is a build parameter, not a decision field.
- **Trigger (would-not-otherwise-authorize):** `auth.owner_override AND (auth.lane_would_deny OR
  (channel is not None AND channel.would_deny_without_override))` (RC-5). Returns `None` when the
  owner would have been authorized anyway (override was a no-op — no audit noise).
- **Emit path (NOT the mutation-audit seam — closes S2/S3).** A `TransparencyAudit` is **not** a
  mutation, so it does **not** route through `emit_audit_action` (the frozen 11-field mutation seam,
  keyed by a pipeline-minted `mutation_id`, shared-vocab ③ — it cannot supply
  `mutation_id`/`mutation_type`/`prev_value`/`new_value`). Instead it uses **two** designed carriers,
  reconciled with spec 02:
  1. the **`TransparencySink` port** (this engine, §2) — the resolver calls
     `build_transparency_audit(...)` at step 4 and, when non-`None`, `sink.emit(audit)`;
  2. the **`override_applied`/`base_allowed` flags** on the resolver's `command.dispatched`
     observability trace (spec 02 §3.5, `observability_only=True`) — derived from `AuthorityDecision`
     (`override_applied = owner_override AND lane_would_deny`, `base_allowed = not lane_would_deny`).

  Neither carrier touches `emit_audit_action`; the mutation-audit seam (K7/domain) is untouched.
  **Spec 02 must name `build_transparency_audit` + `TransparencySink` as the transparency emit
  (owned by this engine)** rather than its unnamed "additionally routes to the transparency-audit
  sink" (§seam-3).
- **Sink (recommendation, owner-gated §8-c):** dual — (1) **bot-log** (deploy-level owner audit
  channel), (2) **server-log** (the guild's configured governance/audit log). Whether the sink is
  *also* promoted to a durable audit row (via a K7 `AuditEventSpec`) is **owner-gated §8-c**; v1
  built default is the operator-notice sink, no durable row.
- **No-log-channel fallback:** guild has no server-log configured ⇒ (1) bot-log **+** (2) **owner DM
  digest** (batched, not per-event). The `TransparencySink` port exposes `emit(audit)` +
  `flush_digest()`; the adapter batches the DM.

### 3.6 The compile-time validator (consumed by the compiler P4)

```python
def validate_authority_ref(ref: str, reserved_capabilities: frozenset[str]) -> None:
    """Raise BadAuthorityError / FormatError if ref does not classify to exactly one lane,
    a CAPABILITY ref is not 3-part or not namespace-reserved, or a tier token is not in TIERS."""
```

Matches the compiler spec (01) P4 seam `authority.validate(ref) -> None|Error` exactly. The check
order mirrors §3.2's pinned predicate: (1) `classify_authority_ref(ref)` — a raise here is
`bad_authority`; (2) if CAPABILITY and `ref != ""`, assert exactly 3 dotted parts else
`FormatError("capability_not_3_part")`, then assert `ref ∈ reserved_capabilities` (K1) +
reserved-prefix rule; (3) if TIER, `ref ∈ TIERS` is already guaranteed by classify. Lane exclusivity
is structural (one string → one lane), closing the "lane-exclusivity check undefined" gap spec 01
flagged.

---

## 4. Provides / Consumes

**Provides (canonical shapes I OWN — everyone else consumes these):**

| Contract | Shape |
|---|---|
| `authority_ref: str` field + the lane resolution table (§3.2) | ONE ref → `{CAPABILITY(admin-floor / dotted+revoke), TIER}`; empty ⇒ ADMIN floor; classifier pinned |
| `resolve_authority(req) -> AuthorityDecision` | the runtime two-lane resolver; **discord-free** (consumes `req.member_tier`); owner-override once at top; `owner_override` + `lane_would_deny` (unconditional) exposed |
| `owner_override_holds(user_id, is_member) -> bool` | the SINGLE owner-override predicate `:= is_platform_owner(user_id) and is_member` (member-guilds-only, self-contained) |
| `resolve_channel_access(..., owner_override) -> ChannelAccessDecision` | the folded-in channel lane honoring override + bootstrap bypass; `AccessMode` = shipped values; `detail` disambiguates the two CHANNEL denials |
| `validate_authority_ref(ref, reserved) -> None` | the compile-time classifier/validator (compiler P4) |
| `TransparencyAudit` + `build_transparency_audit` + `TransparencySink` port | the trigger/payload/sink/no-log-fallback contract; emit path = port + `command.dispatched` flag (NOT `emit_audit_action`) |

**Consumes (ASSUMED from siblings — exact assumption stated for the seam pass):**

| Contract | Assumed shape | Sibling / row |
|---|---|---|
| `ActorRef` carries the pre-computed tier | spec 02 `ActorRef` gains **`member_tier: str \| None`** (adapter computes it via `member_tier_from_member`, §2); `is_guild_operator`/`is_bot_owner`/`user_id`/`is_dm` stay. The resolver builds `AuthorityRequest` from `ResolveRequest` reading `actor.member_tier`, `actor.user_id`, `req.guild_id`, `is_member = req.guild_id is not None and not actor.is_dm`. **Seam correction (§seam-1):** spec 02 `ActorRef` is discord-free and cannot carry a Member/6-tier ladder — it MUST add `member_tier` or L6/the tier lane cannot resolve staff/moderator/administrator/owner | K8 resolver / adapters (02) |
| resolver's authority→… order | K8 `resolve()` calls `resolve_authority` at **step 1**, threads `decision.owner_override` + `actor.is_guild_operator` (`is_operator`) + `actor.is_bot_owner` (`is_owner`) + `is_bootstrap_command(target.key)` into its **step-2** `resolve_channel_access`, and calls `build_transparency_audit(auth, channel, actor_id=…, …)` + `sink.emit` at **step 4**. **Seam correction (§seam-1):** spec 02 step 2 must receive `owner_override` or L-12 re-opens for the owner | C-1 resolver (02, K8) |
| bootstrap classifier | `is_bootstrap_command(key) -> bool` (ported `command_access.py:71`) owned by K1/registry; the caller computes `is_bootstrap` before `resolve_channel_access` | namespace/registry (K1) |
| `DenialReason` / §2.7 outcome constants | imported from `sb/spec/outcomes.py` (spec 02's frozen leaf, built on the REAL `services/lifecycle/contracts.py:48-52`); this engine uses `ALLOWED`, `AUTHORITY`, `CHANNEL`; a denial → resolver maps to `BLOCKED`/`error_class=denied` | outcomes leaf (02/07.1) |
| dispatch-trace / transparency carrier | the resolver's `command.dispatched` `EventSpec` (`observability_only=True`) carries `override_applied`/`base_allowed` **derived** from `AuthorityDecision`; the transparency notice rides the `TransparencySink` port + this flag — **NOT** `emit_audit_action`. The mutation-audit seam (`emit_audit_action`, 11-field) stays K7/domain, untouched | dispatch-trace (02) / audit spine (K7) |
| compiler validates authority strings | the compiler P4 pass calls `validate_authority_ref(ref, reserved_capabilities)` and supplies the namespace-reserved capability set at compile time | compiler (01, K2/tools) |
| namespace capability reservation | `{subsystem}.{resource}.{action}` capabilities are K1-reserved with the reserved-prefix rule (`_internal.*/system.*/governance.*`, `subsystem_registry.py:7`) | namespace (K1) |
| Q-0227 + Q-0237(d) | ONE `authority_ref` (d, frozen); member-guilds-only scope (X-7 supersedes Q-0227's "any server", §8-a) | router (frozen) |

---

## 5. Data model + migration/index shape

**No new table.** The engine is stateless per request. It **reads** existing rows through the db
port: `capability_execution_overrides` (revoke overlay, via `governance.execution.get_capability_
override` semantics), the command-access policy (`get_command_access_policy`). Member/guild state is
**not** read here — the tier is pre-computed by the adapter and arrives on `req.member_tier`. The
revoke overlay and command-access policy tables import **name-stable** (design-spec §5.2); because
`AccessMode` keeps the shipped value strings (`"all_channels"`/…), `AccessMode(snapshot.mode)` on a
stored value resolves with **no migration**. The transparency audit **writes no new schema**: it rides
the `TransparencySink` port + the observability trace; whether it *also* becomes a durable audit row
is owner-gated §8-c (and would reuse the existing audit table, no new schema). The owner id is deploy
config (env `BOT_OWNER_USER_ID`, `config.py:40`), not a table.

---

## 6. Restart & merge=deploy behavior

- **Stateless.** `resolve_authority` re-reads authority on every call — opening a panel is never
  authorization (design-spec §1.2 interaction-lifecycle invariant); every callback re-resolves. No
  in-memory authority state survives or needs to survive a restart.
- **Boot reconcile.** The revoke overlay + command-access policy caches are loaded lazily per guild
  (ported `execution.py:189-194` deterministic-refresh + TTL). A merge=deploy restart cold-loads
  them on first access; no reconcile step is required (authority is derived, never checkpointed).
- **Dual-instance overlap (LP-4).** Two instances resolving the same actor return the **same**
  verdict (pure function of guild rows + the pre-computed tier + deploy owner id) — no split-brain.
  Admission drain (K5, resolver step 0) stops a draining instance *before* authority runs, so no
  double-authorization.
- **Transparency digest.** The owner-DM digest is batched; a restart flushes any pending batch at
  shutdown-drain or re-accumulates next boot (bounded, at-most-a-digest loss — acceptable for a
  transparency notice whose authoritative copy is already the bot-log entry).

---

## 7. Architecture rules honored (INV / layer cites)

- **Layer table (design-spec §1.1).** `kernel/authority` imports `spec`, `namespace`,
  `observability`, and the `TransparencySink` **port it defines**; it is now **discord-free** — the
  discord `Member`→tier read lives in `sb/adapters/discord/member_tier.py`, and the concrete
  transparency sink in `sb/adapters/discord/transparency_sink.py`. The kernel **must NOT** import
  `domain`, `manifest`, `kernel/interaction`, or `adapters` internals. `sb/spec/authority.py` is a
  **dependency-free leaf** (stdlib only) so the compiler (P4) and namespace import it with no cycle —
  honoring "the grammar is a dependency-free leaf." This alignment with spec 02's discord-free
  `ActorRef` is the §seam-1 correction.
- **Owner-override single source (ports `config.py:61`'s intent).** "Every authority seam routes its
  owner check through here so the rule lives in exactly one place" — this design *enforces* that: the
  ~11-16 scattered `is_platform_owner` authorization sites collapse to `owner_override_holds`, called
  once per resolution. The two sanctioned `is_platform_owner` callers are (a) `owner.py`'s
  `owner_override_holds` (the authorization) and (b) the surface adapter's `ActorRef.is_bot_owner`
  construction (a classification fact for the bootstrap `is_owner` leg). An AST fence (generalizing
  `test_setup_delegate_actor_boundary`) asserts **no other** module authorizes on `is_platform_owner`
  directly.
- **Membership invariant preserved (INV — authority bound to the write target).** `capability.py:
  98-113` ports verbatim: a non-scripted actor (owner included) must be a member of `target_guild`
  (`req.is_member`); privilege in guild A never authorizes a write to guild B.
- **Transparency ≠ mutation audit.** The transparency notice is emitted through the `TransparencySink`
  port + the observability trace — never through `emit_audit_action` (which is the 11-field mutation
  seam). The `audit.action_recorded → server_logging` wiring for real mutations is untouched.
- **DB via the port; settings via keys.** All policy reads go through the db port / typed accessors;
  no raw `pool.execute` in the engine; policy keys are `settings_keys` constants.
- **The no-skip fence (design-spec §1.2, spec 02 §7).** Every surface reaches a handler only through
  the K8 resolver, whose step 1 is this engine — so a domain can never forget the authority check.

---

## 8. Options → Decision → Why (forks I CLOSED)

| Fork | Options | Decision | Why |
|---|---|---|---|
| Where the discord `Member`→tier read happens | (a) thread a raw `Member` into `AuthorityRequest` (kernel imports discord) · (b) pre-compute `member_tier` in the adapter, thread a discord-free string | **(b)** | Aligns with spec 02's discord-free `ActorRef` and the "kernel decision logic sees no discord objects" rule. The adapter already holds the `Member`; it computes the tier once and the kernel stays pure. (a) would push discord into `kernel/authority` and contradict spec 02. **Seam correction §seam-1: spec 02 `ActorRef` adds `member_tier`.** |
| Channel-access placement | (a) fold into `resolve_authority` step 1 (one call, override covers all) · (b) keep it a K8 step-2 lane but thread `owner_override` from step 1 | **(b)** | Preserves spec 02's clean separation (authority=*who*, validate=*where/whether*); the ONLY change spec 02 needs is to pass `decision.owner_override` into its step-2 channel call. Owner-override is still computed **once** (step 4); it is merely *consumed* by two lanes. **Flagged §seam-1.** |
| Transparency emit seam | (a) route `TransparencyAudit` through `emit_audit_action` · (b) `TransparencySink` port + `override_applied` on the `command.dispatched` observability trace | **(b)** | `emit_audit_action` is the 11-field **mutation** seam keyed by `mutation_id`; a transparency notice is not a mutation and cannot fill it (shared-vocab ③). The notice is an observability/operator artifact — the sink port + the dispatch-trace flag are its correct carriers. Reconciles 04 with 02 (§seam-3). Durable-row promotion stays owner-gated §8-c. |
| `AccessMode` values | (a) redefine to `"all"/"selected"/"disabled"` · (b) keep shipped `"all_channels"/…` | **(b)** | The command-access policy imports name-stable (§5); the DB stores the shipped strings and the docstring says `AccessMode` "mirrors the DB CHECK constraint". Redefining would make `AccessMode(snapshot.mode)` raise `ValueError` or force a migration. Keep verbatim. |
| Distinguishing the two CHANNEL denials | (a) add a `DenialReason.COMMANDS_DISABLED` member · (b) keep `reason=CHANNEL` + a `detail` field | **(b)** | Matches shared-vocab §7.1 ("`CHANNEL` … distinguished by `detail`") and the existing `AuthorityDecision.detail` pattern; keeps `DenialReason` lean. A distinct `COMMANDS_DISABLED` member stays optional-additive (§9). |
| `is_bootstrap` provenance | (a) invent a `CommandSpec.is_bootstrap` `[S]` field now · (b) port the shipped `is_bootstrap_command(key)` oracle to K1/registry | **(b)** | Bootstrap-ness is a naming/registry property (the shipped classifier is name-pattern based); porting the oracle is the faithful, zero-invention closure. The declared-field refinement is a labeled deferral (§9). |
| `classify_authority_ref` totality | (a) leave arity/case unspecified · (b) pin: "contains a dot" ⇒ CAPABILITY then 3-part format check; tier tokens case-sensitive | **(b)** | Makes the classifier total and deterministic for every input (`"a.b"`, `"a.b.c.d"`, `"Administrator"`), so a fresh builder needs no further decision. Malformed dotted refs fail as `FormatError("capability_not_3_part")` per compiler 01 P4. |
| Owner-override vs bootstrap bypass | (a) owner-override replaces the bootstrap bypass · (b) both, layered | **(b)** | The shipped bootstrap bypass (`:351`) also admits a **guild operator** (not owner) running a bootstrap command — owner-override (bot-owner only) would silently drop that. Keep both: `owner_override` (any command, member owner) *plus* bootstrap bypass (bootstrap command, operator-or-owner). The membership gate narrows the membership-blind `is_owner` leg for the theoretical non-member owner (X-7) — stated in §3.4. |
| One `authority_ref` discriminator | (a) a `lane` tag field beside the ref · (b) syntactic classification of the ref value | **(b)** | Q-0237(d) says authors fill ONE column; a second `lane` field re-introduces the two-field burden. Dotted-capability vs single-word-tier vs empty are total and non-overlapping, so the value alone classifies — and the compiler can prove exclusivity (§3.6). |
| Empty `authority_ref` meaning | (a) domain "user" (everyone) · (b) ADMIN floor | **(b)** | Ports the shipped invariant verbatim (`capability.py:27` "empty resolves to the floor, NOT no-auth"). A domain surface for everyone declares `authority_ref="user"` (a tier token), never empty. |
| `lane_would_deny` computation | (a) skip it, re-derive at audit time · (b) always compute the pure lane result at step 3 | **(b)** | Cheap (the tier check is a string compare on the pre-computed tier), computed once, unconditionally for every member path — keeps the transparency trigger a pure read of the decision and closes the "always populated" gap. |
| `denial_message` source | (a) a second `[S]` spec field · (b) engine-generated generic copy per `(lane, reason)` | **(b)** | Keeps the "one `[S]` field (`authority_ref`)" preamble true; no subsystem must author denial copy in v1. A per-spec `denial_copy` override is a labeled deferral (§9). |

### 8-owner-gated. Forks I must NOT decide (options + recommendation, live-owner review)

- **§8-a — owner-override scope (member-guild vs any-reachable).** *Options:* **(A)** the override
  authorizes only within the actor's **member guilds** (owner must share the guild — X-7); **(B)** in
  **any** guild the platform owner can reach. *Recommendation:* **(A)** — built **structurally** here
  (`owner_override_holds` requires `is_member`; step 2 membership gate is not owner-exempt). The owner
  **confirms** the scope; the predicate and the L-12 fix are designed regardless. **Owner-gated:**
  override reach is an authority-policy / credential-custody decision.
- **§8-c — transparency-audit sink wording + durable-row promotion.** *Options:* the sink is
  **(i)** operator-notice only (bot-log + server-log + owner-DM fallback, no durable row) vs
  **(ii)** *also* a distinct authoritative audit row (a K7 `AuditEventSpec` written through the
  existing audit table — one row per override-authorized dispatch). *Recommendation:* **(i)** for v1
  — the trigger/payload/port/fallback are all designed; a retained row per override is a
  retention/volume posture. Owner also names the "would-not-otherwise-authorize" copy. **Owner-gated:**
  audit-retention + operator-notice wording.

---

## 9. Labeled deferrals (bounded by the capability corpus)

- **Per-capability tier matrix.** v1 keeps the single ADMINISTRATOR floor for every CAPABILITY-lane
  ref (`capability.py:48-51`). A future `{capability → required_tier}` lookup slots into §3.2's table
  with **zero** change to the resolver or the field. *Reason:* no subsystem in the 43-subsystem
  corpus + named amendments requests a non-admin capability tier today.
- **Explicit `CommandSpec.is_bootstrap` field.** v1 ports the name-pattern `is_bootstrap_command(key)`
  oracle (K1). A future explicit `[S]` field would replace the heuristic with a declared bool
  **without** changing `resolve_channel_access` (it already receives a bool). *Reason:* the shipped
  classifier is name-based; a declared field is a manifest-purity refinement, not a v1 requirement.
- **Per-spec `denial_copy` override.** v1 uses the engine's generic `(lane, reason)` copy table
  (§3.3). A future optional `[S]` `denial_copy` on a spec would let a subsystem override the generic
  string; the resolver would prefer it when present. *Reason:* no subsystem needs bespoke denial copy
  today; the generic table covers every deny cause.
- **Distinct `DenialReason.COMMANDS_DISABLED` member.** v1 uses `reason=CHANNEL` + `detail`
  (§3.4). Adding the member is optional-additive (shared-vocab §7.1) with no logic change. *Reason:*
  `detail` already disambiguates; the extra enum member is a consumer convenience.
- **Transparency-audit *sink* implementation** (bot-log channel id config, DM-digest cadence). The
  *contract* (trigger, payload, port) is designed here; the concrete channel wiring + digest window
  are the `adapters/discord` sink's, landing with the logging band (Phase-4 band 2). *Reason:* the
  sink depends on the logging subsystem's binding lane, ported later.
- **`trusted` tier resolution.** `TIERS` includes `trusted` (reserved, `visibility_rules.py:34` "for
  future trust/progression"); it resolves like `user` until a trust system exists. *Reason:* bounded
  to a named-but-unbuilt tier; the token is reserved so no re-grammar is needed when it lands.

---

## 10. Retirement map

| Row | Retires how | Status |
|---|---|---|
| **L-12** (owner-override gaps) | channel-access now consults owner tier — `resolve_channel_access` short-circuits on the once-computed `owner_override`, fixing the non-bootstrap deny (`command_access.py:351`); transparency audit designed (§3.5) via the `TransparencySink` port + `command.dispatched` flag; ~11-16 seams → ONE `owner_override_holds`; member-guild scope preserved | **RETIRED (design)** — transparency *sink policy* owner-gated §8-c |
| **L-13 + T1-4** (authority two-lanes vs one-label) | ONE `authority_ref` + the §3.2 lane resolution table (spec 02 marked this "CONSUMED, not retired by me" — **this engine is what retires it**) | **RETIRED (design)** |
| **T2-10** (owner-override member-guild wording + transparency sink + no-log fallback) | member-guilds-only predicate (§3.3 step 2/4); `TransparencyAudit` sink contract (port + trace flag; bot-log + server-log; fallback bot-log + owner DM digest) to buildable shape | **RETIRED (design)** — sink policy owner-gated §8-c |
| **X-7** (member-guilds-only) | `owner_override_holds` requires `is_member`; the membership gate narrows the membership-blind bootstrap `is_owner` leg for the non-member owner (§3.4); "any server" is not built | **RETIRED (design)** — scope confirm owner-gated §8-a |
| the 5 duplicated `_check_admin` | each → its spec's `authority_ref=""` (ADMIN floor) resolved through this engine; per-service function deleted | **RETIRED (design)** |
| slash/panel owner-blindness (`governance/resolver.py:223`) | the step-2 subsystem-visibility (K8) reads the once-computed `owner_override` instead of re-calling `is_platform_owner` | **RETIRED (design)** — seam note to spec 02 |

**V-3 accountability:** every row above is claimed and closed; nothing evaporates. Rows NOT mine:
L-4/L-5/T2-4/T2-9/T2-17 (the resolver seam, spec 02); L-22 (guild-blind nav); the settings-lane
retirements (§4 owner).

---

## 11. Build order (design-spec §9.1)

- **K6 — this engine.** Land `sb/spec/authority.py` (leaf: classifier + `validate_authority_ref` +
  tier order) first, then `kernel/authority/{owner,decision,resolve,channel_access,transparency}.py`;
  the discord-aware `adapters/discord/member_tier.py` lands with the surface adapters (K8), and the
  concrete transparency sink lands with the logging band (deferral §9).
- **Depends on:** K1 (namespace — capability reservation for `validate_authority_ref` + the
  `is_bootstrap_command` oracle), K3 (db port — revoke overlay + command-access policy reads), K5
  (lifecycle — admission takes the lifecycle/DM legs shed from channel-access). Uses
  `DenialReason`/outcome constants from `sb/spec/outcomes.py` (landed at K7 per spec 02, but the
  *leaf* can precede — recommend landing `outcomes.py` at K6 so authority need not forward-reference
  K7).
- **Blocks:** **K7** (the four workflow lanes each call `resolve_authority` as their first "resolve
  authority" step, design-spec §1.3); **K8** (the resolver's step 1 + step-2 channel lane + step-4
  transparency emit; the adapters that populate `ActorRef.member_tier`); the compiler's **P4**
  authority-string check (can arm as soon as `validate_authority_ref` exists). Nothing in Phase 4 can
  authorize a mutation or dispatch without K6.

---

## Seam-pass notes (for the strand-1 consistency reviewer)

1. **Spec 02 `ActorRef` must add `member_tier: str | None`, and its resolver must thread the
   once-computed flags into channel-access.** The authority kernel is discord-free (this hardening
   pass); it consumes a **pre-computed** tier string. Spec 02's `ActorRef` is discord-free and today
   carries only `is_guild_operator: bool` (which collapses staff/moderator/administrator/owner) — it
   **cannot** populate the 6-tier ladder the TIER lane needs. The surface adapter (which holds the raw
   `Member`) computes `member_tier` via `member_tier_from_member(member, guild.owner_id)` and sets it
   on `ActorRef`. The resolver then builds `AuthorityRequest` and, at step 2, threads
   `decision.owner_override` + `actor.is_guild_operator` (`is_operator`) + `actor.is_bot_owner`
   (`is_owner`) + `is_bootstrap_command(target.key)` into `resolve_channel_access`. Without the
   threaded `owner_override`, the L-12 non-bootstrap deny re-opens for the owner. This is the one
   non-trivial cross-spec wiring (RC-2/RC-4).
2. **`ChannelAccessDecision` gains `detail`; `AccessMode` keeps shipped values.** Shared-vocab §2.4
   lists `ChannelAccessDecision` with 7 fields and no `detail`, yet §7.1 says the two CHANNEL denials
   are "distinguished by `detail`." This engine owns the shape (shared-vocab §10 leaf inventory), so
   its **8-field** form (adding `detail`) is canonical — shared-vocab §2.4 should absorb it. `AccessMode`
   uses the **shipped** value strings (`"all_channels"`/`"selected_channels"`/
   `"disabled_except_bootstrap"`, `command_access.py:184-186`), not `"all"/"selected"/"disabled"`.
   `DenialReason` lives in `sb/spec/outcomes.py` (shared-vocab §7.1) and covers `CHANNEL` for both
   denials; a distinct `COMMANDS_DISABLED` member stays optional-additive.
3. **Transparency emit path = `TransparencySink` port + `command.dispatched` flag, NOT
   `emit_audit_action`.** Spec 02 §3.5 says the trace "additionally routes to the transparency-audit
   sink" without naming the seam; this engine owns `build_transparency_audit` + the `TransparencySink`
   port. The two specs must agree: (a) the resolver derives `override_applied = owner_override AND
   lane_would_deny` / `base_allowed = not lane_would_deny` from `AuthorityDecision` onto the
   `command.dispatched` observability trace (02); (b) the resolver calls `build_transparency_audit(...,
   actor_id=req.actor.user_id, ...)` and `sink.emit` at step 4 (04). Neither touches the 11-field
   `emit_audit_action` mutation seam. Whether the notice becomes a durable audit row is owner-gated
   §8-c (RC-5).
4. **`governance/resolver.py:223`** (subsystem-visibility owner check) is spec 02's step-2 concern,
   not K6's — but under "override once at top" it must consume the K6 `owner_override` flag rather
   than re-derive `is_platform_owner`. Noted so both specs agree the owner check exists in exactly
   one place.

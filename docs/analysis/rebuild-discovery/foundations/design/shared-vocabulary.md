# Shared Vocabulary — Strand-1 Kernel Spine → Strand-2 & Cross-Cutting (FROZEN CONTRACT)

> **Status:** `reference` — foundational design artifact (2026-07-04). **NOT SOURCE OF TRUTH** — a design contract; shipped source + the frozen upstream contracts win (Q-0120).

> **NOT SOURCE OF TRUTH for runtime.** This is a **design contract** — a Phase-B synthesis
> that freezes the exact shape of every recurring seam the strand-1 kernel-spine specs
> (`strand-1-kernel-spine/01…05`, **all five now hardened**) hand to **strand 2** (draft · workflow ·
> outbox · scheduler) and to the **cross-cutting concerns**. It authors no `disbot/` and no `sb/` code.
> **Precedence:** shipped source & merged PRs win over this doc; the five owning specs win over
> this doc *for shapes they own*; this doc wins only where it **reconciles a disagreement between
> two specs** (those rows are marked → the loser spec must change). Spot-verify every source cite.
>
> **Why this exists.** Six vocabularies recur across every kernel spec and every strand-2/cross-cut
> port. If each port re-derives them, they drift (the exact `#763` false-green / `L-4` four-postures
> class the rebuild exists to kill). This file is the single place they are frozen once. A strand-2
> builder writes to **these** shapes and makes zero further design decisions except the forks in §⑧.
>
> **Re-freeze provenance (2026-07-04, all-five pass).** The prior freeze ran while specs **01**
> (compiler) and **04** (authority) were still pre-hardening. Both have since hardened. This pass
> re-freezes over all five and folds the deltas: 04 is now **discord-free** (a pre-computed
> `member_tier` seam, §②), `ChannelAccessDecision` gains `detail` (8 fields), `AccessMode` is pinned
> to shipped value strings, `denial_message` is **engine-generated (not `[S]`)**, the transparency
> emit seam is pinned to a **`TransparencySink` port** (not `emit_audit_action`), and **RC-7 is now
> RESOLVED** (01 adopted K1's namespace oracle shape). New reconciliations: **RC-12…RC-15**.
>
> **Cross-strand seam pass (2026-07-04) — reconciliations RC-16…RC-21 added.** After the strand-2/3
> specs froze, the four mechanically-reconciled cross-strand forks were **applied to the specs** and the
> reconciliation ledger below (§⑨) extended: **RC-16** correlation-id column (formalizes the prior
> "new" row), **RC-17** `DeliveryClass` home = `sb/spec/events.py`, **RC-18** `ActorRef.actor_type`
> additive field (F-4, applied), **RC-19** background `Surface.MAINTENANCE` member + `from_exception.target
> → TargetRef | None` (F-5, applied), **RC-20** poll topology — 09 hosts the outbox relay/reaper lanes
> (F-1, applied), and **RC-21** the pending `ChannelEmitter` 02/K8 egress port (Q-D26). The fifth fork
> (F-3 intent posture) is **owner-gated → register PG-2**, not closed by edit. The frozen contract tables
> in §①–§⑦ are otherwise unchanged; only the reconciled seams (`from_exception.target`, the `MAINTENANCE`
> member) are updated to their applied shape.

---

## 0. Source-wins grounding (Q-0120) — the result-grammar seam everyone shares

Every spec carries the same seam correction; it is the substrate under items ① and ③–⑤, so it is
stated **once, here, canonically**, re-verified against shipped source this session.

| Symbol | Status | Real location / meaning |
|---|---|---|
| `SUCCESS` `PARTIAL` `BLOCKED` `DECLINED` `DISCORD_FAILED` | **REAL — the frozen §2.7 outcome vocab** | `disbot/services/lifecycle/contracts.py:48-52` (verified). The **only** five outcome constants. No 6th is ever added. |
| `REVERSIBLE` `COMPENSATABLE` `IRREVERSIBLE` | **REAL — the reversibility vocab** | `services/lifecycle/contracts.py:40-42` (verified). Read by the compiler `destructive_confirmation` predicate (01 P6). |
| `LifecycleResult` | **REAL** | `services/lifecycle/contracts.py:77` — `{mutation_id, guild_id, domain, operation, outcome, reversibility, steps:tuple[StepResult], committed_at, audit_emitted, event_emitted}`. |
| `LifecyclePreview` | **REAL** | `:66` — `{allowed, operation, summary, reversibility, warnings}` (side-effect-free preview). |
| `StepResult` / `classify_outcome` | **REAL** | `:56` (`target_id, target_name, ok, error`) / `:108` (`steps → SUCCESS/PARTIAL/DISCORD_FAILED`). |
| `WorkflowResult` | **DESIGN TYPE ONLY (K7) — spec-only, NO shipped class** | The §2.7 **kernel** result type — a strict **superset** of the shipped `LifecycleResult`, landed in K7. **Re-verified: no `class WorkflowResult` exists in `disbot/`.** The dispatch-return grammar (`resolve()` step 5) is `WorkflowResult \| None`. |
| `StageResult` | **REAL — the shipped dispatch *analogue*, NOT the design dispatch return** | `disbot/core/runtime/message_pipeline.py:181` — `{deleted, short_circuit, moderation_action}`. The **passive on-message pipeline substrate**, one layer *below* `resolve()`. It is the closest *shipped* thing to "a dispatched stage returning a result," but it **never crosses the `resolve()` seam** and is **dropped from the dispatch-return grammar** so its overloaded `short_circuit` can never be mislabeled a dispatch `BLOCKED`. |
| `disbot/core/contracts.py` + a shipped `WorkflowResult` class | **FABRICATED — re-verified ABSENT this session** | Audit-A cite `core/contracts.py:48-52` does not exist (`ls` → absent; FJ L-4/L-25). Distinct from the **real** `disbot/services/lifecycle/contracts.py:48-52`. Never design against it. |

> **Prompt-phrasing reconciliation (RC-1).** The task brief says the error envelope's outcome is
> *"built on the REAL `StageResult` (message_pipeline.py:181), NOT the fabricated
> `WorkflowResult`/contracts.py:48-52."* Canonical form (all five specs agree): the outcome **vocab**
> is built on `services/lifecycle/contracts.py:48-52` (**real**); the **dispatch return** is
> `WorkflowResult|None` (the K7 **design** superset of `LifecycleResult` — spec-only, not a shipped
> class, not "fabricated"); **`StageResult` is a *different* substrate** (the shipped message-pipeline
> analogue), **not** the outcome source and **not** the design dispatch return. The only *fabricated*
> cite is `disbot/**core**/contracts.py` (absent) — distinct from the real
> `disbot/**services/lifecycle**/contracts.py:48-52`. "Source-wins" resolves to: design against the
> real lifecycle constants + the design `WorkflowResult|None` grammar; never against a shipped
> `WorkflowResult` class or `core/contracts.py`, neither of which exists.

---

## ① THE ERROR ENVELOPE

**Owner:** spec 02 (`kernel/interaction/errors.py` + `result.py`). **Consumers:** every rung/adapter,
the composition-root `tree.error`/`on_app_command_error`/`on_command_error` shims, the DB seam (05),
the wizard fold-in, **strand-2 workflow/outbox** (which classify their own dispatch exceptions through
the same function).

### 1.1 `from_exception` — the one classifier

```python
def from_exception(exc: BaseException, *, surface: Surface,
                   target: TargetRef | None, section_label: str | None = None) -> ErrorEnvelope: ...
#   RC-19 (applied 2026-07-04): `target` is `TargetRef | None` — a headless background fire has no
#   TargetRef and passes `target=None`. `surface`/`target` only enrich `user_message`; the classifier
#   core (exc → error_class → reason → outcome → retryable) is surface/target-independent.

class Surface(enum.Enum):                           # 02 (interaction dispatch) — see RC-11 (do NOT unify w/ namespace Surface)
    SLASH; PREFIX; COMPONENT; MODAL; NL_INTENT; NL_ORCHESTRATION   # the six interaction origins
    MAINTENANCE = "maintenance"                     # RC-19: the ONE background/headless member —
    #   covers 09 scheduler fires AND 11 invariant sweep-repairs; both call
    #   from_exception(exc, surface=Surface.MAINTENANCE, target=None). NOT a per-sibling scheduler/maintenance split.

class ErrorClass(enum.Enum):                       # sb/spec/outcomes.py (the leaf, §⑦.1)
    NONE="none"; USER_ERROR="user_error"; DENIED="denied"; TRANSIENT="transient"; BUG="bug"

@dataclass(frozen=True)
class ErrorEnvelope:
    error_class: ErrorClass
    reason: DenialReason      # machine reason (sb/spec/outcomes.py) — never builder-invented
    retryable: bool
    user_message: str         # [S] one canonical copy per class, surface-enriched
    log_level: int            # WARNING for user_error/denied/transient; ERROR (+traceback) for bug
    outcome: str              # the §2.7 constant this class maps to (below)
```

### 1.2 The frozen exception → class → reason → outcome → copy table

| Exception (representative) | `error_class` | `reason` (`DenialReason`) | `retryable` | §2.7 `outcome` | `user_message` |
|---|---|---|---|---|---|
| `MissingRequiredArgument`, `BadArgument`, `TransformerError`, spec `ValidatorError` | `user_error` | `USER_ERROR` | `True` (after fix) | `BLOCKED` | "Missing/invalid argument `<name>`. `!help <cmd>`." |
| `PermissionError`, `commands.CheckFailure`, `app_commands.CheckFailure` | `denied` | `AUTHORITY` | `False` | `BLOCKED` | authority-engine `denial_message`, else "You don't have permission…" |
| `discord.Forbidden` (bot lacks a Discord perm) | `denied` | `DISPATCH_ERROR` | `False` | `BLOCKED` | "I'm missing a Discord permission: `<perm>`." (reason is `DISPATCH_ERROR`, our gap — **not** `AUTHORITY`) |
| `discord.HTTPException`(non-403), `RateLimited`, `asyncio.TimeoutError`, **`ConnectionError`** (incl. **`DBUnavailable`**), asyncpg pool-timeout | `transient` | `DISPATCH_ERROR` | `True` | `DISCORD_FAILED` | "Discord/the service is busy — try again shortly." |
| anything else (unhandled) | `bug` | `DISPATCH_ERROR` | `False` | `BLOCKED` | "Something went wrong on our end — it's been logged." + ERROR/traceback + operator finding |

- **`CommandOnCooldown` is not an input** — cooldown is caught at `resolve()` step 3 (pre-dispatch),
  never raised into `from_exception`.
- **`bug → BLOCKED` is a documented stretch:** the `{user_error, denied, transient, bug}` nuance lives
  in `error_class` + `reason`, **never** in `outcome`. `outcome` stays the frozen 5 so the golden
  harness reads any `Result` as a `LifecycleResult` ("new-as-old").
- **`DBUnavailable` (05) is zero-edit (RC-8):** `DBUnavailable(ConnectionError)` classifies via the
  **existing** `ConnectionError` transient row — no new row, no edit to 02. The DB seam (05 §3.4) is
  the sole producer of `DBUnavailable`; the resolver is the sole classifier.
- **Wizard fold-in:** `surface=setup` passes `section_label`; the envelope's `user_message` is enriched
  with the section + Retry/Skip. This **retires** `recovery_context_from_exception`; its
  `permission_hints` map **is** the `denied`/`transient` rows.

### 1.3 `Result` — the dispatch result the envelope maps into

```python
@dataclass(frozen=True)
class Result:                                # kernel/interaction/result.py (02)
    outcome: str                   # §2.7 vocab ONLY (copies WorkflowResult.outcome through unchanged)
    reason: DenialReason           # ALLOWED on success
    error_class: ErrorClass        # NONE on success
    retryable: bool
    reply_visibility: ReplyVisibility   # resolved by resolve_reply_visibility (T2-17)
    user_message: str | None       # None = silent
    surface: Surface
    workflow: "WorkflowResult | None"   # None for OPEN_PANEL / confirm-pending
    audit_emitted: bool            # dispatch-trace emitted (publish-accepted only)
    request_id: str
```

**Outcome mapping (the one rule):** a dispatched `HandlerRef`/`WorkflowRef` returns a `WorkflowResult`;
the resolver **copies `outcome` through unchanged** and uses `classify_outcome` semantics for batched
steps. `OPEN_PANEL` and confirm-pending ⇒ `outcome=SUCCESS, workflow=None`. **`StageResult` is never a
dispatch return** (§0); the dispatch-return grammar is `WorkflowResult|None` only.

---

## ② `authority_ref` → TWO-LANE RESOLUTION + owner-override-once (04 hardened — captured verbatim)

**Owner:** spec 04, the authority engine **K6** (`sb/spec/authority.py` leaf + `kernel/authority/*`).
**Consumers:** the resolver (02, step 1), the compiler P4 (`validate_authority_ref`, over **six** spec
types), K7's four workflow lanes (each calls `resolve_authority` as their first step), **strand-2**
(any authored mutation declares one `authority_ref`).

> **Hardening delta (2026-07-04):** the authority kernel is now **discord-free** — it consumes a
> **pre-computed** `member_tier` string, never a `discord.Member` (RC-12). `ChannelAccessDecision`
> gains `detail` (RC-13). `denial_message` is **engine-generated, not a spec field** (RC-14). The
> transparency emit rides a **`TransparencySink` port + the `command.dispatched` flag**, never
> `emit_audit_action` (RC-15). All four are frozen below.

### 2.1 The declared field (one string, always) — on **six** spec types

```python
# on CommandSpec / PanelActionSpec / SelectorSpec / SettingSpec / BindingSpec / ResourceRequirement
authority_ref: str = ""    # [S] — the SOLE authority field. Replaces capability_required + audience_tier (Q-0237d)
```

The **six authority-bearing spec types** are frozen (compiler 01 P4 reads `authority_ref` on all six).
`authority_ref` is the **only** `[S]` field this engine reads; every decision field below carries no
S/A/O tag.

### 2.2 `classify_authority_ref(ref) -> Lane` — pinned, total, non-overlapping

```python
def classify_authority_ref(ref: str) -> Lane:      # sb/spec/authority.py — pure syntactic
    if ref == "":                 return Lane.CAPABILITY   # empty ⇒ ADMIN floor
    if "." in ref:                return Lane.CAPABILITY   # ANY dotted string ⇒ capability lane
    if ref in TIERS:              return Lane.TIER         # exact, case-sensitive (TIERS are lowercase)
    raise BadAuthorityError(ref)                           # neither dotted nor a tier token
```

| `authority_ref` value | `Lane` (04) | Runtime resolution | Compile check (`validate_authority_ref`) |
|---|---|---|---|
| `""` (empty) | `CAPABILITY` (**ADMIN floor**) | `member_tier ≥ administrator`, **no** revoke overlay (ports `capability.py:27` — empty resolves to the floor, NOT no-auth) | always valid (**ADMIN-floor carve-out — never flag `""`**) |
| `"{sub}.{res}.{action}"` (dotted, 3-part) | `CAPABILITY` | ADMIN floor **+** revoke overlay keyed on `ref` (`capability_execution_overrides`) | namespace-reserved (K1 P3) + 3-part/reserved-prefix format |
| `"user"\|"trusted"\|"staff"\|"moderator"\|"administrator"\|"owner"` | `TIER` | `is_tier_sufficient(member_tier, ref)` (ported `visibility_rules.py:61`) | `ref ∈ TIERS` (case-sensitive) |
| dotted but not 3-part (`"a.b"`, `"a.b.c.d"`) | `CAPABILITY` (classifier) | — (rejected at compile) | **`FormatError("capability_not_3_part")`** → `bad_authority` |
| anything else (no dot, not a tier) | — | — | **`BadAuthorityError`** → compiler `bad_authority` → `COMPILE_ERROR` |

- **Classification vs format** are two steps: `classify_authority_ref` never raises on arity — only on
  "neither dotted nor a tier token." A malformed dotted string classifies to CAPABILITY then fails the
  3-part check inside `validate_authority_ref`.
- **Tier tokens are case-sensitive** (`"Administrator"` ≠ `"administrator"` → `BadAuthorityError`).
- **Empty = ADMIN floor, never no-auth** (`_DEFAULT_REQUIRED_TIER="administrator"`, `capability.py:48-51`,
  verified). A domain surface "for everyone" declares `authority_ref="user"` (a tier token), never `""`.
- **v1: every CAPABILITY ref resolves to the administrator tier**; a future `{capability→tier}` matrix
  slots in with zero field/resolver change.

### 2.3 `AuthorityRequest` + `AuthorityDecision` — the frozen shapes (04 owns; 02 imports them — RC-2)

```python
@dataclass(frozen=True)
class AuthorityRequest:              # discord-FREE — carries a pre-computed tier string, never a Member
    authority_ref: str              # [S] from target.spec
    actor_type: str = "user"        # "user" | "system" | "backfill" | "setup_delegate" (ported)
    user_id: int | None = None      # actor identity — for the owner predicate; None for scripted actors
    guild_id: int | None = None     # the TARGET guild id (the write target); None only for scripted bypass
    is_member: bool = False         # actor is a member of the TARGET guild — asserted by the caller
    member_tier: str | None = None  # PRE-COMPUTED tier string in the target guild (adapter); None for scripted/non-member

@dataclass(frozen=True)
class AuthorityDecision:              # the frozen 10-field shape (04/K6 owns; 02 imports it — RC-2)
    allowed: bool
    authority_ref: str
    lane: Lane                        # CAPABILITY | TIER  (sb/spec/authority.py — canonical, RC-3)
    required_tier: str                # "administrator" (capability) | the tier token (tier)
    member_tier: str | None
    owner_override: bool              # the ONCE-computed override verdict — threaded to channel-access
    lane_would_deny: bool             # would the LANE (incl. revoke) have denied? (transparency input)
    reason: DenialReason              # ALLOWED | AUTHORITY  (sb/spec/outcomes.py)
    detail: str                       # ported rich audit reason (capability.py:174-193 strings)
    denial_message: str | None        # ENGINE-GENERATED generic copy on deny (NOT [S], RC-14); None on allow

async def resolve_authority(req: AuthorityRequest) -> AuthorityDecision: ...
```

**Discord-free seam (RC-12).** The 6-tier ladder (`user/trusted/staff/moderator/administrator/owner`)
cannot be recovered from `ActorRef.is_guild_operator: bool` (which collapses staff/mod/admin/owner into
one flag). The **surface adapter** — the discord-touching layer — pre-computes `member_tier` via
`member_tier_from_member(member, guild.owner_id)` (§⑩) and sets it on `ActorRef`. **Spec 02's `ActorRef`
MUST add `member_tier: str | None`** (keeping `is_guild_operator`/`is_bot_owner`/`user_id`/`is_dm`), or
the TIER lane cannot resolve staff/moderator/administrator/owner. This is the one non-trivial cross-spec
wiring — 02 has not yet absorbed it.

**`resolve_authority` fixed internal order** (owner-override computed **once, at the top**, *after* the
membership gate so it composes with no-cross-guild-escalation):

| # | Step | Rule |
|---|---|---|
| 0 | classify | `lane = classify_authority_ref(ref)` — pure syntactic; touches no actor/guild/tier. |
| 1 | scripted bypass | `actor_type ∈ {system, backfill}` ⇒ `allowed=True`, `owner_override=False`, `member_tier=None`, `lane_would_deny=False`, `reason=ALLOWED`. **Return.** |
| 2 | **membership gate** | non-scripted actor must be `is_member` of `target_guild`; else deny (`reason=AUTHORITY`, `owner_override=False`, `lane_would_deny=False`). **Owner is not exempt — member-guilds-only** (§⑧ SF-b). **Return.** |
| 3 | **compute tier + lane result** | `member_tier = req.member_tier`. `lane_allows`: CAPABILITY ⇒ `is_tier_sufficient(member_tier, ADMIN_FLOOR_TIER)` + revoke overlay if `ref` non-empty; TIER ⇒ `is_tier_sufficient(member_tier, ref)`. Set **`lane_would_deny = not lane_allows`** (unconditional, every member path). |
| 4 | **owner-override (ONCE, top)** | `owner_override = owner_override_holds(req.user_id, req.is_member)`. `True` ⇒ `allowed=True` regardless of `lane_allows` (placed before the revoke result so a guild cannot revoke the owner). |
| 5 | setup_delegate | not overridden ∧ `actor_type=="setup_delegate"` ⇒ `allowed = not revoked` (ported Q-0098; still membership-gated, still revoke-subject). |
| 6 | lane check | not overridden, not delegate ⇒ `allowed = lane_allows`. |

`allowed = scripted OR (member AND (owner_override OR (setup_delegate AND not revoked) OR lane_allows))`.
`owner_override_holds(user_id, is_member) := is_platform_owner(user_id) and is_member` is the **single**
owner predicate — the ~11–16 scattered `is_platform_owner` authorization sites collapse to it (an AST
fence forbids any other module authorizing on `is_platform_owner` directly; the sole other sanctioned
caller is the adapter building `ActorRef.is_bot_owner`, a *classification* fact for the bootstrap leg).
Owner id is deploy config (`BOT_OWNER_USER_ID`, `config.py:40`, verified).

**`denial_message` — engine-generated (RC-14, corrects the earlier `[S]` tag).** Selected by
`(lane, reason)`; **not** a spec field. `from_exception`'s `denied` row reads it. The v1 generic table:

| Deny cause | `denial_message` |
|---|---|
| TIER lane, tier floor not met | "You need the **{required_tier}** role (or higher) to use this." |
| CAPABILITY lane, admin floor not met | "You need administrator permission to use this." |
| revoke overlay (`ref` disabled for the guild) | "This action has been turned off for your role in this server." |
| membership gate (non-member) | "You must be a member of this server to use this." |

### 2.4 Channel-access lane (folded in; honors the once-computed override — RC-4, now 8 fields RC-13)

```python
class AccessMode(enum.Enum):                     # SHIPPED value strings, verbatim (command_access.py:184-186)
    ALL_CHANNELS = "all_channels"
    SELECTED_CHANNELS = "selected_channels"
    DISABLED_EXCEPT_BOOTSTRAP = "disabled_except_bootstrap"

@dataclass(frozen=True)
class ChannelAccessDecision:            # 8 fields — canonical (RC-13, supersedes the 7-field view)
    allowed: bool
    mode: AccessMode | None             # None = unconfigured (default-allow)
    reason: DenialReason                # ALLOWED | CHANNEL
    detail: str                         # "" on allow | "commands_disabled" | "channel_not_allowed"  (RC-13)
    owner_override: bool                # short-circuited by the once-computed owner_override
    bootstrap_bypass: bool              # short-circuited by the shipped operator/owner bootstrap path
    would_deny_without_override: bool   # transparency input
    denial_message: str | None

async def resolve_channel_access(
    policy, channel_id: int | None, *,
    owner_override: bool,   # threaded from AuthorityDecision.owner_override (member-gated)
    is_bootstrap: bool,     # = is_bootstrap_command(target.key) — a K1/registry lookup (CONSUMED)
    is_operator: bool,      # = actor.is_guild_operator (shipped _is_guild_operator)
    is_owner: bool,         # = actor.is_bot_owner (is_platform_owner, MEMBERSHIP-BLIND)
) -> ChannelAccessDecision: ...
```

**Order:** ① `owner_override` ⇒ ALLOW **any** command (the **L-12 fix** — was bootstrap-only at
`command_access.py:351`) ② `is_bootstrap AND (is_operator OR is_owner)` ⇒ ALLOW (shipped bootstrap path,
**operator or owner**, `bootstrap_bypass=True`) ③ `mode∈{None, ALL_CHANNELS}` ⇒ ALLOW ④
`DISABLED_EXCEPT_BOOTSTRAP` ⇒ DENY (`reason=CHANNEL, detail="commands_disabled"`); `SELECTED_CHANNELS` ⇒
ALLOW iff `channel_id ∈ policy.allowed_channels`, else DENY (`reason=CHANNEL,
detail="channel_not_allowed"`). Lifecycle/DM legs are **not** here — they moved to K5 admission
(resolver step 0).

- **Two owner semantics (D6).** `owner_override` (leg 1) is **member-gated** (bot-owner AND member — the
  L-12 fix). `is_owner` (leg 2, bootstrap) is **membership-blind** (`is_platform_owner`, preserved
  verbatim from `:351`). Under the composed resolver order authority step-1 runs before channel-access
  step-2, so a non-member owner is already denied at membership (X-7) and the `is_owner` leg is narrowed
  to a theoretical edge; the **guild-operator** bootstrap leg stays live.
- **`detail` disambiguates** the two CHANNEL denials; `reason` stays `CHANNEL`. A distinct
  `DenialReason.COMMANDS_DISABLED` member is optional-additive (§⑦.1).

> **Binding seam (RC-4).** The resolver (02) **must** thread `decision.owner_override` from its step 1
> into the step-2 `resolve_channel_access` call **and** into the subsystem-visibility check
> (`governance/resolver.py:223` reads the once-computed flag, never re-derives `is_platform_owner`). As
> 02 is currently written step-2 treats channel-access as independent — **02 must change**, or L-12
> re-opens for the owner.

### 2.5 The transparency-audit contract (04 owns; emit path pinned — RC-15)

```python
@dataclass(frozen=True)
class TransparencyAudit:
    actor_id: int; guild_id: int; authority_ref: str
    target_key: str                   # command name | "<panel_id>.<action_id>"
    surface: str
    would_deny_reason: DenialReason   # AUTHORITY (lane) | CHANNEL (channel-access)
    timestamp: datetime

def build_transparency_audit(auth: AuthorityDecision, channel: ChannelAccessDecision | None,
                             *, actor_id: int, guild_id: int, target_key: str, surface: str,
                             clock) -> TransparencyAudit | None: ...   # + the TransparencySink port
```

- **Trigger (RC-5):** `auth.owner_override AND (auth.lane_would_deny OR (channel is not None AND
  channel.would_deny_without_override))` — returns `None` when the override was a no-op (no audit noise).
  `actor_id` is a **build parameter** (`req.actor.user_id`), not a decision field.
- **Emit path — NOT `emit_audit_action` (RC-15).** A `TransparencyAudit` is not a mutation and cannot
  fill the 11-field mutation seam (no `mutation_id`/`mutation_type`/`prev_value`/`new_value`). It rides
  **two designed carriers**: (1) the **`TransparencySink` port** (04 calls `sink.emit(audit)` at
  resolver step 4 when non-`None`); (2) the **`override_applied`/`base_allowed` flags** on the resolver's
  `command.dispatched` observability trace (§③), **derived** as `override_applied = owner_override ∧
  lane_would_deny`, `base_allowed = ¬lane_would_deny`. **Spec 02 must name `build_transparency_audit` +
  `TransparencySink`** rather than its unnamed "additionally routes to the transparency-audit sink."
- **Sink + fallback (owner-gated §⑧ SF-b):** dual sink (bot-log + server-log); no server-log ⇒ bot-log +
  batched owner-DM digest (`TransparencySink.emit` + `flush_digest`). Whether the sink is *also* a durable
  audit row is owner-gated.

---

## ③ THE AUDIT-ROW SEMANTICS

**Owner of the row seam:** the shipped `services.audit_events.emit_audit_action` (ported into K7's
workflow engine). **Owner of the dispatch-trace:** the resolver (02, step 4). **Consumers:**
`server_logging._on_audit_action` (via `bus.on`), the operator audit log, **strand-2's workflow engine**
(completes the compound-op row), the transparency sink (04).

### 3.1 When audit fires, and the two distinct seams

| Seam | Fires | Owner | Shape | Retained? |
|---|---|---|---|---|
| **Mutation audit** — `emit_audit_action(...)` | **once per auditable mutation**, *inside* the domain `*_mutation.py` / K7 workflow engine — **never** bypassed by the resolver | K7 / domain | the frozen **11 keyword-only fields** (below), keyed by `mutation_id` | **Yes** — links to the audit DB row |
| **Dispatch trace** — `command.dispatched` EventSpec | **once per dispatch**, at resolver step 4 | resolver (02) | `EventSpec observability_only=True, owner_subsystem="kernel"` (reserved carve-out); payload below | **No** in v1 (telemetry) — promotion is §⑧ SF-c |

**One command ⇒ one dispatch-trace + zero-or-more mutation-audit rows.** The resolver's trace is
**additive and distinct**; it never bypasses `emit_audit_action`. The **transparency notice is neither
of these two** — it is not a mutation, so it never fills the 11-field seam; it rides the `TransparencySink`
port + this trace's `override_applied` flag (§②.5 / RC-15).

### 3.2 `emit_audit_action` — the frozen 11-field payload (shipped, `audit_events.py:52`, verified)

```python
async def emit_audit_action(*, mutation_id: str, subsystem: str, mutation_type: str, target: str,
    scope: str, guild_id: int | None, prev_value: str | None, new_value: str | None,
    actor_id: int | None, actor_type: str, occurred_at: datetime) -> bool: ...
```

- `mutation_id` — pipeline-issued UUID; **the link** between the `audit.action_recorded` bus event and
  the audit DB row. Every auditable mutation mints one.
- Failure-safe: a bus failure logs `exc_info=True` and returns `False`; **DB state is authoritative** —
  a dropped audit event is non-fatal.
- The `audit.action_recorded → server_logging._on_audit_action` subscription is a **`bus.on` edge**
  (invisible to Grimp *and* CodeGraph — `server_logging` does not import `audit_events`); grep the
  event-name string, never trust a blast radius.

### 3.3 One-row-vs-N skeleton (what strand-2's workflow engine completes)

| Operation shape | Rows | Correlation |
|---|---|---|
| **Single mutation** (direct lane) | 1 `emit_audit_action` → 1 row | its own `mutation_id` |
| **Batched lifecycle op** (`LifecycleResult`, N `StepResult`s — e.g. rename 5 channels) | **1** row for the batch; the N steps are sub-detail *inside* the result, **not** N rows | **one** `mutation_id` for the whole apply |
| **Compound draft-lane op** (Final Review applies N distinct `SetupOperation`s across settings) | **N** `emit_audit_action` → N rows | a shared draft/orchestration id correlates them |

**Strand-2 completes:** the K7 workflow engine issues each `mutation_id` and calls `emit_audit_action`
per mutation; it owns the compound-op correlation id and the per-mutation `mutation_type` verb tokens.
The `command.dispatched` payload is: `{request_id, surface, command_key, actor_id, guild_id,
authority_ref, lane, override_applied, base_allowed, orchestration_id?, outcome, reason}` where
`override_applied`/`base_allowed` are **derived** from `AuthorityDecision` (RC-2/RC-5/RC-15).

### 3.4 Compile-time audit fence (01 P6 `audit_completeness`)

Every **mutating** ref must route through the audited seam: a spec whose `effect="mutating"` MUST carry
a **`WorkflowRef`** (the K7 audited workflow engine — the compile-checkable, AST-free proxy for "routes
through `emit_audit_action`"). The manifest `effect ∈ {read, mutating, external}` field (spec 02 §9) is
the input. A mutating ref that is a bare `HandlerRef` is a `SEMANTIC_VIOLATION` → CI-red / `FAILED_STARTUP`.

---

## ④ THE IDEMPOTENCY-KEY CONTRACT (T2-2 skeleton)

**Owner of the shape:** spec 05 (`sb/kernel/db/idempotency.py`). **Consumers:** the resolver dispatch
check-point (02, step 5), **strand-2's outbox + scheduler** (complete per-action `dedup_token`s and the
in-txn outbox), every double-fireable action.

### 4.1 The canonical key + outcome shapes (frozen)

```python
@dataclass(frozen=True)
class IdempotencyKey:
    namespace: str      # the action family, namespace-reserved (e.g. "economy.daily", "rps.forfeit")
    guild_id: int
    dedup_token: str    # the action's NATURAL key: message_id | interaction_id | (tournament_id,round) | …
    def render(self) -> str: ...   # f"{namespace}:{guild_id}:{dedup_token}"  — the stored PK

@dataclass(frozen=True)
class PriorOutcome:
    outcome: str            # §2.7 vocab ONLY
    result_ref: str | None  # pointer to the durable result (audit/mutation id)
    first_seen_at: int

async def once(key, *, conn) -> bool: ...           # INSERT … ON CONFLICT DO NOTHING RETURNING
async def record_outcome(key, outcome, *, result_ref=None, conn) -> None: ...   # UPDATE, same txn, §2.7-validated
async def read_outcome(key, *, conn) -> PriorOutcome | None: ...                # False-branch read
```

**Canonical atomic pattern** — guard row + effect + outcome commit-or-roll-back **together** on one
txn-bound `conn` from `db.transaction()` (05 §3.4/§3.7):

```python
async with db.transaction() as conn:
    if await once(key, conn=conn):
        result = await apply_effect(conn=conn)
        await record_outcome(key, result.outcome, result_ref=result.audit_id, conn=conn)
    else:
        return await read_outcome(key, conn=conn)   # reproduce / no-op (may be None if still mid-flight)
```

### 4.2 Where the key is applied (three sites; strand-2 completes two)

| Site | Key | Owner | Note |
|---|---|---|---|
| **Dispatch dedup** | durable `IdempotencyKey` checked at resolver **step 5** before the handler runs | resolver owns the *check-point*; 05 owns the *format* | dedups a MESSAGE_CREATE/interaction delivered to both gateway connections on deploy overlap |
| **Confirm re-entry dedup** | in-memory **`request_id`** (a uuid on `ResolveRequest`) — **NOT** an `IdempotencyKey` | resolver (02) | a double-clicked confirm runs once; session-scoped, not durable |
| **Leg / relay dedup** (outbox emit, scheduler fire) | `IdempotencyKey.dedup_token`; the outbox row is written inside the **same `db.transaction()` conn** as `once()` | **strand-2** | at-least-once → exactly-once over the durable substrate (L-9) |

**Strand-2 completes:** the per-action `dedup_token` definition for each double-fireable action, and the
in-txn outbox that emits under the same key + `conn`. The `idempotency_keys` table:
`key(PK) · namespace · first_seen_at · outcome(nullable until record_outcome) · result_ref`.

---

## ⑤ THE RESTART-SAFETY PATTERN (skeleton — the scheduler completes it)

**Owners:** the durable store + fast-release handoff (05); the drain gate on all surfaces (02, step 0).
**Consumers / completer:** **strand-2's scheduler** (durable timer store + boot-reconcile).

### 5.1 The frozen skeleton

1. **Durable store.** State that must survive a merge=deploy restart lives in a DB table, not memory:
   `idempotency_keys` (05) for effect dedup; the **scheduler's own durable-timer table** (strand-2) for
   armed timers. Cooldown state is **in-memory** and resets on restart (durable cooldown store deferred,
   §⑧ SF-e · L-8/T2-6). Confirmations **survive nothing** (session-scoped; a restart drops the prompt and
   the actor re-invokes).
2. **Drain gate on every surface.** Resolver **step 0** calls `lifecycle.can_accept_commands()` (K5): a
   draining instance stops **silently** (no ack) for slash/prefix/component/selector/modal/NL — the
   generalization of the shipped message-only gate (**RC-9**: the predicate is
   `lifecycle.is_shutting_down()`; `message_pipeline.py:277` only *invokes* it).
3. **Boot-reconcile fires overdue exactly once.** On boot, **after `/ready` reports 200 (RUNNING)** —
   never against a DB the readiness gate would 503 — the scheduler reads its durable timer store and, for
   each overdue timer, fires it **guarded by `once(IdempotencyKey)` inside `db.transaction()`**. So a
   timer overdue across a restart, or seen by both instances during the fast-release overlap, fires
   **exactly once**.
4. **Fast-release handoff (05 §6).** Old worker → SIGTERM → `DRAINING` → `/ready` 503 (router stops
   routing) → **releases the runtime lock immediately** (no drain-to-zero wait); new worker takes the
   lock at boot. The sub-second both-live window is covered by `once()` — this is why fast-release is
   *correct* where the `#1693` listener-only gate (L-6) was not: `once()`+`db.transaction()` covers
   prefix, interaction, and non-message lanes **uniformly**.

### 5.2 Strand-2 completes

The scheduler's durable-timer table shape + the boot-reconcile procedure (read → filter overdue → fire
under `once()`), and the outbox's at-least-once delivery. Both **consume** §④'s key + `db.transaction()`.
**Invariant strand-2 must honor:** durable timers are re-armed **only after `/ready` 200** (RUNNING-only;
STARTING ⇒ 503, the 05 §3.8 semantics change).

---

## ⑥ THE CONFIG / SECRET GRAMMAR + THE DATA-PLANE RAIL

**Owner:** spec 05 (`sb/spec/config.py` + `sb/kernel/config/*` + `sb/kernel/db/data_plane.py`).
**Consumers:** the composition root (`preflight()` is boot leg-0), `db.init(cfg)`, generated
`docs/ownership.md` env section, **strand-2** (reads config via `cfg.<ENV_VAR>`), K1 (`ConfigSpec.env_var`
is a namespace claim).

### 6.1 The grammar (all fields `[S]`)

```python
class ConfigPosture(StrEnum): FAIL_FAST; DEGRADE; DORMANT
class ConfigType(StrEnum):    STR; INT; FLOAT; BOOL; SECRET; DSN; CSV     # CSV → tuple[str,...]; absent ⇒ ()
class DataPlane(StrEnum):     TEST; PROD

@dataclass(frozen=True)
class ConfigSpec:
    env_var: str            # exact env name AND the Config attribute name (verbatim)
    type: ConfigType; required: bool; default: object | None = None
    posture: ConfigPosture = FAIL_FAST
    owner_subsystem: str | None = None; activation_link: str | None = None
    choices: tuple[str,...] = (); min: float | None = None; redact: bool = False

class SecretSpec(ConfigSpec): ...    # type=SECRET, redact=True enforced; only presence observable
class IntentSpec: name; privileged; required; approval_env    # gateway-intent contract (T2-22/L-17)

CONFIG_FIELDS: tuple[ConfigSpec,...]   # 39 harvested env vars + 8 new operational = 47 total, the ONE registry
INTENT_CONTRACT: tuple[IntentSpec,...] # message_content + members (the two hardcoded privileged intents)
```

### 6.2 The one accessor + preflight (RC-10 — one attribute per field, no `.get(spec)`)

`Config` exposes **one typed frozen attribute per `ConfigSpec`, named verbatim by `env_var`**
(`cfg.DATABASE_URL`, `cfg.DB_COMMAND_TIMEOUT_S`, `cfg.SB_PROD_ATTEST`, …). Coercion by `ConfigType`
(`BOOL→bool` via `parse_bool` — the one grammar `{1,true,yes,on,y,t}` truthy / else `ConfigError`;
`DSN→str` via `parse_dsn` shape-only, no connect; `CSV→tuple[str,...]`). `redact=True` (every SECRET +
DSN) is a **field property** enforced by `__repr__`/diagnostics — no sibling `Secrets` object.
`preflight(env) -> Config` runs **first in the composition root, before the compiler boot_gate legs and
before gateway connect**; it coerces+validates **all** env, accrues `ConfigError`s, and raises one
`StartupError` (→ lifecycle `FAILED_STARTUP`). It then runs `assert_intents` (message_content/members are
the two hardcoded privileged intents — `bot1.py:77-78`, verified; approval enforced in non-test planes)
and `assert_data_plane`.

### 6.3 The data-plane rail invariant (the 4th kernel rail, L-10)

```python
def assert_data_plane(cfg: Config) -> None: ...   # inside preflight(), before db.init; reads only Config attrs
```

- `SB_DATA_PLANE` **required** ∈ `{test, prod}` (absence ⇒ FAIL_FAST).
- `TEST` ⇒ `urlsplit(cfg.DATABASE_URL).hostname ∈ cfg.SB_TEST_DB_HOSTS` **or** the DSN carries `?sb_plane=test`; else `RefuseBoot`.
- `PROD` ⇒ `cfg.SB_PROD_ATTEST` **present** (a `SecretSpec`; presence = attestation, value never logged)
  **AND** `cfg.RAILWAY_SERVICE_NAME == "worker"`; else `RefuseBoot`.
- **Invariant:** a **non-`test` DSN without prod attestation + prod-worker identity ⇒ refuse boot**
  (`RefuseBoot` → `ConfigError` → `StartupError` → `FAILED_STARTUP`, before any network I/O). An
  agent/dev container may carry the prod DSN (Q-0213) but **not** `SB_PROD_ATTEST`, so it **structurally
  cannot open prod even by accident.** (Durable custody of the attest token is §⑧ SF-d · owner-gated.)

---

## ⑦ SUPPORTING FROZEN SEAMS (used by items ①–⑥)

### 7.1 The result-grammar leaf — `sb/spec/outcomes.py` (dependency-free)

Home of: the 5 outcome constants (re-exported), `ErrorClass`, `DenialReason`, `ReplyVisibility`,
`DeferMode`. **`DenialReason` lives here, not in `result.py`** (02 §3.6's inline copy is illustrative —
RC-6); K6 imports it. `DenialReason` = `{ALLOWED, DRAINING, AUTHORITY, DISABLED, VISIBILITY, CHANNEL,
USER_ERROR, COOLDOWN, AI_THROTTLE, NOT_FOUND, CONFIRM_DECLINED, DISPATCH_ERROR}`. `CHANNEL` covers both
`CHANNEL_NOT_ALLOWED` and `COMMANDS_DISABLED` (distinguished by `ChannelAccessDecision.detail`); a
distinct `COMMANDS_DISABLED` member is optional-additive. **The `Lane` enum lives in
`sb/spec/authority.py`** (04), imported by both `outcomes` consumers and the resolver — **not** 02's
`AuthorityLane` (RC-3).

### 7.2 The namespace oracle — `validate` / `is_reserved` / `Collision` (03, K1 owns — **RC-7 RESOLVED**)

The canonical K1 shape (spec 03 §3.2/§3.3), now adopted by 01 (RC-7 resolved — see §⑨):

| Seam | **Canonical (K1, 03)** |
|---|---|
| oracle | `validate(snapshot) -> NamespaceReport{ok, collisions, cap_violations, format_errors, index}` — a **pure function of the snapshot** (no manifest/spec import) |
| point query | `is_reserved(value, kind, *, surface, parent)` (value first; `parent=None` ⇒ top-level only) |
| collision | `Collision(kind, value, **scope**, claimant_a, claimant_b)`, key `(kind, value, scope)`, `scope = CommandScope(surface, parent_group)` for commands else `None` |
| command resolve | `resolve_command(name, *, surface) -> ReservationHit | None`; `check_trigger(word, *, index, min_len)` set-time gate |

The `scope = (kind, surface, parent_group)` key is **load-bearing**: without it `/ticket close` vs
`/thread close` and `!karma` vs `/karma` false-collide. **CI, `git merge-tree`, and boot all call the
same `validate`** → CI-green ⟺ boot-green by construction (kills the `#763` false-green class). A
trigger-set rejection surfaces as `outcome=BLOCKED` on the real `contracts.py:50` constant (§0). **01
adopted this verbatim** — its P3 is a thin call into K1's `validate`, mapping the three violation
categories into its `Violation` stream (`Violation` gained `scope`).

### 7.3 The ephemerality resolver + lane default (02, T2-17) — uses the canonical `Lane` (RC-3)

`resolve_reply_visibility(*, outcome, reason, lane, declared, committed) -> ReplyVisibility` over all
five §2.7 outcomes, single place. `lane_default(lane) = EPHEMERAL if lane is Lane.CAPABILITY else PUBLIC`
(**RC-3:** `CAPABILITY` ≡ 02's `CONFIG_GOVERNANCE`; `TIER` ≡ 02's `DOMAIN`). A defer commits
`V = declared or lane_default(lane)` at the ACK boundary; post-defer renders honor the committed flag.

### 7.4 The two-form `PredicateRef` (01/02) — resolved differently at compile

`enabled_when` / `visible_when` are `PredicateRef`. Two forms: a **namespaced string**
`"<kind>:<key>[=<value>]"` (`kind ∈ {setting, binding, capability, flag}`; `""` = constant-true) that
serializes as a **plain string** and is validated by the compiler P2 format gate (+ P3 key-reservation
for `setting:`/`capability:` heads); or a **registered ref** (`{"$ref":"predicate:<name>"}`) resolved
via the ref table. Runtime evaluator is `predicates.evaluate(ref, ctx)` — the namespaced form is a
parsed string, **never** `resolve()`.

---

## ⑧ OPEN SEAM FORKS (genuinely undecided — strand-2 must NOT assume a resolution)

| # | Fork | Tier / gate | Built default (buildable now) | The open call | Touches |
|---|---|---|---|---|---|
| SF-a | **Panel-action grammar** (02 §8-a / 01 §3.2 dep-flag): route-through-C-1 (panel actions/selectors carry the §3.0 `authority_ref`/`enabled_when`/`reply_visibility`/`cooldown`/`defer_mode` + `action_id`/`mirrors` on their own specs) vs minimal `PanelActionSpec` + derived authority/cooldown | Tier-2, **owner-gated** | (A) per-spec fields (recommended — retires L-5 structurally; **01 arms `never_strand`/`action_cooldown_parity` under option A**) | which spec holds the fields; **resolver contract unchanged either way**; under option B the two P6 predicates read the panel-owned derived path | draft/workflow ports that author panel actions; compiler P6 |
| SF-b | **Owner-override scope + transparency-sink wording** (02 §8-b / 04 §8-a/§8-c): scope member-guild vs any-reachable; sink = observability-only vs a distinct operator-visible transparency log/durable row | Tier-2, **owner-gated** | member-guilds-only is **built structurally** (04 step 2/4, X-7); dual sink (bot-log + server-log, owner-DM digest fallback), no durable row | owner **confirms** the scope; names the sink copy / whether it is a distinct authoritative row | audit-row semantics (③), transparency emit (②.5) |
| SF-c | **Dispatch-trace audit promotion** (02 §8-c): keep `command.dispatched` `observability_only=True` vs promote to a retained `AuditEventSpec` (one row per dispatch) | Tier-3, **owner-gated** | (A) observability-only for v1 | retention/volume posture — a retained row per dispatch | audit-row semantics (③), retention |
| SF-d | **`SB_PROD_ATTEST` durable custody** (05 §9): plain env `SecretSpec` vs sealed/managed secret vs short-lived OIDC claim | ops / CUT-1, **owner-gated** | presence-gated env `SecretSpec` (type CLOSED; the 4th rail is correct today) | the durable custody *source* | config/data-plane rail (⑥) |
| SF-e | **Durable cooldown store** (02 §9 · L-8/T2-6) | strand-2 durability (bounded) | in-memory (matches shipped; resets on restart) | the merge=deploy-surviving backing store the resolver reads off `CooldownSpec` | restart-safety (⑤) |
| SF-f | **Rung-4 orchestration failure policy** (02 §9) | Phase-4 band 6 (bounded) | stop-on-first-non-SUCCESS | a per-plan continue/compensate policy | NL orchestration (later) |
| SF-g | **Store-drop `disposition` default** (01 §8 fork 8) | data-loss policy, **owner-gated** | **no default** — `disposition` is a REQUIRED field on every signed `store_retirements.yml` entry (`export`/`reverse-migrate`/`declared-loss`) | the chosen value per retired store | store-completeness (compiler P7), data custody |

SF-a…SF-d + SF-g are genuinely **owner-gated**; SF-e/SF-f are **bounded deferrals** with a designed
default and a designed seam already in place. None blocks strand-2 from building to the frozen shapes
above.

---

## ⑨ RECONCILIATION LEDGER (where two specs disagreed → one canonical form)

| ID | Disagreement | Canonical form (winner) | Loser spec must change |
|---|---|---|---|
| **RC-1** | "outcome built on `StageResult`" / `WorkflowResult`+`contracts.py:48-52` framing | outcome vocab = `services/lifecycle/contracts.py:48-52` (real); dispatch return = `WorkflowResult\|None` (K7 superset of `LifecycleResult`, **spec-only, no shipped class**); `StageResult` is the shipped message-pipeline **analogue**, **not** the design dispatch return; `disbot/core/contracts.py` **absent** | prompt phrasing (clarified §0); all five specs already agree on the corrected form |
| **RC-2** | `AuthorityDecision` shape: 02's 5-field `{allowed, lane, denial_copy, override_applied, base_allowed}` vs 04's 10-field | **04 (K6) owns it** — 04's 10-field shape wins; `denial_copy`→`denial_message`; `override_applied` is **derived** = `owner_override ∧ lane_would_deny`; `base_allowed` = `¬lane_would_deny` | **spec 02** imports 04's `AuthorityDecision`; derives its trace flags |
| **RC-3** | Lane enum: 02 `AuthorityLane{CONFIG_GOVERNANCE, DOMAIN}` (in `outcomes.py`) vs 04 `Lane{CAPABILITY, TIER}` (in `authority.py`) | **04's `Lane`** (`sb/spec/authority.py`) — same two lanes; `CAPABILITY`≡config-governance⇒EPHEMERAL, `TIER`≡domain⇒PUBLIC | **spec 02** uses `Lane` in `lane_default`/`resolve_reply_visibility`; drops `AuthorityLane` |
| **RC-4** | Owner-override threading into channel-access | resolver **must** pass `decision.owner_override` into step-2 `resolve_channel_access` and the subsystem-visibility check (compute once at step 1) | **spec 02** (step 2 currently independent → L-12 re-opens) |
| **RC-5** | Transparency-audit firing condition | 04's `owner_override ∧ (lane_would_deny ∨ channel.would_deny_without_override)` (includes the channel leg) | **spec 02** extends its `override_applied`-only trigger with the channel decision at step 4 |
| **RC-6** | `DenialReason` home | `sb/spec/outcomes.py` (leaf); K6 imports it; `CHANNEL`+`detail` covers `COMMANDS_DISABLED` | 02 §3.6 inline copy is illustrative only |
| **RC-7** | Namespace seam names/keys (01 vs 03) | **RESOLVED** — **03 (K1) won**; **01 has now adopted** `validate(snapshot)→NamespaceReport`, `is_reserved(value, kind,…)`, `Collision(+scope)` key `(kind,value,scope)`; 01's `Violation` gained `scope`, P3 is a thin call into `validate` | ~~spec 01~~ **done** (01 §4.2/§10 reconciled 2026-07-04) |
| **RC-8** | `DBUnavailable` → resolver classification | zero-edit: `DBUnavailable(ConnectionError)` routes through 02's **existing** `ConnectionError` transient row → transient/retryable/`DISCORD_FAILED` | none (optional annotation on 02's row) |
| **RC-9** | Drain-gate cite | `lifecycle.is_shutting_down()` / `can_accept_commands()` (K5) — `message_pipeline.py:277` only *invokes* it. Two predicates coexist: resolver admission uses `can_accept_commands()` ({STARTING,RUNNING}); `/ready` uses **RUNNING-only** (05 §3.8, STARTING⇒503) — distinct callers, both valid | 02's `message_pipeline.is_shutting_down()` mis-cite corrected |
| **RC-10** | Config accessor: `.get(spec)`+`Secrets` vs one attribute per field | one typed frozen attribute per field, verbatim env name; redact is a field property | resolved in-file (05) |
| **RC-11** | Two `Surface` enums | **Do NOT unify** — namespace `Surface{PREFIX,SLASH}` (03, reservation scope) vs interaction `Surface{SLASH,PREFIX,COMPONENT,MODAL,NL_INTENT,NL_ORCHESTRATION}` (02, dispatch) are different layers/purposes | naming caution only |
| **RC-12** *(new)* | Authority engine discord-dependence: 02's `ActorRef{user_id, is_guild_operator, is_bot_owner, is_dm}` cannot supply the 6-tier ladder the TIER lane needs; 04 is now **discord-free** | 04's discord-free `AuthorityRequest.member_tier` (a pre-computed string) wins; the adapter computes it via `member_tier_from_member(member, guild.owner_id)` | **spec 02** must add `member_tier: str \| None` to `ActorRef` (keep the other four fields), or the TIER lane cannot resolve staff/moderator/administrator/owner |
| **RC-13** *(new)* | `ChannelAccessDecision` field count: earlier 7-field view vs 04's hardened 8-field | 04's **8-field** form (adds `detail ∈ {"", "commands_disabled", "channel_not_allowed"}`) wins — 04 owns the shape (§⑩ leaf inventory); `AccessMode` uses the **shipped value strings** (`"all_channels"`/…, `command_access.py:184`, verified), never `"all"/"selected"/"disabled"` | this doc's §②.4 absorbs the 8th field; any consumer view narrows to it |
| **RC-14** *(new)* | `denial_message` role tag: earlier `[S]`-derived vs 04's engine-generated | **engine-generated** generic copy per `(lane, reason)` — **not** a spec field; the sole `[S]` field is `authority_ref`. A per-spec `denial_copy` override is a labeled deferral (04 §9) | earlier `[S]` tag dropped; `from_exception` reads `AuthorityDecision.denial_message` on the `denied` row |
| **RC-15** *(new)* | Transparency emit seam: 02's unnamed "routes to the transparency-audit sink" vs 04's `TransparencySink` port | 04 owns `build_transparency_audit` + the `TransparencySink` port; emit path = **port + `command.dispatched` `override_applied`/`base_allowed` flags**, **NOT** `emit_audit_action` (a transparency notice is not a mutation and cannot fill the 11-field seam) | **spec 02** must **name** `build_transparency_audit` + `TransparencySink` at step 4 and derive the two flags from `AuthorityDecision` |
| **RC-16** *(cross-strand pass)* | Compound-op ↔ audit correlation: a 12th `emit_audit_action` bus field vs a DB column | **`audit_log.correlation_id` column** (07 §5 / 08 §5.1) — the 11-field bus payload is unchanged; the compound draft correlates its N rows by `ctx.correlation_id = draft_id` written to the column | **RECONCILED across 06/07/08** — resolves 06 §12's open co-decision; no consumer re-derives a bus field |
| **RC-17** *(cross-strand pass)* | `DeliveryClass` home: a local copy in K7 (07) vs the `[S]` grammar owner (08) | **`sb/spec/events.py`** owns `DeliveryClass{AT_LEAST_ONCE,BEST_EFFORT}` + `EventSpec.delivery`; **07 imports it** (no local copy) | **RECONCILED** — 08 §12.1 / 07 §8 fork F; one enum, no drift (see §⑩ leaf inventory) |
| **RC-18** *(cross-strand pass, F-4 — APPLIED 2026-07-04)* | `ActorRef.actor_type`: 09/11 assume it (`system`/`backfill`); frozen `ActorRef` (§⑩) lacked it | **additive `actor_type: str = "user"`** (`{user, system, backfill, setup_delegate}`) on 02's `ActorRef` + vocab §⑩; K7 maps `ctx.actor.actor_type → AuthorityRequest.actor_type` (§②.3 scripted-bypass); `SYSTEM_ACTOR="system"`, `SWEEP_ACTOR="backfill"` | **APPLIED** — 02 §3.1 adds the field; 09/11 consume it (no longer flagged corrections). **Distinct from RC-12 `member_tier`, still pending on 02.** |
| **RC-19** *(cross-strand pass, F-5 — APPLIED 2026-07-04)* | Background `Surface` member + `from_exception.target`: 09 used `surface="scheduler"`, 11 refused a `scheduler`/`maintenance` fork; interaction `Surface` (RC-11) had no background member and `target` was non-optional | **ONE** background member **`Surface.MAINTENANCE = "maintenance"`** (covers 09 scheduler fires AND 11 sweep-repairs — NOT a per-sibling split), added to the **interaction** `Surface` (02, not the namespace one — RC-11 still holds); **`from_exception.target → TargetRef \| None`**; background fires call `from_exception(exc, surface=Surface.MAINTENANCE, target=None)` (surface/target only enrich `user_message`) | **APPLIED** — 02 §3.1/§3.3 define; 09 §3.8 / 11 §2.2/§4 Q4/§8.2 / 07 §3.3-4b adopt; 11's Q4 → CLOSED |
| **RC-20** *(cross-strand pass, F-1 — APPLIED 2026-07-04)* | Poll topology: 08 registered the outbox relay as a `PollLane` on 09's `PollSupervisor`; 09 (as drafted) modeled it as its own standalone `RELAY_TASK(Interval 1s)` — unhosted if built as drafted | **09 HOSTS** `OutboxRelayLane` + `OutboxReaperLane` as `PollLane`s on its **one** `PollSupervisor` at the shared **5 s** cadence; the standalone-1 s-loop / not-my-lane model is withdrawn; the lane roster is **non-exhaustive** (due-queue + draft janitor + outbox relay/reaper today; invariant sweep + credential rotation as future riders) | **APPLIED** — 09 adopts 08's registered-lane model throughout; 08 already cites 09 as host (unchanged) |
| **RC-21** *(cross-strand pass, PENDING — Q-D26)* | `ChannelEmitter` send-egress port: a new `kernel/interaction` egress port + AST fence registered by neither the seam matrix nor this ledger — only inside 10's T-7 | register the **`ChannelEmitter.send` port** + the egress AST fence (raw discord send outside `adapters/discord/responders.py` = `SEMANTIC_VIOLATION`) as a pending **02/K8** seam correction; concrete `DiscordChannelEmitter` is the only module constructing `AllowedMentions` (`UNTRUSTED` default ⇒ `AllowedMentions.none()`) | **PENDING** — a registered additive correction parallel to RC-12/F-4; homed as **Q-D26** in the register, asserted by `10 §2.A`/§8. **02/K8 must add the port** when it wires egress |

---

## ⑩ FROZEN-LEAF INVENTORY (where each shared type lives)

| Leaf / port module | Owns | Landed |
|---|---|---|
| `sb/spec/outcomes.py` | 5 outcome constants (re-export), `ErrorClass`, `DenialReason`, `ReplyVisibility`, `DeferMode` | K6/K7 |
| `sb/spec/authority.py` | `Lane`, `TIERS`, `ADMIN_FLOOR_TIER`, `classify_authority_ref`, `validate_authority_ref`, `is_tier_sufficient` (tier-string order compare) | K6 |
| `sb/spec/config.py` | `ConfigSpec`, `SecretSpec`, `ConfigPosture`, `ConfigType`, `IntentSpec`, `DataPlane`, `CONFIG_FIELDS`, `INTENT_CONTRACT` | K0/K2 |
| `sb/spec/observability.py` | `MetricSpec`, `MetricKind`, `LabelSpec` | K0 |
| `sb/spec/refs.py` | `HandlerRef`/`PanelRef`/`ViewRef`/`PredicateRef`/`EngineRef`/`WorkflowRef`/`ProviderRef` + `@handler` (+ twins; `RefRedefined` on dup) + ref table | K2 |
| `sb/spec/roles.py` | `Role{S,A,O}`, `field_role()`, `snapshot_field_roles()` | K2 |
| `sb/namespace/{kinds,records,validate,index,triggers}.py` | `NamespaceKind`, `Surface`(PREFIX/SLASH), scope key, `validate`, `NamespaceReport`, `Collision(+scope)`, `ReservationIndex`, `is_reserved`, `resolve_command`, `check_trigger` | K1 |
| `sb/kernel/db/idempotency.py` | `IdempotencyKey`, `PriorOutcome`, `once`/`record_outcome`/`read_outcome`, `idempotency_keys` table | K3 |
| `sb/kernel/db/{pool,data_plane,migrations}.py` | `DBUnavailable(ConnectionError)`, `transaction()`/`checked_acquire()`, `assert_data_plane`, `verify_applied_checksums`/`MigrationDrift` | K3 |
| `sb/spec/events.py` | **`DeliveryClass{AT_LEAST_ONCE,BEST_EFFORT}`** (canonical home) + `EventSpec.delivery` [S] field — 07 imports it, no local copy (RC-17) | K4 |
| `kernel/interaction/{request,resolve,result,errors,predicates}.py` | `ResolveRequest`, `ActorRef` (**`actor_type` added — RC-18 applied; still must add `member_tier` — RC-12**), `Surface` (**gains the background `MAINTENANCE` member — RC-19**), `resolve`, `Result`, `from_exception` (**`target: TargetRef \| None` — RC-19**), `resolve_reply_visibility`, `SurfaceResponder` port; **pending: the `ChannelEmitter` send-egress port — RC-21/Q-D26** | K8 |
| `kernel/authority/{owner,decision,resolve,channel_access,transparency}.py` | `owner_override_holds`, `AuthorityRequest`/`AuthorityDecision`/`ChannelAccessDecision`/`AccessMode`/`TransparencyAudit`, `resolve_authority`, `resolve_channel_access`, `build_transparency_audit` + **`TransparencySink` port** | K6 |
| `sb/adapters/discord/member_tier.py` | `member_tier_from_member(member, guild_owner_id) -> str` — the **only** module that reads discord perms for authority (ports `visibility_rules.py:44`) | K8 |
| `sb/adapters/discord/transparency_sink.py` | concrete `TransparencySink` (bot-log + server-log + owner-DM digest) | logging band |
| `is_bootstrap_command(key) -> bool` | the bootstrap oracle (ports `command_access.py:71`) — a **K1/registry** name/registry property; consumed by `resolve_channel_access` | K1 |

---

*Re-synthesized 2026-07-04 over **all five** hardened strand-1 specs (`strand-1-kernel-spine/01…05`),
verified against shipped source this session (`services/lifecycle/contracts.py:40-52/56/66/77/108`,
`core/runtime/message_pipeline.py:181/277`, `services/audit_events.py:52`, `governance/capability.py:27/48-51`,
`core/runtime/command_access.py:71/181-206/256/351`, `utils/visibility_rules.py:21/44/61`, `config.py:40`,
`bot1.py:77-78`; `class WorkflowResult` and `disbot/core/contracts.py` re-confirmed ABSENT).
**NOT SOURCE OF TRUTH for runtime** — a design contract for strand 2 and the cross-cutting concerns to build ON.*

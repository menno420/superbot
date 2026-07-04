# Shared Vocabulary — Strand-1 Kernel Spine → Strand-2 & Cross-Cutting (FROZEN CONTRACT)

> **NOT SOURCE OF TRUTH for runtime.** This is a **design contract** — a Phase-B synthesis
> that freezes the exact shape of every recurring seam the strand-1 kernel-spine specs
> (`strand-1-kernel-spine/01…05`) hand to **strand 2** (draft · workflow · outbox · scheduler)
> and to the **cross-cutting concerns**. It authors no `disbot/` and no `sb/` code.
> **Precedence:** shipped source & merged PRs win over this doc; the five owning specs win over
> this doc *for shapes they own*; this doc wins only where it **reconciles a disagreement between
> two specs** (those rows are marked → the loser spec must change). Spot-verify every source cite.
>
> **Why this exists.** Six vocabularies recur across every kernel spec and every strand-2/cross-cut
> port. If each port re-derives them, they drift (the exact `#763` false-green / `L-4` four-postures
> class the rebuild exists to kill). This file is the single place they are frozen once. A strand-2
> builder writes to **these** shapes and makes zero further design decisions except the forks in §8.

---

## 0. Source-wins grounding (Q-0120) — the result-grammar seam everyone shares

Every spec carries the same seam correction; it is the substrate under items ① and ③–⑤, so it is
stated **once, here, canonically**, verified against shipped source this session.

| Symbol | Status | Real location / meaning |
|---|---|---|
| `SUCCESS` `PARTIAL` `BLOCKED` `DECLINED` `DISCORD_FAILED` | **REAL — the frozen §2.7 outcome vocab** | `disbot/services/lifecycle/contracts.py:48-52` (verified). The **only** five outcome constants. No 6th is ever added. |
| `LifecycleResult` | **REAL** | `services/lifecycle/contracts.py:77` — `{mutation_id, guild_id, domain, operation, outcome, reversibility, steps:tuple[StepResult], committed_at, audit_emitted, event_emitted}`. |
| `StepResult` / `classify_outcome` | **REAL** | `:56` (`target_id, target_name, ok, error`) / `:108` (`steps → SUCCESS/PARTIAL/DISCORD_FAILED`). |
| `WorkflowResult` | **DESIGN TYPE ONLY (K7)** | The §2.7 **kernel** result type — a strict **superset** of the shipped `LifecycleResult`, landed in K7. **Not a shipped class.** The dispatch-return grammar (`resolve()` step 5) is `WorkflowResult \| None`. |
| `StageResult` | **REAL but NOT a dispatch return** | `disbot/core/runtime/message_pipeline.py:181` — `{deleted, short_circuit, moderation_action}`. The **passive on-message pipeline substrate**, one layer *below* `resolve()`. It never crosses the `resolve()` seam and is **dropped from the dispatch-return grammar** so its overloaded `short_circuit` can never be mislabeled a dispatch `BLOCKED`. |
| `disbot/core/contracts.py` + a shipped `WorkflowResult` class | **FABRICATED — re-verified ABSENT** | Audit-A cite `core/contracts.py:48-52` does not exist (FJ L-4/L-25). Never design against it. |

> **Prompt-phrasing reconciliation (RC-1).** The task brief says the error envelope's outcome is
> *"built on the REAL `StageResult` (message_pipeline.py:181), NOT the fabricated
> `WorkflowResult`/contracts.py:48-52."* Corrected to the canonical form above: the outcome **vocab**
> is built on `services/lifecycle/contracts.py:48-52` (real); the **dispatch return** is
> `WorkflowResult|None` (the K7 design superset of `LifecycleResult`); **`StageResult` is a *different*
> substrate**, not the outcome source and not a dispatch return. The fabricated cite is
> `disbot/**core**/contracts.py` (absent) — distinct from the real `disbot/**services/lifecycle**/contracts.py:48-52`.

---

## ① THE ERROR ENVELOPE

**Owner:** spec 02 (`kernel/interaction/errors.py` + `result.py`). **Consumers:** every rung/adapter,
the composition-root `tree.error`/`on_app_command_error`/`on_command_error` shims, the DB seam (05),
the wizard fold-in, **strand-2 workflow/outbox** (which classify their own dispatch exceptions through
the same function).

### 1.1 `from_exception` — the one classifier

```python
def from_exception(exc: BaseException, *, surface: Surface,
                   target: TargetRef, section_label: str | None = None) -> ErrorEnvelope: ...

class ErrorClass(enum.Enum):                       # sb/spec/outcomes.py (the leaf, §9)
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
steps. `OPEN_PANEL` and confirm-pending ⇒ `outcome=SUCCESS, workflow=None`. **`DBUnavailable` (05)
classifies via the existing `ConnectionError` transient row — no new row, no edit to 02** (RC-8).

---

## ② `authority_ref` → TWO-LANE RESOLUTION + owner-override-once

**Owner:** spec 04, the authority engine **K6** (`sb/spec/authority.py` leaf + `kernel/authority/*`).
**Consumers:** the resolver (02, step 1), the compiler P4 (`validate_authority_ref`), K7's four
workflow lanes (each calls `resolve_authority` as their first step), **strand-2** (any authored
mutation declares one `authority_ref`).

### 2.1 The declared field (one string, always)

```python
# on CommandSpec / PanelActionSpec / SelectorSpec / SettingSpec / BindingSpec / ResourceRequirement
authority_ref: str = ""    # [S] — the SOLE authority field. Replaces §2.2's capability_required + audience_tier (Q-0237d)
```

### 2.2 `classify_authority_ref(ref) -> Lane` — total, non-overlapping

| `authority_ref` value | `Lane` (04) | Runtime resolution | Compile check |
|---|---|---|---|
| `""` (empty) | `CAPABILITY` (**ADMIN floor**) | `actor_holds_capability("")` → `required_tier="administrator"`, no revoke overlay (ports `capability.py:27`) | always valid |
| `"{sub}.{res}.{action}"` (dotted, 3-part) | `CAPABILITY` | ADMIN floor **+** revoke overlay keyed on `ref` | namespace-reserved (K1 P3) + 3-part/reserved-prefix format |
| `"user"\|"trusted"\|"staff"\|"moderator"\|"administrator"\|"owner"` | `TIER` | `is_tier_sufficient(member_tier, ref)` | `ref ∈ TIERS` |
| anything else | — | — | **`BadAuthorityError`** → compiler `bad_authority` → `COMPILE_ERROR` |

- **Empty = ADMIN floor, never no-auth** (`_DEFAULT_REQUIRED_TIER="administrator"`, `capability.py:51`,
  verified). A domain surface "for everyone" declares `authority_ref="user"` (a tier token), never `""`.
- **v1: every CAPABILITY ref resolves to the administrator tier** (`capability.py:48-51`); a future
  `{capability→tier}` matrix slots in with zero field/resolver change.

### 2.3 `AuthorityDecision` — the frozen shape (04 owns; 02's 5-field view superseded → RC-2)

```python
@dataclass(frozen=True)
class AuthorityDecision:              # OWNED by kernel/authority (K6); resolver + transparency consume it
    allowed: bool
    authority_ref: str
    lane: Lane                        # CAPABILITY | TIER  (sb/spec/authority.py — canonical, RC-3)
    required_tier: str                # "administrator" (capability) | the tier token (tier)
    member_tier: str | None
    owner_override: bool              # the ONCE-computed override verdict — threaded to channel-access
    lane_would_deny: bool             # would the lane have denied WITHOUT the override? (transparency input)
    reason: DenialReason              # ALLOWED | AUTHORITY  (sb/spec/outcomes.py)
    detail: str
    denial_message: str | None        # [S] user copy on deny; None on allow
```

**`resolve_authority` fixed internal order** (owner-override computed **once, at the top**, after the
membership gate so it composes with no-cross-guild-escalation):

`0` classify → `1` scripted bypass (`system`/`backfill`) → `2` **membership gate** (owner **not** exempt —
member-guilds-only) → `3` **owner-override ONCE** (`owner_override_holds(actor, target_guild)`; record
`lane_would_deny = not lane_allows`) → `4` `setup_delegate` → `5` lane check (+ revoke overlay on non-empty ref).

`allowed = scripted OR owner_override OR setup_delegate OR (member AND lane_allows AND not revoked)`.
`owner_override_holds` is the **single** owner predicate — the ~11–16 scattered `is_platform_owner`
authorization sites collapse to it (an AST fence forbids any other module authorizing on
`is_platform_owner` directly). Owner id is deploy config (`BOT_OWNER_USER_ID`, `config.py:40`, verified).

### 2.4 Channel-access lane (folded in; honors the once-computed override — RC-4)

`resolve_channel_access(policy, channel_id, *, owner_override, is_bootstrap, is_operator, is_owner)
-> ChannelAccessDecision{allowed, mode, reason, owner_override, bootstrap_bypass,
would_deny_without_override, denial_message}`. **Order:** ① `owner_override` ⇒ ALLOW any command
(the **L-12 fix** — was bootstrap-only at `command_access.py:351`) ② `is_bootstrap AND (is_operator OR
is_owner)` ⇒ ALLOW (shipped bootstrap path, **operator or owner**, preserved) ③ `mode∈{None, ALL}` ⇒
ALLOW ④ `DISABLED_EXCEPT_BOOTSTRAP` ⇒ DENY; `SELECTED_CHANNELS` ⇒ ALLOW iff `channel_id ∈ allowed`.
Lifecycle/DM legs are **not** here — they moved to K5 admission (resolver step 0).

> **Binding seam (RC-4):** the resolver (02) **must** thread `decision.owner_override` from its step 1
> into the step-2 `resolve_channel_access` call, and read the once-computed flag in the step-2
> subsystem-visibility check (`governance/resolver.py:223`) rather than re-derive `is_platform_owner`.
> As spec 02 is currently written, step-2 treats channel-access as independent — **02 must change**, or
> L-12 re-opens for the owner.

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
| **Dispatch trace** — `command.dispatched` EventSpec | **once per dispatch**, at resolver step 4 | resolver (02) | `EventSpec observability_only=True, owner_subsystem="kernel"` (reserved carve-out); payload below | **No** in v1 (telemetry) — promotion is §8-c |

**One command ⇒ one dispatch-trace + zero-or-more mutation-audit rows.** The resolver's trace is
**additive and distinct**; it never bypasses `emit_audit_action`.

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
`override_applied`/`base_allowed` are **derived** from `AuthorityDecision` (RC-2/RC-5).

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
txn-bound `conn` from `db.transaction()` (05 §3.4):

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
in-txn outbox that emits under the same key + `conn`.

---

## ⑤ THE RESTART-SAFETY PATTERN (skeleton — the scheduler completes it)

**Owners:** the durable store + fast-release handoff (05); the drain gate on all surfaces (02, step 0).
**Consumers / completer:** **strand-2's scheduler** (durable timer store + boot-reconcile).

### 5.1 The frozen skeleton

1. **Durable store.** State that must survive a merge=deploy restart lives in a DB table, not memory:
   `idempotency_keys` (05) for effect dedup; the **scheduler's own durable-timer table** (strand-2) for
   armed timers. Cooldown state is **in-memory** and resets on restart (durable cooldown store deferred,
   §8 · L-8/T2-6). Confirmations **survive nothing** (session-scoped; a restart drops the prompt and the
   actor re-invokes).
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
**Invariant strand-2 must honor:** durable timers are re-armed **only after `/ready` 200**.

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
  cannot open prod even by accident.** (Durable custody of the attest token is §8 · owner-gated.)

---

## ⑦ SUPPORTING FROZEN SEAMS (used by items ①–⑥)

### 7.1 The result-grammar leaf — `sb/spec/outcomes.py` (dependency-free)

Home of: the 5 outcome constants (re-exported), `ErrorClass`, `DenialReason`, `ReplyVisibility`,
`DeferMode`. **`DenialReason` lives here, not in `result.py`** (02 §3.6's inline copy is illustrative —
RC-6); K6 imports it. `DenialReason` = `{ALLOWED, DRAINING, AUTHORITY, DISABLED, VISIBILITY, CHANNEL,
USER_ERROR, COOLDOWN, AI_THROTTLE, NOT_FOUND, CONFIRM_DECLINED, DISPATCH_ERROR}`. `CHANNEL` covers both
`CHANNEL_NOT_ALLOWED` and `COMMANDS_DISABLED` (distinguished by `detail`); a distinct `COMMANDS_DISABLED`
member is optional-additive. **The `Lane` enum lives in `sb/spec/authority.py`** (04), imported by both
`outcomes` consumers and the resolver.

### 7.2 The namespace oracle — `validate` / `is_reserved` / `Collision` (03, K1 owns; 01 must change — RC-7)

| Seam | **Canonical (K1, 03)** | 01's stated shape (superseded) |
|---|---|---|
| oracle | `validate(snapshot) -> NamespaceReport` (collisions + cap_violations + format_errors + built `ReservationIndex`) | `validate_snapshot(snapshot) -> list[Collision]` |
| point query | `is_reserved(value, kind, *, surface, parent)` (value first; `parent=None` ⇒ top-level only) | `is_reserved(kind, value)` |
| collision | `Collision(kind, value, **scope**, claimant_a, claimant_b)`, key `(kind, value, scope)` | `Collision(kind, value, claimant_a, claimant_b)`, key `(kind, value)` |

The `scope = (kind, surface, parent_group)` key is **load-bearing**: without it `/ticket close` vs
`/thread close` and `!karma` vs `/karma` false-collide. **CI, `git merge-tree`, and boot all call the
same `validate`** → CI-green ⟺ boot-green by construction (kills the `#763` false-green class). A
trigger-set rejection surfaces as `outcome=BLOCKED` on the real `contracts.py:50` constant (§0).

### 7.3 The ephemerality resolver + lane default (02, T2-17) — uses the canonical `Lane` (RC-3)

`resolve_reply_visibility(*, outcome, reason, lane, declared, committed) -> ReplyVisibility` over all
five §2.7 outcomes, single place. `lane_default(lane) = EPHEMERAL if lane is Lane.CAPABILITY else PUBLIC`
(**RC-3:** `CAPABILITY` ≡ 02's `CONFIG_GOVERNANCE`; `TIER` ≡ 02's `DOMAIN`). A defer commits
`V = declared or lane_default(lane)` at the ACK boundary; post-defer renders honor the committed flag.

---

## ⑧ OPEN SEAM FORKS (genuinely undecided — strand-2 must NOT assume a resolution)

| # | Fork | Tier / gate | Built default (buildable now) | The open call | Touches |
|---|---|---|---|---|---|
| SF-a | **Panel-action grammar** (spec 02 §8-a): route-through-C-1 (panel actions/selectors carry the §3.0 `authority_ref`/`enabled_when`/`reply_visibility`/`cooldown`/`defer_mode` on their own specs) vs minimal `PanelActionSpec` + derived authority/cooldown | Tier-2, **owner-gated** | (A) per-spec fields (recommended — retires L-5 structurally) | which spec holds the fields; **resolver contract unchanged either way** | draft/workflow ports that author panel actions |
| SF-b | **Owner-override scope + transparency-sink wording** (02 §8-b / 04 §3.5): scope member-guild vs any-reachable; sink = observability-only vs a distinct operator-visible transparency log | Tier-2, **owner-gated** | member-guilds-only is **built structurally** (04 step 2, X-7); dual sink (bot-log + server-log, owner-DM fallback) | owner **confirms** the scope; names the sink copy / whether it is a distinct authoritative row | audit-row semantics (③), transparency emit |
| SF-c | **Dispatch-trace audit promotion** (02 §8-c): keep `command.dispatched` `observability_only=True` vs promote to a retained `AuditEventSpec` (one row per dispatch) | Tier-3, **owner-gated** | (A) observability-only for v1 | retention/volume posture — a retained row per dispatch | audit-row semantics (③), retention |
| SF-d | **`SB_PROD_ATTEST` durable custody** (05 §9): plain env `SecretSpec` vs sealed/managed secret vs short-lived OIDC claim | ops / CUT-1, **owner-gated** | presence-gated env `SecretSpec` (type CLOSED; the 4th rail is correct today) | the durable custody *source* | config/data-plane rail (⑥) |
| SF-e | **Durable cooldown store** (02 §9 · L-8/T2-6) | strand-2 durability (bounded) | in-memory (matches shipped; resets on restart) | the merge=deploy-surviving backing store the resolver reads off `CooldownSpec` | restart-safety (⑤) |
| SF-f | **Rung-4 orchestration failure policy** (02 §9) | Phase-4 band 6 (bounded) | stop-on-first-non-SUCCESS | a per-plan continue/compensate policy | NL orchestration (later) |

SF-a…SF-d are genuinely **owner-gated**; SF-e/SF-f are **bounded deferrals** with a designed default and
a designed seam already in place. None blocks strand-2 from building to the frozen shapes above.

---

## ⑨ RECONCILIATION LEDGER (where two specs disagreed → one canonical form)

| ID | Disagreement | Canonical form (winner) | Loser spec must change |
|---|---|---|---|
| **RC-1** | "outcome built on `StageResult`" / `WorkflowResult`+`contracts.py:48-52` framing | outcome vocab = `services/lifecycle/contracts.py:48-52` (real); dispatch return = `WorkflowResult\|None` (K7 superset of `LifecycleResult`); `StageResult` is the message-pipeline substrate, **not** a dispatch return; `disbot/core/contracts.py` **absent** | prompt phrasing (clarified here); all specs already agree on the corrected form |
| **RC-2** | `AuthorityDecision` shape: 02's `{allowed, lane, denial_copy, override_applied, base_allowed}` vs 04's 10-field | **04 (K6) owns it** — 04's shape wins; `denial_copy`→`denial_message`; `override_applied` is **derived** = `owner_override ∧ lane_would_deny`; `base_allowed` = `¬lane_would_deny` | **spec 02** imports 04's `AuthorityDecision`; derives its trace flags |
| **RC-3** | Lane enum: 02 `AuthorityLane{CONFIG_GOVERNANCE, DOMAIN}` vs 04 `Lane{CAPABILITY, TIER}` | **04's `Lane`** (`sb/spec/authority.py`) — same two lanes; `CAPABILITY`≡config-governance⇒EPHEMERAL, `TIER`≡domain⇒PUBLIC | **spec 02** uses `Lane` in `lane_default`/`resolve_reply_visibility` |
| **RC-4** | Owner-override threading into channel-access | resolver **must** pass `decision.owner_override` into step-2 `resolve_channel_access` and the subsystem-visibility check (compute once at step 1) | **spec 02** (step 2 currently independent → L-12 re-opens) |
| **RC-5** | Transparency-audit firing condition | 04's `owner_override ∧ (lane_would_deny ∨ channel.would_deny_without_override)` (includes the channel leg) | **spec 02** extends its `override_applied`-only trigger with the channel decision at step 4 |
| **RC-6** | `DenialReason` home | `sb/spec/outcomes.py` (leaf); K6 imports it; `CHANNEL`+`detail` covers `COMMANDS_DISABLED` | 02 §3.6 inline copy is illustrative only |
| **RC-7** | Namespace seam names/keys (01 vs 03) | **03 (K1) wins** — `validate→NamespaceReport`, `is_reserved(value, kind,…)`, `Collision(+scope)` key `(kind,value,scope)` | **spec 01** (P3 wires to K1; `Collision` adds `scope`) |
| **RC-8** | `DBUnavailable` → resolver classification | zero-edit: `DBUnavailable(ConnectionError)` routes through 02's **existing** `ConnectionError` transient row → transient/retryable/`DISCORD_FAILED` | none (optional annotation on 02's row) |
| **RC-9** | Drain-gate cite | `lifecycle.is_shutting_down()` / `can_accept_commands()` (K5) — `message_pipeline.py:277` only *invokes* it. Two predicates coexist: resolver admission uses `can_accept_commands()` ({STARTING,RUNNING}); `/ready` uses **RUNNING-only** (05 §3.8, STARTING⇒503) — distinct callers, both valid | 02's `message_pipeline.is_shutting_down()` mis-cite corrected |
| **RC-10** | Config accessor: `.get(spec)`+`Secrets` vs one attribute per field | one typed frozen attribute per field, verbatim env name; redact is a field property | resolved in-file (05) |
| **RC-11** | Two `Surface` enums | **Do NOT unify** — namespace `Surface{PREFIX,SLASH}` (03, reservation scope) vs interaction `Surface{SLASH,PREFIX,COMPONENT,MODAL,NL_INTENT,NL_ORCHESTRATION}` (02, dispatch) are different layers/purposes | naming caution only |

---

## ⑩ FROZEN-LEAF INVENTORY (where each shared type lives)

| Leaf module | Owns | Landed |
|---|---|---|
| `sb/spec/outcomes.py` | 5 outcome constants (re-export), `ErrorClass`, `DenialReason`, `ReplyVisibility`, `DeferMode` | K6/K7 |
| `sb/spec/authority.py` | `Lane`, `TIERS`, `ADMIN_FLOOR_TIER`, `classify_authority_ref`, `validate_authority_ref`, `is_tier_sufficient` | K6 |
| `sb/spec/config.py` | `ConfigSpec`, `SecretSpec`, `ConfigPosture`, `ConfigType`, `IntentSpec`, `DataPlane`, `CONFIG_FIELDS`, `INTENT_CONTRACT` | K0/K2 |
| `sb/spec/observability.py` | `MetricSpec`, `MetricKind`, `LabelSpec` | K0 |
| `sb/spec/refs.py` | `HandlerRef`/`PanelRef`/`WorkflowRef`/`PredicateRef`/… + `@handler` + ref table | K2 |
| `sb/namespace/{kinds,records,validate,index}.py` | `NamespaceKind`, scope key, `validate`, `ReservationIndex`, `is_reserved`, `check_trigger` | K1 |
| `sb/kernel/db/idempotency.py` | `IdempotencyKey`, `PriorOutcome`, `once`/`record_outcome`/`read_outcome` | K3 |
| `kernel/interaction/{request,resolve,result,errors,predicates}.py` | `ResolveRequest`, `resolve`, `Result`, `from_exception`, `SurfaceResponder` port | K8 |
| `kernel/authority/{owner,decision,resolve,channel_access,transparency}.py` | `AuthorityDecision`, `resolve_authority`, `owner_override_holds`, `resolve_channel_access`, transparency contract | K6 |

---

*Synthesized 2026-07-04 from `strand-1-kernel-spine/01…05`, verified against shipped source
(`services/lifecycle/contracts.py`, `core/runtime/message_pipeline.py`, `services/audit_events.py`,
`governance/capability.py`, `config.py`, `bot1.py`). Marked NOT SOURCE OF TRUTH for runtime — a design
contract for strand 2 and the cross-cutting concerns to build ON.*

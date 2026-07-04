# Strand 1 · Kernel Spine — ② The C-1 Resolver + ③ The Dispatch Error/Failure Envelope

> **Status:** `reference` — Phase-B foundational design, buildable depth. DOCS-ONLY (changes no
> `disbot/` code). One combined seam: the single `resolve(ResolveRequest) -> Result` chokepoint
> **and** the `from_exception` error envelope that lives inside it. Design INTO the frozen design
> spec §2.2 / §2.4 / §2.6 / §2.7 / §2.8 / §2.9 / §9.1
> ([`rebuild-design-spec-2026-07-02.md`](../../../../../planning/rebuild-design-spec-2026-07-02.md))
> and the FJ-5 ledger
> ([`final-judgment-fable5-2026-07-03.md`](../../final-judgment-fable5-2026-07-03.md) §2/§6).
> **Design against, never reverse:** router Q-0237(a–g) — esp. **(d) ONE `authority_ref`** (Gate-0
> maps the single ref to *either* a governance capability *or* a domain audience tier; that internal
> mapping is the **lane**, returned in the `AuthorityDecision` — §3.0).
> **Source-wins grounding (Q-0120):** there is **no shipped `WorkflowResult` class** — it is the
> §2.7 **kernel** type (a strict superset of the shipped `LifecycleResult`,
> `services/lifecycle/contracts.py:77`), landed in K7. The shipped outcome constants
> (`SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED`) live at
> `services/lifecycle/contracts.py:48–52`; the shipped **message-pipeline** stage contract is
> `StageResult` (`core/runtime/message_pipeline.py:181`) — the passive on-message substrate, **not**
> a `resolve()` dispatch return (§3.6). Spot-verify both before building.
> **Cross-strand seam corrections absorbed (PIN-3 / PIN-4).** Two additive cross-spec fields land in
> this spec's leaves: (PIN-3) `ActorRef` carries `actor_type: str = "user"` (§3.1) — K7 maps
> `ctx.actor.actor_type → AuthorityRequest.actor_type`, and the reserved non-user values
> `"system"` (09's `SYSTEM_ACTOR`) / `"backfill"` (11's `SWEEP_ACTOR`) hit `resolve_authority`'s
> step-1 scripted-bypass (§②.3); (PIN-4) the interaction `Surface` enum gains ONE background member
> `MAINTENANCE` (§3.1) — the single token both 09 scheduler-fires **and** 11 invariant sweep-repairs
> classify under, and `from_exception`'s `target` widens to `TargetRef | None` so a headless fire
> passes `target=None` (§3.3). Both are additive: they change no existing field and no classifier core.
> **Buildable-depth test:** a fresh agent builds this from this spec + the frozen upstream contracts
> making zero further design decisions; every unclosable fork is in §8 (owner-gated ones as
> options+recommendation, never decided). **The four resolver-facing grammar fields this design reads
> off `target.spec` are pinned to exact type/default/role in §3.0 and handed to §2.2/§2.4/§2.6 to
> absorb — the resolver invents no field.**

---

## 1. Summary + the exact undesigned gap

**What already exists (anti-pad — not restated).** The design spec §2.6 already fixes the
*per-action* callback choreography (`resolve authority → defer → confirm → invoke → Result → render`,
lines 763–766) and §1.2 already states the interaction-lifecycle invariant ("no code path from a
Discord component to a handler that skips the check"). §2.7 already defines the `WorkflowResult`
grammar (the **kernel** type built in K7 — a strict superset of the shipped `LifecycleResult`, not a
shipped class). **This design does not re-specify those.** It specifies the one thing they do not:
the **surface-agnostic chokepoint** that makes that per-action skeleton the *only* way in, for
*every* rung and *every* panel/component action, plus the error envelope §2.7 names but never shapes.

**The genuinely-undesigned gap this closes:**

| Gap (verified) | Shipped reality | This design |
|---|---|---|
| No single seam | `resolve_command_access` is channel-only (`command_access.py:256`); slash admission `_slash_access_check` (`bootstrap_access_cog.py:185`) skips subsystem-visibility; panel/component actions run a **second** path (`interaction_router.dispatch:104-166`) with visibility **but no cooldown**; AI rungs execute nothing (`next_command` is a string) | `resolve(ResolveRequest) -> Result` — one chokepoint; five rung adapters + the panel/component/selector/modal adapters all build a `ResolveRequest` and funnel it; a net-new AI rung-3/4 adapter turns the `next_command` string into `(command, args)` |
| No error envelope | **zero** `on_app_command_error`/`tree.error` over 31 slash cmds; 4 divergent postures (prefix `on_command_error` `bot1.py:483`; component generic-ephemeral `interaction_router.py:221-234`; slash **none**; wizard-only `recovery_context_from_exception` `recovery.py:457`) | `from_exception(exc) -> ErrorEnvelope` → `{user_error, denied, transient, bug}` + `retryable` + `user_message` + `reason`, mapped INTO the frozen §2.7 outcome vocab; `tree.error`/`on_app_command_error` registered at the composition root |
| Slash skips visibility (drift) | slash → `resolve_command_access` (channel only); components → `get_visible_subsystems` (visibility). Opposite gaps on the two paths | one `validate` step checks per-guild enablement/visibility for **every** surface (T2-9 `enabled_when`, §3.0), killing the drift structurally |

**Fixed pipeline (the spine everyone consumes):**
`admission → authority → validate → cooldown → [ACK/defer boundary] → audit → dispatch → render`.

---

## 2. Files/modules it becomes

New `sb/` paths (layer table §1.1):

| Path | Owns |
|---|---|
| `sb/spec/outcomes.py` | Frozen leaf: the §2.7 outcome constants re-exported (`SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED`), plus the `ErrorClass`, `DenialReason`, `ReplyVisibility`, and `AuthorityLane` enums, and the `DeferMode` enum. Dependency-free so `kernel/workflow`, `kernel/interaction`, and `kernel/authority` all import them. |
| `sb/kernel/interaction/request.py` | `ResolveRequest`, `TargetRef`, `ActorRef`, `NLProvenance`, `Surface`, the `SurfaceResponder` **port**. |
| `sb/kernel/interaction/resolve.py` | `resolve(ResolveRequest) -> Result` — the chokepoint + the fixed order + the dispatch-kind dispatch table (§3.2 step 5). |
| `sb/kernel/interaction/result.py` | `Result` (dispatch result), the `WorkflowResult ↔ §2.7` outcome pass-through (§3.6), the ephemerality resolver `resolve_reply_visibility` (T2-17). |
| `sb/kernel/interaction/predicates.py` | `evaluate(ref: PredicateRef, ctx: PanelContext) -> bool` + the **PredicateRef grammar** (§3.0). Shared by the resolver's `enabled_when`/`visible_when` gate (step 2a) and the panel engine's render-time `visible_when`. |
| `sb/kernel/interaction/errors.py` | `from_exception`, the exception→class→reason table, `user_message` derivation, the wizard section-copy fold-in. |
| `sb/kernel/interaction/adapters/{slash,prefix,fuzzy,component,modal,nl}.py` | Per-surface adapters that build a `ResolveRequest`; `nl.py` holds the **net-new** rung-3/4 adapters. |
| `sb/adapters/discord/responders.py` | `InteractionResponder` / `MessageResponder` — concrete `SurfaceResponder` implementations (the only modules that touch `discord.Interaction`/`Message`). |
| `sb/app/error_handlers.py` | Composition-root registration of `tree.error` + `on_app_command_error` + the prefix `on_command_error`, each a 3-line shim into `from_exception`. |

Shipped paths it **retires** (fold-in, not delete-in-place — old repo stays frozen):

| Shipped path | Fate |
|---|---|
| `command_access.py` `resolve_command_access` (channel-only) | folds into the resolver `validate` step as the **channel-access lane** (one of several enablement checks) |
| `bootstrap_access_cog.py` `_slash_access_check` + `_channel_guard` | replaced by the single `resolve()` funnel; the two `interaction_check`/`bot_check` seams collapse to one |
| `interaction_router.dispatch:104-166` (the second resolver) | panel/component/selector adapters build a `ResolveRequest`; the visibility gate + the missing cooldown both come from the unified pipeline |
| `bot1.py:483 on_command_error` + the **absent** `on_app_command_error` | both become `from_exception`-backed shims |
| `recovery.py:457 recovery_context_from_exception` | **retired**; its `permission_hints` map (Forbidden/HTTPException/TimeoutError) is exactly the denied/transient rows of the `from_exception` table; wizard becomes surface = `setup`, its section-keyed copy a surface-specific *render* of the same envelope |

---

## 3. The complete public contract

Role tags `[S]`/`[A]`/`[O]` appear where a field is a manifest **spec** field the resolver reads;
runtime-request fields carry no S/A/O tag (they are not authored, not simulated).

### 3.0 Grammar amendments this design pins (absorbed by §2.2 / §2.4 / §2.6)

The resolver reads four fields off `target.spec` that the frozen grammar does **not** yet carry.
This design **pins their exact type, default, and role** and hands them to the routable specs
(`CommandSpec` §2.2, `SelectorSpec` §2.4, `PanelActionSpec` §2.6) to absorb in their next revision.
A builder needs no further decision — the shapes are fixed here. All four are `[S]` (hand-authored,
sim-frozen).

| Field | On specs | Type / default | What the resolver does with it | Supersedes / relates to |
|---|---|---|---|---|
| `authority_ref` | `CommandSpec`, `PanelActionSpec`, `SelectorSpec` | `str` (required; `""` ⇒ ADMINISTRATOR floor) | Step 1 hands it to the authority engine (K6), which resolves it to an `AuthorityDecision` (below). **Replaces** the frozen two-lane pair `capability_required` + `audience_tier` on all three specs. | Q-0237(d), L-13/T1-4 — ONE ref; Gate-0 owns the internal capability-or-tier mapping |
| `enabled_when` | `CommandSpec`, `PanelActionSpec`, `SelectorSpec` | `PredicateRef` (default `""` ⇒ constant-true) | Step 2a evaluates it as the **per-guild dispatch-admission gate** for *every* surface. Deny ⇒ reason `DISABLED`. | T2-9 (retired here with a real field, not by location) |
| `reply_visibility` | `CommandSpec`, `PanelActionSpec`, `SelectorSpec` | `ReplyVisibility \| None` (default `None` ⇒ lane default) | The **declared success-visibility override** read by the ephemerality resolver (§3.4). `None` ⇒ derive from the authority lane. | T2-17; distinct from the frozen `PanelActionSpec.result_render` (a render *mode*: toast/refresh_panel/result_card/none), which is orthogonal |
| `defer_mode` | `CommandSpec`, `SelectorSpec` | `DeferMode \| None` (default `None` ⇒ surface-derived, table in §3.2 ACK row) | The ACK boundary reads it to pick defer behavior. **`PanelActionSpec.defer_mode` already exists frozen** (§2.6 line 752, non-optional `{auto, modal, none}`); this adds the *optional* variant to the two specs that lack it. | new — closes the "CommandSpec has no defer_mode" gap |

**`PredicateRef` grammar (pinned).** A `PredicateRef` is a string in one of two forms, resolved by
`predicates.evaluate(ref, ctx)` against read-only settings/binding/guild-state accessors (through the
db + settings ports; no writes):

- **Namespaced predicate** `"<kind>:<key>[=<value>]"`, `kind ∈ {setting, binding, capability, flag}`
  (e.g. the frozen example `setting:logging.enabled`; `binding:log_channel` ⇒ true iff bound;
  `flag:beta` ⇒ a guild feature flag). A bare `""` is the constant-true predicate.
- **Registered ref** — a namespace-reserved name resolving to a pure `(PanelContext) -> bool`
  function, for compound conditions the string form cannot express. Unregistered ⇒ compile error.

`enabled_when` vs the frozen `visible_when` (both `PredicateRef`): **`visible_when` is a component
render gate** — the panel engine evaluates it at panel-*build* time to decide whether a component
appears. **`enabled_when` is a dispatch-admission gate** — the resolver evaluates it in step 2a for
every surface at *dispatch* time. They share the grammar and the evaluator. For a
`component`/`selector` surface the resolver **also** re-evaluates the target's `visible_when` at
dispatch (a defense-in-depth stale/replayed-custom_id guard: a component whose render gate is now
false must not fire); **both** predicates must pass or the dispatch denies `DISABLED`.

**`AuthorityLane` + `AuthorityDecision` (consumed from K6; shape pinned so §3.4 is buildable).** The
authority engine resolves `authority_ref` and returns:

```python
class AuthorityLane(enum.Enum):
    CONFIG_GOVERNANCE = "config_governance"   # ref mapped to a governance capability
    DOMAIN = "domain"                         # ref mapped to a domain audience tier

@dataclass(frozen=True)
class AuthorityDecision:                # OWNED by kernel/authority (K6); the resolver consumes it
    allowed: bool
    lane: AuthorityLane                 # the Gate-0 capability-or-tier mapping IS the lane (Q-0237d)
    denial_copy: str | None            # the authority-engine denial message, when denied
    override_applied: bool             # the owner-override authorized a dispatch base authority would deny
    base_allowed: bool                 # what the decision would have been WITHOUT the override
```

The lane is not a spec field and is not derived from `(outcome, reason, declared)` — it is a property
of the **resolved** decision, produced by the same Gate-0 mapping Q-0237(d) mandates. This is what
makes §3.4's lane-driven default computable after the two-lane collapse.

### 3.1 Surface-agnostic request

```python
class Surface(enum.Enum):
    SLASH = "slash"; PREFIX = "prefix"
    COMPONENT = "component"; MODAL = "modal"
    NL_INTENT = "nl_intent"; NL_ORCHESTRATION = "nl_orchestration"
    MAINTENANCE = "maintenance"        # PIN-4: the ONE background/headless surface — covers 09
    #   scheduler fires AND 11 invariant sweep-repairs (both classify their fire/repair/compensation
    #   exceptions through from_exception with surface=MAINTENANCE, target=None). NOT a per-sibling
    #   "scheduler"/"maintenance" split (that string-drift is exactly what the shared vocab kills).

class DeferMode(enum.Enum):             # frozen [S] on PanelActionSpec (§2.6); optional [S] on
    AUTO = "auto"; MODAL = "modal"; NONE = "none"   # CommandSpec/SelectorSpec via §3.0

@dataclass(frozen=True)
class ActorRef:                        # normalized by the adapter (generalizes CommandAccessContext)
    user_id: int | None
    is_guild_operator: bool            # owner / administrator / manage_guild (shipped _is_guild_operator)
    is_bot_owner: bool                 # platform-owner override candidate (config.is_platform_owner)
    is_dm: bool
    actor_type: str = "user"           # PIN-3: "user" | "system" | "backfill" | "setup_delegate"
    #   (vocab §⑩ / AuthorityRequest §②.3). Default "user" for EVERY interaction surface. K7 maps
    #   ctx.actor.actor_type → AuthorityRequest.actor_type when it builds the request, so the reserved
    #   non-user values — SYSTEM_ACTOR="system" (09 scheduler fires), SWEEP_ACTOR="backfill" (11
    #   invariant sweep-repairs) — hit resolve_authority's step-1 scripted-bypass (allowed=True, not
    #   authority-gated). Last field with a default so the four non-default fields keep their order.

@dataclass(frozen=True)
class TargetRef:
    key: str                           # command name | "<panel_id>.<action_id>" (namespace-reserved, K1)
    spec: "CommandSpec | PanelActionSpec | SelectorSpec"
    # every spec carries authority_ref, enabled_when, reply_visibility, defer_mode(*), cooldown
    #   (§3.0); the ROUTABLE ref differs by type — CommandSpec.route, PanelActionSpec.handler,
    #   SelectorSpec.on_select — read generically at step 5 (§3.6 dispatch-kind table).
    #   (*) defer_mode is frozen on PanelActionSpec, §3.0-added on the other two.

@dataclass(frozen=True)
class NLProvenance:                    # rung-3/4 only — feeds audit + did-you-mean privacy (C2 batch)
    nl_text: str
    intent_key: str
    confidence: float
    orchestration_id: str | None       # links the steps of one rung-4 plan

@dataclass(frozen=True)
class ResolveRequest:
    surface: Surface
    target: TargetRef
    actor: ActorRef
    guild_id: int | None
    channel_id: int | None
    args: Mapping[str, object]         # parsed/extracted, surface-normalized (modal fields on MODAL)
    responder: "SurfaceResponder"      # the ack/reply PORT (never a raw discord object)
    origin: object                     # opaque surface-native handle; kernel never inspects it
    provenance: NLProvenance | None = None
    confirmed: bool = False            # True on the re-entrant confirm dispatch (§3.2 step 5)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

**`SurfaceResponder` port** (defined in `kernel/interaction`, implemented in `adapters/discord`; the
kernel sees only the Protocol — layer rule "kernel imports adapter ports it defines"):

```python
@runtime_checkable
class SurfaceResponder(Protocol):
    surface: Surface
    def is_acked(self) -> bool: ...
    def committed_visibility(self) -> ReplyVisibility | None: ...  # set once a defer froze it (§3.4)
    async def ack(self, *, ephemeral: bool) -> None: ...        # interaction: response.defer(); message: no-op/typing
    async def deny(self, message: str, *, ephemeral: bool) -> None: ...  # pre-ack direct denial (the denial IS the ack)
    async def open_modal(self, modal_ref: "HandlerRef") -> None: ...     # defer_mode=MODAL
    async def open_confirm(self, prompt: "ConfirmPrompt") -> None: ...   # ConfirmationSpec round-trip (§3.2 step 5)
    async def render(self, result: "Result") -> None: ...      # render dispatch Result to the surface
```

### 3.2 The chokepoint + fixed order

```python
async def resolve(req: ResolveRequest) -> Result: ...
```

| # | Step | What runs | Deny → |
|---|---|---|---|
| 0 | **admission** | `lifecycle.can_accept_commands()` (K5). Draining ⇒ every surface stops, **silent** (no ack) — generalizes the shipped `lifecycle.is_shutting_down()` gate (*invoked at* `message_pipeline.py:277`) to all surfaces | `BLOCKED`, reason `DRAINING`, `user_message=None` |
| 1 | **authority** | resolve `target.spec.authority_ref` (ONE ref, Q-0237d) via the authority engine (K6) → `AuthorityDecision{allowed, lane, denial_copy, override_applied, base_allowed}`; owner-override applied **once here** (scope owner-gated §8-b). The resolver builds the `AuthorityRequest` carrying `req.actor.actor_type` (PIN-3) — always `"user"` on an interaction surface, so no scripted-bypass fires here; the reserved `"system"`/`"backfill"` bypass values reach `resolve_authority` **only** via the headless K7/09/11 path. The returned **`lane` feeds the ACK-boundary defer visibility and §3.4** | `BLOCKED`, reason `AUTHORITY`, `error_class=denied`, `user_message=decision.denial_copy` |
| 2 | **validate** | (a) per-guild **enablement/visibility** — evaluate `target.spec.enabled_when` (+ subsystem-visibility + the folded-in channel-access lane; for component/selector surfaces **also** re-evaluate `visible_when`) → deny reason `DISABLED`/`VISIBILITY`/`CHANNEL`; (b) **argument** validation against the spec's ParamSpecs → deny reason `USER_ERROR`, `error_class=user_error` | `BLOCKED` (reason per above) |
| — | **ACK boundary** | steps 0–2 are cached/in-memory (well < Discord's 3 s). A denial in 0–2 responds **directly** via `responder.deny(message, ephemeral=True)` (the denial is its own ack; always ephemeral — pre-ack, nothing frozen). If all passed, resolve `defer_mode` (`CommandSpec`/`SelectorSpec`: `None`⇒ **surface-derived default** — SLASH+`route=PanelRef`⇒`NONE` (the panel render is the ack), SLASH+`route=HandlerRef`⇒`AUTO`, PREFIX/message⇒`NONE`, COMPONENT/SELECT⇒`AUTO`, MODAL-submit⇒`NONE`; `PanelActionSpec`: its frozen `defer_mode`). `AUTO` ⇒ `responder.ack(ephemeral = V==EPHEMERAL)` where **`V = target.spec.reply_visibility or lane_default(decision.lane)`** — this commits (freezes) the visibility for all post-defer renders (§3.4). `MODAL` ⇒ `open_modal` (the modal is the ack); `NONE` ⇒ the handler's first send / panel render acks. Message surfaces: `ack` is a no-op. An `eager_defer` surface flag (bounded escape hatch, defers before step 0 at `V` for a known-slow gate) is **not** the default | — |
| 3 | **cooldown** | charge `target.spec.cooldown: CooldownSpec` (CONSUMED); for NL rungs also charge the **distinct AI-throttle axis** (CONSUMED). Over-limit ⇒ deny | `BLOCKED`, reason `COOLDOWN`/`AI_THROTTLE`, `retryable=True`, retry-after in `user_message` |
| 4 | **audit** | emit the `command.dispatched` trace (skeleton, §3.5), carrying `override_applied`/`base_allowed` from step 1. Distinct from the per-mutation `emit_audit_action` fired *inside* the workflow engine (K7) — the resolver never bypasses that seam | — |
| 5 | **dispatch** | **confirm gate:** if `target.spec.confirm: ConfirmationSpec` is present **and** `not req.confirmed` → render the confirm surface, return a *confirm-pending* `Result` (no mutation ran); the confirm control re-enters `resolve()` with `confirmed=True` (details below). Else **dispatch by routable-ref kind** (§3.6 table): `PanelRef`⇒`OPEN_PANEL` (kernel panel engine), `HandlerRef`⇒`INVOKE_HANDLER` (domain), `WorkflowRef`⇒`INVOKE_WORKFLOW` (kernel workflow engine). Handlers/workflows return `WorkflowResult`; `OPEN_PANEL` returns `None` | exceptions → `from_exception` (§3.3) |
| 6 | **render** | build `Result` (map `WorkflowResult` ↔ §2.7 outcome, §3.6; `OPEN_PANEL`⇒`SUCCESS`); resolve reply-visibility (§3.4, honoring any committed defer visibility); `responder.render(result)`; back-fill the dispatch-trace outcome | — |

**ConfirmationSpec round-trip (closed — no blocking mid-dispatch await).** A confirm is a *second
dispatch*, never a 60-second suspended coroutine (which would neither scale nor survive a
merge=deploy restart). Mechanism:

1. First dispatch, target carries `confirm`, `req.confirmed=False`: the resolver **does not run the
   handler**. It calls `responder.open_confirm(prompt)` — a kernel-owned confirm surface (a
   button for `challenge=button`; a modal for `typed_phrase`/`typed_hash`, §2.7). The confirm
   control's `custom_id` encodes `(<panel_id>.<action_id>, confirm_token, request_id)` — the
   `request_id` doubling as the idempotency key (§6). Returns `Result(outcome=SUCCESS,
   reason=ALLOWED, reply_visibility=EPHEMERAL, workflow=None)` with `audit_emitted` noting
   *confirm-issued*. No mutation, no cooldown consequence beyond the step-3 charge already taken.
2. Confirm click/submit: the **component/modal adapter** builds a fresh `ResolveRequest` for the
   *same* target with `confirmed=True` (parsed from the custom_id). `resolve()` re-runs 0–4 — so
   `re_check_actor` (§2.7, frozen `Literal[True]`) is satisfied *structurally*, authority is
   re-resolved — then step 5 sees `confirmed=True` and dispatches the handler.
3. **Decline / timeout:** the confirm surface is a session-scoped kernel view with
   `timeout_s = ConfirmationSpec.timeout_s` (default 60). A cancel click or the timeout fires the
   kernel confirm-terminal handler → `Result(outcome=DECLINED, reason=CONFIRM_DECLINED,
   error_class=NONE, reply_visibility=EPHEMERAL, user_message=<decline/timeout copy>)`, rendered by
   disabling the confirm controls. `DECLINED`/`CONFIRM_DECLINED` are exactly the §2.7 vocab and the
   §3.6 `DenialReason` this path was reserved for.

**Cooldown refund rule (closed):** the token charged at step 3 is **refunded** iff the dispatch
`error_class ∈ {transient, bug}` (not the actor's fault, no real use); kept on `SUCCESS`/`PARTIAL`,
on `user_error` (a real attempt), and on a `DECLINED` confirm (the actor chose to abandon — a real
use of the slot). Mirrors discord.py's `reset_cooldown`-on-error convention.

### 3.3 The error envelope — `from_exception`

```python
class ErrorClass(enum.Enum):
    NONE = "none"; USER_ERROR = "user_error"; DENIED = "denied"
    TRANSIENT = "transient"; BUG = "bug"

@dataclass(frozen=True)
class ErrorEnvelope:
    error_class: ErrorClass
    reason: DenialReason       # the §3.6 machine reason (added — no longer builder-invented)
    retryable: bool
    user_message: str          # [S] copy — the single canonical message per class (surface-enriched)
    log_level: int             # logging.WARNING for user_error/denied/transient; ERROR (+traceback) for bug
    outcome: str               # the §2.7 constant this class maps to (§3.6)

def from_exception(exc: BaseException, *, surface: Surface,
                   target: TargetRef | None, section_label: str | None = None) -> ErrorEnvelope: ...
```

**`surface`/`target` only enrich `user_message` — the classifier core is surface/target-independent
(PIN-4).** The core mapping `exc → error_class → reason → outcome → retryable` reads **only the
exception type** (the table below); `surface` and `target` feed *nothing but* the `user_message`
derivation (the wizard section fold-in, the `!help <cmd>` argument hint, the missing-permission name).
Because of that separation, a **headless background fire has no interaction target and discards the
copy**: the scheduler (09) and the invariant sweep (11) call
`from_exception(exc, surface=Surface.MAINTENANCE, target=None)` to classify every
fire/repair/compensation exception through the *same* function, taking `error_class`/`reason`/`outcome`
for their audit trail and dropping the (target-less) `user_message`. `target is None` is therefore
valid input: `user_message` derivation skips the target-keyed hints and returns the class's canonical
copy verbatim. `MAINTENANCE` is the ONE background `Surface` both siblings share (§3.1) — never a
`"scheduler"`-vs-`"maintenance"` per-sibling split.

**Exception → class → reason table (the buildable mapping):**

| Exception (representative) | `error_class` | `reason` (`DenialReason`) | `retryable` | §2.7 `outcome` | `user_message` derivation |
|---|---|---|---|---|---|
| `MissingRequiredArgument`, `BadArgument`, `app_commands.TransformerError`, spec `ValidatorError` | `user_error` | `USER_ERROR` | True (after fix) | `BLOCKED` | "Missing/invalid argument: `<name>`. `!help <cmd>` for usage." |
| `PermissionError`, `commands.CheckFailure`, `app_commands.CheckFailure` | `denied` | `AUTHORITY` | False | `BLOCKED` | authority-engine denial copy, else "You don't have permission to use this." |
| `discord.Forbidden` (bot lacks a Discord permission) | `denied` | `DISPATCH_ERROR` | False | `BLOCKED` | "I'm missing a Discord permission for this: `<perm>`." (matches shipped `BotMissingPermissions` copy) — reason is `DISPATCH_ERROR`, not `AUTHORITY`: it is *our* operational gap, not the actor's authority |
| `discord.HTTPException` (non-403), `discord.RateLimited`, `asyncio.TimeoutError`, `ConnectionError`, asyncpg pool-timeout | `transient` | `DISPATCH_ERROR` | True | `DISCORD_FAILED` | "Discord/the service is busy — try again shortly." |
| **anything else (unhandled)** | `bug` | `DISPATCH_ERROR` | False | `BLOCKED` | "Something went wrong on our end — it's been logged." + ERROR log w/ traceback + operator finding |

The **`reason` column** closes the "`Result.reason` unmapped for dispatch exceptions" gap: every
`from_exception` result carries a concrete `DenialReason`; the finer "whose fault" nuance stays in
`error_class`. `CommandOnCooldown` is **not** a `from_exception` input — cooldown is caught at step 3,
before dispatch, so it never surfaces as a raised exception.

**Wizard fold-in (retires `recovery_context_from_exception`).** For `surface ∈ {setup}` the
`section_label` is passed; `from_exception` enriches `user_message` with the section label + the
recommended Retry/Skip action — i.e. the recovery copy becomes a *render* of the same envelope, not
a parallel function. The shipped `permission_hints` map is the `denied`/`transient` rows above.

### 3.4 Ephemerality resolver (retires T2-17)

```python
def lane_default(lane: AuthorityLane) -> ReplyVisibility:
    return ReplyVisibility.EPHEMERAL if lane is AuthorityLane.CONFIG_GOVERNANCE else ReplyVisibility.PUBLIC

def resolve_reply_visibility(*, outcome: str, reason: "DenialReason",
                             lane: AuthorityLane, declared: ReplyVisibility | None,
                             committed: ReplyVisibility | None) -> ReplyVisibility:
    if committed is not None:            # a defer already froze the flag (§3.2 ACK) — Discord binds it
        return committed
    if reason is DenialReason.DRAINING:
        return ReplyVisibility.SILENT
    if reason in _PRE_DISPATCH_DENIALS:  # authority/disabled/visibility/channel/user_error/cooldown/ai_throttle/not_found
        return ReplyVisibility.EPHEMERAL
    if outcome in (SUCCESS, PARTIAL):
        return declared or lane_default(lane)
    return ReplyVisibility.EPHEMERAL     # DISCORD_FAILED / BLOCKED(bug/dispatch) / DECLINED(confirm), uncommitted
```

```python
class ReplyVisibility(enum.Enum):
    EPHEMERAL = "ephemeral"; PUBLIC = "public"; SILENT = "silent"
```

**Complete over all five §2.7 outcomes, one place** (not the ~1,079 hand-set `ephemeral=` call sites,
L-15/L-24):

- **Pre-ack denials** (steps 0–2, and the cooldown deny) respond via `responder.deny(...,
  ephemeral=True)` before any defer — always `EPHEMERAL` (`DRAINING` ⇒ `SILENT`). Nothing is frozen,
  so the rule is honored exactly.
- **The ACK-time-vs-outcome-time tension (closed).** Discord commits the ephemeral flag at
  `defer()`; after an `AUTO` defer it cannot change. So when a defer happens the resolver commits
  **`V = declared or lane_default(lane)`** — the target's *success* visibility, computed from the
  step-1 lane (available at the ACK boundary because authority already resolved). Every post-defer
  render — `SUCCESS`, `PARTIAL`, a step-5 `BLOCKED`(bug), `DISCORD_FAILED`, or a `DECLINED` confirm —
  renders at that committed `V` (the responder returns it from `committed_visibility()`, and
  `resolve_reply_visibility` short-circuits on it). This is deliberate: past the ACK boundary the
  actor has cleared admission/authority/validate, so a post-defer failure is a genuine operational
  result worth showing where the success would have shown. The "any denial ⇒ EPHEMERAL" intent
  therefore governs the **pre-dispatch** denials (which are the denials that were never deferred);
  post-defer failures follow the frozen flag. For a `NONE`-defer target (prefix, panel-open, message)
  nothing is committed, so `DISCORD_FAILED`/bug/decline fall to the final `EPHEMERAL` branch and
  `SUCCESS`/`PARTIAL` use `declared or lane_default`.

### 3.5 Audit-fires-at-dispatch (skeleton)

The resolver **owns the dispatch-trace seam**: at step 4 it emits `command.dispatched`
(`EventSpec`, `observability_only=True` by default, `owner_subsystem="kernel"` — the reserved
observability owner; see the carve-out below) with payload:

```
{request_id, surface, command_key, actor_id, guild_id, authority_ref,
 lane, override_applied, base_allowed,        # step-1 AuthorityDecision — the transparency signal
 orchestration_id?, outcome (back-filled), reason}
```

It is **distinct from and additive to** the per-mutation `emit_audit_action` fired inside the
workflow engine (K7) — one command ⇒ one dispatch-trace + zero-or-more mutation-audit rows.

**Transparency audit (L-12/T2-10), now conditionally firable.** The payload carries
`override_applied` (True when the owner-override authorized a dispatch that `base_allowed=False`
would otherwise have denied) — the exact condition Q-0227/T2-10 requires. When `override_applied` is
True the trace **additionally** routes to the transparency-audit sink; the *sink wording* and
whether the sink is a distinct authoritative row are **owner-gated §8-b/§8-c**, but the firing
condition and the flag are designed now, so the generic trace no longer fails to distinguish
override-authorized dispatches.

**Kernel-owned EventSpec carve-out (closes the §2.8 `owner_subsystem` nit).** `command.dispatched` is
kernel-emitted, not subsystem-owned. It takes the reserved `owner_subsystem="kernel"` — an
observability owner in the reserved `system.*`/`_internal.*` namespace class (§2.1 reserved
prefixes). This is a named carve-out to the §2.8 rule that every `EventSpec` names a subsystem
owner: kernel observability events use the reserved `kernel` owner; the catalogue generator and the
subscriber-drift check both accept it as an `observability_only=True` carrier.

### 3.6 The dispatch `Result`

```python
@dataclass(frozen=True)
class Result:
    outcome: str                       # §2.7 frozen vocab ONLY — no 6th constant (harness reads new-as-old)
    reason: DenialReason               # ALLOWED on success; fine-grained machine reason otherwise
    error_class: ErrorClass            # NONE on success
    retryable: bool
    reply_visibility: ReplyVisibility  # resolved by §3.4
    user_message: str | None           # [S] copy; None = silent
    surface: Surface
    workflow: "WorkflowResult | None"  # the wrapped mutation result; None for OPEN_PANEL / confirm-pending
    audit_emitted: bool                # dispatch-trace emitted (publish-accepted only, §1.2 honesty)
    request_id: str

class DenialReason(enum.Enum):
    ALLOWED = "allowed"; DRAINING = "draining"; AUTHORITY = "authority"
    DISABLED = "disabled"; VISIBILITY = "visibility"; CHANNEL = "channel"
    USER_ERROR = "user_error"; COOLDOWN = "cooldown"; AI_THROTTLE = "ai_throttle"
    NOT_FOUND = "not_found"; CONFIRM_DECLINED = "confirm_declined"; DISPATCH_ERROR = "dispatch_error"

_PRE_DISPATCH_DENIALS = frozenset({           # used by §3.4
    DenialReason.AUTHORITY, DenialReason.DISABLED, DenialReason.VISIBILITY,
    DenialReason.CHANNEL, DenialReason.USER_ERROR, DenialReason.COOLDOWN,
    DenialReason.AI_THROTTLE, DenialReason.NOT_FOUND,
})
```

**Dispatch-kind table (step 5 — closes "route=PanelRef has no dispatch path").** The routable ref is
read generically off the spec (`CommandSpec.route` / `PanelActionSpec.handler` /
`SelectorSpec.on_select`) and dispatched by its type:

| Routable ref type | Dispatch kind | Runs | Returns | Result outcome | Re-entrant `resolve()`? |
|---|---|---|---|---|---|
| `PanelRef` (CommandSpec.route) | `OPEN_PANEL` | kernel panel engine builds + renders the panel (the render **is** the reply) | `None` | `SUCCESS` (or `from_exception` on a build error) | **No** — opening a panel is a terminal render. The panel's own actions each spawn their *own* `ResolveRequest` when clicked (component/selector adapter). |
| `HandlerRef` | `INVOKE_HANDLER` | a registered domain handler | `WorkflowResult` | mapped, below | No |
| `WorkflowRef` | `INVOKE_WORKFLOW` | the kernel workflow engine (setting edit, binding set, provision, toggle, paginate) | `WorkflowResult` | mapped, below | No |

**`WorkflowResult` → §2.7 mapping (built on the REAL shipped grounding).** A dispatched
handler/workflow returns a **`WorkflowResult`** — the §2.7 **kernel** type (K7), a strict superset of
the shipped `LifecycleResult` (`services/lifecycle/contracts.py:77`) reusing the shipped outcome
constants verbatim (`:48–52`) and the shipped `StepResult` (`:56`). The resolver **copies the
`outcome` through unchanged** and uses `classify_outcome` (`services/lifecycle/contracts.py:108`)
semantics for batched steps. `OPEN_PANEL` and confirm-pending produce `outcome=SUCCESS,
workflow=None`. **No new outcome constant is introduced** — the `{user_error, denied, transient,
bug}` nuance lives in `error_class` + `reason`, not `outcome`, so the golden harness reads `Result`
as a `LifecycleResult`.

**`StageResult` is NOT a dispatch return (closes the under-motivation gap).** The shipped
`StageResult` (`core/runtime/message_pipeline.py:181`: `deleted`/`short_circuit`/`moderation_action`)
is the **passive on-message pipeline** stage contract — a *different substrate* one layer below
`resolve()`. When a message stage recognizes a prefix command it hands off to the `prefix` adapter →
`resolve()` → a `WorkflowResult`; the stage itself returns its `StageResult` to steer the *pipeline*
(short-circuit / delete). `StageResult` never crosses the `resolve()` seam, so its overloaded
`short_circuit` (gate-block vs successful delete-and-stop) is a message-pipeline concern, never
mislabeled as a dispatch `BLOCKED`. The resolver's dispatch-return grammar is **`WorkflowResult |
None`** only.

### 3.7 The surface adapters (build a `ResolveRequest`)

| Adapter | Input | Notes |
|---|---|---|
| `slash` | `discord.Interaction` (app cmd) | generalizes `from_interaction` (`command_access.py:462`); `args=interaction.namespace` |
| `prefix` | `commands.Context` | generalizes `from_prefix_ctx` (`:441`); K1 exact name |
| `fuzzy` | a `CommandNotFound` raw token | K1 fuzzy → AUTO/SUGGEST; replaces the `bot1.py:541-586` re-dispatch (no more `process_commands` re-entry) |
| `component` | `discord.Interaction` (button **or** select) | replaces `interaction_router.dispatch`; button ⇒ `target.spec` a `PanelActionSpec`, select ⇒ a `SelectorSpec`; `target="<panel_id>.<action_id\|selector_id>"` from the custom_id; **gains cooldown** (L-5). Also carries the confirm re-entry (`confirmed=True`, §3.2). |
| `modal` | `discord.Interaction` (modal submit) | `surface=MODAL`; `args` = the submitted modal fields; `target.spec` = the `PanelActionSpec` that declared `defer_mode=MODAL` (or opened a typed-phrase confirm). A modal is an ACK/entry mechanism of an existing action, not a separate primitive — so it needs no new spec member. |
| **`nl` (net-new)** | `ResolvedIntent` (rung 3) / a plan (rung 4) | turns the `next_command` **string** into a real `TargetRef` (K1) + validated `args`; funnels through `resolve()` so an NL intent runs the identical order as a slash command |

```python
# rung 3 — the net-new adapter that makes AI rungs execute
async def request_from_intent(intent: ResolvedIntent, *, responder, origin,
                              guild_id, channel_id, actor) -> ResolveRequest:
    target = namespace.resolve_command(intent.next_command)     # K1 (CONSUMED); None → NOT_FOUND/BLOCKED
    return ResolveRequest(surface=Surface.NL_INTENT, target=target, args=intent.args,
                          provenance=NLProvenance(intent.nl_text, intent.intent_key,
                                                  intent.confidence, orchestration_id=None),
                          actor=actor, guild_id=guild_id, channel_id=channel_id,
                          responder=responder, origin=origin)

# rung 4 — orchestration: N intents → N ResolveRequests sharing one minted orchestration_id,
#   resolve()'d sequentially via the task supervisor (INV-T); stop on first non-SUCCESS
#   (or a declared policy, §9); each step audited under the shared id.  A mid-sequence failure is
#   reported as ONE aggregate PARTIAL (§2.7 vocab, via classify_outcome §3.6) carrying the completed
#   prefix: the steps before the stop ran and succeeded, the failing step's error_class/reason is
#   surfaced, and the untried suffix did not run.  (Closes the NL_ORCHESTRATION
#   "no producer" nit — this adapter is the producer that sets surface=NL_ORCHESTRATION.)
async def request_from_plan_step(step: PlanStep, *, plan_id: str, responder, origin,
                                 guild_id, channel_id, actor) -> ResolveRequest:
    target = namespace.resolve_command(step.next_command)       # K1; None → NOT_FOUND/BLOCKED
    return ResolveRequest(surface=Surface.NL_ORCHESTRATION, target=target, args=step.args,
                          provenance=NLProvenance(step.nl_text, step.intent_key,
                                                  step.confidence, orchestration_id=plan_id),
                          actor=actor, guild_id=guild_id, channel_id=channel_id,
                          responder=responder, origin=origin)
```

---

## 4. Provides / Consumes

**Provides (canonical shapes I OWN — everyone else consumes these):**

| Contract | Shape |
|---|---|
| `resolve(ResolveRequest) -> Result` | the ONE chokepoint every rung + panel/component/selector/modal action funnels through |
| `ResolveRequest` + `SurfaceResponder` | the surface-agnostic request + the ack/reply port (no discord type in kernel decision logic) |
| Fixed order + ACK placement | `admission→authority→validate→cooldown→[ack]→audit→dispatch→render`; denials pre-ack, defer on the allow path only, defer commits the success-visibility `V` |
| Dispatch-kind table | `PanelRef⇒OPEN_PANEL`, `HandlerRef⇒INVOKE_HANDLER`, `WorkflowRef⇒INVOKE_WORKFLOW` (§3.6) |
| ConfirmationSpec round-trip | confirm = a second `resolve()` dispatch (`confirmed=True`); decline/timeout ⇒ `DECLINED`/`CONFIRM_DECLINED` (§3.2 step 5) |
| `from_exception` + the exception→class→reason table + `user_message` derivation | §3.3 |
| `Result`/outcome grammar as returned by dispatch | copies `WorkflowResult.outcome` through into §2.7; `error_class`+`reason` carry the nuance; `outcome` stays the frozen 5 |
| dispatch-trace audit skeleton | `command.dispatched` EventSpec (`owner_subsystem="kernel"`), `override_applied`/`base_allowed` payload, additive to `emit_audit_action` |
| ephemerality resolver | `resolve_reply_visibility(outcome, reason, lane, declared, committed)` (T2-17) |
| the four grammar amendments (§3.0) | `authority_ref` / `enabled_when` / `reply_visibility` / `defer_mode` — pinned type+default+role, absorbed by §2.2/§2.4/§2.6 |
| PredicateRef grammar + evaluator | `predicates.evaluate(ref, ctx)` + the `<kind>:<key>` / registered-ref forms (§3.0) |

**Consumes (ASSUMED from siblings — exact assumption stated for the seam pass):**

| Contract | Assumed shape | Sibling / row |
|---|---|---|
| `authority_ref` resolution | **ONE** `authority_ref: str` on the spec, resolved to `AuthorityDecision{allowed, lane, denial_copy, override_applied, base_allowed}`; owner-override applied inside it; the `lane` (config_governance vs domain) is the Gate-0 capability-or-tier mapping (Q-0237d). **Supersedes** design-spec §2.2's two-lane `capability_required`/`audience_tier` (L-13/T1-4). The lane is what makes §3.4's default computable | authority engine (K6) |
| `CooldownSpec` + AI-throttle | `CooldownSpec{rate, per_s, scope}` (design-spec §2.2 G-4) as **one axis**; the AI-throttle a **distinct** axis on the NL rung — two independent limiters | throttle spec (K7/settings) |
| K1 name resolution | `namespace.resolve_command(name) -> TargetRef | None` for exact + fuzzy | namespace (K1) |
| PredicateRef read accessors | settings/binding/guild-state read accessors behind the db + settings ports, for `predicates.evaluate` | settings (K-settings) / db port |
| idempotency-key contract | a per-action key checked **at dispatch** dedups under merge=deploy overlap (L-6, T2-2/T2-21); the resolver provides the dispatch seam where the key is checked (`request_id` on the confirm re-entry), does not own the key format | mutation/idempotency spec |
| `PanelActionSpec`/`SelectorSpec` funnel | **assumed:** panel actions and selectors funnel through `resolve()` and carry `authority_ref`/`enabled_when`/`reply_visibility`/`cooldown`/`defer_mode` per §3.0 — the route-through-C-1 vs PanelActionSpec-own-fields grammar fork is **owner-gated §8-a**. If the owner picks the own-fields option the change is localized to those spec fields; the resolver reads `target.spec.<field>` either way | panel grammar (§2.4/§2.6) |

---

## 5. Data model + migration/index shape

**No new table.** The resolver is stateless per request. It **reads** cached policy through existing
accessors (command-access policy `get_command_access_policy`, subsystem visibility
`get_visible_subsystems`, `enabled_when`/`visible_when` predicate reads) via the db + settings ports;
it **charges cooldown in-memory** (the shipped `@commands.cooldown` model — durability is a consumed
sibling, L-8/T2-6 territory, not owned here); it **emits** the `command.dispatched` trace as an
`EventSpec` with **no persistence** while `observability_only=True`. The trace's new
`override_applied`/`base_allowed` fields are payload additions only — no schema. If §8-c selects
dispatch-time-authoritative audit, the trace writes the **existing** audit table through the workflow
engine's `emit_audit_action` fan-out (no new schema); its `payload_schema` becomes an
`AuditEventSpec` (§2.8) — the payload doubling as the audit-row shape.

---

## 6. Restart & merge=deploy behavior

- **Boot reconcile.** `tree.error`/`on_app_command_error`/`on_command_error` are registered at the
  composition root (`sb/app/error_handlers.py`) during host construction, **before gateway
  connect** (§1.2 boot order) — so the envelope is armed the instant the first interaction arrives,
  closing the "31 slash commands, zero handler" gap deterministically.
- **Dual-instance overlap (LP-4).** A draining instance's `resolve()` returns at **step 0**
  (`can_accept_commands()` false) ⇒ `BLOCKED`/silent, dispatching nothing. This generalizes the
  shipped `lifecycle.is_shutting_down()` gate (*invoked at* `message_pipeline.py:277`) — today only
  the message pipeline consults it — to **slash, component, selector, modal, and NL surfaces**,
  closing the interaction-surface leg of L-6's double-fire during handoff.
- **Idempotency at dispatch (CONSUMED).** For the additive-side-effect leg (double-XP class), the
  per-action idempotency key (T2-2) is checked at **step 5** before the handler runs, so a
  MESSAGE_CREATE/interaction delivered to both gateway connections dedups **before** dispatch. The
  confirm re-entry reuses `request_id` as its dedup key so a double-clicked confirm runs once. The
  resolver owns the *seam*; the key format is the sibling's.
- **Cooldown state** is in-memory and resets on restart — identical to shipped behavior; a durable
  cooldown store is explicitly deferred (§9).
- **Confirmations survive nothing by design.** A confirm surface is session-scoped
  (`timeout_s`); a restart mid-confirm drops the prompt and the actor re-invokes — no persisted
  confirm state, matching the shipped ephemeral-confirm posture.

---

## 7. Architecture rules honored (INV / layer cites)

- **Layer table (§1.1).** `resolve.py` in `kernel/interaction` imports `spec`, `namespace`,
  `observability`, `kernel/authority` (K6), `kernel/workflow` (K7), `kernel/lifecycle` (K5),
  `kernel/settings` (visibility/enablement reads), the shared `predicates` evaluator, and the
  `SurfaceResponder` **port it defines**. It **must NOT** import `domain`, `manifest`, or `adapters`
  internals. Concrete responders live in `adapters/discord` implementing the port. Honors **"the
  kernel never imports domains"** (the zero-tolerance generalization of shipped `services → views`).
  Domain handlers are resolved via **registered refs** (namespace) at composition time — no
  `kernel → domain` edge, no dynamic import (§1.6).
- **INV-T** (design-spec §8 decision 4): the rung-4 orchestrator spawns via the managed task
  supervisor, never a free-floating `asyncio.create_task` (AST-fenced).
- **The no-skip fence** (§1.2, made structural): an AST check asserts there is **no path** from any
  surface (`@bot.event`/`tree.interaction_check`/component/selector/modal/NL) to a handler except
  through `resolve()` — the generalization of "no code path from a Discord component to a handler
  that skips the check." This is the enforcing guard for L-4's "AST no-skip fence."
- **Audit fan-out preserved.** Auditable mutations still call `emit_audit_action` **inside** the
  workflow engine (K7); the resolver's dispatch-trace is additive, never a bypass — the
  `audit.action_recorded → server_logging` wiring (§1.3) is untouched.
- **DB via the port; settings via keys.** All policy reads (incl. PredicateRef evaluation) go through
  the db + settings ports / typed accessors; enablement/visibility keys are `settings_keys`
  constants, never raw strings.

---

## 8. Options → Decision → Why (forks I CLOSED)

| Fork | Options | Decision | Why |
|---|---|---|---|
| Outcome vocab for admission denials + `bug` | (a) add a 6th "internal error"/"denied" outcome constant · (b) keep the frozen 5, put nuance in `error_class`+`reason` | **(b)** | The prompt directs "map INTO the frozen §2.7 vocab"; a 6th constant breaks the golden-harness "read new-as-old" contract (§2.7). `error_class` + `reason` carry the nuance; `bug`→`BLOCKED` is a documented stretch (the traceback + operator finding carry the "our fault" signal, not the enum). |
| ACK placement + ACK-time visibility | (a) eager-defer before step 0 (denials become followups) · (b) check-then-ack after step 2; commit the **success visibility `V`** at defer, and let post-defer failures render at `V` | **(b) default, (a) as a bounded `eager_defer` flag** | Steps 0–2 are cached/in-memory ≪ 3 s; check-then-ack gives clean pre-ack ephemeral denials (`response.send_message`, matching `_slash_access_check:206-215`) with **nothing frozen**. The residual ACK-vs-outcome tension is closed by committing `V=declared or lane_default(lane)` at defer (lane is known — step 1 ran) and honoring the frozen flag for post-defer results (§3.4). |
| Confirmation plumbing | (a) block `resolve()` awaiting the confirm interaction · (b) confirm = a **second** `resolve()` dispatch via its own component | **(b)** | A 60 s suspended coroutine neither scales nor survives merge=deploy. The confirm control is its own custom_id → re-enters via the component/modal adapter with `confirmed=True`; timeout/cancel → `DECLINED`/`CONFIRM_DECLINED`. Reuses the existing component machinery — no bespoke plumbing (§3.2 step 5). |
| Cooldown refund on failure | (a) always keep · (b) always refund on error · (c) refund only transient/bug (+ keep on declined) | **(c)** | A `user_error`/`DECLINED` is a real use of the slot (keep); a `transient`/`bug` is not the actor's fault (refund) — mirrors discord.py's `reset_cooldown`-on-error and prevents "spent a cooldown on our crash." |
| StageResult in the dispatch-return grammar | (a) map `StageResult` as a dispatch return · (b) drop it — dispatch returns `WorkflowResult\|None`; `StageResult` stays the message-pipeline substrate | **(b)** | `StageResult` (`message_pipeline.py:181`) is the passive on-message stage contract one layer below `resolve()`; its overloaded `short_circuit` would mislabel a successful moderation delete as `BLOCKED`. Dropping it removes an ambiguous seam (§3.6). |
| NL rung execution | (a) leave `next_command` a string (status quo) · (b) net-new adapters → `(command,args)` → `resolve()` | **(b)** | The whole point of L-4's "slash/prefix/fuzzy/NL all funnel"; running the identical order means an NL intent inherits authority/validate/cooldown/audit for free — no second policy surface. The rung-4 adapter is the `NL_ORCHESTRATION` producer. |
| Wizard recovery copy | (a) keep `recovery_context_from_exception` · (b) fold into `from_exception` as a surface render | **(b)** | Its `permission_hints` map **is** the denied/transient rows; a separate function is the 4th divergent posture L-4 kills. |
| Drain gate scope | (a) message pipeline only (status quo) · (b) all surfaces via step 0 | **(b)** | Closes L-6's interaction-surface double-fire leg at the same seam — one gate, every surface. |

### 8-owner-gated. Forks I must NOT decide (options + recommendation, live-owner review)

These three cross-referenced forks are genuinely owner-gated (product/architecture/audit-retention);
they are presented, never decided. Each is also in the structured `open_decisions`.

- **§8-a — panel-action grammar: route-through-C-1 vs PanelActionSpec-own-fields.**
  *Options:* **(A)** panel actions and selectors funnel through `resolve()` and carry the §3.0 fields
  (`authority_ref`/`enabled_when`/`reply_visibility`/`cooldown`/`defer_mode`) on their own specs, so
  the resolver reads `target.spec.<field>` uniformly across commands and components — one code path,
  every surface; **(B)** panel actions keep a lighter spec and the resolver derives their
  authority/cooldown from the *owning panel* or a shared table, keeping `PanelActionSpec` minimal.
  *Recommendation:* **(A)** — it is what makes L-5 ("component = 2nd resolver, no cooldown") retire
  structurally and gives every surface one authority story; (B) reintroduces a per-surface derivation
  the whole design exists to remove. *Impact if (B):* localized to which spec holds the fields — the
  resolver contract is unchanged. **Owner-gated:** it sets the panel grammar shape §2.6 freezes.
- **§8-b — owner-override scope + transparency-audit sink wording.**
  *Options (scope):* **(A)** the owner-override authorizes only within the actor's **member guilds**
  (owner must share the guild); **(B)** the override authorizes in **any** guild the platform owner
  can reach. *Options (sink):* the transparency trace (fired when `override_applied`, §3.5) routes to
  **(i)** the existing observability trace only, **(ii)** a distinct operator-visible transparency
  log with named "would-not-otherwise-authorize" copy. *Recommendation:* scope **(A)** member-guild
  (least-surprise, matches the shipped platform-owner posture) + sink **(ii)** (the point of T2-10 is
  operator-visible transparency). *Impact:* step-1 override scope + one audit-sink route; the
  `override_applied` flag and firing condition are designed regardless. **Owner-gated:** override
  reach is an authority-policy / credential-custody decision. *(Reconciled: step 1 no longer
  hardcodes member-guild — it applies the override once and defers the scope to this fork; §10's
  L-12/T2-10 row and this entry now agree.)*
- **§8-c — promote the dispatch-trace to authoritative audit?**
  *Options:* **(A)** keep `command.dispatched` `observability_only=True` (telemetry, not a retained
  audit row); **(B)** promote it to an `AuditEventSpec` written through the `emit_audit_action`
  fan-out into the existing audit table (every dispatch becomes a retained row). *Recommendation:*
  **(A)** for v1 — the per-mutation audit already covers the auditable writes; a retained row per
  *dispatch* is a retention/volume decision. *Impact if (B):* no new schema (reuses the audit table),
  but changes retention posture. **Owner-gated:** audit-retention + data-volume policy.

---

## 9. Labeled deferrals (bounded by the capability corpus)

- **Durable cooldown store** — merge=deploy-surviving cooldown state. Bounded to L-8/T2-6
  (ManagedTaskSpec durability); the resolver reads whatever `CooldownSpec` backing store that row
  provides. *Reason:* durability is a distinct owned seam; in-memory matches shipped behavior today.
- **Idempotency-key format** — the per-action dedup key (T2-2/T2-21). *Reason:* consumed; the
  resolver owns only the dispatch check-point.
- **Fuzzy safety classification** — which fuzzy AUTO-corrections are safe to auto-run is derived from
  the manifest `effect` field (Tier-3 batch C2-Q5), not a hand-list. *Reason:* consumed from the
  manifest; the `fuzzy` adapter reads it.
- **Rung-4 orchestration failure policy** — stop-on-first-non-SUCCESS is the default, and a
  mid-sequence stop reports **one aggregate `PARTIAL` with the completed prefix** (§3.7); a per-plan
  policy (continue/compensate) is bounded to the AI/knowledge band (Phase 4 band 6). *Reason:* the
  orchestration corpus is not yet enumerated; the sequential seam + shared `orchestration_id` +
  the `PARTIAL`-with-prefix aggregate reporting are designed now.

---

## 10. Retirement map

| Row | Retires how | Status |
|---|---|---|
| **L-4** (C-1 cluster: no envelope, slash bypass, no single seam) | single `resolve()` seam (§3.2); `from_exception` envelope (§3.3); slash/prefix/fuzzy/component/selector/modal/**NL** funnel (§3.7); the AST no-skip fence (§7) | **RETIRED** |
| **L-5** (panel/component = 2nd resolver, no cooldown) | component/selector adapters build a `ResolveRequest`; cooldown read off `target.spec` at step 3 for every surface | **RETIRED (design)** — the grammar fork (route-through-C-1 vs PanelActionSpec-own-fields) is **owner-gated §8-a** |
| **T2-4** (error-envelope home = inside C-1) | `from_exception` lives in `kernel/interaction`, invoked at step 5 for all rungs; `{user_error,denied,transient,bug}`+`retryable`+`reason` | **RETIRED** |
| **T2-9** (per-guild enablement gate on CommandSpec at C-1) | `enabled_when: PredicateRef` (§3.0) checked in the `validate` step for every surface (§3.2 step 2a) — a **real field with a pinned predicate grammar**, not by location | **RETIRED** |
| **T2-17** (ephemerality / silent-vs-reply resolver) | `resolve_reply_visibility` over **all five** §2.7 outcomes (§3.4), lane-driven + committed-visibility policy, not per-call-site | **RETIRED** |
| **slash-skips-subsystem-visibility drift** | the `validate` step runs the same visibility check for slash + prefix + component + selector + NL — the divergent second path is deleted | **RETIRED** |
| **L-6** (deploy-overlap double-fire — interaction leg) | step-0 drain gate on all surfaces + the dispatch idempotency check-point (§6) | **PARTIAL** — interaction/NL legs closed here; the key format is consumed (T2-2) |
| **L-12 / T2-10** (owner-override: one map behind C-1, override once at top; transparency audit) | authority resolved once at step 1 (single top-of-order override point); the dispatch-trace payload carries `override_applied`/`base_allowed`, so the transparency audit **fires conditionally** at step 4 | **PARTIAL / surfaced** — the *mechanism* (flag + firing condition) is designed; override **scope** (member-guild vs any) + **sink wording** are **owner-gated §8-b** |
| **L-13 / T1-4** (authority vocabulary) | consumed as ONE `authority_ref` (Q-0237d) resolving to `AuthorityDecision` (carrying the lane) — not retired by me; the resolver reads a single ref | **CONSUMED** (seam correction) |

---

## 11. Build order (design-spec §9)

- **K7 (workflow engine band):** land `sb/spec/outcomes.py` (constants + `ErrorClass`/`DenialReason`/
  `ReplyVisibility`/`AuthorityLane`/`DeferMode`), `Result`, the `WorkflowResult → §2.7` outcome
  pass-through, `resolve_reply_visibility`, and `from_exception` — they are pure, spec-leaf, and
  extend the workflow Result grammar. No Discord. `AuthorityDecision` lands with the authority engine
  (K6); the resolver consumes it.
- **K8 (interaction runtime band, at its front):** land `resolve()`, `ResolveRequest`, the
  `SurfaceResponder` port, the `predicates.evaluate` evaluator, the six surface adapters
  (slash/prefix/fuzzy/component/modal/nl), the ephemerality commit at the ACK boundary, the confirm
  round-trip, and the composition-root `tree.error`/`on_app_command_error` registration.
- **Grammar absorption:** the four §3.0 amendments (`authority_ref`/`enabled_when`/`reply_visibility`/
  `defer_mode`) land in `sb/spec/` on `CommandSpec`/`SelectorSpec`/`PanelActionSpec` when those specs
  are cut — before any subsystem authors against them.
- **Depends on:** K1 (name resolution for adapters), K5 (admission gate), K6 (`authority_ref`
  resolution → `AuthorityDecision`), K7 (Result grammar + audit spine).
- **Blocks:** all of Phase 4 — **nothing dispatches without `resolve()`**; specifically band 1
  (settings/help) cannot flip `pending → ported` until the K8 chokepoint exists. The AST no-skip
  fence arms with K8 so no ported subsystem can add a bypassing path.

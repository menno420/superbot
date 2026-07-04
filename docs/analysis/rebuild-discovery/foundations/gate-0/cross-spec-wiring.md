# Gate-0 · Cross-spec wiring — the four pending absorptions, CLOSED-AT-GATE-0

> **Status:** `reference` — Gate-0 grammar-freeze artifact (2026-07-04). **NOT SOURCE OF TRUTH** —
> a design/spec contract; shipped source + the owning specs win (Q-0120). This doc does **not**
> rewrite the strand spec bodies — the Gate-0 frozen grammar + **this** wiring doc are the
> authoritative consolidated home for these four seam edits. The **real Phase-B build applies them
> to `sb/spec/` + `sb/kernel/`** as specified below.

The four specs **flagged** these cross-spec absorptions but did not land them (each spec is
buildable-consistent, but the loser-side edit is pending). Gate-0 **closes** them. Each is a precise,
ready-to-apply edit: exact field/shape · exact target leaf · exact owning-spec § · the RC it closes ·
status **CLOSED-AT-GATE-0**. Sources re-verified this pass against the owning specs (Q-0120):
[`02-resolver-error-envelope.md`](../design/strand-1-kernel-spine/02-resolver-error-envelope.md) §3.0/§3.1/§3.3/§3.4/§3.5,
[`04-authority-engine.md`](../design/strand-1-kernel-spine/04-authority-engine.md) §3.3/§3.4/§3.5 + Seam notes 1-3,
[`07-workflow-engine.md`](../design/strand-2-runtime-durability/07-workflow-engine.md) §3.2,
[`06-draft-pipeline.md`](../design/strand-2-runtime-durability/06-draft-pipeline.md) §12,
[`10-security-abuse-rubric.md`](../design/strand-3-cross-cutting-concerns/10-security-abuse-rubric.md) §8.1,
and the RC ledger in [`seam-consistency-matrix.md`](../design/seam-consistency-matrix.md) §9.

**Mis-cite check (Q-0120):** all four prompt cites verified correct against source — `04 §3.3`
carries the pre-computed `member_tier` (closure 1), `04 §3.3/§3.4/§3.5` own the authority hardening
shapes (closure 2), `07 §3.2` is the `WorkflowContext` block flagged by `06 §12` (closure 3), and
`10 §8.1` designs the egress port (closure 4). **No mis-cite corrected.** One naming precision folded
in below: spec 02 §3.0's field is `denial_copy`; spec 04's canonical name is `denial_message` — the
rename is part of RC-14 (closure 2).

---

## Closure 1 — `ActorRef.member_tier` onto spec 02 (RC-12)

**Why.** Spec 04's `AuthorityRequest` carries a **pre-computed** `member_tier` string (04 §3.3,
`member_tier: str | None = None` — "PRE-COMPUTED tier string in the target guild"). Spec 02's
discord-free `ActorRef` carries only `is_guild_operator: bool`, which collapses
staff/moderator/administrator/owner into one flag — it **cannot** recover the 6-tier ladder. Without
this field the **TIER lane cannot resolve staff/mod/admin/owner** and L6/the tier lane re-opens (04
Seam note 1: "the one non-trivial cross-spec wiring"). The adapter — the discord-touching layer that
already builds `ActorRef` — pre-computes the tier via `member_tier_from_member(member, guild.owner_id)`
(`sb/adapters/discord/member_tier.py`, 04 §2) and sets it; the resolver reads `actor.member_tier` when
it builds the `AuthorityRequest`.

| Edit | Target leaf | Owning-spec § | RC closed | Status |
|---|---|---|---|---|
| Add `member_tier: str \| None = None` to `ActorRef` (runtime field, no S/A/O tag; adapter-set via `member_tier_from_member`) | `sb/kernel/interaction/request.py` → `ActorRef` (spec 02 §3.1) | 04 §3.3 owns the need; 02 §3.1 absorbs | **RC-12** | **CLOSED-AT-GATE-0** |

**Exact shape a builder applies** (append to `ActorRef`, after `actor_type` — both are defaulted
trailing fields so dataclass ordering is preserved):

```python
@dataclass(frozen=True)
class ActorRef:                        # spec 02 §3.1 — kernel/interaction/request.py
    user_id: int | None
    is_guild_operator: bool
    is_bot_owner: bool
    is_dm: bool
    actor_type: str = "user"           # RC-18 (already landed)
    member_tier: str | None = None     # RC-12 (this closure): PRE-COMPUTED 6-tier ladder string in the
    #   TARGET guild, set by the surface adapter via member_tier_from_member(member, guild.owner_id)
    #   (04 §2 / sb/adapters/discord/member_tier.py). None for scripted actors / non-members. The ONLY
    #   input by which the TIER lane resolves user/trusted/staff/moderator/administrator/owner. The
    #   resolver reads actor.member_tier into AuthorityRequest.member_tier (04 §3.3). is_guild_operator
    #   / is_bot_owner stay verbatim (the channel-access bootstrap legs are NOT a clean tier threshold).
```

---

## Closure 2 — Spec 02 absorbs 04's frozen authority contracts (RC-2/3/4/5/13/14/15; + RC-12 via closure 1)

**Why.** Spec 02 §3.0 is written to **pre-hardening** shapes: a local
`AuthorityLane{CONFIG_GOVERNANCE, DOMAIN}` enum, a **5-field** `AuthorityDecision`, a channel-access
step not threaded `owner_override`, and an **unnamed** transparency sink. Spec 04's hardening pass
(2026-07-04) froze the winners; **02 is the single loser-spec** on RC-2/3/4/5/13/14/15 (matrix §9
"Pending-absorption summary"). None is a *disagreement* — the winners are frozen — but this is the one
concentrated `02` edit that must land before K8 builds, or L-12 (owner channel-deny) and the tier lane
re-open. Each RC → its exact 02-side edit:

| RC | Edit (02-side) | Target leaf | Owning-spec § | Status |
|---|---|---|---|---|
| **RC-2** | **Import** 04's **10-field** `AuthorityDecision`; **delete** 02 §3.0's local **5-field** dataclass. The resolver reads `decision.{allowed, denial_message, owner_override, lane, lane_would_deny}` and **derives** the trace flags (they are no longer stored fields): `override_applied = owner_override AND lane_would_deny`, `base_allowed = not lane_would_deny` | `sb/kernel/authority/decision.py` (import); resolver `sb/kernel/interaction/resolve.py` | 04 §3.3 | **CLOSED-AT-GATE-0** |
| **RC-3** | **Drop** `AuthorityLane{CONFIG_GOVERNANCE, DOMAIN}` from `sb/spec/outcomes.py` **and** 02 §3.0; **use** `Lane{CAPABILITY, TIER}` from `sb/spec/authority.py` (04-owned leaf). §3.4 `lane_default` re-keys: `EPHEMERAL if lane is Lane.CAPABILITY else PUBLIC` (was `CONFIG_GOVERNANCE`→ephemeral / `DOMAIN`→public — the substitution is exact) | `sb/spec/outcomes.py` (remove enum); `sb/spec/authority.py` (import `Lane`); resolve.py §3.4 | 04 §3.2 | **CLOSED-AT-GATE-0** |
| **RC-4 / RC-13** | Step-2 **channel-access lane** calls `resolve_channel_access(policy, channel_id, owner_override=decision.owner_override, is_bootstrap=is_bootstrap_command(target.key), is_operator=actor.is_guild_operator, is_owner=actor.is_bot_owner)` — **threading the once-computed `owner_override`** (RC-4, the L-12 fix); consumes 04's **8-field** `ChannelAccessDecision` (with `detail ∈ {"", "commands_disabled", "channel_not_allowed"}`, RC-13) | resolver `resolve.py` step 2; `sb/kernel/authority/channel_access.py` (import) | 04 §3.4 | **CLOSED-AT-GATE-0** |
| **RC-5** | **Extend** the transparency-emit trigger (§3.5) to the 04 condition: `owner_override AND (lane_would_deny OR (channel is not None AND channel.would_deny_without_override))` — not the narrower authority-only test | resolver `resolve.py` step 4 (§3.5) | 04 §3.5 | **CLOSED-AT-GATE-0** |
| **RC-14** | `from_exception`'s `denied` row reads the **engine-generated** `AuthorityDecision.denial_message` (not `denial_copy`, not a `[S]` field). Rename 02 §3.0/§3.2's `denial_copy` → `denial_message` at every read site | `sb/kernel/interaction/errors.py` + resolve.py step 1 | 04 §3.3 | **CLOSED-AT-GATE-0** |
| **RC-15** | **Name** the transparency emit: at step 4, when the trigger holds, call `build_transparency_audit(auth, channel, actor_id=req.actor.user_id, guild_id, target_key, surface, clock)` and, when non-`None`, `sink.emit(audit)` via the **`TransparencySink` port** (04-owned) — replacing 02 §3.5's unnamed "additionally routes to the transparency-audit sink." Neither carrier touches `emit_audit_action` | resolver `resolve.py` step 4; `sb/kernel/authority/transparency.py` (import port) | 04 §3.5 | **CLOSED-AT-GATE-0** |
| RC-12 | `ActorRef.member_tier` (the AuthorityRequest input) — **closed by Closure 1** above; listed here because the prompt groups it with the authority batch | see Closure 1 | 04 §3.3 | **CLOSED-AT-GATE-0 (Closure 1)** |

**Exact shape a builder applies.** After this edit spec 02's authority-consumption reads:

```python
# sb/spec/outcomes.py — RC-3: AuthorityLane is REMOVED from this leaf.
#   (ErrorClass, DenialReason, ReplyVisibility, DeferMode stay; Lane now lives in sb/spec/authority.py.)

# sb/kernel/interaction/resolve.py — step 1 (authority), after RC-2/3/4/5/14/15:
from sb.spec.authority import Lane                       # RC-3 (was local AuthorityLane)
from sb.kernel.authority.decision import AuthorityDecision, ChannelAccessDecision   # RC-2 / RC-13
from sb.kernel.authority.transparency import build_transparency_audit, TransparencySink  # RC-15

decision = await resolve_authority(AuthorityRequest(
    authority_ref=target.spec.authority_ref, actor_type=actor.actor_type,
    user_id=actor.user_id, guild_id=req.guild_id,
    is_member=(req.guild_id is not None and not actor.is_dm),
    member_tier=actor.member_tier,                       # RC-12 (Closure 1)
))
# denied → user_message = decision.denial_message (RC-14, engine-generated)
override_applied = decision.owner_override and decision.lane_would_deny   # RC-2 (DERIVED, not a field)
base_allowed     = not decision.lane_would_deny                          # RC-2 (DERIVED)

# step 2 (validate) — channel-access lane, RC-4 / RC-13:
chan = await resolve_channel_access(
    policy, req.channel_id,
    owner_override=decision.owner_override,              # RC-4: the L-12 fix — threaded, not re-derived
    is_bootstrap=is_bootstrap_command(target.key),      # CONSUMED from K1/registry
    is_operator=actor.is_guild_operator, is_owner=actor.is_bot_owner,
)   # reads 8-field ChannelAccessDecision incl. `detail` (RC-13)

# step 4 (audit) — transparency emit, RC-5 / RC-15:
audit = build_transparency_audit(decision, chan, actor_id=actor.user_id, guild_id=req.guild_id,
                                 target_key=target.key, surface=req.surface.value, clock=clock)
if audit is not None:                                    # trigger = owner_override AND (lane_would_deny
    await sink.emit(audit)                               #   OR chan.would_deny_without_override)  — RC-5

# §3.4 ephemerality — RC-3 re-key:
def lane_default(lane: Lane) -> ReplyVisibility:
    return ReplyVisibility.EPHEMERAL if lane is Lane.CAPABILITY else ReplyVisibility.PUBLIC
```

---

## Closure 3 — `WorkflowContext.test_mode` onto spec 07

**Why.** Spec 06 §12 note 2 flags it for 07: a `RELEASE_TEST` draft **must not** fire a real Discord
write against a real guild. `test_mode` is distinct from `dry_run` — `dry_run` rolls the DB back;
`test_mode` **commits** the DB test but **suppresses/routes** the external EFFECT legs. Spec 07 §3.2's
`WorkflowContext` has `dry_run` and (landed) `correlation_id` but **no** `test_mode`; the draft-apply
loop already constructs the field (06 §3.5, `test_mode=(draft.verification.test_mode if
draft.verification else False)`) — 07 must accept and honor it. It threads `draft`
`verification.test_mode` into **each op's** `WorkflowContext`.

| Edit | Target leaf | Owning-spec § | RC closed | Status |
|---|---|---|---|---|
| Add `test_mode: bool = False` to `WorkflowContext` (runtime field); 07's EFFECT-leg runner (07 §3.3 step 5) **honors** it — built default: suppress the real Discord write and render the planned effect to `VerificationContext.debug_channel_id` | `sb/kernel/workflow/context.py` → `WorkflowContext` (spec 07 §3.2) | flagged by 06 §12 note 2; absorbed by 07 §3.2 | **no RC row** — a `06 §12` seam-correction (twin of `correlation_id`/RC-16); the suppress-default is register **Q-D28** (RATIFY-DEFAULT) | **CLOSED-AT-GATE-0** |

**Exact shape a builder applies** (append to `WorkflowContext`, alongside `correlation_id` — both are
the two 06 §12 seam-correction fields):

```python
@dataclass(frozen=True)
class WorkflowContext:                 # spec 07 §3.2 — sb/kernel/workflow/context.py
    actor: ActorRef
    guild_id: int
    request_id: str
    confirmed: bool = False
    dry_run: bool = False              # set by preview(); ROLLS the DB back
    correlation_id: str | None = None  # RC-16 (landed): set by ④ = draft_id
    test_mode: bool = False            # 06 §12 seam-correction (this closure): set by ④ =
    #   draft.verification.test_mode. COMMITS the DB test but suppresses the external EFFECT legs — the
    #   EFFECT-leg runner (07 §3.3 step 5) honors it: built default = suppress the real Discord write and
    #   render the planned effect to VerificationContext.debug_channel_id (Q-D28 fail-safe suppress). NOT
    #   dry_run (which rolls the DB back). Richer route-to-a-real-test-guild is the release-testing band's.
    params: Mapping[str, object] = field(default_factory=dict)
    clock: Clock = SYSTEM_CLOCK
```

---

## Closure 4 — Register the `ChannelEmitter` egress port on 02/K8 (RC-21)

**Why.** Spec 10 §8.1 **designs** the send-egress port to buildable depth but registered it in
**neither** the seam-matrix fork roster (now RC-21) **nor** 02's K8 file/provides table — it was
"buried in the dossier's owner table" (10 §8.1 / Seam note 7). It is a **spec-02/K8 seam correction**,
parallel to RC-12/RC-18 (the additive `ActorRef` fields): a kernel builder wiring K8 must see it where
it looks for every other cross-spec seam. It closes the **X-1 mass-ping vector**
(`automation_executor.py:220 await channel.send(template)` with default `allowed_mentions`, L-24): the
`UNTRUSTED` default ⇒ `AllowedMentions.none()` makes `@everyone` from user-authored template text
structurally impossible.

| Edit | Target leaf | Owning-spec § | RC closed | Status |
|---|---|---|---|---|
| Register the `ChannelEmitter` send-egress **port** (Protocol) + `OutboundContent` + `TrustLevel` as a 02/K8 seam correction — a **new** `kernel/interaction` module, sibling to the frozen `SurfaceResponder` reply-egress port; add it to spec 02's §2 file table + §4 Provides. Concrete `DiscordChannelEmitter` in `adapters/discord/responders.py` (the only module that constructs `discord.AllowedMentions`). **AST-fenced**: a raw `channel.send`/`.reply`/`Messageable.send` outside `adapters/discord/responders.py` is a `SEMANTIC_VIOLATION` (a `check_architecture` egress rule) | `sb/kernel/interaction/egress.py` (new); `sb/adapters/discord/responders.py` (concrete) | 10 §8.1 designs; registered onto 02/K8 | **RC-21** (Q-D26) | **CLOSED-AT-GATE-0** |

**Exact shape a builder applies** (verbatim from 10 §8.1 — folded, not re-derived):

```python
# sb/kernel/interaction/egress.py  — the send-egress port (sibling to SurfaceResponder), RC-21 / Q-D26
class TrustLevel(StrEnum):                     # [S] content-trust tag — default-DENY
    UNTRUSTED = "untrusted"   # member-supplied text → mentions ALWAYS suppressed, markdown escaped (DEFAULT)
    TRUSTED   = "trusted"     # operator/owner-authored → mentions gated to an explicit allowlist
    SYSTEM    = "system"      # bot-authored constant copy → mentions only if statically declared

@dataclass(frozen=True)
class OutboundContent:
    body: str
    trust: TrustLevel = TrustLevel.UNTRUSTED   # default-deny
    allow_mentions: tuple[str, ...] = ()        # ("everyone"|"here"|"role:<id>"|"user:<id>") — honored ONLY for TRUSTED/SYSTEM

@dataclass(frozen=True)
class EmitResult:                               # send-egress outcome envelope — reuses sb/spec/outcomes.py leaf (no new enum)
    delivered: bool                             # True = the channel.send landed
    error_class: ErrorClass = ErrorClass.NONE   # NONE on delivered; DENIED/TRANSIENT/BUG on a failed send
    reason: DenialReason = DenialReason.ALLOWED # ALLOWED on delivered; machine reason on failure

@runtime_checkable
class ChannelEmitter(Protocol):                 # every service-initiated send routes through this ONE seam
    async def send(self, channel_id: int, content: OutboundContent, *, guild_id: int) -> EmitResult: ...

# Concrete DiscordChannelEmitter (adapters/discord/responders.py) computes discord.AllowedMentions from
# (trust, allow_mentions): UNTRUSTED ⇒ AllowedMentions.none() + markdown-escape; TRUSTED/SYSTEM ⇒ the allowlist only.
# The automation_executor.py:220 mass-ping becomes:
#     await emitter.send(cid, OutboundContent(body=template), guild_id=g)   # UNTRUSTED ⇒ mentions off
```

---

## Roll-up

| # | Closure | RC(s) closed | Target leaf(s) | Owning § |
|---|---|---|---|---|
| 1 | `ActorRef.member_tier` | RC-12 | `kernel/interaction/request.py` | 04 §3.3 → 02 §3.1 |
| 2 | 02 absorbs 04 authority contracts | RC-2, RC-3, RC-4, RC-5, RC-13, RC-14, RC-15 (+RC-12) | `spec/outcomes.py`, `kernel/interaction/resolve.py`/`errors.py`, `kernel/authority/*` (imports) | 04 §3.3/§3.4/§3.5 → 02 §3.0/§3.3/§3.4/§3.5 |
| 3 | `WorkflowContext.test_mode` | none (06 §12 seam-correction; Q-D28 default) | `kernel/workflow/context.py` | 06 §12 → 07 §3.2 |
| 4 | `ChannelEmitter` egress port | RC-21 (Q-D26) | `kernel/interaction/egress.py` (new) | 10 §8.1 → 02/K8 |

**Net-new Gate-0 fork?** None. All four map to **existing** register / RC rows (RC-2/3/4/5/12/13/14/15,
RC-21/Q-D26) or an already-flagged seam-correction with a ratified default (test_mode → Q-D28
RATIFY-DEFAULT). No closure surfaced a decision that is not already a register row.

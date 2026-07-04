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

---

## 1. Summary + the exact undesigned gap

**What already exists (anti-pad — not restated).** The shipped `actor_holds_capability`
(`governance/capability.py:71`) already implements the config/governance lane field-for-field:
system/backfill bypass, target-guild membership binding (`:98-113`), platform-owner override
(`:125`), ADMINISTRATOR floor (`:51 _DEFAULT_REQUIRED_TIER`), setup_delegate, revoke-only overlay.
The tier lane already exists as `get_member_visibility_tier` + `is_tier_sufficient`
(`utils/visibility_rules.py:21,44`). The design-spec §2.2 already frames the two lanes; §4.4 already
states "empty `capability_required` ⇒ ADMINISTRATOR floor governs *who may change*, orthogonal to
`activation`." The sibling **C-1 resolver** (`02-resolver-error-envelope.md`) already owns the
fixed order and calls this engine at its step 1. The sibling **compiler** (`01-compiler-snapshot-
amendments.md` P4) already declared it will call `authority.validate(ref)`. **This design does not
re-specify those.**

**The genuinely-undesigned gap this closes:**

| Gap (verified) | Shipped / upstream reality | This design (K6) |
|---|---|---|
| **Two author-facing fields, not one** | design-spec §2.2 still declares `capability_required` **and** `audience_tier`; Q-0237(d) collapses them to ONE `authority_ref`, but nobody designed the classification/resolution | `authority_ref: str` → a **total, non-overlapping lane classifier** (§3.2) + `validate_authority_ref` (compile) + `resolve_authority` (runtime). One string, one lane, always |
| **Owner-override is copy-pasted ~11-16× and channel-blind** | `is_platform_owner` re-checked in 6 mutation services (5 via a duplicated `_check_admin`), 5 views, `governance/writes.py:96`, `governance/resolver.py:223`, `capability.py:125`; **`command_access.py:351` bypasses only *bootstrap* commands** → owner denied a non-bootstrap command in a `SELECTED_CHANNELS`/`DISABLED_EXCEPT_BOOTSTRAP` guild (L-12) | ONE `owner_override_holds(actor, target_guild)` predicate, computed **once at the top** of `resolve_authority`, its verdict threaded into the channel-access lane so owner bypasses **any** command's channel restriction (the L-12 non-bootstrap-deny fix) |
| **Channel-access is a second, owner-blind gate** | `resolve_command_access` (`command_access.py:256-414`) is a standalone channel/lifecycle/DM/bootstrap gate that never consults owner tier | **folded in** as `resolve_channel_access` (§3.4) — sheds lifecycle/DM (→ K5 admission), keeps mode + allowed-channels + bootstrap bypass, **honors the once-computed `owner_override`** |
| **Transparency audit unimplemented** | grep finds **zero** transparency emit anywhere (L-12); Q-0227's promise that an owner sees when the bot-owner used elevated authority in their guild has no code | the `TransparencyAudit` contract (§3.5): trigger = would-not-otherwise-authorize, dual sink, no-log-channel fallback (owner-gated policy, §8-c) |

**Where this sits in the spine everyone consumes** (the K8 resolver's fixed order, spec 02 §3.2):
`admission → **authority (K6, this engine)** → validate (incl. channel-access lane, this engine) →
cooldown → [ack] → audit (incl. transparency emit, this engine's contract) → dispatch → render`.

---

## 2. Files/modules it becomes

New `sb/` paths (layer table design-spec §1.1 — `kernel/authority/` imports `spec`, `namespace`,
`observability`, discord, and adapter ports it defines; **must NOT import** `domain`, `manifest`,
`adapters` internals, `kernel/interaction`):

| Path | Owns |
|---|---|
| `sb/spec/authority.py` | **Frozen leaf** (dependency-free): `Lane` enum, `TIERS` (ported `visibility_rules.py:21`), `ADMIN_FLOOR_TIER = "administrator"`, `classify_authority_ref(ref) -> Lane` (pure syntactic), `validate_authority_ref(ref, reserved_capabilities) -> None` (compile-time; raises `BadAuthorityError`), `is_tier_sufficient(member, required)` (pure order compare). Importable by the compiler (P4) and the namespace with no cycle. |
| `sb/kernel/authority/owner.py` | `owner_override_holds(actor, target_guild) -> bool` — the SINGLE owner-override predicate; `is_platform_owner(user_id)` ported from `config.py:46-73` (deploy-config leaf). |
| `sb/kernel/authority/decision.py` | `AuthorityDecision`, `ChannelAccessDecision`, `CapabilityDecision` (ported), `TransparencyAudit` dataclasses. |
| `sb/kernel/authority/resolve.py` | `resolve_authority(req) -> AuthorityDecision` (the two-lane resolver + owner-override-once); `member_tier(member, guild_owner_id) -> str` (discord-aware, ported `get_member_visibility_tier`). |
| `sb/kernel/authority/channel_access.py` | `resolve_channel_access(policy, channel_id, *, owner_override, is_bootstrap, is_operator, is_owner) -> ChannelAccessDecision` — the folded-in channel-access lane. |
| `sb/kernel/authority/transparency.py` | `build_transparency_audit(auth, channel, ctx) -> TransparencyAudit | None` (the trigger predicate + payload build) + the `TransparencySink` **port**. |
| `sb/adapters/discord/transparency_sink.py` | concrete `TransparencySink`: bot-log send, server-log send, owner-DM-digest fallback (the only module that touches Discord channels for this). |

Shipped paths it **retires** (fold-in, not delete-in-place — old repo stays frozen):

| Shipped path | Fate |
|---|---|
| `governance/capability.py` `actor_holds_capability` / `CapabilityDecision` | ported field-for-field as the **CAPABILITY lane** inside `resolve_authority` (§3.3) |
| `utils/visibility_rules.py` `get_member_visibility_tier` / `is_tier_sufficient` | split: pure order → `sb/spec/authority.py`; discord-aware tier read → `member_tier` (the **TIER lane**) |
| `core/runtime/command_access.py` `resolve_command_access` | **folded in** → `resolve_channel_access` (§3.4); lifecycle/DM legs move to K5 admission (spec 02 step 0); the `:351` bootstrap-only bypass generalizes |
| the **5 duplicated** `_check_admin` (`ai_instruction_mutation.py:51`, `ai_orchestration_mutation.py:66`, `help_overlay_mutation.py:79`, `btd6_source_mutation.py:48`, `ai_policy_mutation.py:108`) | deleted; each becomes the owning spec's `authority_ref=""` (ADMIN floor) resolved through this engine |
| the ~11-16 authorization `is_platform_owner` call sites (settings/ai_*/bot_knowledge/setup_access mutations; `views/base.py:109,124`; `views/{btd6,settings,tickets,starboard}/*`; `governance/writes.py:96`; `governance/resolver.py:223`) | collapse to ONE `owner_override_holds` at the top of `resolve_authority`; downstream axes read the flag, never re-derive it |

---

## 3. The complete public contract

`[S]` marks the one manifest **spec** field this engine reads; all runtime-request/decision fields
carry no S/A/O tag (not authored, not simulated).

### 3.1 The declared field — ONE `authority_ref`

```python
# on CommandSpec / PanelActionSpec / SelectorSpec / SettingSpec / BindingSpec / ResourceRequirement
authority_ref: str = ""      # [S] — replaces §2.2's capability_required + audience_tier (Q-0237d)
```

One string per surface/spec. **Supersedes** the design-spec §2.2 two-field pair (L-13/X-8, stale vs
Q-0237). Mutual exclusivity is now **structural** (one string classifies to exactly one lane — no
"leave the other empty" rule to violate).

### 3.2 The `authority_ref → lane` resolution table (canonical, owned)

`classify_authority_ref(ref)` is a pure syntactic function; the three cases are total and
non-overlapping (a dotted capability and a single-word tier token can never collide):

| `authority_ref` value | `Lane` | Runtime resolution | Compile check (`validate_authority_ref`) |
|---|---|---|---|
| `""` (empty) | `CAPABILITY` (**ADMIN floor**) | `actor_holds_capability(capability="")` → `required_tier="administrator"`, **no** revoke overlay (ports `capability.py:27` "empty resolves to the floor, NOT no-auth") | always valid |
| `"{subsystem}.{resource}.{action}"` (dotted, 3 parts) | `CAPABILITY` | `actor_holds_capability(capability=ref)` → ADMIN floor **+** revoke overlay keyed on `ref` (`capability_execution_overrides`) | ref namespace-reserved (K1); format + reserved-prefix rule `subsystem_registry.py:7` |
| `"user" \| "trusted" \| "staff" \| "moderator" \| "administrator" \| "owner"` | `TIER` | `is_tier_sufficient(member_tier, ref)` — the shipped visibility-tier check | ref ∈ `TIERS` |
| anything else | — | — | **`BadAuthorityError`** (compiler `bad_authority` → `COMPILE_ERROR`, spec 01 P4) |

**ADMIN-floor semantics (owned).** Empty `authority_ref` ⇒ CAPABILITY lane at the administrator
floor — the shipped mutation-pipeline invariant, verbatim, at its shipped scope. Under v1 policy
**every** CAPABILITY-lane ref resolves to the administrator tier (`capability.py:48-51`); the
dotted string differs from `""` only in that it carries a per-guild **revoke** key. A future
capability→tier matrix replaces the constant with a lookup **without touching this table** (the
shipped forward-compat note ported).

### 3.3 `resolve_authority` — the runtime resolver (owner-override once at top)

```python
@dataclass(frozen=True)
class AuthorityRequest:
    actor: object                 # discord Member-like (or None for scripted actors)
    target_guild: object          # the TARGET guild of the action/write (may be None only for bypass)
    authority_ref: str            # [S] from target.spec
    actor_type: str = "user"      # "user" | "system" | "backfill" | "setup_delegate" (ported)

@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    authority_ref: str
    lane: Lane                    # CAPABILITY | TIER
    required_tier: str            # "administrator" (capability lane) | the tier token (tier lane)
    member_tier: str | None       # computed tier; None for bypass / non-member
    owner_override: bool          # the ONCE-computed override verdict — threaded to channel-access
    lane_would_deny: bool         # would the lane have denied WITHOUT the override? (transparency input)
    reason: DenialReason          # ALLOWED on allow; AUTHORITY on deny (from sb/spec/outcomes.py)
    detail: str                   # ported rich audit reason (capability.py:174-193 strings)
    denial_message: str | None    # [S]-derived user copy on deny; None on allow

async def resolve_authority(req: AuthorityRequest) -> AuthorityDecision: ...
```

**Fixed internal order** (ports `capability.py` step order; owner-override stays *after* membership
so it composes with the no-cross-guild-escalation invariant):

| # | Step | Rule |
|---|---|---|
| 0 | classify | `lane = classify_authority_ref(ref)`; compute `lane_allows` (the pure lane result, always, for transparency) |
| 1 | scripted bypass | `actor_type ∈ {system, backfill}` ⇒ `allowed=True`, `owner_override=False`, never dereferences actor/guild (`capability.py:85`) |
| 2 | **membership gate** | non-scripted actor must be a member of `target_guild` (`capability.py:98-113`); else `allowed=False`, `reason=AUTHORITY`. **Owner is not exempt — member-guilds-only** (§8-a) |
| 3 | **owner-override (ONCE, top)** | `owner_override = owner_override_holds(actor, target_guild)`. If True ⇒ `allowed=True` regardless of lane; record `lane_would_deny = not lane_allows` for §3.5 |
| 4 | setup_delegate | `actor_type=="setup_delegate"` ⇒ `allowed=True` (ported Q-0098; still membership-gated + revoke-subject) |
| 5 | lane check | not overridden ⇒ `allowed = lane_allows`; CAPABILITY: `member_tier ≥ admin floor` **+** revoke overlay (if ref non-empty, explicit `False` flips allow→deny, `capability.py:157-171`); TIER: `is_tier_sufficient` |

`allowed = scripted OR owner_override OR setup_delegate OR (member AND lane_allows AND not revoked)`.
`owner_override` and `lane_would_deny` are always populated so the channel-access lane and the
transparency builder can read them.

### 3.4 `resolve_channel_access` — the folded-in channel lane (honors owner-override)

Ports `command_access.py` **minus** lifecycle/DM (those become K5 admission, spec 02 step 0), plus
the owner-override fix:

```python
class AccessMode(enum.Enum):
    ALL_CHANNELS = "all"; SELECTED_CHANNELS = "selected"; DISABLED_EXCEPT_BOOTSTRAP = "disabled"

@dataclass(frozen=True)
class ChannelAccessDecision:
    allowed: bool
    mode: AccessMode | None                 # None = unconfigured (default-allow)
    reason: DenialReason                    # ALLOWED | CHANNEL (COMMANDS_DISABLED mapped to CHANNEL + detail)
    owner_override: bool                    # short-circuited by the once-computed owner_override
    bootstrap_bypass: bool                  # short-circuited by the shipped operator/owner bootstrap path
    would_deny_without_override: bool       # transparency input
    denial_message: str | None

async def resolve_channel_access(
    policy,                                 # CommandAccessSnapshot (mode + allowed_channels), via db port
    channel_id: int | None,
    *, owner_override: bool,                # threaded from AuthorityDecision.owner_override
    is_bootstrap: bool, is_operator: bool, is_owner: bool,
) -> ChannelAccessDecision: ...
```

**Order (buildable):**
1. `owner_override` ⇒ **ALLOW** for *any* command (the **L-12 fix** — was bootstrap-only at `:351`);
   `would_deny_without_override` = what steps 3-4 would return.
2. `is_bootstrap AND (is_operator OR is_owner)` ⇒ ALLOW, `bootstrap_bypass=True` (shipped `:351`
   verbatim — preserves the **guild-operator** bootstrap path, not just owner).
3. `mode is None OR ALL_CHANNELS` ⇒ ALLOW.
4. `DISABLED_EXCEPT_BOOTSTRAP` ⇒ DENY (`COMMANDS_DISABLED`); `SELECTED_CHANNELS` ⇒ ALLOW iff
   `channel_id ∈ policy.allowed_channels` else DENY (`CHANNEL`).

### 3.5 The transparency-audit contract (owned; policy owner-gated §8-c)

```python
@dataclass(frozen=True)
class TransparencyAudit:
    actor_id: int                 # the platform owner
    guild_id: int
    authority_ref: str
    target_key: str               # command name | "<panel_id>.<action_id>"
    surface: str                  # Surface value
    would_deny_reason: DenialReason   # AUTHORITY (lane) | CHANNEL (channel-access)
    timestamp: datetime

def build_transparency_audit(auth: AuthorityDecision, channel: ChannelAccessDecision | None,
                             *, target_key, surface, guild_id, clock) -> TransparencyAudit | None: ...
```

- **Trigger (would-not-otherwise-authorize):** `auth.owner_override AND (auth.lane_would_deny OR
  (channel is not None AND channel.would_deny_without_override))`. Returns `None` when the owner
  would have been authorized anyway (override was a no-op — no audit noise).
- **Sink (recommendation, owner-gated):** dual — (1) **bot-log** (deploy-level owner audit channel),
  (2) **server-log** (the guild's configured governance/audit log). Emitted through the audit spine
  via the `emit_audit_action` seam (CONSUMED §4) so it also rides the shipped
  `audit.action_recorded → server_logging` wiring (design-spec §1.3).
- **No-log-channel fallback:** guild has no server-log configured ⇒ (1) bot-log **+** (2) **owner DM
  digest** (batched, not per-event). The `TransparencySink` port exposes `emit(audit)` +
  `flush_digest()`; the adapter batches the DM.

### 3.6 The compile-time validator (consumed by the compiler P4)

```python
def validate_authority_ref(ref: str, reserved_capabilities: frozenset[str]) -> None:
    """Raise BadAuthorityError if ref does not classify to exactly one lane,
    a CAPABILITY ref is not namespace-reserved, or the format is malformed."""
```

Matches the compiler spec (01) P4 seam `authority.validate(ref) -> None|Error` exactly. Lane
exclusivity is checked here (structural: one string → one lane), closing the "lane-exclusivity check
undefined" gap spec 01 flagged.

---

## 4. Provides / Consumes

**Provides (canonical shapes I OWN — everyone else consumes these):**

| Contract | Shape |
|---|---|
| `authority_ref: str` field + the lane resolution table (§3.2) | ONE ref → `{CAPABILITY(admin-floor / dotted+revoke), TIER}`; empty ⇒ ADMIN floor |
| `resolve_authority(req) -> AuthorityDecision` | the runtime two-lane resolver; owner-override once at top; `owner_override` + `lane_would_deny` exposed |
| `owner_override_holds(actor, target_guild) -> bool` | the SINGLE owner-override predicate (member-guilds-only) |
| `resolve_channel_access(..., owner_override) -> ChannelAccessDecision` | the folded-in channel lane honoring override + bootstrap bypass |
| `validate_authority_ref(ref, reserved) -> None` | the compile-time classifier/validator (compiler P4) |
| `TransparencyAudit` + `build_transparency_audit` + `TransparencySink` port | the trigger/payload/sink/no-log-fallback contract |

**Consumes (ASSUMED from siblings — exact assumption stated for the seam pass):**

| Contract | Assumed shape | Sibling / row |
|---|---|---|
| resolver's authority→… order | K8 `resolve()` calls `resolve_authority` at **step 1**, threads `decision.owner_override` into its **step-2** `resolve_channel_access`, and calls `build_transparency_audit` + `sink.emit` at **step 4**. **Seam correction (§seam):** spec 02 step 2 currently frames channel-access as independent of the step-1 decision — it MUST receive `owner_override` or L-12 re-opens for the owner | C-1 resolver (02, K8) |
| `DenialReason` / §2.7 outcome constants | imported from `sb/spec/outcomes.py` (spec 02's frozen leaf, built on the REAL `services/lifecycle/contracts.py:48-52`); this engine uses `ALLOWED`, `AUTHORITY`, `CHANNEL`; a denial → resolver maps to `BLOCKED`/`error_class=denied` | outcomes leaf (02) |
| audit-row semantics | the transparency audit fires through an `emit_audit_action`-equivalent seam in K7 with the `audit.action_recorded → server_logging` wiring intact (design-spec §1.3) | workflow/audit spine (K7) |
| compiler validates authority strings | the compiler P4 pass calls `validate_authority_ref(ref, reserved_capabilities)` and supplies the namespace-reserved capability set at compile time | compiler (01, K2/tools) |
| namespace capability reservation | `{subsystem}.{resource}.{action}` capabilities are K1-reserved with the reserved-prefix rule (`_internal.*/system.*/governance.*`, `subsystem_registry.py:7`) | namespace (K1) |
| Q-0227 + Q-0237(d) | ONE `authority_ref` (d, frozen); member-guilds-only scope (X-7 supersedes Q-0227's "any server", §8-a) | router (frozen) |

---

## 5. Data model + migration/index shape

**No new table.** The engine is stateless per request. It **reads** existing rows through the db
port: `capability_execution_overrides` (revoke overlay, via `governance.execution.get_capability_
override` semantics), the command-access policy (`get_command_access_policy`), and member/guild
state. The revoke overlay and command-access policy tables import **name-stable** (design-spec §5.2).
The transparency audit **writes no new schema**: it rides the existing audit table through
`emit_audit_action`; only the two extra Discord sinks (bot-log send, owner-DM digest) are additive
and stateless. The owner id is deploy config (env `BOT_OWNER_USER_ID`, `config.py:40`), not a table.

---

## 6. Restart & merge=deploy behavior

- **Stateless.** `resolve_authority` re-reads authority on every call — opening a panel is never
  authorization (design-spec §1.2 interaction-lifecycle invariant); every callback re-resolves. No
  in-memory authority state survives or needs to survive a restart.
- **Boot reconcile.** The revoke overlay + command-access policy caches are loaded lazily per guild
  (ported `execution.py:189-194` deterministic-refresh + TTL). A merge=deploy restart cold-loads
  them on first access; no reconcile step is required (authority is derived, never checkpointed).
- **Dual-instance overlap (LP-4).** Two instances resolving the same actor return the **same**
  verdict (pure function of guild rows + member perms + deploy owner id) — no split-brain. Admission
  drain (K5, resolver step 0) stops a draining instance *before* authority runs, so no
  double-authorization.
- **Transparency digest.** The owner-DM digest is batched; a restart flushes any pending batch at
  shutdown-drain or re-accumulates next boot (bounded, at-most-a-digest loss — acceptable for a
  transparency notice whose authoritative copy is already the bot-log audit row).

---

## 7. Architecture rules honored (INV / layer cites)

- **Layer table (design-spec §1.1).** `kernel/authority` imports `spec`, `namespace`,
  `observability`, discord, and the `TransparencySink` **port it defines**; it **must NOT** import
  `domain`, `manifest`, `kernel/interaction`, or `adapters` internals. The concrete sink lives in
  `adapters/discord`. `sb/spec/authority.py` is a **dependency-free leaf** (stdlib only) so the
  compiler (P4) and namespace import it with no cycle — honoring "the grammar is a dependency-free
  leaf."
- **Owner-override single source (ports `config.py:61`'s intent).** "Every authority seam routes its
  owner check through here so the rule lives in exactly one place" — this design *enforces* that: the
  ~11-16 scattered `is_platform_owner` authorization sites collapse to `owner_override_holds`, called
  once per resolution. An AST fence (generalizing `test_setup_delegate_actor_boundary`) asserts no
  other module performs an authorization on `is_platform_owner` directly.
- **Membership invariant preserved (INV — authority bound to the write target).** `capability.py:
  98-113` ports verbatim: a non-scripted actor (owner included) must be a member of `target_guild`;
  privilege in guild A never authorizes a write to guild B.
- **Audit fan-out preserved.** The transparency audit is emitted through `emit_audit_action` (the
  auditable seam), never a bypass; the `audit.action_recorded → server_logging` wiring is untouched.
- **DB via the port; settings via keys.** All policy reads go through the db port / typed accessors;
  no raw `pool.execute` in the engine; policy keys are `settings_keys` constants.
- **The no-skip fence (design-spec §1.2, spec 02 §7).** Every surface reaches a handler only through
  the K8 resolver, whose step 1 is this engine — so a domain can never forget the authority check.

---

## 8. Options → Decision → Why (forks I CLOSED)

| Fork | Options | Decision | Why |
|---|---|---|---|
| Channel-access placement | (a) fold into `resolve_authority` step 1 (one call, override covers all) · (b) keep it a K8 step-2 lane but thread `owner_override` from step 1 | **(b)** | Preserves spec 02's clean separation (authority=*who*, validate=*where/whether*) with minimal disruption — the ONLY change spec 02 needs is to pass `decision.owner_override` into its step-2 channel call. Owner-override is still computed **once** (step 1); it is merely *consumed* by two lanes. (a) would move a *where* concern into the *who* engine and duplicate spec 02's step. Either way I own the lane logic. **Flagged for the seam pass** (§seam). |
| Owner-override vs bootstrap bypass | (a) owner-override replaces the bootstrap bypass · (b) both, layered | **(b)** | The shipped bootstrap bypass (`:351`) also admits a **guild operator** (not owner) running a bootstrap command — owner-override (bot-owner only) would silently drop that. Keep both: owner-override (any command, owner) *plus* bootstrap bypass (bootstrap command, operator-or-owner). |
| One `authority_ref` discriminator | (a) a `lane` tag field beside the ref · (b) syntactic classification of the ref value | **(b)** | Q-0237(d) says authors fill ONE column; a second `lane` field re-introduces the two-field burden. Dotted-capability vs single-word-tier vs empty are total and non-overlapping, so the value alone classifies — and the compiler can prove exclusivity (§3.6). |
| Empty `authority_ref` meaning | (a) domain "user" (everyone) · (b) ADMIN floor | **(b)** | Ports the shipped invariant verbatim (`capability.py:27` "empty resolves to the floor, NOT no-auth"). A domain surface for everyone declares `authority_ref="user"` (a tier token), never empty — so empty is unambiguously the config-lane ADMIN floor. |
| `lane_would_deny` computation | (a) skip it, re-derive at audit time · (b) always compute the pure lane result | **(b)** | Cheap (the lane check is cache-backed), and computing it once inside `resolve_authority` keeps the transparency trigger a pure read of the decision — the alternative re-runs the lane check in the audit path (duplication + drift risk). |

---

## 9. Labeled deferrals (bounded by the capability corpus)

- **Per-capability tier matrix.** v1 keeps the single ADMINISTRATOR floor for every CAPABILITY-lane
  ref (`capability.py:48-51`). A future `{capability → required_tier}` lookup slots into §3.2's table
  with **zero** change to the resolver or the field. *Reason:* no subsystem in the 43-subsystem
  corpus + named amendments requests a non-admin capability tier today; adding the matrix now would
  be speculative.
- **Transparency-audit *sink* implementation** (bot-log channel id config, DM-digest cadence). The
  *contract* (trigger, payload, port) is designed here; the concrete channel wiring + digest window
  are the `adapters/discord` sink's, landing with the logging band (Phase-4 band 2, where server-log
  bindings exist). *Reason:* the sink depends on the logging subsystem's binding lane, ported later.
- **`trusted` tier resolution.** `TIERS` includes `trusted` (reserved, `visibility_rules.py:34` "for
  future trust/progression"); it resolves like `user` until a trust system exists. *Reason:* bounded
  to a named-but-unbuilt tier; the token is reserved so no re-grammar is needed when it lands.

---

## 10. Retirement map

| Row | Retires how | Status |
|---|---|---|
| **L-12** (owner-override gaps) | channel-access now consults owner tier — `resolve_channel_access` short-circuits on the once-computed `owner_override`, fixing the non-bootstrap deny (`command_access.py:351`); transparency audit designed (§3.5); ~11-16 seams → ONE `owner_override_holds`; member-guild scope preserved | **RETIRED (design)** — transparency *sink policy* owner-gated §8-c |
| **L-13 + T1-4** (authority two-lanes vs one-label) | ONE `authority_ref` + the §3.2 lane resolution table (spec 02 marked this "CONSUMED, not retired by me" — **this engine is what retires it**) | **RETIRED (design)** |
| **T2-10** (owner-override member-guild wording + transparency sink + no-log fallback) | member-guilds-only predicate (§3.3 step 2); `TransparencyAudit` sink contract (bot-log + server-log; fallback bot-log + owner DM digest) to buildable shape | **RETIRED (design)** — sink policy owner-gated §8-c |
| **X-7** (member-guilds-only) | `owner_override_holds` requires target-guild membership (ports `capability.py:98-113`); "any server" is not built | **RETIRED (design)** — scope confirm owner-gated §8-a |
| the 5 duplicated `_check_admin` | each → its spec's `authority_ref=""` (ADMIN floor) resolved through this engine; per-service function deleted | **RETIRED (design)** |
| slash/panel owner-blindness (`governance/resolver.py:223`) | the step-2 subsystem-visibility (K8) reads the once-computed `owner_override` instead of re-calling `is_platform_owner` | **RETIRED (design)** — seam note to spec 02 |

**V-3 accountability:** every row above is claimed and closed; nothing evaporates. Rows NOT mine:
L-4/L-5/T2-4/T2-9/T2-17 (the resolver seam, spec 02); L-22 (guild-blind nav); the settings-lane
retirements (§4 owner).

---

## 11. Build order (design-spec §9.1)

- **K6 — this engine.** Land `sb/spec/authority.py` (leaf: classifier + `validate_authority_ref` +
  tier order) first, then `kernel/authority/{owner,decision,resolve,channel_access,transparency}.py`;
  the concrete sink lands with the logging band (deferral §9).
- **Depends on:** K1 (namespace — capability reservation for `validate_authority_ref`), K3 (db port —
  revoke overlay + command-access policy reads), K5 (lifecycle — admission takes the lifecycle/DM
  legs shed from channel-access). Uses `DenialReason`/outcome constants from `sb/spec/outcomes.py`
  (landed at K7 per spec 02, but the *leaf* can precede — recommend landing `outcomes.py` at K6 so
  authority need not forward-reference K7).
- **Blocks:** **K7** (the four workflow lanes each call `resolve_authority` as their first "resolve
  authority" step, design-spec §1.3); **K8** (the resolver's step 1 + step-2 channel lane + step-4
  transparency emit); the compiler's **P4** authority-string check (can arm as soon as
  `validate_authority_ref` exists). Nothing in Phase 4 can authorize a mutation or dispatch without
  K6.

---

## Seam-pass notes (for the strand-1 consistency reviewer)

1. **Spec 02 (resolver) must thread `AuthorityDecision.owner_override` into its step-2
   `resolve_channel_access` call, and finalize the transparency trigger at step 4 over both the
   authority decision and the channel decision.** As written, spec 02 §3.2 step 2 treats channel-
   access as an independent enablement check — if it does not receive the once-computed override, the
   L-12 non-bootstrap deny re-opens for the owner. This is the one non-trivial cross-spec wiring.
2. **`DenialReason` lives in `sb/spec/outcomes.py`** (spec 02 §2 table), not `kernel/interaction/
   result.py` (spec 02 §3.6's code block is illustrative). K6 imports it from the leaf. K6 uses
   `CHANNEL` for both `CHANNEL_NOT_ALLOWED` and `COMMANDS_DISABLED` (distinguished by `detail`); if
   spec 02 prefers a distinct `COMMANDS_DISABLED` member, add it to the leaf — additive, no logic
   change here.
3. **`governance/resolver.py:223`** (subsystem-visibility owner check) is spec 02's step-2 concern,
   not K6's — but under "override once at top" it must consume the K6 `owner_override` flag rather
   than re-derive `is_platform_owner`. Noted so both specs agree the owner check exists in exactly
   one place.

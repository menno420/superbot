# Strand 3 · Cross-cutting concern ⑭ — Discord platform-governance (verification cap · intent approval · per-guild permission overrides)

> **Status:** `reference` — foundational design artifact (2026-07-04). **NOT SOURCE OF TRUTH** — a design contract; shipped source + the frozen upstream contracts win (Q-0120).

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B **design contract** for one never-surfaced
> foundational concern: the rebuild treats Discord's **externally-owned** governance gates as if they
> did not exist. Three gates bite: (1) an **unverified bot hard-caps at ~100 guilds** and the growth
> mission ("free for everyone") walks straight into it (FJ **L-17** / §4 #1); (2) past verification,
> **`message_content` approval is discretionary and routinely denied** — and the prefix-heavy rung-1/2
> ladder plus every passive on-message feature **requires** that intent, so denial darks a whole
> surface class (L-17); (3) guild admins' **per-command Server-Settings permission overrides are a
> second security-config DB the importer cannot see**, and a Q-0224 rename silently destroys it at
> cutover (FJ **L-23** / §4 #6). This dossier designs the **growth posture** (slash-first survivability
> + an intent-denial fallback ladder + a verification-application milestone) and the **CUT-2 permission
> census** (bot-token-**readable**) + a **rename→override-preservation map** + an **admin-notice**.
> **Precedence:** shipped source & merged PRs win (Q-0120); the five strand-1 specs +
> `shared-vocabulary.md` win for shapes they own; this dossier owns only the growth-posture leg + the
> census/preservation mechanics. It authors no `disbot/` and no `sb/` code.
>
> **A platform-contract correction baked into this revision:** Discord's command-permission write
> endpoint (`PUT …/commands/{id}/permissions`) is **not** performable with a bot token — it requires an
> OAuth2 **Bearer** token with the `applications.commands.permissions.update` scope from a user who can
> manage the guild. The **read** endpoint (`GET …/commands/permissions`) **is** bot-token-readable. So
> the census (read) is automatable; **automated carryover-replay (write) is not**. The override
> "carryover" is therefore redesigned as **id-stability preservation** (reuse the same Discord
> application id ⇒ un-renamed commands keep their ids ⇒ their overrides survive re-registration with
> **zero action**) **plus an admin-notice** for the renamed/dropped remainder — never an automated PUT.
> The application-id choice (same vs new) is the pivot and is owner-gated (**PG-5**).
>
> **Consumes (does NOT redefine):** the config/intent grammar `IntentSpec` + `INTENT_CONTRACT` +
> `assert_intents` + the `ConfigPosture` DEGRADE pattern (⑥ / spec 05 §3.1); `MetricSpec`/gauge for the
> guild-count signal (05 §3.3); the K1 namespace **surface** (PREFIX/SLASH) + the Q-0237(e)
> 100/25/1-nest slash-cap budget baked into `validate` (⑦.2 / L-14); the authority engine's
> pre-computed `member_tier` seam (②/RC-12). It **consumes** the frozen Q-0237(e)
> slash-common-+-prefix-long-tail split (NEVER reversed) as the substrate the survivability posture
> *completes* — the `essential` set **is** that slash-common set, no new classification judgment.

---

## 0. The gap in one paragraph (anti-pad — what is already designed vs what is not)

**Already designed / frozen — this dossier does NOT redesign (one line each):** spec 05 §3.1 already
builds the **intent rail** — `IntentSpec(name, privileged, required, approval_env)`, the two hardcoded
privileged intents declared (`message_content`/`members`, `bot1.py:77-78`), and `assert_intents`
gating on an `approval_env` BOOL in prod; the **100-top-level slash-cap** is already the Q-0237(e)
100/25/1-nest budget baked into K1's `validate` (L-14/T1-5); concern ⑩'s **class-13 N-3 probe** is the
standing *lens* that flags a permission-override loss forward. **The genuine, undesigned gaps** are
three: (a) spec 05 marks `message_content`/`members` **`required=True` and fail-closes** — so an intent
denial makes the bot **refuse to boot** (`FAILED_STARTUP`) instead of **degrading to slash-only**, the
opposite of survivability (spec 05 §9 *explicitly defers* "the intent-denial fallback ladder" to
"build-plan/owner" — this is that ladder); (b) **nothing** intersects the frozen slash-common set with
the intent-denial-survivable set, so a "free-for-everyone" mission has no mechanic guaranteeing its
*essential* surface survives a denial or a 100-guild wall; (c) guild admins' **per-command
Server-Settings permission overrides** are a real second config DB (Discord-side, bot-token-**readable**
but bot-token-**un-writable**) the importer's disposition report never sees — so a Q-0224 rename
silently resets that security config with **no census, no preservation, no notice**. (The code ships
`default_permissions` on **25 surfaces across 11 cogs**, but that is the count of *code-declared
defaults* — **admins can override any registered command**, so the census scope is *all* commands, not
those 25; §2.D.) Depth is spent on those three — the **survivability posture**, the **intent-denial
degrade**, and the **census/preservation/notice** — not on the intent rail spec 05 already shaped.

---

## 1. THREAT / FAILURE MODEL

Concrete scenarios, grounded in shipped source / frozen decisions / the Discord platform contract,
bounded by the capability corpus + the known Discord-bot governance model (no open-ended speculation).
"Blast radius" = who/what is harmed. Grouped by the three externally-owned gates.

### 1.A Growth-cap gate — the ~100-guild verification wall (L-17)

| # | Scenario (who / how) | Blast radius | Grounding |
|---|---|---|---|
| G-1 | The bot reaches **~100 guilds unverified**; Discord **silently blocks further guild joins server-side** — no in-bot event, joins just fail | Growth stops dead at the wall; a "free for everyone" mission is externally capped with **zero in-bot signal** | Discord platform contract (unverified bots cap at 100 guilds); FJ L-17 (growth gate never a design constraint) |
| G-2 | Verification is applied for **reactively at guild ~100** — but approval takes days–weeks, so growth is frozen for the whole review window with no lead time | Extended growth freeze; the milestone fired too late to be non-blocking | L-17 (verification is externally-owned, latency not controllable) |

### 1.B Intent-approval gate — `message_content` / `members` denial (L-17, the core)

| # | Scenario | Blast radius | Grounding |
|---|---|---|---|
| I-1 | Past verification, Discord **denies `message_content`** (discretionary, routinely denied). The bot connects (the intent flag is set in code) but **message content arrives empty** — every **prefix command** (`!cmd`), the **fuzzy/typo resolver**, **trigger words**, **NL-over-message**, and every **passive on-message stage** (xp · counting · chain · four_twenty · content-automod) silently sees empty text and **cannot function** | An **entire surface class goes dark at once** — the prefix long-tail + all passive features; on the rung-1/2 *prefix-heavy* ladder this is most of the product | `bot1.py:77` (`intents.message_content = True`, hardcoded); L-17 (prefix ladder collides with denial) |
| I-2 | Spec 05's `assert_intents` marks `message_content` **`required=True`** and **fail-closes in prod** → an unapproved intent makes the bot **`FAILED_STARTUP`** — it refuses to boot **even though it could serve every slash command perfectly** | The whole bot is dark instead of degrading to slash-only — the **worst** outcome of the two | spec 05 §3.1-3.2 (`required=True`, "missing approval in prod ⇒ ConfigError → StartupError") — the seam this dossier corrects |
| I-3 | Discord **denies `members`**; `on_member_join`/`on_member_remove`, the full member cache, and bulk-member features go dark | Welcome/leave flows + member-count features break | `bot1.py:78` (`intents.members = True`); note the **invoker's** `member_tier` on a **slash** command is unaffected — the INTERACTION_CREATE payload carries the invoking member + roles, so no privileged intent is needed (Discord platform fact; the pre-computed-tier *shape* is ②/RC-12) — only events/cache degrade |
| I-4 | The **271-command corpus** is registered as global slash and exceeds the **100 top-level cap** (or a group exceeds 25 subcommands / nests > 1) — Discord **silently truncates/rejects** the registration | Some commands never appear; a silent partial surface | Discord slash-cap (100 top-level / 25 per group / 1 nest); Q-0237(e)/L-14 budget — asserted here, not redesigned |

### 1.C Per-guild permission-override gate — the invisible second config DB (L-23)

| # | Scenario | Blast radius | Grounding |
|---|---|---|---|
| P-1 | A guild admin tightens a command in **Server Settings → Integrations** (e.g. `/purge` restricted to **@Staff**, only in **#mod-log**). A **Q-0224 rename** ships (`/purge` → `/mod purge`). The override is keyed on the **old command id**; renaming *deletes* the old id and *creates* a new one, so the new command **reverts to the code `default_permissions`** — silently **more permissive** (or reappears to `@everyone`) | The guild's **security config is silently lost at cutover**; a command an admin locked down becomes open — a **privilege-escalation-at-migration** class | `settings_cog.py:198`, `moderation_cog.py:96`, `ai_cog.py:578,775` (verified `default_permissions` surfaces); 25 occurrences / 11 cogs — but note **admins can override *any* command, not only these 25** |
| P-2 | The CUT-2 importer sweeps the **bot's own DB** and produces a coverage disposition report — but the per-command overrides live **in Discord**, not the bot DB, so the report **structurally never sees them** and cutover drops them | "Coverage proven" while a whole config DB is invisible — the exact "disposition proves coverage, never correctness" hole | FJ L-23 / §4 #6; concern ⑩ N-3 (the *lens*; this is the *fix*) |
| P-3 | A guild admin who spent effort tightening permissions gets **no notice** that a rename resets their config — discovers it only when an unauthorized member runs a now-open command. And because the override **write** is bot-token-un-writable, even a well-intentioned rebuild **cannot** silently re-apply it — the admin must | Silent trust breach with the guild admin; no *automatable* remediation path — only a notice + re-apply checklist | FJ §4 #9 (no user-facing change-comms mechanic); Discord platform contract (permission write needs admin OAuth2) — reinforced here |

---

## 2. DESIGN RESPONSE

Four artifacts. **(A)** the slash-first survivability posture + the `check_intent_survival` gate — to
**buildable depth**; **(B)** the intent-denial fallback ladder — the `IntentPosture` DEGRADE correction
to spec 05, to **buildable depth**; **(C)** the growth/verification milestone + an **active** lead-time
alert — to **buildable depth**; **(D)** the CUT-2 census + rename-override-preservation + admin-notice —
to **buildable depth**, corrected for the bot-token write limit.

### 2.A Slash-first survivability posture + `check_intent_survival` (buildable)

**The load-bearing platform fact** (why this is cheap and robust): a **slash / component / modal /
selector** interaction is delivered via `INTERACTION_CREATE` and carries the **invoking member + their
roles in the resolved payload** — it needs **neither `message_content` nor `members`** (a Discord
platform fact). So a slash-first surface **survives denial of both privileged intents** for its command
surface *and* for authority resolution: the adapter's pre-computed `member_tier` (the discord-free seam
*shape* is ②/RC-12) can be computed from that same interaction payload, so the invoker's tier resolves
under denial too. Only the *message-origin* and *event/cache* classes depend on a privileged intent:

| Capability class | Privileged intent needed | Under denial |
|---|---|---|
| Slash commands (invoker + roles from interaction payload) | **none** | **FULL — survives** |
| Component / modal / selector interactions (`PanelActionSpec`/`SelectorSpec`) | **none** | **FULL — survives** |
| Authority TIER-lane `member_tier` for the **invoker** (slash) | **none** (interaction payload; shape ②/RC-12) | **FULL — survives** |
| Prefix commands (`!cmd`), fuzzy/typo resolver, trigger words, NL-over-message | `message_content` | **DARK** → must have a slash/component twin if *essential* |
| Passive on-message (xp · counting · chain · four_twenty · content-automod) | `message_content` | **DARK** → degrade to disabled + admin notice |
| Member-join/leave (welcome), full member cache, presence | `members` | **DARK/partial** → degrade; invoker-tier unaffected |

**The survivability invariant (buildable):** *every capability classified `essential` must have at
least one entry point that is delivered via `INTERACTION_CREATE`* — i.e. a **SLASH** command
registration **or** a panel/component/selector entry point (`PanelActionSpec`/`SelectorSpec`). Such an
entry point needs no privileged intent, so intent denial can **never dark an essential capability** — it
only strips the prefix-convenience long-tail and the passive features.

- **`essential` ≡ the frozen Q-0237(e) slash-common set — no new classification judgment.** The
  slash-common set (grow-now, put under the 100-cap) *is by construction* the survives-denial set:
  Q-0237(e) already decided which capabilities carry the growth mission, and that **is** the
  mission-essential set. This dossier adds **no** new per-capability judgment; it only makes the
  slash-common ⇒ survives-denial intersection a **checked invariant**, not a hope. The one build task is
  to **materialize** the already-made slash-common decision as a manifest-readable tag (the **D-5
  slash-common tag**) so CI can read it — a *record* of an existing decision, not a new decision.
- **Where the tag lives (landing).** The slash-common tag is carried on each capability's **entry-point
  spec** — on `CommandSpec` for a command-rooted capability, on `PanelActionSpec`/`SelectorSpec` for a
  panel-rooted one — exactly as `authority_ref` is carried across its six spec types (②.1). A
  capability whose only non-privileged entry point is a component is therefore **visible** to the
  invariant (its tag lives on the `PanelActionSpec`), closing the "CommandSpec-only field can't see
  panel entry points" hole.
- **`check_intent_survival`** (CI gate, mirrors `check_metric_cardinality` / `check_cost_posture`):
  walk the manifest; for every capability whose **slash-common (essential) tag** is set, assert it has
  **≥1 entry-point registration** that is *interaction-delivered* — concretely, **either** a
  `CommandSpec` whose K1 namespace **`Surface == SLASH`** (⑦.2/§⑩; the K1 `Surface` enum is `{PREFIX,
  SLASH}` — this reads the SLASH member, it does **not** invent a `COMPONENT` value the frozen namespace
  lacks, RC-11) **or** any `PanelActionSpec`/`SelectorSpec` for that capability (these are
  *inherently* interaction-delivered and carry no namespace `Surface`, so their **presence** is the
  survivable signal). A slash-common capability whose only registrations are **PREFIX-surface
  `CommandSpec`s** is **CI-red**. Every input is already in the manifest — the K1 `Surface` per command
  registration, the spec *type* (CommandSpec vs Panel/Selector), and the D-5 slash-common tag. **No AST
  needed.**
- **Bound to the 100-cap** (asserts, does not redesign — G-2/I-4): `check_intent_survival`'s companion
  `check_slash_cap` asserts the registered global slash tree ≤ **100 top-level / 25 per group / 1
  nest** — the Q-0237(e) budget already computed in K1's `validate`. The survivability set ⊆ the
  under-cap slash set is the single composed assertion: *the essential surface both fits the cap and
  survives denial.*

### 2.B Intent-denial fallback ladder — the `IntentPosture` DEGRADE correction (buildable)

Spec 05's `assert_intents` fail-closes a prod bot on an unapproved privileged intent. That is correct
*intent* ("don't silently rely on an unapproved intent" — silent empty-content is a footgun) but the
wrong *action*: **refuse-to-boot is strictly worse than degrade-to-slash-only.** The fix turns "must not
**silently** rely" into "must **explicitly** degrade" — better than both fail-closed and
silent-degradation. Extend `IntentSpec` with a posture field mirroring the existing `ConfigPosture`:

```python
class IntentPosture(StrEnum):        # NEW — mirrors ConfigPosture (05 §3.1)
    REQUIRED = "required"            # denial ⇒ FAILED_STARTUP (reserved; none today)
    DEGRADE  = "degrade"             # denial ⇒ boot with THIS intent's capability class disabled + admin notice

@dataclass(frozen=True)
class IntentSpec:                     # 05 §3.1 shape + TWO fields (posture + degrades)
    name: str; privileged: bool; required: bool          # keep verbatim (frozen shape)
    approval_env: str | None = None                       # keep verbatim
    posture: IntentPosture = IntentPosture.DEGRADE        # NEW — the AUTHORITATIVE action-on-denial signal
    degrades: tuple[str, ...] = ()   # NEW — capability classes disabled on denial
                                     #   e.g. ("prefix","fuzzy","triggers","nl_message","passive_onmessage")

INTENT_CONTRACT = (
  IntentSpec("message_content", privileged=True, required=False,   # required True→False (survivability)
             approval_env="SB_INTENT_MSGCONTENT_OK", posture=IntentPosture.DEGRADE,
             degrades=("prefix","fuzzy","triggers","nl_message","passive_onmessage")),
  IntentSpec("members",         privileged=True, required=False,
             approval_env="SB_INTENT_MEMBERS_OK",    posture=IntentPosture.DEGRADE,
             degrades=("member_join","member_leave","member_cache")),
)
```

**Precedence — `posture` is authoritative, `required` is a shape-compat mirror (resolves the "two
overlapping necessity fields" hole).** `posture` is the **sole action-on-denial signal**; the frozen
`required: bool` is **kept only to preserve the 05 §3.1 shape** and **must satisfy the invariant
`required == (posture is IntentPosture.REQUIRED)`**. A `preflight`/`assert_intents` compile assertion
rejects any `INTENT_CONTRACT` entry where they disagree — `required=False + posture=REQUIRED` (or the
converse) is a **`ConfigError` → `StartupError`** (a config-compile error, never a silent
ambiguity). Today both privileged intents are `required=False, posture=DEGRADE` (consistent). This
mirrors the frozen `ConfigSpec`, which already carries `required` **and** `posture` side by side
(⑥.1) — the same pattern, with the disagreement made illegal by an enforced check rather than left
undefined.

**`assert_intents` (corrected behavior):** for a `DEGRADE` privileged intent whose `approval_env` is
absent/falsy in a non-`test` plane, **do not accrue a `ConfigError`** — record a
`DegradedCapability(intent, degrades)` marker on the boot result and **continue boot**. The composition
root reads the markers and, before gateway serve:

1. **`message_content` degraded** → **do not register the prefix listener / process_commands path**,
   the fuzzy resolver, trigger-word intake, NL-over-message, or the passive on-message pipeline stages.
   (Not-registering is cleaner than a per-dispatch denial and removes the empty-content footgun at the
   source.)
2. **`members` degraded** → skip `on_member_join`/`on_member_remove` wiring + bulk-member features;
   invoker `member_tier` still resolves from the interaction payload (shape ②/RC-12), so **authority is
   unaffected**.
3. Emit a **`DegradedCapability` operator notice** + surface the degrade set in `/lifecycle` diag so it
   is **explicit, never silent** (the fail-closed rule's real goal, achieved by degrade). **Dedup —
   once-per-state-change, not per-deploy (resolves the merge=deploy re-fire hole).** Persist the
   last-emitted degrade set in a small durable flag (a settings row keyed `platform.degrade_state`); on
   boot, emit the operator notice **only when the current degrade set differs from the persisted one**,
   then update the flag. So a redeploy (Railway auto-redeploys `worker` on every merge, minutes apart —
   Q-0193) while the *same* `message_content` denial persists **does not re-fire** — only a *change*
   (a new denial, or a denial cleared) fires. The `/lifecycle` diag is **always-current** (reads the
   live markers, not the latch), so the current state is never stale even when no notice fires.

This composes with the frozen vocab with **zero resolver-grammar change**: it rides the existing
`ConfigPosture=DEGRADE` pattern (the posture is defined in the 05 §3.1 enum; its shipped precedents are
`paragon → local-estimate` and `youtube → key_missing` — **not** AI keys, which are `DORMANT`), and a
message-origin surface simply **does not exist** on a message_content-degraded bot rather than returning
a new denial reason.

### 2.C Growth / verification milestone + an active lead-time alert (buildable)

The ~100-guild wall (G-1/G-2) has **no in-bot mechanic that raises it** — verification is the only
path, and it is externally-owned. The design response is a **posture + one *active* lead-time signal**:

| Leg | Mechanic | Depth |
|---|---|---|
| **Lead-time signal (active)** | a `guild_count` **gauge** `MetricSpec` (05 §3.3) **+ an in-bot threshold evaluator** that fires an operator notice at **~75 and ~90 guilds** — so the milestone fires with **weeks of lead time**, not reactively at 100 (G-2). The gauge alone is passive; the evaluator (below) is what makes the signal *fire* | buildable |
| **Verification milestone** | a **build-plan milestone** (not a growth gate): apply for verification when the lead-time signal fires; the application declares the `message_content` justification | decision-ready (roadmap horizon) |
| **Denial contingency** | if `message_content` approval is **denied**, the survivability posture (§2.A/§2.B) is **already the plan** — the bot degrades to slash-only, no rework | folds into §2.A/§2.B |

**The alert firing + delivery mechanic (resolves the "passive gauge, no firing" hole).** The `~75/~90`
alert is an **in-bot latched threshold check**, not a bare metric:

- **Evaluation site.** On `on_guild_join`/`GUILD_CREATE` (the only event that can move the count *up*
  toward the wall), read the current guild count and compare against the ordered thresholds
  `(75, 90)`. (A belt-and-braces re-check on the lifecycle heartbeat catches a count that crossed while
  the join listener was degraded, but the join event is the primary trigger.)
- **Fire-once latch (durable, restart-safe).** Each threshold fires **exactly once** across restarts:
  persist a per-threshold latch (a settings row keyed `platform.guildcap.<threshold>`, or an
  `IdempotencyKey` in namespace `platform.guildcap` — §④). When the count first crosses a threshold
  whose latch is unset, emit and set the latch. A redeploy while sitting at 82 guilds **does not
  re-fire** the 75 alert. (If the bot ever drops back below a threshold, the latch stays set — this is
  a one-way lead-time signal, not an oscillating alarm.)
- **Delivery.** The alert rides the **same operator-notice carrier as §2.B's `DegradedCapability`
  notice** (owner-log event + owner-DM digest via the logging band) — one operator-notice seam, two
  producers. Message: "Approaching the unverified-bot guild cap ({count}/100) — apply for verification
  now (lead time to the ~100 wall)."

**Why verification is a *milestone*, not a growth *gate* (the headline owner call, PG-1):** approval is
discretionary, externally-owned, and its latency is not controllable — you **cannot** make an
unreliable external decision a reliable internal gate without freezing growth on Discord's queue.
Slash-first survivability makes growth **robust to the outcome either way**: verified + approved ⇒ full
surface; verified + `message_content` denied ⇒ slash-only survives; verification pending ⇒ grow to the
wall on the slash surface. This is precisely what Q-0237(e)'s slash-common-+-prefix-long-tail split
**already implies** — §2 completes it.

### 2.D CUT-2 permission census + rename-override-preservation + admin-notice (buildable)

The overrides are **bot-token-readable** (`GET`) even though the bot DB can't see them — that read is
the visibility fix. But the override **write** (`PUT …/commands/{id}/permissions`) is **not**
performable with a bot token (it needs an admin OAuth2 Bearer with
`applications.commands.permissions.update`), so there is **no automated replay**. Preservation is
therefore achieved by **not changing the command id** (reuse the same Discord application — un-renamed
commands keep their ids ⇒ Discord keeps their overrides through re-registration) plus an **admin-notice**
for the renamed/dropped remainder. The same-vs-new application-id choice is the pivot — **PG-5**,
owner-gated; the mechanics below are written for the recommended **same-application-id** path and noted
where the new-application path differs.

| Mechanic | Shape | Closes |
|---|---|---|
| **Census** (`tools/permission_census.py`) | before cutover, for every guild call **`GET /applications/{app_id}/guilds/{guild_id}/commands/permissions`** (bot-token-readable) → snapshot `permission_census.json` = `{guild_id → [{command_id, command_name, [ {id, type∈role/user/channel, permission} ] }]}`. **The GET returns overrides for *every* command in that guild that has one — regardless of whether the code ships a `default_permissions`** — so the census is **not** bounded to the 25 code-declared defaults; it is a **per-guild sweep** (one GET per guild ⇒ bound = guild count). This makes the **second config DB visible** | **P-2** (invisible config DB) |
| **Rename→preservation map** | the Q-0224 renames are an **enumerable** set (the corpus rename table). Build `old_command_name → new_command_name` (+ regroup) and partition every censused override into **PRESERVED** (command un-renamed ⇒ same id survives re-registration under the same app ⇒ override kept **automatically, zero action**), **RENAMED** (id changes ⇒ override lost, **not** auto-restorable via bot token → admin-notice), or **DROPPED** (no successor → admin-notice) | **P-1** (rename destroys the override) |
| **Carry-verify** | after cutover re-registers the tree under the **same app id**, read back per-guild permissions (`GET`, bot-token-readable) and **assert every PRESERVED override is still present** — a copy-**fidelity** check on the un-renamed set (the FJ §4 #7 "correctness of the copy" gap). Any PRESERVED override that did **not** survive re-registration is a cutover failure (CI-shaped/blocking) | P-1/P-2 residue |
| **Admin-notice** | every **RENAMED** or **DROPPED** override (no auto-preserved successor) → a per-guild line in the **CUT-3 comms plan**: "these permission customizations were reset by the rename/removal of `<cmd>` and need re-applying in Server Settings → Integrations: …" (with the captured overlay so the admin can reproduce it exactly). This is the **only** available remediation for RENAMED/DROPPED — the write is admin-only | **P-3** (silent trust breach) |

- **Ordering (cutover step):** census (pre-freeze) → import → register new tree **under the same app
  id** → carry-verify PRESERVED → admin-notice for RENAMED/DROPPED → swap. The carry-verify slots into
  the CUT-3 cutover runbook exactly where the FJ §4 #7 "verify-import step between freeze and swap"
  belongs.
- **New-application-id path (PG-5 option b), if chosen:** **all** command ids change ⇒ **no** override
  is PRESERVED ⇒ **every** censused override becomes RENAMED/DROPPED ⇒ the admin-notice covers the
  *entire* census and PG-4 option (a) is effectively forced for all of them. This is why the
  same-app-id path is strongly recommended (PG-5): it turns "every admin re-applies everything" into
  "un-renamed overrides survive silently; only the enumerable rename/drop set needs a notice."
- **Automated restoration is out of reach with a bot token.** The *only* way to auto-re-apply a
  RENAMED/DROPPED override is a **per-guild admin OAuth2 grant** of the
  `applications.commands.permissions.update` scope, which itself requires each admin's action — barely
  better than a re-apply notice, and a large integration surface. It is **deferred + owner-gated** (§6;
  PG-4/PG-5), not designed here.

---

## 3. LANDING SITE (so no response can evaporate — V-3)

| Response | Lands exactly at | Cannot evaporate because |
|---|---|---|
| Slash-first survivability invariant + the D-5 slash-common (`essential`) tag | the tag lands on the capability's **entry-point spec** — `CommandSpec` **or** `PanelActionSpec`/`SelectorSpec` (mirrors `authority_ref`'s six-type placement) — **Gate-0 grammar** | a slash-common capability with only a PREFIX entry point is CI-red; a panel-only essential capability is visible via its Panel/Selector spec |
| `check_intent_survival` + `check_slash_cap` | `tools/` CI gates (mirror `check_metric_cardinality`); required-check set | an essential capability with no interaction-delivered entry point (SLASH CommandSpec or Panel/Selector), or a slash tree over 100/25/1, fails CI |
| `IntentPosture` DEGRADE + `degrades` + `required=False` + the `required == (posture==REQUIRED)` compile assertion on message_content/members | **spec 05 `sb/spec/config.py`** `IntentSpec` / `INTENT_CONTRACT` (corrects §3.1) — **seam correction** | `assert_intents` reads `posture`, enforces the mirror-invariant, and drives the boot markers |
| `assert_intents` degrade behavior + `DegradedCapability` markers + register-guard wiring + the `platform.degrade_state` once-per-change latch | **spec 05 §3.2** `assert_intents` + the composition root's serve-wiring; `/lifecycle` diag | boot records the marker; the prefix/passive path is not registered when degraded; the notice fires only on state change |
| `guild_count` gauge + the `on_guild_join` threshold evaluator + the `platform.guildcap.<t>` fire-once latch | **spec 05 §3.3** `MetricSpec` + `sb/adapters/http/health.py:/metrics` **for the gauge** + the composition root's join-listener/heartbeat **for the evaluator** + the §2.B operator-notice carrier **for delivery** | the alert is an active latched check that emits an operator notice with lead time, not a passive metric |
| Verification-application milestone + denial contingency | a **build-plan / roadmap horizon** (`docs/roadmap.md`) — posture, owner-gated (PG-1) | it is a named milestone the lead-time signal fires; the contingency is §2.A/§2.B |
| `tools/permission_census.py` + `permission_census.json` (per-guild, all-command sweep) | **CUT-2 stage gate** (the importer) — a bound pre-cutover deliverable | cutover cannot proceed past CUT-2 without the census (PG-3) |
| Rename→preservation partition + carry-verify of the PRESERVED set | **CUT-3 cutover runbook** step (between register-under-same-app and swap) | the runbook step is the FJ §4 #7 verify-import slot; carry-verify is bot-token-readable and CI-shaped |
| Admin-notice for RENAMED/DROPPED overrides | the **CUT-3 user-comms plan** (reinforces FJ §4 #9) | the comms plan enumerates the per-guild remainder — the only remediation for un-writable overrides |
| Same-vs-new application-id decision | **CUT-1/CUT-2 deployment identity** (`docs/roadmap.md` / cutover runbook) — owner-gated (PG-5) | the census/preservation scope is undefined until it is chosen; the runbook records the choice |

---

## 4. OWNER-GATED?

Per response: decide-able by design (recommended default, flagged) vs a genuine owner-only call
(options + recommendation only). Q-0237(a–g) are **frozen** (design AGAINST, never reverse); anything
that touches the frozen INTENT_CONTRACT or a product/growth/deployment call is **proposed, not
self-applied**.

| ID | Decision | 🔒? | Options | Recommendation |
|---|---|:--:|---|---|
| **PG-1** | **Growth posture** — slash-first ladder **with** intent-denial fallback vs pursue verification as a **hard milestone that gates growth** | 🔒 owner | (a) slash-first survivability + intent-denial fallback; verification pursued **in parallel** as a milestone, **not** a growth gate · (b) treat verification + `message_content` approval as a **hard gate** — freeze growth past ~75 guilds until approved | **(a)** — verification approval is **externally-owned + discretionary + latency-uncontrollable**; making it a growth gate freezes the mission on Discord's queue, and `message_content` denial is *routine*. Slash-first is robust to **every** outcome (approved ⇒ full; denied ⇒ slash-only survives; pending ⇒ grow on slash). It **completes** frozen Q-0237(e), which already chose slash-common-+-prefix-long-tail |
| **PG-2** | **`IntentPosture` DEGRADE** — message_content/members `required=False` + degrade-to-slash-only vs spec 05's `required=True` fail-closed | design (flagged) — but **touches frozen INTENT_CONTRACT** → propose | (a) DEGRADE (boot slash-only + explicit `DegradedCapability` + admin notice) · (b) keep fail-closed (`FAILED_STARTUP` on denial) | **(a)** — fail-closed darks the **whole** bot when it could serve every slash command; degrade preserves the fail-closed rule's real goal (no *silent* reliance) by making the degrade **explicit**. Route as a **spec 05 seam correction** (§3.1), owner-visible since it flips a frozen `required` field (and adds `posture`/`degrades` with an enforced `required == (posture==REQUIRED)` mirror) |
| **PG-3** | **CUT-2 census + preservation as a binding cutover gate** — no swap until the census is captured, the PRESERVED set is carry-verified, and the RENAMED/DROPPED remainder is enumerated into the admin-notice. (The gate is *visibility + verification + notice*, **not** automated replay — the write is bot-token-un-writable) | design (flagged) | binding gate vs advisory | **Binding** — a rename that silently opens a locked-down moderation command is a **privilege-escalation-at-migration**; the census is a bounded per-guild sweep and carry-verify is a bot-token read. *Decided by design (flagged).* The one thing it **cannot** bind is automated restoration of RENAMED/DROPPED overrides (platform-blocked) — those land in the notice |
| **PG-4** | **Un-preserved-override disposition** — RENAMED/DROPPED overrides that cannot be auto-restored (bot-token-un-writable) | 🔒 owner | (a) admin-notice + exact re-apply overlay (recommended) · (b) per-guild admin OAuth2 grant of `applications.commands.permissions.update` + automated PUT-replay (large surface; still needs each admin's action) · (c) silent drop | **(a)** — never silently reset a guild's security config; (b) is a heavy integration that is *barely* better than a notice because it still requires each admin to authorize. Lands in the CUT-3 comms plan (FJ §4 #9) |
| **PG-5** | **Deployment identity — same Discord application id vs a new application** at cutover | 🔒 owner | (a) **reuse the same application id** — un-renamed commands keep their ids ⇒ their overrides survive re-registration with zero action; only the enumerable rename/drop set needs a notice · (b) **new application** — every command id changes ⇒ **every** override is lost and (per the bot-token write limit) none is auto-restorable ⇒ the admin-notice covers the entire census | **(a)** — same-app-id shrinks the override-loss blast radius from "every override in every guild" to "only renamed/dropped commands," and is the difference between PG-3 being a light verify-gate vs a mass re-apply campaign. Only choose (b) if an ops constraint (token custody, org migration) forces a new application; then budget the full-census admin-notice |

---

## 5. RETIREMENT MAP (FJ L-rows / §4 gaps / owner-queue closed or advanced)

| Item | What it was | How this dossier closes / advances it |
|---|---|---|
| **L-17** (FJ §2, class 2 — **product/growth leg**) | "Discord platform-governance growth gate never treated as a design constraint … prefix-heavy ladder + free-for-everyone mission collide with the ~100-guild cap + discretionary `message_content` denial. Durable fix: name it in the BUILD-PLAN — **slash-first survivability posture, verification-application milestone, intent-denial fallback plan**" | **RETIRED (design):** §2.A slash-first survivability + `check_intent_survival`, §2.B the intent-denial fallback ladder (`IntentPosture` DEGRADE), §2.C the verification milestone + active lead-time signal — the **exact three** L-17's durable fix names. Spec 05 §10 already PARTIAL-retired the *intent-rail* leg (`IntentSpec`/`assert_intents`); **together = fully closed.** Growth call is owner-gated **PG-1** |
| **L-23** (FJ §2, class 2/9) | "Discord-side per-guild slash-permission overrides are a second config DB the import cannot see; ~10 surfaces ship `default_permissions`; Q-0224 renames silently destroy that security config at cutover. Durable fix: **CUT-2 Discord-side config census (API-readable) + a rename→permission-carryover map + admin-notice**" | **RETIRED (design):** §2.D the census (`GET …/commands/permissions`, bot-token-readable) + the rename→**preservation** partition (id-stability under the same app, **corrected** from the un-buildable automated `PUT`-replay — the write is admin-OAuth2-only) + carry-verify + the admin-notice — the durable fix, made platform-correct. Concern ⑩ carried L-23 only as the **class-13 N-3 *lens*** ("advanced, not claimed"); **this is the *mechanic* that lens asserts exists.** Binding-gate + deployment-identity calls are **PG-3/PG-4/PG-5** |
| **FJ §4 #1** (★ starred completeness miss) | "★ Discord platform-governance growth gate (L-17) — verification at ~75-100 guilds + discretionary `message_content` approval, vs a free-for-everyone mission on a prefix-heavy ladder" | **RETIRED (design):** same closure as L-17; the star graduates into a shipped survivability posture + fallback ladder + milestone |
| **FJ §4 #6** (★ starred completeness miss) | "★ Discord-side permission-override config invisible to the import (L-23)" | **RETIRED (design):** same closure as L-23; the census makes the invisible config DB visible + (for un-renamed commands under the same app) preserved |
| **New owner rows PG-1 / PG-4 / PG-5** | L-17's growth posture, L-23's un-preserved disposition, and the deployment-identity pivot had **no** owner-queue row in FJ §6 (both were §4 completeness misses; T1-5 slash-cap is the only adjacent frozen row, Q-0237(e)) | **GRADUATED** into owner-decidable rows with options + recommendation — the same §4-gap → owner-decision move concerns ⑩ (L-19→T-1) and ⑫ (#10/#12→CL-1/2/3) made. PG-5 is *new this revision*, surfaced by the bot-token write limit |
| **spec 05 §9 deferral** ("Slash-first survivability posture (L-17 product leg)") + **§10 L-17 PARTIAL** | spec 05 built the intent rail and **explicitly deferred** the product survivability posture + intent-denial fallback ladder to "build-plan/owner" | **CLAIMED:** this dossier **is** that deferred leg — §2.A-C. spec 05's PARTIAL L-17 becomes **RETIRED** in composition with this concern |

**Advanced but NOT claimed retired** (honest under V-3): **Q-0237(e)** (slash-cap policy) is a **frozen
decision designed *against*, not retired** — §2.A intersects the frozen slash-common set with the
survivable set; it does not re-decide the split. **FJ §4 #9** (user-comms mechanic) is *reinforced* by
the admin-notice (P-3) but its full CUT-3 comms plan is owned at Stage-3/CUT-3. **FJ §4 #7**
(verify-import between freeze and swap) is *reinforced* by carry-verify but owned at CUT-3.

---

## 6. DEFERRALS (labeled with reason)

| Deferral | Reason | Bound |
|---|---|---|
| The **verification-application content** (Discord's justification form, review back-and-forth) | An external process, not a design contract — the *milestone + active lead-time signal + contingency* are designed here; the application itself is owner/ops execution | Build-plan / owner (the milestone fires it) |
| The **census API-integration wiring** (concrete `GET …/commands/permissions` calls + rate-limit handling) | The *tool shape · census schema · per-guild sweep · preservation partition · carry-verify* are designed here; the concrete Discord-API GET integration is CUT-2 ops build (same tier as the importer) — **bot-token-readable** | CUT-2 census ops |
| **Automated restoration of RENAMED/DROPPED overrides** (the admin-OAuth2 `applications.commands.permissions.update` grant flow + PUT-replay) | The override **write** is **not** a bot-token operation; automating it needs a **per-guild admin OAuth2 grant** that still requires each admin's action — a large integration barely better than the re-apply notice. The *notice + exact overlay* is designed (P-3/PG-4); the OAuth2 flow is owner-gated, not designed here | PG-4 option (b) — owner-gated |
| The **passive-feature re-enable path** once `message_content` is later approved | Degrade-to-slash-only is designed; the reverse (approval granted after a degraded boot ⇒ re-register the prefix/passive surface) is a redeploy-picks-it-up case (`assert_intents` re-evaluates on the next boot; the `platform.degrade_state` latch fires a "capability restored" notice on the change) — no live hot-swap designed | Next merge=deploy (Q-0193) re-reads approval; no extra mechanic |
| The **richer growth-cap observability** (per-region joins, join-rate) beyond the `guild_count` gauge + latched ~75/90 alert | Those two signals give the milestone its lead time; a richer model is ops observability, not a foundational rail | ops observability (bounded) |
| The **full CUT-3 user-comms plan** (announcements, progressive ring) that the admin-notice slots into | The admin-notice *content* for un-preserved overrides is designed (P-3/PG-4); the surrounding comms plan is FJ §4 #9's own home | Stage-3 consolidation / CUT-3 (FJ §4 #9) |

No open-ended speculation — every threat is grounded in a shipped site (`bot1.py:76-78`,
`settings_cog.py:198`, `moderation_cog.py:96`, `ai_cog.py:578,775`), a frozen decision (Q-0237(e), spec
05 §3.1), or the Discord platform contract, and every deferral names its owning phase within the
corpus.

---

*Authored 2026-07-04 for the strand-3 cross-cutting concerns; revised same day to close a critic pass
(carryover-write authorization, census scope, the `check_intent_survival` surface vocabulary, the
`essential`≡slash-common reconciliation, the active alert mechanic, `required`/`posture` precedence, the
degrade-notice dedup, and two cite corrections). Consumes `shared-vocabulary.md` (⑥ config/intent
grammar, ⑦.2 namespace surface + slash-cap, ② `member_tier`/RC-12) + spec 05 (§3.1 `IntentSpec`/
`assert_intents`, §3.3 `MetricSpec`, §9 the deferred product leg) + concern ⑩ (class-13 N-3 lens).
Spot-verified this session against shipped source: `bot1.py:76-78` (`intents =
discord.Intents.default()` / `intents.message_content = True` / `intents.members = True`, the two
hardcoded privileged intents), `settings_cog.py:198` + `moderation_cog.py:96` + `ai_cog.py:578,775`
(`default_permissions` surfaces; **25 occurrences across 11 cogs — code-declared defaults, not the
census bound**). Discord platform facts relied on: an unverified bot caps at ~100 guilds; the
INTERACTION_CREATE payload carries the invoking member + roles (no privileged intent);
`GET …/commands/permissions` is **bot-token-readable** while `PUT …/commands/{id}/permissions` requires
an admin OAuth2 Bearer (`applications.commands.permissions.update`). `sb/` re-confirmed design-only (no
files). **NOT SOURCE OF TRUTH for runtime** — a design contract; source wins (Q-0120).*
</content>
</invoke>

# Strand 3 · Cross-cutting concern ⑭ — Discord platform-governance (verification cap · intent approval · per-guild permission overrides)

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
> census** (API-readable) + a **rename→permission-carryover map** + an **admin-notice**. **Precedence:**
> shipped source & merged PRs win (Q-0120); the five strand-1 specs + `shared-vocabulary.md` win for
> shapes they own; this dossier owns only the growth-posture leg + the census/carryover mechanics. It
> authors no `disbot/` and no `sb/` code.
>
> **Consumes (does NOT redefine):** the config/intent grammar `IntentSpec` + `INTENT_CONTRACT` +
> `assert_intents` + the `ConfigPosture` DEGRADE pattern (⑥ / spec 05 §3.1–3.2); `MetricSpec`/gauge for
> the guild-count signal (05 §3.3); the K1 namespace **surface** (PREFIX/SLASH) + the Q-0237(e)
> 100/25/1-nest slash-cap budget baked into `validate` (⑦.2 / L-14); the authority engine's
> `member_tier` seam — critically, `member_tier` for a **slash invoker is resolved from the interaction
> payload**, needing **no** privileged intent (②/RC-12). It **consumes** the frozen Q-0237(e)
> slash-common-+-prefix-long-tail split (NEVER reversed) as the substrate the survivability posture
> *completes*.

---

## 0. The gap in one paragraph (anti-pad — what is already designed vs what is not)

**Already designed / frozen — this dossier does NOT redesign (one line each):** spec 05 §3.1-3.2 already
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
*essential* surface survives a denial or a 100-guild wall; (c) the **~25 `default_permissions` surfaces
across 11 cogs** are a real second config DB (Discord-side, API-readable) the importer's disposition
report never sees — so a Q-0224 rename destroys guild admins' security config with **no census, no
carryover, no notice**. Depth is spent on those three — the **survivability posture**, the
**intent-denial degrade**, and the **census/carryover/notice** — not on the intent rail spec 05 already
shaped.

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
| I-3 | Discord **denies `members`**; `on_member_join`/`on_member_remove`, the full member cache, and bulk-member features go dark | Welcome/leave flows + member-count features break | `bot1.py:78` (`intents.members = True`); note the **invoker's** `member_tier` on a **slash** command is unaffected (resolved from the interaction payload, RC-12) — only events/cache degrade |
| I-4 | The **271-command corpus** is registered as global slash and exceeds the **100 top-level cap** (or a group exceeds 25 subcommands / nests > 1) — Discord **silently truncates/rejects** the registration | Some commands never appear; a silent partial surface | Discord slash-cap (100 top-level / 25 per group / 1 nest); Q-0237(e)/L-14 budget — asserted here, not redesigned |

### 1.C Per-guild permission-override gate — the invisible second config DB (L-23)

| # | Scenario | Blast radius | Grounding |
|---|---|---|---|
| P-1 | A guild admin tightens a command in **Server Settings → Integrations** (e.g. `/purge` restricted to **@Staff**, only in **#mod-log**). A **Q-0224 rename** ships (`/purge` → `/mod purge`). The override is keyed on the **old command id/name**; the new command **reverts to the code `default_permissions`** — silently **more permissive** (or reappears to `@everyone`) | The guild's **security config is silently lost at cutover**; a command an admin locked down becomes open — a **privilege-escalation-at-migration** class | `settings_cog.py:198`, `moderation_cog.py:96`, `ai_cog.py:578,775` (verified `default_permissions` surfaces); 25 occurrences / 11 cogs; L-23 |
| P-2 | The CUT-2 importer sweeps the **bot's own DB** and produces a coverage disposition report — but the per-command overrides live **in Discord**, not the bot DB, so the report **structurally never sees them** and cutover drops them | "Coverage proven" while a whole config DB is invisible — the exact "disposition proves coverage, never correctness" hole | FJ L-23 / §4 #6; concern ⑩ N-3 (the *lens*; this is the *fix*) |
| P-3 | A guild admin who spent effort tightening permissions gets **no notice** that a rename resets their config — discovers it only when an unauthorized member runs a now-open command | Silent trust breach with the guild admin; no remediation path | FJ §4 #9 (no user-facing change-comms mechanic) — reinforced here |

---

## 2. DESIGN RESPONSE

Four artifacts. **(A)** the slash-first survivability posture + the `check_intent_survival` gate — to
**buildable depth**; **(B)** the intent-denial fallback ladder — the `IntentPosture` DEGRADE correction
to spec 05, to **buildable depth**; **(C)** the growth/verification milestone — to **decision-ready
posture depth**; **(D)** the CUT-2 census + rename-carryover + admin-notice — to **buildable depth**.

### 2.A Slash-first survivability posture + `check_intent_survival` (buildable)

**The load-bearing platform fact** (why this is cheap and robust): a **slash / component / modal /
selector** interaction is delivered via `INTERACTION_CREATE` and carries the **invoking member + their
roles in the resolved payload** — it needs **neither `message_content` nor `members`**. So a
slash-first surface **survives denial of both privileged intents** for its command surface *and* for
authority resolution (`member_tier` of the invoker, RC-12). Only the *message-origin* and
*event/cache* classes depend on a privileged intent:

| Capability class | Privileged intent needed | Under denial |
|---|---|---|
| Slash commands (invoker + roles from interaction payload) | **none** | **FULL — survives** |
| Component / modal / selector interactions | **none** | **FULL — survives** |
| Authority TIER-lane `member_tier` for the **invoker** (slash) | **none** (payload) | **FULL — survives** |
| Prefix commands (`!cmd`), fuzzy/typo resolver, trigger words, NL-over-message | `message_content` | **DARK** → must have a slash/component twin if *essential* |
| Passive on-message (xp · counting · chain · four_twenty · content-automod) | `message_content` | **DARK** → degrade to disabled + admin notice |
| Member-join/leave (welcome), full member cache, presence | `members` | **DARK/partial** → degrade; invoker-tier unaffected |

**The survivability invariant (buildable):** *every capability classified `essential` must have at
least one entry point on a surface that does not depend on a privileged intent* (a slash or component
registration). Then intent denial can **never dark an essential capability** — it only strips the
prefix-convenience long-tail and the passive features.

- **The `essential` classification IS the frozen Q-0237(e) slash-common set** — no new judgment: the
  slash-common set (grow-now, put under the 100-cap) is *by construction* the survives-denial set. This
  dossier only makes the intersection a **checked invariant**, not a hope.
- **`check_intent_survival`** (CI gate, mirrors `check_metric_cardinality` / `check_cost_posture`):
  walk the manifest; for every capability in the **slash-common (essential) set**, assert ∃ a
  registration whose K1 **surface ∈ {SLASH, COMPONENT}** (not PREFIX-only). A message_content-only
  essential capability is **CI-red**. Input is already in the manifest — the K1 `Surface`
  (PREFIX/SLASH, ⑦.2/RC-11) per registration + the one new `essential: bool` (or reuse the D-5 triage
  tag). No AST needed.
- **Bound to the 100-cap** (asserts, does not redesign — G-2/I-4): `check_intent_survival`'s companion
  `check_slash_cap` asserts the registered global slash tree ≤ **100 top-level / 25 per group / 1
  nest** — the Q-0237(e) budget already computed in K1's `validate`. The survivability set ⊆ the
  under-cap slash set is the single composed assertion: *the essential surface both fits the cap and
  survives denial.*

### 2.B Intent-denial fallback ladder — the `IntentPosture` DEGRADE correction (buildable)

Spec 05's `assert_intents` fail-closes a prod bot on an unapproved privileged intent (§3.2). That is
correct *intent* ("don't silently rely on an unapproved intent" — silent empty-content is a footgun)
but the wrong *action*: **refuse-to-boot is strictly worse than degrade-to-slash-only.** The fix turns
"must not **silently** rely" into "must **explicitly** degrade" — better than both fail-closed and
silent-degradation. Extend `IntentSpec` with a posture field mirroring the existing `ConfigPosture`:

```python
class IntentPosture(StrEnum):        # NEW — mirrors ConfigPosture (05 §3.1)
    REQUIRED = "required"            # denial ⇒ FAILED_STARTUP (reserved; none today)
    DEGRADE  = "degrade"            # denial ⇒ boot with THIS intent's capability class disabled + admin notice

@dataclass(frozen=True)
class IntentSpec:                    # 05 §3.1 shape + one field
    name: str; privileged: bool; required: bool          # keep verbatim
    approval_env: str | None = None                       # keep verbatim
    posture: IntentPosture = IntentPosture.DEGRADE        # NEW — message_content/members BOTH degrade
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

**`assert_intents` (corrected behavior):** for a `DEGRADE` privileged intent whose `approval_env` is
absent/falsy in a non-`test` plane, **do not accrue a `ConfigError`** — record a
`DegradedCapability(intent, degrades)` marker on the boot result and **continue boot**. The composition
root reads the markers and, before gateway serve:

1. **`message_content` degraded** → **do not register the prefix listener / process_commands path**,
   the fuzzy resolver, trigger-word intake, NL-over-message, or the passive on-message pipeline stages.
   (Not-registering is cleaner than a per-dispatch denial and removes the empty-content footgun at the
   source.)
2. **`members` degraded** → skip `on_member_join`/`on_member_remove` wiring + bulk-member features;
   invoker `member_tier` still resolves from the interaction payload (RC-12), so **authority is
   unaffected**.
3. Emit a **`DegradedCapability` startup log** + surface it in `/lifecycle` diag and to the operator so
   the degrade is **explicit, never silent** (the fail-closed rule's real goal, achieved by degrade).

This composes with the frozen vocab with **zero resolver-grammar change**: it rides the existing
`ConfigPosture=DEGRADE` pattern (05 §3.2 already has DEGRADE for AI keys), and a message-origin surface
simply **does not exist** on a message_content-degraded bot rather than returning a new denial reason.

### 2.C Growth / verification milestone (decision-ready posture)

The ~100-guild wall (G-1/G-2) has **no in-bot mechanic that raises it** — verification is the only
path, and it is externally-owned. The design response is a **posture + one lead-time signal**:

| Leg | Mechanic | Depth |
|---|---|---|
| **Lead-time signal** | a `guild_count` **gauge** `MetricSpec` (05 §3.3) + an alert at **~75 and ~90 guilds** — so the milestone fires with **weeks of lead time**, not reactively at 100 (G-2) | buildable (MetricSpec + threshold) |
| **Verification milestone** | a **build-plan milestone** (not a growth gate): apply for verification when the lead-time signal fires; the application declares the `message_content` justification | decision-ready (roadmap horizon) |
| **Denial contingency** | if `message_content` approval is **denied**, the survivability posture (§2.A/§2.B) is **already the plan** — the bot degrades to slash-only, no rework | folds into §2.A/§2.B |

**Why verification is a *milestone*, not a growth *gate* (the headline owner call, PG-1):** approval is
discretionary, externally-owned, and its latency is not controllable — you **cannot** make an
unreliable external decision a reliable internal gate without freezing growth on Discord's queue.
Slash-first survivability makes growth **robust to the outcome either way**: verified + approved ⇒ full
surface; verified + `message_content` denied ⇒ slash-only survives; verification pending ⇒ grow to the
wall on the slash surface. This is precisely what Q-0237(e)'s slash-common-+-prefix-long-tail split
**already implies** — §2 completes it.

### 2.D CUT-2 permission census + rename-carryover + admin-notice (buildable)

The overrides are **API-readable** even though the bot DB can't see them — this is the whole fix:

| Mechanic | Shape | Closes |
|---|---|---|
| **Census** (`tools/permission_census.py`) | before cutover, for every guild call **`GET /applications/{app_id}/guilds/{guild_id}/commands/permissions`** → snapshot `permission_census.json` = `{guild_id → [{command_id, command_name, [ {id, type∈role/user/channel, permission} ] }]}`. This makes the **second config DB visible** | **P-2** (invisible config DB) |
| **Rename→carryover map** | the Q-0224 renames are an **enumerable** set (the corpus rename table). Build `old_command_name → new_command_name` (+ regroup). After cutover registers the new tree, for each carried override **`PUT /applications/{app_id}/guilds/{guild_id}/commands/{new_id}/permissions`** with the captured overlay | **P-1** (rename destroys the override) |
| **Carry-verify** | read-back the new-tree permissions per guild; assert the applied overlay matches the census (minus DROPPED commands) — a copy-**fidelity** check, not just coverage (the FJ §4 #7 "correctness of the copy" gap) | P-1/P-2 residue |
| **Admin-notice** | any override on a **DROPPED** command (no rename target) → a per-guild line in the **CUT-3 comms plan**: "these permission customizations need re-applying: …" | **P-3** (silent trust breach) |

- **Ordering (cutover step):** census (pre-freeze) → import → register new tree → **replay carryover**
  → carry-verify → admin-notice for the un-carryable remainder → swap. The carryover replay slots into
  the CUT-3 cutover runbook exactly where the FJ §4 #7 "verify-import step between freeze and swap"
  belongs.
- **Bounded:** only the **~25 surfaces / 11 cogs** that ship `default_permissions` can bear an override
  (Discord only lets admins customize commands that expose one), so the census target set is small and
  known — the tool is a bounded sweep, not an open-ended crawl.

---

## 3. LANDING SITE (so no response can evaporate — V-3)

| Response | Lands exactly at | Cannot evaporate because |
|---|---|---|
| Slash-first survivability invariant + `essential`/`intent_dependency` derived from K1 surface | **CommandSpec** grammar (`essential: bool`, or reuse the D-5 slash-common tag) — **Gate-0 grammar** | a message_content-only essential capability is CI-red |
| `check_intent_survival` + `check_slash_cap` | `tools/` CI gates (mirror `check_metric_cardinality`); required-check set | an essential capability with no non-privileged-intent entry point, or a slash tree over 100/25/1, fails CI |
| `IntentPosture` DEGRADE + `degrades` + `required=False` on message_content/members | **spec 05 `sb/spec/config.py`** `IntentSpec` / `INTENT_CONTRACT` (corrects §3.1) — **seam correction** | `assert_intents` reads the posture; the boot markers drive registration |
| `assert_intents` degrade behavior + `DegradedCapability` markers + register-guard wiring | **spec 05 §3.2** `assert_intents` + the composition root's serve-wiring; `/lifecycle` diag | boot records the marker; the prefix/passive path is not registered when degraded |
| `guild_count` gauge + ~75/90 alert thresholds | **spec 05 §3.3** `MetricSpec` + `sb/adapters/http/health.py:/metrics` | a declared metric family; the alert fires the milestone with lead time |
| Verification-application milestone + denial contingency | a **build-plan / roadmap horizon** (`docs/roadmap.md`) — posture, owner-gated (PG-1) | it is a named milestone the lead-time signal fires; the contingency is §2.A/§2.B |
| `tools/permission_census.py` + `permission_census.json` | **CUT-2 stage gate** (the importer) — a bound pre-cutover deliverable | cutover cannot proceed past CUT-2 without the census (PG-3) |
| Rename→carryover replay + carry-verify | **CUT-3 cutover runbook** step (between register-new-tree and swap) | the runbook step is the FJ §4 #7 verify-import slot; carry-verify is CI-shaped |
| Admin-notice for un-carryable overrides | the **CUT-3 user-comms plan** (reinforces FJ §4 #9) | the comms plan enumerates the per-guild remainder |

---

## 4. OWNER-GATED?

Per response: decide-able by design (recommended default, flagged) vs a genuine owner-only call
(options + recommendation only). Q-0237(a–g) are **frozen** (design AGAINST, never reverse); anything
that touches the frozen INTENT_CONTRACT or a product/growth call is **proposed, not self-applied**.

| ID | Decision | 🔒? | Options | Recommendation |
|---|---|:--:|---|---|
| **PG-1** | **Growth posture** — slash-first ladder **with** intent-denial fallback vs pursue verification as a **hard milestone that gates growth** | 🔒 owner | (a) slash-first survivability + intent-denial fallback; verification pursued **in parallel** as a milestone, **not** a growth gate · (b) treat verification + `message_content` approval as a **hard gate** — freeze growth past ~75 guilds until approved | **(a)** — verification approval is **externally-owned + discretionary + latency-uncontrollable**; making it a growth gate freezes the mission on Discord's queue, and `message_content` denial is *routine*. Slash-first is robust to **every** outcome (approved ⇒ full; denied ⇒ slash-only survives; pending ⇒ grow on slash). It **completes** frozen Q-0237(e), which already chose slash-common-+-prefix-long-tail |
| **PG-2** | **`IntentPosture` DEGRADE** — message_content/members `required=False` + degrade-to-slash-only vs spec 05's `required=True` fail-closed | design (flagged) — but **touches frozen INTENT_CONTRACT** → propose | (a) DEGRADE (boot slash-only + explicit `DegradedCapability` + admin notice) · (b) keep fail-closed (`FAILED_STARTUP` on denial) | **(a)** — fail-closed darks the **whole** bot when it could serve every slash command; degrade preserves the fail-closed rule's real goal (no *silent* reliance) by making the degrade **explicit**. Route as a **spec 05 seam correction** (§3.1-3.2), owner-visible since it flips a frozen `required` field |
| **PG-3** | **CUT-2 census + carryover as a binding cutover gate** (no swap until census captured + carryover replayed + carry-verified) | design (flagged) | binding gate vs advisory | **Binding** — a rename that silently opens a locked-down moderation command is a **privilege-escalation-at-migration**; the census is a bounded sweep of ~25 known surfaces. *Decided by design (flagged).* |
| **PG-4** | **Un-carryable-override disposition** — overrides on **DROPPED** commands | 🔒 owner | (a) admin-notice + re-apply guidance (recommended) · (b) best-effort map to the nearest surviving command · (c) silent drop | **(a)** — never silently reset a guild's security config; (b) risks mis-binding an admin's intent. Lands in the CUT-3 comms plan (FJ §4 #9) |

---

## 5. RETIREMENT MAP (FJ L-rows / §4 gaps / owner-queue closed or advanced)

| Item | What it was | How this dossier closes / advances it |
|---|---|---|
| **L-17** (FJ §2, class 2 — **product/growth leg**) | "Discord platform-governance growth gate never treated as a design constraint … prefix-heavy ladder + free-for-everyone mission collide with the ~100-guild cap + discretionary `message_content` denial. Durable fix: name it in the BUILD-PLAN — **slash-first survivability posture, verification-application milestone, intent-denial fallback plan**" | **RETIRED (design):** §2.A slash-first survivability + `check_intent_survival`, §2.B the intent-denial fallback ladder (`IntentPosture` DEGRADE), §2.C the verification milestone + lead-time signal — the **exact three** L-17's durable fix names. Spec 05 §10 already PARTIAL-retired the *intent-rail* leg (`IntentSpec`/`assert_intents`); **together = fully closed.** Growth call is owner-gated **PG-1** |
| **L-23** (FJ §2, class 2/9) | "Discord-side per-guild slash-permission overrides are a second config DB the import cannot see; ~10 surfaces ship `default_permissions`; Q-0224 renames silently destroy that security config at cutover. Durable fix: **CUT-2 Discord-side config census (API-readable) + a rename→permission-carryover map + admin-notice**" | **RETIRED (design):** §2.D the census (`GET …/commands/permissions`) + the rename→carryover replay (`PUT …/commands/{new_id}/permissions`) + carry-verify + the admin-notice — the exact durable fix. Concern ⑩ carried L-23 only as the **class-13 N-3 *lens*** ("advanced, not claimed"); **this is the *mechanic* that lens asserts exists.** Binding-gate call is **PG-3/PG-4** |
| **FJ §4 #1** (★ starred completeness miss) | "★ Discord platform-governance growth gate (L-17) — verification at ~75-100 guilds + discretionary `message_content` approval, vs a free-for-everyone mission on a prefix-heavy ladder" | **RETIRED (design):** same closure as L-17; the star graduates into a shipped survivability posture + fallback ladder + milestone |
| **FJ §4 #6** (★ starred completeness miss) | "★ Discord-side permission-override config invisible to the import (L-23)" | **RETIRED (design):** same closure as L-23; the census makes the invisible config DB visible + carried |
| **New owner rows PG-1 / PG-4** | L-17's growth posture + L-23's un-carryable disposition had **no** owner-queue row in FJ §6 (both were §4 completeness misses; T1-5 slash-cap is the only adjacent frozen row, Q-0237(e)) | **GRADUATED** into owner-decidable rows with options + recommendation — the same §4-gap → owner-decision move concerns ⑩ (L-19→T-1) and ⑫ (#10/#12→CL-1/2/3) made |
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
| The **verification-application content** (Discord's justification form, review back-and-forth) | An external process, not a design contract — the *milestone + lead-time signal + contingency* are designed here; the application itself is owner/ops execution | Build-plan / owner (the milestone fires it) |
| The **census/carryover API-integration wiring** (concrete `GET`/`PUT …/commands/permissions` calls + rate-limit handling) | The *tool shape · census schema · carryover map · replay ordering · carry-verify* are designed here; the concrete Discord-API integration is CUT-2/CUT-3 ops build (same tier as the importer) | CUT-2 census / CUT-3 replay ops |
| The **passive-feature re-enable path** once `message_content` is later approved | Degrade-to-slash-only is designed; the reverse (approval granted after a degraded boot ⇒ re-register the prefix/passive surface) is a redeploy-picks-it-up case (`assert_intents` re-evaluates on the next boot) — no live hot-swap designed | Next merge=deploy (Q-0193) re-reads approval; no extra mechanic |
| The **richer growth-cap observability** (per-region joins, join-rate) beyond the `guild_count` gauge + ~75/90 alert | Those two signals give the milestone its lead time; a richer model is ops observability, not a foundational rail | ops observability (bounded) |
| The **full CUT-3 user-comms plan** (announcements, progressive ring) that the admin-notice slots into | The admin-notice *content* for un-carryable overrides is designed (P-3/PG-4); the surrounding comms plan is FJ §4 #9's own home | Stage-3 consolidation / CUT-3 (FJ §4 #9) |

No open-ended speculation — every threat is grounded in a shipped site (`bot1.py:77-78`,
`settings_cog.py:198`, `moderation_cog.py:96`, `ai_cog.py:578,775`), a frozen decision (Q-0237(e), spec
05 §3.1-3.2), or the Discord platform contract, and every deferral names its owning phase within the
corpus.

---

*Authored 2026-07-04 for the strand-3 cross-cutting concerns. Consumes `shared-vocabulary.md`
(⑥ config/intent grammar, ⑦.2 namespace surface + slash-cap, ② `member_tier`/RC-12) + spec 05
(§3.1-3.2 `IntentSpec`/`assert_intents`, §3.3 `MetricSpec`, §9 the deferred product leg) + concern ⑩
(class-13 N-3 lens). Spot-verified this session against shipped source: `bot1.py:76-78` (`intents =
discord.Intents.default()` / `intents.message_content = True` / `intents.members = True`, the two
hardcoded privileged intents), `settings_cog.py:198` + `moderation_cog.py:96` +
`ai_cog.py:578,775` (`default_permissions` surfaces; 25 occurrences across 11 cogs). `sb/` re-confirmed
design-only (no files). **NOT SOURCE OF TRUTH for runtime** — a design contract; source wins (Q-0120).*

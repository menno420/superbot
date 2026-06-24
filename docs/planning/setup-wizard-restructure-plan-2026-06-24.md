# Setup-wizard restructure — buildable plan (one action per step, zero jargon)

> **Status:** `plan` — buildable spec (2026-06-24). Cross-check source before implementing;
> `docs/current-state.md` owns what is live. **Sector:** S1 — Bot product.
> **⚑ Owner-directed (chat, 2026-06-24):** *"the setup wizard has never been completely working as
> intended… we now have nearly all setup-worthy functions… make a good plan on what to include and which
> steps… thorough research and possibly run a simulator… easy and intuitive, no Discord/bot knowledge, no
> jargon, quick with buttons/dropdowns, each step is one complete action that actually completes a setup
> step properly."* This plan answers that directly. Plan-first: greenlight before build.
>
> **▶ Build progress:** not started. PR 1 = the jargon-free essentials spine; PR 2 = extras + health
> check; PR 3 = retire the dead/legacy sections.
>
> **Sim:** [`tools/sim/setup_wizard_sim.py`](../../tools/sim/setup_wizard_sim.py) (runnable) —
> models a non-technical owner walking the flow. Current standard-depth flow scores **~4% finish**
> (17 screens · 6 dead steps · 2 dead-ends · 44 jargon hits); the proposed essentials spine scores
> **~79% finish** (8 screens · 0 dead · 0 dead-ends · 0 jargon). Verdict: **PASS** on all four owner goals.
> Folio: [`settings-bindings-provisioning`](../subsystems/settings-bindings-provisioning.md).

## 1. Why

The wizard's *architecture* is sound (a clean section registry → draft → Final Review pipeline). Its
*experience* is not, and the owner has flagged it as P0 twice
([`cog-improvement-audit`](../ideas/cog-improvement-audit-2026-06-08.md) L115–121; the consolidation
audit §3.5). The research this session (three source sweeps) pins exactly why, and the simulator
quantifies it:

1. **~Half the steps complete no real action.** Of 17 standard-depth steps, **6 are dead**: `purpose`
   (metadata only), `server_scan` / `readiness` / `diagnostics` (read-only), `btd6` (announcement),
   `ai_setup` (link-only to `/aimenu`). The owner's words: *"about half the steps do nothing."* A wizard
   that makes you click through steps that change nothing destroys trust.
2. **Pervasive jargon.** The copy exposes internals: *"Each pick stages a `bind_channel` operation in the
   draft — nothing applies until Final review"*; *"The resolver walks thread → channel → category → guild
   → default"*; *"cog routing"*; *"set_role_threshold operation … through the audited role-automation
   seam."* A non-technical owner understands none of: **draft, operation, stage, bind/binding, Final
   review, cog, subsystem, scope, resolver, threshold, seam, pipeline, routing, tier, guild, preset.**
3. **Dead-ends on prerequisites.** `roles` says *"create roles first in Discord or via the role
   manager"* — the step cannot create what it configures. `channels` assumes channels exist. The user
   hits a wall mid-wizard.
4. **It's a long grid, not a guided path.** 17 buttons in a depth-filtered grid, no clear 1-2-3 order,
   read-only diagnostics interleaved with real config. People get lost and quit.
5. **Major setup-worthy features are missing entirely.** The inventory found **welcome/greetings,
   automod, security (raid/new-account), counters, starboard, image-mod, karma** are configurable but
   **not in the wizard** — yet *greeting newcomers* is the single most universal first-run task. (Tickets
   were just wired in via #1417; this plan extends that direction to the rest.)

The fix is not more sections — it is a **structure** built from four laws.

## 2. The four design laws (every decision below derives from these)

1. **One action per step, and it completes for real.** Every step in the main flow performs and
   **applies** one concrete configuration when you finish it. No metadata-only, no read-only, no
   link-out-and-come-back steps in the completion path. *(Direct lane — see §5.)*
2. **Zero jargon.** The operator never sees a Discord/bot internal term. The wizard speaks in outcomes
   ("Greet new members", "Block spam and bad links"), never mechanisms ("bind a channel", "stage an
   operation"). §4 is the rename table; a CI guard (§7, PR 1) keeps it honest.
3. **The bot creates what the step needs.** If a step needs a channel or role that doesn't exist, it
   **offers to create it** ("We can make a #welcome channel for you"). Never "go make it first." This
   kills both dead-ends.
4. **Short, linear, button-only.** A guided next → next spine of ~6 essentials, each a single screen with
   buttons/dropdowns (never "type an ID"), a clear **Skip**, and a visible "step 3 of 7". Diagnostics and
   the long tail move *out* of the spine into an optional menu.

## 3. Current → disposition (every existing section accounted for)

| Current section | Verdict | Becomes |
|---|---|---|
| `purpose` (metadata-only) | **Convert → actionable** | Opening step "What kind of server is this?" that *applies a starter preset* (now changes config). |
| `preset_select` | **Fold in** | Powers the opening step's starter set; not a standalone jargon step. |
| `server_scan`, `readiness`, `diagnostics`, `suggestions` | **Move out of flow** | Single optional **"Check my setup"** button (health check), not completion steps. |
| `channels` + `logging_presets` | **Merge + rename** | "Where should activity appear?" — pick/auto-create a log channel pair. |
| `roles` + `role_templates` | **Merge + rename + auto-create** | "Reward active members" — turn on levels + auto-create & grant roles (fixes the dead-end). |
| `moderation` | **Rename + simplify** | "Who are your moderators?" + safe mod defaults. |
| `cleanup` | **Demote → extras / advanced** | Powerful but jargon-heavy ("resolver walks scopes"); not a first-run essential. |
| `cog_routing` | **Demote → advanced** | Per-channel feature toggles are an advanced concern, not onboarding. |
| `identity` | **Remove from flow** | Demo-only (`warn_threshold`); subsumed by the moderation step. |
| `btd6`, `ai_setup` | **Remove from flow** | `btd6` = announcement (no settings yet); AI becomes an **extra** with a real in-wizard toggle, not a link-out. |
| `ticket` | **Keep** (already direct-apply, #1417) | "Set up a help desk" — already the right shape; light copy polish. |
| `final_review` | **Rename + reframe** | "All done" — for direct-apply essentials there is nothing pending to apply; it confirms + lists extras you skipped. (Draft/Final Review stays for the advanced bulk path.) |
| **NEW** | **Add** | "Greet new members" (welcome), "Block spam and bad links" (automod) — the missing universals. |

## 4. The rename table (jargon → plain language)

| Internal term (today's copy) | What the operator sees instead |
|---|---|
| draft / stage / operation / "stages a `set_setting` operation" | *(invisible — the step just says "Saved ✅")* |
| Final review / apply the draft | "All done" / "Save and finish" |
| bind / binding / bind a channel | "choose a channel" / "pick where this happens" |
| cog / subsystem / cog routing | "feature" / "turn features on or off" |
| scope / resolver walks / precedence | *(hidden; default to whole-server, "Advanced" reveals per-channel)* |
| threshold / set_role_threshold | "after this many days" / "at this level" |
| seam / pipeline / audited settings pipeline | *(never shown)* |
| tier (time tier / XP tier) | "by time in the server" / "by level" |
| guild | "server" |
| preset | "starter set" / "recommended setup" |

## 5. Step structure (the proposed wizard)

**Spine — the guided essentials (each applies immediately, direct lane):**

0. **What kind of server is this?** — Community · Gaming · Support · Creator · Just exploring. Applies a
   matching **starter set** of safe defaults right away (this is `purpose` made actionable + `preset`).
1. **Greet new members** *(NEW)* — turn on a welcome message; pick **or auto-create** the channel;
   optionally give newcomers a role. (`welcome` + entry role.)
2. **Who are your moderators?** — pick the role that can warn/remove people; set safe defaults
   (DM-on-action, require-reason). (`moderation` + governance mod role.)
3. **Block spam and bad links** *(NEW)* — one screen of toggles with sensible pre-filled limits.
   (`automod` spam/invites/caps/mentions.)
4. **Where should activity appear?** — a quick **multi-select** of logging types across **two channels**:
   a **moderation log** (always on → `mod_channel`) and an **activity log** (→ `events_channel`) for the
   ticked categories (members join/leave · role changes · message edits ⚠️). Pick or **auto-create** each
   (`#mod-log` / `#server-log`). **Shipped:** moderation-only first (`#1429`), then reworked to the
   two-channel multi-select (`#1432`, owner decision Q-0203 — "moderation only" was the first slice, not a
   cap). Full per-category routing stays in the advanced `!logging` UI.
5. **Reward active members** — turn on levels; optionally auto-grant a role as members stay & chat —
   **the bot creates the roles**. (`xp` + `roles` + `role_templates`, dead-end removed.)
6. **Set up a help desk** — let members open private support; pick who answers; bot makes the rest.
   (`ticket`, already direct-apply.)
7. **All done** — plain summary of what's on + a one-tap menu of extras you skipped.

**Off-spine (optional, reachable from "All done" or `/setup`, each still one real action):**

- **Extras menu** — Hall of Fame (`starboard`) · Live member counts (`counters`) · Raid & new-account
  protection (`security`) · Image filtering (`image_moderation`) · Thanks/Karma (`karma`) · AI helper
  (`ai`) · Reaction roles · Giveaways · **Replace another bot** (the
  [bot-migration assistant](bot-migration-assistant-plan-2026-06-24.md) — its natural home is here).
- **Advanced** — per-channel feature toggles (`cog_routing`), cleanup scopes (`cleanup`), the full draft
  → Final Review bulk editor (kept intact for power users).
- **Check my setup** — the read-only scan/readiness/diagnostics, as *one* optional health button.

The three depths collapse to: **the spine** (everyone) · **Extras** (opt-in) · **Advanced** (power
users). "Quick/standard/advanced" as the operator-facing choice goes away — the spine *is* quick.

## 6. The one architectural decision (surface, don't bury)

**Essentials apply per-step (direct lane), not via the deferred draft → Final Review batch.**
Law 1 ("each step completes for real") is in tension with today's draft model, where every step only
*stages* and nothing happens until Final Review. The ticket section already resolves this the right way —
it uses the **direct lane** and applies on confirm (`docs/ownership.md` § "Direct vs. draft mutation
lanes": focused / reversible / single-domain → direct). Each essential step is exactly that shape, so:

- **Spine steps → direct lane.** On confirm, the step writes through its audited service immediately and
  shows "Saved ✅". No draft, no Final Review jargon, true per-step completion.
- **Advanced bulk editor → keeps the draft → Final Review pipeline** unchanged (compound/multi-setting/
  generated changes are its correct use).

This is consistent with the canonical lane rule and is the change that makes Law 1 real. It is the one
decision with architectural weight → called out as open question Q-A below.

## 7. PR breakdown (≤3 PRs)

- **PR 1a — the jargon guard (SHIPPED 2026-06-24, ahead of the spine):** `scripts/check_setup_copy.py`
  (Q-0105 warn-first disposable tool) + ratchet invariant test
  (`tests/unit/invariants/test_setup_copy_jargon.py`). It AST-scans operator-facing strings (UI kwargs +
  `send`/`followup` args, excluding docstrings/logs) in `disbot/views/setup/` for the §4 banned list. It
  is independent of Q-A, so it shipped first. **Measured ground-truth baseline: 207 jargon strings across
  33 files** (top offenders: `stage`×66, `guild`×58, `final review`×46, `operation`×40) — far above the
  *modelled* 44 in the sim, which only counted the standard-depth spine. The ratchet tolerates the
  existing copy but fails on any *new* jargon or any new dirty setup file; the spine rewrite drives the
  count to zero, then the guard graduates to `--strict` in CI. This is Law 2's durable enforcement.
- **PR 1b — plain-language sweep 1: `guild → server` (SHIPPED 2026-06-24):** reworded the 53 operator-facing
  strings containing "guild" — the bulk being the uniform *"X requires a guild context."* error
  collapsed to *"This can only be used in a server."* (which also clears co-located jargon like "Final
  review"/"Binding"). Zero-risk string-only edits, no behaviour change. **Baseline 207 → 154** (4
  sections went fully clean: server_scan, readiness, suggestions, ticket); ratchet lowered in lock-step.
  This is the Q-A-independent half of the copy cleanup; the structural jargon (`stage`/`draft`/`final
  review`/`operation`, the remaining ~154) is reworded *as part of* the spine rebuild (PR 1), since its
  wording depends on the direct-apply vs. Final-Review decision (Q-A).
- **PR 1 — the essentials spine (the headline). Owner greenlit + Q-A answered "save each step
  instantly" (direct lane), 2026-06-24.** Installment 1 SHIPPED: `disbot/views/setup/essential_setup.py`
  — a new **linear, plain-language, direct-apply** flow (`EssentialFlow` + per-step `BaseView`s with
  Save/Skip/Back + "Step X of N"), opened by a new **`!quicksetup` / `/quicksetup`** cog
  (`cogs/quicksetup_cog.py`, admin-gated, server-only). **Four steps live end-to-end** (each writes
  through its audited service immediately — no draft, no Final Review — plus an **All-done summary**):
  **Greet new members** (welcome) `#1425` · **Set your moderators** (moderation) `#1425` · **Block spam
  and bad links** (automod toggles) `#1427` · **Set up a help desk** (`ticket_mutation`) `#1427`.
  Additive: the old wizard is untouched (retired in PR 3). Jargon-clean (guard: the new file adds 0
  findings). **Remaining steps are mechanical follow-ons on the exact same pattern — append a `_StepView`
  subclass to `EssentialFlow._steps` + a test; no new cog/command/artifact, so no registration fan-out:**
  - **Choose a log channel** *(SHIPPED 2026-06-24 — `#1429` moderation-only, then reworked in `#1432`)* —
    binding writes via `BindingMutationPipeline` + auto-create via `ChannelLifecycleService.create_channels`
    (⚠ both on the no-top-level-import list — **lazy-imported** inside the step, like `_set` does for
    settings). **Final scope = two-channel + multi-select (owner decision Q-0203, superseding the Q-0202
    moderation-only answer):** a quick multi-select of activity types (members join/leave + role changes on
    by default; message edits/deletions ⚠️ off by default) across a **moderation log** (always on →
    `logging.mod_channel`) and an **activity log** (→ `logging.events_channel`). On Save: `logging.enabled`,
    bind `mod_channel`, set the `*_enabled` flags per the multi-select, bind `events_channel` when any
    activity is on. **Leave a channel empty → auto-create** `#mod-log` / `#server-log` (one-tap defaults).
  - **Reward activity** — the `xp` enable toggle is trivial via `_set`; the role-threshold sub-step
    **needs a small new direct-apply role-threshold service** (the one genuine gap — no direct-apply path
    exists today) + `RoleLifecycleService.create_role` for auto-create.
  - **Server-type starter preset** (step 0) — **needs a direct-apply preset path** (presets are
    draft-only today); design decision before building.
- **PR 2 — extras + health check:** the **Extras menu** (each existing config surface as a one-action
  step: starboard, counters, security, image-mod, karma, AI, reaction roles, giveaways) + the single
  **"Check my setup"** health button (folds in scan/readiness/diagnostics/suggestions). Wires the
  bot-migration assistant in as the "Replace another bot" extra once that plan ships.
- **PR 3 — retire the dead/legacy sections:** delete or demote `purpose`(old), `identity`, `btd6`,
  `ai_setup`(link-only), `server_scan`/`readiness`/`diagnostics`/`suggestions` as *standalone spine
  sections* (their function now lives in step 0 / Check-my-setup), and move `cog_routing` + `cleanup`
  under **Advanced**. Keep the draft → Final Review engine for the Advanced bulk path. This is the
  "strip the steps that do nothing" the owner asked for — done last so the new spine is proven first.

## 8. Arch & contracts checklist (binding)

- Spine steps write through each domain's **audited service** (`welcome_config`, `moderation`/governance,
  `automod_config`, `server_logging_config`, xp/role services, `ticket_mutation`) — never `pool.execute`
  outside `utils/db/`; emit `audit.action_recorded` for each applied change (`runtime_contracts.md` §9).
- Auto-create channels/roles go through the **provisioning** lane (`create_channel`/`create_managed_role`
  semantics), guild-keyed → `guild_lifecycle.py` teardown where applicable.
- Views extend `BaseView`; **re-check operator authority at callback time** (discord-views rule — opening
  the wizard ≠ authorizing a later apply). No cog import from views; no view import from services.
- New guard `check_setup_copy.py` runs in `code-quality` (advisory→ratchet): operator-facing setup
  strings contain no §4 banned term.
- Tests: each spine step applies its config via a stubbed service + emits audit; auto-create path creates
  then binds; skip path writes nothing; the "All done" summary reflects exactly what was applied; jargon
  guard catches a planted banned term. Mirror `tests/unit/views/setup/` + the section tests.

## 9. Verification (before each PR)

```bash
python3.10 tools/sim/setup_wizard_sim.py            # re-run; proposed must stay PASS
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_docs.py --strict
```

## 10. Open questions for the owner

- **Q-A (the one with weight):** confirm **essentials apply per-step immediately** (direct lane), so each
  step truly "completes" — rather than staging into the draft for a Final Review at the end. (Plan
  strongly recommends direct-apply; it's what makes "one complete action per step" real, and it matches
  the existing ticket section + the canonical lane rule.)
- **Q-B:** is the **6-step spine** (0–6 above) the right essentials set, or do you want a different
  cut — e.g. tickets as an extra rather than a spine step, or reaction-roles promoted into the spine?
- **Q-C — ANSWERED (owner, 2026-06-24): auto-apply safe defaults.** When someone picks a server type
  (step 0), it instantly switches on a curated, **reversible** bundle of defaults — fastest, nothing
  irreversible. (Not built this PR; settles the step-0 preset follow-on.)
- **Q-D — ANSWERED (owner, 2026-06-24): plain-language names.** Auto-created channels/roles use the
  short, friendly §4 wording (`#mod-log` / `#server-log`, "Level 10", "Regular") rather than the longer
  `bot-`-prefixed `suggested_name` convention. (Log step `#1429` creates `#mod-log` accordingly.)
- **Q-E — ANSWERED (owner, 2026-06-24): keep but REWORK.** Keep the Advanced bulk editor for power
  users, but **rework it — "currently most of it does not do anything."** So PR 3 is not just "demote
  cog_routing/cleanup under Advanced"; it must audit the draft → Final Review editor and either wire up
  or strip its dead actions. (Was: "keep as-is"; the owner sharpened it to keep-and-fix.)

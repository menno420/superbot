# Consolidated productive-session plan — 2026-06-09

> **Status:** `plan` — **reasoning + verification record, NOT the execution pointer.**
> The execution pointer is the multi-lane scoreboard
> ([`multi-lane-execution-plan-2026-06-09.md`](multi-lane-execution-plan-2026-06-09.md));
> this doc records *why* the queue looks the way it does, reconciles the 2026-06-09
> audit burst (#625/#627/#628) against live truth, and hands the next implementation
> session its prompt. Source-verified at main HEAD `b0c2d07` (the #625 merge).
> Source and merged PRs win over this file.
> **Last updated:** 2026-06-09.

## §1 Verification snapshot

Verified live (GitHub API) + at source this session — not inherited from docs:

- **Branch/HEAD:** session branch is at `b0c2d07` = **live `main` HEAD** (#625's merge
  commit is the final HEAD; #628's content was folded in before it). **Zero open PRs**
  (checked twice: session start + pre-push).
- **Merged chain (2026-06-09):** #621 (repo review) → #622 (gate-lifting interview:
  Q-0028–33/36/44/45 answered, Q-0046–51 recorded) → #620 (062-storage test) → #623
  (fun/ease brainstorm + pets plan) → #624 (mining Workshop + durability + live hub
  overview; Q-0046–48 routed) → #626 (`scripts/new_subsystem.py` scaffold + Community
  Spotlight registered) → #627 (help customization audit) → #628 (agent-memory review)
  → #625 (settings centralization audit).
- **Router (final numbering after the §9 collision renumbers):** Q-0044–Q-0054
  **answered** (incl. Q-0045 tier-input *option b*, Q-0047/Q-0048 gate lifts, Q-0052
  draft-PR-at-first-push, Q-0054 durability). Q-0060–Q-0062 answered (#628).
  *Post-merge update (same evening, two structured-choices rounds):* **Q-0055–Q-0059
  and Q-0063–Q-0065 all answered** — every pick was the recommended option except
  **Q-0059 = embed builder** (owner chose the richest Help-Home format → structured
  overlay storage, not a scalar). See §7. Next free number: **Q-0066**.
- **Source confirmations (file:line checked on disk):**
  - Settings hub lists all **28 non-internal SUBSYSTEMS** and silently truncates at the
    Discord 25-option cap — `disbot/views/settings/hub.py:44` + `:136`. Scalar stack is
    healthy: 36 `SettingSpec`s across 9 subsystems, 51 `settings_keys` constants.
  - The **scalar→typed AI projection dual-write seam is real**:
    `disbot/services/settings_mutation.py:335` calls
    `ai_policy_mutation.project_from_legacy_settings` post-write (best-effort, tested) —
    Q-0063 is a legitimate open ownership question, *not* doc rot.
  - `disbot/services/access_projection.py` has **zero runtime consumers** (grep-verified:
    only the module's own internal lines match in `disbot/`) — Lane 2 is its first consumer.
  - Community Spotlight **is registered** (`disbot/utils/subsystem_registry.py:360-382`,
    `parent_hub="community"`) and `scripts/new_subsystem.py` **exists** — #626 fully intact.
  - Help routes apply **inconsistent filters** per surface (`disbot/cogs/help_cog.py`,
    `disbot/cogs/help/route.py`) and Help does **not** consume `access_projection`.
  - `.github/workflows/` has **no** btd6 refresh workflow (Lane 5 genuinely undone);
    orchestration Phases 1–3 and answerability Phases 1A/1B/2 are in source, Phase 4 /
    Phase 3 code is **absent** (Lanes 3/4 genuinely open).
- **State docs agree on the pointer** (current-state ▶ Next action → scoreboard; roadmap
  defers to current-state) but carried stale merge/status hedges — all reconciled in this
  PR (§6).
- **Cross-agent corrections** (scouts vs source — source won): the scaffold *does* exist;
  the dual-write *is* real (one scout saw only the read-side
  `ai_config_projection_service`, which is genuinely non-mutating and AST-pinned —
  both seams exist and are different things); Workshop+durability attribution **#624 is
  correct** (PR title verified).
- *Not verified this session:* no bot boot, no runtime test suite (docs-only session —
  doc checks + doc-pin tests only).

## §2 Executive recommendation

**Next implementation session = scoreboard Lane 2 (Adaptive P1B remainder).** Rationale:
the lane order 1–6 is an owner decision (gate-lifting interview) and Lane 2 was unblocked
*by that same interview* (Q-0045 → governance tier-input, Q-0036 → Claude-drafted
denial copy); it is also the dependency head — it gives `access_projection` its first real
consumer (shipped service, zero consumers = live architectural debt), and P1C Help
Preview, the `help_advertises_locked` drift surface, and the future help-overlay lane all
stack on it. Full prompt: **§8**.

**Pointer architecture: extend, don't supersede.** The scoreboard remains the one
canonical "what do I execute next" pointer (memory-review convention). This PR appends
two audit-sourced lanes at the end — **Lane 7 = Settings Phase 0+1** (discovery/display
correctness) and **Lane 8 = Help bounded doc/test reconciliation** — explicitly marked
*agent-recommended, not owner-ordered*, with **Q-0065** as the owner's zero-cost lever to
pull Lane 7 forward (the 25-option truncation is the only operator-visible *defect* in
the queue; everything else is enhancement).

**What NOT to do yet** (all gates intact, none lifted by this plan):
- No generic configuration god-object; Settings stays a **discovery/navigation surface
  over separate mutation owners** (scalar / bindings / provisioning / governance /
  command-access / role / AI policy / rollout / participation / runtime-game state).
- Help-overlay storage/editors are **no longer question-gated** — the full batch was
  answered 2026-06-09 (display-only hide · Help-only names · panel-local order ·
  custom+default in admin · **embed-builder Home message**) — but stay **sequenced**:
  after Lane 8's characterization net and the HLP-2 projection seam, not before.
- No new projected AI keys (**frozen by the Q-0063 answer, 2026-06-09**: converge
  gradually — typed-panel convergence planned at settings Phase 3); no AI writes /
  external calls / cost-bearing behavior / new AI UI without per-exposure lift (Q-0048
  posture: only read-only + deterministic + tiered tools have the standing lift).
- BTD6 extraction/cutover stays gated (ADR-006 lane discipline; `--all` is not
  auto-safe); the refresh workflow is approved **only** as `workflow_dispatch` (Q-0049 —
  the cron sketch in the pipeline plan is annotated as not-approved residue).
- Community Spotlight registration is **done** (#626) — do not re-plan it.

**What this PR itself changed:** this doc; scoreboard tail repointed + Lanes 7/8
appended; current-state hedges reconciled (#620/#624/#626, Spotlight, stamp);
settings-roadmap banner extended (S7–S12 sequencing → audit §11); post-merge annotations
in both audits; "(this session)" markers dated in 3 AI docs; BTD6 cron residue
annotated; router gains Q-0065; session log with context-delta.

## §3 Area-grouped plan

Item IDs are greppable and referenced (not restated) by §4/§5/§7.
Priorities: **[C]**ritical blocker · **[I]**mportant next · **[CL]**eanup ·
**[F]**uture opportunity · **[G]**ated/off-limits.

### Adaptive Setup / Access / Help Preview

Shipped: P0 complete; P1A `access_projection` (#589); P0C seam conversion + P1B
`routing_access_conflict` (#592); Q-0045/Q-0036/Q-0032 all answered.

- **ADP-1 [I]** — **Lane 2: P1B remainder** — governance tier-input (Q-0045 option b) +
  `help_advertises_locked` drift provider + denial-copy **draft** (PR-body review only).
  The next implementation session; full spec in §5/§8.
- **ADP-2 [I]** — **P1C: Access Map + Help Preview** as staff-hub subpanels, no new
  command names (Q-0032). Builds directly on ADP-1's tier-input; next adaptive slice
  after Lane 2 (not yet a scoreboard lane — promote when Lane 2 lands).
- **ADP-3 [G]** — Wiring denial copy (`LockedReason.safe_text`) into live denial paths.
  Gated on the maintainer's read-through of ADP-1's draft table (Q-0036: nothing
  user-facing ships unseen).
- **ADP-4** — *(debt note, resolved by ADP-1)* `access_projection` currently has zero
  consumers; Lane 2 closes this.

### Settings / Bindings / Provisioning

Shipped/true: scalar stack healthy (§1); three-lane mutation ownership intact; the
audit's real finding is **discovery/display, not a missing settings system**.

- **SET-1 [I]** — **Lane 7 (appended): settings audit Phases 0+1** — Phase 0
  reconciliation/test-targets folded in as the session's first checklist item, then
  discovery/display correctness: actionable-groups-only catalogue (editable scalar ∨
  binding editor ∨ provisionable flow ∨ registered domain panel), >25 reachability
  (pagination/categories), empty-page exclusion, actor-aware availability.
  `disbot/views/settings/hub.py` + a catalogue helper + hub tests. Not blocked by any
  open question. Position ratifiable via **Q-0065**.
- **SET-2 [G→F]** — Phase 2 declaration/coverage completion (missing schemas/bindings/
  domain-panel registrations for *verified real* config; BTD6/proof/logging/economy
  pointer classification). Partially gated: **Q-0064** for the BTD6 pointers; mining is
  an active lane; AI policy UI stays gated.
- **SET-3 [F]** — Phase 3 duplicate/hardcoded/command-only path elimination + AI
  projection convergence. **Direction decided (Q-0063, 2026-06-09): converge
  gradually** — keep + diagnose the tested seven-key projection, projected-key set
  frozen, typed-panel convergence planned at this phase; AI UI exposure stays
  per-case gated. Sequenced after Lane 7.
- **SET-4 [F]** — Phase 4 structured editors (group/order/advanced/reset metadata,
  guided ranges, presets, member/multi-select; less free text).
- **SET-5 [F]** — Phase 5 Setup/Settings convergence (shared catalogue/definition
  projection; Setup consumes definitions; draft/preview/final-review lane preserved).
  High risk — needs its own planning session first.
- **SET-6** — *(standing constraint)* the dual-write seam (`settings_mutation.py:335`)
  is tested and stays as-is pending Q-0063; treat "projection failed" diagnostics as
  the seam's canary.
- **SET-7 [CL]** — *(done in this PR)* settings-customization-roadmap S7–S12 sequencing
  bannered as superseded by audit §11 (three-lane architecture content retained).

### Help / Hubs / Navigation / Customization

True today: five render paths apply five different filter sets; Help does not consume
`access_projection`; surface-map preamble counts are stale (test-pinned, so fixing them
is test work, not a prose patch).

- **HLP-1 [CL]** — **Lane 8 (appended): bounded doc/test session** — reconcile
  `docs/help-command-surface-map.md` counts (10 hubs, post-#626 cog/subsystem counts)
  **with** its pin tests (`tests/unit/docs/test_help_surface_map_doc.py`), and add
  current-behavior **characterization tests** for the five Help render paths (pin
  today's filters so the future projection seam has a regression net). No behavior
  changes, no owner answers needed.
- **HLP-2 [F]** — Help Projection seam (read-only `HelpCatalogue` + `HelpProjectionService`
  composing governance + command-access + routing + **access_projection**). Design home:
  help audit §9. Sequence after ADP-1/ADP-2 (it consumes their seams); the *read-only*
  projection service needs no overlay answers.
- **HLP-3 [F]** — Guild Help **overlay storage/editor**. **Fully decided 2026-06-09
  (Q-0055–Q-0059):** hiding is display-only (never execution denial) · names Help-only ·
  ordering panel-local (no UI until stable panel/action identities) · admin/debug shows
  custom + default + key · Help Home message = **embed builder** (structured
  title/description/color → needs the structured overlay model, not a scalar; bounded +
  mention-suppressed + preview mandatory). Sequenced after Lane 8 + the HLP-2 seam.
- **HLP-4** — *(constraint)* Help customization must never change slash registration or
  execution authorization; presentation overlays stay separate from governance and
  command access.

### AI orchestration / answerability

Shipped: orchestration Phases 1–3 (#612/#618/#619), answerability 1A/1B/2 (#612/#616).

- **AI-1 [I]** — **Lane 3: orchestration Phase 4 MVP** — one vertical slice
  (round-cash family plan→execute→verify + one typed answer-with-evidence contract;
  default byte-identical; Q-0046). Q-0043 inclusive-range semantics ride along.
- **AI-2 [I]** — **Lane 4: answerability Phase 3** — the three read-only self-awareness
  tools over the #616 read model (tools-available · policy-explanation ·
  answerability-summary), audience-tiered at construction (Q-0047; Q-0048 standing
  lift — cite both in the PR).
- **AI-3** — *(posture)* Q-0048: read-only + deterministic + tiered ⇒ standing lift;
  writes / cost / external calls / new UI ⇒ per-exposure ask. Unchanged by this plan.
- **AI-4 [F]** — durable per-decision orchestration audit trace (orchestration plan
  §12.1, explicitly deferred).

### BTD6 data / tools

- **BTD-1 [I]** — **Lane 5: data-refresh workflow**, `workflow_dispatch`-**only**
  (Q-0049): runs the existing manual chain, opens a PR, never pushes to main, no
  schedule. Small (~1h); batched with Lane 6 in one session (two PRs) per §5.
- **BTD-2 [F]** — CT-team + version-announcement pointer promotion. **Shapes decided
  (Q-0064, 2026-06-09):** announcement channel → first-class BTD6 **binding** (native
  selector); CT group → **guided advanced flow** (URL/ID → parse → preview → confirm).
  Lands with settings Phase 2's BTD6 rows, after Lane 7.
- **BTD-3 [G]** — extraction/cutover (`--all`): ADR-006 lane discipline; zone/buff/
  subtower tail + name guard + value-pinned test updates make it human-reviewed, not
  automatable.
- **BTD-4 [CL]** — *(done in this PR)* refresh-plan cron residue annotated (the §
  "Proposed automation" sketch and open-decision 1 predate Q-0049's dispatch-only
  sign-off).

### Games / Mining

Shipped: Wave 1 #606–#610 + Workshop/durability + live hub overview (#624); tuning
confirmed, duels-wear queued (Q-0054).

- **GME-1 [F]** — next mining frontier (after the scoreboard): functional **structures**
  (Forge/Vault/Home — remaining §7.5 sinks) **or** the first Wave-2 platform layer
  (**game-XP service**, §7.4). Owner picks at promotion time; brainstorm §7.7 routes.
- **GME-2 [F]** — duels weapon/armor wear slice (queued by Q-0054 answer).
- **GME-3 [G]** — pets & companions (`pets-companions-plan-2026-06-09.md`): gated on
  Wave-1 keystones + balance review + owner promotion.
- **GME-4 [F]** — Q-0053 ease quick-wins (context-menu actions, persistent reminders) —
  top candidates when a light session needs a win.

### Server management

- **SRV-1 [F]** — PR13 AI template layer, then **SRV-2 [F]** PR14 unified hub. The
  authoritative queue is `docs/planning/server-management-status-2026-06-05.md` —
  not re-enumerated here; not in the current scoreboard (owner did not order it into
  this cycle).

### Docs / workflow / memory system

- **DOC-1 [CL]** — *(done in this PR)* reconciliation pass: current-state hedges
  (#620/#624/#626 + Spotlight contradiction + stamp), scoreboard tail, audit
  annotations, settings-roadmap banner, BTD6 cron residue.
- **DOC-2 [F]** — **check_docs freshness gate** (repo-review R3, groomed 2026-06-09
  from audit-recommendation → structured tooling item): fail CI on `(this session)` /
  `Reconcile PR #` markers in `docs/current-state.md`. Small `scripts/check_docs.py`
  slice + test; good rider on any docs-tooling session.
- **DOC-3** — *(shipped conventions, #628 — apply, don't re-decide)* router collision
  rule + answer-scope lines (`ai-project-workflow.md` §9); Protocol END step 6a;
  lazy vision-ledger blocks (Q-0062); grep-plan-headers reading rule.
- **DOC-4 [CL]** — *(done in this PR)* "(this session)" → dated stamps in the 3 AI
  planning docs.
- **DOC-5 [I]** — **Lane 6: vision draft-answers** for Q-0038–Q-0042 (Q-0051 route,
  docs-only): one concrete proposed answer per question, `draft-answer — awaiting
  maintainer markup`, grounded in existing decisions + the ideas-lab §6 rejection
  ledger + ADR-001/002/007.

### Health / diagnostics

- **HLT-1** — *(cross-ref)* the `help_advertises_locked` provider lands in
  `setup_diagnostics` via **ADP-1** — diagnostics is the consumer surface, adaptive is
  the owner lane.
- **HLT-2 [F]** — production live-tests for the owner-gated AI health tool + grouped
  findings (maintainer-driven; folio routes it).

## §4 Priority rollup

| Priority | Items |
|---|---|
| Critical blocker | — none. Nothing red-stops the queue; the worst live defect is the bounded 25-option truncation (SET-1). |
| Important next | ADP-1 → AI-1 → AI-2 → BTD-1 + DOC-5 → SET-1 (scoreboard order; Q-0065 may pull SET-1 forward) · then ADP-2 |
| Cleanup | DOC-1, DOC-4, BTD-4, SET-7 (all shipped in this PR) · HLP-1 (Lane 8) |
| Future opportunity | HLP-2, HLP-3, SET-2, SET-3, SET-4, SET-5, AI-4, BTD-2, GME-1, GME-2, GME-4, SRV-1, SRV-2, DOC-2, HLT-2 *(SET-2/SET-3/BTD-2/HLP-3 directions all decided 2026-06-09 — Q-0063/Q-0064/Q-0055–59; sequenced after Lanes 7/8)* |
| Gated / off-limits | ADP-3 (copy review) · BTD-3 (ADR-006) · GME-3 (keystones+balance) · AI writes/external/UI (Q-0048 posture) · plus the standing off-limits in `current-state.md` |

## §5 Recommended session sequence

Rule: an autonomous session may take **consecutive lanes in scoreboard order** — never
out of order, never half-done (blocked→skip applies); **one PR per lane**; draft PR at
first push (Q-0052); CI mirror green before the next lane.

| Session | Lane(s) | Objective | Size | Gates |
|---|---|---|---|---|
| **S1 (this)** | — | Consolidated plan + reconciliation + scoreboard extension | S, docs-only | none |
| **S2 (next)** | Lane 2 | **ADP-1** — tier-input + `help_advertises_locked` + denial-copy draft | M | none (Q-0045/Q-0036 answered) |
| S3 | Lane 3 | **AI-1** — orchestration Phase 4 MVP slice | M | none (Q-0046) |
| S4 | Lane 4 | **AI-2** — three self-awareness tools | M | none (Q-0047/Q-0048) |
| S5 | Lanes 5+6 | **BTD-1** + **DOC-5**, batched — **two PRs**, one session | S | none (Q-0049/Q-0051) |
| S6 | Lane 7 | **SET-1** — Settings Phases 0+1 | M | none; position = Q-0065 |
| S7 | Lane 8 | **HLP-1** — surface-map counts + Help characterization tests | S–M | none |
| later | — | Settings P2/3 planning (SET-2/SET-3) | M | **Q-0063, Q-0064** |
| later | — | Help overlay/editor (HLP-3, via HLP-2 seam) | L | questions answered 2026-06-09 — sequenced after Lane 8 + HLP-2 |
| later | — | ADP-2 P1C panels · GME-1 frontier · SRV queue | M | owner promotion |

### S2 expanded — Lane 2 (Adaptive P1B remainder)

- **Objective:** make audience simulation honest and give `access_projection` its first
  consumers: (1) Q-0045 option-b **tier-input** — the governance axis prefers
  `AccessContext.member_tier` when explicitly set; (2) the **`help_advertises_locked`**
  drift provider (what Help advertises to a baseline audience that full-axis resolution
  says is locked); (3) the **denial-copy draft** delivered in the PR body for maintainer
  read-through.
- **Scope / seams (verified on disk):** `disbot/governance/resolver.py:379`
  (`get_visible_subsystems`) · `disbot/governance/models.py:83` (`GovernanceContext`) ·
  `disbot/services/access_projection.py:147` (`AccessContext.member_tier`, currently
  unconsumed) + its `_SAFE_TEXT` table · `disbot/services/setup_diagnostics.py:698`
  (`_diagnose_routing_access_conflict` — the shape template; register the new collector
  alongside the existing ones).
- **Out of scope:** wiring `safe_text` into live denial paths (ADP-3); P1C panels
  (ADP-2); any Help-route filter change (HLP-2); **do-not-duplicate:**
  `routing_access_conflict` (shipped #592), `configured_resource_missing` (covered by
  the four existing collectors), `identity_mismatch` (covered by
  `validate_identity_contract` + ledger tests).
- **Risks:** the governance resolver is a live access-control surface — tier-input must
  be read-only, opt-in, never derived for real members; axis short-circuiting can
  produce false locked-positives (adaptive plan §16.8 item 6); per-guild provider cost —
  reuse the batch projection surface and bound the work; simulation must label what it
  cannot model (§16.4).
- **Verification:** patched-resolver-style tests (P1A pattern) + tier-honored-only-when-set
  + real-member-path-unchanged cases; the read-only AST invariant stays green; full CI
  mirror; no migrations, no data writes → rollback = single revert.
- **Stop conditions:** any governance **write**-path touch needed → stop and report;
  member simulation beyond tier/role inputs → ship with labeled limits instead of
  synthesizing members; copy-table disagreement → stays draft.

## §6 Conflict & duplication cleanup (one fact, one home)

| Durable fact | Canonical home | Everyone else |
|---|---|---|
| Execution order / next lane | multi-lane scoreboard (checkboxes + PR #s) | current-state ▶ Next action *points*; this doc *reasons* |
| What is true right now | `docs/current-state.md` | dated snapshots defer to it; source wins over all |
| Settings phasing (what we build when) | settings audit **§11** | settings-customization-roadmap = architecture reference (banner added); folio routes |
| Settings/bindings/provisioning ownership | folio + `ownership.md` | audits cite, don't redefine |
| Help current behavior + customization phases | help audit (#627) | surface-map = pinned inventory (counts fixed in Lane 8, with its tests) |
| Adaptive P1 scope/specs | adaptive plan §16.8 (Q-0045 decision recorded at its line 587) | scoreboard Lane 2 summarizes |
| BTD6 refresh shape | refresh-plan **header** (Q-0049 dispatch-only) | the in-body cron sketch is annotated not-approved residue |
| Owner intent / decisions | question router (append-only, §9 collision rule) | docs link Q-numbers, never restate answers as their own |

Stale/conflicting text **fixed in this PR**: current-state:48 ("Still open: not
registered…") vs :15 (#626 executed) → resolved-by-#626 wording; current-state:9 #620
hedge → merged, zero open PRs; current-state:11/:15 "verify merged" hedges → verified;
scoreboard tail (named #624's content as *future* frontier) → repointed; settings
audit ~:182 + help audit Spotlight lines → post-merge annotations; "(this session)"
markers in the three AI docs → dated; BTD6 cron block → annotated. **Deferred, with
homes:** surface-map counts (Lane 8 — test-coupled); check_docs freshness gate (DOC-2);
`.claude/CLAUDE.md` is propose-only — nothing in this pass needed it.

## §7 Question routing

No duplicates minted — router tail re-checked before appending. **Next free after this
session: Q-0066.**

| Question | Status | Gates |
|---|---|---|
| Q-0038–Q-0042 (vision batch) | open — Q-0051 drafts route | DOC-5 / Lane 6 produces the draft answers |
| Q-0055 (hide = display-only vs deny) | **answered 2026-06-09: display-only** | HLP-3 keystone settled; hiding never blocks execution |
| Q-0056 (custom-name scope) | **answered 2026-06-09: Help-only** | stable names everywhere else |
| Q-0057 (ordering scope) | **answered 2026-06-09: panel-local** | no ordering UI until stable panel/action identities |
| Q-0058 (admin/debug names) | **answered 2026-06-09: custom + default + key** | audit/diagnostics keep canonical identity |
| Q-0059 (Help Home format) | **answered 2026-06-09: embed builder** *(deviates from recommendation)* | structured overlay storage; bounds/sanitation mandatory |
| Q-0063 (AI hybrid projection durable?) | **answered 2026-06-09: converge gradually** | projected keys frozen; typed-panel convergence at SET-3/Phase 3 |
| Q-0064 (BTD6 CT/version pointers) | **answered 2026-06-09: binding + guided flow** | BTD-2 shapes set; lands with settings Phase 2 |
| Q-0065 (new, this session) | **answered 2026-06-09: end of queue** | Lanes 7/8 stay after Lane 6 |

**End-of-session structured choices (Protocol END 6a) — outcome:** two rounds, both
after #629 went ready. Round 1 (Q-0065 · Q-0063 · Q-0064 · Q-0055): all four answered
with the recommended option. Round 2 (offered when the maintainer asked "any more
questions?" — Q-0056–Q-0059): three recommended options plus one deviation, **Q-0059 =
embed builder**, which settles the overlay-storage question (structured model, not a
scalar). All recorded verbatim with answer-scope lines in the router (§25/§27/§28) and
routed in the follow-up PR. Nothing in S2–S5 was ever blocked on them; the entire
gated-tail question set (except the Lane-6 vision batch) is now pre-cleared.

## §8 Next-session prompt (copy-paste)

```text
You are working in menno420/superbot. Execute scoreboard Lane 2 (Adaptive P1B
remainder) end-to-end this session.

Orientation (in order): .claude/CLAUDE.md → docs/current-state.md →
docs/planning/multi-lane-execution-plan-2026-06-09.md (Lane 2) →
docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md §16.4 + §16.8 →
docs/planning/consolidated-productive-session-plan-2026-06-09.md §5 (S2 spec).
Verify first: live open-PR state; that Lane 2 is still the first unchecked lane.

Objective (three items, one PR):
1. Tier-input (Q-0045 = option b, decided): the governance axis prefers
   AccessContext.member_tier when explicitly set. Seams:
   disbot/governance/resolver.py get_visible_subsystems (~:379),
   disbot/governance/models.py GovernanceContext (~:83),
   disbot/services/access_projection.py AccessContext.member_tier (~:147 —
   currently unconsumed). Read-only, opt-in; never derive a tier for a real member.
2. help_advertises_locked drift provider in disbot/services/setup_diagnostics.py,
   modeled on _diagnose_routing_access_conflict (~:698); register it alongside the
   existing collectors. Judge the tier dimension via the new tier-input — beware
   first-deny short-circuiting (§16.8 item 6); label what the simulation cannot
   model (§16.4).
3. Denial copy (Q-0036, decided): draft/extend the _SAFE_TEXT strings and present
   the full table in the PR BODY for maintainer read-through. Do NOT wire them into
   live denial paths — wiring is a follow-up after his OK.

Do NOT build (already shipped/covered): routing_access_conflict (#592);
configured_resource_missing (the four existing collectors cover it);
identity_mismatch (validate_identity_contract + ledger tests cover it).
Hidden dependencies: tests/unit/services/test_ai_readonly_invariants.py-style AST
read-only pin on access_projection must stay green; patched-resolver test pattern
(P1A precedent); new bus events (if any) → core/events_catalogue.py KNOWN_EVENTS.

Verification: python3.10 scripts/check_quality.py --full +
python3.10 scripts/check_architecture.py --mode strict (both exit 0); targeted
governance/access-projection/setup_diagnostics tests incl. tier-honored-only-when-set
and real-member-path-unchanged. No migrations, no data writes (rollback = revert).

Workflow: draft PR right after first push (Q-0052); tick the scoreboard checkbox with
the PR #; update current-state ▶ Next action (next unchecked lane = Lane 3); session
log with context-delta; mark PR ready when green.

Stop conditions: any governance WRITE-path change needed → stop and report; member
simulation beyond tier/role inputs → ship with labeled limits; copy disagreement →
keep as draft. If Lane 2 finishes with context to spare, continue with Lane 3 per the
scoreboard — never out of order.
```

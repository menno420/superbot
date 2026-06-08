# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **▶ Next action:** Phase 0 of the [Adaptive Setup, Access, Profile, and Routine Platform](planning/adaptive-setup-access-routine-platform-2026-06-08.md) is **complete**; Phase 1 is underway. Done: the **Q-0026 multi-word subsystem identity repair** (`cog_name_to_subsystem` CamelCase → snake_case, registry key `server_management`, plus the latent `proof_channel` / `four_twenty` collapse fix); the Phase 0 **direct-vs-draft mutation boundary** (`docs/ownership.md` § "Direct vs. draft mutation lanes") and **access read-model contract** (planning §4 + §16); **P1A** — `services/access_projection.py`, the side-effect-free composed Access Map read model (command-access + routing + governance + help axes, reusing existing owners; reason schema reuses `command_access.DecisionReason`) with 19 tests, no UI/persistence; and **P0C** — all six role-threshold write sites now route through the audited `role_automation.set_{time,xp}_threshold` seam (write + audit + XP-cache invalidation), so the drift-fence allowlist (`tests/unit/invariants/test_no_direct_role_threshold_writes.py`) is **empty** (absolute rule). The next lanes are **P1B** (re-scoped + partly shipped this session — §16.8 items 5–7: ✅ `routing_access_conflict` built (`setup_diagnostics._diagnose_routing_access_conflict`, member-independent, read-only, 7 tests); **remaining** `help_advertises_locked` needs the audience-sim decision first; **skipped** `configured_resource_missing` — already covered by the four existing `setup_diagnostics` collectors; the denial-message UX is a confirm-with-maintainer step) and **P1C** (read-only Access Map + Help Preview panels; resolve the audience-simulation point in planning §16.8 first). Owner decisions Q-0017–Q-0027 merged via **#585**; Q-0028–Q-0033 hold at their safe defaults. The server-management PR13 AI generation layer remains gated by the AI-expansion gate.
>
> **Last updated:** 2026-06-08 · Adaptive Setup/Access platform Phase 0 complete → Phase 1: **#588** (Q-0026 identity repair + Phase 0 contracts), **#589** (P1A Access Map projection service), and **#591** (P0C drift-fence groundwork + §16.8 plan review) merged; then **P0C shipped** — all six role-threshold writes converted onto the audited `role_automation` seam and the drift-fence allowlist emptied (this session's PR; reconcile its # next session). Earlier the same day **#584** merged the Server Management Hub and **#585** merged Q-0017–Q-0027. Also 2026-06-08: **SuperBot Context Compiler** shipped — `docs/agent/index.yml` (7-subsystem manifest), `tools/agent_context/build_pack.py` + `validate_pack.py`, 7 generated context packs in `docs/agent/generated/`, 13 pinning tests, `docs/agent/README.md`, `.claude/rules/` path-scoped guidance files, and AGENT_ORIENTATION + repo-navigation-map updates. Source and live GitHub state supersede older wording. This file lists merged work + the next action; verify open PRs live.
> **Purpose:** the one file that answers "what is true right now?" so a new
> session does not reconstruct it from the journal + planning docs. Read it
> **second**, right after `.claude/CLAUDE.md`.

---

## Stability baseline

Operational stability **accepted after #535** (live cog walk: server-management,
economy, moderation, games, hub navigation). **Do not run a broad re-audit unless
a regression is reported** — this is an *accepted baseline*, not a fresh re-test.
Env-gated features (AI / scheduler / YouTube / Paragon / webhook) run **degraded
in the sandbox**, not broken. Known UX follow-ups remain (below).

## In flight (verify against live GitHub)

**Do not trust a hard-coded PR count here — it goes stale on every push.** Get the
real list at session start from live GitHub (`list_pull_requests`, state=open);
this snapshot deliberately names no open PRs. For an initiative's shipped/queued
status read its tracker (e.g. the server-management tracker), not this section.
Source code and merged PRs win over anything written here.

## Recently shipped (newest first)

> Convention: **merged PRs only** (with #numbers). In-flight work is *not* listed here —
> get it from live GitHub. The newest merge a session sees may not be added yet; that
> lag is expected (the next session reconciles). A merged PR tagged "pending" is the bug.

- *(this session)* — **SuperBot Context Compiler**: `docs/agent/index.yml` (7-subsystem manifest, curated for every folio + binding docs + source roots + do-not-create warnings + gates + verification), `tools/agent_context/build_pack.py` + `validate_pack.py`, 7 generated context packs in `docs/agent/generated/`, 13 pinning tests in `tests/unit/docs/test_agent_context_index.py`, `docs/agent/README.md`, `.claude/rules/` path-scoped Claude guidance files (mutation-and-db, discord-views, context-compiler), and updates to `docs/AGENT_ORIENTATION.md` + `docs/repo-navigation-map.md`. Reconcile PR # next session.
- **#591** — Adaptive Setup **P0C groundwork**: the role-threshold direct-write drift-fence invariant (`tests/unit/invariants/test_no_direct_role_threshold_writes.py`) + a turn-key swap recipe (planning §16.5) + §16.8 plan-review refinements for the next agent. (The conversion itself shipped next; see ▶ Next action.)
- **#589** — Adaptive Setup **P1A**: the **Access Map projection service** (`services/access_projection.py`) — a side-effect-free composed read model (command-access + routing + governance + help axes, reusing existing owners) with 19 tests; no UI, no persistence.
- **#588** — Adaptive Setup **Q-0026 identity repair** (`cog_name_to_subsystem` CamelCase → snake_case; registry key `server_management`; latent `proof_channel`/`four_twenty` collapse fixed, regression-pinned) + Phase 0 **direct-vs-draft** and **access read-model** contracts (planning §16, `ownership.md`).
- **#585** — captured and routed owner decisions Q-0017–Q-0027 for the Adaptive Setup/Access/Routine planning lane.
- **#584** — merged the unified Server Management Hub as a first-class subsystem and completed the non-AI server-management lane.
- **#582** — server-management **PR13 deterministic slice**: `services/setup_role_templates.py` (built-in permission-free role bundles + pure `plan_template`) + the audited **`create_managed_role`** op-kind (routes through `RoleLifecycleService`, optional time/XP tier companion) + a **Role templates** setup section. Fixed a **latent PR11 regression** (the roles section's `set_role_threshold` op was never added to the DB op-kind gate/CHECK → couldn't stage): **migration 059** + a dispatcher↔gate↔CHECK drift-guard test close it. The **PR13 AI generation layer** + PR14 (hub) remained queued. (PR12 setup diagnostics & repair shipped 2026-06-07.)
- **#581** — idea-backlog grooming demo (Q-0015): promoted the mining-brainstorm `!explore` wiring into a structured plan + a `docs/roadmap.md` horizon; the standing end-of-session secondary task in action.
- **#570** — server-management **PR11** (moderation + roles setup sections) + workflow tooling + ecosystem docs (owner decision **Q-0008**: Moderation + Roles now, Governance deferred). The moderation section stages `set_setting` drafts for the PR10 knobs; the roles section adds the `set_role_threshold` op-kind for time/XP auto-role tiers. Setup diagnostics & repair (PR12) builds on top.
- **#567** — server-management **PR10 fourth slice**: optional post-kick/ban **message cleanup** (`post_action_cleanup`: none/kick/ban/both up to `post_action_cleanup_limit`, **default OFF**), owned at the `moderation_service` kick/ban seam and *requested from* `services/history_cleanup.py` (new author-scoped plan + a shared `apply_history_cleanup_plan` extracted from `!cleanuphistory` — one delete path). Best-effort: a blocked sweep never undoes the action.
- **#566** (merged) — **cross-area implementation roadmap** (`docs/roadmap.md`): the one by-area "what's planned, in what order" index (relative Now/Next/Later/Someday horizons + gates, not dates), linking each authoritative plan + folio, with a clearly-marked not-approved ideas section. Its AI section defers to the AI roadmap. Re-badged two mis-badged historical plans (`phase_2b_bindings_plan`, BTD6 extraction). Wired into `current-state` + `AGENT_ORIENTATION`.
- **#565** (Codex, merged) — source-verified **AI roadmap** (`docs/planning/ai-roadmap-2026-06-07.md`, Phase 0–11) + a 10-question batch. Opus-reviewed (sound; read-only boundary preserved). Owner answers (router §18): **AR-10** first Opus target = lock the orchestration foundation; **AR-08** tiered audience; **AR-09** explanation-only now. AR-01–07 hold at safe defaults until their lanes activate.
- **#564** — docs reachability cleanup: consolidated the 14-file BTD6 doc island into `docs/btd6/` behind the folio; archived the retired 2026-06 planning/audit burst into `docs/archive/`; corrected `AGENT_ORIENTATION`'s stale self-count and wired the orphaned `docs/context-map-tooling.md`. Added a **hard reachability gate** to `scripts/check_docs.py` (an unreachable doc fails CI unless badged `historical`/`archive`).
- **#563** — owner-workflow mapping: split the #562 capture into `docs/owner/maintainer-working-profile.md` (the *person*) + `docs/owner/ai-project-workflow.md` (the multi-agent pipeline, per-project roles, handoff templates, idea-state vocabulary); de-duplicated the restated rules to links; routed the **"a new idea is not a new priority"** rule into `.claude/CLAUDE.md` + `docs/collaboration-model.md`. Docs-only.
- **#558** — server-management **PR10 third slice**: configurable **warn escalation** owned at the `moderation_service` seam: `warn_escalation_action` (timeout/kick/ban/none at `warn_threshold`), `warn` returns a `WarnOutcome`, escalation deduplicated out of the cog + panel modal. Scalar/KV, no migration, behaviour-preserving by default.
- **#556** — server-management **PR10 second slice**: `require_reason` enforcement at the `moderation_service` seam (warn/kick/ban; timeout exempt) + a read-only bot-readiness diagnostics line on the mod panel (`utils/moderation_feasibility.py`).
- **#555** — server-management **PR10 first slice**: config-backed moderation behaviour (`moderation_config` policy + `dm_on_action` / `dm_template` / `ban_delete_message_days` / `max_timeout_minutes`) applied at the `moderation_service` mutation seam; behaviour-preserving by default.
- **#554** — implementation-readiness reconciliation: source-grounded readiness audit (`docs/audits/implementation-readiness-review-2026-06-06.md`) + reclassified stale Phase-2 / platform-consistency status cells so they aren't mistaken for current work queues; docs-only.
- **#553** — consistency-warning presentation fix (the health snapshot no longer flags benign `SKIPPED` consistency sections — bindings-from-DM / no-backfill-rows — as "needs attention") + role-hierarchy tiebreak (`role_feasibility` / `role_automation` compare hierarchy by (position, id) like discord.py, not raw `position`).
- **#552** — session journal made lean + self-maintaining: archive split (`.session-journal-archive.md`), a Quick reference, Rules regrouped, and a "tidy-each-session" protocol step (mirrored in `.claude/CLAUDE.md`); docs-only.
- **#551** — role-automation degradation fix: `role_automation.apply` preflight-guards at the mutation seam (via `utils.role_feasibility`), classifies failures, and keeps predictable Manage-Roles/hierarchy blockers off the ERROR-only health surface; operator + role-Diagnostics surfaces show the cause.
- **#550** — collaboration-model doc + truth-layer restructure (goal-first, prompts-as-guidance); docs-only.
- **#549** — server-management cleanup PR8+PR9: `policy_version` marker, presets builder + dry-run + panel diagnostics, and the guild-default `scope_id=0` no-op fix.
- **#548** — closed the migration-`057` persistence/dedupe/retention integration-test gap (test-only).
- **#546** — canonical subsystem folios (health/diagnostics, server-mgmt, settings, BTD6, games, media).
- **#544** — freshness-oriented docs route, lifecycle labels, ideas area, and subsystem-folio model.
- **#543** — boot / test-bot capability doc correction.
- **#542** — docs reconciled to shipped bot-awareness status.
- **#541** — bot-awareness **PR4–PR6**: grouped recent-error findings (opt-in),
  owner-gated `diagnostics_health_snapshot` AI tool (D1 resolved), persistent
  operational-health findings (migration `057`).
- **#539** — AI extra-tool capability **ideas backlog** (capture only, not approved work).
- **#537** — bot-awareness **PR1–PR3**: health contracts + aggregator, `!platform
  health`, startup-health snapshot.
- **#535** — back-to-Help navigation fix; stability baseline accepted.

> Older than this: see `docs/planning/*` trackers and `docs/decisions/*` ADRs.

## Next candidates

- **Cross-area sequencing + the plan index now live in [`docs/roadmap.md`](roadmap.md)**
  (by area, with Now / Next / Later / Someday horizons + gates — where to find which plan
  for which part of the code). The picks below are the current top of that list.
- Highest-value approved implementation lane: server-management. **PR10 is complete**
  (six slices, ADR-008). **PR11 (moderation + roles setup sections) merged via #570**;
  PR11's **governance** section is **deferred** (cleanup already owns the main governance
  write — revisit only with a scope decision). **PR12 (setup diagnostics & repair) was built
  2026-06-07** (read-only `setup_diagnostics` service + Diagnose & repair section). **PR13's
  deterministic role-templates slice was built 2026-06-08** (`setup_role_templates` catalogue +
  `create_managed_role` op + Role-templates setup section; also fixed a latent PR11 staging
  regression via migration 059). The next steps are the **PR13 AI generation follow-up**, then
  **PR14** (hub). The `docs/planning/server-management-status-2026-06-05.md` tracker is the
  authoritative queue — don't duplicate it here.
- Health/diagnostics maintainer live-tests (production AI tool + grouped findings):
  see `docs/subsystems/health-diagnostics.md`.
- **Docs consolidation (Q-0010) — executed 2026-06-08.** Top-level `docs/` is now **16**
  (the 13 binding contracts + `current-state` + `roadmap` + `context-map-tooling`); plans /
  audits / inventories / historical snapshots moved into clustered subdirs behind their
  folios, and `_TOP_LEVEL_DOCS_BUDGET` lowered 41 → 16. Paired with the idea-backlog
  lifecycle + grooming secondary task (Q-0015, `docs/ideas/README.md`) and the binding-doc
  section-ownership convention (`docs/owner/ai-project-workflow.md` §9). The original handoff
  was [`planning/docs-restructure-brief-2026-06-08.md`](planning/docs-restructure-brief-2026-06-08.md).
  Verify merge status on live GitHub.
- Use the canonical subsystem folios for area-specific implementation/planning. The
  2026-06-06 readiness audit classifies stale, gated, and ready workstreams.

## Gates / blocked work

- **AI / BTD6 feature expansion** is gated on *all* of: bot-wide stability **+**
  provider/provenance checks **+** caching / source-health clarity **+** AI
  behavior/config correctness — **not** just the RC-11 guard suite passing.
- **BTD6 data extraction** — ADR-006 provenance schema **now implemented**
  (`docs/btd6/btd6-provenance-schema.md`); extraction may resume against the ordered
  backlog in `docs/btd6/btd6-gamedata-decode-status.md`. The broader AI/BTD6
  feature-expansion gate (stability + provider/provenance + caching + AI config) still
  applies.
- `_derive_scope` → `PLATFORM_OWNER` (decision D1) — **RESOLVED** in #541; owner-only
  AI tools are now reachable.

## Known UX follow-ups (not stability bugs)

- Server-management member/role UX follow-ups: see
  `docs/subsystems/server-management.md`.
- Dense DiagnosticCog platform-subview pagination idea: see
  `docs/subsystems/health-diagnostics.md`.

## Near-term technical debt (decided, not yet implemented)

- **`cog_name_to_subsystem` CamelCase fix (Q-0026) — IMPLEMENTED 2026-06-08.** The function
  now converts CamelCase → snake_case and the registry key is `server_management`; the same
  fix also repaired the latent `proof_channel` / `four_twenty` collapse and added regression
  tests pinning the snake_case output contract. (Kept here as a one-line record until the next
  session reconciles the merge into "Recently shipped"; verify the PR live.)

- **`new_subsystem.py` scaffold script (Q-0025).** Adding a hub/subsystem requires
  ~8 coordinated edits with no automation. Decided deliverable: a `new_subsystem.py`
  scaffold script in `scripts/` that covers all required touch-points. Capture in
  `docs/ideas/` as a decided backlog item. **Owner decision Q-0025.**

## Off-limits / do-not-propose

- No Redis / external state store (**ADR-001**).
- Game state is **not** restart-safe by design (**ADR-002**) — accepted, not a bug.
- Do not re-litigate the rejection ledger in
  `docs/planning/superbot-ideas-lab-2026-06-05.md` §6.
- Do not restate "bot fully tested & working" as *newly* verified without an actual
  boot + live walk — cite the #535 baseline instead.

## Where to read next

The **canonical read path + "what lives where"** lives in
**`docs/AGENT_ORIENTATION.md`** ("Reading order by task" + the document-classification
lists). This file is *step 3* of that path: read it for **what is true right now**, then
follow the orientation route for your task. The read-path table is **not** duplicated
here — one canonical home (`AGENT_ORIENTATION.md`).

**One-fact-one-home rule:** if a fact belongs in one of those homes, **link** to it —
do not restate it here. Restatement across files is where drift breeds. In particular,
**don't summarize plans'/trackers' PR numbers or status here** — link to the folio or
tracker, which is authoritative for its own area.

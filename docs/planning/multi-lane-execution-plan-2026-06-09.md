# Multi-lane autonomous execution plan — 2026-06-09

> **Status:** `plan` — the **launch pad for the autonomous multi-lane test session**
> and the **one canonical execution pointer** (cross-session scoreboard).
> Lanes 1–6 were decided + gate-lifted in the 2026-06-09 interview (router §22 /
> Q-0044–Q-0051); nothing in them needs a new owner decision unless marked. **Lanes 7–8
> were appended 2026-06-09 by the consolidated plan** — audit-sourced (#625/#627),
> agent-recommended; their **end-of-queue position was owner-ratified same evening
> (Q-0065 answered: after Lane 6)**. Reasoning/verification record for this queue:
> [`consolidated-productive-session-plan-2026-06-09.md`](consolidated-productive-session-plan-2026-06-09.md).
> Written so the next session needs **no directing prompt beyond "execute the
> multi-lane plan"**. Source and merged PRs win; verify lane state against live GitHub
> before starting each.

## How to run this (session protocol)

1. Normal orientation first (CLAUDE.md route). Then execute lanes **in order** — the
   order is an owner decision, not a suggestion (earlier lanes de-risk later ones).
2. **One PR per lane** (small/focused for `disbot/` lanes; docs lanes may ride along).
   **Open each lane's PR as a DRAFT right after the lane's first push** (Q-0052) so its
   real # goes straight into this scoreboard + the docs; mark it ready when the lane is
   green. Run the full CI mirror + arch check green **before starting the next lane**.
3. **Blocked? Skip forward, never half-route.** If a lane hits a genuine blocker,
   finish its docs/log trail (what + why + exact resume point), then start the next
   lane. A lane left mid-flight with no trail is the only failure mode this plan
   forbids.
4. **Context budget:** when context runs low, do not start a new lane — run the END
   protocol (session log + current-state + this plan's checkboxes), push, open the PR.
   The next session resumes at the first unchecked lane.
5. Tick the checkbox + add the PR # here as each lane lands (this file is the
   cross-session scoreboard).
6. **Running lanes in parallel (multiple agents at once)?** Proven viable 2026-06-09
   (Lanes 2+3). Follow `docs/owner/ai-project-workflow.md` §9 → "Parallel execution
   lanes": edit only your own lane's card/paragraph, re-sync `origin/main` before the
   final docs push, second-to-merge reconciles (UNION), skip the grooming pass.

## Known tripwires (read once, they bite across lanes)

- **800-LOC cog ceiling**: `ai_cog.py` ≈ 795, `setup_cog.py` ≈ 744 — add panel
  buttons/views, not cog subcommands (the Phase-3 `ai:tools` precedent).
- New bus events must be added to `core/events_catalogue.py KNOWN_EVENTS`.
- Doc-pin tests (`tests/unit/docs/`) red when their doc + code drift — update both in
  the same commit (help-surface-map, ai-config-ownership, current-state structure).
- The sandbox has **no AI provider key**: model-loop behaviour (lanes 3/4) is verified
  deterministically + by unit tests here; the live model pass happens on the
  maintainer's prod bot.
- Real-Postgres tests: module-local skip-if-unreachable fixture only (journal rule).

---

## Lane 1 — `new_subsystem.py` scaffold → register Community Spotlight (Q-0025 + Q-0044)

- [x] Shipped in PR: **#626** (2026-06-09). *Executor note:* the verified touch-point
  list missed one — the parent hub's `primary_children` tuple must also declare the
  child (`test_every_hub_primary_children_match_parent_hub_filter` pins it). The
  scaffold now checks it (`hub-primary-children`).
- **Goal:** build `scripts/new_subsystem.py` (custom tooling, repo-AST based — no
  external scaffold deps), then use it to register `community_spotlight` as a
  `community`-hub child; panel adopts hub navigation; delete the help-map §3 banner.
- **The ~8 touch-points the script must cover** (from Q-0025, verified 2026-06-09):
  `SUBSYSTEMS` entry (schema v2 — `tests/unit/utils/test_subsystem_registry.py`
  validates; key must equal `cog_name_to_subsystem(CogClassName)` → snake_case) ·
  `HUBS` entry *(only if new hub — not needed here; Spotlight is a child via
  `parent_hub="community"`)* · `KNOWN_PANEL_COMMANDS` · `build_help_menu_view` hook ·
  `docs/help-command-surface-map.md` §1+§2 rows · the command-map `###` section ·
  the four enumeration tests · `docs/repo-navigation-map.md` row.
- **Read first:** the `xp` entry in `utils/subsystem_registry.py` (sibling shape,
  `parent_hub="community"`), `tests/unit/docs/test_help_surface_map_doc.py` (what the
  doc-test will demand once registered), `docs/building-roadmap/command-integration-standard.md`.
- **Exit:** Spotlight appears in `!help` dropdown + typed route; all doc-pin +
  registry tests green; §3 banner removed; scaffold script has its own tests + a
  provenance header (CLAUDE.md tooling rule).

## Lane 2 — Adaptive P1B remainder: tier-input + `help_advertises_locked` + denial copy (Q-0045 / Q-0036)

- [x] Shipped in PR: **#632** (2026-06-09; parallel session — Agent 2 ran Lane 3
  concurrently by owner direction). *Executor notes:* (1) "advertised to the baseline
  audience" must include governance visibility — help menus/typed routes already filter
  through `resolve_visibility`, so the provider reads `get_visible_subsystems` once up
  front (the projection short-circuits on a routing deny before its governance axis);
  the per-feature drift that remains is the **routing** axis. (2) The denial-copy table
  is in the PR #632 body for the maintainer's read-through — **not live-wired** (Q-0036);
  wiring is a follow-up after his markup. Details: adaptive plan §16.8 items 3/6/7.
- **Goal:** implement the decided governance tier-input path (Q-0045 option b):
  governance axis prefers `AccessContext.member_tier` when set; build the
  `help_advertises_locked` drift provider on top; draft the full denial-copy set.
- **Read first:** adaptive plan §16.4 (simulation limits — the simulation must label
  what it can't model), §16.8, `services/access_projection.py`
  (`member_tier` forward hook), `services/setup_diagnostics.py`
  (`_diagnose_routing_access_conflict` is the shape template),
  `governance/resolver.py` (`get_visible_subsystems`).
- **Denial copy (Q-0036):** write the `_SAFE_TEXT` strings, but **do not wire them
  into live denial paths** — present the full set in the PR description for the
  maintainer's read-through; wiring is a follow-up commit after his OK.
- **Exit:** provider + tests (patched-resolver style, like P1A's); read-only AST
  invariant stays green; copy table in the PR body.

## Lane 3 — Orchestration Phase 4 MVP: one vertical slice (Q-0046)

- [x] Shipped in PR: **#634** (2026-06-09, parallel-session Agent 2). *Executor note:*
  the presets already declared the `workflow` labels, so no preset/catalogue/migration
  changes were needed — the gate is the resolved decision's `workflow` field in
  `_invoke_gateway`. The faithfulness ledger entry must carry **both** number forms
  (formatted `$19,840.00` + raw `19840.0`) because the verifier is a comma-normalised
  substring test. **Model loop flagged for the maintainer's prod check** (no sandbox key).
- **Goal:** the plan→execute→verify workflow for the **round-cash question family**
  ("cash from A to B / can I afford X at round R?") + **one** typed
  answer-with-evidence contract. Everything else in plan §7 stays deferred.
- **Read first:** orchestration plan §4–§9 (the shipped foundation it composes:
  catalogue → resolver → tool_choice/budget), `services/btd6_data_service.round_cash`
  (the deterministic owner), `natural_language_stage._invoke_gateway` (the seam the
  workflow hangs off), Q-0043 (inclusive range semantics — the contract must carry it).
- **Compatibility bar (same as Phases 1–3):** default behaviour byte-identical; the
  workflow activates only under the orchestration profile that selects it.
- **Exit:** deterministic tests for plan/execute/verify + the contract; live boot
  green; model-loop behaviour explicitly flagged for the maintainer's prod check.

## Lane 4 — Answerability Phase 3: the three self-awareness tools (Q-0047, gate lifted)

- [x] Shipped in PR: **#639** (2026-06-09). *Executor notes:* (1) the answerability tool is
  named **`btd6_answerability`** (not the roadmap's `get_btd6_answerability_snapshot`
  candidate): it must carry `grounding_domain="btd6"` so its counts/versions join the
  faithfulness ledger — on the `BTD6_ANSWER` path **every number** in a reply is checked
  against the ledger, and an unledgered inventory would block the very "what do you know"
  replies it serves; the catalogue invariant pins grounding ⟺ the `btd6_*` name prefix.
  (2) Audience tiering is **construction-time**: the registry bakes the request `AIScope`
  into each handler; the tools take no scope/target arguments at all. (3) `build_registry`
  gained an optional `channel=` param so the policy explanation binds to the asking
  channel. Model loop flagged for the maintainer's prod check (no sandbox key).
- **Goal:** expose the #616 read model as three read-only AI tools —
  tools-available · policy-explanation · answerability-summary — audience-tiered
  (AR-08) at construction.
- **Read first:** answerability roadmap Phase 3, `services/ai_introspection_service.py`
  (the read model — already audience-filtered), `services/ai_tool_catalogue.py`
  (**every new tool needs a `CATALOGUE` entry + toolset membership** — the pinning
  test enforces it), `ai_tools.build_registry` (register here, never a parallel path).
- **Covered by the Q-0048 standing lift** (read-only, deterministic, tiered) — no
  per-tool ask needed; cite Q-0047/Q-0048 in the PR.
- **Exit:** tools registered + catalogued + tested per tier; instruction stack updated
  if it should advertise them; grounding allowlists untouched unless the plan says so.

## Lane 5 — BTD6 data-refresh workflow, manual-dispatch only (Q-0049)

- [x] Shipped in PR: **#633** (2026-06-09). *Executor note:* live-running the chain
  before committing caught a real trap — `btd6_decode_inventory_report.py` didn't emit
  the `Status:` badge `check_docs.py --strict` demands (it was hand-added to the
  committed artifact only), so any regeneration would have reddened the refresh PR's
  doc-hygiene gate; fixed at the generator + pinned by test in the same PR. Decode
  roll-up regen is an opt-in default-false dispatch input (plan doc decision 3, per its
  own recommendation). First real dispatch still owed (needs the repo
  "Actions can create PRs" setting — documented in the workflow header).
- **Goal:** commit `.github/workflows/btd6-data-refresh.yml` with **`workflow_dispatch`
  only** (no schedule — that variant is explicitly not approved). It runs the existing
  manual chain from `docs/btd6/btd6-data-refresh-pipeline-plan.md` and opens a PR with
  the refreshed data (never pushes to main).
- **Caveat:** this is executable CI config — the interview approval (Q-0049) covers
  exactly the dispatch-only shape; any deviation (schedule, push-to-main) needs a new
  ask. Keep the job minimal; the ~320 MB clone cost is known + accepted for manual runs.
- **Exit:** workflow lints (`actionlint` if available / GitHub's parser), dry-run
  documented, plan doc's command chain referenced not duplicated.

## Lane 6 — Vision draft-answers for Q-0038–Q-0042 (Q-0051; docs-only)

- [x] Shipped in PR: **#631** (2026-06-09, parallel-agent run — Lane 6 only), **and the
  maintainer marked up all five same day** (structured-choices round in the PR session):
  Q-0038/Q-0039/Q-0041/Q-0042 approved as drafted; **Q-0040 adjusted — bounded-menu DM
  posture** (AI selects quest/reward/difficulty from pre-approved, hard-capped menus).
  Answers + scopes recorded in the router; conclusions routed to the four roadmap
  drafts, `docs/roadmap.md` gate lines, and the AI folio's first Q-0062 owner-voice
  block. Posture only — implementation still needs per-lane promotion.
- **Goal:** one drafted, concrete proposed answer per open vision question (clans
  identity · VIP fairness · AI dungeon-master posture · integrations/voice privacy ·
  web dashboard), each grounded in existing decisions + safe defaults, formatted so
  the maintainer can mark up approve/adjust/reject per item (the gate-lifting
  interview pattern, but with drafted prose to react to).
- **Read first:** each question's router entry (§21) + its "Suggested destination";
  `docs/planning/superbot-ideas-lab-2026-06-05.md` §6 rejection ledger (don't propose
  anything it rejects); ADR-001/002/007 boundaries.
- **Exit:** drafts appended to the router under each question (clearly marked
  `draft-answer — awaiting maintainer markup`); safe defaults stay binding until
  marked up.

## Lane 7 — Settings Phases 0+1: actionable-groups discovery + >25 reachability *(appended)*

> Appended 2026-06-09 by the consolidated plan — audit-sourced (settings audit §11,
> #625), agent-recommended; **position owner-ratified (Q-0065 answered 2026-06-09):
> here, after Lane 6.** Phase 2/3 directions were also decided same evening (Q-0063
> converge-gradually · Q-0064 binding+guided flow) — they remain *after* this lane.

- [x] Shipped in PR: **#640** (2026-06-09, same session as Lane 4). *Executor notes:*
  (1) the discovery rule lives in `services/customization_catalogue.actionable_settings_groups()`
  (the audit's sanctioned home; live composition, no snapshot staleness) — the real
  taxonomy is **11 groups**, matching audit §4/§5 exactly. (2) Domain-config groups are a
  **declared table** for Phase 1 (`DOMAIN_CONFIG_SUBSYSTEMS = {"cleanup"}`) — Phase 2
  replaces it with real registrations. (3) Availability = per-guild **cog routing**
  (guild-scope disable rows only), rendered as a "⛔ routed off" option marker — the group
  stays reachable and callbacks still re-check authority; a routing read failure renders
  the plain hub. (4) All 8 hub construction sites now use the async
  `SettingsHubView.create(author, guild_id)` factory.
- **Goal:** settings audit **Phase 0** (reconciliation + test targets — the session's
  first checklist item) + **Phase 1** display correctness: the Settings hub lists only
  **actionable** groups (editable scalar · binding editor · provisionable flow ·
  registered domain panel), every group reachable past the 25-option select cap
  (pagination/categories), empty pages excluded, actor-aware availability.
  Today the hub lists all 28 non-internal `SUBSYSTEMS` and silently truncates 3.
- **Read first:** `docs/planning/settings-cog-centralization-audit-2026-06-09.md`
  §6 + §11, `disbot/views/settings/hub.py` (`_DISCORD_SELECT_OPTION_LIMIT` :44, the
  `[:25]` slice :136), `core/runtime/settings_registry.py`, the settings folio.
- **Hard boundary:** discovery/navigation only — do **not** absorb domain mutation
  services (scalar / bindings / provisioning / governance / command-access / AI policy
  stay separate owners); Phases 2/3 stay gated on **Q-0063/Q-0064**.
- **Exit:** hub tests (empty-group exclusion · >25 reachability · gated/unavailable
  rendering); CI mirror + arch strict green.

## Lane 8 — Help bounded reconciliation: surface-map counts + characterization tests *(appended)*

> Appended 2026-06-09 by the consolidated plan — audit-sourced (help audit §13, #627),
> agent-recommended; **end-of-queue position owner-ratified (Q-0065 answered
> 2026-06-09)**. The full overlay question batch (Q-0055–Q-0059) was answered the same
> evening — display-only hide · Help-only names · panel-local order · custom+default in
> admin · **embed-builder** Home message — so the overlay is design-ready (structured
> storage), sequenced **after** this lane + the projection seam.

- [ ] Shipped in PR: ____
- **Goal:** reconcile `docs/help-command-surface-map.md` preamble counts (10 hubs;
  post-#626 cog/subsystem counts) **together with its pin tests**, and add
  current-behavior **characterization tests** for the five Help render paths (Home ·
  Advanced · typed routes · generic embed · dedicated panels) so the future Help
  projection seam has a regression net. No behavior changes.
- **Read first:** help audit §4–§5 + §13,
  `tests/unit/docs/test_help_surface_map_doc.py`, `disbot/cogs/help_cog.py`,
  `disbot/cogs/help/route.py`.
- **Hard boundary:** no overlay storage/editor — **Q-0055–Q-0059 open**; the audit's
  safe defaults bind (presentation-only hiding, Help-only names, panel-local order).
- **Exit:** preamble counts true + pin tests green; characterization tests pin today's
  per-route filters.

---

## After all lanes (or when stopping)

Run the standing END protocol (journal → END) + tick this scoreboard. *(The previous
tail named the mining Workshop/durability slice + mother-panel live overview as the
next frontier — those shipped in **#624**, before Lane 1 even landed.)* When every lane
above is done, the gated tail + next frontier live in
[`consolidated-productive-session-plan-2026-06-09.md`](consolidated-productive-session-plan-2026-06-09.md)
§5: Settings Phase 2/3 planning behind **Q-0063/Q-0064** · help overlay behind
**Q-0055–Q-0059** · adaptive P1C promotion · mining structures / game-XP service —
see `docs/current-state.md` ▶ Next action.

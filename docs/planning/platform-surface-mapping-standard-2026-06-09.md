# Platform surface mapping standard — 2026-06-09

> **Status:** `plan` — the binding mapping standard for the two parallel Codex
> platform-mapping agents (Agent A: user-facing surface · Agent B: admin/platform
> surface) and the merge/implementation session that follows them. Produced by the
> 2026-06-09 standards-setting session (PR #641); source-verified at HEAD `7534e3e`
> (merge of #637). **Source code and merged PRs win over this document** — re-verify
> the §2 baseline facts and the §2.4 in-flight list against live GitHub before
> mapping.
>
> **What this is:** the schema, vocabulary, evidence rules, scope partition, and
> consistency target that make the two mapping reports mergeable into one
> implementation plan. **What this is not:** an implementation approval. No runtime
> behavior changes in the mapping sessions.
>
> **Companions (read, don't restate):** the two prior Codex audits this composes
> with — [`settings-cog-centralization-audit-2026-06-09.md`](settings-cog-centralization-audit-2026-06-09.md)
> (#625, settings stack) and
> [`help-cog-customization-audit-2026-06-09.md`](help-cog-customization-audit-2026-06-09.md)
> (#627, Help architecture). Those two already map the settings and Help *stacks*
> in depth; this campaign maps the **whole command/panel/service surface, per
> subsystem**, against one schema.

---

## 1. Purpose and campaign shape

The maintainer's goal: SuperBot becomes a **perfectly consistent, easily
manageable, customizable platform** — every command reachable through the right
help/panel path, every panel following the same UX principles, overlapping
services merged or routed through the right owner, every cog feeling like part of
one platform.

The campaign has three stages:

1. **This standard** (shipped here) — verified baseline + schema + split.
2. **Two parallel Codex mapping agents** — each maps a disjoint half of the bot
   using §3's schema, producing implementation-ready mapping docs (no code
   changes). Prompts: §6.
3. **One merge/implementation session** (Claude) — merges both reports,
   prioritizes by severity, and implements consistency fixes in risk-sized PRs
   (§7).

The mapping agents answer, for every subsystem/command/panel/service: *is it in
the right place, reachable the right way, owned by the right seam, consistent
with its siblings — and if not, what exactly is wrong, with evidence?*

---

## 2. Verified baseline facts (source-verified 2026-06-09 @ `7534e3e`)

Mapping agents: treat this section as the starting ground truth, then re-verify
anything load-bearing for your half. When source disagrees with any doc
(including this one), source wins — record the conflict.

### 2.1 The three different inventories (never conflate)

"Loaded cog", "subsystem", and "Help category/hub" are **three different
concepts** (a prior audit finding that keeps biting):

| Inventory | Count | Source of truth |
|---|---|---|
| Loaded extensions | **36** | `disbot/config.py` `INITIAL_EXTENSIONS` (`bootstrap_access_cog` MUST stay first — admission guard) |
| Registered subsystems | **29** | `disbot/utils/subsystem_registry.py` `SUBSYSTEMS` (frozen after `validate_registry()`; schema v2 with `parent_hub`/`hub_group`) |
| Mother hubs | **10** (+ the `all_commands` Advanced sentinel) | `disbot/utils/hub_registry.py` `HUBS` |

The **7 loaded cogs that are not subsystems**: `bootstrap_access_cog` (command
admission guard), `setup_cog` (`!setup`, `/setup`, `/setup-hub`, `/setup-depth`,
`/setup-skip`, `/setup-unskip` — the wizard surface), and the five split BTD6
cogs (`btd6_reference_cog`, `btd6_events_cog`, `btd6_strategy_cog`,
`paragon_cog`, `btd6_ops_cog`) which all surface under the single `btd6`
subsystem. Every one of the 29 subsystems has exactly one owning `*_cog.py`.

The 10 hubs: `games`, `btd6`, `economy`, `moderation`, `community`, `utility`,
`admin`, `settings`, `diagnostic` (displays as "Platform / Diagnostics"),
`server_management`. Parent/child and cross-link placement is declared in
`SUBSYSTEMS[*].parent_hub` + each hub's `primary_children`/`cross_link_children`
(pinned to agree by `test_every_hub_primary_children_match_parent_hub_filter`).

### 2.2 Canonical seams (the composition stack every mapping row points at)

| Concern | Canonical owner | Notes |
|---|---|---|
| Subsystem identity/metadata | `utils/subsystem_registry.py` | The five-surface identity contract is `docs/runtime_contracts.md` §1 |
| Hub presentation | `utils/hub_registry.py` | Display only; no policy |
| Help routing | `cogs/help/route.py` (`resolve_route`/`open_route`) | The ONLY resolver; typed `!help`, `/help`, and the dropdown all use it. `HUB_PANEL_BUILDERS` override: `diagnostic` → `build_platform_help_menu_view` |
| Help rendering | `cogs/help_cog.py` (Home, Advanced, generic cog embed, single-command embed) + per-cog `build_help_menu_view` hooks | 5 render paths; they apply **different** filters today (help audit §3) |
| Command classification | `core/runtime/command_surface_ledger.py` | Canonical vocabulary, §3.5 below |
| Panel inventory | `services/customization_catalogue.py` (`@panel_command` > `KNOWN_PANEL_COMMANDS` > `.+menu$` regex fallback) | Read-only catalogue, not storage |
| Subsystem visibility (per scope) | `governance/resolver.py` `resolve_visibility` / `get_visible_subsystems`; writes via `GovernanceMutationPipeline` | Help Advanced consumes it; Help Home + typed routes do **not** (known, Lane-8/projection territory) |
| Command admission | `core/runtime/command_access.py` + `services/command_access_service.py` | Prefix global check + `tree.interaction_check`, installed by `bootstrap_access_cog` |
| Per-scope cog routing | `services/command_routing.py` | Not consumed by Help today |
| Composite access read model | `services/access_projection.py` | Explainable, reason-coded; Help does not consume it yet (adaptive P1B/P1C lane) |
| Scalar settings | `SettingSpec` schemas → `core/runtime/settings_registry` → `settings_resolution` (read) / `SettingsMutationPipeline` (write) | 36 settings / 9 settings-bearing schemas + BTD6 binding-only schema (settings audit §5) |
| Bindings / provisioning | `BindingMutationPipeline` / `ResourceProvisioningPipeline` | Channel/role pointers are bindings, never scalars |
| Compound config | setup draft lane: `setup_draft` → `SetupOperation` → Final Review | Direct-vs-draft lane rule: `docs/ownership.md` § "Direct vs. draft mutation lanes" |
| Audited domain mutations | per-domain services (`docs/ownership.md` § "Service ownership") + `services.audit_events.emit_audit_action` | INV-E/F/G AST-enforced |
| Shared view primitives | `views/base.py` (`BaseView`/`HubView`/`send_panel`), `views/navigation.py` (`attach_back_button` — canonical, no second module), `views/selectors/` | Back-to-X helpers enumerated in `docs/help-command-surface-map.md` §4 |

### 2.3 Decided product posture (binding on recommendations)

Mapping recommendations must align with these answered owner decisions
(`docs/owner/maintainer-question-router.md`):

- **Q-0055** — hiding a command from Help is **display-only**, never
  execution-blocking (execution disabling stays with command-access / routing /
  governance owners).
- **Q-0056** — custom names are **Help-only** presentation.
- **Q-0057** — command ordering is **panel-local**, not guild-global.
- **Q-0058** — admin/debug views show **custom + default + stable key**.
- **Q-0059** — guild Help-Home message = **embed builder** (structured overlay,
  bounds/sanitation/preview mandatory).
- **Q-0063** — AI's seven-key scalar→policy projection **converges gradually**
  (kept + diagnosed; projected-key set frozen; typed-panel convergence at
  settings-audit Phase 3).
- **Q-0064** — BTD6 version-announcement channel → **binding**; CT group →
  **guided advanced flow** (lands with settings-audit Phase 2).
- **Q-0065** — scoreboard Lanes 7–8 stay at end of queue (after Lane 6).
- **Q-0048** — read-only **and** deterministic **and** audience-tiered AI tools
  carry a standing lift; anything that writes / costs / calls external / adds UI
  still needs a per-exposure lift.
- Settings hub target inclusion rule (settings audit §6, agent-recommended and
  lane-ratified): a settings group appears only with ≥1 actionable surface;
  pagination replaces silent 25-option truncation. (Implementation = Lane 7.)

### 2.4 In-flight and queued work (verify live before mapping)

In-flight state at the late-2026-06-09 reconciliation (re-verify live) — for
anything still open: **provisional surfaces; do not absorb, do not propose
conflicting reorganizations**:

- **#638 — BTD6 game-data mapping continuation** (ABR/income-set ingestion,
  decode-tail extensions). Touches `parse_gamedata`, `btd6_data_service`,
  `btd6_round_cash`/`btd6_round_composition` tool params, `docs/btd6/*`.
  → The BTD6 **command/panel surface** may still be mapped; mark the BTD6
  **data-service layer and AI-tool internals** `provisional(#638)` and skip
  recommendations there.
- **#639 — AI answerability Phase 3** (Lane 4, Q-0047) — **merged
  2026-06-09, after this standard's baseline verification**: three
  self-awareness tools registered in `ai_tools.build_registry` +
  `ai_tool_catalogue` + the instruction stack. → The AI cog/panel/policy-UI
  surface maps normally; for the **AI tool registry/catalogue/instruction
  stack and `ai_introspection_service`**, map the **landed #639 state** (it
  post-dates the §2 baseline commit) rather than treating it as drift, and
  keep recommendations there `blocked-by-gate(AI per-exposure)` unless
  Q-0048's standing lift clearly covers them.

Queued, owner-sequenced lanes (map the current state, but **route findings to
the lane instead of recommending parallel work**):

- **Lane 7** (`multi-lane-execution-plan-2026-06-09.md`): Settings hub
  actionable-groups discovery + >25 reachability (settings audit Phases 0+1).
- **Lane 8**: help-surface-map count reconciliation **with pin tests** + the five
  Help render-path characterization tests. (The stale prose counts themselves
  were corrected in this standard's PR; the pin tests + characterization tests
  remain Lane 8's.)
- **Adaptive Setup/Access P1C** (Q-0032): Access Map + Help Preview as staff-hub
  subpanels, no new command names. Help-consumes-projection work belongs to this
  lane — do not design a parallel Help lock/preview detector.
- **Server management PR13 AI layer + PR14 hub** — sequence owned by
  `planning/server-management-status-2026-06-05.md`; the governance setup
  section is **deferred** (Q-0008/Q-0011).
- Help overlay storage/editor — design-ready (Q-0055–Q-0059 answered) but
  sequenced **after** Lane 8 + the Help projection seam (help audit §11).

Hard gates that bound recommendations: AI/BTD6 broad expansion gate
(`docs/current-state.md` § Gates), ADR-001 (no Redis), ADR-002 (game state not
restart-safe — accepted), ADR-006 (BTD6 provenance), the
`superbot-ideas-lab-2026-06-05.md` §6 rejection ledger (do-not-repropose), and
the mining active lane (no speculative mining settings — settings audit §4).

### 2.5 Doc-trust notes for mapping agents

- `docs/help-command-surface-map.md` — **binding** inventory; tables verified
  correct at 29 subsystems / 10 hubs (prose counts corrected 2026-06-09 in this
  standard's PR). Lane 8 will pin the counts with tests.
- `docs/setup-platform/settings-customization-command-map.md` — the per-cog
  24-field inventory; body sections are useful prior art, but several were
  written pre-#142/#143 era and individual fields may lag source. Verify
  per-field before citing.
- `docs/building-roadmap/interface-completion-roadmap.md` L1–L6 sequencing is
  **superseded** by `mother-hub-map.md` S1–S13; `settings-customization-roadmap.md`
  S7–S12 status labels are **not a current queue** (its own banner says so).
- `docs/building-roadmap/command-expansion-backlog.md` and
  `admin-powers-config-coverage.md` are idea backlogs — cross-check source
  before citing anything in them as a gap.
- The 7 subsystem folios are `docs/subsystems/` (ai, btd6, games,
  health-diagnostics, media-youtube, server-management,
  settings-bindings-provisioning). **There is no folio for help/hubs, economy,
  community, moderation, admin, or utility** — for those areas the entry points
  are the help-surface map, the two prior audits, and `docs/ownership.md`.

---

## 3. The mapping schema (binding for both agents)

Every mapping doc contains, in order: an executive summary with severity-ranked
findings; one **subsystem section per assigned subsystem** (template §3.1) each
containing its command table (§3.2), panel records (§3.3), and service records
(§3.4); a **cross-boundary observations** section; a **future opportunities**
section (captured only); an **open owner questions** section (§5.4 — collected
in-doc, not routed to the router); and a **verification log** (§3.7).

### 3.1 Subsystem record (one `###` section per subsystem)

Numbered field list (the settings command-map convention — doc-test-friendly):

1. **subsystem_key** — the `SUBSYSTEMS` key (or `none — loaded cog only` for
   `setup_cog`/`bootstrap_access_cog`/split BTD6 cogs).
2. **owning_cog** — `disbot/cogs/<file>.py` (+ sibling package if decomposed).
3. **owning_services** — service/helper/workflow files this subsystem's
   logic lives in (each gets a §3.4 record).
4. **hub_placement** — top-level hub / `parent_hub` child / cross-links, as
   declared in registries, plus what the hub *views* actually render.
5. **help_routes** — what `!help <key>`, the dropdown, Advanced, and aliases
   actually open (verify via `resolve_route`, don't assume).
6. **panel_entry** — panel command(s) + the `build_help_menu_view` hook target;
   how the catalogue detects the panel (`@panel_command` / `KNOWN_PANEL_COMMANDS`
   / regex fallback — regex hits are findings).
7. **settings_setup_routes** — the subsystem's settings group state (scalar /
   binding / domain panel / none per the settings audit §4 vocabulary) + any
   setup-wizard section.
8. **governance_access** — `visibility_tier`, capabilities, how the surface
   behaves under governance/routing/command-access (verified, not assumed).
9. **placement_tier** — one of `top_level` / `child` / `cross_linked` /
   `legacy` / `hidden` / `internal` + whether placement is **correct** (judged
   against §4; deviations become findings).
10. **overlap** — services/commands overlapping another subsystem; merge or
    re-route candidates (each also appears as a finding with severity).
11. **protections** — tests + docs currently pinning this subsystem (name the
    test files).
12. **gaps_risks** — severity-labeled findings list (format §3.7).

### 3.2 Command record (one table row per command, per subsystem section)

Columns (split into two stacked tables if width hurts readability — keep the
column names exactly, they are the merge keys):

| Column | Content |
|---|---|
| `command` | canonical name + group path (e.g. `platform anchors`) |
| `aliases` | all registered aliases |
| `kind` | `prefix` / `slash` / `hybrid` / `listener-driven` |
| `cog` | owning cog file |
| `audience` | intended user type: `user` / `moderator` / `admin` / `owner` / `internal` |
| `surface_class` | current `command_surface_ledger` classification: `primary_entrypoint` / `power_user_shortcut` / `panel_action` / `legacy_duplicate` / `internal_admin` / `hidden` / `deprecated` (read the ledger/extras — do not invent values) |
| `help_path` | how Help reaches it (Home→hub→panel / Advanced / typed-only / not discoverable) |
| `panel_path` | which panel button/select reaches it, or `none` |
| `right_panel` | is it in the right panel? (`yes` / finding-ref) |
| `service_ok` | does it call the correct canonical seam? (`yes` / finding-ref; flag any cog-level business logic or direct DB write) |
| `duplicates` | overlapping/duplicate command(s), or `—` |
| `gov_ok` | respects governance/access/routing per §2.2? (`yes` / finding-ref) |
| `verdict` | disposition label (§3.5) |
| `evidence` | `file:line` anchors (§3.7) |

For every command also judge (fold into findings, not extra columns): is it
useful enough to keep; should it be **panel-first**, **typed-only**, **hidden
legacy**, or **admin-only**; would a better panel action / select flow replace
it (link the §3.3 record); what test or live verification its change would need.

### 3.3 Panel/view record (one numbered block per panel/hub/major child view)

1. **view** — class + file (e.g. `GamesHubView` — `views/games/hub.py`).
2. **entry** — opening command(s) / hook / parent-panel button.
3. **preset** — closest `hub-ui-standard.md` preset (User Navigation Hub /
   Feature Action Panel / Operator Hub / Platform Manager Panel / Setup Wizard
   Page) + whether it conforms (density, action-vs-nav, thresholds).
4. **components** — buttons / selects / modals inventory (labels + callbacks);
   note static-vs-dynamic option sources (guild channels/roles/members and
   live state should be dynamic — hardcoded option lists are findings).
5. **navigation** — back-button targets, which shared helper attaches them
   (`views/navigation.py` lineage), anchor/persistence behavior
   (`PersistentView` vs ephemeral `BaseView`), dead-end check.
6. **lifecycle_safety** — callbacks defer via `safe_defer` (INV-L); terminal
   states disable buttons where relevant; authority re-checked at callback
   time for mutating panels (`docs/capability-authority.md`).
7. **multiselect_fit** — would a (bounded) multi-select / native selector
   improve a flow that is currently N single actions or a text modal?
   (`edit_command_access.py` channel multi-select is the prior art; a Discord
   **modal cannot contain a select** — selector-izing a modal means a
   view→modal restructure.)
8. **copy_consistency** — does panel copy match actual command behavior and
   sibling panels' phrasing?
9. **visibility** — does the panel respect tier/visibility on open AND on
   callbacks; does it leak admin actions to user-tier panels?
10. **reuse** — uses `BaseView`/`HubView`/`PersistentView`, shared selectors,
    shared back helpers — or one-off primitives (findings)?
11. **consistency_gaps** — deltas vs. the closest sibling panel of the same
    preset, severity-labeled.

### 3.4 Service/helper/workflow record (one table row per service)

| Column | Content |
|---|---|
| `service` | file (e.g. `services/economy_service.py`) |
| `owner_of` | what it canonically owns (tables/writes/read models) |
| `consumers` | cogs/views/services that call it (grep-verified) |
| `mutation` | `mutating-audited` / `mutating-unaudited` (finding) / `read-only` / `pure` |
| `bypasses` | call sites that skip it and touch its domain directly (findings; check the invariant tests + `docs/ownership.md` blocklist) |
| `overlap` | similar logic living elsewhere; single-source-of-truth candidate? |
| `cache_events` | cache invalidation + catalogued events emitted (INV-A) |
| `observability` | logging/metrics posture |
| `tests` | the test files protecting it |
| `verdict` | §3.5 label + evidence |

### 3.5 Classification labels

**Current-state command classification** reuses the ledger vocabulary verbatim
(§3.2 `surface_class`). **Disposition verdicts** (commands, panels, services,
subsystem placements) use exactly:

`keep` · `reorganize` (right feature, wrong place/path) · `merge` (duplicate of
a named sibling) · `hide-legacy` (keep callable, reclassify
`legacy_duplicate`/`hidden`) · `needs-owner-decision` (product call — write the
question in §"Open owner questions") · `future-opportunity` (captured only, not
active work) · `blocked-by-gate(<gate>)` (correct change, but §2.4 sequencing
owns it — name the lane/PR/gate).

A `remove` recommendation is expressed as `hide-legacy` +
`needs-owner-decision` — mapping agents never decide deletion.

### 3.6 Severity labels

Reuse `docs/owner/agent-workflow-spec.md` §3.3 verbatim: **1 critical blocker**
· **2 important improvement** · **3 cleanup** · **4 future opportunity**.
Severity ranks the *finding*; the verdict says what to do about it.

### 3.7 Evidence format (non-negotiable)

Every non-trivial claim carries evidence; every finding carries all four:

```
FIND-<agent><nn> [severity] <one-line statement>
  evidence: <file>:<line>(-<line>) · <symbol or quoted fragment>
  verified-by: <how: read source / grep '<pattern>' / test name / registry enumeration>
  verdict: <§3.5 label>  (+ owner-question ref if needs-owner-decision)
```

Rules: cite `file:line` for the version you read (record your HEAD commit in
the doc header); prefer naming the pinning test over re-deriving a guarantee;
grep-verify any caller/consumer list (CodeGraph caller lists are a starting
point, never the list — `.claude/CLAUDE.md` CodeGraph tiers); when you contradict
a doc, say which doc and quote the stale text. Counts ("N commands") must come
from enumeration you ran, with the command you used.

### 3.8 Per-cog quality checklist (answer all 11, per subsystem)

1. Is this cog in the right hub (and tier)?
2. Are all useful commands discoverable from the right panel/help route?
3. Which commands should merge into a panel or reclassify as hidden legacy?
4. Do any commands belong in another cog/subsystem?
5. Are there overlapping services to consolidate (one owner per concern)?
6. Are selects/multiselects/modals/buttons used consistently with §4 and the
   hub-ui presets?
7. Are guild/channel/role/member choices dynamic from live state and
   permission-safe?
8. Are command names clear to a normal Discord admin/user?
9. What obviously missing commands/panel actions fit this cog?
   (`future-opportunity` only — Discord-feasible, architecture-consistent.)
10. Are new-idea suggestions consistent with ADRs/gates (§2.4)?
11. What should be fixed in the implementation session vs. captured as
    future opportunity?

---

## 4. Perfect-consistency target standard

The platform-level rules every cog/command/panel should eventually satisfy.
Mapping agents judge **against these**; the implementation session enforces
them. Each rule names its source; rules marked *(this standard)* are
newly-promoted defaults — deviations are findings, not violations of a binding
contract.

**Discoverability & placement**

- T1. Every user-facing command is reachable from `!help` via an acceptable
  path (panel, hub, Advanced, or admin section); hidden standalone commands are
  intentionally `internal`/`hidden`-classified
  (`command-integration-standard.md` §2).
- T2. Every subsystem has exactly one primary hub placement (`parent_hub` or
  top-level); cross-listing is cross-link buttons only and never changes
  ownership (`mother-hub-map.md` § Primary children vs cross-links).
- T3. Typed commands stay first-class — panels are the discoverable surface,
  typed entry the fast path; removing a typed shortcut to force panel use is
  forbidden (`hub-ui-standard.md` principle 8).
- T4. Help, hubs, and panels derive from `SUBSYSTEMS`/`hub_registry`/ledger
  metadata — no parallel registries (`hub-ui-standard.md` principle 10; help
  audit target: one Help catalogue/projection seam).

**Panels & UX**

- T5. Each hub/panel matches one `hub-ui-standard.md` preset; option counts
  follow the component thresholds (≤8 buttons; 9–12 grouped; 13–25 dropdown;
  25+ paginate/subgroup — silent truncation at 25 is always a finding).
- T6. Hubs navigate, child panels act; user-facing hubs don't mix action and
  navigation (`hub-ui-standard.md` principles 2–3).
- T7. Every panel has back-navigation via the canonical helpers; no dead ends
  (`command-integration-standard.md` §3; `views/navigation.py` is the only
  navigation module).
- T8. Panel options that represent live guild state (channels, roles, members,
  game state) are built dynamically and permission-checked; bounded
  multi-selects are preferred over repeated single-pick flows or text modals
  *(this standard; prior art `edit_command_access.py`)*.
- T9. Mutating callbacks re-check authority at execution time; I/O callbacks
  `safe_defer` (INV-L); terminal states disable their buttons *(this standard,
  generalizing `docs/capability-authority.md` + game-view practice)*.
- T10. Panel copy states what the action actually does, consistent with the
  typed command's help text *(this standard)*.

**Ownership & wiring**

- T11. Commands are thin entrypoints: validate → call service/runtime → render
  (`command-integration-standard.md` §4); business logic in a cog/view is a
  finding.
- T12. Writes go through the canonical seam for their kind: scalar →
  `SettingsMutationPipeline`; pointers → `BindingMutationPipeline`; resource
  creation → `ResourceProvisioningPipeline`; governance →
  `GovernanceMutationPipeline`; domain mutations → their owning service with
  `emit_audit_action`; compound/generated → the setup draft lane
  (`docs/ownership.md`, both lane tables).
- T13. One owner per concern: duplicate/parallel implementations of the same
  logic merge into the canonical owner; helpers needed by two layers live in
  `utils/` (`docs/helper-policy.md`).
- T14. Display visibility ≠ execution permission, ever: display-only hiding
  (Q-0055) composes with — never replaces — command-access/routing/governance
  (help audit §9; the one zero-tolerance UI rule).

**Settings, customization & platform feel**

- T15. A subsystem appears in Settings only with ≥1 actionable surface; domain
  panels register as catalogue destinations instead of pretending to be scalar
  pages (settings audit §6/§10 — Lane 7 implements).
- T16. Avoidable text entry converges on structured editors (toggles, enums,
  native selectors, numeric presets); free text remains only for genuinely
  authored content (settings audit §7).
- T17. Customization follows the decided posture: Help-only names, panel-local
  order, display-only hide, admin views show custom+default+key, embed-builder
  Home message (Q-0055–Q-0059) — through one audited overlay/projection design
  (help audit §8–§9), not per-panel hacks.

**Protection**

- T18. Every kept command/panel has at least a smoke-level test or an explicit
  manual-smoke note (`command-integration-standard.md` § Testing); every
  consistency fix lands with the test that pins the fixed behavior *(this
  standard)*.
- T19. Inventory docs (help-surface map, command map) update in the same PR
  that changes the surface; counts come from enumeration, not memory
  (`repo-navigation-map.md` § Updating; Lane 8 adds pins).

---

## 5. Two-agent split

Partition is **by subsystem** (the proven parallel-lane pattern —
`ai-project-workflow.md` §9). Both agents are **mapping-only**: no `disbot/`
changes, no test changes, no registry edits. Each agent's PR touches exactly
three files: its own output doc, its own line in §5.5, and its own
`.sessions/` log.

### 5.1 Agent A — user-facing / community / games / economy surface

**Subsystems (17):** `games`, `blackjack`, `rps_tournament`, `deathmatch`,
`counting`, `chain`, `mining`, `economy`, `inventory`, `leaderboard`, `xp`,
`community`, `community_spotlight`, `utility`, `general`, `four_twenty`,
`btd6` (including the five split BTD6 cogs' command surfaces:
`btd6_reference_cog`, `btd6_events_cog`, `btd6_strategy_cog`, `paragon_cog`,
`btd6_ops_cog`).

**Provisional carve-out:** BTD6 commands/panels are mappable; the BTD6
data-service layer + BTD6 AI-tool internals are `provisional(#638)` — describe,
don't recommend.

**Must NOT map:** every Agent B subsystem (§5.2); the help/registry
architecture itself (read it, route findings about it to "cross-boundary
observations"); the settings *stack* (map only your subsystems' settings
groups/rows).

### 5.2 Agent B — admin / moderation / setup / platform / governance surface

**Subsystems (12):** `admin`, `moderation`, `cleanup`, `logging`,
`proof_channel`, `role`, `channel`, `server_management`, `settings`,
`diagnostic`, `help`, `ai`.

**Plus the non-subsystem surfaces:** `setup_cog` (wizard commands + sections),
`bootstrap_access_cog` (admission), and the **composition architecture
records**: `cogs/help_cog.py` + `cogs/help/route.py`, `utils/hub_registry.py`,
`utils/subsystem_registry.py`, `core/runtime/command_surface_ledger.py`,
`services/customization_catalogue.py`, `services/access_projection.py`,
`services/command_routing.py`, command access. For the settings stack and Help
architecture, **start from the two prior audits and verify/delta** — do not
re-derive what they already mapped; your job there is the §3 records + what
changed since.

**Carve-out:** AI cog/panel/policy-UI surface maps normally. The AI tool
registry/catalogue/instruction-stack internals changed in **#639 (merged
2026-06-09, post-baseline)** — map the landed state, and keep recommendations
there `blocked-by-gate(AI per-exposure)` unless Q-0048's standing lift clearly
covers them. The governance **setup section** is deferred (Q-0008/Q-0011) —
map the current state, verdict `blocked-by-gate`.

**Must NOT map:** every Agent A subsystem (§5.1).

### 5.3 Shared read-only inputs (both agents)

This standard; the two prior audits; `docs/help-command-surface-map.md`;
`docs/ownership.md` + `docs/architecture.md` + `docs/runtime_contracts.md`;
`docs/building-roadmap/{command-integration-standard,hub-ui-standard,mother-hub-map}.md`;
`docs/setup-platform/settings-customization-command-map.md` (prior art per
cog); `docs/current-state.md`; the folios that exist (§2.5). **Read freely;
rewrite none of them.**

### 5.4 Non-overlap and conflict-prevention rules

1. **One subsystem, one agent.** A finding about the other half goes in your
   "Cross-boundary observations" section (one line + evidence), never as a
   mapped record. The merge session joins them.
2. **No shared-file edits.** Don't touch `docs/current-state.md`,
   `docs/roadmap.md`, the help-surface map, the command map, the question
   router, or any folio. Owner questions are **collected in your own doc's
   "Open owner questions" section** with proposed multiple-choice options; the
   merge session routes them to the router (this avoids the documented
   parallel-append renumbering cost).
3. **Skip the standing backlog-grooming secondary task** (parallel-session
   rule, `ai-project-workflow.md` §9).
4. **Name your sibling in the PR body**: "Parallel mapping agent
   (A|B) is concurrently mapping <other scope>; this PR maps only <yours>."
5. **Mapping-only**: if a fix is tempting, record it as a finding with a
   verdict — implementation belongs to the merge session. The only exception
   in scope: fixing a factual error **inside your own output doc**.

### 5.5 Output registry

Pre-allocated paths (stable, undated filenames; each agent records its actual
date + HEAD inside the doc header, badge `> **Status:** \`audit\``):

- **Agent A output** — `docs/planning/platform-mapping-a-user-surface.md`
  *(Agent A: when the doc lands, convert this line's path into a markdown link
  — that link is what keeps your doc reachable for `check_docs.py`.)*

- **Agent B output** — `docs/planning/platform-mapping-b-admin-surface.md`
  *(Agent B: same — convert this line's path into a markdown link in your PR.)*

### 5.6 Required checks for mapping-only PRs

```
python3.10 scripts/check_docs.py --strict      # badge + links + reachability + freshness
python3.10 scripts/check_quality.py --full     # CI mirror (docs PRs finish fast; doc-pin tests still run)
```

If `python3.10` is unavailable in the Codex environment (it happened in the
#627 session), run with the available Python, record the substitution in your
verification log, and treat any check you could not run as an explicit
limitation in the doc. If live GitHub PR state is unreachable (no `gh`, no
remote — also happened in #627), say so and fall back to §2.4's pinned list,
marked "unverified-live".

### 5.7 Stop conditions (both agents)

Stop and surface (in the PR/doc, with what you found) only if: a §2.4 PR has
merged and materially rewrote your half's architecture; you find a source/docs
conflict that changes a §2 baseline fact; your scope turns out to require
runtime changes to map at all; or the two halves' boundary is wrong in a way
that forces overlap. Otherwise proceed best-effort and record limitations.

---

## 6. Copy-paste Codex prompts

> Generated per `docs/owner/agent-workflow-spec.md` §6.3. Hand each block to
> one Codex session unchanged. Both reference this standard as the schema
> authority instead of restating it.

### 6.1 Agent A prompt

```text
You are Codex mapping Agent A for SuperBot — one of TWO parallel mapping agents
working from the same standard. You map the USER-FACING half (games, economy,
community, utility, BTD6 surfaces). Agent B is concurrently mapping the
admin/moderation/setup/platform/governance half (admin, moderation, cleanup,
logging, proof_channel, role, channel, server_management, settings, diagnostic,
help, ai, setup, bootstrap access, and the help/registry composition
architecture) — that half is explicitly OUT of your scope.

Context
- Repo: menno420/superbot. Read `.claude/CLAUDE.md` first, then
  `docs/planning/platform-surface-mapping-standard-2026-06-09.md` — it is the
  BINDING standard for this session: verified baseline (§2), the mapping schema
  you must follow exactly (§3), the consistency target you judge against (§4),
  your scope partition and conflict rules (§5), and your output path (§5.5).
- Then read `docs/current-state.md` and re-verify open PRs on live GitHub.
  Expected: #638 (BTD6 game-data) in flight as a draft; #639 (AI self-awareness
  tools) merged 2026-06-09. If GitHub is unreachable from your environment,
  record the limitation and use the standard's §2.4 list marked
  "unverified-live".
- Prior art to compose with, not re-derive:
  `docs/planning/help-cog-customization-audit-2026-06-09.md` (#627),
  `docs/planning/settings-cog-centralization-audit-2026-06-09.md` (#625),
  `docs/help-command-surface-map.md`,
  `docs/setup-platform/settings-customization-command-map.md` (per-cog prior art),
  `docs/building-roadmap/hub-ui-standard.md` + `command-integration-standard.md`
  + `mother-hub-map.md`, `docs/ownership.md`, `docs/subsystems/games.md`,
  `docs/subsystems/btd6.md`.

Objective
Produce the implementation-ready mapping doc
`docs/planning/platform-mapping-a-user-surface.md` covering your 17 subsystems:
games, blackjack, rps_tournament, deathmatch, counting, chain, mining, economy,
inventory, leaderboard, xp, community, community_spotlight, utility, general,
four_twenty, btd6 (+ the five split BTD6 cogs' command surfaces). For every
subsystem, command, panel/view, and owning service: verify it in source and
record it per the standard's §3 schema — subsystem record (§3.1), command table
(§3.2), panel records (§3.3), service records (§3.4), the 11-question per-cog
checklist (§3.8) — judging against the §4 consistency target, with §3.5
verdicts, §3.6 severities, and §3.7 evidence format on every finding.

Scope
- Mapping ONLY. No disbot/ changes, no test changes, no registry edits, no
  command additions/removals. Your PR touches exactly: your output doc, your
  one pre-allocated line in the standard's §5.5 (convert your path to a
  markdown link), and your `.sessions/` log.
- BTD6: map commands/panels; the BTD6 data-service layer + BTD6 AI-tool
  internals are provisional(#638) — describe, don't recommend.
- Do NOT map Agent B's half or the help/settings architecture itself; a finding
  that crosses the boundary goes in your "Cross-boundary observations" section
  as one evidence-backed line.
- Do NOT edit docs/current-state.md, docs/roadmap.md, the help-surface map, the
  command map, any folio, or the question router. Collect owner questions in
  your doc's "Open owner questions" section as multiple-choice proposals — the
  merge session routes them.
- Skip the end-of-session backlog-grooming task (parallel-session rule).
- New feature ideas: only as §3.5 `future-opportunity` rows in your doc —
  Discord-feasible, gate-respecting (ADR-001/002/006, the ideas-lab §6
  rejection ledger, the AI/BTD6 expansion gate).

Repo checks
- For each disbot/*.py you inspect deeply, run
  `python3.10 scripts/context_map.py <path>` (if python3.10 is unavailable, use
  the available python and record the substitution).
- Before opening your PR:
  python3.10 scripts/check_docs.py --strict
  python3.10 scripts/check_quality.py --full
  (docs-only PRs run fast in CI; the doc-pin tests must stay green).

Boundaries
- Source code and merged PRs win over docs — verify, then cite file:line.
- Severity tiers and verdict labels come from the standard; do not invent
  vocabulary. Counts must come from enumeration you ran.
- If a standard §2 baseline fact is wrong, or #638/#639 merged and rewrote your
  half, record it prominently and continue best-effort (stop conditions: §5.7).

Output format
One new doc at `docs/planning/platform-mapping-a-user-surface.md`, badge line
`> **Status:** \`audit\`` with your run date + HEAD commit, structured exactly
per §3: executive summary with severity-ranked findings first, then one section
per subsystem, then Cross-boundary observations, Future opportunities, Open
owner questions, Verification log.

End of session
- Open a PR (standing consent). Title: "Platform mapping A — user surface".
  PR body: summary, test plan (the two checks), the in-flight/gate notes you
  verified, and the line "Parallel mapping agent B is concurrently mapping the
  admin/platform half; this PR maps only the user-facing half."
- Write `.sessions/<date>-platform-mapping-a.md` with a Context-delta section
  (needed-not-pointed / pointed-not-needed / discovered-by-hand).
```

### 6.2 Agent B prompt

```text
You are Codex mapping Agent B for SuperBot — one of TWO parallel mapping agents
working from the same standard. You map the ADMIN/PLATFORM half: admin,
moderation, cleanup, logging, proof_channel, role, channel, server_management,
settings, diagnostic, help, ai — plus the non-subsystem surfaces setup_cog and
bootstrap_access_cog, and the composition architecture (help_cog + help/route,
hub_registry, subsystem_registry, command_surface_ledger,
customization_catalogue, access_projection, command_routing, command access).
Agent A is concurrently mapping the user-facing half (games, blackjack,
rps_tournament, deathmatch, counting, chain, mining, economy, inventory,
leaderboard, xp, community, community_spotlight, utility, general, four_twenty,
btd6) — that half is explicitly OUT of your scope.

Context
- Repo: menno420/superbot. Read `.claude/CLAUDE.md` first, then
  `docs/planning/platform-surface-mapping-standard-2026-06-09.md` — the BINDING
  standard: verified baseline (§2), the schema you must follow exactly (§3),
  the consistency target (§4), your partition + conflict rules (§5), your
  output path (§5.5).
- Then read `docs/current-state.md` and re-verify open PRs on live GitHub.
  Expected: #638 (BTD6 game-data) in flight as a draft; #639 (AI self-awareness
  tools — touched ai_tools/ai_tool_catalogue/instruction stack) merged
  2026-06-09. If GitHub is unreachable, record the limitation and use §2.4
  marked "unverified-live".
- Your two cornerstone inputs already map your stacks in depth — verify and
  delta them rather than re-deriving:
  `docs/planning/settings-cog-centralization-audit-2026-06-09.md` (#625) and
  `docs/planning/help-cog-customization-audit-2026-06-09.md` (#627). Also:
  `docs/help-command-surface-map.md`,
  `docs/setup-platform/settings-customization-command-map.md`,
  `docs/building-roadmap/{hub-ui-standard,command-integration-standard,mother-hub-map}.md`,
  `docs/ownership.md` (esp. the Direct-vs-draft lane table),
  `docs/capability-authority.md`, `docs/subsystems/server-management.md`,
  `docs/subsystems/settings-bindings-provisioning.md`, `docs/subsystems/ai.md`,
  `docs/subsystems/health-diagnostics.md`,
  `docs/planning/server-management-status-2026-06-05.md` (authoritative
  shipped/queued), `docs/planning/multi-lane-execution-plan-2026-06-09.md`
  (Lanes 7–8 own settings-hub display + help-map count/test work — route
  findings there, don't re-plan them).

Objective
Produce the implementation-ready mapping doc
`docs/planning/platform-mapping-b-admin-surface.md` covering your 12 subsystems
+ setup/bootstrap + the composition architecture. For every subsystem, command,
panel/view, and owning service: verify in source and record per §3 — subsystem
record (§3.1), command table (§3.2), panel records (§3.3), service records
(§3.4), the 11-question checklist (§3.8) — judged against §4, with §3.5
verdicts, §3.6 severities, §3.7 evidence on every finding. For the composition
architecture, produce §3.4-style records plus an explicit "which filter applies
on which Help render path" matrix delta against the help audit §3 (what
changed since #627, if anything).

Scope
- Mapping ONLY. No disbot/ changes, no test changes, no registry edits. Your PR
  touches exactly: your output doc, your one pre-allocated line in the
  standard's §5.5 (convert your path to a markdown link), and your `.sessions/`
  log.
- AI: map the cog/panel/policy-UI surface normally. The AI tool
  registry/catalogue/instruction-stack internals changed in #639 (merged
  2026-06-09, post-baseline) — map the landed state; recommendations there
  stay blocked-by-gate(AI per-exposure) unless Q-0048's standing lift clearly
  covers them. The governance setup section is deferred (Q-0008/Q-0011): map
  current state, verdict blocked-by-gate.
- Settings hub display correctness and help-map counts/characterization tests
  are owned by queued Lanes 7–8: map current state, verdict
  blocked-by-gate(Lane 7|8) instead of proposing parallel work. Help-consumes-
  projection work belongs to Adaptive P1C — same rule.
- Do NOT map Agent A's half; boundary findings go in "Cross-boundary
  observations" as one evidence-backed line each.
- Do NOT edit docs/current-state.md, docs/roadmap.md, the help-surface map, the
  command map, any folio, or the question router. Collect owner questions in
  your doc's "Open owner questions" section as multiple-choice proposals.
- Skip the end-of-session backlog-grooming task (parallel-session rule).
- New feature ideas: only as `future-opportunity` rows — Discord-feasible,
  gate-respecting (AI per-exposure gates, Q-0048 limits, the ideas-lab §6
  rejection ledger).

Repo checks
- For each disbot/*.py you inspect deeply, run
  `python3.10 scripts/context_map.py <path>` (if python3.10 is unavailable, use
  the available python and record the substitution).
- Before opening your PR:
  python3.10 scripts/check_docs.py --strict
  python3.10 scripts/check_quality.py --full

Boundaries
- Source code and merged PRs win over docs — verify, then cite file:line.
- Severity tiers and verdict labels come from the standard; counts come from
  enumeration you ran.
- If a §2 baseline fact is wrong, or #638/#639 merged and rewrote your half,
  record it prominently and continue best-effort (stop conditions: §5.7).

Output format
One new doc at `docs/planning/platform-mapping-b-admin-surface.md`, badge line
`> **Status:** \`audit\`` with your run date + HEAD commit, structured exactly
per §3: executive summary with severity-ranked findings first, then one section
per subsystem (+ setup/bootstrap + composition architecture), then
Cross-boundary observations, Future opportunities, Open owner questions,
Verification log.

End of session
- Open a PR (standing consent). Title: "Platform mapping B — admin/platform
  surface". PR body: summary, test plan (the two checks), the in-flight/gate
  notes you verified, and the line "Parallel mapping agent A is concurrently
  mapping the user-facing half; this PR maps only the admin/platform half."
- Write `.sessions/<date>-platform-mapping-b.md` with a Context-delta section
  (needed-not-pointed / pointed-not-needed / discovered-by-hand).
```

---

## 7. After the mapping: the merge/implementation session contract

The follow-up Claude session (full envelope, plan-then-execute):

1. **Merge** both mapping docs: join on subsystem/command/panel/service keys;
   reconcile cross-boundary observations; route the collected owner questions
   into the router as proper Q-blocks (multiple-choice, ≤4 options); verify any
   finding marked `unverified-live`.
2. **Prioritize** by §3.6 severity, then by blast radius: severity-1 findings
   and root-cause/foundation fixes first (agent-workflow-spec §4.2);
   `blocked-by-gate` items route to their lanes (7, 8, P1C, PR13/14) instead of
   being implemented out of band.
3. **Implement** in risk-sized PRs (small/focused for `disbot/`), preserving:
   one command/menu architecture (no duplicate systems), the §2.2 canonical
   seams, the §2.3 decided posture, T1–T19. Every fix lands with its pinning
   test.
4. **Docs follow reality in the same PRs**: help-surface map + command map rows
   update with the surfaces they describe; this standard gets re-badged
   `historical` once the campaign's fixes ship and T-rules graduate into the
   binding docs (`one-fact-one-home` — the durable rules' homes are
   `command-integration-standard.md` / `hub-ui-standard.md` /
   `architecture.md`, not this dated plan).

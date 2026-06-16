# docs/ideas — the idea backlog & lifecycle

> **Status:** `ideas`. **Nothing here is approved for implementation.** These are
> capture docs so ideas live in the repo instead of in chat. Source code, the
> binding contracts, and `docs/current-state.md` always win over anything here.
>
> **This folder is a conveyor, not a graveyard.** The maintainer drops ideas in *any
> order, any time*; agents capture them, route each to a reasonable home, and keep the
> backlog moving so **every idea eventually becomes _implemented_ or _discussed_** (or
> explicitly _rejected_). Grooming this backlog is also the standing **secondary task** —
> what an agent does with leftover capacity once its main work + PR are done (see §
> "Backlog grooming").

## What lives here

Pure brainstorm backlogs — capture without commitment. Each file should carry an
`ideas` badge in its header and state what it is *not* (not a plan, not approval). **Once a
capture reaches its lifecycle outcome (§5) by being _implemented_, it is re-badged `historical`
during grooming** (it stays listed here, annotated ✅) so the active backlog reflects only live ideas.

Current broad captures:

- [`idea-spotlight-verdict-loop-2026-06-16.md`](./idea-spotlight-verdict-loop-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the idea-spotlight skill PR #959):** the new daily
  `superbot-idea-spotlight` surfaces an idea + asks for a verdict, but the selector has no memory of
  what the owner already decided, so a settled idea can resurface and nothing measures backlog drain.
  Give it a tiny **verdict ledger** (persist each `intake` route), bias selection toward un-decided
  ideas, and add a weekly drain-rate line to the briefing — turning the ritual into a self-draining
  decision queue. Small/decided-lane. → relates `scripts/hermes/idea_spotlight.py`.
- [`architecture-atlas-and-structure-review-2026-06-16.md`](./architecture-atlas-and-structure-review-2026-06-16.md) —
  **owner-uploaded external review + agent judgment (2026-06-16):** an outside-in repo-architecture
  review ("repository-architectuuratlas") recommending a generated **architecture atlas** over any
  filesystem reorg. Cross-checked against live source: the *direction is right* but the drift diagnosis
  is **overstated** (only 3 real stale counts remained — fixed in PR #957) and the flagship "per-file
  dashboard" is **~80% already shipped** as `context_map.py`. Genuinely-new signal: an **extension-type
  taxonomy crosswalk** (43 ext ↔ 33 subsystems, 10 non-1:1) → **✅ SHIPPED PR #958** (overlay +
  `scripts/extension_crosswalk.py` → `docs/architecture/extension-taxonomy-crosswalk.md`,
  [plan](../planning/extension-taxonomy-crosswalk-plan-2026-06-16.md)); a *thin* unified atlas (→ PR 2)
  + a root-README question → **Q-0151** (answered); count-cite guard → fold into
  `readiness-maps-cite-regen-command`. → relates `scripts/{context_map,wiring_map,review_scope}.py` ·
  `utils/subsystem_registry.py` · `architecture_rules/layers.yaml`.
- [`round-range-comparison-bare-range-list-2026-06-16.md`](./round-range-comparison-bare-range-list-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the §7.5 round-range comparison floor PR #955):** the new
  round-range cash comparison requires a round token before *each* range's first anchor (to keep
  crosspath codes like `5-0-0` out), so the natural comma-list phrasing "rounds 1-30, 30-60 or 60-80"
  (token only on the first) silently defers to the model — the BUG-0009 mis-assembly class the floor
  exists to own. Accept round-anchored bare `N-M` ranges (once ≥1 explicit round-token range is
  present) that are not crosspath-adjacent. Decided-lane; small. → relates
  `services/btd6_context_service.py::_extract_round_ranges`.
- [`btd6-ct-event-detail-relics-map-2026-06-16.md`](./btd6-ct-event-detail-relics-map-2026-06-16.md) —
  **BTD6 UX follow-up to #953 (2026-06-16, Q-0089):** the new Live Events overview drills into a rich
  detail for race/boss/odyssey, but CT has no `_towers` metadata so a live CT event shows only
  name+window — while the rich relic/hex-map data already exists in the panel's 🗺️ CT view. Bridge
  them by surfacing relics + `build_ct_map_file(ct_id)` on the CT event detail (a button, reusing the
  proven renderer; CT-gated; degrade to text when Pillow is absent). → relates
  `views/btd6/live_events_view.py` · `views/btd6/ct_map_view.py` · `services/btd6_live_query_service.py`.
- [`button-command-surface-parity-2026-06-16.md`](./button-command-surface-parity-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the `!coglist` command request PR #951):** the admin panel
  had a 📋 Cog List button but no text command — users expect a button's action to also be reachable
  by a command. A review-lane audit (not a brittle CI guard — many buttons are navigation, not
  actions) pairing distinct action-buttons with command front doors would surface the rest; a lighter
  automatable slice is mining "command not found" misses for high-frequency expected names (BUG-0014
  was one). → relates `cogs/admin_cog.py` · `core/runtime/command_surface_ledger.py`.
- [`reference-integrity-invariants-2026-06-16.md`](./reference-integrity-invariants-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the BUG-0014 `!coglist`-loop fix PR #949):** BUG-0014 was a
  dangling reference (a synonym → a command that didn't exist) that failed *silently*. Extract the
  AST command-surface discovery from the new synonym guard into a shared test helper, and close the
  known sibling gap — `SUBSYSTEMS.entry_points` → real command, which `test_entrypoints.py` documents
  as unchecked. One "what commands exist" source for every "this declaration must resolve" invariant.
  → relates `tests/unit/registry/test_entrypoints.py` · `utils/subsystem_registry.py` · `utils/synonyms.py`.
- [`server-owner-configurable-moderation-dms-2026-06-16.md`](./server-owner-configurable-moderation-dms-2026-06-16.md) —
  **owner policy → feature (2026-06-16, from the Q-0147 decision):** the owner's standing DM rule is
  *profile/onboarding DMs are opt-in and never on join; the only non-opt-in DMs are moderation/warning
  DMs, and only when the server owner enables them with per-action config.* The opt-in half is
  myprofile PR C; this captures the second half — a `moderation_dm_enabled` master + per-action map
  (warn/timeout/kick/…) on the `!settings` → Moderation surface, riding the audited `moderation_service`
  seam (off by default, fail-open). → relates `services/moderation_service.py` · the settings surface.
- [`close-timeout-align-with-platform-grace-2026-06-16.md`](./close-timeout-align-with-platform-grace-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the runtime-lock deploy-downtime fix PR #948):** make
  `LIFECYCLE_CLOSE_TIMEOUT_SECONDS` env-configurable (mirror the `RUNTIME_LOCK_BOOT_*` knobs) so an
  operator can set it **below** the platform's real SIGTERM→SIGKILL grace (~10s observed on Railway vs
  the hardcoded 20s) — defense-in-depth so the close-driver's force-exit fallback actually fires before
  the platform kills the process. Small/decided-lane follow-up. → relates `disbot/bot1.py` ·
  `disbot/services/runtime.py`.
- [`control-plane-single-source-pointer-2026-06-15.md`](./control-plane-single-source-pointer-2026-06-15.md) —
  **session idea (2026-06-15, Q-0089) — ✅ EXECUTED (PR #943):** the autonomous-loop
  control-plane truth lives in two prose homes (the canonical table in `autonomous-routines.md` **and**
  a restating bullet in `current-state.md` Gates) — the second drifted again this pass. Collapse the
  `current-state.md` bullet to a **pure pointer** at the canonical table (zero verdict prose), so one
  fact has one home and can't contradict itself; optional `check_docs` lint that the pointer stays a
  pointer. → relates `docs/operations/autonomous-routines.md` · Q-0135.
- [`honcho-memory-evaluation-2026-06-16.md`](./honcho-memory-evaluation-2026-06-16.md) —
  **bot / AI-lane idea (2026-06-16, owner wants to look into soon):** give SuperBot's AI **per-user
  memory** — remember a Discord user across conversations (V-04) — via Honcho-style
  conclusion-extraction memory (better + cheaper than dumping raw history; matters under the Q-0082
  spend ceiling). Evaluated for Hermes first and rejected there (now a footnote) — it's a **bot**
  idea, not a Hermes one. Next: promote to a `docs/planning/` plan when the AI lane has capacity.
- [`executor-chain-trigger-via-workflow-2026-06-15.md`](./executor-chain-trigger-via-workflow-2026-06-15.md) —
  **session idea (2026-06-15, Q-0089, from the eval-coverage 34/34 run; owner live concern):** the
  executor's STEP 3 self-chaining is unreliable because a `continue` issue opened by a routine *session*
  doesn't re-fire a routine (loop-prevention by event actor — the same axis as the #768 bot-author miss),
  while a cron/`ROUTINE_PAT` workflow-opened issue does (#894 fired, #887 didn't). Fix: a GitHub Action
  opens the next `continue` issue via `ROUTINE_PAT` when a session *requests* a chain, so every chaining
  trigger comes from the proven external path. → relates `docs/operations/autonomous-routines.md`.
- [`dispatch-phase-gate-precheck-2026-06-15.md`](./dispatch-phase-gate-precheck-2026-06-15.md) —
  **session idea (2026-06-15, Q-0089, from the mining-Phase-2 feature dispatch):** run
  `check_phase_gate.py --phase` at the **dispatcher** before firing a `CLASS: feature` work
  order — if `fix`, re-route to the fix-phase queue or hold the feature until invent-phase,
  instead of burning a fire on capture-and-stop (and risking a stuck "slice opener" PR like
  #888). Executor-side gate stays the backstop. → relates Q-0137 Thread 1.
- [`games-economy-faucet-sink-diagnostic-2026-06-14.md`](./games-economy-faucet-sink-diagnostic-2026-06-14.md) —
  ✅ **PROMOTED to a plan (2026-06-15, band-#930 pass → `historical`):** a read-only operator read
  model that sums the economy audit ledger (`mining:sell_ore` faucet vs. `buy`/`repair`/`respec`/
  `build`/`vault_upgrade` sinks) into a per-guild net-coin-flow view — *observe* the self-balancing
  loop live. The gate (a sink-heavy slice landing) was cleared by respec #912 + structures #905/#910;
  now [`planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md`](../planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md)
  (turn-key, read-only).
- [`routine-dispatch-and-staged-reconciliation-2026-06-14.md`](./routine-dispatch-and-staged-reconciliation-2026-06-14.md) —
  **owner design conversation (2026-06-14, → Q-0137 DISCUSS):** three linked threads — (1) dispatch every
  routine via Hermes *except* reconciliation (the watchdog); (2) evolve reconciliation into a staged,
  resumable **deep-clean** with a checkable terminal condition; (3) a **planning-sector** taxonomy
  (bot · BTD6 · agent substrate · **+ a forgotten Operations/control-plane sector**) distinct from the
  `repo-review-map.md` review taxonomy. Captured owner direction + agent opinion; not approved.
- [`dispatch-resolution-json-hermes-2026-06-14.md`](./dispatch-resolution-json-hermes-2026-06-14.md) —
  ✅ **EXECUTED → `historical` (2026-06-16, PR #959, owner-directed):** `scripts/dispatch_menu.py --json`
  shipped **and** the Hermes-wiring half landed as the new **`superbot-dispatch-resolve`** skill, so
  *"dispatch S2"* resolves to a concrete work order and routes by the resolved **executor**
  (`Claude-in-repo` → `/fire`; `Hermes-VPS` → Hermes does it; `maintainer` → tell the owner). Originally
  the 2026-06-14 Q-0089 session idea (the read-side of **Q-0137 Thread 1**; the broader cron-backstop
  part of Thread 1 stays owner-undecided).
- [`routine-system-improvements-2026-06-14.md`](./routine-system-improvements-2026-06-14.md) —
  **workflow / routine-system (2026-06-14, owner-requested):** first-hand field notes from a live
  routine run on making the unattended Hermes-dispatch loop smoother. Core orientation already
  works (a 2-word trigger still produced a correct end-to-end run); the weak links are the *edges*.
  Prioritized: **(1)** a standardized **run-report block** in the session log (the artifact Hermes
  summarizes — with required "owner decisions needed" / "owner manual steps" fields that otherwise
  vanish); **(2)** align the routine prompt with reality (the `PushNotification` it centers on isn't
  provisioned — the human is reached via Hermes reading artifacts); **(3)** get Hermes to use the
  dispatch contract it already has (my fire was bare "auth probe"); **(4)** a repo-area map for
  non-overlapping parallel dispatch; **(5)** owner-directed-vs-agent-feature phase-gate clarity +
  a "productive once started" fallback ladder.
- [`agent-env-credential-smoke-check-2026-06-14.md`](./agent-env-credential-smoke-check-2026-06-14.md) —
  **tooling (2026-06-14, the `auth probe` routine / PR #840):** a stdlib `check_agent_env.py` that
  does a minimal authenticated round-trip for each external credential the env *claims* to provide
  (Railway / Anthropic / OpenAI), printing PASS/SKIP/FAIL at SessionStart. Absence = SKIP, only
  present-but-broken = FAIL. Surfaced because the owner's Railway access sat **silently inert** (a
  var-name mismatch + a Cloudflare UA block) until a routine happened to probe it by hand — this
  would have flagged both on the first session after provisioning. Small; one script + a hook line.
- [`external-cron-trigger-for-routines-2026-06-14.md`](./external-cron-trigger-for-routines-2026-06-14.md) —
  **workflow / ops (2026-06-14, workflow-health review):** drive the overnight cadence from an
  external scheduler hitting `workflow_dispatch` (a VPS cron, a Worker) instead of GitHub's
  best-effort `schedule:` cron — observed firing ~4¾ h late / occasionally dropped this session.
  Converts "sometime in a ~5 h window" into "at the time I chose". Small; one cron line on the
  already-live Hermes VPS, GitHub `schedule:` kept as a backstop.
- [`routine-activity-visibility-2026-06-14.md`](./routine-activity-visibility-2026-06-14.md) —
  **workflow / UX (2026-06-14, owner-observed):** routine *run* sessions are hidden from the
  Recents tab (intentional upstream behavior; open FR
  [anthropics/claude-code#54517](https://github.com/anthropics/claude-code/issues/54517)), so there
  is no at-a-glance "is a session active?" signal. Can't change the app UI — the DIY fit is a
  **Discord webhook ping** from each routine on start/finish (ask-gated: needs a channel + webhook).
- [`scheduled-maintenance-registry-2026-06-14.md`](./scheduled-maintenance-registry-2026-06-14.md) —
  **tooling / arch (2026-06-14, P0-2 media-retention session):** a central
  `register_maintenance(name, interval, coro, owner)` registry + one runner cog, to retire the
  "mint a whole cog per `tasks.loop`" tax (counters / spotlight / role / the new
  `media_maintenance_cog`) and give periodic work the observability it currently lacks (last-run /
  result / next-run / error per job — also feeds the P0-2 media-diagnostics follow-up). Surfaced
  by this session minting a zero-command cog just to host one purge loop. Medium; slice
  registry-first then migrate loop cogs one PR at a time.
- [`readiness-map-claim-vs-source-guard-2026-06-14.md`](./readiness-map-claim-vs-source-guard-2026-06-14.md) —
  **tooling (2026-06-14, P0-4 PR 2 session):** a guard that fails when a readiness-map /
  ownership row's **routing claim** ("routes through X", "uses the Y lane", "Done") contradicts
  the cited source file (reusing the channel invariants' forbidden-call sets). Surfaced by a real
  drift this session caught — `create_panel.py` was marked "uses the provisioning lane" while the
  source called `guild.create_text_channel` directly. Lifts the per-PR `test_no_direct_*`
  invariants up to the docs that describe them. Small/safe grooming-lane candidate.
- [`decade-queue-lead-with-the-active-thread-2026-06-15.md`](./decade-queue-lead-with-the-active-thread-2026-06-15.md) —
  **workflow / process (2026-06-15, band-#900 reconciliation pass):** lead the decade queue with the
  thread that filled the *previous* band's "buffer / steered" slot, as a named top-tier slot, instead
  of deriving the queue from the static P0→P1→safety priority list. Four bands running had their
  headline work happen in the buffer slot (Railway · Hermes control-plane · mining structures), so the
  queue's lead keeps mis-predicting where the next band's energy goes. The *promote*-recurring-buffer
  complement to the slot-carry *detect* + the §6 owner-slot *demote* rules. Docs/process-only;
  promote into the routine prompt if a fifth band repeats the pattern.
- [`reconciliation-slot-carry-tracker-2026-06-14.md`](./reconciliation-slot-carry-tracker-2026-06-14.md) —
  **workflow / tooling (2026-06-14, band-#870 reconciliation pass):** a stdlib check that parses the
  chain of `reconciliation-pass-*.md` §4 queue tables and reports, per recurring slot, how many
  consecutive bands it has **carried unexecuted** (matched on scope-anchor text, not the unstable
  `#` column). Turns the band-#870 §6 "escalate if a slot carries a fourth band" rule into a
  self-firing guard so gated/owner-steered work can't silently rot in a plan that keeps re-listing
  it — the plan-slot cousin of the open-PR-with-state stale-PR snapshot. Composes with the
  print-subjects/pre-brief family. Runtime-lane (new `scripts/` check), out of scope for a docs-only pass.
- [`reconciliation-prebrief-at-session-start-2026-06-14.md`](./reconciliation-prebrief-at-session-start-2026-06-14.md) —
  **workflow / orientation (2026-06-14, band-#840 reconciliation pass):** when a recon pass is
  due, have the SessionStart hook drop a `reconcile-prebrief.txt` with the band computed —
  every merged PR since the marker annotated `[in-ledger|MISSING]` + subject, the open-PR-with-state
  snapshot, and the ratchet delta — so the routine reads one file instead of re-deriving with ~10
  tool calls. *Composes* the print-subjects idea (build that first); orientation-lane, not a
  checker change. Surfaced by this pass spending ~8 tool calls deriving the band by hand before any
  reconciliation thinking. Runtime-lane (hook + `scripts/`), so out of scope for a docs-only pass.
- [`grounding-completeness-claim-primitive-2026-06-14.md`](./grounding-completeness-claim-primitive-2026-06-14.md) —
  **AI faithfulness (2026-06-14, the #855 path-resolution session):** promote the ad-hoc "these
  are every X" roster sentence (#855's path header, the rosters, the capabilities reply) into a
  first-class grounding primitive that emits a **parseable completeness marker** — so the
  faithfulness guard can gain a *completeness* check beside its value check and catch the
  **BUG-0009** long-list drop/add class (which "maps have water" → 64 vs 69). Emit side is cheap
  retrieval; the guard check rides with absence-guard Layer B. Routes to AI orchestration §7 /
  the absence-claim family.
- [`ledger-checker-print-pr-subjects-2026-06-14.md`](./ledger-checker-print-pr-subjects-2026-06-14.md) —
  **✅ implemented (2026-06-14, band-#840 queue slot 9):** `check_current_state_ledger.py` now
  prints each **missing PR's merge-commit subject** next to its number (via the memoized
  `_git_merged_pr_map`), collapsing the reconciler's manual `git log --grep` loop and reducing
  mis-attributed ledger entries.
- [`cogs-layer-view-residence-guard-2026-06-14.md`](./cogs-layer-view-residence-guard-2026-06-14.md) —
  **tooling / arch invariant (2026-06-14):** a guard flagging `discord.ui.View`/`Modal`
  subclasses **defined under `cogs/`** — invisible to the baseview ratchet (which only scans
  `views/`). Surfaced when the `!list` paginator was found mislayered in `channel_cog.py`
  only by tripping the cog-size ceiling. Warn → ratchet. Small/safe grooming-lane candidate.
- [`diagnostic-cog-platform-group-extraction-2026-06-16.md`](./diagnostic-cog-platform-group-extraction-2026-06-16.md) —
  **refactor / near-term blocker (2026-06-16) — ✅ EXECUTED (PR #943):** moved the `!platform`
  command group off `DiagnosticCog` onto a `PlatformCommandsMixin` (`cogs/diagnostic/platform_group.py`);
  the cog dropped 799 → 260 LOC, clearing the 800-LOC ceiling. Pinned by
  `tests/unit/cogs/test_diagnostic_platform_group.py`.
- [`ledger-guard-exempt-reconciliation-prs-2026-06-16.md`](./ledger-guard-exempt-reconciliation-prs-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the diagnostic-mixin dispatch #943):** a
  `docs(current-state): reconcile ledger` PR structurally can't list its own (not-yet-assigned)
  number, so it always omits itself and `check_current_state_ledger.py --strict` flags it next
  session (the #942 drift this run fixed). Teach the guard to **skip a docs-only ledger-bookkeeping
  PR** (title + diff-confined-to-`current-state*.md`), closing the recurrence at the guard level.
  **✅ Shipped 2026-06-16 (Q-0152):** implemented as a `reconcil`-in-merge-subject exemption in
  `find_missing` (the diff-confinement bound was deferred as merge-strategy-fragile; subject-match is
  tight + disposable per Q-0105). Tests in `test_check_current_state_ledger.py`.
- [`autospec-mock-fidelity-guard-2026-06-16.md`](./autospec-mock-fidelity-guard-2026-06-16.md) —
  **tooling/testing (2026-06-16):** make project mocks signature-faithful (`create_autospec` /
  `AsyncMock(spec=…)`) via a lint/AST guard or a tiny `autospec_setattr` helper, so a call-site
  kwarg typo that the real function would reject also fails the test. Born from the BTD6 drill-down
  crash that shipped green because a bare `AsyncMock` masked a `search_facts(entity_key=…)` signature
  mismatch. Small/safe tooling-lane candidate.
- [`effective-check-constraint-test-helper-2026-06-14.md`](./effective-check-constraint-test-helper-2026-06-14.md) —
  **tooling (2026-06-14, PR #817):** a shared `effective_check_constraint(table, column)` test
  helper that derives the *current* SQL `CHECK (col IN …)` set by scanning all migrations in
  order, so the bespoke per-table **alignment tests never need manual repointing** when a
  constraint is widened in a later migration (059→op_kind, 069→actor_type each hand-rolled it).
  Small/safe grooming-lane candidate.
- [`ux-lab-interface-gallery-2026-06-12.md`](./ux-lab-interface-gallery-2026-06-12.md) —
  **owner-commissioned design (2026-06-12):** the **UX Lab** — a zero-write, admin-gated
  gallery cog (`!uxlab`) exhibiting every Discord interaction/layout pattern the pinned
  library supports (buttons · all 5 selects · modals incl. Label-wrapped selects · embed
  card archetypes · **Components V2** layouts (verified: 40-child/4 000-char budget on
  discord.py 2.7.1) · PIL cards), plus a **platform-limit probe bench** and clickable
  **mockups of the approved Q-0108–Q-0112 features**. Each exhibit carries registry
  metadata (`pattern_id`, status, limits) that graduates into `docs/ux/pattern-library.md`
  — the bot's design vocabulary. **State: IMPLEMENTED same day** (owner-steered):
  PRs **#758 / #760 / #762**, 2026-06-12 — the design
  ([plan](../planning/ux-lab-interface-gallery-plan-2026-06-12.md), now `historical`)
  shipped end-to-end; the durable artifact is
  [`../ux/pattern-library.md`](../ux/pattern-library.md) (Q-0116 records the call).
- [`server-safety-and-automod-2026-06-12.md`](./server-safety-and-automod-2026-06-12.md) —
  **owner-uploaded research (2026-06-12):** four moderation-safety modules SuperBot
  lacks vs. competitors (Carl-bot, Dyno, YAGPDB, Koya, Double Counter):
  **automod rules engine** (spam/link/caps/mention filtering with per-rule escalation) ·
  **server logging service** (message edits/deletes, join/leave, role changes) ·
  **image moderation** (OpenAI omni-moderation free endpoint vs. API4AI vs. Hive 50+
  categories) · **security service** (raid detection, account-age filter, alt detection,
  VPN blocking — tiered by privacy risk). **Decisions ANSWERED 2026-06-12
  (Q-0108/Q-0109/Q-0111, PR #740):** automod (all 4 rule types) + OpenAI-only image
  moderation + logging v1 + security tiers 1+2 **approved, plan-first** (routed to the
  roadmap's safety/community lane); security tiers 3+4 + paid image tiers declined.
- [`community-platform-features-2026-06-12.md`](./community-platform-features-2026-06-12.md) —
  **owner-uploaded research (2026-06-12):** five community-management features from
  ProBot, Koya, YAGPDB, Sesh, and Statbot:
  **welcome service** (PIL avatar-composited welcome cards, join DM, auto-role, goodbye) ·
  **social feed notifications** (YouTube-first per Q-0041, then Twitch/RSS/Reddit, with
  optional LLM video summarization) ·
  **event scheduler** (simple RSVP tier first; NL parsing gated on AI cost) ·
  **custom commands** (TagScript-safe, DB-stored, admin-only creation) ·
  **dynamic server counters** (statdock channel-renaming, quick-win candidate).
  **Decisions ANSWERED 2026-06-12 (Q-0110/Q-0112, PR #740):** welcome = embed-first,
  PIL cards phase 2; event scheduler = NL parsing from day one (Q-0082-metered) —
  both **approved, plan-first** (routed to the roadmap's safety/community lane).
- [`repo-manageability-2026-06-12.md`](./repo-manageability-2026-06-12.md) — ✅ **EXECUTED →
  `historical`** (2026-06-13 reconciliation): #1/#2/#3/#5 shipped (`scripts/{review_scope,_review_units,
  readiness_scoreboard,check_doc_freshness}.py` + the `current-state.md` trim/ratchet), #4 resolved via
  Q-0101. Originally (owner-asked 2026-06-12) five workflow-substrate manageability ideas.
- [`voice-mode-planning-capture-2026-06-11.md`](./voice-mode-planning-capture-2026-06-11.md) —
  **voice-mode brainstorm (2026-06-11):** UX and product ideas from a casual spoken planning
  session via ChatGPT. Covers setup wizard clarity, centralized settings navigation, help-menu
  modernization, crafting filters, craft-and-equip shortcut, deeper mining/chopping progression,
  world/exploration hub concept, idle/pets/co-op/NPC ideas, and routing notes per candidate.
  Strongest near-term candidates: crafting UX polish + AI settings clarity.
- [`ci-cost-and-duplicate-work-prevention-2026-06-14.md`](./ci-cost-and-duplicate-work-prevention-2026-06-14.md) —
  **owner-asked (2026-06-14, Q-0126):** `code-quality.yml` is the repo's dominant CI cost
  (940 runs / 2,396 min/month). **(a) CI efficiency — SHIPPED (PR #814):** concurrency
  cancellation of superseded PR runs + pip/mypy caching. `pytest -n auto` was tried (3× faster)
  but **reverted** — CI proved the suite isn't parallel-safe (non-deterministic state pollution).
  **(b) duplicate-work prevention — DECIDED & implemented:** claim ledger (`docs/owner/active-work.md`)
  + push-batching. **Live remaining idea:** make the suite parallel-safe → re-enable xdist (the
  ~3× unlock).

> **Standing intake note (Q-0089, 2026-06-10):** every session now *generates*
> one new `💡 Session idea` at END (owner directive — consistent generation
> beats occasional brilliance). Substantial ones land here as files; small ones
> live in their session log's 💡 flag. The grooming pass then moves them.

- **`scripts/command_surface_dump.py`** *(Q-0089 session idea, 2026-06-12 — **EXECUTED
  same session as grooming pass**)* — offline AST-based command-surface dump: reads
  all cog files without a live bot and emits every prefix/slash/group command by
  subsystem. `--diff-checklist` flags commands in source with no checklist entry (found
  120 gaps on first run — expected, as the checklist covers hub-level entries not individual
  commands). 8 tests. Makes `docs/audits/untested-surface-checklist.md` machine-verifiable
  going forward.

- [`wager-flow-map-2026-06-12.md`](./wager-flow-map-2026-06-12.md) —
  **session idea (2026-06-12, Q-0089, from the P0-1 wager-safety session #748):** a
  read-only offline `scripts/wager_flow_map.py` that traces every game's money path
  (accept→escrow→settle/refund, entry→payout) from the new `game_wager_workflow` call
  sites + `*_escrow` subsystems — the human-readable companion to the
  `test_game_wager_write_boundary` fence, with a `--check` drift mode (every escrow
  subsystem must have a matching settle + recovery). Quick-win, read-only tooling lane;
  build it next time an economy path is touched. Not auto-promoted.
- [`review-unit-tagging-2026-06-12.md`](./review-unit-tagging-2026-06-12.md) — ✅ **EXECUTED →
  `historical`** (2026-06-13 reconciliation): shipped as `scripts/review_scope.py` +
  `scripts/_review_units.py` + the `context_map.py` "Review unit" line. Originally a 2026-06-12
  Q-0089 session idea to make the repo-review partition a toolchain signal.
- [`portable-agent-memory-package-2026-06-12.md`](./portable-agent-memory-package-2026-06-12.md) —
  **maintainer vision (2026-06-12, voice):** extract this repo's consistent-memory +
  self-improving-workflow substrate into a standalone **open-source package** (à la CodeGraph)
  — the externalization of the "real artifact" CLAUDE.md already names. Carries a **priority
  reorientation**: lead with memory/workflow-substrate improvements so sessions auto-execute
  bot work. Core hard problem = mechanism-vs-content separation; sequencing = harden in-repo
  first (no approval needed), extract later. → **GRADUATED 2026-06-13 to an approved executable
  plan:** [`../planning/portable-substrate-kit-extraction-2026-06-13.md`](../planning/portable-substrate-kit-extraction-2026-06-13.md)
  (10 review rounds + owner approval; entry point PR 1a).
- [`autonomous-improvement-loop-vision-2026-06-12.md`](./autonomous-improvement-loop-vision-2026-06-12.md) —
  **maintainer vision (2026-06-12, voice):** the north-star — agents continuously improve
  the bot, chain session→session autonomously (idea → revised plan → implement), gate
  agent-*generated* features behind correctness (bugs/UX first), and use **Hermes as the
  independent reviewer** (a non-Claude "different mind" that critiques plans + implementations,
  explains features to the maintainer, and routes his approve/deny verdict). Maps each claim
  to existing scaffolding (`ai-project-workflow.md` §10/§11, the idea lifecycle); the loop is
  ~3 seams short. Decomposes into reviewable steps (dispatch bridge → reviewer seam → phase
  gate) → **discuss lane**.
- [`hermes-claude-dispatch-bridge-2026-06-12.md`](./hermes-claude-dispatch-bridge-2026-06-12.md) —
  **session idea (2026-06-12, Q-0089):** let Hermes *trigger* a Claude Code-on-the-web
  session from Telegram (not just prepare the prompt), closing the autonomous loop —
  phone idea → Hermes orients + dispatches → Claude Code builds/tests/PRs/self-merges →
  Hermes reports back. Preserves the safety split (Hermes read-only; Claude Code mutates
  under CI gates). Needs web-trigger API research → **discuss lane** (router Q-block).
- [`claude-code-plugins-evaluation-2026-06-12.md`](./claude-code-plugins-evaluation-2026-06-12.md) —
  **owner-asked (2026-06-12):** "any good Claude (Code) plugins useful for us?" —
  ecosystem survey (official + community marketplaces, spot-verified), filtered
  against our existing hooks/skills/CodeGraph stack. Verdict: most categories
  duplicate or fight our bespoke workflow; shortlist = **Context7** (live
  version-pinned library docs, strongest), read-only **Postgres MCP**, trial-only
  `pyright-lsp`. Supply-chain posture + pinning rules included. Adoption =
  executable-config change → routed to **Q-0096** (discuss lane).
- [`ai-panel-inplace-navigation-2026-06-11.md`](./ai-panel-inplace-navigation-2026-06-11.md) —
  **owner-requested (2026-06-11 live session):** the AI settings/panel family
  spawns a new ephemeral message per navigation click, scatters config across seven subpanels + a flat scalar editor (second owner ask: centralize), and extends raw
  `discord.ui.View` behind a blanket `views/ai/` yaml exemption (ratchet-invisible
  debt). Migrate it to the rest-of-bot in-place HubView pattern (V-02 navigation
  doctrine); source-confirmed diagnosis + scope sketch in the file.
- [`gap-analysis-2026-06-11.md`](./gap-analysis-2026-06-11.md) — six
  dedup-verified blind spots from the owner's "what's still missing?" probe:
  cross-server character identity (**Q-0091**, the public-era architectural
  question) · per-user data export/erasure (V-15's mirror) · owner alerting /
  dead-man's switch · session telemetry (quantify the self-improvement loop) ·
  AI spend metering (the Q-0082 instrument) · toolchain rot watch (live
  example: the Node-20 actions deprecation, forced 2026-06-16).
- [`bot-self-test-walker-2026-06-10.md`](./bot-self-test-walker-2026-06-10.md) —
  owner idea (brainstorm round 3): **the bot tests itself** — an owner-gated
  in-process walker that synthetically invokes every ledger-listed command
  (EventBus as witness, governance audience simulation, scratch test guild)
  + an AI eval mode running scripted prompts through the real pipeline
  (Q-0086 keys). Pairs with the commissioned untested-surface testing
  checklist; candidate probe set for the workflow-§10 Stage 1 caretaker.
  **→ Routed Later (structure-or-defer, 2026-06-13):** clear direction but bigger; pairs with
  P1-1 AI eval matrix and wants its own plan before building (roadmap → agent-ecosystem / Later).
- [`hermes-bug-triage-flow-2026-06-13.md`](./hermes-bug-triage-flow-2026-06-13.md) —
  **owner-directed (design captured, build next):** route `/bugreport` *through Hermes*
  (spam/genuine triage → reproduce + reword + fetch logs → save a curated `bug` issue +
  Discord summary) → nightly executor batch-fixes. Replaces the current direct instant-fire.
  **→ Routed Next (2026-06-13, roadmap agent-ecosystem lane); gated on Q-0121** — Hermes's
  second sanctioned write (`gh issue create`) needs an owner decision (the Q-0117 pattern).
- [`backup-integrity-check-2026-06-13.md`](./backup-integrity-check-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the backup-posture session):** add a dump
  integrity step to `backup-db.yml` — verify the dump contains ≥ threshold `CREATE TABLE`
  statements before uploading, catching the silent empty-dump failure class (pg_dump exits 0
  on permission errors). Turns the backup posture from "uploads something" to "uploads a
  verifiable schema snapshot." Small one-step addition; quick-win ops lane.
  ✅ **EXECUTED → `historical` (2026-06-13):** the `CREATE TABLE`-count gate shipped in `backup-db.yml`.
- [`safety-community-operator-landing-2026-06-13.md`](./safety-community-operator-landing-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the welcome+counters slot-6 session):** a read-only
  operator landing (`!safety` / Settings supergroup) aggregating the lane's scattered
  subsystems (automod · logging · welcome · counters · image-mod · security) with each
  master-flag state + a jump to its `!settings` group. Closes the operator-discoverability
  cost of going hub-less; composes from the existing schema registry (zero new state).
  Sequence after the lane's remaining slices land.
- [`readiness-maps-cite-regen-command-2026-06-13.md`](./readiness-maps-cite-regen-command-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the P0-3 settings pointer-lane session):**
  `production-readiness/*` maps embed frozen inventory counts that rot the moment a feature
  lands (the settings map was 1 day old and already wrong — 36/13 claimed vs 65/17 real).
  Convention (soft `check_docs` rule): a map stating a count must cite its regen command
  (`scripts/settings_lane_matrix.py`, `command_surface_dump.py`) beside it. Source-wins
  applied to the doc class most prone to drift.
- [`live-decade-queue-pointer-invariant-2026-06-13.md`](./live-decade-queue-pointer-invariant-2026-06-13.md) —
  **session idea (2026-06-13, Q-0089, from the third Q-0107 reconciliation pass):** a small
  invariant (extend `check_docs.py`) asserting the "one live queue" rule on disk — exactly one
  non-`historical` `reconciliation-pass-*.md`, and the current-state ▶ + roadmap pointers both
  resolve to it. Turns a convention every pass must remember into a CI guard; motivated by the
  three pointers this pass hand-verified. Workflow lane; quick-win when capacity allows.
- [`ledger-guard-benign-lag-vs-drift-2026-06-14.md`](./ledger-guard-benign-lag-vs-drift-2026-06-14.md) —
  **session idea (2026-06-14, Q-0089, from the ledger-guard-hardening slice):** have
  `check_current_state_ledger.py` distinguish **benign newest-merge lag** (the newest ~2 merges,
  or anything newer than the `Last reconciliation pass: #M` marker — expected, informational)
  from **real drift** (an older PR never recorded — actionable), and gate `--strict` on drift
  only. Removes the standing false-red `/session-close --strict` hits on every session whose
  newest sibling merge lags. Workflow lane; small. Pairs with the two shipped guard slices.
- [`ledger-checker-range-scope-2026-06-13.md`](./ledger-checker-range-scope-2026-06-13.md) —
  **✅ implemented (2026-06-14, paired with the print-subjects slice):**
  `check_current_state_ledger.py`'s `known_ledger_numbers` now expands `#AAA–#BBB` ranges only
  inside `## Recently shipped` (+ the whole archive), so a forward-looking planning range in the
  `▶ Next action` pointer can no longer silently mask a whole merged band from the ledger guard
  (the band-#800 false-green that hid ~14 PRs). Individual `#N` refs still count everywhere; the
  convention mitigation stays good practice but is no longer load-bearing.
- [`executable-verification-over-prose-verified-2026-06-12.md`](./executable-verification-over-prose-verified-2026-06-12.md) —
  **orientation-review capture (2026-06-12):** make evidence status machine-checkable — turn prose
  "verified" checklist items into executable checks/CI tests, or label them explicitly manual with a
  trace ID; treat any item without a verification rule as implicitly unverified. Prevents
  rot-by-narrative. Workflow lane.
- [`lane-scoped-session-state-2026-06-12.md`](./lane-scoped-session-state-2026-06-12.md) —
  **orientation-review capture (2026-06-12):** cut the parallel-session merge tax by making
  in-flight session state lane-scoped by default (per-lane sub-files under `.sessions/` + `docs/ideas/`,
  scoped Q-router prefixes), aggregated on demand — prevention rather than after-the-fact UNION/renumber
  cleanup. Workflow lane; partially embodied by the existing per-`.sessions/`-file + ledger-discipline rules.
- [`single-canonical-execution-pointer-2026-06-12.md`](./single-canonical-execution-pointer-2026-06-12.md) —
  **orientation-review capture (2026-06-12):** enforce that exactly one doc is canonical for "what do I
  execute next," and a superseding plan must repoint the old one in the same commit. **Overlaps
  [`live-decade-queue-pointer-invariant-2026-06-13.md`](./live-decade-queue-pointer-invariant-2026-06-13.md)**
  (the later, more specific form) — grooming to reconcile the two into one invariant.
- [`setup-wizard-onboarding-planner-spec.md`](./setup-wizard-onboarding-planner-spec.md) —
  **preserved target-scope spec (from closed issue #232, owner 2026-05-21):** the full
  guided server-onboarding planner — scan → propose plan → presets → `SetupOperation` drafts →
  Final Review, with confidence/conflict-detection/completeness-scoring/post-setup-summary. Much
  is now the active setup-platform lane; this preserves the original vision + the open-tail
  enhancements. Settings/setup lane.
- [`media-quota-health-finding-2026-06-14.md`](./media-quota-health-finding-2026-06-14.md) —
  **small, decided-lane (Q-0089 session idea):** bridge PR #854's process-local media
  provider-outcome counters (quota_limited / timeout) into the persistent health-findings
  store (#843, Q-0097) so recurring YouTube quota exhaustion is visible across restarts, not
  just within one boot. Content-free; reuses the findings seam. Sequence after the
  provider-execution hardening follow-up.
- [`rps-tournament-service-refactor.md`](./rps-tournament-service-refactor.md) —
  **preserved refactor spec (from closed issue #229, owner 2026-05-20):** move RPS tournament
  orchestration/state out of `rps_tournament_cog.py` into an `RpsTournamentService` (5-step
  decomposition; the money seam already audited via `game_wager_workflow`). Games lane; medium-high
  before new tournament features.
- [`superbot-vision-2026-06-10.md`](./superbot-vision-2026-06-10.md) — the
  maintainer's written **product vision statement** (2-minute setup, panel
  navigation doctrine, 4-button help home, per-user preferences, RPG
  difficulty/survival/energy design, story pets, AI-as-panel-orchestrator) +
  the agent's creative response (AG-01…AG-15), dedup-mapped against every
  existing capture/plan/decision, with flagged tensions (T-1…T-5) and a routing
  ledger. **Newest owner-voice capture — read alongside the 2026-06-08 one.**
- [`fun-and-ease-brainstorm-2026-06-09.md`](./fun-and-ease-brainstorm-2026-06-09.md) —
  24 dedup-verified new ideas for "more fun + easier to use" (social/competition layer,
  ambient delight, member UX), each grep-checked against docs *and* source before
  capture. Owner cluster picks recorded (Q-0053): **pets & companions** (structured →
  [`../planning/pets-companions-plan-2026-06-09.md`](../planning/pets-companions-plan-2026-06-09.md)),
  context-menu actions, persistent reminders.
- [`cog-improvement-audit-2026-06-08.md`](./cog-improvement-audit-2026-06-08.md) —
  cog-by-cog improvement audit from a 36-question interactive session (2026-06-08).
  Covers all 35 existing cogs; includes a priority-ranked routing table. Top finding:
  setup wizard is P0 (half its steps do nothing); AI cog settings and RPS tournament
  decoupling are next.
- [`owner-vision-ideas-2026-06-08.md`](./owner-vision-ideas-2026-06-08.md) —
  20-question interactive session with the maintainer (2026-06-08); covers games
  (poker, idle), economy (marketplace, streaks), AI (dungeon master, NL, events),
  social (guilds, achievements, profiles), integrations (Twitch, YouTube, Spotify,
  Steam), and UX priorities. Includes a routing summary table. **Start here for
  the most up-to-date owner preferences.**
- [`future-product-direction-2026-06-07.md`](./future-product-direction-2026-06-07.md) —
  source-aware future product direction across polish, extensions, reusable systems,
  and long-term expansions; capture-only, not a roadmap.
- [`settings-presets-and-ai-template-advisor.md`](./settings-presets-and-ai-template-advisor.md) —
  the **Q-0070 presets-everywhere posture** (decided — routed to settings-audit
  Phase 4) + the **AI template/preset advisor** idea (modular prompt designs/styles
  as AI-cog settings so the AI can suggest the right template per task; captured
  only, gated).
- [`ai-extra-tool-capability-ideas.md`](./ai-extra-tool-capability-ideas.md) — AI
  extra-tool capability backlog (capture only, not approved work).
- [`mining_exploration_brainstorm.md`](./mining_exploration_brainstorm.md) — design-intent
  for the mining subsystem, referenced by `disbot/cogs/mining/exploration.py`.

Related idea-shaped docs that live elsewhere **by design**:

- `docs/planning/superbot-ideas-lab-2026-06-05.md` — brainstorm backlog, **but** its
  §2 (operating decisions) and §6 (rejection ledger) are **binding** "do-not-propose"
  — so it stays in `planning/`, not here.

## The idea lifecycle

```text
(1) INTAKE      maintainer drops an idea, any time, any order
      ↓         → capture it in docs/ideas/<topic>.md (state: raw → captured)
(2) MAP         name the owning subsystem, rough size, rough risk
      ↓
(3) ROUTE       send it to ONE reasonable home:
      ├─ small + safe + in an active lane → quick-win (execute now or next session)
      ├─ clear direction, bigger          → structured plan in docs/planning/ + a
      │                                      horizon on docs/roadmap.md (Now/Next/Later/Someday)
      └─ excessive / ambiguous / product  → DISCUSS FIRST: a Q-block in
                                             docs/owner/maintainer-question-router.md
(4) GROOM       leftover-capacity work: pull one routable idea forward (see below)
      ↓
(5) OUTCOME     every idea ends as exactly one of:
                implemented · on the roadmap at a horizon · in discussion (router) · rejected
```

**Routing rule — never auto-promote.** An idea is *captured and routed*, not promoted to
active work, unless the maintainer says so or it exposes a blocker / safety / architecture
conflict (`.claude/CLAUDE.md` Working agreement; `docs/collaboration-model.md`). Routing
just gives every idea a **state** and a **next destination** so none sits at `raw`.

**"Discuss if excessive."** If an idea is large, ambiguous, or a product-vision call,
the right route is a router Q-block — not silent promotion and not silent drop. The
maintainer's answer then sends it back onto this lifecycle (roadmap horizon, plan, or the
rejection ledger).

## Promotion gates (idea → implementation plan)

An idea may graduate to an implementation plan only after **all** of:

1. **Ownership** — the owning service / cog / pipeline is identified (`docs/ownership.md`).
2. **Reuse check** — existing service/helper/abstraction reuse is confirmed; no
   duplicate systems (`docs/helper-policy.md`).
3. **Risk review** — privacy, security/permissions, cost, and moderation risk reviewed.
4. **Mechanics** — migration / cache / test / rollback needs are listed.
5. **Promotion** — `docs/current-state.md` marks it an active candidate (and/or it lands
   on `docs/roadmap.md` at a horizon).

> **Idea-state vocabulary maps here.** The shared idea-states used across the AI projects
> (`raw → captured → … → shipped`, see
> [`../owner/ai-project-workflow.md`](../owner/ai-project-workflow.md) §5) are just words
> for an idea's position on *this* lifecycle plus the question-router question-lifecycle.
> This README owns the `captured → ready-for-planning → shipped` gates; the workflow doc
> references them — it does **not** define a parallel tracker.

## Backlog grooming (the standing secondary task)

So an agent **always has a next thing to do** — and so the backlog actually drains — every
session ends with a grooming pass once the main task + PR are done and capacity remains:

1. **Browse** `docs/ideas/` (and any new ideas the maintainer dropped this session).
2. **Pick one** routable idea and move it *one step* down the lifecycle:
   - **Execute it now** if it is small, safe, reversible, and in an already-decided lane
     (this is real work, not scope creep — `docs/collaboration-model.md` act-vs-ask).
   - **Structure it into a plan** for the next agent (`docs/planning/…`) + place it on
     `docs/roadmap.md` at a horizon, if the direction is clear but the work is bigger.
   - **Open a discussion** (router Q-block) if it is excessive / ambiguous / a product call.
3. **Record** the move: update the idea's state, and note the grooming in the `.sessions/`
   log so the next agent sees the backlog is live.

A **periodic sweep** (the `.session-journal.md` REVIEW cadence) confirms no idea is stuck
at `raw`/`captured` with no destination — that is the no-orphan guarantee, made checkable.

## Routed planning pass — 2026-06-08

The current cross-source lifecycle outcomes are recorded in
[`../planning/idea-roadmap-inventory-2026-06-08.md`](../planning/idea-roadmap-inventory-2026-06-08.md).
That ledger groups ideas by canonical subsystem/platform seam and links the resulting roadmap drafts; it does not approve implementation or replace the preserved capture docs above.

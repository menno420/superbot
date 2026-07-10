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

**Optional `Subsystem:` tag (authoritative idea↔command link).** An idea may declare which bot
subsystem(s) it touches with a front-matter header line — `> **Subsystem:** economy, mining` (or
`> **Area:** …`) — using **subsystem-registry keys**. The bot-site command browser
(`scripts/export_dashboard_data.py` → `_subsystem_open_work`) **prefers this explicit tag** over its
filename-slug heuristic, which fixes generic-word cross-matches (e.g. an agent-workflow
"executor-chain" idea slug matching the Word-Chain game's `chain` subsystem). Use the sentinel
`> **Subsystem:** none` for agent-workflow / meta ideas that touch **no** bot subsystem (links to
nothing). The tag is **optional** — un-tagged ideas keep the safe (title+status-only) heuristic — and
only the header block is read, so a `**Subsystem:**` *example* in an idea's body is ignored. See
[`idea-subsystem-tag-on-ideas-2026-06-19.md`](./idea-subsystem-tag-on-ideas-2026-06-19.md).

Current broad captures:

- [`purpose-specific-test-bot-fleet-2026-07-10.md`](./purpose-specific-test-bot-fleet-2026-07-10.md) —
  **owner-raised (2026-07-10, round-3 dispatch):** later, purpose-specific test bot identities (a
  games-testing bot etc.) instead of the one shared test bot; deferred by the owner, capture only.
  Subsystem: none.

- [`project-capability-self-awareness-2026-07-10.md`](./project-capability-self-awareness-2026-07-10.md) —
  **owner-raised (2026-07-10, dispatch part-4c):** "ask a project what its abilities are and it
  answers honestly" — platform half routed to the EAP email (§(d) item 2); buildable half = a kit
  `capabilities --probe` battery that regenerates `docs/CAPABILITIES.md` from live probe results.
  Subsystem: agent-ecosystem / substrate-kit.

- [`seat-boot-verification-harness-2026-07-10.md`](./seat-boot-verification-harness-2026-07-10.md) —
  **session ender (2026-07-10, round-3 dispatch part 4):** script the dispatch copilot's
  four-times-repeated per-seat boot verification (trigger-registry match + raw heartbeat/inbox/outbox
  checks) into `scripts/check_seat.py`, emitting a ready-to-paste runbook §5 row with the verified
  facts filled and only the verdict left to judgment — the 3 games-seat boots are imminent consumers.
  Subsystem: agent-ecosystem / dispatch.

- [`kit-seed-command-fleet-repo-bootstrap-2026-07-10.md`](./kit-seed-command-fleet-repo-bootstrap-2026-07-10.md) —
  **session ender (2026-07-10, round-3 dispatch part 3):** a kit `bootstrap.py seed --profile <shape>`
  collapsing the now-twice-proven ~10-step fleet-repo birth (adopt → slot answers → render → gate →
  lane layer → card/heartbeat → check → push) into one command; sim-lab + 3 games repos are imminent
  consumers, and it's the natural home for the #1890 render/engage-stranding fix. Subsystem:
  agent-ecosystem / substrate-kit.

- [`trigger-registry-liveness-sweep-2026-07-10.md`](./trigger-registry-liveness-sweep-2026-07-10.md) —
  **session ender (2026-07-10, round-3 dispatch session):** make `list_triggers` a standing manager
  wake-step diffing the account trigger registry against the manifest — missing / orphaned /
  session-bound routine detection (all three classes found by hand today; launch-readiness DECISION
  F-1 hit the same gap). Subsystem: none.

- [`telemetry-model-name-vocabulary-2026-07-10.md`](./telemetry-model-name-vocabulary-2026-07-10.md) —
  **session ender (2026-07-10, 41st Q-0107 reconciliation pass, band-#1920):** pin the
  `telemetry/model-usage.jsonl` `model` field to a canonical short-name enum + validator (reusing the
  #1894 gate) so the Q-0248 allocation feed doesn't fragment one model across `opus-4.8`/`opus 4.8`/
  `claude-opus-4-8` spellings — and resolve the undercover-ID-vs-telemetry tension explicitly (record
  the *family* name, never the exact `claude-*[1m]` ID). Hit live this pass. Subsystem: none.
- [`shift-plan-premise-verify-lines-2026-07-10.md`](./shift-plan-premise-verify-lines-2026-07-10.md) —
  **session ender (2026-07-10, overnight shift D, PR #1920):** every actionable scout-report /
  shift-plan item carries a one-line `verify:` command proving its *premise* still holds at pick-up
  time (distinct from "Verification:", which proves the fix). Born from a live miss: the shift plan's
  Q2 claimed 6 views lacked baseview justifying comments, but all 6 had them since #1871 — a 5-second
  `grep -L` in the plan would have killed the stale item before any session picked it up.
- [`command-surface-extractor-consolidation-2026-07-10.md`](./command-surface-extractor-consolidation-2026-07-10.md) —
  **session ender (2026-07-10, command-collision-checker session, PR #1918):** three stdlib-AST tools
  (`scan_commands.py`, `check_command_collisions.py`, `check_command_reachability.py`) now each
  re-implement the cog-decorator command-surface parse with different edge coverage (the collision
  checker's hybrid-command blind spot was caught only by a lucky dedup look at its sibling). Factor
  one `scripts/lib/command_surface_ast.py` declaration stream and re-base all three — a concrete
  first slice of `warn-first-checker-authoring-kit-2026-07-06.md`. Subsystem: none (build hygiene).
- [`reconcile-fleet-runtime-digest-2026-07-10.md`](./reconcile-fleet-runtime-digest-2026-07-10.md) —
  **raised by the band-#1950 (42nd) reconciliation pass (2026-07-10):** superbot has been "entirely
  docs-only" for ~10 bands because runtime work migrated to `superbot-next`/games/`substrate-kit` —
  emit a one-line **fleet-runtime digest** in the pass record from the sibling repos the pass already
  reads via `check_manifest_freshness.py` (#1923) so the ledger stops implying the program stalled.
  Distinct from `band-archetype-classifier` (intra-repo queue ratio); gen-3 verify-and-consolidate
  aligned (Q-0259 §2). Subsystem: docs system / engine tooling.
- [`adopt-codetool-lab-tools-2026-07-10.md`](./adopt-codetool-lab-tools-2026-07-10.md) —
  **owner repo-disposition review (2026-07-10):** the three codetool "test" labs each built a
  real CLI (mdverify — released; envdrift; cfgdiff) — adopt them as fleet tools (mdverify
  over docs/ first), then archive sonnet5+fable5 repos after harvest. Subsystem: tooling.
- [`idea-probe-brainstorm-simulator-2026-07-10.md`](./idea-probe-brainstorm-simulator-2026-07-10.md) —
  **owner-raised (2026-07-10, round-3 planning day):** a brainstorming simulator — probe any
  idea with a structured question battery (+ panel-simulation mode) to get the filled-in
  picture and the way forward; Q-0254 understand-and-reflect turned from habit into tool,
  and the natural core method of the new Idea Engine (round-3 pack §5). One engine, two
  skins with the suggestion copilot below. Subsystem: Idea Engine / agent workflow.
- [`website-suggestion-copilot-2026-07-10.md`](./website-suggestion-copilot-2026-07-10.md) —
  **owner-raised (2026-07-10, round-3 planning day):** an AI helper on the websites that
  turns vague suggestions/bug reports (from the owner or visitors) into structured,
  routable intake via a short clarifying interview — the public skin of the idea-probe
  battery; lands on the `/submit` path. Needs a capped server-side API key (owner-gated).
  Subsystem: websites / intake pipeline.
- [`cross-agent-trust-ledger-2026-07-10.md`](./cross-agent-trust-ledger-2026-07-10.md) —
  **session ender (2026-07-10, GPT-5.6 Sol eval session):** generalize the Sol Codex
  eval suite (`docs/owner/gpt-5-6-sol-codex-eval-2026-07-10.md`) into a standing
  per-model trust ledger — capability/trust scores + allowed lanes per external model,
  re-run on every model release — so cross-agent routing (Q-0120) is data-driven
  instead of tribal knowledge.
- [`fleet-manifest-freshness-checker-2026-07-10.md`](./fleet-manifest-freshness-checker-2026-07-10.md) —
  **gen-2 night-prep seed (2026-07-10, PR #1915) · `historical` — implemented PR #1923:** a checker
  comparing each fleet-manifest row's last-seen against the lane repo's `control/status.md` header —
  the manifest cells went stale within hours all through gen-1 (grand review §5); "enforce, don't
  exhort" applied to the fleet dashboard. Shipped as `scripts/check_manifest_freshness.py` (git
  transport, advisory, fail-open).
- [`coordinator-self-review-against-1901-2026-07-10.md`](./coordinator-self-review-against-1901-2026-07-10.md) —
  **gen-2 night-prep seed (2026-07-10, PR #1915) · `historical` — implemented PR #1924:** the
  coordinator lane is the only gen-1 lane that never answered the #1901 retro question set it
  planted — assemble its self-review from the existing corpus so the gen-2 blueprint's input
  covers all ten lanes. Shipped as `docs/retro/self-review-2026-07-09.md` (protocol-canonical
  path), indexed from `docs/eap/README.md`.
- [`cross-repo-eap-verification-orientation-pointer-2026-07-09.md`](./cross-repo-eap-verification-orientation-pointer-2026-07-09.md) —
  **reconciliation session ender (2026-07-09, 40th Q-0107 pass):** add a short cross-repo verification
  pointer to the orientation route — verify a sibling EAP repo with *its own* CI interpreter
  (`superbot-next` = Py3.11, not superbot's pinned 3.10 — the trap that cost the fleet-review session
  ~75 phantom failures) and name the `add_repo` → GitHub-MCP → clone-and-run first-party flow, so every
  manager-Project run stops re-deriving it.
- [`pinned-feed-contract-for-dashboard-json-2026-07-09.md`](./pinned-feed-contract-for-dashboard-json-2026-07-09.md) —
  **session ender (2026-07-09, PR #1884); first slice SHIPPED (PR #1920)** — extend the
  pinned-feed-contract pattern (the console.json shape contract) to `dashboard.json` — the websites
  repo's dashboard renders ~12 pages off that feed with no contract at all. #1920 shipped
  `dashboard/data/dashboard_data_contract.json` (slice semantics; `meta` + `bugs`) + producer parity +
  fail-closed checker; remaining families (catalogue / cogs / settings / env_usage / ideas / updates /
  synonyms / access) land family-by-family with version bumps.
- [`live-tree-test-culprit-attribution-2026-07-08.md`](./live-tree-test-culprit-attribution-2026-07-08.md) —
  **grooming capture (2026-07-08, PR #1846 follow-on pass):** live-tree ground-truth tests
  (plan homing etc.) fail on innocent fresh branches whenever an earlier merge shipped tree
  drift — observed three times, hand-bisected each time (#1843 being the latest: a docs-only
  PR skipped pytest entirely, then reddened every full-CI branch). Proposes a named CI step
  ("tree drift, probably not your diff"), a `push:main` leg that opens a culprit issue (a
  push-main failure names its own culprit — no bisect), and running the stdlib live-tree docs
  guards on the docs-only fast path to close the introduction vector.
- [`reconcile-cross-lane-stale-runtime-pr-escalation-2026-07-08.md`](./reconcile-cross-lane-stale-runtime-pr-escalation-2026-07-08.md) —
  **reconcile-pass idea (2026-07-08, Q-0089, thirty-ninth Q-0107 pass, band-#1860):** the 6 dependabot
  dep-bumps #1761–#1766 have been "left in flight — not my lane" by **four consecutive** reconciliation
  passes; correct each time, but the aggregate is a cross-lane orphan (docs lane can't merge, execution
  lane hasn't). Adds a cross-pass memory step that escalates a runtime PR deferred ≥3 passes into a loud
  one-line owner/dispatch hand-off, so "not my lane" stops becoming "no lane forever."
- [`claim-remote-visibility-scan-2026-07-08.md`](./claim-remote-visibility-scan-2026-07-08.md) —
  **session idea (2026-07-08, Q-0089, grooming wave-1 lane C, #1845) — ✅ SHIPPED (PR #1919):** claims only become visible
  to siblings via the open PR — `check_lane_overlap.py` reads the *local* claims dir, so a claim on
  an un-merged sibling branch (and any lane in the pre-first-push window of a simultaneous-start
  wave) is invisible to the tool. Add a `--remote` mode that scans recent `origin/claude/*` refs for
  claim files not on main, plus a "re-scan once right after your own claim push" protocol line — the
  parallel-wave race window closed at the claim's native (git-ref) layer.
- [`forward-only-project-quality-experiment-2026-07-08.md`](./forward-only-project-quality-experiment-2026-07-08.md) —
  **owner-raised (2026-07-08, EAP-email thread):** configure a Project's instructions so agents
  never *attempt* destructive git (forward-only by design), run real work through it, and measure
  the actual quality cost — the empirical version of "the permission wall is friction, not a
  work-stopper," and strong evidence for the Anthropic feedback. Pairs with the per-repo settings
  ledger plan (`docs/planning/per-repo-settings-state-ledger-2026-07-08.md`).
- [`agent-readable-external-reviewer-entrypoint-2026-07-08.md`](./agent-readable-external-reviewer-entrypoint-2026-07-08.md) —
  **session idea (2026-07-08, Q-0089, EAP email two-reviewer session):** add a stable top-level
  `EXTERNAL-REVIEWER-START-HERE.md` (or `docs/eap/README.md`) written for an external agent reviewer
  arriving cold with no injected `CLAUDE.md` — states what the repo is, links the evidence, lists
  concrete verification tasks. The external mirror of `AGENT_ORIENTATION.md`; makes the email's "put a
  Claude session on it" ask easy to act on.
- [`session-start-capability-self-probe-2026-07-08.md`](./session-start-capability-self-probe-2026-07-08.md) —
  **session idea (2026-07-08, Q-0089, EAP-email-refresh session):** a cheap read-only session-start
  self-probe that records which tools a session actually has (shell, git write, self-wake timer,
  spawn types) — turns late/expensive "this session has no Bash tool" discoveries (the standing-grant
  `NOT ATTEMPTED` row; the phantom `send_later`) into free up-front ones. The self-serve version of
  the email's spawn-time-capability-introspection ask.
- [`session-start-staleness-banner-2026-07-07.md`](./session-start-staleness-banner-2026-07-07.md) —
  **session idea (2026-07-07, Q-0089, Projects-EAP eval-journal session):** the coordinator's
  container clone was 7 merged PRs behind origin at first turn and nothing warned it — add a
  cheap staleness check at session start (`git fetch` + `HEAD..origin/main` count → loud banner)
  so a stale clone announces itself instead of silently answering from an old world. The checker
  script is free to ship; the hook wiring is owner-gated (Q-0106).
- [`cold-start-ab-vague-idea-task-2026-07-07.md`](./cold-start-ab-vague-idea-task-2026-07-07.md) —
  **session idea (2026-07-07, Q-0089, kit-doctrine port session, Q-0254):** the understand-and-
  reflect + guiding-questions doctrine just shipped into the kit's templates has no enforcement
  (by design — not mechanically checkable). Add a **T6 vague-idea task** to the kit-lab's B1
  cold-start A/B corpus (alongside T5's break-a-rule task) so a future kit edit or model drift
  that silently stops following the written rule gets caught, instead of the doctrine quietly
  rotting unnoticed.
- [`adopt-kit-stance-classifier-2026-07-07.md`](./adopt-kit-stance-classifier-2026-07-07.md) —
  **session idea (2026-07-07, Q-0089, understand-and-reflect rule session, Q-0254):** the
  substrate-kit ships a genuine 5-stance task classifier (question/analysis/debug/review/plan —
  reading-route + tool-scope + output contract per stance) but it's dormant — nothing in this
  repo's live workflow tells a session to classify an incoming message first. Wiring it in is
  real scope (touches `.claude/settings.json`, changes every session's opening move) and
  measurable (the kit-lab program's B1 A/B harness can test whether it helps) — routed there
  rather than decided unmeasured in a quick chat session.
- [`automod-spam-detection-gaps-2026-07-07.md`](./automod-spam-detection-gaps-2026-07-07.md) —
  **session idea (2026-07-07, owner-raised, code-verified):** confirmed the owner's suspicion —
  automod's spam rule (`SpamTracker`) is pure rate-counting with zero content comparison, so it
  can't distinguish a burst of different messages from the same message repeated. Found a more
  severe related gap while verifying: the tracker is keyed per-channel, so a burst spread across
  multiple channels never trips the rule at all regardless of content — the only rate limit
  automod has is fully bypassable today. Tracked on the automod completion certificate's
  punch-list (items #5/#6).
- [`channel-role-scoped-authority-gap-2026-07-07.md`](./channel-role-scoped-authority-gap-2026-07-07.md) —
  **⚠ time-sensitive (2026-07-07, owner-raised):** neither the live governance stack nor the frozen
  K6 authority design (`Lane{CAPABILITY,TIER}` + `ChannelAccessDecision`) can express "only role X in
  channel Y" — confirmed at both layers. K6 hasn't been built yet and sits on the strand-1 chain
  (S8/K7 consumes it), so this is worth deciding before the next K6-touching session, not filed for
  later like most of this backlog.
- [`moderation-feature-gaps-2026-07-07.md`](./moderation-feature-gaps-2026-07-07.md) —
  **session idea (2026-07-07, owner-raised):** researched the live moderation/security stack against
  competitor-bot feature sets — most suspected gaps turned out already shipped; three genuine misses
  found: a join-time verification/CAPTCHA gate, a dedicated ban-appeal/modmail flow distinct from the
  general ticket system, and custom trigger→response commands. Feature-level, not architectural.
- [`guild-config-backup-and-data-export-gap-2026-07-07.md`](./guild-config-backup-and-data-export-gap-2026-07-07.md) —
  **session idea (2026-07-07, foundational-capability sweep):** two adjacent misses found while
  checking the rebuild's K0-K10 taxonomy for completeness — self-service per-guild settings
  backup/restore (distinct from whole-DB disaster recovery), and the "export" half of GDPR-style user
  data requests (erasure is thoroughly mechanized; export never reappeared after the original idea).
- [`user-self-service-automation-scheduler-2026-07-07.md`](./user-self-service-automation-scheduler-2026-07-07.md) —
  **session idea (2026-07-07, Q-0089, rebuild-plan-review session):** owner-proposed guardrailed,
  unlockable, user-facing recurring scheduler ("cron jobs for themselves" — a daily rank ping, a
  periodic game-state check), explicitly asked for as a **foundational, cross-subsystem** primitive
  rather than a one-off command. Splits the ask into a low-risk notify-only tier and a higher-risk
  auto-acting tier (names the concrete fairness failure: automating an action a forgetful human would
  otherwise miss is a balance break, not a QoL win) and ties the design to the not-yet-built K9
  durability band so it lands as a kernel extension instead of a later per-feature bolt-on.
- [`usage-limit-aware-routines-2026-07-07.md`](./usage-limit-aware-routines-2026-07-07.md) —
  **session idea (2026-07-07, Q-0089, kit-lab founding-plan session PR #1804):** routines and
  multi-agent orchestrations should treat the account usage-limit error as a distinct failure
  class — self-reschedule at the stated reset time (`limit-deferred` on the run report) instead
  of dying silently; limit-killed lanes never count as evidence. Observed live: a 4-lane review
  fleet returned an empty "success" when the 5-hour limit hit mid-flight. One prompt clause +
  one orchestration rule converts silent lost firings into scheduled retries; the counter feeds
  the Q-0248/Q-0249 spend dataset. **→ PROMOTED to a plan (2026-07-08, grooming lane C, #1845):**
  [`usage-limit-aware-routines-plan`](../planning/usage-limit-aware-routines-plan-2026-07-08.md).
- [`substrate-kit-auto-drafted-handoff-2026-07-07.md`](./substrate-kit-auto-drafted-handoff-2026-07-07.md) —
  **session idea (2026-07-07, Q-0089, final-review session #1778):** the Phase-2.5 A/B measured the
  same failure twice — sessions with a rendered ledger/session-log scaffolding in-repo still write
  back nothing (recall isn't the bottleneck; discipline-dependent write-back doesn't happen). Make
  the kit's session-close/Stop-hook **auto-draft** the handoff card from evidence (git diff, test
  state, docs touched) so the agent edits a draft instead of authoring from memory; a follow-up T4
  re-run then measures whether continuity finally moves. **→ SCHEDULED into the
  [kit-lab founding plan](../planning/kit-lab-founding-plan-2026-07-07.md) band KL-5 (2026-07-07,
  PR #1804)** — it is the ruled prerequisite for the standing cold-start A/B routine's first firing.
- [`claude-code-projects-for-the-rebuild-2026-07-07.md`](./claude-code-projects-for-the-rebuild-2026-07-07.md) —
  **session idea (2026-07-07, Q-0089, Projects-EAP + Q-0241 PR #1776):** use the Claude Code Projects
  early-access program (coordinator + shared memory + routines + session sidebar; the *Claude Code*
  environment, **not** claude.ai Chat/Cowork) as the rebuild's orchestration layer — prove it on
  reversible canonical-plan §5 steps 1–4 in this repo, then let it coordinate the `superbot-next` build.
  Composes with **Q-0241** (never-wait autonomy + live-test-in-server + silence=consent). Open
  considerations: cloud memory vs. our repo-as-source-of-truth; overlap with our hand-rolled claim/
  babysitting/cron tooling.
- [`supersede-banner-integrity-checker-2026-07-06.md`](./supersede-banner-integrity-checker-2026-07-06.md) —
  ✅ **IMPLEMENTED 2026-07-08 (PR #1846**; was: session idea 2026-07-06, Q-0089, rebuild-consolidation
  PR #1770**):** a warn-first checker for the
  hand-maintained supersede web — every `SUPERSEDED` banner's successor must resolve + link back, and
  a superseded doc may not keep its `plan` badge (the "design-spec header stayed stale 4 days" /
  "phantom handoff §F" drift classes, mechanized). Shipped as `scripts/check_supersede_integrity.py`
  + a `check_docs.py` soft check + unit tests; `--strict` promotion pending (Q-0105 warn-first).
- [`reconcile-band-anchor-guard-2026-07-06.md`](./reconcile-band-anchor-guard-2026-07-06.md) —
  **session idea (2026-07-06, Q-0089, 35th reconciliation pass PR #1742):** a warn-only checker that
  fails when the three/four hand-edited band-number anchors in `current-state.md` (the marker, the S4
  sector row, the "next recon at #N+30" / "cross #N+30" lines) disagree — a detector for the
  restatement-drift class every pass currently guards by hand.
- [`warn-first-checker-authoring-kit-2026-07-06.md`](./warn-first-checker-authoring-kit-2026-07-06.md) —
  **session idea (2026-07-06, Q-0089, CI-arc completion PR #1748):** after building two sibling AST
  guards, factor the copy-pasted AST/reachability primitives (incl. the import-qualified call
  resolution that defeats the `self.X`-vs-`module.X` collision) into `scripts/lib/astguard.py`, and add
  a `scripts/new_checker.py` scaffold that stamps out the checker + allowlist + gate-bites/real-tree-clean
  tests + advisory CI step — turning "write a warn-first checker" from a session-craft into a fill-in.
- [`audit-seam-coverage-checker-2026-07-05.md`](./audit-seam-coverage-checker-2026-07-05.md) — ✅ **BUILT
  advisory #1747 (2026-07-06).**
  **session idea (2026-07-05, Q-0089, "save fixes" PR #1728):** a general (AST + `architecture_rules/`
  allowlist) checker that flags any function performing a state mutation (Discord `edit/delete/…`,
  a DB write outside `utils/db/`, a known mutation-table helper) whose success path never reaches
  `emit_audit_action` — generalizing the narrow `test_no_direct_channel_mutations` invariant. Four
  of this session's eight bug fixes (#3/#5/#6) were exactly this "unaudited mutation" class; it would
  catch them at authoring time instead of at a subsystem walk. Start advisory (Q-0105), graduate on
  proof.
- [`deferred-action-restart-recovery-checker-2026-07-05.md`](./deferred-action-restart-recovery-checker-2026-07-05.md) — ✅ **BUILT advisory #1748 (2026-07-06).**
  **session idea (2026-07-05, Q-0089, rebuild Stage-2 walk PR #1725):** a warn-only checker for
  one-shot deferred actions (`asyncio.sleep`+`tasks.spawn`) with no persisted deadline / boot
  reconcile — the identical restart-recovery gap was found independently in security's
  raid-lockdown timer and proof_channel's prize-unlock timer this session, both confirmed G-9
  `DeferredActionSpec` consumers.
- [`dependabot-automerge-enabler-2026-07-04.md`](./dependabot-automerge-enabler-2026-07-04.md) —
  **session idea (2026-07-04, Q-0089, open-PR sweep PR #1719):** extend the `auto-merge-enabler`
  workflow to `dependabot/**` PRs — CI (full suite on the bumped deps) is the gate and the
  `tool-pins` guard already holds the dangerous requirements-dev drift class red, so green
  dependency PRs stop piling up for days (#1555–#1560 sat 5 days; staleness bred a conflict and
  a closed-and-recreated group PR). Workflow edit ⇒ owner-gated (Q-0194 split).
- [`rebuild-release-testing-loop-2026-07-03.md`](./rebuild-release-testing-loop-2026-07-03.md) —
  **owner idea (2026-07-03):** the in-server **release → test → verify loop** — a boot/release
  announcer of what changed (so members know what to test), per-command "tested-since-its-change"
  coverage from real usage, a dedicated **test/debug mode** (full traces to a channel, actions
  self-explain), and an **explain-then-approve button** that doubles as the `verified_live`
  sign-off. Closes judgment gaps #5/#7/#8 and is the missing *mechanism* for the decided Q-0234
  oracle + Q-0222 CUT-1 live co-test. Routes as new Stage-2 capabilities; A/C could ship in the
  current bot now.
- [`rebuild-websites-cutover-role-2026-07-03.md`](./rebuild-websites-cutover-role-2026-07-03.md) —
  **owner idea (2026-07-03):** give the off-Discord **botsite + dev dashboard** a rebuild
  disposition (they die at cutover today — judgment #4), repoint their producer at the new repo's
  manifest, and use them **during the switch** as the public changelog/cutover-comms surface and a
  **rebuild-progress + verified_live dashboard** (the owner-consumable visual artifact judgment #16
  flagged missing). Pairs with the release-loop idea.
- [`fleet-structured-output-placeholder-guard-2026-07-03.md`](./fleet-structured-output-placeholder-guard-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089, final-judgment PR #1701):** reject placeholder values
  (`test`, `t/e/f`, `TODO`) in required evidence/reasoning fields of fleet structured outputs, with
  one retry — schema validation passed twice on the same day while shipping degenerate content
  (audit A row 221's `"test"` verdict; audit B's three `t/e/f` ledger rows, one HIGH). Few lines at
  one seam; protects the whole Gate-V/audit-fleet trust chain.
- [`ultracode-audit-consolidation-stage-2026-07-03.md`](./ultracode-audit-consolidation-stage-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089, surface+proving audit PR #1691):** add a semantic
  **consolidation/dedup stage** between the completeness loop and synthesis in the reusable
  ultracode-audit pattern — the completeness-critic's missing twin ("what did we say twice?" vs
  "what did we forget?"). This session's completeness loop grew the inventory to 46 mechanics with
  several near-duplicates that only exact-name dedup let through; a semantic-cluster merge makes the
  inventory (and its headline count) honest by construction and lets the loop terminate on
  "nothing *semantically* new."
- [`rebuild-layout-success-simulator-2026-07-03.md`](./rebuild-layout-success-simulator-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089/Q-0235, PR #1687):** one instruction-driven layout-success
  simulator (deterministic + AI user models) that scores any generated hub/menu by task success
  rate ("create roles" → does the user reach the node?), unifying the 5 bespoke UX-layout sims.
  Quantifies the "self-explanatory" half of the Q-0234 oracle; sim defines settings, live co-test
  is the final review.
- [`rebuild-critical-review-checkers-2026-07-03.md`](./rebuild-critical-review-checkers-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089, critical-review-rubric PR #1685):** mechanize the rubric's
  finding-classes into checkers — extend `check_plan_staleness.py` for un-anchored `NN%` claims now
  (the class that misled twice on the substrate kit), and build dep-order / thin-step /
  fragmentation / verification-hole / nav-contract checkers against the rebuild's declared
  manifests. The enforce-don't-exhort arm of Q-0233.
- [`owner-decision-packet-renderer-2026-07-04.md`](./owner-decision-packet-renderer-2026-07-04.md) —
  **session idea (2026-07-04, Q-0089, Gate-0 brief-prep PR #1713):** a reusable renderer/skill
  (`/decision-packet`) that turns a question-register (options+recommendation rows) into an
  owner-consumable **visual decision packet** — markdown v1 now, an Artifact-HTML v2 later. Closes FJ
  gap #13 ("nothing renders decisions visually for a non-coding owner"); first consumer is the Gate-0
  session's 12 owner-only rows.
- [`rebuild-design-cite-checker-2026-07-04.md`](./rebuild-design-cite-checker-2026-07-04.md) —
  **session idea (2026-07-04, Q-0089, foundational-design PR #1708):** a `check_doc_cites.py` that
  validates every `path.py:NNN` source citation in an analysis/design doc resolves to a real file
  (+ line-in-bounds). Kills the fabricated-cite class at authoring time — the exact
  `core/contracts.py:48-52` bug (FJ L-25) that threaded a correction through ~11 design specs this
  session. Stdlib, disposable (Q-0105), sibling of `check_docs`; missing-file → strict, line-bounds →
  advisory.
- [`rebuild-navigation-completeness-check-2026-07-03.md`](./rebuild-navigation-completeness-check-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089, hub/navigation PR #1684):** a CI golden that walks every
  generated panel state and asserts Back+Home are present/working (the enforcement arm of the
  Q-0231 navigation contract) + a preset-coverage assertion (every feature in ≥1 preset). Enforce,
  don't exhort; routed to Gate-0 NavigationSpec.
- [`rebuild-invocation-ladder-centralization-2026-07-03.md`](./rebuild-invocation-ladder-centralization-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089, conventions-freeze PR #1680):** the invocation-stack
  centralization set C-1…C-7 (one command resolver, one draft pipeline with two producers, a
  template primitive, one response grammar, one fuzzy engine, one cooldown engine, one description
  surface) — the second-consumer rule applied where it has the most consumers. Proposed (Q-0228),
  pending owner reaction; routed to Gate-0 K8.
- [`rebuild-schema-growth-ledger-2026-07-03.md`](./rebuild-schema-growth-ledger-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089, Stage-1 global review PR #1679):** enforce the Q-0219
  schema-growth guardrail mechanically in the new repo — every grammar field addition mints a
  same-PR ledger entry naming the ≥2 consumers that justified it (else: handler), with a CI diff
  check; kills the inner-platform creep one-field-at-a-time failure mode. Routed to the Gate-0/K2
  grammar plan.
- [`golden-recapture-on-bugfix-2026-07-03.md`](./golden-recapture-on-bugfix-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089, rebuild-planning-phase session):** a one-line protocol —
  every current-bot behavior fix must **re-capture its `parity/` golden** (or record "pre-capture,
  no golden yet") — so the rebuild's parity oracle never green-lights a *fixed* bug's old buggy
  behavior. The six audit-routed bugs are the first candidates; applies through cutover.
- [`rebuild-amendment-registry-2026-07-03.md`](./rebuild-amendment-registry-2026-07-03.md) —
  **session idea (2026-07-03, Q-0089, capability-audit capstone #1674):** one committed registry
  file as the **sole minting authority** for rebuild grammar-amendment IDs (G-n families, R-n
  riders, P-n provisional, the refuted set) — Lanes B/C/D independently minted colliding G-7…G-9
  and the capstone reconciled the numbering by hand; the rebuild's namespace discipline applied
  to its own meta-artifacts. The Gate-0 spec pass consumes it and stamps `in-spec`.
- [`convergent-amendment-discovery-signal-2026-07-02.md`](./convergent-amendment-discovery-signal-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, Lane A capability-audit session):** when a multi-agent audit
  fans out N independent workers over disjoint scope, count and surface **independent
  rediscoveries** of the same proposed fix/amendment as a confidence-ranking signal during
  synthesis — the Lane A audit found 2 grammar amendments each rediscovered 3-4× by unrelated
  subsystem workers with no cross-talk, which is stronger evidence than any single agent's
  argument. Cheap, tooling-free synthesis-step convention for the next multi-lane reconciliation.
- [`central-admin-and-logging-guilds-2026-07-02.md`](./central-admin-and-logging-guilds-2026-07-02.md) —
  **owner idea (2026-07-02, in-chat):** a dedicated **admin guild** (manage any server's bot config
  via a cross-guild selector — Q-0212's authority without the "must be in the guild" clause) + a
  **central logging guild** (all-server logging + platform feeds). Ops lane buildable; the
  member-content mirror is owner-gated on a privacy policy; **the Railway-alerts feed was restored
  live same-session** (`#railway-alerts` in the test guild; rule updated in place).
- [`substrate-kit-review-followups-2026-07-02.md`](./substrate-kit-review-followups-2026-07-02.md) —
  **review capture (2026-07-02):** the two deferred findings from the independent review of #1649
  (10 of 12 confirmed defects were fixed at root that session) — make `JsonStateBackend.transaction`
  re-entrant so `apply_review_verdict` is atomic (its own PR, changes core semantics), and a
  verified-low-risk `confirm_slot` floor note. Buildable follow-up.
- [`tried-before-ledger-2026-07-02.md`](./tried-before-ledger-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, owner-requested harvest):** a greppable negative-results
  ledger (`docs/operations/tried-before.md`) for abandoned operational experiments — born from the
  wait-for-CI near-miss, where one line of owner history ("kept failing") beat a correct-looking
  fresh analysis and existed nowhere in the repo. Candidate substrate-kit template.
- [`wire-level-live-bot-loop-2026-07-02.md`](./wire-level-live-bot-loop-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, harvest):** boot the bot under the verified Galaxy-Bot test
  token and drive it over the real Discord gateway in a test guild — dissolves the
  `[needs-live-bot]` startability gate and *is* the Phase-0.5 golden-harness Discord driver;
  complements (not duplicates) the in-process `bot-self-test-walker`.
- [`context-cost-telemetry-2026-07-02.md`](./context-cost-telemetry-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, retention-policy design session):** parse session transcripts
  to measure *real* per-session docs-words-read (boot tax, grep-hit class split) — recalibrates the
  retention simulator's assumption-grade constants and supplies the rebuild's §5.2 footprint KPI;
  enforce-with-measurements applied to the memory system's own biggest claim.
- [`continuously-verified-backups-2026-07-02.md`](./continuously-verified-backups-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, harvest):** the restore drill as a *scheduled* workflow
  (service-container Postgres + restore newest artifact + substance asserts) — pg_dump is now the
  only backup layer (Railway backups plan-gated), and a backup that never restores is a hope.
- [`shadow-clone-rehearsal-2026-07-02.md`](./shadow-clone-rehearsal-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, harvest):** agent-operated Railway shadow of the current bot
  (Galaxy Bot + snapshot-restored Postgres) — rehearses the Phase-5 cutover choreography, proves
  restore end-to-end, and gives the golden harness a consequence-free capture target. Real spend →
  flag before running.
- [`no-transcript-secret-plumbing-2026-07-02.md`](./no-transcript-secret-plumbing-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, harvest):** `scripts/secret_plumb.py` — secrets move
  store-to-store (Railway ↔ GitHub secrets) process-to-process with hash-receipt output, never
  through transcripts — the missing safety half of the Q-0213 full-automation grant.
- [`railway-deploy-alerts-discord-webhook-2026-07-02.md`](./railway-deploy-alerts-discord-webhook-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, from the Railway automation-grant session):** point a Railway
  project webhook at Discord so failed `worker` deploys push-alert the owner — today a broken
  deploy is only discovered by looking; platform-side, no bot code, works even when the bot itself
  failed to boot. Agent-executable under Q-0213 (confirm the destination channel first).
- [`railway-config-drift-checker-2026-07-02.md`](./railway-config-drift-checker-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, from the Railway audit):** a read-only checker + weekly
  routine diffing live Railway deploy config (wait-for-CI flags, healthchecks, backup schedules,
  watch paths, variable *names*) against a committed expected-state file — the audit found
  deploys-don't-wait-for-CI and zero DB backup schedules precisely because nothing watches the
  dashboard; a checker makes the fixes regression-proof.
- [`owner-gate-docs-plain-language-rule-2026-07-02.md`](./owner-gate-docs-plain-language-rule-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, from the design-spec revision):** every owner-gate deliverable
  must open with a `## Plain-language summary` (the approving reader is the non-coder owner), backed
  by a ~10-line `check_docs` rule keyed on an `owner-gate` status token — the design spec needed a
  full revision PR to retrofit exactly this, and the miss was structurally predictable.
- [`judge-panel-as-saved-workflow-2026-07-02.md`](./judge-panel-as-saved-workflow-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, from the rebuild-design-spec session):** encode the proven
  judge-panel method (N forced-diverse designs + cross-model design → lens-diverse judges → best-of
  synthesis → multi-lens adversarial review incl. a live non-Claude GPT reviewer → source-verifying
  reviser) as one **saved, parameterized workflow** so every future owner-gate-grade deliverable
  (Phase-3 spine designs, harness architecture) reuses it instead of re-authoring the orchestration.
- [`rebuild-doc-set-start-here-index-2026-07-02.md`](./rebuild-doc-set-start-here-index-2026-07-02.md) —
  **session idea (2026-07-02, Q-0089, from the thirty-second reconciliation pass):** the fresh-rebuild
  initiative (top-focus S3 lane) has accreted **nine** `docs/planning/rebuild-*`/`*-substrate-*` docs with
  no single ordered entry point; add one "START HERE" index that orders them into a reading path with each
  doc's **role + gate-state** (start-gate §B vs commit-gate §F), so the queued K0 executor starts cold
  without re-deriving the map — paired with plan-homing so a new `rebuild-*` doc must join the index.
- [`audit-log-catchup-on-reconnect-2026-07-01.md`](./audit-log-catchup-on-reconnect-2026-07-01.md) —
  **session idea (2026-07-01, Q-0089, from the server-logging-v2 audit-log pass):** replay missed
  Discord audit-log entries on `on_ready`/`on_resume` so moderation/server logging is **gap-free
  across restarts and deploys** (every merge redeploys `worker`). A per-guild high-water mark (last
  posted entry id) bounds the replay and dedups against live gateway delivery.
- [`leaderboard-row-avatars-2026-07-01.md`](./leaderboard-row-avatars-2026-07-01.md) —
  **session idea (2026-07-01, Q-0089, from the Arcane/MEE6 card-polish pass):** add a per-row avatar
  thumbnail to the `!leaderboard` image (the Arcane-defining visual) — the `avatar_disc` primitive +
  `fetch_avatar_png` seam shipped this session make it pure-additive; needs bounded concurrent avatar
  fetches + a small in-process avatar LRU so re-renders don't re-hit the CDN.
- [`superbot-fresh-rebuild-vision-2026-06-30.md`](./superbot-fresh-rebuild-vision-2026-06-30.md) —
  **maintainer vision (2026-06-30, in-chat, captured verbatim + Claude's verified counter-research):**
  a full rebuild of SuperBot as a fresh repo — keep all working code, port it incrementally against the
  current repo as a frozen reference, separate the bot from the AI-memory project, design the question
  router and architecture once from accumulated knowledge instead of incrementally. **Not approved for
  execution** — explicitly gated on finishing the portable substrate-kit, a large multi-agent
  planning/review pass, the maintainer's own keep/change spec, and (per the maintainer) Fable 5
  availability — **research finding: Fable 5 has been generally available via the API since
  2026-06-09**, so that gate may already be clear. Carries Claude's full verification trail (router
  archive status, the historical-docs-value audit, the portable-kit's real ~60%-built state, zero
  code-coupling between `substrate-kit/` and `disbot/`, concrete evidence for code-level debt) — read
  the doc for the reconciled position, not just the proposal.
- [`orientation-doc-linecap-guard-2026-06-30.md`](./orientation-doc-linecap-guard-2026-06-30.md) —
  **reconciliation idea (2026-06-30, Q-0089, band-#1590 pass, from the fresh-rebuild-vision audit):**
  enforce each read-path doc's **own stated line/char budget** (`AGENT_ORIENTATION.md` is 2× its declared
  ~250-line cap, unenforced) with a warn-first `check_docs` extension that reads the cap from the doc
  itself — makes the #1586 orientation-cost cut **durable** instead of a one-time win that silently
  regrows. Friction→guard (Q-0194). Subsystem: docs-system (S3/S4).
- [`compute-dont-refuse-capability-sweep-2026-06-30.md`](./compute-dont-refuse-capability-sweep-2026-06-30.md) —
  **session idea (2026-06-30, Q-0089, from building the BTD6 boss-fight estimator #1574):** mine the
  `ai_review_log` for refusals that are actually **computable** (the bot has the grounded data, it just
  refused or confabulated — boss fights, economy projections, XP-to-level, …) and build a deterministic
  compute tool per recurring class. Generalizes `deterministic_btd6_list_reply` / the round-cash workflow /
  the new estimator. Adds a `computable` triage disposition. Subsystem: ai, btd6.
- [`review-log-frequency-preset-suggestions-2026-06-30.md`](./review-log-frequency-preset-suggestions-2026-06-30.md) —
  **session idea (2026-06-30, Q-0089, from building the AI review-log answer loop #1569):** when the *same
  normalized question* recurs as an `unknown` N times in a window, push a one-line "author a preset?" nudge
  to the review channel — turning the review log into a **demand-ranked** worklist (vs. the chronological
  `!aireview list`). Reads existing redacted rows + the shared `normalize_question` key; no new table; pairs
  with a preset hit-counter. Completes the operator-pull loop with a bot-push direction. Subsystem: ai.
- [`command-collision-checker-2026-06-29.md`](./command-collision-checker-2026-06-29.md) —
  **implemented (PR #1918, 2026-07-10 — script + tests shipped; the `code-quality.yml` step wiring is
  the noted follow-up in the idea file); captured 2026-06-29 (band-#1560 reconciliation pass, Q-0089):** a `check_command_collisions.py` (offline,
  stdlib AST, CI-wired) that fails when two cogs register the same top-level command name/alias — turning the
  band's `give`-collision **prod boot-crash** (#1541/#1544, statically detectable yet it reached production)
  into a red PR. The cheapest-tier (CI) half of the Q-0194 friction→guard escalation; pairs with #1544's
  runtime boot guard. Subsystem: none (agent-workflow / build hygiene).
- [`knowledge-domain-conversation-carryover-2026-06-29.md`](./knowledge-domain-conversation-carryover-2026-06-29.md) —
  **session idea (2026-06-29, Q-0089, from building the Project Moon combat-mechanics layer #1549):** a
  short-lived per-(channel, author) domain-context memory so a bare follow-up ("how does clashing work?")
  inherits the last-routed knowledge domain (BTD6 / Limbus) and grounds — entity-resolution-gated +
  fast-decaying so it never re-introduces over-routing. Promotes the BTD6 single-turn carryover (#668)
  into a domain-agnostic router capability; folds into the Slice B `KnowledgeDomain` seam. Subsystem: ai.
- [`no-dead-end-terminal-view-guard-2026-06-28.md`](./no-dead-end-terminal-view-guard-2026-06-28.md) —
  **session idea (2026-06-28, Q-0089, from fixing the Deathmatch + RPS PvP dead-ends #1527):** an arch
  lint flagging any game terminal view that disables/`stop()`s without swapping to a nav-bearing result
  view (or posts a terminal message with no `view=`). Turns a recurring manual catch (fishing, deathmatch,
  rps, chain/farm) into an enforced guard — the "friction → guard" pattern (Q-0194). Warn-tier first,
  disposable (Q-0105). Subsystem: S1 games / S3 tooling.
- [`router-q-index-generator-2026-06-28.md`](./router-q-index-generator-2026-06-28.md) —
  **session idea (2026-06-28, Q-0089, from documenting the open-question sweep + deciding Q-0210):** a
  stdlib `build_q_index.py` → a one-line-per-Q index (number · title · status · Home · file) over the
  router + its archive, so an agent resolves a `Q-0NNN` reference (~9k repo-wide) by grepping ~215 lines
  instead of loading the 490 KB router. The *findability* half of Q-0210's *size* fix; regenerate in the
  reconciliation pass. Disposable (Q-0105). Subsystem: none (S4/S3 tooling).
- [`completion-ledger-registry-parity-guard-2026-06-27.md`](./completion-ledger-registry-parity-guard-2026-06-27.md) —
  **session idea (2026-06-27, Q-0089, from building the feature-completion framework #1513):** a stdlib
  `check_completion_ledger_parity.py` asserting every user-facing game/server-function registry key has a
  row in the [completion ledger](../planning/feature-completion/README.md) (and vice-versa), so a newly
  added game can't silently miss a completion certificate. The completeness-axis sibling of the
  `subsystem-inventory-homed-guard`; reuses the `completion_scoreboard.py` table reader. Disposable
  (Q-0105). Subsystem: none (S4/S3 tooling).
- [`queue-slice-staleness-age-2026-06-28.md`](./queue-slice-staleness-age-2026-06-28.md) —
  **captured 2026-06-28 (band-#1530 reconciliation pass, Q-0089):** tag each §4 forward-queue slice with a
  one-token `carried since band-#N` age, so a slice carried un-executed across many bands becomes a legible
  signal (move to gated, or owner re-prioritise) instead of an identical-looking row. Converts the
  execution-rate *count* into a per-slice *history*; the manual precursor to E3. Subsystem: S4 docs-system.
- [`band-queue-execution-rate-2026-06-27.md`](./band-queue-execution-rate-2026-06-27.md) —
  **captured 2026-06-27 (band-#1500 reconciliation pass, Q-0089):** three of the last four bands executed
  **zero** named §4 forward-queue slices (the work was owner-directed BTD6 accuracy + autonomous
  hardening instead). Add one computed line per pass record — "queue slices executed this band: X of N
  named" — making the planning-vs-reality gap legible across bands. The manual precursor to E3 (the
  planned-slice hit-rate tracker). Subsystem: S4 docs-system.
- [`fishing-gear-stats-2026-06-27.md`](./fishing-gear-stats-2026-06-27.md) —
  **✅ BUILT 2026-06-27 (#1504, dispatch run):** the Q-0175 "matching gear → better fishing" half.
  `EffectiveStats` gained `fishing_power`/`bite_luck`, a CHARM-slot fishing-charm ladder + gear-shop rows,
  the pure converter `utils/fishing/gear.py`, and `begin_cast` now folds them in as the 4th cast knob
  (rod × bait × weather × gear) — turning the loadout presets (#1499) from convenience into a real
  optimisation, reusing the cross-game `EffectiveStats` seam. Subsystem: games (mining/fishing).
- [`cog-routing-enforcement-gap-2026-06-27.md`](./cog-routing-enforcement-gap-2026-06-27.md) —
  **surfaced 2026-06-27 (PR #1496):** the per-feature, per-channel command toggle system (`cog_routing`)
  is configurable but **not wired to runtime enforcement** — `is_cog_enabled` is read only by the
  read-only access-projection + the setup preview, never by either live command gate (the planned
  "central availability resolver" was never built). The literal "allowed commands per channel" the owner
  asked for; the *enforced* coarse half (Command Access) shipped in #1496, this fine-grained half needs a
  cached read model in the command hot-path → its own plan-first PR. Subsystem: none (command gate + setup).
- [`bot-migration-assistant-2026-06-24.md`](./bot-migration-assistant-2026-06-24.md) —
  **owner-directed (2026-06-24, chat):** the bot recognizes the *other* bots in a server, maps what each
  offers, suggests how to **replicate** it with SuperBot's subsystems, then offers to **retire** the
  now-redundant bots once setup is done — the in-product engine for the consolidation wedge. Grounded in
  the real seams (`member.bot` detection · `guild_snapshot` · `subsystem_registry` · setup advisor →
  draft → Final Review · `moderation_service.kick`) **and** the one hard constraint — Discord has **no
  API to introspect another bot's commands**, so discovery rests on a curated app-id-keyed catalog +
  observable signals, never live command reads. The *live-in-server* counterpart to the V-14
  hand-harvest teardown lane. Subsystem: setup.
- [`help-nav-attachment-seam-2026-06-24.md`](./help-nav-attachment-seam-2026-06-24.md) —
  **session-idea (2026-06-24, Q-0089) from the `!xpmenu` H3 slice (#1413):** hub panels show their
  visual image card when opened by their direct command but a plain embed when reached through Help
  (`build_help_menu_view` is embed-only across the codebase). Proposes one help-nav attachment seam so
  the card carries through Help too — closing the inconsistency at the root as the cards go universal.
  Subsystem: none.
- [`askuserquestion-preview-for-design-forks-2026-06-24.md`](./askuserquestion-preview-for-design-forks-2026-06-24.md) —
  **grooming promotion (2026-06-24, from a session log):** use `AskUserQuestion`'s per-option `preview`
  field to render a mockup of each option's resulting UX for **design/UX forks**, so the owner picks the
  option that *looks* best, not the one that *reads* safest. Motivated by the same-day #1429→#1432 setup
  rework (a scope-narrowing answer read as final). Rescued from `.sessions/` so grooming can find it.
  Subsystem: none.
- [`settle-once-architecture-guard-2026-06-24.md`](./settle-once-architecture-guard-2026-06-24.md) —
  **session-idea (2026-06-24, Q-0089) from the settle-once dispatch run (#1444/#1445):** a
  `check_architecture` rule that flags a game view / state object whose settlement path (posts a result
  or calls `settle_pvp`/`refund_pvp`) is reachable from >1 trigger but doesn't adopt `SettleOnceMixin` —
  the CI ratchet form of the by-hand double-settle hunt that run did across four views. Warn-first, after
  the mixin earns more trust. Subsystem: none.
- [`btd6-runtime-mechanics-from-game-2026-06-23.md`](./btd6-runtime-mechanics-from-game-2026-06-23.md) —
  **owner-raised (2026-06-23):** get the BTD6 *runtime/simulation* layer (freeplay health/speed ramp,
  superceramic swap, per-round RBE & cash) **straight from the game** — the dump only exports entity
  *models*, so every "conflicting numbers" dispute (topper64 vs cyberquincy vs us: cash ~300K/350K/400K;
  the wrong r>100 health brackets in #1384) comes from re-deriving runtime mechanics against contradictory
  secondary sources. Proposes a BTD Mod Helper runtime-extraction mod as the game-sourced oracle. Subsystem: btd6.
- [`ultracode-worker-pr-scope-guard-2026-06-23.md`](./ultracode-worker-pr-scope-guard-2026-06-23.md) —
  **session-idea (2026-06-23, Q-0089) from the ultracode consolidation fleet (#1375):** a coordinator-side
  `scripts/check_worker_pr_scope.py` that asserts a worker PR's diff touches *only* its declared ALLOWED
  file globs (and no held-set files) — mechanizing the by-hand Phase-2 scope review that protects the
  file-disjoint guarantee. The post-work half of `check_lane_overlap.py`. Cross-cutting / agent workflow.
- [`session-followups-visual-ai-setup-2026-06-23.md`](./session-followups-visual-ai-setup-2026-06-23.md) —
  **session-idea promotion (2026-06-23, Q-0089):** the three open forward-ideas from the visual-engine /
  AI-setup arc (PRs #1349/#1352/#1355/#1357/#1361), lifted out of their `.sessions/` logs into the
  backlog so grooming finds them — **(1)** golden-image snapshot tests for the card engine (catches
  layout regressions the byte-check misses; load-bearing at engine roadmap H2), **(2)** a user-visible
  *cosmetic-only monetization pledge* surface (the north-star's Pillar 1, user-facing half), **(3)** a
  per-kind breakdown in the #1361 setup create-count guard. Cross-cutting; build-when-convenient.
- [`new-subsystem-followup-tracker-2026-06-23.md`](./new-subsystem-followup-tracker-2026-06-23.md) —
  **reconciliation idea (2026-06-23, band-#1350 Q-0089):** the band stood up **four** new subsystems
  (farm/karma/casino/treasury), each with obvious follow-up depth that lives only in scattered session-card
  prose. Make `new_subsystem.py` write a `## Follow-ups` stub into each subsystem folio + a stdlib checker
  that lists them, so the dispatch/reconciliation routines pull buildable slices from *real shipped depth*
  instead of aspirational runtime initiatives. Complements the band-queue hit-rate metric idea. Subsystem: S4/S3 tooling.
- [`planned-slice-hit-rate-tracker-2026-06-24.md`](./planned-slice-hit-rate-tracker-2026-06-24.md) —
  **reconciliation idea (2026-06-24, band-#1380 Q-0089):** every pass hand-counts "~N/M planned slices
  executed" against the previous §4 queue (1/11 band-#1350, 2/12 band-#1380); the band-#1320 pass proposed
  measuring it but it's still re-derived prose. A stdlib `check_plan_hit_rate.py` that parses a pass
  record's §4 slice→PR-lineage table against the next band's merges, reporting the measured **hit rate**,
  makes the buffer-becomes-band gap trend-able instead of an impression. Pairs with the new-subsystem
  follow-up tracker (one feeds the queue from shipped depth, this measures whether the queue predicts the
  band). Subsystem: S4/S3 tooling.
  *(Groomed 2026-06-23: cross-linked to the inventory-homed guard below — same root cause, plan as one slice.)*
- [`recon-cadence-boundary-jitter-2026-06-24.md`](./recon-cadence-boundary-jitter-2026-06-24.md) —
  **reconciliation idea (2026-06-24, band-#1410 Q-0089):** the band-#1410 pass fired ~50 min after band-#1380
  on a band of just 4 merges (one being the prev pass itself) — because the prev pass reset its marker to
  #1404 while #1405–#1410 were already merged/in-flight, so the next merge crossed #1410 instantly. At burst
  velocity a strict "every 30th PR" can fire a near-empty full-ritual pass right behind a full one. The idea:
  a **jitter guard** in `check_reconciliation_due.py`/the trigger workflow that suppresses a new `reconcile`
  issue when the prev pass is too recent **and** too few product PRs have merged since — folding the tiny
  band into the next real one (recording the skipped boundary, with a hard ceiling). Pairs with the hit-rate
  tracker above (this keeps each measured band big enough for the metric to mean anything). Subsystem: none.
- [`band-archetype-classifier-2026-06-24.md`](./band-archetype-classifier-2026-06-24.md) —
  **reconciliation idea (2026-06-24, band-#1440 Q-0089):** three of the last four passes scored "~0–1/N of
  the forward queue executed; the band was owner-directed off-queue work" (band-#1440 Essential Setup,
  band-#1410 ticket subsystem, band-#1380 fishing/card) — re-derived by hand each pass, never trended. Tag
  each pass record with a one-line **band archetype** (`queue-executing` / `owner-directed` / `mixed` /
  `micro`) computed from named-slice hits vs. owner-directed merges, so a trivial grep yields the owner's
  real signal: *how much of the roadmap the autonomous fleet drives vs. how much he steers live* — the core
  "is the workflow self-driving?" metric. Reuses the planned-slice hit-rate tracker's parse. Subsystem: S4/S3 tooling.
- [`reconcile-trigger-band-consistency-guard-2026-06-26.md`](./reconcile-trigger-band-consistency-guard-2026-06-26.md) —
  **✅ SHIPPED 2026-06-27** (`scripts/check_reconcile_marker.py`, dispatch run): the warn-first guard that
  asserts the `Last reconciliation pass: PR #N` marker is internally consistent (leading `#N` == the stated
  reset target · `band-#M` == `(N // 30) * 30` · the linked pass doc exists). Caught + fixed the live
  band-#1470 drift (marker read `#1472`, the pass's own PR, vs the reset target `#1470`). Subsystem: S4/S3 tooling.
- [`reconcile-marker-generator-2026-06-27.md`](./reconcile-marker-generator-2026-06-27.md) —
  **reconciliation idea (2026-06-27, Q-0089):** the generate-don't-validate complement to the guard above — a
  `scripts/set_reconcile_marker.py` that *emits* the canonical marker line from the latest-merged PR + band
  math (so the agreeing numbers come from one source and can't be mistyped), turning the routine's "reset the
  marker" step into *run this script*. The guard catches the drift; the generator prevents it. Subsystem: S4/S3 tooling.
- [`dispatch-menu-suppress-shipped-lanes-2026-06-26.md`](./dispatch-menu-suppress-shipped-lanes-2026-06-26.md) —
  **dispatch-tooling idea (2026-06-26, groomed from the #1477 left-open note):** `check_sector_next_freshness`
  catches a `▶ Next` linking a shipped (`historical`) plan at *session close*; `dispatch_menu.py` has no such
  guard at the *pick*, so a roadmap `Now`/`Next` whose plan already shipped is still offered. A naive port
  over-suppresses (roadmap bullets link multiple plans, some shipped-as-context), so it needs a `▶ [operative-plan]`
  convention first; then dispatch_menu reads only the operative link's status and suppresses shipped lanes.
  Pick-time + close-time double coverage of the same drift class. Subsystem: S3 dispatch tooling.
- [`subsystem-inventory-homed-guard-2026-06-23.md`](./subsystem-inventory-homed-guard-2026-06-23.md) —
  **workflow idea (2026-06-23, Q-0089, ultracode-map session):** four mapping agents verified the repo's own
  inventory docs lag source — `repo-navigation-map.md`'s cheat-sheet table omits **18 shipped cogs** (54 in
  source) and `ownership.md` lists only `fishing` of the newer subsystems. Propose a warn-first ratchet guard
  (`check_subsystem_inventory_homed.py` + test + exceptions yml, the proven 3-file shape) asserting every
  `*_cog.py` / `SUBSYSTEMS` key is homed in the canonical inventory + ownership tables — closing the drift
  class at the root. Sibling to the follow-up-tracker idea above. Subsystem: none (S4/S3 tooling).
- [`competitive-positioning-north-star-2026-06-23.md`](./competitive-positioning-north-star-2026-06-23.md) —
  **owner-directed (2026-06-23):** follow-up to the Dank Memer visual work — *"what would make people prefer
  ours over any other bot?"* Grounded in a fan-out research pass across 15+ bots (Dank Memer, UnbelievaBoat,
  MEE6, Carl-bot, Dyno, ProBot, Wick, Tatsu, Lurkr, Amari, Pokétwo/PokéMeow, OwO, Mudae, IdleRPG, Sapphire +
  an AI-native/market-gaps synthesis). Finding: **four failure modes recur in nearly every incumbent** —
  utility paywalls (the MEE6 backlash), pay-to-win, setup friction, and jack-of-all-trades mediocrity. Our
  wedge: the **AI-operated, best-in-class-per-feature all-in-one with cosmetic-only monetization by promise**.
  Pillars ranked by defensibility + the honest counter-arguments (the "specialize-as-you-grow" objection; the
  AI-setup lane is now contested; Discord's 2026 gambling headwind). Product-positioning north-star. Subsystem: none.
- [`visual-card-engine-vision-2026-06-23.md`](./visual-card-engine-vision-2026-06-23.md) —
  **owner-directed (2026-06-23):** the maintainer shared a Dank Memer fishing season-card screenshot and
  asked us to enumerate DM's commands/functions, dissect its *visual* approach, and plan how to **beat** it.
  Finding: DM's moat is **server-rendered PNG/GIF cards, not embeds** ("image is the screen, buttons are the
  controls"), each season a re-skin of one templated engine. **Foundation built same session** — the themeable
  card engine (`utils/card_render.py`) + the first feature card (`utils/profile_render.py` → `/myprofile`);
  H2–H5 (migrate existing renderers · skinnable season cards · real art/fonts · animation + per-user themes)
  remain. Presentation-layer product depth. Subsystem: none (cross-cutting render layer).
- [`ai-self-curated-memory-notebook-2026-06-22.md`](./ai-self-curated-memory-notebook-2026-06-22.md) —
  **owner-dropped (2026-06-22), alongside the treasury build:** give the bot's in-product AI a narrow,
  audited write-back seam — a staging table it appends small *non-personal* notes to (user corrections,
  facts worth remembering) via three triggers (AI-judged value · correction · daily cron), reviewed by a
  human before any promotion into the system instruction / a cached layer / a **deterministic answer preset**
  (vetted exact response, preloaded, zero API call). Privacy (no PII, ever) is the gating constraint; phase
  the **preset layer first** (smallest, no privacy surface). The in-product mirror of the agent network's
  two-part curated memory (`collaboration-model.md`). AI lane.
- [`giveaway-competitive-teardown-2026-06-23.md`](./giveaway-competitive-teardown-2026-06-23.md) —
  **owner-directed (2026-06-23):** maintainer shared jagrosh's GiveawayBot and asked what it does, what we
  lack (no giveaway system today), and how to beat it. Teardown + beat-it feature list (entry requirements,
  weighted/bonus entries, auto-paid coin prizes, recurring) → routed to a 2–3-PR
  [plan](../planning/giveaway-system-plan-2026-06-23.md). Community lane.
- [`fishing-bait-crafting-2026-06-22.md`](./fishing-bait-crafting-2026-06-22.md) —
  **captured by the fishing-bait dispatch run (2026-06-22, PR #1329):** close the fishing economy loop by
  letting the cook/campfire loop (#1289) also craft small caught fish into bait, so catch → craft → bait →
  bigger-catch feeds itself instead of bait being a pure coin sink. Reuses the shipped bait seam + the
  inventory grant. Games (fishing) product depth.
- [`sim-assumption-telemetry-loop-2026-06-22.md`](./sim-assumption-telemetry-loop-2026-06-22.md) —
  **captured by the fishing-minigame design session (2026-06-22, PR #1296):** when a feature is designed
  off a Monte-Carlo sim (e.g. `tools/sim/fishing_minigame_sim.py`, whose recommendation rests entirely on
  assumed Discord latency constants), ship a one-line telemetry counter logging the *exact* quantity the
  sim assumed (the bite→click round trip), so a later session can replay live data through the sim and
  validate/correct its load-bearing constants. Makes a design sim **self-verifying** — the ground-truth
  path the Q-0105 "unverified" header asks for. Agent-workflow / meta. Disposable (Q-0105).
- [`karma-reputation-system-2026-06-22.md`](./karma-reputation-system-2026-06-22.md) —
  **owner-dropped "Karma" (2026-06-22), clarified to thanks/upvote reputation:** members grant each other
  peer reputation; per-user totals + a leaderboard, on an audited mutation seam modelled on economy/XP.
  Anti-abuse (no self/bot, per-giver→receiver cooldown, daily cap, positive-only) is the hard part.
  Routed → [`../planning/karma-reputation-plan-2026-06-22.md`](../planning/karma-reputation-plan-2026-06-22.md).
  Community lane.
- [`audited-score-subsystem-scaffold-2026-06-22.md`](./audited-score-subsystem-scaffold-2026-06-22.md) —
  **captured by the Karma planning session (2026-06-22):** economy/xp/karma repeat the identical six-piece
  "audited per-user score" shape by hand. A `new_score_subsystem` scaffold + a leaderboard-parity guard
  (every score table has a `RankProvider` or an explicit exclusion) make the next one fill-in-the-blanks
  and stop the INV-test / leaderboard-provider pieces from being forgotten. Agent-workflow / meta.
  Disposable (Q-0105).
- [`reconcile-open-pr-staleness-classifier-2026-06-22.md`](./reconcile-open-pr-staleness-classifier-2026-06-22.md) —
  **captured by the band-#1290 reconciliation pass (2026-06-22):** the Q-0125 open-PR disposition step is the
  one part of the recon pass with **no tooling assist** (manual `list_pull_requests` + eyeball each PR's
  age/label/CI). A small stdlib classifier would bucket open PRs into *active in-flight* / *parked carve-out* /
  *genuinely stale*, so the reconciler only decides on the stale bucket — the one the routine warns is
  easiest to miss (#766 sat red 21h). Sibling of the band-status classifier (#1181) + trim actuator (#1206).
- [`reconcile-headline-sector-currency-check-2026-07-03.md`](./reconcile-headline-sector-currency-check-2026-07-03.md) —
  **captured by the band-#1680 reconciliation pass (2026-07-03):** the recon routine reliably updates its
  home **S4** docs-sector file but can leave the band's *headline* sector (S1/S2/S3) stale — the file a
  dispatcher actually reads for the hot lane. This pass found `current-state/S3-ai-memory.md` next-action
  lagging the rebuild arc that dominated the band. A tiny advisory checker would infer the band's dominant
  sector and warn if its `current-state/SN-*.md` doesn't mention a headline PR. Sibling of the open-PR
  staleness classifier (same stdlib/advisory/disposable shape).
  Sector S3/S4. Disposable (Q-0105).
- [`ledger-fragmentation-linter-2026-07-04.md`](./ledger-fragmentation-linter-2026-07-04.md) —
  **captured by the band-#1710 reconciliation pass (2026-07-04):** a warn-only linter (in `check_docs`
  or a small disposable) that flags a run of N ≥ 3 consecutive Recently-shipped bullets sharing a
  session-branch/date + theme-prefix/Q-arc signal, so a reconciler consolidates them into one grouped
  entry instead of the fragmentation surviving every pass (this band's #1683–#1688 were six bullets for
  one Phase-A arc). Mechanizes the grouped-entry convention the ledger depends on (Q-0194 friction →
  guard). Sector S4. Disposable (Q-0105).
- [`codex-evidence-pr-disposition-guard-2026-07-06.md`](./codex-evidence-pr-disposition-guard-2026-07-06.md) —
  **captured by the band-#1770 reconciliation pass (2026-07-06):** a warn-only checker that flags an open
  `codex/*`/evidence PR whose added doc has already been consumed into a merged corrections/synthesis doc,
  so the raw Gate-V evidence PRs (this band's #1752–#1755/#1758) get an explicit merge-or-close decision
  instead of accumulating unreviewed across passes. Sibling of the open-PR staleness classifier + the
  reconcile-headline-sector-currency-check. Sector S4. Disposable (Q-0105).
- [`reconcile-open-pr-disposition-actuator-2026-07-07.md`](./reconcile-open-pr-disposition-actuator-2026-07-07.md) —
  **captured by the band-#1800 reconciliation pass (2026-07-07):** promote the passive disposition-*guard*
  above into an active *actuator* — a dry-run helper that emits a ready-to-run disposition line per open PR
  (`close #N — evidence-consumed into <merged doc>` / `leave #N — dependabot`), so a reconciler stops
  re-deriving the same merge-or-close judgment and deferring it (the 5 Codex evidence PRs sat two passes
  before this pass closed them). Advisory/dry-run; the reconciler still decides. Sector S4. Disposable (Q-0105).
- [`band-queue-hit-rate-metric-2026-06-22.md`](./band-queue-hit-rate-metric-2026-06-22.md) —
  **captured by the band-#1320 reconciliation pass (2026-06-22):** every pass plans a ~30-slice next band, and
  almost every subsequent pass records "the buffer became the band" in prose only — no number. Extend
  `band_pr_status.py` with a `--queue-hit-rate` mode (planned slices shipped ÷ planned, + count of unplanned
  PRs) and track that one line per pass, so the owner gets **data-driven evidence** of whether deep
  forward-planning predicts reality or should go lighter/reactive. Sibling of `--themes` (#1271) + the trim
  actuator (#1206). Sector S3/S4. Disposable (Q-0105).
- [`ci-dropped-synchronize-auto-retrigger-2026-06-22.md`](./ci-dropped-synchronize-auto-retrigger-2026-06-22.md) —
  **owner-endorsed (2026-06-22, surfaced diagnosing PR #1283's stuck Code Quality):** GitHub sometimes
  **drops the `pull_request: synchronize` event**, so a PR head gets no `code-quality` run and
  auto-merge stalls silently (no run = no failure webhook). A scheduled watcher re-kicks the check
  (empty commit / re-request) when a `claude/*` head has no run after N min — automating the manual
  empty-commit remedy. The *last* strand of "CI didn't run on my latest commit" (cancellation =
  fixed #1275; dropped delivery = this). Sector S5/S3. → relates `.github/workflows/code-quality.yml` ·
  `scripts/check_loop_health.py` · #1275.
- [`workflow-gh-permission-coverage-checker-2026-07-06.md`](./workflow-gh-permission-coverage-checker-2026-07-06.md) —
  **surfaced building the CodeQL stuck-scan watchdog (2026-07-06):** a warn-first checker that maps the
  `gh` ops a workflow step's script runs (`gh issue create` → `issues: write`, `gh workflow run` →
  `actions: write`, …) against the job's `permissions:` block, so an escalation path can't ship that
  silently no-ops under the `GITHUB_TOKEN` fallback. Would have caught the #1743 `issues: write` gap
  (fixed this session). Distinct from `check_routine_permission_surface` (that guards `.claude/settings.json`,
  a different layer). Sector S5. → relates `scripts/check_ci_coverage.py` · `scripts/check_codeql_coverage.py`.
- [`formatter-tool-set-consistency-checker-2026-07-06.md`](./formatter-tool-set-consistency-checker-2026-07-06.md) —
  **surfaced doing the ruff migration (2026-07-06):** extend `check_tool_pins.py` to assert the formatter
  tool *set* is identical across the three pin surfaces, not just the versions — so a *partial* tool swap
  (the ruff migration touched 8+ surfaces in lockstep) can't leave a stale `black`/`isort` reference that
  drifts local vs CI. Plus: `.pre-commit-config.yaml` is not run by any workflow (CI only reads its pins),
  so a broken hook config is unguarded. Sector S5. → relates `scripts/check_tool_pins.py`.
- [`project-moon-wiki-knowledge-domain-2026-06-21.md`](./project-moon-wiki-knowledge-domain-2026-06-21.md) —
  **owner-dropped feasibility finding (2026-06-21):** bring the **Project Moon wiki** (Lobotomy Corp /
  Library of Ruina / Limbus Company) into the bot "in one area," the way BTD6 data is available today.
  Verdict: **achievable and a good fit, but a real build** — the reusable half (wiki ingestion via the
  existing `fetch_bloonswiki` MediaWiki/Cargo path + the generic fact store + AI grounding) transfers;
  the hard part is that the knowledge stack is bespoke `btd6_*` and Project Moon's data is more
  fragmented (wiki.gg + Fandom + Miraheze + datamines) and more prose-heavy. Recommend generalizing the
  BTD6 knowledge seam into a domain-agnostic *knowledge domain* with Project Moon as its first second
  instance; phase from Limbus lore Q&A → structured lookups → parity. **PROMOTED to a plan — owner
  picked _full parity, all games_ (Q-0192):**
  [`planning/project-moon-knowledge-domain-plan-2026-06-21.md`](../planning/project-moon-knowledge-domain-plan-2026-06-21.md).
  → relates `subsystems/btd6.md` · `subsystems/ai.md` · `scripts/fetch_bloonswiki.py` ·
  `.github/workflows/btd6-data-refresh.yml`.
- [`free-for-everyone-mission-2026-06-21.md`](./free-for-everyone-mission-2026-06-21.md) —
  **owner-directed (2026-06-21, Q-0190) — the product North Star:** SuperBot becomes a **completely
  free, all-inclusive bot** — no paywalls, premium tiers, or freemium feature-gating; every function
  free for everyone, forever. Owner rationale: it isn't *fair* to paywall online functions; the strategy
  is **consolidation** — one free bot that replaces 5+ paywalled ones ("a revolution"), so *free **and**
  better — and all-in-one* is the wedge (pairs with the V-14 feature-mining lane + the Q-0080 public-bot
  goal). Elevates a scatter of per-feature calls (Q-0039 cosmetic-only/no-P2W · Q-0108 paid tiers
  declined) into one binding principle; resolves tension T-6 via the owner's live "voluntary
  zero-benefit support allowed" pick. The doc's *principle* is decided (Q-0190); its strategy/tactics +
  open questions (open-source posture, anti-paywall lint, the `/support` surface) stay capture-only. →
  relates `roadmap.md` (product principle) · `current-state.md` ▶ Off-limits · router Q-0190 · Q-0039 ·
  Q-0080 · Q-0087.
- [`channel-deployed-component-menu-primitive-2026-06-21.md`](./channel-deployed-component-menu-primitive-2026-06-21.md) —
  **session idea (2026-06-21, Q-0089, from the Carl-bot reaction-roles overhaul plan):** a shared
  primitive for an operator-deployed, DB-persisted `PersistentView` message in a guild channel
  (post → store `message_id` → re-attach on boot → guild-teardown). Three captured features share the
  shape — role menus (the overhaul plan PR 2), starboard (`fun-and-ease` §B1), polls/suggestions
  (`superbot-vision` AG-15) — so extract it at consumer #1 (role menus) and starboard reuses it free.
  → relates `core/runtime/persistent_views.py` · `core/runtime/message_anchor_manager.py` ·
  `planning/reaction-roles-overhaul-plan-2026-06-21.md`.
- [`permission-overlap-guard-2026-06-21.md`](./permission-overlap-guard-2026-06-21.md) —
  **agent-observed, SHIPPED (2026-06-21, self-initiated Q-0172):** a stdlib config-lint
  (`scripts/check_permission_overlap.py`) that flags an `allow` rule shadowed by a broader
  `ask`/`deny` in `.claude/settings.json` — the class behind the maintainer's recurring
  *verify + force-push* confirmation prompt (`git push --force*` ask shadowed
  `git push --force-with-lease*` allow). Catches it at config-edit time, one source of
  truth over the per-incident patch.
- [`bug-book-claimed-signal-2026-06-19.md`](./bug-book-claimed-signal-2026-06-19.md) —
  **agent-observed (2026-06-19):** bug-book entries need a **"claimed / in-progress" signal**. Two
  dispatch runs both picked up **BUG-0016** and one's fix was duplicated/superseded — the Q-0126 claim
  ledger didn't catch it because **bug-book pickups are never claimed there** (the bugs-first reflex
  skips the claim step). Fix (lightest that works): flip the entry's `Status:` to `IN PROGRESS —
  <branch>` in the born-red first commit **+** a claim-ledger line. → extends
  `ci-cost-and-duplicate-work-prevention`.
- [`premature-closure-self-check-2026-06-19.md`](./premature-closure-self-check-2026-06-19.md) —
  **owner-directed (2026-06-19, brainstorm):** teach a session to smell its own **"done."** Premature
  closure — declaring "done / verified / no questions" while latent uncertainty remains — showed up three
  ways in one session (the owner's catch: *"no questions"* → a probe → plenty of questions; the docs-cleanup
  that finished fast but shallow; verification-by-proxy). The idea: a session-close **"are you sure?"
  self-audit** (+ an independent reviewer) — the system performing the probe the owner currently does. →
  relates `ground-truth-audit-protocol` · `autonomous-improvement-loop-vision` · Q-0102.
- [`dev-site-project-status-donut-2026-06-19.md`](./dev-site-project-status-donut-2026-06-19.md) —
  **owner-directed (2026-06-19):** a **modern multi-segment status donut** for the **dev site**
  (build / planned / ideas / bugs at a glance), mapped onto the **doc-badge lifecycle**
  (`ideas`→`plan`→`historical` *is* the state machine) + the bug book — live data via
  `export_dashboard_data.py`. Paired with a **direction**: refocus the dev site on *projects*, not the
  bot (the public site owns the bot). → refines the website-two-site-split plan.
  [mockup](./assets/dev-site-status-donut-mockup-2026-06-19.png).
- [`cog-chooser-customize-before-invite-2026-06-19.md`](./cog-chooser-customize-before-invite-2026-06-19.md) —
  **owner-directed (2026-06-19):** a public-site **"customize before you invite"** cog chooser — pick
  sections (games / moderation / server-mgmt) → toggle the relevant cogs on/off (all-on-deselect *or*
  all-off-select). Maps onto **existing data + seam**: the site catalogue's categories + every
  subsystem's per-guild `enabled` setting. Design crux = *how the pre-invite selection reaches the bot*
  (recommend a seeded setup-link v1; OAuth-state pre-config rides the control-API security review). →
  pre-invite sibling of the Q-0179 manage-my-server panel.
- [`sector-scoped-lean-boot-for-cheap-models-2026-06-19.md`](./sector-scoped-lean-boot-for-cheap-models-2026-06-19.md) —
  **owner-directed (2026-06-19; B1-priority next session):** make Sonnet usable by cutting the orientation
  tax — a **sector-scoped lean boot** (declare your sector → load only its invariants + folio + active plan
  + Next-action, skip the rest), built on the owner's existing 5-sector partition (Q-0137) via the
  agent-context compiler. Unlocks the separate Sonnet weekly bucket; also flags verifying the file-ignore
  mechanism (`.claudeignore` / settings deny-globs) to keep tests/data/generated files out of context. →
  relates `planning/procedures-to-skills-conversion-plan` · `.claude/rules/context-compiler.md`.
- [`ai-correction-report-and-ticket-service-2026-06-19.md`](./ai-correction-report-and-ticket-service-2026-06-19.md) —
  **owner-directed (2026-06-19, brainstorm; needs its own extensive session):** when a user corrects the
  AI, have it **report the correction to the owner** (a write into the owner review inbox, never the public
  site) — the first step toward an **AI ticket service** (bug reports · server problems · moderation). The
  hard part the owner named: **audience routing, fail-closed** — the AI must classify *who each report is
  for* (owner / this server's mods / public) and never leak a server-private issue to the public website.
  Rails already exist (owner-review-inbox · submissions DB · Hermes triage); it's the AI's first *write*
  capability, so gated by Q-0048. **PARTIALLY PROMOTED (band-#1140 pass):** the *board* it writes into is
  planned ([`planning/feedback-board-generalization-plan-2026-06-19`](../planning/feedback-board-generalization-plan-2026-06-19.md));
  the AI audience-router stays plan-the-questions-first → routed as **Q-0183**. → relates
  `planning/owner-review-inbox-plan` · `per-command-feedback-threads`.
- [`explore-hub-federated-world-2026-06-19.md`](./explore-hub-federated-world-2026-06-19.md) —
  **owner-directed (2026-06-19, brainstorm):** the **Explore hub** as the missing spine — a *federated*
  open world where mining/fishing/pets/quests share one character, currency, and a light survival/adventure
  overlay, **but each subsystem still feels like its own complete game**. Codifies the direction the fishing
  plan is already drifting toward (shared `game_xp` · unified character · swappable loadouts); homes four
  separate gated lanes under one world model. **PROMOTED → plan (band-#1140 pass, Q-0172):**
  [`planning/explore-hub-federated-world-plan-2026-06-19`](../planning/explore-hub-federated-world-plan-2026-06-19.md)
  (ungated spine: top-level hub + world registry + global/per-game XP split; deferred layers routed as
  **Q-0182**). → relates `planning/{explore-hub-federated-world-plan,fishing-open-world-expansion,mining-hub-redesign,rpg-survival-difficulty-design}`.
- [`wild-encounters-activity-spawning-2026-06-20.md`](./wild-encounters-activity-spawning-2026-06-20.md) —
  **from the owner's Pokétwo/JMusicBot research report (2026-06-20):** activity-based **wild encounters** —
  non-bot messages accrue a per-channel counter → the bot spawns a Claim-button encounter → first valid
  claimer gets a reward routed through `economy`/`game_xp`/inventory. The **one Pokétwo mechanic with no
  analog** (fishing/mining are command-only); net-new, ungated, anti-P2W, docks into the Explore world hub.
- [`idle-game-offline-summary-2026-06-22.md`](./idle-game-offline-summary-2026-06-22.md) —
  **BUILT 2026-06-22 (PR #1331):** `utils/idle_summary.py` narrates the "🌙 while you were away,
  +N eggs" return-moment on the farm panel. Kept for provenance; the live remainder is reusing
  the helper from a *second* idle system (the rule-of-three `settle/spend` extraction).
- [`mining-grid-encounters-2026-06-22.md`](./mining-grid-encounters-2026-06-22.md) —
  **owner-named follow-up to the grid Mine (Q-0173):** the grid Mine (hub-redesign PR 3) shipped
  encounter-free by decision; this captures the deferred **depth-gated, sparse** random encounters while
  roaming the grid ("after a certain depth … but not too many"), routed through `mining_workflow` (RS02).
  Distinct from wild-encounters (exploration-triggered vs. chat-activity-triggered) but could share one
  resolution engine. → relates `planning/mining-hub-redesign-2026-06-15` · Q-0173 · Q-0087.
  **SPEC'D → plan (Lane A):** [`planning/poketwo-musicbot-feature-mapping-plan-2026-06-20`](../planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md);
  build sequence + spawn design routed as **Q-0186**. → relates `planning/{explore-hub-federated-world-plan,fishing-open-world-expansion}`.
- [`plan-homing-guard-2026-06-19.md`](./plan-homing-guard-2026-06-19.md) — **SHIPPED 2026-06-20 (PR #1174).**
  **session idea (2026-06-19, Q-0089, from the planning-map cleanup):** a stdlib
  `scripts/check_plan_homing.py` asserting every non-`historical` `docs/planning/` doc is linked from a
  **routing** doc (roadmap · a folio · current-state · the new plan index) — not merely *reachable* from
  anywhere. Closes the gap that let the dashboard/website cluster (~8 active plans) go unrouted for ~30 PRs
  while `check_docs --strict` stayed green. The plan-level complement to `check_sector_map.py` (folio
  homing) + `check_plan_backlog.py` (depth). Disposable (Q-0105). → relates `scripts/check_docs.py` ·
  `docs/planning/README.md`.
- [`loop-health-gh-unavailable-fallback-2026-06-19.md`](./loop-health-gh-unavailable-fallback-2026-06-19.md) —
  **session idea (2026-06-19, Q-0089, from the band-#1110 reconciliation pass):** `check_loop_health.py`
  (Q-0135) SKIPs on every reconciliation pass because the in-container routine has no `gh` — give it a
  `gh`-absent fallback (read the newest `reconcile` issue's author via the GitHub REST API, the same read
  the agent does by hand) so the control-plane ROUTINE_PAT row is verifiable *by the script*, not only by a
  manual MCP read no checker can see. Disposable (Q-0105). **PROMOTED → plan (band-#1170 pass, 2026-06-20,
  Q-0172):** [`planning/loop-health-gh-fallback-plan-2026-06-20`](../planning/loop-health-gh-fallback-plan-2026-06-20.md).
  → relates `scripts/check_loop_health.py` · `operations/autonomous-routines.md` § "Control-plane state".
- [`reconcile-pass-tail-trim-actuator-2026-06-20.md`](./reconcile-pass-tail-trim-actuator-2026-06-20.md) —
  **session idea (2026-06-20, Q-0089, from the band-#1200 reconciliation pass):** the `current-state.md`
  ▶ Next action callout grows one "Nth Q-0107 PASS DONE" sentence every pass and is now a wall of consumed
  band-history (the standing Q-0102 finding). The Recently-shipped *list* got its trim actuator (#1181); the
  *callout* has none. Idea: a `--callout` actuator that keeps the two newest pass segments and moves older
  ones into their per-band pass records, leaving a one-line pointer — making the documented "aggressive prune"
  deterministic. Disposable (Q-0105); heed BUG-0020 (ground-truth + self-test the fragile spot).
  → relates `docs/current-state.md` · `scripts/trim_recently_shipped.py`.
- [`reconcile-callout-line-budget-guard-2026-06-21.md`](./reconcile-callout-line-budget-guard-2026-06-21.md) —
  **session idea (2026-06-21, Q-0089, from the band-#1230 reconciliation pass):** the ▶ Next action callout
  reached a **40.5 KB wall** before a pass finally pruned it — because the bloat was *prose*, not a measured
  number a checker could flag. Idea: a warn-only sub-check that measures the live callout's length and warns
  when it crosses a budget (≥ 6 KB), the way `check_docs` ratchets Recently-shipped at 20. The **gauge** that
  pairs with the trim **actuator** above (number trips → `--callout` run resolves it). Disposable (Q-0105).
  → relates `docs/current-state.md` · `scripts/check_docs.py`.
- [`recently-shipped-auto-trim-helper-2026-06-20.md`](./recently-shipped-auto-trim-helper-2026-06-20.md) —
  **SHIPPED 2026-06-20** as `scripts/trim_recently_shipped.py` + `tests/unit/scripts/test_trim_recently_shipped.py`,
  wired into the reconciliation routine's STEP 2. A stdlib **actuator** for
  the Recently-shipped trim-to-archive step — move the oldest over-ratchet bullets from `current-state.md`
  into the archive and **recompute the "Older merges (#X … #535)" floor pointer** from the actual lowest
  live PR, with a dry-run diff. The *actuator* complement to the `check_current_state_ledger.py` *detector*;
  closes the unguarded "wrong floor pointer" drift class (#763-style, Q-0120). Disposable (Q-0105). →
  relates `scripts/check_current_state_ledger.py` · `scripts/check_docs.py` · `band-pr-merge-status-helper`.
- [`band-pr-status-author-classifier-2026-06-21.md`](./band-pr-status-author-classifier-2026-06-21.md) —
  a `band_pr_status --themes` mode that reads each band PR's touched paths and emits a **draft
  grouped-entry skeleton** for the Recently-shipped ledger, so the pass edits rather than reverse-engineers
  the opaque merge-commit PRs (this pass hand-`git show --stat`'d 11 of them). The next mechanisation of the
  reconciliation routine after the trim actuator + callout prune. Stdlib, disposable (Q-0105). → relates
  `scripts/band_pr_status.py` · the reconciliation routine STEP 2.
- [`band-themes-show-pr-subject-2026-07-01.md`](./band-themes-show-pr-subject-2026-07-01.md) —
  follow-on to the classifier above: `--themes` buckets by **touched dir** and omits each PR's **subject**,
  so the agent still hand-greps `git log` titles to regroup (the band-#1620 pass did exactly this). Print
  the PR subject on every skeleton line (from the git log the helper already runs) so themes are readable
  without re-fetching. Additive, offline, disposable (Q-0105). → relates `scripts/band_pr_status.py`.
- [`band-pr-merge-status-helper-2026-06-19.md`](./band-pr-merge-status-helper-2026-06-19.md) —
  **SHIPPED 2026-06-20** as `scripts/band_pr_status.py` + `tests/unit/scripts/test_band_pr_status.py`,
  wired into the reconciliation routine's STEP 2. A stdlib
  `scripts/band_pr_status.py` that classifies
  every PR in a band as **merged / closed-unmerged / open** — so the reconcile ledger step doesn't hand-check
  merged-vs-superseded (this pass had to verify #1133 was closed-unmerged by `git branch --contains`). Closes
  a #763-class ground-truth gap (Q-0120/Q-0181). Disposable (Q-0105). → relates
  `scripts/check_current_state_ledger.py` · the reconciliation routine.
- [`per-command-feedback-threads-2026-06-19.md`](./per-command-feedback-threads-2026-06-19.md) —
  **owner-directed (2026-06-19):** every command/cog on the bot site carries an optional **feedback thread**
  (anyone posts questions/bugs/improvements), gated by an **Anthropic-API moderation pass** (clean-up +
  foul-language block/rewrite) — "Codex for the bot's features." Goals: owner leaves inline thoughts to
  review later · users see if an issue was already raised · honest feedback for all. Supersedes the v1
  static `notes` field; reuses the submissions store + moderation pipeline. → relates website plan P2/§2.3/§4.
- [`idea-to-cog-command-mapping-2026-06-19.md`](./idea-to-cog-command-mapping-2026-06-19.md) —
  **owner-directed (2026-06-19):** map every idea (and bug) to its **cog/command** (explicit tag + a
  validator; heuristic as interim fallback) — the truth source for the site's per-command **status**
  (`in-progress` if any related ideas/bugs) and **linked-ideas** discoverability. "As fast as possible,
  not rushing." → relates `export_dashboard_data.py` · the subsystem registry · website plan S1.1.
- [`website-two-site-split-2026-06-19.md`](./website-two-site-split-2026-06-19.md) —
  **owner-directed (2026-06-19, Q-0178):** split the single dashboard into a **public bot site** (users;
  command reference, changelog, public bug/suggestion form → DB → owner-approve → mirror to GitHub) and a
  **dev/repo site** (the current dashboard, all pages public read-only, owner-gated edits); 2 Railway
  services. Structured into the required-output brief
  [`planning/website-two-site-split-planning-brief-2026-06-19.md`](../planning/website-two-site-split-planning-brief-2026-06-19.md)
  for the next planning session. → relates `dashboard/` · `scripts/export_dashboard_data.py`.
- [`public-data-contract-field-snapshot-2026-06-19.md`](./public-data-contract-field-snapshot-2026-06-19.md) —
  **session idea (2026-06-19, Q-0089, from the website two-site-split foundation build #1109):** S1
  guards the public `site.json` subset at the **top-level key** boundary (fail-closed whitelist); the
  uncovered leak class is a new *field* inside an allowed family (`commands`/`catalogue`). A tiny stdlib
  snapshot test pins the **exact leaf field set per public family** so any new field trips a conscious
  "is this public?" review — extending redaction-by-construction from keys to leaves. Quick-win,
  disposable (Q-0105). → relates `scripts/export_dashboard_data.py` (`build_site_subset`) ·
  `scripts/check_dashboard_data.py` · the split plan §2.2/§4.1.
- [`governance-files-presence-guard-2026-06-19.md`](./governance-files-presence-guard-2026-06-19.md) —
  **SHIPPED (PR #1120)** as `scripts/check_governance_files.py` — a tiny
  stdlib guard that asserts the new root governance files (`LICENSE` ·
  `SECURITY.md` · `CONTRIBUTING.md` · `CITATION.cff`) stay present **and** that the repo paths cited in
  `CONTRIBUTING.md`/`SECURITY.md` still resolve — `check_docs.py` scopes `docs/**` only, so these root
  files are unguarded. "Executable verification over prose" applied to the governance layer. Quick-win,
  disposable (Q-0105). → relates `scripts/check_docs.py` · the P0 work in
  [`planning/repo-structure-improvement-plan-2026-06-19.md`](../planning/repo-structure-improvement-plan-2026-06-19.md).
- [`repo-consistency-linter-2026-06-17.md`](./repo-consistency-linter-2026-06-17.md) —
  **owner-directed (2026-06-17, Q-0170):** *"something like CI but specifically to find
  inconsistencies"* — panels missing a back button, cogs not following the arch rules, cogs sending
  ephemeral follow-ups instead of editing in place. A new `scripts/check_consistency.py` (stdlib AST,
  the `check_architecture.py` house style) with a per-rule allowlist + warn-first graduation. **The
  flagship buildable lane** (one rule per PR = a real slice, feeds Q-0164). Executable plan:
  [`repo-consistency-linter-plan-2026-06-17.md`](../planning/repo-consistency-linter-plan-2026-06-17.md).
  → relates `scripts/check_architecture.py` · `disbot/views/` · `disbot/cogs/`.
- [`product-lanes-gated-balance-flag-2026-06-18.md`](./product-lanes-gated-balance-flag-2026-06-18.md) —
  **session idea (2026-06-18, Q-0089, from the band-#1050 reconciliation pass):** a warn-only
  `⚑ Product lanes gated` reporter — the **balance-axis** sibling of the Q-0164 PLAN-BACKLOG-THIN
  (depth-axis) flag. Classifies the buildable queue by sector and flags when *every* S1/S2 product
  lane is gated (the current standing state), so the owner-side lever (merge a `needs-hermes-review`
  PR / decide Q-0175) surfaces automatically every pass instead of via a hand-written §3 paragraph.
  → relates the Q-0164 flag · `check_plan_backlog.py` · `roadmap.md` sectors.
- [`owner-review-inbox-2026-06-17.md`](./owner-review-inbox-2026-06-17.md) —
  **owner-directed (2026-06-17, Q-0169, capture-only):** a channel to **post ideas/cog-command
  reviews** that sessions read and act on, with a visible open→resolved status (the owner forgets
  cog-review notes mid-session and has no "is it fixed?" view). Near-term = a dashboard "Review board"
  backed by labeled issues / a committed markdown inbox; eventual = a standalone communication site.
  Executable plan: [`owner-review-inbox-plan-2026-06-17.md`](../planning/owner-review-inbox-plan-2026-06-17.md).
  → relates `dashboard/` · the bug book · Q-0159.
- [`agent-tooling-automation-shortlist-2026-06-17.md`](./agent-tooling-automation-shortlist-2026-06-17.md) —
  **owner-directed (2026-06-17, Q-0170):** a shortlist to pick from for **dedicated Claude Code
  skills** (`/route-idea`, `/cog-review`, `/plan-band`, `/fix-drift`) + **automation scripts**
  (`check_plan_backlog.py` for the Q-0164 flag) + a **repo-native discovery aid** (CodeGraph/Grimp
  but domain-semantic — must complement `context_map.py`/`wiring_map.py`, not re-do them). Builds on
  the plugins-evaluation idea. → relates `scripts/` · the existing `/pre-pr`,`/session-close` skills.
- [`codex-automated-pr-review-2026-06-17.md`](./codex-automated-pr-review-2026-06-17.md) —
  **owner-mentioned (2026-06-17, Q-0171, research-stage):** wire Codex (OpenAI) to auto-review PRs —
  a second, different-model reviewer (the anti-monoculture principle behind `needs-hermes-review`).
  Research the exact mechanism + cost/auth, then put augment-vs-replace + merge-authority to the
  owner. No build until the mechanism + spend envelope are confirmed. → relates Q-0117 (Hermes review).
- [`generated-artifact-freshness-umbrella-2026-06-17.md`](./generated-artifact-freshness-umbrella-2026-06-17.md) —
  **session idea (2026-06-17, Q-0089, from the dashboard.json structural-drift reporter #1025):** the
  warn-only structural-drift reporter just built for `dashboard.json` applies to *every* committed
  generated artifact (`env-vars.md`, the agent-context packs, …), each guarded in isolation today. One
  small `check_generated_artifacts_fresh.py` umbrella — a registry of `(generator, committed_path,
  structural-key extractor)` tuples emitting soft "N surfaces behind" warnings — generalizes the
  manifest-spine "AST is drift-detection" philosophy so no future artifact silently rots.
  **IMPLEMENTED #1027** (2026-06-17) as `scripts/check_generated_artifacts_fresh.py` — built as Q-0105
  dev tooling (read-only/warn-only/disposable, not a bot feature so the FIX-phase gate is N/A); kept
  manual/ad-hoc (not hard-CI-wired) with `--strict` for the reconciliation cadence pass. → relates
  `scripts/` tooling · the reconciliation cadence pass.
- [`routine-permission-surface-lint-2026-06-16.md`](./routine-permission-surface-lint-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the band-#990 reconciliation pass):** the routine stalled
  twice on a `permissions.ask` `rm` prompt (fixed reactively as Q-0161). A stdlib
  `scripts/check_routine_permission_surface.py` would evaluate the commands the routines run against
  the current `.claude/settings.json` `ask`/`allow` rules and **fail on any that resolve to `ask`** —
  turning "every routine command must be `allow`, never `ask`" into a pre-flight CI guard so a settings
  change can't silently re-introduce an unattended stall. Cheap, read-only, disposable (Q-0105). →
  relates `.claude/settings.json` · Q-0149/Q-0161.
- [`btd6-shorthand-corpus-eval-2026-06-16.md`](./btd6-shorthand-corpus-eval-2026-06-16.md) —
  **SHIPPED 2026-06-16 (PR #1007)** via a Q-0015 grooming pass: the **corpus class-guard test**
  (`tests/unit/services/test_btd6_shorthand_corpus.py`) holds the canonical community-shorthand
  vocabulary (`despo`/`impop`/`r53`/`420 farm`/`d67`/…) and asserts each routes to
  `AITask.BTD6_ANSWER` (+ conservatism negatives), guarding the recurring "shorthand falls to the
  unguarded general path → model freelances" bug class (BUG-0001/0003/0004/0008/0015) against a
  silent router regression — previously covered only by scattered per-bug tests. The *minor*
  hero-per-level-stats sibling finding (only non-headline-level exact stats are a gap) stays
  `captured` at low priority. → relates `services/ai_task_router.py` · `utils/btd6/keywords.py`.

- [`developer-dashboard-2026-06-16.md`](./developer-dashboard-2026-06-16.md) —
  **owner-requested + approved (2026-06-16, Q-0155):** a personal website / developer dashboard
  deployed as a second Railway service — checklist, update tracker, bot-function catalogue,
  ideas/bug board, **public** bug reporting (+ GitHub-issue mirror), a multi-AI **control board**
  over the current flow, and a **secrets** zone (manage via Railway + a static "where is each env var
  used" map). Core principle: *surface the repo's existing structured data, don't duplicate it.*
  **Phase 1 (read-only MVP) ✅ shipped PR #967**; the **Phase 3 env-usage map ✅ shipped PR #969**
  (`/env` page + `scripts/scan_env_usage.py` + generated `docs/operations/env-vars.md`); Phases 2/4
  + Phase 3 value-management active. Authoritative plan:
  [`developer-dashboard-plan.md`](../planning/developer-dashboard-plan.md). → relates `dashboard/` ·
  `scripts/export_dashboard_data.py`.

- [`env-map-deploy-readiness-cross-check-2026-06-16.md`](./env-map-deploy-readiness-cross-check-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the env-usage map #969):** the scanner now knows which env
  vars are *required*; cross-reference that set against the names present in the target Railway service
  (names only, never values) so the dashboard `/env` page shows a **deploy-ready / N required unset**
  banner — turning the passive inventory into an active config check. Gated on the Phase 3 Railway-API
  integration. → relates `scripts/scan_env_usage.py` · `dashboard/`.

- [`dashboard-registry-coverage-check-2026-06-16.md`](./dashboard-registry-coverage-check-2026-06-16.md) —
  **SHIPPED 2026-06-16 (PR #990)**, broader than sketched: `scripts/check_dashboard_data.py` validates
  the exported `dashboard.json` — cog→subsystem resolution (with a curated allow-list) + count
  integrity + required fields — and a unit test validates the freshly-built export, so a new
  unregistered cog / broken join / count drift **fails CI** instead of silently degrading a page.
  → `scripts/check_dashboard_data.py` · `tests/unit/scripts/test_check_dashboard_data.py`.
- [`dashboard-subcog-parent-subsystem-2026-06-16.md`](./dashboard-subcog-parent-subsystem-2026-06-16.md) —
  **mostly SHIPPED 2026-06-16 (PR #995):** `scan_commands._COG_SUBSYSTEM_OVERRIDES` maps the BTD6
  sub-cogs → `btd6` and RPS → `rps_tournament`, so they inherit the parent's registry identity on
  `/commands` (no more generic 🧩); the integrity guard's allow-list shrank 8 → 3. **Deferred (owner
  intent):** `ParagonCog` / `SetupCog` / `HermesCog` stay allow-listed until a parent is confirmed.
  → relates `scripts/scan_commands.py` · `scripts/check_dashboard_data.py`.
- [`cog-declares-its-subsystem-2026-06-16.md`](./cog-declares-its-subsystem-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the sub-cog mapping #995):** the dashboard guesses each
  cog's subsystem from its **class name**, propped up by three hand-maintained lists (acronym table ·
  override map · the guard's allow-list) that drift independently — and #995 still couldn't resolve 3
  cogs from the name alone. Replace it with an **authoritative declaration** the scanner reads (a cog
  `SUBSYSTEM = "btd6"` class attribute, or a command-surface-ledger join), deleting the override map
  and self-describing every cog including sub-cogs. → relates `scripts/scan_commands.py` ·
  `core/runtime/command_surface_ledger.py` · `utils/subsystem_registry.py`.
- [`idea-subsystem-tag-on-ideas-2026-06-19.md`](./idea-subsystem-tag-on-ideas-2026-06-19.md) — ✅
  **IMPLEMENTED (re-badged `historical` 2026-06-19):** the `> **Subsystem:**` header tag is live in
  `export_dashboard_data.py` (`_subsystem_open_work`). —
  **session idea (2026-06-19, Q-0089, from building S1.1 of the website command browser):** the public
  command browser links each command to its subsystem's open **ideas** ("what's planned" teasers +
  the finished/in-progress badge), but idea files carry no subsystem field, so the producer falls back
  to a filename-slug **heuristic** that cross-matches single common-word keys (`chain`/`channel`).
  Add an optional **`Subsystem:` front-matter tag** on idea files (registry-validated); prefer it,
  keep the heuristic as fallback — the "explicit tag, heuristic fallback" shape S1.1 recommended. The
  redaction lens keeps even a stray match safe, so this is precision, not safety. Counterpart to
  `cog-declares-its-subsystem` (cogs declare; this is *ideas* declare). → relates
  `scripts/export_dashboard_data.py` (`_subsystem_open_work`) · `tests/unit/scripts/`.
- [`ledger-dedup-linter-2026-06-16.md`](./ledger-dedup-linter-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the merge=union fix #1003):** #1003 made the append-only
  ledgers (`active-work.md`, `ideas/README.md`) auto-merge via git `merge=union`, whose one downside is
  it never deletes/dedups — so stale or duplicate claim/idea lines can accumulate. A tiny stdlib
  `scripts/check_ledger_hygiene.py` flagging duplicate claim branches + duplicate idea-file links
  (report-only, `--strict` fails CI) keeps the now-conflict-free ledgers *clean*. → relates
  `docs/owner/active-work.md` · `docs/ideas/README.md` · `.gitattributes`.
- [`success-metric-alignment-with-verified-success-2026-06-16.md`](./success-metric-alignment-with-verified-success-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the Claude Code expertise research readout):** Anthropic's
  ~400K-session study measures **verified success** by *hard signals* (tests passing, commits,
  explicit confirmation) — our CI-green + auto-merge + born-red gate is the same philosophy. Mostly
  confirmatory; the contained value is naming which session *classes* should require explicit owner
  confirmation before auto-merge vs. CI-only (the `needs-hermes-review`/`do-not-automerge` seam may
  already cover it). → relates `docs/collaboration-model.md` · CLAUDE.md § Session workflow.
- [`docs-ledger-parsing-helper-2026-06-16.md`](./docs-ledger-parsing-helper-2026-06-16.md) —
  **promoted Q-0089 idea (2026-06-16, originally surfaced in #967's session log):** extract the
  repeatedly-copied markdown-ledger regexes (Status badge / `BUG-NNNN` / idea-file parsers) into one
  stdlib `scripts/_docs_ledger.py` so the dashboard exporter and the `check_*` scripts share one
  source of truth (the `_STATUS_RE` "Mirrors check_session_gate.py" copy is the drift smell). Build it
  in a session that does **not** depend on `check_session_gate` for its own merge. → relates
  `scripts/check_session_gate.py` · `scripts/export_dashboard_data.py`.
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
- [`sessionstart-surface-soft-check-signals-2026-06-16.md`](./sessionstart-surface-soft-check-signals-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the atlas thread #960/#964):** the repo keeps adding *soft*
  signals that only help if run by hand (the `check_docs` ratchets + new inventory-count guard, the
  uncommitted atlas body, the `--check` tools). Add **one SessionStart banner line** (`Docs: soft — …`)
  backed by a `check_docs --soft-summary` mode so the soft ratchets are proactively visible, not
  discovered by luck. Touches the SessionStart hook → owner-wires per Q-0106. → relates
  `scripts/claude_session_start.sh` · `scripts/check_docs.py`.
- [`deterministic-floor-catalogue-2026-06-16.md`](./deterministic-floor-catalogue-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the §7.6 capability/bloon roster-floor PR #975):** the
  `_BTD6_LIST_BUILDERS` family grows ~one floor per dispatch, but "what's already fronted / which data
  surface has no floor yet?" is recoverable only by grepping the dispatcher + reading each builder. A
  tiny stdlib script that introspects the live tuple → maps each builder to its trigger phrase + the
  service it fronts, and **flags roster-shaped surfaces with no floor** (hero capabilities, CT relics),
  makes the next member obvious + the family's coverage legible. Decided-lane; small. → relates
  `services/btd6_context_service.py::_BTD6_LIST_BUILDERS` · `services/btd6_capability_service.py`.
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
- [`creature-sim-engine-constant-parity-guard-2026-06-21.md`](./creature-sim-engine-constant-parity-guard-2026-06-21.md) —
  **session idea (2026-06-21, Q-0089, from the creature PvP battle-engine PR #1213):** the combat
  design constants (rarity budgets, archetype weights, type-chart multipliers, move powers, buff
  step/cap, level-scaling rates) now live in **both** `tools/game_sim/creature_battle_sim.py` (the
  balance simulator) and `disbot/utils/creatures/battle.py` (the runtime engine that graduated the
  math) — a two-sources-of-truth drift class. A small stdlib parity test (`importlib`-loads both,
  asserts they agree) keeps the sim's "PLAYABLE" verdict honest about the bot players actually play.
  Self-merge lane; disposable once the sim is retired. → relates `tests/unit/tools/` ·
  `tests/unit/views/test_panel_base_class_allowlist_parity.py` (the same parity-guard shape).
- [`creature-pvp-rematch-button-2026-06-21.md`](./creature-pvp-rematch-button-2026-06-21.md) —
  **⚑ self-initiated (2026-06-21, Q-0172, built #1262):** a 🔄 Rematch button on the creature-PvP
  outcome embed, clickable by either fighter, re-issuing a fresh `!cbattle` challenge — continuous
  laddering with no new battle logic (reuses the challenge flow + the #1257 audited result-recording).
  Mirrors the rps `🔁 Play again` affordance. → relates `disbot/views/creature_battle/`.
- [`reference-integrity-invariants-2026-06-16.md`](./reference-integrity-invariants-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the BUG-0014 `!coglist`-loop fix PR #949):** BUG-0014 was a
  dangling reference (a synonym → a command that didn't exist) that failed *silently*. Extract the
  AST command-surface discovery from the new synonym guard into a shared test helper, and close the
  known sibling gap — `SUBSYSTEMS.entry_points` → real command, which `test_entrypoints.py` documents
  as unchecked. One "what commands exist" source for every "this declaration must resolve" invariant.
  → relates `tests/unit/registry/test_entrypoints.py` · `utils/subsystem_registry.py` · `utils/synonyms.py`.
- [`ledger-bookkeeping-tally-soft-lint-2026-06-17.md`](./ledger-bookkeeping-tally-soft-lint-2026-06-17.md) —
  **workflow / tooling (2026-06-17, band-#1020 Q-0107 pass):** the `current-state.md` "Older merges →
  archive" pointer had accreted a ~2,000-word per-session running tally that duplicated the archive
  file's own record — pruned this pass. A disposable soft `check_docs` lint could flag a
  pointer/bookkeeping line that crosses a word budget ("this is a running tally — point at the
  authoritative record instead"). The reusable principle: *don't hand-maintain a tally of a fact that
  already has an authoritative record.* → relates `scripts/check_docs.py` · `docs/current-state.md`.
- [`server-owner-configurable-moderation-dms-2026-06-16.md`](./server-owner-configurable-moderation-dms-2026-06-16.md) —
  **owner policy → feature (2026-06-16, from the Q-0147 decision):** the owner's standing DM rule is
  *profile/onboarding DMs are opt-in and never on join; the only non-opt-in DMs are moderation/warning
  DMs, and only when the server owner enables them with per-action config.* The opt-in half is
  myprofile PR C; this captures the second half — a master toggle + per-action map
  (warn/timeout/kick/…) on the `!settings` → Moderation surface, riding the audited `moderation_service`
  seam (off by default, fail-open). → relates `services/moderation_service.py` · the settings surface.
  **✅ PROMOTED TO A PLAN (2026-06-17, band-#1020 Q-0107 pass, Q-0144 idea→plan):**
  [`planning/moderation-dm-config-plan-2026-06-17.md`](../planning/moderation-dm-config-plan-2026-06-17.md)
  — scouting the seam found the DM machinery already exists (`_notify_target` + `ModerationPolicy.dm_on_action`
  + `render_dm_message`), so the plan *extends* it (master `dm_on_action` + a `dm_actions` csv mirroring
  `public_log_actions`), not a new subsystem. Turn-key, one PR, no migration. **This is the next ungated ▶ slice.**
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
  memory** — remember a Discord user across conversations (V-04). **Owner policy (2026-06-19): opt-in,
  user-chosen global/per-guild scope, declared `remember this:` storage as the cheap/accurate v1;
  Honcho-style conclusion-extraction is an optional *later* inference layer** (matters under the Q-0082
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
- [`pil-card-render-contract-guard-2026-06-22.md`](./pil-card-render-contract-guard-2026-06-22.md) —
  **test tooling (2026-06-22, reaction-roles PR 6 session):** one cross-cutting invariant that pins the
  whole `utils/*_render.py` card family to its shared contract — lazy PIL import, `bytes | None` return
  (`None` when Pillow is absent), no network. Each renderer has its own per-module no-PIL test, but
  nothing catches a *new* renderer that forgets the guard and lets `ImportError` propagate (a crash on a
  Pillow-less boot path — the sandbox runs degraded, exactly where it bites). Small; an explicit
  `(callable, sample_kwargs)` registry + the existing `__import__`-fail monkeypatch.
- [`migration-number-collision-guard-2026-06-22.md`](./migration-number-collision-guard-2026-06-22.md) —
  **dev tooling / CI (2026-06-22, reaction-roles PR 6 saga):** kill the migration-number **renumber
  treadmill** — a held PR's migration was renumbered 4× in one afternoon (085→086→088→089) as the fleet
  kept appending the next integer to `main`. A `scripts/check_migration_collision.py` (fetch main, diff
  the branch's new numbers, print the next-free + the `git mv`) wired into the Stop/`pre-pr` hook catches
  it **before** the 4-min CI round-trip; a merge-aware local CI mirror closes the local-green/CI-red gap
  (CI tests `refs/pull/N/merge`, the branch-only local run can't see the dup). Durable cure: assign the
  number at merge time.
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
- [`meter-external-moderation-calls-2026-06-16.md`](./meter-external-moderation-calls-2026-06-16.md) —
  **session idea (2026-06-16, Q-0089, from the image-moderation build #941):** image moderation
  calls OpenAI's moderation endpoint once per uploaded image (when enabled) with **no cost
  accounting** — the same un-metered-external-call gap the NL event scheduler (Q-0112) was told to
  close. Route the `openai_moderation` call through the Q-0082 spend-meter and fail open when the
  ceiling is hit. Small, reuses existing machinery; natural next-band slice once the meter seam is
  confirmed. Small/safe grooming-lane candidate.
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
- [`multi-repo-program-kit-lab-trading-2026-07-07.md`](./multi-repo-program-kit-lab-trading-2026-07-07.md) —
  **maintainer vision (2026-07-07, live drop, captured strengthened):** the program frame above
  the rebuild — three repos on one substrate: `superbot-next` (the plan of record) · **the
  substrate-kit as its own repo = the autonomous self-improvement lab** (fitness functions —
  the Phase-2.5 A/B as standing benchmark, ideas-that-ship as the acceptance metric; own work
  surfaces: test-bot token, Railway project with caps, deployable sites) · **a trading-research
  repo** (backtest-decides-strategy, falsification promotion ladder, real-money brake). Also
  answers repo-start mechanics: fresh-from-kit + old repo attached read-only as the oracle,
  never clone-as-base. Kit extraction rides the step-7 second-consumer moment → **discuss/plan
  lane** (the step-6–8 kickoff session reads this and decides the extraction fork ⚑).
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
  **→ PROMOTED to an executable plan (2026-06-19, Q-0172):**
  [`planning/ai-panel-inplace-navigation-plan-2026-06-19.md`](../planning/ai-panel-inplace-navigation-plan-2026-06-19.md)
  (2–3 PRs; also the blocker for graduating the consistency linter's `edit_in_place` rule, whose 17
  remaining findings are exactly this family).
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
  **✅ IMPLEMENTED 2026-06-19 (Q-0015 grooming):** `check_current_state_ledger.py` now parses the
  `Last reconciliation pass:** PR #N` marker (`marker_pr`), partitions missing PRs into **drift**
  (`pr <= N`, actionable) vs **benign lag** (`pr > N`, informational) via `classify_missing`, and
  `--strict` exits 1 **only on drift** — removing the standing false-red `/session-close --strict`
  hit on newest-merge lag (the live run, red on 23 lag PRs, now exits 0). Benign lag is still printed
  so the reconciliation routine reads the band. Shipped with its window-scale sibling below.
- [`ledger-window-scale-to-marker-2026-06-19.md`](./ledger-window-scale-to-marker-2026-06-19.md) —
  **✅ IMPLEMENTED 2026-06-19 (Q-0015 grooming):** `check_current_state_ledger.py`'s default window is
  now sized to the band since the `Last reconciliation pass:** PR #N` marker (`band_window` =
  `max(DEFAULT_WINDOW, <merges newer than #N>)`), so a fast band can't hide an older drift past a fixed
  edge (`--window N` stays an explicit override). The live run auto-sized to the full 23-merge band vs
  the old fixed 15. Same marker mechanism as the benign-lag sibling above; both verified + unit-tested.
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

## Completion-first gate (soft default — Q-0209)

The bot is close to production-ready, so the standing bias is **finish existing features before
starting new ones**. When grooming or promoting an idea, sort it first:

- **Deepens / completes an existing unit** (a missing action, a variant, a depth layer, a UX fix for
  a game or server function already in the
  [completion ledger](../planning/feature-completion/README.md)) → **in-scope and prioritized**.
  This is *deepening*, not new — promote it normally.
- **A brand-new unit** (a game/function the bot doesn't have yet) → still **captured here**, but
  **parked behind the completion gate** by default. The owner can greenlight one anytime; without
  that, prefer moving an "deepens-existing" idea instead.

This is a **soft** default, not a freeze — it steers the backlog toward certifying what exists
([`docs/planning/feature-completion/`](../planning/feature-completion/README.md)) without blocking
the owner's explicit "build this new thing." Full policy + the unit ledger live in the
feature-completion system.

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

# SuperBot — Current State

> **Status:** `living-ledger` — living status ledger (project state). **Not binding.**
> **Source code and merged PRs always win over this file.**
> The In-flight section below is a dated snapshot — **verify open PRs against
> live GitHub** before trusting it (two same-session reports already
> contradicted each other across a single merge).
>
> **▶ Next action — one live queue:** the **[decade queue](planning/reconciliation-pass-2026-06-12.md)** (the first Q-0107 reconciliation pass, 2026-06-12): hardening **P0 tracks** (P0-2/3/4 unblocked by Q-0098–Q-0100) · **backup posture** · the new **Q-0108–Q-0112 safety/community lane** first slices (family plan → automod v1 → logging v1 → welcome + counters). Owner-steered alternates + the deliberately-deferred list live in that doc §4; [`roadmap.md`](roadmap.md) stays the per-area index. **Status is per-lane below — a session edits ONLY its own lane's bullet** (this paragraph used to be one shared mega-line and collided on every parallel merge; convention: [`owner/ai-project-workflow.md`](owner/ai-project-workflow.md) §9 "Cross-cutting ledger discipline").
>
> - **Consolidated batches:** **Batches 1–8 ALL executed + verified merged 2026-06-10** ([EOD verification](audits/past-day-verification-2026-06-10.md)) — #650 truth/clarity · #651 surface-classification invariant · #652 service boundaries · #654 Settings Phase 2 core · #656 adaptive P1C subpanels · **#657 Help projection seam** (HLP-2: `services/help_catalogue.py` + `services/help_projection.py`, all five render paths on one reason-coded `HelpProjection`; Q-0074 executed in the same PR) · **#659 HLP-3 guild overlay** (migration 064 `help_overlay`, audited `help_overlay_mutation` seam, cached read model, hide/rename through every render path; Q-0055 display-only pinned by an admission import fence) · **Batch 7 via the mining stack** (#661 + #663/#664/#665 → #667) · **Batch 8 = the #649 cutover**. **The queue-remainder session (PR #671, merged 2026-06-10) executed the RS07 chain-service slice** (audited `services/chain_service.py`, Batch 3 pattern, repo-wide write fence) **+ Batch 9's RS08 slice** (diagnostic read models out of the cog layer; new no-raw-SQL-in-cogs/views invariant) **+ the EOD audit's Tier-2 Help-Preview fix** (now consumes `project_help_with_execution`); **its continuation (PR #672) completed Batch 4** (proof-channel binding/resource declaration + binding-first read; logging rows verified satisfied) **and executed the Batch 10 selections** (wizard PR1–PR3 tranche verified shipped via #435 → setup-lane next = PR4 `/myprofile` planning session; next AI §7 family = **§7.5 multi-entity comparison**, sequenced after the maintainer's prod check — banners in the two plans carry the evidence). **The Help overlay editor UI executed 2026-06-10 ([plan](planning/help-overlay-editor-ui-plan-2026-06-10.md) → PR A #677 + PR B #679, both MERGED same day):** the hide/rename/re-describe editor (staff-hub `✏️ Help editor` button + the Settings-hub "Help appearance" domain group, 13th group) and the Q-0059 Home-message embed builder (migration 067, **mandatory preview**, shared `home_embed_frame` composer, byte-identical default pinned) — both live-verified on real Postgres. **Batch 9 then executed in PR #681** (open at write time): the RS05 publish-accepted delivery contract (runtime_contracts §2) + bus delivery stats / failure metric / the `event_bus` diagnostics provider, and the RS10 economy view family onto BaseView (conformance ratchet 17→13, arch warnings 84→80). **The consolidated plan's queue is FULLY EXECUTED (Batches 1–10; #681 MERGED).** A follow-on slice (PR #682, open at write time) migrated the **mining family** onto BaseView — the last true lifecycle-duplication family; ratchet 13→11 with a disposition note (remaining direct-View entries are ephemeral pipeline-gated follow-ups / bespoke admin checks, not RS10 duplication). **The PR4 `/myprofile` planning session ran (PR #684, open at write time):** [`planning/myprofile-foundation-plan-2026-06-10.md`](planning/myprofile-foundation-plan-2026-06-10.md) — §6 backend re-verified exact (4 audited pipeline entrypoints, typed accessors, schema registry, zero UI callers); PR A = read-only profile card (zero writes, turn-key) · PR B = the pipeline's first UI consumer · PR C onboarding **gated** on an owner decision; Q-0080 stranger-grade envelope applied throughout. Remaining plan-first/gated: Help audit Phase 4 records (Q-0057 rider) · AI §7.5 (post-eval).
> - **BTD6 data + answerability:** the `--all` cutover **#649 merged 2026-06-10; post-cutover VERIFIED + every carry-forward DECODED the same day** (#653 wave 1 ∥ PR #655 — dump fidelity byte-identical · 2,022 menu embeds in-limits · AI battery green · `_CUTOVER_CARRYFORWARD` empty, audit 91 CLEAN / 0 DELTA / 0 SUSPECT · banana economy answerable · fixes for mode-rules dark data / `!btd6 diagnostics` 400 / stamp-rot / path leak); **answerability items 5+6d shipped in PR #658**; **the Navarch "no coins" live miss diagnosed (missing ROUTING, not data) + fixed end-to-end with items 6a–c — #662 MERGED 2026-06-10** (paragon grounding gains income + effect lines · article-tolerant/shorthand paragon names · minion-name → owner grounding ("Mini Sun Avatar"/"Crushing Sentry"/UAV) · Pouākai diacritic-fold · honest dataset source labels/summary); follow-up slice **#666** adds `scripts/btd6_probe.py` (grounding triage) + structures item 7 into [`planning/btd6-conversation-grounding-plan-2026-06-10.md`](planning/btd6-conversation-grounding-plan-2026-06-10.md); **item 7 slice 1 (conversation carryover) + the zero-fact sweep fixes (ranking rosters · bare distinctive shorthand) shipped same day in #668**. **The 2026-06-11 morning screenshots (3 live AI-knowledge misses) fixed end-to-end in PR #703** — BUG-0002 (elite boss HP: dataset had no elite figures + boss names never routed BTD6 → standard table served as "Elite"; elite_tiers backfilled from the pinned v55.1 dump for all 7 bosses, boss canonicals route + name-index, variant-labeled grounding) · BUG-0003 ("despos on impop" hallucinated as PMFC; impop/despo keywords, Desperado alias, resolver plural fold, the `<quantity> <crosspath> <tower>` pricing leg — "10 041 despos" = ten 0-4-1s, owner-corrected) · BUG-0001 recurrence (round-cash refusals in #general: the workflow was profile-gated OFF on default channels — compatible_default/balanced_helper now declare analyze_execute_verify (Q-0048), matcher gained the money-question gate + by-round anchors). **Owner action: run `!btd6ops seed-data` after the deploy** (bosses/towers json are blob-lane data; owner-confirmed done 2026-06-11 ~12:38 — despos answers correct in prod). **The live re-test round shipped in PR #706 (merged 2026-06-11):** BUG-0004 (r-shorthand rounds + "end of r53" start shift — the $71,315.20 cumulative mislabel; truth $56,318.70) + the bulleted capabilities list (owner format ask; boss_health/crosspath/projection rows advertised). **Next:** decode-status ⭐ item 3 (buff/zone tail, demand-driven) + item 4 (maintainer live spot-check).
> - **Gated:** the Q-0036 denial-copy wiring stays gated on the maintainer's markup of the #632 table.
>
> *(The 8-lane scoreboard completed 2026-06-09/10 — record: [`planning/multi-lane-execution-plan-2026-06-09.md`](planning/multi-lane-execution-plan-2026-06-09.md), now `historical`.)*
>
> 1. **Mining character platform** — **the 2026-06-10 finalization session executed Batch 7 + the Wave-2 seed in one 4-PR stack — all four merged 2026-06-10:** **#661** (RS01 — atomic shop-purchase workflow + the Q-0071 transaction plumbing) → **#663** (RS02 stage 1 — pure domain relocated to `utils/mining/`, `services/mining_workflow.py` owns the workshop ops, views→cogs allowlist entries deleted) → **#664** (RS02 stage 2 — *every* mining write behind the workflow service, one transaction per op; AST ratchet; recipes.json reconciled to the catalog under a new alignment lint — **Batch 7 COMPLETE**) → **#665** (shared **game-XP** service + leaderboards + depth records (migrations 065/066) · **deeper ladders** incl. the diamond lantern that makes MAGMA reachable (it never was) · Gear panel + Recipe browser + fuzzy names + `!fastmine` · **duels gear wear — Q-0054 CLOSED** · PIL inventory + stat cards). Session decisions: **Q-0075** (curated economy + deeper ladders) + **Q-0076** (both PIL cards) — router §32. *(Merge mechanics note: the stacked bases didn't auto-retarget, so #663/#664/#665 merged into their parent branches — the content reached `main` via the same-day completion PR **#667**, content-verified EOD; migrations renumbered 065/066 around #659's 064.)* Earlier Wave-1 chain: #606–#610, #624. **The V-16 phase-1 gear slice shipped 2026-06-11 (PR #702, full Q-0092 scope):** 9-slot set-piece model (+ migration 068 legacy fold) · same-tier set bonus with set-aware Equip Best + "breaks set" picker warnings · bronze/silver ores · sim-pinned numbers ([record](planning/gear-set-numbers-2026-06-11.md)) · picker stat previews · the paper-doll compositor (placeholder sprites; owner pack drops into `disbot/assets/gear/`). **Next slice: V-16 phase 2** (owner's PNG pack + anchor tuning) **or structures §7.5 (Forge/Vault/Home)**, then the §7.4 skill tree (its `game_xp` substrate now exists). Route in: `docs/ideas/mining_exploration_brainstorm.md` §7.7 + the games folio.
> 2. **Adaptive Setup/Access platform** — Phase 0 complete; Phase 1 underway: Q-0026 identity repair + Phase 0 contracts **#588**, P1A Access Map projection **#589**, P0C groundwork **#591**, P0C seam conversion + P1B `routing_access_conflict` **#592**; **P1B remainder shipped in #632 (2026-06-09, execution-plan Lane 2 — verify merged on live GitHub):** the Q-0045 governance tier-input path (`GovernanceContext.member_tier`, declared tier preferred verbatim, simulation-labeled per §16.4) + the `help_advertises_locked` drift provider + the full Q-0036 denial-copy **draft** (in the PR body for maintainer read-through — **not live-wired**; wiring follows his markup). **P1C merged 2026-06-10 (consolidated plan Batch 5, #656):** Access Map + Help Preview shipped as **staff-hub subpanels, no new command names** (Q-0032), on the tier path as-is. **The Batch 6 Help projection seam consumed this lane 2026-06-10 (#657, merged):** Help's five render paths now compose governance + the projection contract end-to-end (`services/help_projection.py`, incl. an execution-enriched mode over `access_projection`). **Next: P2** Feature Profile preview (own planning first). Q-0028–Q-0031 + Q-0033 are also **answered** (catalogue committed · availability owns quiet mode · snapshots compound+high-risk · risk policy approved · account links deferred — router §20). Route in: plan §16.8.
> 3. **AI tooling (orchestration + answerability)** — orchestration Phases 1–3 shipped (**#612**, **#618**, **#619** — including the gate-lifted `ai:tools` Tools & Workflows operator UI; default byte-identical); answerability Phase 1A/1B (**#612**, Q-0043: range cash **inclusive**) + Phase 2 read model (**#616**) shipped. **Orchestration Phase 4 MVP (Q-0046) built 2026-06-09 in PR #634** (execution-plan Lane 3, parallel session): the round-cash plan→execute→verify workflow + the one typed answer-with-evidence contract, profile-gated, default byte-identical — **model loop awaits the maintainer's production check** (no sandbox provider key). **Answerability Phase 3 shipped 2026-06-09 in PR #639** (execution-plan Lane 4, **Q-0047**): the three read-only self-awareness tools — `get_ai_tool_catalog` ("what can you do here?") · `get_ai_policy_explanation` ("why didn't you reply?") · `btd6_answerability` ("what BTD6 data do you know?") — audience-tiered **at construction** over the #616 read model; **model loop awaits the maintainer's prod check** (no sandbox key). **Next:** the remaining orchestration §7 workflow families; answerability Phases 4/5 stay gated (settings UI per-exposure ask · dashboard schema acceptance). Standing posture **Q-0048**: read-only deterministic tools ship without a per-case ask; writes/external/UI stay per-exposure. Plans: [`ai/ai-complex-request-tool-orchestration-plan.md`](ai/ai-complex-request-tool-orchestration-plan.md) · [`planning/ai-btd6-answerability-roadmap-2026-06-09.md`](planning/ai-btd6-answerability-roadmap-2026-06-09.md). **The first Q-0086 joint live session ran 2026-06-11 (PR #707): the model-loop gate is LIFTED** (keys in agent sessions; full loop verified on both providers); BUG-0005…0008 fixed live (tool quantity laundering · carryover routing/forcing · conversation-meta floor copy + guard haystack · farm/possessive/double-cash routing); **BUG-0009** (claim assembly) OPEN in the [bug book](health/bug-book.md); **BUG-0010 (ABR qualifier) FIXED same day in the follow-up slice (PR #709** — shared ABR cue → grounding round legs + the round-cash workflow compute/label the ABR set, modifier honesty deterministic**)**; **Q-0094** (memory floor canon) + **Q-0095** (Haiku-4.5 allocation for the two NL tasks · the guild-default-provider trap · sandbox floor-testing posture) recorded; the owner-requested **AI panel rework** captured ([idea](ideas/ai-panel-inplace-navigation-2026-06-11.md)). Gear/mining (#702) is still never owner-played — the eval-checklist Tier 2+ walk stays queued.
>
> Cross-cutting: **Community Spotlight** (side-lane **#613**/**#614** + hotfixes **#615**/**#617**) was hardened in the review session (canonical `utils/db/xp.py` read, `member_count` crash fix, first tests) and **Q-0044 is executed**: the Q-0025 `scripts/new_subsystem.py` scaffold was built and used to register Spotlight as a `community`-hub child (**#626**, 2026-06-09 — execution-plan Lane 1; merged, verified live), and the `!hub`/`!server` aliases were **dropped same day** (kept `!spotlight`/`!activity`). Also decided: BTD6 data-refresh automation = **manual-dispatch workflow** (Q-0049 — **built same day in #633**, execution-plan Lane 5: `workflow_dispatch`-only, opens a reviewable PR, never pushes to main); mining descent lights **permanent, owner-confirmed** (Q-0050); the five product-vision questions (Q-0038–Q-0042) got their **draft-answer session** (Q-0051) **and the maintainer marked all five up same day (Lane 6, PR #631, structured choices)**: Q-0038 server-scoped clans, Q-0039 cosmetic-only donations (no bot-side billing), Q-0041 YouTube-first/dual-opt-in/voice-deferred, Q-0042 staged-Someday website — all approved as drafted; **Q-0040 adjusted: the AI dungeon master picks quests/rewards/difficulty from bounded, hard-capped menus** (not pure narration, not free-form authority). Posture decisions only — every lane still needs its own plan/promotion + the AI per-exposure lift; conclusions routed to the four roadmap drafts + router §21. Full repo review: [`audits/repo-review-2026-06-09.md`](audits/repo-review-2026-06-09.md) · agent-memory system review (did the orientation/memory system work in practice?): [`audits/agent-memory-system-review-2026-06-09.md`](audits/agent-memory-system-review-2026-06-09.md).
>
> **Last updated:** 2026-06-12 (evening), **the first Q-0107 reconciliation pass (PR #741)** — every #715–#740 plan mapped, the decade queue set ([pass record](planning/reconciliation-pass-2026-06-12.md)), ledger + roadmap drift fixed; stamp-line history older than 2026-06-11 moved to [`current-state-archive.md`](current-state-archive.md) § Stamp-line history. · 2026-06-11 (afternoon), **first Q-0086 joint live-testing session (PR #707)** — model-loop gate lifted, BUG-0005…0008 fixed live, BUG-0009/0010 opened, Q-0094/Q-0095 recorded — see the AI lane bullet. · 2026-06-11, **AI-knowledge bug session (PRs #703 + #706 + process record #705): the morning's 3 live misses + the re-test round's BUG-0004 + the capabilities format fixed** — see the BTD6 lane bullet above. · Earlier same day: **gear-lane session (PR #702): V-16 phase 1 executed** — see the mining lane bullet above; this stamp line otherwise preserves the 2026-06-10 marathon record below.

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
>
> **Last reconciliation pass:** PR #741 (2026-06-12 —
> [the pass record + decade queue](planning/reconciliation-pass-2026-06-12.md)). The next
> **docs-only review + planning reconciliation** is due once merged PRs cross #750 (every
> multiple of 10 — Q-0107; `scripts/check_reconciliation_due.py` flags it). Reset this
> marker to the latest PR after a pass.

- **#745 (2026-06-12, the direction-lock round)** — owner question-panel round: **next
  implementation session = P0-1 wager money-safety** (design pinned:
  [games-wager-money-safety-plan](planning/games-wager-money-safety-plan-2026-06-12.md)) ·
  **Q-0097 = operator-managed findings lifecycle** (every hardening gate now answered) ·
  **Q-0082 interim global AI ceiling = €30/month** · **Q-0115**: Stage 0 folded into the
  #742 Routine bridge (one continuation-dispatch seam; bounded protocol activates on
  wired + calibrated). (#743/#744 same day: the loop session's close + a journal
  draft-first wording fix.)
- **#742 (2026-06-12, the autonomous-loop seams — parallel Hermes session)** — Hermes
  `superbot-review` skill (independent non-Claude plan/PR critique with a maintainer
  summary) · `scripts/check_phase_gate.py` (machine-readable **fix-phase vs. invent-phase**;
  invent requires zero OPEN bugs + zero Not-Done readiness rows — reports FIX-PHASE today) ·
  the `superbot-dispatch` skill + runbook (Hermes → Claude Code Routine `/fire`). Owner
  decisions **Q-0113** (routine PRs self-merge on green CI) + **Q-0114** (human approve/deny
  for agent-originated features; invent-phase-only origination) — workflow §12. Maintainer
  follow-ups: wire the Routine + token, calibrate per Q-0105 before trusting unattended.
- **#741 (2026-06-12, the first Q-0107 reconciliation pass)** — every plan added in
  #715–#740 mapped ([pass record + decade queue](planning/reconciliation-pass-2026-06-12.md)):
  new roadmap lanes **safety/community** (Q-0108–Q-0112) + **agent ecosystem/workflow**;
  the next ~9 PRs planned (hardening P0s · backup posture · the safety lane's first
  slices); ledger drift reconciled; the cadence checker taught to fetch `origin/main`.
- **#738–#740 (2026-06-12, the cadence rule + owner research/decisions arc)** — **#738**: the
  **Q-0107 reconciliation cadence** (a docs-only review + planning pass each time merged PRs
  cross a multiple of 10; `scripts/check_reconciliation_due.py` guards the marker). **#739**:
  owner research captured — [safety/automod ideas](ideas/server-safety-and-automod-2026-06-12.md) ·
  [community-features ideas](ideas/community-platform-features-2026-06-12.md) · the
  [Discord platform-limits reference](operations/discord-platform-limits.md). **#740**: owner
  decisions **Q-0108–Q-0112** recorded (automod all-4 rule types + OpenAI-only image
  moderation · logging v1 scope with owner-configurable channels · welcome embed-first, PIL
  cards phase 2 · security tiers 1+2 only, 3+4 declined · NL event parsing from day one) →
  routed to the roadmap's new **safety/community lane**.
- **#732 (2026-06-12, command-surface dump tool)** — `scripts/command_surface_dump.py`:
  offline AST dump of every prefix/slash command by subsystem (+ `--json` and
  `--diff-checklist` against the untested-surface checklist); 8 tests. The #731 session's
  grooming companion; roadmap queue item 1 closed with it.
- **#737 (2026-06-12, Context7 MCP adopted)** — wired `@upstash/context7-mcp@3.2.0` (live
  library docs → kills the "API-from-memory" bug class) as a pinned `.mcp.json` server +
  [`docs/operations/mcp-servers.md`](operations/mcp-servers.md) (when-to-use, key setup, Q-0105
  provenance). Q-0096 answered (Context7 yes; Postgres-MCP/pyright-lsp still open).
- **#736 (2026-06-12, CodeGraph health check + doc pin fix)** — verified CodeGraph 3.11.2 is
  healthy (no regression from the bump; the "problems" are the cold-start availability blip + the
  documented false positives). Fixed the real bug: `docs/codegraph-usage.md` told agents to run the
  old `@optave/codegraph@3.10.0` while the live pin is 3.11.2 — bumped all command refs.
- **#733–#735 (2026-06-12, the agent-workflow/memory hardening arc)** — **#733**: **Q-0102**
  (mandatory `⟲ Previous-session review` session-ender) + **Q-0103** (open session PRs **ready not
  draft**; every PR reaches a terminal state). `scripts/check_session_log.py` + post-edit/Stop-hook
  wiring enforce the Q-0089/Q-0102 enders. New
  [`docs/operations/claude-code-hooks-and-plugins.md`](operations/claude-code-hooks-and-plugins.md)
  (the 6 wired hooks + brainstorm + plugins posture → Q-0096). `.claude/settings.json`
  permission-friction cut (`acceptEdits` + curated allowlist; force-push/destructive still prompt).
  **#734**: reconciled this ledger's drift (added #730/#733, relabeled #731, added #724–#728) and
  built `scripts/check_current_state_ledger.py` (the living-ledger self-check) + **Q-0104** (closing
  documentation audit) + **Q-0105** (adopt-tooling-with-a-delete-if-unreliable kill-switch) +
  permissions-posture doc. **#735**: **Q-0106** — agents propose `CLAUDE.md` rule changes via a
  router Q-block, never self-edit (binding for a session but not pinned; read-only to a fully
  autonomous agent). Captured ideas: autonomous self-improvement loop · Hermes→Claude Routines
  dispatch bridge · portable OSS memory/workflow package · ledger session-arc aggregation.
- **#730 (2026-06-12, Hermes skills installable)** — `scripts/hermes/build_skills.py` generates
  installable `SKILL.md` files (Hermes frontmatter) from the skill docs + `install-skills.sh`
  deploys them to the VPS; `repo-health` self-schedules a daily Telegram digest via a frontmatter
  `blueprint.schedule`. New `log-triage` skill (read-only prod/gateway log diagnosis) +
  [`hermes-operating-prompt.md`](operations/hermes-operating-prompt.md) (the Hermes-side `CLAUDE.md`).
  `tests/unit/scripts/test_build_skills.py` freshness-gates the generated artifacts.
- **#731 (2026-06-12, untested-surface checklist)** — the owner-commissioned
  [`docs/audits/untested-surface-checklist.md`](audits/untested-surface-checklist.md):
  18 sections, 70+ `[ ]` items covering every command/UI surface that automated CI
  cannot verify and has no live-walk record — Economy · General · Utility · Roles ·
  XP · Moderation · Channel/Word-filter · Counting · Admin · Diagnostic · Logging ·
  BTD6 ref/strat/paragon · Deathmatch · Community/Games/420 · Server-mgmt subpanels ·
  Bootstrap access · Regression sweep. Persistent successor to the 2026-06-10 eval
  checklist. Linked from hardening roadmap.
- **#729 (2026-06-12, 429 login crash-loop fix)** — `_maybe_backoff_on_rate_limit()`:
  when `bot.start()` returns HTTP 429 (Discord/Cloudflare 1015 rate limit), the
  process now sleeps 60 s before exiting so Railway's on-failure restart fires after
  the backoff has elapsed rather than immediately. Breaks the rapid crash loop that
  deepened the ban (live incident 2026-06-12 — 4 restarts in ~2 min). Non-429
  crashes unaffected; 5 targeted tests added.
- **#724–#728 (2026-06-12, the readiness/roadmap/tooling arc)** — **#724** indexed + reconciled
  the seven production-readiness maps; **#725** the consolidated hardening roadmap + the
  `repo-manageability` ideas + routed Q-0098–Q-0100; **#726** the four manageability tools
  (`review_scope.py` + readiness scoreboard + doc-freshness guard + the `current-state.md`
  trim/auto-archive ratchet); **#727** closed that arc's session; **#728** recorded owner
  decisions Q-0098–Q-0101 (all the recommended option). Docs/tooling.
- **#715–#723 (2026-06-12, the review-map + readiness-map set)** — **#715** founded `docs/repo-review-map.md` (the review/refactor partition: Axis A repo domains · Axis B subsystem-slice vs. shared-platform review units); **#716** closed that session. Then **seven per-subsystem production-readiness maps** (#717 AI · #718 health/diagnostics + Q-0097 · #719 server-management · #720 settings/bindings/provisioning · #721 BTD6 · #722 games · #723 media/YouTube) landed under [`planning/production-readiness/`](planning/production-readiness/README.md) — each a source-verified Done/Partial/Not-Done inventory of one slice, linked from its folio. A reconciliation pass added the directory README index, normalized two badges to `audit`, and linked the set from the review map. Docs-only; recurring cross-map themes = settings pointer-lane debt · server-management channel-ownership convergence · AI projection dual-store · BTD6 runtime/data split.
- **Older merges (#706 … #535) → [`current-state-archive.md`](current-state-archive.md).** Recently-shipped keeps the ~15 newest; older entries are archived (`scripts/check_docs.py` soft-ratchets the count).

> Older than this: see `docs/planning/*` trackers and `docs/decisions/*` ADRs.

## Next candidates

- **Cross-area sequencing + the plan index now live in [`docs/roadmap.md`](roadmap.md)**
  (by area, with Now / Next / Later / Someday horizons + gates — where to find which plan
  for which part of the code). The picks below are the current top of that list.
- Server-management is **structurally complete** *(bullet corrected 2026-06-10 — it
  still queued PR14 long after the hub merged)*: **PR10 complete** (six slices,
  ADR-008), **PR11** (#570; governance section **deferred** — revisit only with a
  scope decision), **PR12** (2026-06-07), **PR13's deterministic slice** (2026-06-08,
  incl. the migration-059 staging fix), and **PR14 — the unified Server Management
  Hub — shipped 2026-06-08 via #584**. The only remainder is the **gated PR13 AI
  generation layer**. The `docs/planning/server-management-status-2026-06-05.md`
  tracker is the authoritative queue — don't duplicate it here.
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

- **AI / BTD6 feature expansion — re-postured 2026-06-09 (Q-0048):** AI tools that are
  **read-only AND deterministic** (no writes, no external calls, audience-tiered) carry a
  **standing lift** and may ship without a per-case ask. Anything that **writes, costs
  money, calls external services, or adds UI** still needs the per-exposure lift, and broad
  expansion stays gated on *all* of: bot-wide stability **+** provider/provenance checks
  **+** caching / source-health clarity **+** AI behavior/config correctness.
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

*(The Q-0025 `new_subsystem.py` scaffold that used to sit here is reconciled: built
and used to register Community Spotlight in **#626** (execution-plan Lane 1,
2026-06-09 — verify merged on live GitHub).)*

*(The Q-0026 `cog_name_to_subsystem` fix that used to sit here is reconciled: merged
in **#588**, listed under Recently shipped.)*

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

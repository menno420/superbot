# C2 — capability & invocation truth (non-game surface)

## §5 common Codex preamble

You are a GPT Codex session on menno420/superbot, Arm B (session C2) of a four-arm GATE V verification
fleet. Do a READ-ONLY, source-first verification pass over your assigned scope only. Use Plan mode for
initial investigation and Extra High reasoning if available. You are the fleet's empirical source/test
spine: prove or disprove dated planning claims against live source at current HEAD — do NOT produce a
broad architecture brainstorm (that is Arm A's job; defer to it and add only source deltas).

## §3 shared fleet contracts

**3.1 Readiness classification enum (pinned — use exactly these, no synonyms):**
`READY_FOR_TEST_DESIGN` · `NEEDS_CONTRACT_FREEZE` · `NEEDS_OWNER_DECISION` ·
`NEEDS_SOURCE_RECONCILIATION` · `NEEDS_ORACLE` · `NEEDS_EXTERNAL_VALIDATION` · `BLOCKED_BY_GATE` ·
`DEFERRED`.

**3.2 Evidence labels (pinned):** `CONFIRMED` · `INFERRED` · `STALE` · `CONTRADICTED` · `UNVERIFIED`.
For Arm B additionally tag the *method*: `source-read` vs `test-confirmed`.

**3.3 Claim-anchor scheme:** every contradiction/discrepancy-ledger row is keyed on the exact
canonical artifact + location: `path/to/artifact.md:Lnn` (or `:§x.y`).

**3.4 CodeGraph / import-graph caveats:** graph tools do not prove dead/zero-caller status; command,
event, registry, prefix-dispatch, and callback edges need source grep/registry/source reads.

**3.5 CI-parity & runtime-evidence caveats:** checkers must go through `python3.10`; if a suite cannot
run, mark evidence `source-read`; source beats false-green checks.

**3.6 Degrade-gracefully priority ladder:** primary deliverables plus contradiction ledger at full depth
first; mark lower-priority sections partial rather than thinning the core.

**3.7 Read-only (Arms A/B/C):** no source/plan/current-state edits, no GitHub mutation, no Phase-3
approval, no new-repo code. Writing this single output report is the only permitted write.

**3.8 Exact canonical paths:** `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md`
and `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md`; per-sector
ledgers: `docs/current-state/S1-bot.md`, `S2-btd6.md`, `S3-ai-memory.md`, `S4-docs.md`, `S5-ops.md`.

**3.9 Shared startup route:** `.claude/CLAUDE.md` → `docs/collaboration-model.md` → `docs/current-state.md`
→ per-sector `S*.md` ledgers → `docs/AGENT_ORIENTATION.md` → owner workflow docs → rebuild planning docs
+ architecture contracts + verification infra. Do not trust dated snapshots without live verification.

## Scope and preflight

- Session: C2, Arm B.
- Scope executed: capability & invocation truth for non-game L1a/L1b/L1c/L2/L4/L5 only.
- Explicitly excluded: L3 product review and game-surface evaluation. Game rows only appear when needed as exclusions from counts or cross-link caveats.
- Local checkout: branch `work`; HEAD `cf5a234 Merge pull request #1749 from menno420/bot/dashboard-refresh`.
- Live GitHub remote was unavailable in this checkout (`git remote -v` showed no remotes; `git fetch origin ...` failed), so evidence distinguishes local HEAD from the PR-1750 launch-pad prompt fetched by raw GitHub URL.

## Commands / searches performed

- `git status --short --branch`
- `git log --oneline -10`
- `curl -fsSL https://raw.githubusercontent.com/menno420/superbot/claude/chatgpt-prompt-review-kzvr4v/docs/planning/rebuild-gate-v-verification-fleet-2026-07-06.md -o /tmp/gatev.md`
- `rg --files docs/planning | rg 'rebuild-gate-v|C2-capability|verification-fleet'`
- `rg -n "L1a|L1b|L1c|L2|L4|L5|ADD|command|slash|prefix|capability" ...`
- `PYENV_VERSION=3.10.20 python3.10 scripts/scan_commands.py --summary`
- `PYENV_VERSION=3.10.20 python3.10 scripts/scan_commands.py > /tmp/commands.txt`
- Python aggregation over `/tmp/commands.txt` for the non-game capability set.

## Confirmed facts

### Command scanner and invocation model

- `scripts/scan_commands.py` is AST-only and intentionally avoids importing `disbot`, so its counts are source-read evidence rather than runtime-registration evidence. It classifies decorators into prefix/slash/both and detects button-backed commands from panel classifications or view-opening tokens.
- At local HEAD, the scanner reported: 55 cogs, 58 command classes, 484 command records, 243 top-level prefix commands, 209 subcommands, 32 slash roots, 78 slash command records, 406 prefix command records, and 134 button-backed command records.
- This means the plan's non-game slash-mirroring work remains real: the live bot is still overwhelmingly prefix-first outside selected slash front doors.

### Non-game capability rows from the capstone plan vs source surface

The capstone build plan's non-game rows are source-real as categories, but the live invocation surface is uneven and sometimes newer than the prose map.

| Layer | Plan capabilities in C2 scope | Source/invocation evidence | Evidence label | Readiness |
|---|---|---:|---|---|
| L1a | `settings`, `diagnostic`, `help` | `settings`: 3 records (2 prefix, 1 slash); `diagnostic`: 13 records (12 prefix, 1 slash); `help`: 2 records (1 prefix, 1 slash). | CONFIRMED/source-read | NEEDS_SOURCE_RECONCILIATION |
| L1b | `admin`, `server_management`, `moderation`, `logging`, `automod`, `image_moderation`, `security`, `cleanup`, `welcome`, `counters`, `channel`, `role`, `ticket`, `proof_channel` | Present in cogs/registry; scanner shows many prefix-only operator domains (`channel` 17 prefix, `role` 15 prefix, `ticket` 12 prefix, `logging` 6 prefix, `proof_channel` 5 prefix). | CONFIRMED/source-read | NEEDS_CONTRACT_FREEZE |
| L1c | `ux_lab`, visual card engine ADD | `ux_lab`: 2 records (1 prefix, 1 slash). I found no runtime subsystem/cog for a generic visual-card engine in C2 source scan; it remains ADD/design work. | CONFIRMED/source-read for `ux_lab`; UNVERIFIED/source-read for ADD runtime | NEEDS_CONTRACT_FREEZE |
| L2 | `economy`, `inventory`, `treasury`, `xp`, `karma`, `community`, `community_spotlight`, `leaderboard`, profile surface ADD | Existing rows are source-real; examples: `economy` 8 records (7 prefix, 1 slash), `karma` 4 (3 prefix, 1 slash), `community` 2 (1 prefix, 1 slash), `xp` 6 prefix. `myprofile` exists as Utility slash/prefix records rather than a full profile-surface subsystem in the plan sense. | CONFIRMED/source-read plus NEEDS_SOURCE_RECONCILIATION for profile ADD | NEEDS_SOURCE_RECONCILIATION |
| L4 | `ai`, `btd6`, `project_moon`, shared ingestion ADD, `utility`, `general` | `ai`: 23 records (11 slash, 12 prefix); BTD6 split/unified source totals 112 records (39 slash, 73 prefix) across scanner rows; `project_moon`: 11 (10 prefix, 1 slash); `utility`: 15 (13 prefix, 2 slash); `general`: 8 prefix. No generic shared-ingestion command subsystem found in C2 command scan. | CONFIRMED/source-read | NEEDS_SOURCE_RECONCILIATION |
| L5 | web dashboard/live editor, boards ADD, migration assistant ADD | `botsite/` and dashboard templates exist, but no Discord command surface equivalent to boards or migration assistant surfaced in the C2 command scan. | CONFIRMED/source-read for existing web app; UNVERIFIED/source-read for ADD command surface | NEEDS_CONTRACT_FREEZE |

### Subsystem registration and routing truth

- `disbot/utils/subsystem_registry.py` is the declared subsystem manifest and says it is the single source of truth for subsystem definitions, with capability namespace constraints and immutable post-validation semantics.
- The registry distinguishes subsystem keys from command identifiers; e.g. `server_management` is the key, while `servermanagement` is the command entry point.
- `server_management` is registered as a routing-only hub with no own capabilities; treating it as a normal capability owner would overstate the source surface.
- The help surface map states loaded extensions, subsystems, and Help categories are different concepts; no-row cogs such as setup, quicksetup, Hermes, media/health maintenance, role grants, and starboard may still expose commands or tasks.
- The help map's prose is partly stale against current source: it says broader slash rollout for `/platform`, `/settings`, etc. follows later, but the scanner now sees slash records for `settings`, `diagnostic/platform`, `server-management`, `admin`, `moderation`, and others.

### Hidden / generated / dynamic surfaces

- The AST scanner explicitly includes inherited mixin commands, module-level bot/tree commands, app-command groups, nested groups, and button-backed detection; this reduces the risk of missing generated or split command surfaces.
- Dynamic Help and hub navigation are not equivalent to command registration. Button-backed commands exist (134 scanner records), and Help may reach panels even where direct slash parity is absent.
- Several no-row cogs remain intentionally outside `SUBSYSTEMS`; C2 should not classify them as missing solely because they lack registry rows.

## §3.3 discrepancy ledger

| Claim anchor | Plan claim | Source evidence | Test evidence | Status | Severity | Required final-session action |
|---|---|---|---|---|---|---|
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:L68` | `channel` should replace 17 prefix verbs with a small slash set. | Scanner confirms `channel` currently has 17 prefix command records and 0 slash records. | Not run beyond AST scanner. | CONFIRMED/source-read | High | Preserve as a real L1b rebuild requirement; do not mark channel slash work done. |
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:L69` | `role` needs slash mirrors. | Scanner confirms `role` has 15 prefix command records and 0 slash records. | Not run beyond AST scanner. | CONFIRMED/source-read | High | Keep `role` slash parity as open L1b work. |
| `docs/help-command-surface-map.md:L295` | Broader slash rollout (`/platform`, `/settings`, etc.) follows in subsequent PRs. | Scanner now sees slash records in several of those domains, including settings and diagnostic/platform. | Not run beyond AST scanner. | STALE/source-read | Medium | Update final synthesis to treat help-map slash rollout prose as stale and prefer live scanner/source. |
| `docs/help-command-surface-map.md:L121` | `platform` opens via a legacy `HUB_PANEL_BUILDERS["diagnostic"]` override and is top-level. | Earlier same doc says `HUB_PANEL_BUILDERS` is now empty and platform is reached via Server & Admin; scanner sees diagnostic slash/prefix records but routing prose conflicts internally. | Not run beyond source read. | CONTRADICTED/source-read | Medium | Reconcile help-map §2 table against the newer routing-summary prose before using it as evidence. |
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:L82` | Profile surface is ADD-from-plans and unbuilt. | Scanner sees `myprofile` utility records in parity/goldens and Utility command surface; source suggests a partial/current profile entry exists, not a full profile subsystem/card. | Not runtime-tested. | NEEDS_SOURCE_RECONCILIATION/source-read | Medium | Split “current myprofile command exists” from “new profile surface/card ADD still needed.” |
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:L103` | Current web app is FastAPI and L5 should become generated web projection. | `botsite/` exists and generated dashboard data was refreshed in recent commits; C2 did not inspect web runtime deeply. | Not tested. | CONFIRMED/source-read (partial) | Low | Assign deeper L5 implementation/runtime validation to a web/dashboard scope if needed. |
| `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md:L110` | Ecosystem contributes one genuine build and otherwise folds into existing surface. | C2 command scan supports that most non-game surfaces already exist; no extra giveaway/voice-style non-game command gap was found in C2 scope. | Not tested. | CONFIRMED/source-read | Low | Do not expand C2 into ecosystem re-review; cite source scan only. |

## Contradicted or stale claims

1. The help-map table still contains older routing text for `diagnostic/platform` that conflicts with the same document's newer routing summary.
2. The help-map slash-rollout future-tense prose is stale for multiple slash front doors now present in source.
3. Any summary that equates “subsystem row” with “all loaded command/task surfaces” is false; the help-map itself warns against that and lists no-row command/task cogs.

## Unresolved assumptions

- I did not start the bot, query Discord runtime command registration, or compare against live application-command sync state. Slash findings are AST/source-truth, not live Discord-truth.
- I did not execute the unit/parity suites; the scanner is source-read evidence only.
- Command counts include game surfaces in the global total but per-layer tables filtered to C2 non-game scope. BTD6 is included because the prompt explicitly includes L4; L3 games are not product-reviewed.
- Capability labels in `SUBSYSTEMS` are not complete acceptance criteria; many rows have command surfaces but still need contract freeze for the new rebuild grammar.

## Confidence

- High confidence in AST-derived command counts at local HEAD, with the scanner's own Q-0105 caveat that it is a convenience generator.
- Medium confidence in subsystem registration/routing conclusions because dynamic help/hub paths require source reads beyond one scanner.
- Low confidence in live slash deployment state because no Discord runtime or sync check was performed.

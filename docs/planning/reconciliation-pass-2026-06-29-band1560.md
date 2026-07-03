# Twenty-ninth Q-0107 reconciliation pass — band-#1560

> **Status:** `historical` — the docs-only reconciliation + planning pass for the band crossing #1560.
> Trigger: `reconcile` issue **#1563** (auto-opened by `reconciliation-trigger.yml`, author `menno420`).
> Reset target: marker #1530 → **#1560**.
>
> **Band archetype:** `mixed` (owner-directed S1 feature-completion certification + autonomous S1 game
> depth + a **PROD boot-crash hotfix** + a Project Moon content layer + best-in-class operator commands).
> No named §4 forward-queue lane was executed this band — the fourth consecutive `mixed` zero-queue band.

---

## 1. Verified state at this pass (against git log + live GitHub)

Merged since the marker #1530: **#1532–#1561** (#1531 = the prior band's trigger issue, #1532 = the
band-#1530 pass's own docs PR, #1563 = this pass's trigger issue). The band's headline is the
**S1 feature-completion certification arc** (Q-0209) — every S1 bot unit assessed to **100% assessed**
against the #1513 framework, which root-fixed **BUG-0029** (XP role grants bypassing the audited seam)
and drove a wave of completion-first feature deepening (leaderboard providers, Creatures game panel,
inventory sort/filter). The band's sharpest event is the **`give`-collision prod boot-crash** (#1541 →
#1544, Q-0211): a new `!give`/`!pay` command collided with a dormant-since-initial-commit mining `give`,
the STRICT identity-contract aborted startup, and the bot crash-looped offline until `give` was retired
surface-wide with a cross-cog duplicate-command boot guard.

**Open PRs at pass time (Q-0125 disposition):** **8** —
- **#1562** (`bot/dashboard-refresh`) — routine generated-data refresh; auto-merges on green. **Leave.**
- **#1555–#1560** (six `dependabot[bot]` dependency bumps: prometheus-client, asyncpg, pillow, openai,
  a python minor/patch group, a dashboard fastapi bump) — owner/dependabot-managed. **Leave.**
- **#1509** (`codex`-labeled, owner-authored "repo-grounded unfinished-work audit", one doc) — carried
  open from the band-#1530 pass; its one actionable thread (BTD6 live-miss findings) was already
  harvested by #1510, so the audit doc is a point-in-time snapshot. A deliberate owner-launched Codex
  task (no auto-merge enabler arms it). **Left for the owner** to merge or close — not closed unilaterally.

None are stale-red `claude/*` orphans; nothing to fix or close this pass.

## 2. Band scorecard (#1532–#1561)

| Theme | PRs | Source |
|---|---|---|
| **S1 feature-completion certification arc (Q-0209)** — assess every S1 unit to **100% assessed** against the #1513 framework: Mining/Creatures (◐)+Welcome (#1534), Moderation/Economy/Roles/XP **+ root-fix BUG-0029** (#1536), Settings/Leaderboards/Tickets/Karma (#1538), the final 17 server-fn units → 100% + stale-claim cleanup (#1545) | #1534 · #1536 · #1538 · #1545 | owner-directed (completion drive) — marquee |
| **PROD hotfix — `give`-collision boot crash (Q-0211)** — #1541 added `!give`/`!pay`, colliding with mining's dormant admin `give` → STRICT identity-contract aborted boot → bot offline; #1544 retired `give` surface-wide + a cross-cog duplicate-command boot guard | #1541 · #1544 | owner-directed live incident |
| **S1 game depth + workflow guards** — Creatures interactive game panel + dex browser + settle-once (#1546), session-slug-uniqueness guard + Mining how-to (#1548), registry↔ledger completion-parity guard + inventory sort/type-filter + display tests (#1553) | #1546 · #1548 · #1553 | autonomous feature depth |
| **Unified-hub leaderboard providers** — Fishing (#1540) + Farm (#1542) leaderboard providers | #1540 · #1542 | autonomous (completion-first) |
| **Operator command gaps + proof-channel audit** — `!slowmode`/`!topic` (audited seam)+`!roleinfo` (#1561), proof_channel audit prize lock/unlock + re-check `manage_channels` at callbacks (#1550/#1551) | #1561 · #1550 · #1551 | autonomous best-in-class |
| **Project Moon (Limbus)** — combat-mechanics knowledge layer (clash/speed/IDs+passives) | #1549 | autonomous content depth |
| **Docs / dashboard** — the twenty-eighth Q-0107 pass (band-#1530, #1532) + eight dashboard refreshes | #1532 · #1533/#1535/#1537/#1539/#1543/#1547/#1552/#1554 | routine |

**Queue-execution rate this band:** **0 of 17 named §4 forward-queue slices executed.** The fourth
consecutive `mixed` zero-queue band — owner-directed completion-certification + the prod hotfix +
autonomous S1 depth, none of it an A/B/C/D/E queue slice. The §4 queue is **carried forward essentially
intact** and stays well over the 30-slice cadence threshold (no THIN flag).

## 3. Reconciled / fixed + control-plane

- **Ledger:** added the band #1532–#1561 work as **seven grouped entries** (operator commands +
  proof-channel · S1 game depth + workflow guards · leaderboard providers · Project Moon combat layer ·
  the `give`-collision hotfix · the feature-completion certification arc · 28th pass + dashboard),
  trimmed Recently-shipped back to 20 via `trim_recently_shipped.py --apply` (moved the oldest 7 bullets
  #1444-band · #1449-band · #1463-band · #1443-band · #1418-band · #1417-band · #1413-band to
  [`current-state-archive.md`](../current-state-archive.md)), reset the marker **#1530 → #1560**, and
  bumped the `Last updated:` stamp + the top-of-file sector table (S4 row) + the `Last reconciliation
  pass` marker block.
- **Checkers:** `check_current_state_ledger.py --strict` ✓ · `check_docs.py --strict` ✓ ·
  `check_dashboard_data.py --drift` 0 warnings (58 cogs).
- **Dashboard:** regenerated `dashboard/data/dashboard.json` (cadence-half freshness, Q-0167).
- **Control-plane (Q-0135):** `check_loop_health.py` SKIP locally (no `gh`/token); the live read via the
  GitHub MCP — the trigger issue **#1563** authored by **`menno420`** — confirms **ROUTINE_PAT is set and
  the loop self-fires**. No control-plane drift to correct.
- **Owner decisions:** Q-0208, Q-0209, Q-0211 all verified recorded in the question router.

## 4. The next band (depth to #1590)

**Depth check: well over the 30-slice cadence threshold, so NO `⚠️ PLAN-BACKLOG-THIN` flag.** This band
executed **no §4 queue lane**, so the band-#1530 §4 queue is **carried forward intact**, refreshed below
with two band deltas: (a) the S1 feature-completion arc reached **100% assessed**, so D4 narrows to
*acting on the ◐/✗ findings* each assessment recorded rather than further assessment; (b) `give` is
retired surface-wide (Q-0211), so any peer-transfer economy feature is **off the table** unless re-scoped.

| Slice | Lane | Gate | Notes |
|---|---|---|---|
| A1 | **Project Moon — shared `KnowledgeDomain` seam extraction (Slice B)** | `plan-first` | Detector/disjointness groundwork (#1470) + the combat-mechanics layer (#1549) landed. Extract the shared seam (data/fact-store/resolver/grounding/guard) from BTD6 + Limbus, byte-identical for BTD6. [plan](project-moon-knowledge-domain-plan-2026-06-21.md) §5. |
| A2 | **Project Moon — Slice A item 1 (StaticData exact-number ingest) + a second game (LoR / LobCorp)** | `plan-first` | After the seam: exact-number facts + the next domain as a one-line registration (#1470 recipe). |
| A3 | **BTD6 counter-recommendation — curated/verified tower lists** | `ready` | The #1498 open question (still open after Layer B #1511): hand-curated wiki-verified lists, owner-supplied, or rules-only. Plus the open golden-set over-refusals + stale golden rubrics in the BTD6 corpus doc. |
| B0 | **Bot-migration assistant PR 1** | `plan-first` | Plan #1416: detect → map → replicate → retire other bots. Build the detect/map foundation on the Essential Setup spine. [plan](bot-migration-assistant-plan-2026-06-24.md). |
| B1 | **Native giveaway system PR 1** | `plan-first` | Plan #1348; build create/enter/draw on the audited service+migration pattern. [plan](giveaway-system-plan-2026-06-23.md). |
| B2 | **Hub child-rendering consistency PR 1** | `plan-first` | Plan #1347; normalise child-panel rendering + placement on `HubChildButton` (#1373). [plan](hub-child-rendering-and-placement-2026-06-23.md). |
| C1 | **Card-render engine — next surfaces** | `plan-first` | Roll the themeable card onto economy/level/fishdex + finish H2 `mining_render` rebase. [vision](../ideas/visual-card-engine-vision-2026-06-23.md). |
| C2 | **botsite React-SPA migration PR 2+** | `plan-first` | PR 1 landed (#1305); continue migrating the live bot-site. [plan](botsite-react-spa-migration-plan-2026-06-20.md). |
| C3 | **Consistency-linter AI-nav PR 1** | `plan-first` | U1 landed (#1376); clear the `views/ai/` `edit_in_place` findings, then graduate the rule. [plan](ai-panel-inplace-navigation-plan-2026-06-19.md). |
| D1 | **Support-ticket subsystem follow-ups** | `plan-first` | Subsystem + discoverability shipped. Remaining: transcript polish, category templates, staff-routing rules, the AI-action-tool audit walk (Q-0201). |
| D2 | **Essential Setup PR 3b + game-unit depth** | `plan-first` | PR 3b = rework the Advanced draft→Final-Review editor (Q-E) + delete dead service code (**needs live-bot verification**). Plus depth in farm / karma / casino / treasury. [setup plan](setup-wizard-restructure-plan-2026-06-24.md). |
| D3 | **Reconcile open-PR staleness classifier** (band-#1290 idea) | `ready` | Machine help for the Q-0125 disposition step (#1509 sitting open across two passes is the exact case). [idea](../ideas/reconcile-open-pr-staleness-classifier-2026-06-22.md). |
| D4 | **Act on the feature-completion ◐/✗ findings** (NEW — 100%-assessed delta) | `ready` | The S1 units are now 100% assessed (#1545); the next step is *building* the depth each ◐/✗ assessment flagged (mining/blackjack/word-chain/casino/treasury), not more assessment. |
| E1 | **procedures→skills Batch 2** | `plan-first` | [plan](procedures-to-skills-conversion-plan-2026-06-17.md). Edits CLAUDE.md → owner-directed only. |
| E2 | **New-subsystem follow-up auto-tracker** (band-#1350 idea) | `ready` | A `## Follow-ups` stub per new subsystem folio + a checker. [idea](../ideas/new-subsystem-followup-tracker-2026-06-23.md). |
| E3 | **Planned-slice hit-rate tracker** (band-#1380 idea) | `ready` | Automate the queue-execution-rate line this pass computed by hand (0 of 17 → fourth consecutive zero). [idea](../ideas/planned-slice-hit-rate-tracker-2026-06-24.md). |
| E4 | **Band-archetype + one-plan-badged-pass guards** (band-#1410/#1440 ideas) | `ready` | Assert exactly one `plan`-badged pass doc; auto-tag each pass with a band archetype (this is the fourth `mixed` band — a classifier would have labelled it). [idea](../ideas/band-archetype-classifier-2026-06-24.md). |

Gated/owner-paced (not in the buildable count): Project Moon Q-0086 live runtime walk · BTD6 live
re-test (re-run *AI Evals → suite: btd6* after deploy + live Discord spot-check) · reaction-roles web
builder (control-API write + security review) · creature-game PvP balance + art (Q-0187) · website
rollout · feedback-board PR 1 (owner dashboard auth) · dashboard writes / control-API (security review).

## 5. The idea + the previous-pass review + the system improvement

- **💡 Q-0089 idea (NEW):** *a `check_command_collisions.py` checker (offline, stdlib, CI-wired) that
  fails when two cogs register the same top-level command name or alias.* The band's prod boot-crash
  (#1541/#1544) was a duplicate global `give` that sat dormant since the initial commit and only
  crash-looped the bot once a second `give` was added — a static, fully-offline-detectable collision that
  cost a live outage. #1544 added a *runtime* boot guard; a CI checker would catch the collision **before
  merge**, turning a prod incident into a red PR (the Q-0194 friction→guard escalation, at the cheapest
  CI tier). Captured in `docs/ideas/`.
- **⟲ Q-0102 previous-pass review (band-#1530, #1532):** it did the reconcile cleanly and correctly
  predicted "zero-queue `mixed` bands are the norm" — which held again here (fourth consecutive). What it
  *missed*: it left **#1509 open for the owner** but did not capture that the open-PR D3 staleness
  classifier it listed would have flagged #1509's multi-pass staleness automatically. This pass carries
  #1509 forward identically (correct — it is owner's), but the recurrence is itself evidence the D3 idea
  is worth promoting from `ready` to *built*: an open `codex`/owner PR sitting across two reconciliation
  passes is exactly the signal a classifier should surface, so a human glances at it rather than each pass
  re-deciding "leave it" by hand.
- **System improvement surfaced:** the prod crash proves the born-red/auto-merge pipeline has **no
  pre-merge command-namespace check** — a class of bug (global-namespace collision) that is 100%
  statically detectable yet reached production. The Q-0089 idea above is the concrete fix; flagging it
  here so the next dispatch run can build it as a high-value E-lane guard.

# Repo sector map — the top layer of the 3-tap navigation

> **Status:** `reference` — the **planning/navigation top layer**: the rough sectors the repo
> divides into, each a link down to its subsystems (middle) and cogs/ideas (bottom). Owner-directed
> (Q-0137 settled, 2026-06-14). The goal: **≤3 taps from anywhere to anywhere.** This is a *planning*
> lens; for the *review-scoping* lens see [`repo-review-map.md`](repo-review-map.md) (they differ —
> see "Two taxonomies" below). Source and binding contracts win over this.

## The 3-layer model (≤3 taps)

```
TAP 1 — SECTOR        this file: the 5 rough sectors (S1–S5)
   ↓
TAP 2 — SUBSYSTEM     docs/subsystems/<area>.md folios — scope · rules · state · next
   ↓
TAP 3 — COG / IDEA    a specific cog/file (repo-navigation-map cheat-sheet) or docs/ideas/<x>.md
```

From any sector you reach any subsystem in one hop, and any cog/idea in two. The middle and bottom
layers **already exist** (folios, the navigation cheat-sheet, the idea backlog); this top layer
names the sectors and wires each to its entry points so the hierarchy is navigable end-to-end.

## The organizing axis: mechanism vs. content (owner, 2026-06-14)

The five sectors aren't all the same *kind* of thing. The load-bearing distinction is between the
**mechanism** (the self-improving-agent engine — shippable as its own project) and the **content**
(what the mechanism produces and operates on — specific to this repo):

> **The AI-Memory system relies on the docs, but the docs are not the system — the docs are a
> *product* of the system.** The memory/workflow engine should be a **shippable project of its own**
> (the `portable-substrate-kit`); the documentation is what it generates and consumes.

The test that assigns any file to **S3** vs **S4**: *"Could this ship decoupled from SuperBot's
specific knowledge?"* → **S3 (mechanism)**. *"Is this SuperBot's specific knowledge/content?"*
→ **S4 (content)**. The checker `check_docs.py` is S3 (engine); the `docs/` it validates are S4.

## The five sectors

### S1 — Bot product
- **Is:** the Discord bot itself — what users interact with. The runtime product.
- **Holds:** `disbot/` (cogs · services · views · core · utils · governance · migrations · data),
  `bot1.py`, `config.py`, `guild_lifecycle.py`, `healthserver.py`. The **in-bot AI**
  (`ai_cog`, `core/runtime/ai/`, `*_ai_service.py`) is a **vertical slice within S1**, integrated —
  *one with the bot* (owner). Promote it out only if it grows its own roadmap.
- **Middle layer:** the [`docs/subsystems/`](subsystems/README.md) folios (games · health-diagnostics ·
  server-management · settings-bindings-provisioning · ai · media-youtube), and the per-subsystem
  cheat-sheet in [`repo-navigation-map.md`](repo-navigation-map.md).
- **Roadmap:** [`docs/roadmap.md`](roadmap.md) bot lanes.

### S2 — BTD6
- **Is:** the Bloons TD 6 vertical — a standing sector (owner), spanning **runtime + offline data**.
- **Holds:** runtime — `cogs/btd6_*`, `paragon_cog`, `views/btd6/`, `services/btd6_*`,
  `utils/db/btd6_*`; offline — `scripts/parse_gamedata.py` & the BTD6 extraction scripts, `data/btd6/`.
- **Middle layer:** [`docs/subsystems/btd6.md`](subsystems/btd6.md) +
  [`decisions/006-btd6-data-provenance-ownership.md`](decisions/006-btd6-data-provenance-ownership.md).
- **Note:** the review map deliberately *splits* BTD6 (A1 runtime / A2 pipeline); as a *planning*
  body of work it is one sector — the clearest proof that planning ≠ review taxonomy.

### S3 — AI-Memory system  *(the mechanism — a shippable project of its own)*
- **Is:** the self-improving-agent **engine** — the substrate that makes any agent work correctly
  with little steering. Content-agnostic and liftable; the `portable-substrate-kit` is S3 extracted.
- **Holds:** the **hooks** (`scripts/claude_*`, `check_branch_freshness.py`), the **autonomous loop**
  (`.github/workflows/{reconciliation-trigger,auto-merge-enabler}.yml`, the console-Schedule dispatch routine,
  Hermes orchestration + the skill *builder* `scripts/hermes/build_skills.py`), the **context-compiler
  machinery** (`tools/agent_context/build_pack.py`), the **checkers** (`scripts/check_*.py`), and the
  **governance scaffolding** (`.claude/CLAUDE.md` as a template, `settings.json`, the question-router
  *mechanism*).
- **Middle layer:** [`docs/operations/autonomous-routines.md`](operations/autonomous-routines.md),
  [`docs/operations/hook-policy.md`](operations/hook-policy.md),
  [`docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md`](ideas/autonomous-improvement-loop-vision-2026-06-12.md),
  [`docs/planning/portable-substrate-kit-extraction-2026-06-13.md`](planning/portable-substrate-kit-extraction-2026-06-13.md).
- **Roadmap:** the agent-ecosystem lane.

### S4 — Documentation system  *(the content/product the engine generates)*
- **Is:** SuperBot's actual knowledge corpus — what S3 produces and consumes. Repo-specific; the
  product, not the mechanism.
- **Holds:** `docs/current-state.md`, `.session-journal.md`, `.sessions/*`, `docs/ideas/*` (content),
  `docs/subsystems/*` folios, `docs/AGENT_ORIENTATION.md`, the binding contracts
  (`architecture.md` · `ownership.md` · `runtime_contracts.md`), `docs/agent/index.yml` (the manifest
  *content*; its *builder* is S3), and this map.
- **Middle layer:** [`docs/AGENT_ORIENTATION.md`](AGENT_ORIENTATION.md) (the read-order router) +
  [`docs/agent/README.md`](agent/README.md) (the context-pack manifest).
- **Reachability:** every doc must be reachable per `check_docs.py` (an S3 engine guarding S4 content).

### S5 — Operations / control-plane
- **Is:** the operational health that **isn't a file** — is it running, is it backed up, is it secret-set?
- **Holds:** deployment (Railway/`Procfile`), secrets (`DATABASE_PUBLIC_URL`, `ROUTINE_PAT`, API keys),
  backups (`backup-db.yml`), CI health (`code-quality.yml`), routine-firing, the Hermes VPS uptime.
- **Middle layer:** [`docs/operations/production-deployment.md`](operations/production-deployment.md),
  [`docs/operations/hermes-control-plane.md`](operations/hermes-control-plane.md),
  the `check_loop_health.py` control-plane probe.
- **Note:** under-represented in any file-based partition precisely because much of it is *live state*,
  not code — every recent silent failure (backups inert, routines not firing, cron lag) lived here.

## The sectors as dispatch targets

The point of a small, memorable top layer is that a **sector is a dispatch unit**: an autonomous
worker (or a Hermes-fired routine) is dispatched by naming a **sector + an action + an executor** (the
executor is usually implied by the sector — see "Who runs it" below) — e.g. *"continue the S2 BTD6 plan
execution"* or *"plan the S3 AI-Memory sector, then an hour later execute it."* The worker reads that
sector's **live queue**, checks the next item's **startability tag**, and advances it. This makes the
five sectors the **menu** a dispatcher picks from.

**Where the live queue lives:** each sector's `Now / Next / Later` is the
[roadmap's per-sector dispatch index](roadmap.md#by-sector--the-live-dispatch-queues). This map
defines the *stable* dispatch contract (below); the roadmap holds the *live* horizons — one source of
truth each, so they don't drift.

**The action vocabulary** (small on purpose):

| Action | Means | Reads | Routine seam |
|---|---|---|---|
| **plan** | draft or refine the plan for the sector's next slice | the sector's `Now`/`Next` + its folios/plans | a dispatch work order (`CLASS: plan`) |
| **execute · continue** | advance the sector's active `Now` slice (or resume a `continue` handoff) | the linked plan + `docs/current-state.md` ▶ | the night-executor / a dispatch work order |
| *reconcile / deep-clean* | *(sector-spanning, not a per-sector dispatch)* — the Q-0107 docs pass over **all** sectors | the ledger + every sector's queue | **kept independent of Hermes** (the watchdog, Q-0137 Thread 1) |

| Sector | Default executor | A worker dispatched here… | Live queue |
|---|---|---|---|
| **S1 Bot** | Claude-in-repo | builds/fixes a bot subsystem slice (incl. the in-bot AI) | roadmap → S1 |
| **S2 BTD6** | Claude-in-repo | runs the decode/answerability backlog or a data refresh | roadmap → S2 |
| **S3 AI-Memory** | Claude-in-repo | builds a mechanism (checker · hook · loop seam · substrate-kit slice) | roadmap → S3 |
| **S4 Docs** | Claude-in-repo | grooms ideas, de-stales a doc area, or runs the docs pass | roadmap → S4 |
| **S5 Operations** | **Hermes-VPS / maintainer** | builds a read-only ops skill or verifies/hardens the control plane | roadmap → S5 |

### Who runs it — the executor dimension
A complete dispatch is **sector + action + executor**. The executor is *usually implied by the
sector*, but naming it is what makes a dispatch unambiguous — three runners:

- **Claude-in-repo** — a Claude Code session/routine that edits the repo and opens a PR. The default
  for **S1–S4** (subsystem code · BTD6 data/answerability · mechanism · docs).
- **Hermes-on-VPS** — the always-on VPS agent: read-only ops, log-triage, dispatch. It edits *nothing*
  in the repo by default (its sanctioned writes are Q-0117 review-merge + Q-0140 docs-only PRs).
- **maintainer** — the human: deploy, secrets, the Railway token, live prod spot-checks.

**S5 is the executor outlier.** Most of S5 is *not* Claude-in-repo — it runs on the **Hermes VPS** or
is a **maintainer** action (every recent silent failure lived here precisely *because* it isn't a file
an agent edits). Only S5's in-repo control-plane *tooling* (a `check_*` script, a workflow guard) is
Claude-shaped. So **don't fire a repo-editing agent at an S5 token/deploy task** — route it to Hermes
or the maintainer. *(Derived 2026-06-14 from the dispatch test — **Q-0143**; the refinement of Q-0137
Thread 1's "every routine started by Hermes": **which** runner depends on the sector.)*

### Is it dispatchable at all — the startability tag
A non-empty `Now` is **necessary but not sufficient** for a dispatch — an item can be blocked. So each
`Now` item in the [roadmap](roadmap.md#by-sector--the-live-dispatch-queues) carries one tag:

- **▶ startable** — an autonomous executor can begin now (no gate).
- **⛔ gated** — blocked on a decision, dependency, or credentials.
- **👤 maintainer** — only the maintainer can do it (deploy · secrets · a live spot-check).

A sector whose `Now` is entirely `⛔`/`👤` is **not autonomously dispatchable** — surface its first
**▶ startable** item (often in `Next`) as the de-facto target. *(S2's `Now` was exactly this: item 3
`⛔` demand-driven, item 4 `👤` maintainer-only — so a "dispatch S2 execute" falls to the `▶` BTD6
grounding-eval cases in `Next`. Q-0143.)*

**What this map does *not* do:** it does not wire Hermes. Turning a phone message into a `/fire`
dispatch — and moving the night executor off GitHub cron onto the always-on Hermes VPS — is **Q-0137
Thread 1** (owner-undecided). The actions above map onto the existing routine fleet documented in
[`operations/autonomous-routines.md`](operations/autonomous-routines.md); this map just makes the
sectors *dispatch-ready*.

## Two taxonomies (don't let them compete)

This **planning** map coarsens the **review** map; they answer different questions and both are valid:

| Planning sector (this map) | ⇄ | Review domain ([`repo-review-map.md`](repo-review-map.md) Axis A) |
|---|---|---|
| S1 Bot product | ⇄ | A1 (minus BTD6) — reviewed as B-slices / B-platform |
| S2 BTD6 | ⇄ | A1 (BTD6 cogs) **+** A2 (offline pipeline) |
| S3 AI-Memory system (mechanism) | ⇄ | A3 (the `scripts/`, `tools/`, CI, hooks *machinery*) |
| S4 Documentation system (content) | ⇄ | A4 (`docs/`, `.claude/` content) |
| S5 Operations / control-plane | ⇄ | A3 (deploy/CI config) **+ live state with no file home** |

- **Planning** asks *"what standing body of work is this, and where's its roadmap?"* → this map.
- **Review** asks *"what's the smallest self-contained unit to review for this change?"* → review map.

When the two disagree on where a file belongs, route by the **question you're asking**: planning a
roadmap → sector; scoping a PR review → review unit.

## Folio homing (machine-readable — the source of truth for `check_sector_map.py`)

Every `docs/subsystems/*.md` folio (the middle layer) homes to **exactly one** sector. Only **S1** and
**S2** have subsystem folios — S3/S4/S5 are mechanism/content/ops, not bot subsystems. The block below
is the machine-readable source of truth that
[`scripts/check_sector_map.py`](../scripts/check_sector_map.py) validates against `docs/subsystems/`:
it fails if a folio on disk is missing here (orphan), listed but absent (phantom), or listed twice
(double-home). When you add/rename/remove a folio, update its sector line here.

<!-- BEGIN sector-folio-map (machine-readable — do not reformat; check_sector_map.py parses S<n>: lines) -->
```
S1: ai, games, health-diagnostics, media-youtube, server-management, settings-bindings-provisioning
S2: btd6
```
<!-- END sector-folio-map -->

## How to keep this alive
- A **new top-level directory** or a **new standing body of work** → add/extend a sector here.
- A **new subsystem** → it lands in its sector's middle layer (a `docs/subsystems/` folio), not here.
- Keep it to **five sectors** unless a genuinely new *kind* of work appears — the value is a small,
  memorable top layer. If it grows past ~7, it has stopped being a top layer.
- **After changing the sectors, run the guards:** `python3.10 scripts/check_sector_map.py` (asserts
  every folio is homed exactly once + every sector's Dispatch names an executor + every `Now` is
  tagged) and `python3.10 scripts/dispatch_menu.py` (previews the live per-sector dispatch menu). Both
  are disposable convenience tools (Q-0105/Q-0143), read-only, **not** CI-wired.

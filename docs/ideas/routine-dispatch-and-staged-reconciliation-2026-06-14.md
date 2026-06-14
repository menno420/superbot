# Routine dispatch, staged deep-clean reconciliation, and planning sectors

> **Status:** `ideas` — **discussion in progress (2026-06-14), not approved.** Owner direction
> dropped in chat + the agent's opinion, captured so it isn't lost. The owner-decision parts are
> routed to **Q-0137** (DISCUSS lane). Binding contracts and `docs/current-state.md` win.

**Captured:** 2026-06-14 (owner design conversation, voice/chat) · **Owning area:** the agent
ecosystem / workflow substrate (the *real artifact*) + operations. Expect refinement as the
discussion continues.

## The owner's direction (three threads)

1. **Dispatch — "a better way to dispatch the routines; every routine started by Hermes, except
   reconciliation."** The current overnight cadence is GitHub's best-effort `schedule:` cron, which
   was measured firing ~4¾ h late / occasionally dropped (the `external-cron-trigger` idea). The
   owner wants a more reliable, Hermes-centred dispatch — with reconciliation kept out of Hermes's
   hands.
2. **Reconciliation → a larger staged "deep clean."** It should evolve from the docs-only Q-0107
   pass into a periodic deep-clean that: surfaces problems, de-stales docs, **disposes of outstanding
   PRs and open branches**, reviews the work that shipped, and produces a **refactored, updated
   roadmap**. Guiding aim: *there is always enough outstanding work* — balanced across **improvement
   + stability** and **new features**. It should have **stages** so it has time for everything.
3. **Planning sectors.** The repo divides into a few standing sectors that planning/reconciliation
   should treat separately: **the main bot · BTD6 (its own standing sector) · the AI-memory /
   workflow substrate (the documented "real artifact") · the documentation system**; the **AI inside
   the bot** is integrated and can be treated as one with the bot. Owner asked: opinion + anything
   forgotten?

## The agent's opinion (honest, source-grounded)

### On dispatch — endorse, with one architectural sharpening + one safety rail
- **It already half-exists.** Per `docs/operations/autonomous-routines.md`: the general **dispatch**
  routine is *already* Hermes-driven (`/fire`, classified by `CLASS:`). The **night executor** is the
  one still cron-driven (`executor-nightly.yml`, 01:17/03:17 UTC). So the concrete change is mostly
  **move the executor's trigger from GitHub cron → Hermes**, which *also* fixes the reliability
  complaint, because **Hermes is the always-on VPS** and a far more reliable scheduler than GitHub's
  `schedule:`.
- **Why reconciliation must stay independent — sharper than "just because":** reconciliation is the
  **watchdog**. It is the pass that verifies the control plane (now via `check_loop_health.py`, the
  #853 probe). If it *also* depended on Hermes, a Hermes outage would silently take down the very
  routine that detects outages. Keeping reconciliation on its deterministic PR-boundary trigger makes
  it the **dead-man's switch** for the Hermes-dispatched fleet. The owner's instinct is right for a
  reason worth writing down.
- **Safety rail — don't make Hermes a silent single point of failure.** The failure class we have
  *already* hit twice is *routines silently not firing*. If Hermes becomes the sole trigger, a Hermes
  outage = the whole fleet stops, invisibly. Keep GitHub `schedule:` as a **degraded backstop** so an
  outage means "late," not "stopped." Defense-in-depth, not either/or.

### On the staged deep-clean — strong agree on intent; two refinements
- **(a) Separate the mechanical from the judgment.** Stale-doc detection, ledger drift, open-PR /
  open-branch disposition, and control-plane health should be **generated into a punch-list by
  checkers** (`check_docs`, `check_current_state_ledger`, `check_loop_health`, `check_reconciliation_due`
  + a new open-PR/branch sweep), so the session spends its scarce *judgment* budget on the roadmap
  refactor and new-feature planning — not on re-deriving state. (Composes the `reconcile-prebrief`
  + `ledger-checker-print-pr-subjects` ideas.)
- **(b) Stages must each ship a durable artifact and be resumable.** One context window cannot
  deep-clean *everything* well; a 7-task mega-session yields shallow passes, which violates the
  verify / source-wins ethos. Make it a staged **program** that self-chains like the executor already
  does via `continue` issues — e.g. **Stage 1** hygiene + triage (punch-list, PR/branch disposition,
  control-plane verify) → **Stage 2** review of shipped work → **Stage 3** per-sector roadmap refactor
  → **Stage 4** backlog replenishment (ensure each sector has live Now/Next work).
- **Terminal condition (so it's bounded, not infinite):** the deep-clean is "done" when **every
  sector has non-empty Now/Next horizons, zero rotting PRs/branches, ledger + docs green, and the
  control plane is verified healthy.** That is the owner's "always enough outstanding work" turned
  into a **checkable backlog-health invariant**.

### On sectors — the key reframe: planning taxonomy ≠ review taxonomy
The repo **already** has a partition: `docs/repo-review-map.md` **Axis A** (A1 bot runtime · A2 BTD6
data pipeline · A3 dev/CI/agent tooling · A4 docs & agent system · A5 tests). But that is a
**review-scoping** taxonomy ("what is the smallest self-contained unit for *this change*?"). What the
owner is describing is a **planning** taxonomy ("what standing bodies of work does the roadmap /
reconciliation organize around?"). These are related but **not the same**, and the repo does **not yet
have the planning one** — that is the real gap this question exposes. **BTD6 proves it:** the
review-map deliberately *splits* BTD6 across A1 (runtime cogs) and A2 (offline pipeline), yet as a
*planning* body of work it is clearly **one standing sector** (the owner is right). Two valid
taxonomies, different jobs.

**Proposed planning sectors (coarsening of Axis A for roadmap purposes):**

| # | Planning sector | Maps to | Notes |
|---|---|---|---|
| **S1** | **Bot product** | A1 (minus BTD6) | The in-bot AI (`ai_cog`, `core/runtime/ai/`, `btd6_ai_service`) is a **vertical slice within S1**, integrated — *one with the bot*, per owner. Promote to its own sector only if it ever grows its own roadmap. |
| **S2** | **BTD6** | A1 BTD6 cogs **+** A2 pipeline | Standing sector (owner). Spans runtime + offline; review-map keeps them split, planning treats them as one. |
| **S3** | **Agent substrate** | A3 + A4 | The "real artifact": memory (journal, current-state, sessions, ideas) + the **documentation system** + governance (CLAUDE.md, Q-router) + tooling/hooks + the autonomous loop. The owner's "AI-memory system" and "documentation system" are **two faces of this one sector** (mirrors the A3 *enforcement* / A4 *content* split) — keep as one sector with sub-lanes for planning. |
| **S4** | **Operations / control-plane** | *(new — not in Axis A)* | **The forgotten sector.** See below. |
| **(S5)** | **Substrate-as-product** | the portable-substrate extraction plan | Future / outward face of S3; only once it's real. |

### What was forgotten — Operations / control-plane (the important one)
The existing partition is **code-centric** — it partitions *files*. It has **no home for operational
health that isn't a file**: *is the routine firing? is the backup actually working? are the Railway
secrets present? is Hermes up?* **Every recent real failure lived here** — `DATABASE_PUBLIC_URL` unset
(no working backups), routines-not-booting, cron lag — and **none of them is "a file to review."** This
deserves to be its own planning sector (**S4**), and it is exactly what the deep-clean's Stage-1
control-plane check (`check_loop_health`) feeds. Corollary: **the deep-clean must verify the control
plane *ran* before planning on top of it** — never plan assuming the routines fired; check first.

### Other things worth not forgetting
- **Security / authority as a cross-cutting concern.** As Hermes gains dispatch power, its blast radius
  grows — the `ROUTINE_PAT` scope, secret handling, Hermes's sanctioned writes (Q-0117/Q-0121). Partly
  under S4, but track it deliberately.
- **Measurement.** The deep-clean is the natural place to compute "is the loop getting healthier?"
  (the `session-telemetry` / `gap-analysis` idea) — turn the felt autonomy into a measured trend.
- **Reconcile the two taxonomies in-doc.** Whatever sectors are adopted, note the S→A mapping in *both*
  `repo-review-map.md` and the roadmap so the repo doesn't grow two competing partitions.

## Routing
- Owner-decision parts (adopt the planning-sector taxonomy? move the executor to Hermes + keep a cron
  backstop? approve the staged deep-clean shape + terminal condition?) → **Q-0137** (DISCUSS lane).
- Mechanical follow-ons that need no decision (the open-PR/branch sweep checker; folding
  `check_loop_health` into the deep-clean) are quick-win tooling once the shape is approved.

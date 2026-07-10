# Gen-3 Project deployment standard — the fast path (2026-07-10)

> **Status:** `plan` — the owner-requested standard for deploying gen-3 Projects fastest
> and most efficiently, with the settings/instructions standards distilled from the
> round-3 boot day (Q-0258/Q-0259/Q-0260, the manager boot verification, the gen2
> blueprint). Strategy choice is **simulation-backed**:
> [`../../tools/sim/gen3_deployment_sim.py`](../../tools/sim/gen3_deployment_sim.py)
> (results pinned in §1). Companions:
> [`round3-dispatch-runbook-2026-07-10.md`](round3-dispatch-runbook-2026-07-10.md)
> (live checklist; this doc is the *method*, the runbook is the *state*) · founding
> packages: [`idea-engine`](round3-founding-package-idea-engine-2026-07-10.md) ·
> [`product-forge`](round3-founding-package-product-forge-2026-07-10.md).

## 0. Owner ruling on scope (Q-0261, 2026-07-10 — supersedes §1's recommendation for the core)

The **core-6 Projects** (manager · substrate-kit · superbot-next · Idea Engine · Product
Forge · sixth seat TBN) deploy **one at a time, finalize-first**: a Project launches only
after its repo's open owner-actions/questions are drained and its settings are done — a
conscious depth-over-speed trade for the system's roots. The pipelined fast path below
remains the standard for the **post-core** manual and game lanes. substrate-kit is the
second Q-0260 exception (write-all for kit distribution, hard-scoped by its founding
instructions).

## 1. The verdict — pipeline the boots, keep the calibration gate

Three strategies simulated over the 6 remaining boots (Idea Engine · Product Forge ·
3 game Projects · Builder re-dispatch), 5 000 Monte-Carlo runs, durations from today's
observed boots where available (labeled in the sim source):

| Strategy | Wall-clock (med / p90) | Owner active | Error exposure (mean) |
|---|---|---|---|
| sequential (one Project end-to-end at a time) | 296m / 326m | 54m | 15.5m |
| big-bang (paste everything, no calibration gate) | **110m** / 130m | **36m** | **77.4m** |
| **pipelined + gate (RECOMMENDED)** | 113m / **121m** | 49m | **15.1m** |

- **Pipelined pays ~3 minutes of wall-clock over big-bang and buys a 5× cut in error
  exposure** (wrong-premise boots running uncorrected). Its p90 is actually the best —
  big-bang's tail is fattened by post-hoc rework.
- Sensitivity sweep (P(package error) 0 → 0.6): the ranking is stable; at high error
  rates pipelined beats big-bang even on raw wall-clock. Today's observed error rate is
  ~0.35 (the six-vs-seven miscount + the pre-seeded-inbox premise both hit at the manager
  boot — and the calibration gate caught both, which is the effect the sim encodes).
- Sequential's only virtue is simplicity; it wastes ~3 hours of wall-clock vs either.

**Why the gate stays cheap in the pipeline:** the owner reads Project i's calibration
answer *while Projects i+1…n are already booting* — it gates one lane, not the world.

## 2. The standards (what every gen-3 Project gets, no per-case thought)

**Repo settings (new repos; two-touch by necessity):**
1. At creation: public (Q-0260 raw-read path; private only for a pokemon-class reason,
   which then must be attached to the manager env), default branch `main`.
2. After the seed PR lands CI: *Allow auto-merge* ON + the seed's named check (kit
   `substrate-gate` / smoke) as the **required check**. One settings visit per repo,
   batched — the boot's ⚑ OWNER-ACTION names the exact check.

**Environment (Q-0260 + launch pack §6b):** one env per repo, named exactly like the
repo, **single repo attached** (write = lane boundary; the manager is the only
multi-repo exception). Setup script = the matching fleet archetype **verbatim**
(`fleet-manager/environments/archetype-*.sh`). Variables: none unless a genuine secret.

**Custom Instructions (the Project-scoped job description, ≤7,500 chars):** who the
Project's agents are + the ONE repo they work · "the repo's doctrine governs mechanics"
pointer (never restate ceremony) · typical-tasks list with how-to · reporting bar
(cite commits/PRs, family model names, negatives are headlines, no secrets) · session
shape (HEAD-first, **work loop per Q-0265** — slice after slice, each its own
merged-on-green PR *(amended 2026-07-10; was "one bounded slice")* — heartbeat last,
decide-and-flag, walls quoted verbatim and never re-probed).

**Coordinator chat brief (first message; the routine fires into this chat):** mission +
done-when · durable-twin pointer (committed file to re-read when context thins) ·
numbered BOOT NOW list ending in ARM YOUR ROUTINE with the exact `create_trigger` args
and wake prompt · verify-the-trigger + record-the-recipe-verbatim step, with the
owner-manual fallback block if walled · known-platform-facts block · **calibration ask**
(mission back in one paragraph + the concrete first moves + the routine name/cadence).

**Operating model + routine — AMENDED 2026-07-10 (owner directive Q-0265, folded by the
manager per the part-4 brief §2b MANAGER-ONLY rider; supersedes this section's original
one-slice pacing).** Every gen-3 seat is **born continuous**:

- **Work loop, not one bounded pass:** when a slice finishes and genuinely useful work
  remains, the seat starts the next slice the same turn — slice after slice, each still
  its own merged-on-green PR (the throttle is removed, not the ceremony; near context
  limits, hand off cleanly to a fresh card/branch instead of degrading).
- **The `send_later` continuation chain (~15 min out, "continue the work loop") is the
  pacemaker**, armed before ending any turn — where the seat's toolset has the tool.
  **If a scheduling tool is absent from the coordinator's toolset, FIRST retry from a
  spawned worker seat** — toolsets are seat-dependent *within one Project*: twice-proven
  on 2026-07-10 (idea-engine, then sim-lab, whose coordinator lacked BOTH
  `create_trigger` and `send_later` while its worker had both and armed first-try).
  Only after a worker-seat denial (recorded verbatim) does the cron below become the
  pacemaker / the ask go owner-manual.
- **The standing cron is demoted to a dead-man failsafe**, named "<seat> failsafe wake",
  keeping the 2-hourly stagger (lanes `0 */2 * * *`, manager `30 */2 * * *`); its prompt:
  if the chain is alive, verify liveness in one line and end; if it stalled, resume the
  work loop and re-arm the chain. Verify in the trigger registry immediately
  (`list_triggers`) — **never wait for the first fire as proof** (runs aren't
  inspectable owner-side; the registry is).
- **Backpressure, not time, is the brake:** pause the specific activity whose downstream
  queue is saturated (generation pauses on several unpulled outbox proposals; building
  pauses at done-when + empty inbox after flagging the manager) — grooming,
  verification, hygiene, and backlog work continue.
- **The Q-0089 honesty guard survives:** genuinely out of useful work → say so in
  status and idle until the failsafe; never invent filler — the output stays usable as
  evaluation data.
- **Free-window posture:** through 2026-07-14 use the free Projects **excessively**
  (more parallel work, child workers, fan-out — within the quality bar); everything
  produced feeds the owner's post-window consolidation pass.
- **Volume-first founding doctrine (owner directive Q-0266, 2026-07-10):** every
  Project is *created* to maximize output — the founding package aims the seat at "as
  much material as we can" from its first turn. The bar is **CORRECT over BEST**:
  honest states, citations, working increments are mandatory (and a lane's
  non-negotiables — e.g. trading's pre-registration contract — are part of *correct*),
  but good-enough beats polished; refinement is consolidation-phase work. Lifecycle:
  **populate all repos now → owner-gated consolidation later → a few dedicated
  maintenance projects** — so seats produce committed, discoverable, honestly-labeled
  artifacts the future triage can grade.

*(Superseded pre-Q-0265 text, kept for the record: "2-hourly, lanes at `0 */2 * * *`
(even hours :00), manager offset `30 */2 * * *`; prompt = ONE bounded pass in role
vocabulary + 'no excessive work' (Q-0259 r.1) + heartbeat-last + the one-shot re-arm
fallback line.")*

**Boot verification ritual (dispatch copilot, per boot):** calibration reviewed (gate)
→ trigger in registry with exact name/cron → boot PR merged + heartbeat at HEAD (verify
against git, not the agent's report) → tick the runbook §5 log.

## 3. The step-by-step deployment (pipelined, concrete)

**Phase 0 — owner click batch (~10 min, all up front):**
1. Create repos: `product-forge` + the 3 game repos (once the manager's Q-0259 r.5
   mapping names them; if it proposes reusing existing repos, skip those creates).
2. Create envs from archetypes for the new repos (§2 standard); Idea Engine selects the
   existing `superbot` env; Builder keeps its existing env.
3. While in settings anyway: the standing sweep items (venture-lab auto-merge +
   required check; superbot-next up-to-date rule relax; fleet-manager env += 
   pokemon-mod-lab per Q-0260).

**Phase 1 — paste wave (owner, ~2 min per Project, no waiting between):**
For each Project in order — Idea Engine → Product Forge → games → Builder: paste
Custom Instructions, then the chat brief, move straight to the next. Builder gets the
launch-pack §2 continuation prompt + the standing-@codex line (Q-0259 r.3) instead of a
founding package.

**Phase 2 — calibration reads (owner, interleaved):** as each calibration answer
arrives, read it against the package's §4 checklist (good = mission + concrete first
move + exact routine + anticipated owner clicks; red flags listed per package). One word
("go") continues the boot; a correction now costs minutes, not a rework cycle.

**Phase 3 — verification wave (copilot, async):** I verify each boot as it completes
(trigger registry → heartbeat/PR at HEAD) and keep the runbook §5 log live; you only
get pinged for the batched required-check clicks and anything that fails verification.

**Phase 4 — loop closure (next 24h):** all core routines show completed runs across
24h · owner-queue holds only owner-only items · zero stuck PRs (launch pack §5
criteria). The manager's staleness sweep is the standing safety net under all of it.

## 4. Fold-back

This standard is round-3 material; its durable home for gen-3+ is the manager's
doctrine (gen2-blueprint successor / playbook) via the Q-0259 r.2 gen-3 report — the
manager should fold §2 in as the environment/instructions standard and cite the sim.

**Fold-back is materializing (owner-reported live, 2026-07-10 part-4d):** the manager
is preparing a **centralized prompt registry** — one home for Custom Instructions,
coordinator briefs, and wake prompts. One-source-of-truth rule once it exists: the
registry copy is canonical; the founding packages' §1/§2 blocks in this repo become
frozen historical copies with superseded-by pointers; any prompt change is made in the
registry FIRST and then re-pasted by the owner (pasted instruction text is otherwise
invisible to the fleet — version-stamp every prompt `vN · YYYY-MM-DD` so a seat can be
asked to quote its header and drift becomes detectable). Ingest inventory + registry
rules: the dispatch runbook §6.1 paste block.
The sim itself follows Q-0105: parameters are estimates pending the next real boots;
re-run with measured durations before trusting fine-grained minutes (the *ranking* is
robust across the sweep).

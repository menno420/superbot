# Fleet centralization plan — `fleet-manager` as the single source of truth

> **→ SUPERSEDED 2026-07-14 (ORDER 005; fm central-docs plan §1 Self-application / Slice 0
> item 9):** the living central-docs plan is now **fleet-manager
> [`docs/planning/2026-07-14-central-docs-plan.md`](https://github.com/menno420/fleet-manager/blob/main/docs/planning/2026-07-14-central-docs-plan.md)**
> (fm main @ `780c81b`). This file is the **superseded/frozen seed** — cross-repo/fleet doc
> doctrine is fleet-manager-canonical (same supersession pattern as
> [`../eap/fleet-manifest.md`](../eap/fleet-manifest.md) → the generated roster). Plan and
> amend fm-side, not here.
>
> **Status:** `historical` (was `plan`; re-badged on supersession, the band-#1980-pass
> convention) — owner-directed. Turns the owner's ask ("fleet-manager should become
> the one source of truth… its sole purpose should be to maintain perfect doc records
> across all repos based on its timely triggers") into a concrete, verified, phased design.
> Grounded in the 2026-07-11 fan-out (centralization + drift probes) and firsthand reads of
> `fleet-manager`'s actual substrate. Companion to the [fleet
> review](fleet-review-2026-07-11.md). Decide-and-flag (Q-0240): reversible planning
> decisions are made here with rationale; the **one genuine product fork is flagged in §1
> for your veto/redirect.**

## 0. The reframe (why this is smaller than it sounds)

**`fleet-manager` is already ~70% the single source of truth you're describing.** It is not
a from-scratch build; it's a **refocus + gap-closing**. What already exists and works
(verified against source):

- **`docs/roster.md` — a machine-generated, ≤~2h-fresh aggregation** of every lane's
  `control/status.md` heartbeat + the live `list_triggers` registry (`scripts/gen_roster.py`,
  R25). It emits per-lane Age/Verdict (FRESH/STALE/DARK/DEAD), phase, kit version, orders,
  wake-trigger id+cron, and repo@HEAD evidence. The old hand-maintained
  `superbot/docs/eap/fleet-manifest.md` was **explicitly superseded** by it on 2026-07-11
  and now hard-redirects all fleet-state reads here.
- **`docs/owner-queue.md`** — the one deduplicated owner-only queue (R17 evidence per item).
- **`control/` bus** — inbox ORDER grammar + status heartbeat, **CI-enforced** by
  `substrate-gate.yml` (append-only inbox, control-status gate).
- **`environments/`** — `archetypes.md` + `env-grant-policy.md` (tiered secret-grant doctrine).
- **`MISSION.md`** already declares the custodian job: *"keep every lane ordered, truthful,
  and never stuck… the doctrine matches verified reality."*

So the work is: **(a) pick the mission sharpness (§1), (b) close the six verified gaps that
let drift in (§2), (c) build the generators/guards + the timely-trigger loop (§3), (d)
consolidate the split records home (§4).**

## 1. ⚑ The one fork for you — mission sharpness (decide/veto)

Your words were "its **sole** purpose should be to maintain perfect doc records." That is a
real strategic choice with three shapes:

| Option | What fleet-manager does | Trade-off |
|---|---|---|
| **A — Custodian-primary (recommended)** | Records-custody becomes the **CI-enforced primary** mission; the ORDER-relay coordination is **retained as secondary** (it demonstrably works — the model-attribution relay hit 14/14 lanes) | Keeps the working relay; the custodian job gets teeth. Lowest risk. |
| **B — Sole custodian** | Strip coordination entirely; fleet-manager *only* generates/guards records; dispatch moves to the owner + per-lane self-arm | Cleaner mission, but throws away a working coordination mechanism and needs a new home for cross-lane orders |
| **C — Status quo (dual, hand-run)** | No change | Leaves the drift + single-point-of-freshness that this whole review flagged |

**My recommendation: A.** The evidence says the coordination *works* and the records-custody
is the part that's *manual and fragile and drifting*. "Sole purpose" is best read as
**"custody is the job it must never fail at,"** not "delete the relay." Sharpen custody to
CI-enforced; keep the relay as the delivery arm that *acts on* what custody detects.

> **✅ OWNER DECISION (2026-07-11): Option A — custodian-primary.** Records-custody becomes
> the CI-enforced primary mission; the ORDER-relay coordination is retained as the secondary
> delivery arm. The rest of this plan (§2–§6) is written for A and is unchanged. (Veto-able
> per Q-0240 if you later want true B.)

## 2. The six verified gaps (what lets drift in today)

From the centralization + drift probes, confirmed against source:

1. **No automated roster regeneration.** The only workflow in fleet-manager is
   `substrate-gate.yml` (a PR/push *gate*, not a regen). Regen is an agent action at the
   manager wake, and `gen_roster.py --triggers` **requires a hand-exported JSON** (no
   headless `list_triggers`). ⇒ if the manager seat parks, the roster silently freezes.
   **Live proof: the roster is ~13h stale right now, under its own 24h alarm.**
2. **Owner-queue is hand-swept, not generated.** `parse_status` extracts
   `updated/phase/kit/orders/health/lane` but **not** the heartbeat's `⚑ needs-owner`
   block ⇒ a new owner-ask doesn't surface centrally until a manual re-sweep. The
   highest-value channel has no automated aggregation.
3. **Multi-lane repos leak sub-seat heartbeats.** `read_heartbeat` reads **one** file per
   repo (breaks after `control/status.md`) ⇒ superbot-games' `status-mining.md` +
   `status-exploration.md` sub-lanes are invisible; one row stands in for three.
4. **Only the truncated header is centralized.** The rich per-repo record (EAP program
   docs, each lane's `current-state.md`, `.sessions/`, `docs/retro`) lives **only** in each
   repo. No generated index links a roster row to its evidence home ⇒ navigation is tribal
   knowledge and the two record homes (superbot/docs/eap ↔ fleet-manager/docs) can drift.
5. **fleet-manager doesn't keep its own ledger.** `docs/current-state.md` and
   `project.index.json` are **unfilled template stubs**, yet `current-state.md` is a declared
   boot readpath doc — an agent booting per the reading route gets an empty living-ledger.
   The manager enforces a heartbeat discipline it doesn't itself hold.
6. **The load-bearing generator is self-flagged UNVERIFIED.** `gen_roster.py` carries a
   Q-0105 "confirm across sessions" header with only **1** clean verification run logged of
   the "several" it requires. The SSOT depends on a tool not yet graduated.

## 3. The design — a self-refreshing, self-guarding records custodian

The target: **fleet state is *generated* from lane heartbeats on a timely trigger, *guarded*
against drift by checkers, and *navigable* from one index — so no fleet fact depends on a
human or an agent remembering to update a doc.** Concretely:

### 3a. Close the freshness single-point-of-failure (highest leverage)
- **`telemetry/triggers-snapshot.json`** — at each manager wake, dump `list_triggers` to a
  committed JSON (gives `gen_roster.py` a headless source **and** a git-visible registry
  history). Unblocks everything below.
- **Automated regen on a timely trigger** that does **not** depend on the manager agent
  waking: a fleet-manager GitHub Actions cron (or a dedicated CCR trigger whose *only* job
  is regen) reads the committed triggers-snapshot + re-fetches heartbeats + regenerates
  `roster.md`. This is the "timely triggers" mechanism the owner asked for, made robust.
- **`check_roster_freshness.py`** — reds/escalates when `generated-at` is older than 2×
  cadence (~4h), replacing the retired `check_manifest_freshness.py` (superbot #1974) but
  pointed at the *canonical* roster. Make "regenerate roster" a **required, verified** wake
  step, not an optional "commit only on change" (a 13h gap means the wake ran without regen).

### 3b. Generate the owner-queue candidate feed
- Extend `gen_roster.parse_status` to also extract each heartbeat's `⚑ needs-owner` /
  `OWNER-ACTION` block and emit a **generated candidate list**. The manager still curates /
  dedups the human-readable `owner-queue.md`, but nothing is silently stranded in a lane.
- **`check_owner_queue.py`** (the session-idea `verify_owner_queue.py`, promoted) — at each
  wake, for every queue item citing a PR with a MERGE action or a "RESOLVED-PENDING-MERGE of
  PR #N" status, query live PR state and flag anything already merged/closed. *(Items 1–3
  and 13 would all have fired today.)*
- **Stable slug IDs** for queue items (`OQ-GAMES-MERGE`, not positional numbers the periodic
  rewrite reshuffles) + a lint flagging cross-repo `owner-queue item <N>` references.

### 3c. Surface every heartbeat + link the evidence
- Enumerate **all** `control/status*.md` per repo (each repo already declares them in
  `substrate.config.json heartbeat_files`) and emit **one roster sub-row per lane** — closes
  the superbot-games blind spot and any future multi-seat repo.
- **Generated cross-repo index** linking each roster row to its program-record home
  (`superbot/docs/eap` pointer, the lane's `docs/current-state.md`, latest `.sessions/` +
  `docs/retro`). Makes the manager-internal ↔ program-facing split navigable from one place,
  so the two homes get **reconciled** instead of drifting.

### 3d. Harden the heartbeat contract (so the inputs are trustworthy)
- **Reject future-dated `updated:` stamps** at push time (extend the monotonic-heartbeat
  guard) — a future stamp poisons staleness math (product-forge did exactly this).
- **Move buried self-reviews to `docs/retro/`** (fleet-standard; `websites
  docs/retro/self-review-2026-07-11.md` is the template) so lane state that outlives a wake
  isn't overwritten in `status.md`.
- **Give the hub (superbot) a heartbeat.** The roster literally shows `n/a — no
  control/status.md` for superbot — the most important repo isn't in the aggregation. A
  minimal `superbot/control/status.md` (or a hub-adapter in `gen_roster`) puts it in.

### 3e. Graduate the generator + fill the custodian's own ledger
- Log the remaining clean `gen_roster.py` verification runs to clear its Q-0105 UNVERIFIED
  header before the roster is treated as unconditionally authoritative.
- Fill (or retire) `fleet-manager/docs/current-state.md` + `project.index.json` so the hub
  models the discipline it enforces.

## 4. Consolidate the split records home

Today records live in **two** places: manager-internal (fleet-manager/docs) and
program-facing (superbot/docs/eap). That split is the structural drift risk. The rule going
forward:

- **fleet-manager = canonical for cross-repo/fleet state**: the generated roster, the
  owner-queue, the fleet-triage register (below), the capability ledger, the env archetypes.
- **Each repo = canonical for its own internal state**: `current-state.md`, `.sessions/`,
  `docs/retro`, subsystem docs. fleet-manager **links** these via the 3c index; it does not
  copy them (copies drift).
- **superbot/docs/eap** (program reviews, night-reviews, Anthropic email drafts) → keep the
  *program-narrative* docs there, but **register each in the fleet-manager cross-repo index**
  so there's one front door. The product-catalog + this review are program-facing; they stay
  in superbot with a fleet-manager pointer.

**Port the triage register to fleet-manager** (the Q-0089 session-idea `fleet-triage.md`):
the keep/replace/archive/delete table in the [review](fleet-review-2026-07-11.md) §1 is the
seed. It becomes a standing, re-reviewable "should-it-exist?" ledger — distinct from the
roster (freshness) and product-catalog (what each is). It belongs in fleet-manager as
cross-repo state.

## 5. Build plan (phased, 2–3 PRs; assign to the fleet-manager dispatch session)

| Phase | Deliverable | Unblocks |
|---|---|---|
| **P1 — Freshness (do first)** | `telemetry/triggers-snapshot.json` dump at wake · automated regen trigger · `check_roster_freshness.py` · make regen a required wake step | Kills the single-point-of-freshness; the ~13h-stale class |
| **P2 — Queue generation** | `parse_status` `⚑ needs-owner` extraction → candidate feed · `check_owner_queue.py` (PR-state prober) · slug IDs | Kills "already-satisfied ask" + "stale pending-merge" drift |
| **P3 — Coverage + index** | multi-heartbeat sub-rows · generated cross-repo evidence index · superbot hub heartbeat · fill fleet-manager `current-state.md`/`project.index.json` · port `fleet-triage.md` · graduate `gen_roster.py` | Closes the reachability + self-ledger gaps; one front door |

Each phase is docs/tooling-only in fleet-manager, CI-gated by its existing `substrate-gate.yml`,
and reversible. **This is the mission of the [fleet-manager dispatch
prompt](../owner/dispatch-prompts-2026-07-11.md).**

## 6. What success looks like (done-when)

- A fresh session (or you) reads **one** roster that is provably ≤4h fresh, with a red alarm
  if not — no silent stale trust.
- Every owner-ask a lane raises appears in a generated candidate feed the *same wake*; no
  ask waits on a manual sweep; no already-done item survives.
- Every roster row links to its evidence home; the manager-internal ↔ program-facing split
  is navigable and reconciled, not drifting.
- fleet-manager keeps its own ledger to the standard it enforces; `gen_roster.py` is
  graduated out of UNVERIFIED.
- The custodian **generates and guards** — the human/agent no longer has to *remember* to
  keep a doc true. That is "perfect doc records on timely triggers," mechanized.

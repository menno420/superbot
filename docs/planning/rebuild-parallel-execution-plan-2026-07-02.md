# Rebuild — parallel-execution plan & realistic schedule (2026-07-02)

> **⚠ SUPERSEDED (2026-07-06):** gates + sequencing live in
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md) §4/§5 — this
> doc's "two gates" (linchpin proof; kit shipped) **both cleared** (#1639/#1649), and its
> "K4/K5/K6 run concurrently off the K7→K8 spine" claim is **corrected** there (D-19: the
> edge-verified S0–S15 order shows S8/K7 consumes K4–K6; parallelism is within-band fan-out).
> §1's measured velocity baseline stays citable data. Note: this doc's "handoff §F" citations are
> phantom (the handoff ends at §E).

> **Status:** `historical` — the execution-timing companion to
> [`rebuild-design-spec-2026-07-02.md`](rebuild-design-spec-2026-07-02.md) (which specifies *what* to
> build and in *what order*, but puts no clock on it). This doc answers **"how long, really?"** by
> grounding the estimate in **this project's observed agent-fleet velocity**, not a traditional
> software-team estimate — and by separating the work that compresses under parallelism from the work
> that does not. Decision-support for the Phase-3 go/no-go. Source + merged PRs win over this file.
>
> **One calibration caveat:** the two variance-driving numbers (golden-harness coverage %, grammar-fit
> %) are being *measured* by the linchpin-proof Fable mission (handoff §F). Until they land, §6's ranges
> are model-based; the go/no-go replaces them with real figures (§9).

## 0. The answer up front

**"A few weeks or less" is correct.** The reflexive "multi-month" estimate is simply the wrong model for
a 16-wide agent fleet that merges 20–40 PRs/day. Grounded in the measured velocity below:

- **Realistic active-build center ≈ ~2 weeks.**
- **Hard floor ≈ ~1.5 weeks** — set by the *one* thing no amount of parallelism removes: the
  topologically-sequential kernel (K0→K10) plus a deliberately-careful cutover.
- **Stretch ≈ 3–4 weeks** — only if the two throttles (§4) come in weak (low harness coverage forcing
  manual port verification, or a grammar that forces heavy escape-hatch rework).

The estimate is short because **the bulk of the work (the ~100-PR port) is close to embarrassingly
parallel and self-verifying**, and the parts that aren't are small. The whole scheduling problem reduces
to: *compress the sequential kernel, and keep the two throttles green.*

**Two gates, not one — and neither is on the clock above until it's cleared.** *Committing* to the build
is gated by the linchpin proof (harness coverage + grammar fit, §4). *Starting* the new repo is gated by
a more fundamental deliverable: the **finished, shippable AI-memory system** (the substrate-kit) — because
design-spec §9.1 makes it the first thing K0 does (it plants the doc skeletons, decision ledger,
orientation budget, namespace guard, and seam-authority checks). If the memory system isn't shipped before
K0, the new repo is born without its nervous system and reintroduces the exact "nothing is centralised"
failure the rebuild exists to end. Both gates clear via **parallel Fable missions buildable now** (§8.1);
the kernel clock starts only once the memory system is shippable.

## 1. The empirical velocity baseline (why the estimate is short)

Measured from `origin/main`, last ~72h (not aspirational — the demonstrated steady state):

| Signal | Observed |
|---|---|
| Peak merge day | **41 PRs merged 2026-07-01** (12 on 06-30, partial 07-02 already 8 by midday) |
| Substantive agent PRs | **37 of the last 60 merges** (~62%; rest are automated dashboard-refresh + merge-main) |
| Concurrent agent lanes | **~16 distinct `claude/*` branches** live across the last 120 commits |
| Merge cadence (active hours) | multiple PRs/hour (e.g. 6 merges in the 17:49→18:51 window on 07-01) |
| Session turnaround | sessions open → born-red PR → complete → auto-merge in **hours**, not days |

So the fleet already sustains **~20–30 substantive merges/day across ~16 parallel lanes**, with
server-side auto-merge-on-green removing the human from the merge loop. That is the engine the rebuild
runs on.

## 2. The execution model — four classes of work

Every piece of the rebuild falls into one of four classes, and the class — not the size — decides whether
throwing agents at it helps:

| Class | Rebuild examples | Parallelism helps? | Duration driven by |
|---|---|---|---|
| **Sequential critical path** | kernel **K0→K10** (each band depends on the ones above it) | **No** — topological deps | how fast each band lands; how many bands truly overlap |
| **Parallel fan-out** | **Phase-4 port** (~100 PRs), the de-risking prep | **Yes, hugely** | # concurrent lanes × harness self-verification |
| **Human gates** | design approval · the go/no-go · 3 sim "why-it-won" ratifications · cutover sign-off | N/A | **owner-decision cadence** |
| **Careful / irreversible** | the importer + the Phase-5 cutover | **Deliberately no** | you *want* it slow, dry-run-reviewed |

**The schedule identity:** `total ≈ (sequential critical path) + (careful cutover) + (human-gate latency)`.
Everything else — the port, the prep — hides underneath the critical path *if the throttles are green*.
That is why the port's size (~100 PRs) is not the scary number; the kernel's depth (11 sequential bands)
is.

## 3. Per-phase schedule

| Phase | Class | Est. (active) | Notes |
|---|---|---|---|
| **0.5 golden harness + 0 substrate-kit + grammar proof** (pre-gate, now) | fan-out | **~2–3 days** | one Fable mission (harness + grammar) ∥ one Opus session (substrate-kit); buildable today, no gate |
| **Owner gate** (design + go/no-go) | human gate | hours–1 day | external-review seam already exercised (#1637); decision, not work |
| **Kernel K0→K10** | **critical path** | **~5–8 days** | the irreducible spine; K7 (workflow engine) + K8 (interaction) are the big bands (~1–1.5 d each); K4/K5/K6 partly overlap once K2/K3 land |
| **Phase-4 port** (7 bands, ~100 PRs) | fan-out | **~5–8 days** | starts overlapping the kernel tail (settings band needs only K7+K8); self-verifying red-until-parity → auto-merge |
| **Sim passes 1–3** | fan-out + gate | overlaps port | each needs one owner "why-it-won" ratification |
| **Phase-5 cutover** | careful | **~1–2 days** + rollback watch | importer dry-run → owner reconciliation review → freeze → delta import → Railway flip → bounded rollback window |

**The critical-path chain** (what actually sets the floor):
`K0 → K1 → K2 → K3 → K7 → K8 → [port band 1 can start] → … → cutover`.
K4/K5/K6/K9 branch off K2/K3 and run *concurrently* with the K7→K8 spine; K10 (sim + golden wiring)
lands alongside K8. So the kernel's *wall-clock* is the **longest dependency chain (~K0-K1-K2-K3-K7-K8)**,
not the sum of all 11 bands.

## 4. The two throttles that set the variance

Everything above assumes the two linchpins come in strong. They are the master variables — and both are
being *measured* by the pre-gate Fable mission, which is precisely why that mission is the right first
move:

1. **Golden-harness coverage.** Red-until-parity lets ported subsystems self-verify and auto-merge with
   no human in the loop — *that* is what makes the port a fan-out instead of a serial review queue. High
   coverage → the ~100-PR port compresses to ~1 week. Low coverage → humans must hand-verify each port →
   the port re-serializes on owner attention and the estimate blows out. Coverage % is the single most
   schedule-relevant number in the whole program.
2. **Grammar fit (tier-1/2 fraction).** If ~80%+ of surfaces are generated/declared, ports are
   declaration-writing (fast, uniform, agent-friendly). If the real fraction is lower, each miss is
   bespoke escape-hatch code — slower, and it serializes where a domain's UI is entangled. The grammar
   spike measures this before the kernel is built around the assumption.

**Implication:** the linchpin proof isn't just correctness insurance — it *converts this schedule from a
model into a date.* Spend generously on harness coverage; it directly buys the port's parallelism, the
single biggest chunk of calendar.

> **MEASURED (same day, #1639 — [the evidence package](rebuild-linchpin-validation-2026-07-02.md)):**
> both throttles came in **strong**. (1) Harness coverage: **96% of prefix commands (390/406), 88% of
> slash, 94% of persistent-panel components** — replay-deterministic at full-corpus scale (465 goldens,
> final gating replay 459/459 green + a 5-case named advisory tail);
> the thin dimensions (events 21% · tables 25% · settings mutations 2%) are named per-band curated work,
> not unknowns. (2) Grammar fit: **73% as-specced → 85% with six named amendments; the operator band —
> where the port bulk lives — measures 97%.** On this plan's own model, the center estimate holds:
> the port fans out; it does not re-serialize.

## 5. Where to add parallelism — and where you can't

- **Port (Phase 4): add lanes freely.** Per-subsystem manifest modules are independent files; collisions
  surface at *compile*, not merge (design-spec §10.1 r8); goldens make each port independently
  acceptable. This is the textbook case for 16-wide × multiple-session fan-out. The only ceiling is CI
  throughput (below), not the work.
- **Kernel (Phase 3): you cannot parallelize across the dependency chain.** More agents don't make K3
  land before K2. The two levers that *do* compress it: (a) **fan out *within* a band** (one ultracode
  session per band, its 16 agents splitting the band's modules), and (b) **run the genuinely-independent
  bands concurrently** (K4/K5/K6/K9 off K2/K3). **Compressing the kernel is the highest-leverage
  scheduling move** — it's the floor everything else sits on.
- **The CI/merge ceiling is real and worth managing.** `code-quality` runs the full pytest suite
  (~5 min) per PR; 100 port PRs is a lot of runner-minutes. Mitigations already in place: parallel
  runners, superseded-run cancellation (Q-0126), server-side auto-merge. Watch it during the port —
  if the merge queue backs up, it becomes the binding constraint instead of the work.

## 6. The concrete timeline (tested against "a few weeks")

| Scenario | Assumptions | Active build |
|---|---|---|
| **Best** | harness coverage high, grammar fit ≥85%, kernel bands land clean, owner decisions same-day | **~10–12 days (~1.5 wk)** |
| **Expected** | coverage good-with-gaps, grammar ~75–85%, one or two kernel bands need a second pass | **~2–3 weeks** |
| **Stretch** | coverage forces manual port verification, grammar rework needed, or owner-gate latency stacks up | **~3–4 weeks** |

The **floor is ~1.5 weeks** and it is *hard*: the sequential kernel chain (~1 week) plus a careful
cutover (~1–2 days) cannot be parallelized away. Below that is not reachable by adding agents — only by
making the kernel itself smaller, which the design already resists (the kernel is the whole point).

## 7. Calendar vs. active-build — the human gates are now the pacing item

When agents merge this fast, **the owner-decision cadence becomes the dominant calendar variable**, not
the work. The gates, in order: (1) the **design approval** (pending now), (2) the **go/no-go** after the
linchpin proof, (3) three **sim "why-it-won" ratifications** during the port, (4) the **cutover
reconciliation sign-off**. If each turns around in hours, calendar ≈ active build. If each takes a day,
add ~4–5 days. Keeping these gates fast (pre-reading the artifacts, batching the sim ratifications) is
the cheapest schedule win available to the owner.

## 8. How to actually run it — the parallel-session choreography

1. **Now (pre-gate, parallel) — two Fable missions, both buildable today with no owner gate:**
   (a) the **linchpin proof** — golden harness + grammar proof + go/no-go (handoff §F) — the gate for
   *committing* to the build; and (b) **finalise + ship the AI-memory system** (handoff §B, elevated to a
   Fable mission) — the gate for *starting* the new repo, because design-spec §9.1 makes the substrate-kit
   K0's very first act (it plants the doc skeletons, decision ledger, orientation budget, namespace guard,
   and seam-authority checks). Ship the memory system *before* K0 or the new repo is born without its
   nervous system. ~2–3 days.
2. **Kernel (post-gate, the critical path):** consecutive focused ultracode sessions, **one per band**,
   each turn-key-prompted straight from design-spec §9.1 (the K-band definitions are already
   session-sized). Run K4/K5/K6/K9 as concurrent lanes off K2/K3. This is where owner attention should
   concentrate — it's the floor.
3. **Port (fan-out):** N concurrent ultracode lanes, **claim-per-subsystem** (the existing
   `docs/owner/claims/` discipline), each porting a manifest+service+importer-mapping against the golden
   harness, auto-merging on parity-green. N is bounded by the CI ceiling and the sim-ratification cadence,
   **not by the work** — push N as high as the merge queue sustains.
4. **Cutover (careful, single-threaded):** one deliberate session — importer dry-run → owner
   reconciliation review → freeze → delta → Railway flip → rollback watch (per the `railway-setup-plan`).

## 9. Calibration — the numbers that firm this up

This plan is a *model*; the pre-gate Fable mission returns the two measurements that turn it into a date:
the **golden-harness coverage %** (→ how parallel the port actually is, §4.1) and the **grammar-fit %**
(→ how much of the port is fast declaration vs. slow bespoke code, §4.2). The go/no-go should re-state
§6's scenario the owner is actually in, with those two figures filled in — at which point "a few weeks"
becomes a specific week.

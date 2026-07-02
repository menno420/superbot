# Context-cost telemetry — measure real per-session reads, not modeled ones

> **Status:** `ideas` — captured 2026-07-02 (retention-policy design session, PR #1643; Q-0089
> session idea). Related: [`memory-retention-and-context-economy-plan-2026-07-02.md`](../planning/memory-retention-and-context-economy-plan-2026-07-02.md)
> (whose simulator this would recalibrate), the fresh-rebuild §5.2 "footprint KPI",
> [`orientation-doc-linecap-guard-2026-06-30.md`](orientation-doc-linecap-guard-2026-06-30.md).

**The gap.** The retention simulator's read-cost constants (greps/session, skim words per hit,
boot-route words actually read) are modeled estimates, sensitivity-swept but not observed. The
honest next step the sim itself names: replace modeled constants with telemetry.

**The idea.** Sessions already leave machine-readable traces — the harness writes per-session
transcripts (tool calls with file paths, byte counts, grep patterns and hit counts). A small
parser over those transcripts yields, per session: which docs were Read (and how many lines),
which greps ran and what fraction of hits landed in terminal-badged files, and total
docs-words-consumed vs. code-words-consumed. That gives:

1. **Real calibration** for `tools/sim/retention_policy_sim.py` (replace the 4 assumption-grade
   constants; re-run the search; confirm or move the windows).
2. **The footprint KPI** the rebuild reserves (§5.2): boot-tax + discovery-tax per session,
   trendable across bands — the number the context-economy engine is accountable to.
3. **Route-vs-reality audit**: does the prescribed reading order match what agents actually read?
   (The orientation plan compresses what the route *says*; telemetry shows what sessions *do*.)

**Shape when built.** Read-only script over transcript JSONL (wherever the harness stores them in
the environment at hand — degrade gracefully to "not available here"); aggregates to a small
per-band summary the reconciliation pass can append to its record; zero runtime coupling.

**Why it's worth having.** It closes the loop the memory system preaches everywhere else —
enforce with measurements, not vibes — on the memory system's own most expensive claim (what a
session costs to orient). One session of observed data either validates the retention windows or
gives the exact numbers to retune them.

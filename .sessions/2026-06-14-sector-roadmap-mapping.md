# Session: map the roadmaps/plans onto the 5 planning sectors (dispatch targets)

> **Status:** `complete`

**Branch:** `claude/ecstatic-euler-bslyvd` · **PR:** #877 · **Date:** 2026-06-14 · **Type:** owner-directed workflow substrate (docs-only)

## What this session did
Continued the 5-sector work. The **top layer** (`docs/repo-sector-map.md`, #859) already named the
sectors; this session made them **live, dispatchable queues** by organising the roadmap under them.
**Owner goal:** each sector becomes a clean **Hermes-dispatch target** — *"send a worker to S2 to
continue the BTD6 plan execution"* / *"plan the S3 AI-Memory sector, then an hour later execute it."*
A worker names a **sector + an action** and reads that sector's live `Now`. (Hermes/routine *wiring* =
Q-0137 Thread 1, owner-undecided — structured *for* it, **not built**.)

### Shipped (docs-only — zero `disbot/`)
1. **`docs/roadmap.md` restructured by sector.** New top layer **`## By sector — the live dispatch
   queues`**: a per-sector block (S1–S5) with `Now / Next / Later` + a **Dispatch** line (what *plan*
   vs *execute·continue* mean for that sector) + live-queue pointer. The old "At a glance" horizon
   table is demoted to `## Cross-horizon snapshot`. The 9 area sections become `## Area drill-down`,
   each heading **sector-chipped** (S1 for the 8 bot areas, S2 for BTD6). **Row text preserved** — only
   grouping/headers changed (parallel-safety).
2. **Split the former "Agent ecosystem" lane into its real sectors** — **S3** (mechanism: substrate-kit,
   loop seams, checkers, bot-self-test walker, Hermes bug-triage mechanism) / **S4** (docs content:
   reconciliation content-pass, idea grooming, nav middle/bottom layers, this mapping) / **S5**
   (operations: Railway log-triage, backup-cron verify, dispatch reliability Q-0137 Thread 1, BUG-0011).
   This **populated the two previously-thin sectors** so every sector has a non-empty `Now/Next` — the
   Q-0137 deep-clean **terminal condition**.
3. **Dispatch contract → `docs/repo-sector-map.md`** new `## The sectors as dispatch targets`: the
   action vocabulary (*plan* · *execute·continue*; *reconcile/deep-clean* is sector-spanning, kept
   independent of Hermes) + a per-sector "a worker dispatched here…" table, pointing at the roadmap's
   live queues. Stable contract here; live horizons in the roadmap — one source of truth each.
4. **Reconciled the two taxonomies** — planning S1–S5 ⇄ review A1–A5 cross-pointers in `roadmap.md`
   (sector-index intro) **and** `repo-review-map.md` (a new "Planning/roadmap scoping" bullet + a
   keep-in-sync note in "Updating this file").
5. Close-out: `current-state.md` ▶ flipped (sector mapping DONE → the new dispatch queues) + a stamp
   line; the handoff [brief](../docs/planning/next-session-sector-roadmap-mapping-2026-06-14.md)
   re-badged `historical` (EXECUTED).

## Parallel-session coordination (a bot session ran concurrently)
Owner opened a parallel **bot** session mid-flight. This PR is **docs-only**; the only contact points
are shared ledgers. The watch-items (also in the PR body + `active-work.md`): **`roadmap.md`** is the
one real collision point (restructured whole-file, **row text preserved** → UNION by re-placing an
edited row under its sector header, S1=bot areas / S2=BTD6); `current-state.md` only the ▶ pointer +
stamp; `active-work.md` both append. Cleanest path: land this docs-only PR first (fast CI), rebase the
bot PR onto it. No bot-code overlap.

## 💡 Session idea (Q-0089)
**`scripts/sector_health.py`** — a read-only per-sector **backlog-health telemetry** report: for each
S1–S5, (a) is its roadmap `Now` non-empty? (b) when was a session last logged against it (mine sector
tags / chips)? → one dashboard the deep-clean / dispatcher reads to pick the next dispatch and to catch
a **starving sector** (S4/S5 were thin until today). Turns the owner's "always enough outstanding work,
**balanced**" into a measured trend (the Q-0137 measurement thread) and *enforces* the deep-clean
terminal condition I operationalized here. **Distinct from** the predecessor's `check_sector_map.py`
(coverage/homing) and `check_docs` (reachability) — this measures *attention/freshness*, not structure.
Dedup-grepped `docs/ideas/` + roadmap: no overlap. (Pairs naturally with `check_sector_map.py`.)

## ⟲ Previous-session review (Q-0102)
Reviewing the **sector-map + hook-policy session (#859)** — the direct predecessor that built the top
layer I extended. **Did well:** settled a genuinely hard taxonomy cleanly (the mechanism-vs-content
S3/S4 split on the owner's "the docs are a product of the system" line) and, crucially, **wrote a
handoff brief** (`next-session-sector-roadmap-mapping`) that made this session a clean pickup — the
build-a-structure-*and*-the-brief-that-operationalizes-it pattern is worth keeping standard. **Missed:**
it shipped the map but left the roadmap *unmapped*, so the sectors weren't yet **dispatchable** — naming
sectors ≠ giving each a live queue. That's exactly the gap this session closed; the lesson is that a
new *navigational top layer isn't done until work hangs under it.* **System improvement it surfaces:**
its own Q-0089 idea (`check_sector_map.py`) is still unbuilt and would have *automatically verified* my
sector-homing (no orphan/double-home) — good tooling ideas should be promoted to a concrete **Next**
queue item with a home, not just logged. I did that: it's now an **S3 Next** roadmap row, alongside my
`sector_health.py`.

## Doc audit (Q-0104)
`check_docs --strict` ✓ (263 docs; top-level ratchet 19 unchanged; badge shift `plan 46→45 /
historical 23→24` = the brief re-badge; all links reachable — kept the brief link in current-state so
it stays reachable). `check_current_state_ledger --strict` flags **#872–#876** unrecorded — **expected
between-pass lag** (last recon #870, next due #900; current-state itself tolerates this, and Q-0124
makes it the **reconciliation routine's** job, not a manual docs session's). **Not** a CI gate for
docs-only PRs (CI = `check_docs` + `check_session_gate`). Left for the routine; flagged here. No
`disbot/` touched → `check_quality` not applicable.

**Grooming (Q-0015):** this session *is* the grooming move for the sector lane — it advanced the
captured sector design from "top layer built" to "live, dispatchable, populated queues," and routed two
tooling ideas (`check_sector_map.py`, `sector_health.py`) into the S3 Next queue.

## Context delta (reflection interview)
- **Route miss:** none major — `repo-sector-map.md` + the handoff brief pointed me exactly right. The
  one thing not in any orientation doc: the **exact sector home of each of the ~10 roadmap areas** and
  the agent-ecosystem **split** — I derived it from the sector-map's mechanism-vs-content test. Worth
  pinning once `check_sector_map.py` exists (it'll be the machine-checked homing).
- **Route excess:** read the full Hermes control-plane + autonomous-routines docs to be *aware* of the
  dispatch model; only a fraction was load-bearing (the user said don't over-focus on Hermes). Right
  call to skim, but the **dispatch contract** I needed is small — now captured in `repo-sector-map.md`
  so the next session doesn't re-read the whole control-plane to learn it.
- **Discovered by hand:** docs-only PRs run **only** `check_docs` + `check_session_gate` in CI (from
  the live job log), so the ledger-checker lag wasn't a blocker — useful to know for scoping.
- **Decided alone (within the envelope):** kept the change **non-reordering** (sector chips + a sector
  index rather than physically moving sections) to honor the docs-only/parallel-safety promise; kept
  the dispatch contract *stable* in the sector map and the *live* queue in the roadmap (no duplication →
  no drift). Did **not** build `check_sector_map.py`/`sector_health.py` this session — a `.py` change
  would break the docs-only promise I made to the parallel bot session; queued instead.
- **Weak point of what shipped:** in the drill-down, BTD6 (S2) still physically sits between S1 areas
  (not reordered, by design) — the sector chips + index resolve it, but a purist grouping would move it.
  `check_sector_map.py` + a future reorder can finish that.
- **One change that would have helped:** a machine-readable sector→area map (what `check_sector_map.py`
  will encode) so homing is verified, not asserted.

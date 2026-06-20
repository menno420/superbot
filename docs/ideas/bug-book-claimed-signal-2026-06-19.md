# Bug-book entries need a "claimed / in-progress" signal (close the claim-ledger gap)

> **Status:** `ideas` — captured 2026-06-19 (agent-observed, in-session). Not a plan; not
> approval. Source + merged PRs win. **Subsystem:** none (agent-workflow / meta).
> Extends [`ci-cost-and-duplicate-work-prevention-2026-06-14.md`](./ci-cost-and-duplicate-work-prevention-2026-06-14.md)
> (b) — the claim-ledger convention (Q-0126) — by closing a gap it doesn't cover.

## The observed waste (concrete, this session)

A scheduled dispatch run picked up **BUG-0016** (reconciliation-trigger stale cadence copy),
built the fix, and during a long mid-run gap a **second dispatch run also picked up BUG-0016**
and merged a fix first. The first run's symptom-fix slice was then **redundant** — it had to
rebase onto the concurrent fix and salvage only the novel root-cause half. Real work was
duplicated and largely thrown away.

## Why the existing claim ledger didn't catch it

The Q-0126 claim ledger (`docs/owner/active-work.md`) is the early duplicate-work signal —
*before* a PR exists. But it only works for work an agent **remembers to claim**, and the
**"bugs first, durably"** reflex pulls an agent straight into a `docs/health/bug-book.md` entry
without a claim step. Bug-book entries carry a `Status:` line (`FIXED` / open) but **no
"someone is fixing this right now" state**, so:

- two runs reading the same open bug-book entry both see it as *available*, and
- neither appears in `active-work.md` (the bug was never claimed there).

The ledger covered *planned lanes*; **bug-book pickups are the uncovered path** — and they are
exactly the high-urgency, "jump the queue", grab-it-immediately work most likely to be raced.

## Idea — give a bug-book entry an in-progress state (pick the lightest that works)

1. **Status verb on the entry (recommended, zero-CI).** Extend the bug-book convention: when an
   agent starts a fix, flip the entry's `Status:` to `IN PROGRESS — <branch>, <date>` in its
   *first* commit (the same born-red moment as the session card). A second run reading the entry
   sees it's taken and picks another. Reverts to `FIXED`/open on completion/abandonment. Cheapest,
   greppable, no new file — but relies on the same "remember to mark it" discipline as the ledger.
2. **Auto-mirror bug-book pickups into the claim ledger.** Make "claim it in `active-work.md`"
   an explicit step of the bugs-first procedure, so the *one* dedupe surface stays authoritative.
   No new mechanism — just extends the claim rule to name bug-book entries.
3. **A tiny checker nudge.** `scripts/` guard that warns (advisory, Q-0105 disposable) when a
   branch's diff touches a bug-book entry whose `Status:` is still open-and-unclaimed — turns the
   convention into a reminder instead of pure memory. Overkill unless 1–2 keep slipping.

**Recommendation:** start with **(1)+(2)** as a one-line convention add (no code) — an
`IN PROGRESS` verb on the bug-book entry *and* a claim-ledger line, both in the born-red first
commit. Only build (3) if the convention alone keeps losing the race.

## Caveats / open question

- The deeper fix to *this class* is **shorter run gaps / smaller bug slices** so the collision
  window is narrow — a convention reduces but can't eliminate a true simultaneous start.
- Routing question if built as a rule: it touches the bug-book convention header and the Q-0126
  claim rule → record as a router Q-block (DISCUSS) rather than self-editing the convention,
  since both live in owner-reviewed homes.

## Relates to

- `ci-cost-and-duplicate-work-prevention-2026-06-14.md` — the claim-ledger half (the mechanism
  this extends).
- `lane-scoped-session-state-2026-06-12.md` · `grounding-completeness-claim-primitive-2026-06-14.md`
  — adjacent "make in-flight intent visible" ideas.

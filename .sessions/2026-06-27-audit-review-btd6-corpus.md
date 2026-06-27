# 2026-06-27 — Reviewed the codex unfinished-work audit (PR #1509); shipped a BTD6 regression-corpus expansion

> **Status:** `complete`

**Run type:** owner-directed (*"I asked codex to review the current state of the bot and find some
unfinished work, please review the open PR and see what you can execute"*)

## What this run did

**1. Reviewed PR #1509 (the codex audit) against live source** — per the working agreement, cross-agent
output is *input to verify against shipped source, never an order*. The audit (`docs/analysis/
unfinished-work-audit.md`) is solid and repo-grounded, but was produced in a **degraded environment** (no
`gh`, broken `python3.10` shim) so it could not check live PRs or run the quality suite. Doing the live +
deep-source verification it couldn't tightened its "startable offline" classification:

- **Fishing-gear acquisition depth** (its clean S1 offline item) is **already in flight as PR #1508** —
  ruled out (no duplication).
- **Unwired `light_radius`/`luck` stats** = **BUG-0026**, an explicit **owner gameplay decision**
  (wire-or-remove) — not mine to decide.
- **procedures→skills Batch 2** edits **`.claude/CLAUDE.md`** → off-limits to self-initiate autonomously
  (Q-0106); its Batch 3–4 skills already exist.
- **Advanced Setup PR 3b** is `[needs-live-bot]` (editor rework); the **self-test walker** needs runtime;
  **absence-guard Layer B** is **design-review-gated** by the project's own rule (*"design-first, do NOT
  implement blind"*). All gated for an autonomous offline session.
- `check_quality.py --full` runs **green** here (the verification the audit's env couldn't complete).

Net finding: every *substantive* item the audit flagged "startable" is, on live inspection, claimed /
owner-gated / CLAUDE.md-restricted / design-gated / needs-live-bot. The one genuinely safe, offline,
additive, non-gated lane serving the audit's **#1 critical area (BTD6 correctness)** is the offline
regression corpus.

**2. Shipped — expanded the offline BTD6 regression corpus** (`tests/evals/btd6_corpus.py`), the
project's creds-free *"test all BTD6 questions at once"* layer the README says to *grow from real
failures*. The 14 existing probes were all damage-type/immunity (the #1487 arc); added **4 probes on new
axes**, each pinning the answer-bearing grounding fact for a documented owner-reported live miss so a
data/retrieval regression is caught offline on every PR:

| Question | Pins |
|---|---|
| "what is the damage of a d67 dart paragon" | **BUG-0015** — `d67` is the paragon DEGREE, not a `0-6-7` path |
| "does the monkey buccaneer have a paragon" | absence-claim repro (guard design doc Update 2 — the false "no paragon") |
| "how much is a despo on impoppable" | **BUG-0003** — `despo` shorthand → Desperado, not PMFC |
| "what is the health of an elite lych" | **BUG-0002** — Elite HP from the Elite table, not Standard |

Each verified groundable via `btd6_context_service.build()` before wiring (real retrieval, no model). Two
(`elite_lych_hp`, `despo`) double as live *over-refusal* items in the corpus doc's checklist — the probe
now localizes any live miss to the guard/model layer, not a data-retrieval gap. Doc synced
(`docs/btd6/qa-accuracy-corpus-2026-06-27.md` § "Regression probes from prior fixed live misses").

CI: `check_quality.py --full` green (with changes); `tests/evals/` 144 passed; corpus 14 → 18 probes.

## ⚑ Self-initiated

Owner-directed to *execute startable work from the audit*; **I selected the specific lane** (BTD6
regression-corpus expansion) after verifying the audit's other startable items were claimed/gated (see
above). Additive test-data + docs only — no runtime/`disbot/` change, fully reversible.

## 💡 Session idea (Q-0089)

*A `check_corpus_doc_sync` guard (Q-0105 disposable): assert every `GROUNDING_PROBES` question appears in
the human-readable `qa-accuracy-corpus-2026-06-27.md` and vice-versa.* The corpus module calls itself
*"the machine-readable half of"* that doc, but **nothing enforces the link** — I had to remember to update
the doc by hand this session. A tiny stdlib lint over the two would close that drift class (same shape as
the existing thin-pointer-integrity ideas). Genuinely useful, not built here. *(Dedup-checked: no test
currently references the corpus doc.)*

## ⟲ Previous-session review (Q-0102)

The immediately-prior corpus session (`2026-06-27-btd6-eval-corpus-action.md`, PR #1488) did the hard
part well — a clean shared `GroundingProbe` table feeding both the offline and live layers, so extending
it took minutes. **What it missed:** it seeded the corpus with *only* the #1487 interaction-arc questions,
leaving the bug book's own fixed BTD6 misses (BUG-0002/0003/0015, the absence-claim repro) un-probed —
yet the README explicitly says to *"grow from real failures,"* and the **bug book is the canonical
real-failures source.** **System improvement (applied this session):** when seeding a regression corpus,
draw from the bug book's fixed-entry list, not just the current arc — a "test all the questions" corpus
that omits the project's own logged bugs is incomplete by construction.

## 🧾 Doc audit (Q-0104)

`check_quality --check-only` (incl. `check_docs` + `check_consistency`) green; ledger checker green. New
facts homed: the 4 probes (module) + the regression-probe section (corpus doc), kept in sync. No new owner
decision to route. Ledger: merged-only convention — the next reconciliation pass adds this PR. Backlog
grooming (Q-0015): the 💡 idea above is the forward contribution; no idea-file move this run (contained
single-lane session).

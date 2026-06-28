# Idea: a generated router Q-index (resolve a Q-number without loading 490 KB)

> **Status:** `ideas`. **Not a plan, not approval.** Capture doc. Source + binding contracts +
> `docs/current-state.md` win. **Subsystem:** none (S4/S3 docs tooling).
>
> **Session idea (2026-06-28, Q-0089, from documenting the open-question sweep + deciding Q-0210).**

## The friction

`docs/owner/maintainer-question-router.md` is **~490 KB / 215 Q-blocks** and now **exceeds the
file-read size limit** — this session had to read it in offset/limit slices just to find the open
questions, and every agent that needs to resolve a single `Q-0NNN` reference (there are ~9,000 across
1,307 files) pays that cost. Q-0210 decided the structural fix (archive old blocks on the
reconciliation cadence), but archiving is coarse and periodic; it doesn't help an agent that needs to
look up *one* answered Q **today** without loading the whole file.

## The idea

A tiny stdlib generator — `scripts/build_q_index.py` → `docs/owner/maintainer-question-router-index.md`
— that parses every `### Q-0NNN — …` header (live router **and** the Q-0210 archive) and emits **one
line per Q**: `Q-0NNN · <title> · <status: PROPOSED/ANSWERED/DEFERRED/SUPERSEDED> · <Home: pointer> ·
<file it lives in>`. An agent resolves a Q-number by grepping the ~215-line index instead of the
490 KB body, and only opens the full block when it needs the reasoning.

- **Status** is derivable from the block's callouts (the `> **ANSWERED …**` / `> **PROPOSED …**` /
  `> **DEFERRED …**` lines this session's convention already uses).
- **Home** is the existing `**Home:**` line each block carries (§7 routing).
- Regenerate it in the reconciliation pass (next to the archive step) so it never drifts; a warn-only
  checker can assert every `Q-0NNN` header appears in the index.

## Why it's worth having

It's the cheap, *queryable* complement to Q-0210's archive: archiving controls **size**, the index
controls **findability**. Together they make the router scale without agents paying the full-file read
cost — and the index doubles as a human "what was decided, and where did it land?" overview. Pure
stdlib, read-only, disposable (Q-0105 — delete if it drifts or goes unused).

## Related

- **Q-0210** (router stays canonical/append-only; archive old blocks) — this is its findability half.
- **Q-0107** (reconciliation pass owns ledger/index maintenance).
- `current-state-archive.md` + `completion_scoreboard.py` (generated-overview precedent).

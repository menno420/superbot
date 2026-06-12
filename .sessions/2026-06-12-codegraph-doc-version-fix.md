# 2026-06-12 — CodeGraph health check + doc version-pin fix

> **Status:** `audit`

**PR:** opened this batch (codegraph-usage version fix)
**Branch:** `claude/codegraph-doc-version-fix`

## Context

Owner: "see if you can find out what's wrong with CodeGraph — maybe nothing, but I thought
agents had problems after we updated it" (the 3.10.0 → 3.11.2 bump on 2026-06-08).

## Findings — CodeGraph itself is healthy

- Live-tested at 3.11.2 this session: graph builds (35,912 nodes / 64,181 edges at SessionStart),
  `list_functions validate_registry` resolves correctly, `check` returns accurate
  complexity/boundary analysis (boundaries pass, no cycles). **No functional regression found.**
- The "problems" agents hit are the two **documented, version-independent** issues, not a 3.11.2
  regression:
  1. **Availability gotcha** — on a cold container the first `npx -y` download blips and the hook
     reports "CLI unavailable", silently disabling CodeGraph for the session (CLAUDE.md documents
     this; two session logs confirm it: 2026-06-09/06-10). Environmental, clears on retry.
  2. **Inherent false positives** — `dead-unresolved` (~100% FP; `validate_registry` confirmed),
     name-collision caller merges, empty `callees`, invisible decorator/event edges. These are the
     5 critical CLAUDE.md rules and existed identically at 3.10.0.

## Findings — a real bug, now fixed

`docs/codegraph-usage.md` was **stale at 3.10.0**: every rebuild/troubleshoot command said
`npx -y @optave/codegraph@3.10.0 …` while the live pin (`.mcp.json` + SessionStart `CG_PKG`) is
**3.11.2**. An agent following the doc would build/probe with the *wrong, old* version → a graph
that can differ from the live MCP server. Bumped all command refs to 3.11.2; kept the historical
"evaluated at 3.10.0" note but added the current-pin callout. (Drift since the 2026-06-08 bump —
4 days unnoticed.)

## Verification

- `check_docs --strict` ✓. Live CodeGraph MCP tools verified working. Docs-only.

## Grooming move

None — directed investigation + bug fix, not backlog grooming.

## ⟲ Previous-session review (Q-0102 — reviewing the #735 governance batch)

- **What it did well:** cleanly encoded Q-0106 (propose-don't-self-edit) and tied it to the
  permission-prompt rationale; folded #734 into the ledger.
- **What it missed:** nothing in that batch — but this investigation shows a *class* of drift the
  system doesn't yet guard: a version pin in a doc silently diverging from the canonical pin
  (`.mcp.json`). The 3.10.0→3.11.2 doc lag sat unnoticed for 4 days.
- **System improvement surfaced:** a version-pin drift check (docs vs. the canonical pin). →
  this batch's 💡 idea.

## 💡 Session idea

**Idea:** A `check_pin_drift.py` (Q-0105 disposable guard) that greps docs for pinned-package refs
(e.g. `@optave/codegraph@X.Y.Z`, `youtube-transcript-api<1.0`) and flags any that disagree with the
canonical source (`.mcp.json`, `requirements*.txt`, the SessionStart `CG_PKG`).
**Why:** the stale CodeGraph version commands sat in the canonical doc for 4 days because nothing
cross-checks doc-stated pins against real pins. This closes that gap the way the ledger/log checks
closed theirs — pin drift becomes a checkable signal, not a thing someone happens to notice.
Advisory, git/stdlib, carries its own delete-if-unreliable header. _Small — recorded here._

# 2026-06-14 — born-red session merge-gate (Q-0133)

> **Status:** `complete`
<!-- born-red flow (Q-0133): was `in-progress` (PR born red); flipped to `complete` as the
     deliberate final close step so the merge-gate goes green and auto-merge fires. -->

**PR:** [#849](https://github.com/menno420/superbot/pull/849) — enforce the owner's "hold the
merge until the session flips its plan/outcome doc green" rule. **Branch:**
`claude/session-gate-born-red`.

This is the second piece of the 2026-06-14 session (the first — hardening **P1-2**,
health findings lifecycle + retention — shipped as **#843** + **#846**). The owner asked
to fix auto-merge firing too quickly, having hit exactly that on #843.

## What's about to happen / what was done

- **Root problem:** native auto-merge (Q-0123) merges a `claude/*` PR the instant **Code
  Quality** is green. A session pushing code first and close-out docs second merges a
  *partial* PR — the #843 race (merged without its ledger entry → stranded #846).
- **Owner's mechanism (refined live):** one per-session file that is **both** the
  start-declaration ("what's about to happen", visible to parallel/next sessions on the
  open PR) **and** the end-record ("what happened"), whose status gates the merge. That
  file = the existing `.sessions/<date>-<slug>.md` log.
- **Shipped:**
  - `scripts/check_session_gate.py` — fails when a PR *adds* a session card whose
    `> **Status:**` badge isn't a ready token; born-red at `in-progress`, green at
    `complete`. Engage-when-present (a PR adding no card is not gated → routines /
    workflow-authored PRs never deadlock). Only newly-*added* cards are inspected, so
    re-badging an old log to `historical` never holds a PR. +11 unit tests.
  - `.github/workflows/code-quality.yml` — a PR-only `Session merge-gate` step (the
    required `code-quality` check carries the gate; no branch-protection change needed).
  - `.claude/CLAUDE.md` § Session & plan workflow — the binding rule (open born-red first,
    flip ready last); supersedes "open the PR ready" for `claude/*` sessions.
  - `docs/owner/maintainer-question-router.md` **Q-0133** — the decision + rationale +
    the engage-when-present strictness choice (and the airtight-later follow-up).
  - `.claude/skills/session-close/SKILL.md` — the flip-to-`complete` close step + fixed a
    stale "audit badge token" instruction (real cards close at `complete`) + added the
    missing Status line to the template.
- **Dogfooded:** this PR is born red by this very card (`in-progress`) — proving the gate
  on its own change — then flipped to `complete` as the final step.

## Decisions recorded

- **Q-0133** (owner-directed, applied in-session per the Q-0106 exception): born-red
  session-card merge-gate; engage-when-present strictness (safe for the autonomous loop),
  tightenable to airtight later.

## Left open / next session

- **Tighten to airtight** (absent card = red for `claude/*` PRs, with carve-outs for
  workflow-authored PRs) once routine adoption of the born-red card is proven reliable.
- A SessionStart-hook reminder to *create* the born-red card could make adoption automatic
  (left out of v1 to keep the hook surface untouched).

## 💡 Session idea

**Idea:** have the SessionStart hook auto-scaffold the born-red session card (a stub
`.sessions/<date>-<branch>.md` at `in-progress`) so step 1 of every session is done for
free, and the gate becomes effectively airtight without anyone remembering to create it.
**Why:** the engage-when-present gate's one gap is a session that never creates a card;
auto-scaffolding closes it at the source while keeping the file the owner's
start+end+coordination artifact. Small hook change; pairs with the airtight follow-up.
[small — recorded here; promote to `docs/ideas/` if the airtight tightening is taken up]

## ⟲ Previous-session review

The previous session was this same session's P1-2 work (#843 → #846). It did the
engineering well (real-Postgres-verified SQL, sole-writer discipline, pattern reuse) but
**surfaced this very bug by living it**: it pushed code first and session-close docs
second, and auto-merge merged #843 without its ledger entry — a stranded #846 follow-up.
That is the strongest kind of system feedback: the workflow's own gap caught in practice.
The concrete improvement is exactly what this PR ships — make "the ledger/close-out docs
must be in the same push as the code" an *enforced* born-red gate rather than a discipline
rule (the journal's own standing principle: a doc claim mirroring code state should be
CI-backed, not refreshed by per-session human discipline — Q-0132). System now self-heals
the class instead of relying on the next session to notice.

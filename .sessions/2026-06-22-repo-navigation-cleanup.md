# 2026-06-22 — Repo navigation cleanup: stale claims + conflicting instructions

> **Status:** `complete` — owner-directed cleanup pass. The maintainer reports the repo
> "feels a little messy" after a burst of merges + the now-mostly-fixed merge problems, and
> wants it easy to navigate and work in **without conflicting claims or instructions**.
> Owner-directed (Q-0191) → merge immediately on green; no `needs-hermes-review`.

> **Run type:** `manual · owner-directed`

## What I'm about to do

A docs/orientation hygiene pass (no `disbot/` runtime code). Confirmed + candidate scope:

- **Prune stale `active-work.md` claims.** Both "Active claims" are merged work:
  `claude/modest-gates-0ble76` (CI-strand fix → **#1267 merged**) and
  `claude/funny-franklin-mjvqrx` (BUG-0023 → **#1272 merged**). The claim ledger is the
  early duplicate-work signal — stale claims defeat its purpose (Q-0166 drift-on-sight).
- **Reconcile genuinely conflicting / contradictory instructions** surfaced by a docs sweep
  across `.claude/CLAUDE.md`, `.claude/rules/`, `docs/collaboration-model.md`, the journal,
  `docs/owner/*`, and the binding contracts — where a reader can't tell which guidance is
  current. CLAUDE.md *content* stays propose-not-edit unless the owner directs the specific
  change in-session (Q-0106); anything load-bearing there → a router DISCUSS Q, not a self-edit.
- **Remove resolved-but-still-present merge/CI scaffolding** cluttering active reading paths,
  now that the merge problems are mostly fixed.

## What shipped

- **Pruned both stale `active-work.md` Active claims** — `claude/modest-gates-0ble76`
  (CI-strand fix, **#1267 merged**) and `claude/funny-franklin-mjvqrx` (BUG-0023, **#1272
  merged**). Both were finished, merged work still sitting in the live claim ledger, which
  exists to be the *early* duplicate-work signal — stale claims defeat its whole purpose
  (Q-0166 drift-on-sight). Replaced with this session's lane claim. (Open PR #1274 is
  independently pruning the funny-franklin line; UNION-resolves cleanly if it lands first.)

## What I checked and deliberately did NOT change

A docs sweep (Explore agent) flagged six candidate "conflicts." Verified each against
source — most were over-flagged, and the rest are out of this session's free-edit scope:

- **"Open PR READY" (Q-0103) vs "open born-red card" (Q-0133) in CLAUDE.md** — *not* a true
  contradiction. They are **orthogonal axes**: READY = the GitHub *draft-state* (non-draft);
  born-red = the *session-card status badge* (`in-progress`) that holds the CI merge-gate. A
  PR is opened non-draft **and** born-red. The born-red bullet already says "open it born-red,
  flip it ready last," explicitly reconciling them. The only residual friction is that the
  earlier "Open it READY" bullet lacks a forward-pointer to that refinement ~40 lines down —
  a **clarity nit, not a conflict**. CLAUDE.md content is **propose-first** (Q-0035/Q-0106),
  so flagged for the owner rather than self-edited.
- **`autonomous-routines.md` reconciliation-procedure pointer (CLAUDE.md)** — sweep called it
  stale; **verified false** — the full step-by-step procedure *does* live there (the routine's
  pasted STEP 1–2 instructions). No change.
- **`merge = deploy` stated in CLAUDE.md + `production-deployment.md`** — CLAUDE.md already
  names `production-deployment.md` as canonical and links to it, so this satisfies
  one-fact-one-home (rule + pointer-to-home). No change.
- **`self-merge on green` vs `auto-merge on green` phrasing / Q-0084 "manual-merge envelope"
  language** — only present in **append-only historical records** (`active-work.md` "Recently
  cleared" lines, the question router). Those are a *record of what each past session said*,
  not live instructions an agent acts on; rewriting history is churn, not cleanup. The one
  place it was a *live* instruction (Active claims) is fixed by the prune above. No change.

## Findings / decisions

- **The perceived "mess" is not mechanical drift.** `check_docs --strict`,
  `check_current_state_ledger --strict`, and `check_reconciliation_due` are all green; the
  ledger is in sync; the container is fresh with `main`. The real residue was the stale claim
  ledger (now fixed) + one CLAUDE.md clarity nit (flagged, propose-first).
- **Decision made alone — minimal, in-bounds scope.** I declined to churn CLAUDE.md or the
  append-only router/active-work history. Cross-agent (Explore) findings are input to verify,
  not orders (Q-0120) — verifying them is exactly what shrank a six-item punch-list to one
  real fix + one owner-facing nit.

## Flagged for maintainer

One genuine clarity nit, left for your call because CLAUDE.md is propose-first: the
"Always create a PR every session … Open it READY, not draft" bullet has no forward-pointer
to the later "open it born-red, flip it ready last" refinement, so a reader briefly sees
"open ready" without the born-red context. A one-line parenthetical cross-link would close
it. Say the word and I'll apply it under the Q-0106 in-session exception (+ record the Q).

## 💡 Session idea

**A `check_active_work.py` staleness guard (Q-0105-disposable).** The claim ledger went
stale because nothing flags an Active claim whose branch/PR already merged. A tiny stdlib
check that parses `active-work.md` Active claims, extracts each `claude/<branch>`, and warns
when that branch is already merged into `main` (via `git branch --merged` / a PR-state read)
would turn "an agent eventually notices the stale claim" into a SessionStart/CI nudge — the
same detector→guard shape the repo already rewards (ledger checker, lane-overlap scan).
Dedup-checked: `check_lane_overlap.py` reads the ledger for *overlap* but doesn't assert
*freshness* (merged-branch staleness); this is the freshness complement.

## ⟲ Previous-session review (Q-0102)

The previous session (BUG-0023 slash-scan coverage, #1272) was strong: it *disproved* the
bug-book's own root-cause hypothesis before fixing, which is the Q-0120 instinct working as
intended. **Where it (and the broader cadence) could improve:** it left its Active claim in
`active-work.md` after the PR merged — exactly the staleness this session had to clean. The
session-close checklist drives `current-state` + the session log but doesn't explicitly say
"clear your Active claim," so claims accumulate. **System improvement (initiated):** the
`💡 Session idea` above (a `check_active_work.py` freshness guard) mechanizes the missing
session-ender so the next session doesn't inherit a stale ledger.

## 📤 Run report

- **Did:** repo navigation/hygiene pass — pruned stale Active claims, verified the docs-sweep
  findings against source · **Outcome:** shipped (this PR, auto-merge on green)
- **Run type:** `manual · owner-directed`
- **⚑ Owner decisions needed:** one optional clarity nit in CLAUDE.md (see *Flagged for
  maintainer*) — apply-on-request, propose-first.
- **⚑ Owner manual steps:** none — docs-only; merged = deployed (no runtime change).
- **⚑ Self-initiated:** no — owner-directed ("check if there's anything that should be
  cleaned up"). Scope kept minimal + reversible by design.
- **↪ Next:** if the owner wants it, apply the CLAUDE.md forward-pointer; otherwise the
  ungated build lanes (current-state ▶) are untouched.

## ⟳ Doc audit (Q-0104)

`check_docs --strict` + `check_current_state_ledger --strict` green. No merged-PR ledger
entries to add (docs-only session; merged-PRs-only convention). No new owner decisions for
the router (the CLAUDE.md nit is *flagged*, not decided). `active-work.md` is now free of
stale claims.

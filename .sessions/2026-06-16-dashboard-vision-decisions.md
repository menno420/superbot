# Session (cont.) — solidify the dashboard finalized-vision plan with owner panel decisions

> **Status:** `complete`

## What I'm about to do (born-red declaration, Q-0133)

Continuation of the dashboard finalized-vision session (PR #1002, merged). The owner asked me to put the
plan's open forks to him via the question panel "so we can solidify this plan", then answered **8**
questions across two panels. This PR records those decisions durably — into the vision doc
(`docs/planning/dashboard-vision-finalized-state.md`) and the question router.

**The 8 decisions (owner, 2026-06-16):**

1. **Homepage** → **hybrid router landing** (newcomers → product tour; logged-in → straight to workspace)
   — *not* the pure product-site default.
2. **Manifest spine** → **yes, sequenced before the editors** (Q-0162 fork 1 answered).
3. **Owner zone** → **owner-only now, but scope-shaped** for later delegated roles (Q-0162 fork 2 answered).
4. **First live edits** → **help → settings → aliases/routing → panels**.
5. **Authority UX** → **cautious edits, open info** (show edit controls only when near-certain allowed;
   show read-only info + authority preview freely).
6. **Mobile** → **FULL management on mobile** (not just oversight) — a design constraint on every editor.
7. **Panel editor** → **last**, after the simpler editors.
8. **Setup** → **already completed and confirmed working** (owner's own answer) — the Discord OAuth +
   control-token Railway gating is **done**, so the live-editing path is **unblocked**, not a "don't rush"
   wait. This un-gates roadmap phases C/E/F's owner-setup dependency.

**Plan:** apply 5/6/8 (the genuine *changes*) + confirm the rest in the vision doc; mark Q-0162 DECIDED
(its two forks); add **Q-0163** for the other six panel decisions (preserve questions + owner choices).
Docs only; no `disbot/`. Will resync + renumber if a parallel session grabs Q-0163 first (the Q-0162→…
collision lesson from last PR).

## What shipped (PR #1006 — docs only)

- **`dashboard-vision-finalized-state.md`** — recorded all 8 owner panel decisions: rewrote the
  **Homepage** section → hybrid router landing; the **Mobile** section → full management on mobile
  (first-class per-screen constraint); added a **Decisions (owner question-panel)** table; updated the
  **roadmap gate column**; sharpened the **manifest decision** wording.
- **Router** — **Q-0162 → DECIDED** (both forks chose the agent recommendation); new **Q-0163** (the
  other six panel decisions, preserved as asked + chosen).
- **Synced to main** (owner directive) — merged origin/main cleanly, which pulled in the parallel
  **#1005** review session's **§ Reviewer note** + the write-side activation. **Reconciled the plan with
  that review** (see below).

## ⟲ Reviewing the previous session's review of our plan (owner directive)

The owner asked me to "sync to main and review the previous session's review of our plan." That review is
**#1005's § Reviewer note & post-activation status** (by the session that *built + activated* the control
panel: #993 endpoints · #996 OAuth+editors · #1001 IPv6 bind).

**My assessment: the review is correct, grounded, and high-value — adopt it.** It is verified against
shipped PRs, not speculation. Its core finding matters: the write side went **live in production right
after I wrote the plan**, the build jumped **C-auth → F-writes and skipped Phase E** (the current-value
read endpoints), so **the live editors write blind**. That is a real, important correction my original
"Status today" cells missed (the exact status-freshness drift the reviewer names in their Q-0102).

**What I did about it (reconciled the plan so it's internally consistent):**
- Fixed the **roadmap table** the reviewer deliberately left stale: **C** 🟡 partly-shipped-live (richer
  read workspace still open) · **F** ✅ shipped + LIVE · **E** ⚠️ **skipped → now the top next priority**
  (editors write blind until the GET endpoints land) · added a "Status reconciled (2026-06-17)" note.
- **Sharpened the manifest decision** per R2: it gates **command-management + the panel editor (H)**, not
  the already-shipped settings/help/routing editors (already-typed seams).
- Folded R4 (**Railway IPv6-only** bind gotcha) into § Security, and R3 (**rate-limit + CSRF token**
  live-hardening gap) as an explicit near-term item.

**One thing I'd push back on slightly:** nothing — the review is accurate. The only nuance is that R1
(Phase E now) and the owner's Q-0163 "first-edit order" aren't in tension: E is about *reads that make any
editor non-blind*, F is about *which editors*; the plan now states both. Net: the plan is stronger for the
review, and the two sessions' findings reinforce each other.

## 💡 Session idea (Q-0089) — a "Status today" cell freshness guard

Both #1002 (mine) and #1005's review converged on the same gap: **living plan/status cells go stale within
hours in a fast parallel-merge repo.** Idea: extend the proposed handoff-freshness guard to also scan
`docs/planning/**` for **status-claim cells** (`✅ shipped`, `Status today`, `gated`) whose subject
matches a **more-recently-merged PR** that flips that status — i.e. flag "this cell says *gated* but PR #X
shipped it." It's the in-doc-cell sibling of the ledger/handoff guards (#992 + #1005 both gestured at it).
Small, stdlib, decided-lane; recorded here, promote to `docs/ideas/` when the handoff guard is built.

## 📋 Documentation audit (Q-0104)

`check_docs --strict` green throughout. All 8 decisions are durable (vision doc + Q-0162/Q-0163); the
reviewer reconciliation is applied in-doc; the Q-number-collision lesson is in the #1002 log. Did not
touch `current-state.md` ledger (recon-routine territory, Q-0124). Nothing from this session lives only in
chat. *(Q-number watch: grabbed Q-0163; will renumber on resync if a parallel session took it first — the
#1002 collision lesson.)*

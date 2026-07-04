# 2026-07-02 — Ideas harvest from today's session arc (owner-requested)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Docs-only; `check_docs --strict` ✓, ledger ✓ (benign lag). PR #1641.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1640 merged).

## What I'm about to do (intentions — as declared born-red)

Owner asked for ideas/improvements distilled from today's arc (design spec + judge panel →
external reviews → Railway audit → Q-0213 automation grant). Dedup against the backlog, capture
the genuinely new ones.

## What shipped

Five deduped idea captures + README index entries:

1. **`tried-before-ledger`** — negative operational results as first-class greppable memory
   (from the wait-for-CI near-miss: one line of owner history beat a correct-looking config
   analysis and lived nowhere in the repo). Substrate-kit template candidate.
2. **`wire-level-live-bot-loop`** — Galaxy-Bot-driven real-gateway testing in a test guild;
   dissolves the `[needs-live-bot]` startability gate and doubles as the Phase-0.5 golden-harness
   Discord driver. Explicitly complementary to the in-process `bot-self-test-walker` (checked for
   overlap; different mechanism, honest `author.bot` caveat recorded).
3. **`continuously-verified-backups`** — R6 restore drill promoted from one-shot task to a
   scheduled restore-verify workflow (pg_dump is now the *only* backup layer).
4. **`shadow-clone-rehearsal`** — agent-operated Railway shadow of the current bot on a restored
   snapshot: proves restore end-to-end, rehearses the Phase-5 choreography early, gives the golden
   harness a consequence-free capture target (spend-flagged).
5. **`no-transcript-secret-plumbing`** — store-to-store secret moves with hash receipts, never
   through transcripts — the safety half of the Q-0213 grant, needed concretely by R-3 bootstrap
   and the DATABASE_PUBLIC_URL rotation class.

## Context delta

- The best ideas in this batch are **couplings of today's new capability (Q-0213) with existing
  gates**: live-bot loop ↔ `[needs-live-bot]` tag; shadow clone ↔ Phase-5 choreography; secret
  plumbing ↔ "never rely on the owner to enter values." A new grant's value shows up as *which
  standing blockers it dissolves* — worth asking explicitly after every authority change.
- Dedup discipline paid off: the live-bot idea nearly duplicated `bot-self-test-walker`; reading
  it first turned a duplicate into a sharper, complementary capture (in-process vs wire-level).

## 🛠 Friction → guard

None encountered — docs-only session; the born-red gate red on the card commit was the mechanism
working as designed.

## 💡 Session idea (Q-0089)

This session *is* an idea batch; the one I believe in most (and would build first) is the
**tried-before ledger** — smallest build, prevents the scariest failure class (confidently
re-running a known-bad experiment), and generalizes into the substrate kit.

## ⟲ Previous-session review (Q-0102)

Previous session (#1640, the automation grant): executing with per-change read-back and recording
the grant in three homes (router / ops doc / plan) was right — nothing needed re-explaining when
the owner returned. What it missed: when R2 hit plan-gating it recorded "upgrade is the lever" but
attached **no price** — the §7.5 owner decision still lacks the number that would make it
decidable in one glance. **Concrete improvement:** when a blocked capability turns into an owner
decision, attach the concrete cost/benefit delta (plan price, storage rate) in the same edit —
a decision without its price is a question, not a decision surface.

## 📤 Run report

- **Did:** distilled today's arc into five deduped idea captures · **Outcome:** shipped
- **Shipped:** #1641 — 5 idea files + README index
- **Run type:** `manual` (owner-directed)
- **⚑ Owner decisions needed:** none new — if any harvest idea should jump the queue, say which
  (the tried-before ledger and the restore-verify workflow are both small/decided-lane and could
  ship next session; the shadow-clone rehearsal is the one that costs real money and stays
  flag-first).
- **⚑ Owner manual steps:** none (the artifact-retention dropdown from #1640 still stands).
- **⚑ Self-initiated:** none (owner-requested harvest; captures, not builds)
- **↪ Next:** unchanged — design-spec owner gate · Phase 0.5 · R6/restore-verify.

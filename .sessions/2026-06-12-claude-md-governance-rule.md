# 2026-06-12 — CLAUDE.md governance: propose, don't self-edit (Q-0106)

> **Status:** `audit`

**PR:** opened this batch (CLAUDE.md self-edit governance)
**Branch:** `claude/claude-md-governance-rule`

## Context

Owner directive (voice), closing the autonomy-safety thread: for full autonomous improvement,
agents must **never edit `CLAUDE.md` on their own initiative** when they have an idea — they
**document the proposal for live review**. But the instructions, while binding *for* a session,
are **not locked/pinned** — they are still in development like the rest of the system.

## What was done

- **Q-0106 (binding governance rule).** `.claude/CLAUDE.md` Working agreement now states:
  CLAUDE.md is **binding for a session but not pinned**; agents **propose** rule changes via a
  **router Q-block (DISCUSS lane)**, never self-edit; the **one exception** is a maintainer-
  directed in-session change (the owner *is* the live reviewer, so it applies directly with a
  provenance Q). In a **fully autonomous session, CLAUDE.md is read-only** to the agent — it
  only writes proposals. Recorded in the router (Q-0106).
- This is the governance counterpart to the self-audit loop (Q-0102/Q-0104) and the reason the
  `Edit(.claude/CLAUDE.md)` permission prompt is deliberately kept (it is the live-review gate
  when a human is present — `claude-code-hooks-and-plugins.md` § Permissions posture).

## Verification

- `check_docs --strict` ✓ · `check_session_log --strict` ✓ · `check_current_state_ledger --strict` ✓.
  Docs/config only.

## Grooming move

None — this batch *is* a directed governance change, not backlog grooming. Backlog was groomed
across the #730/#733/#734 batches this session.

## ⟲ Previous-session review (Q-0102 — reviewing the #734 batch)

- **What it did well:** built the ledger guard, found + reconciled real pre-existing drift, and
  landed Q-0104/Q-0105 — each rule change carrying a provenance Q.
- **What it could have done better:** the #734 batch accreted scope mid-flight (drift fix → ledger
  tool → Q-0104 → Q-0105) across several pushes → several CI runs. Acceptable when directives
  arrive live, but the recurring "batch keeps growing" pattern is worth naming.
- **System improvement surfaced:** every rule change this session shipped with a provenance Q —
  but nothing *checks* that. → captured as this batch's 💡 idea (provenance self-check), which
  directly enforces Q-0106's "rules ship with a provenance Q."

## 💡 Session idea

**Idea:** A `check_claude_md_provenance.py` (Q-0105 disposable guard) that verifies every binding
rule in `CLAUDE.md` citing a `Q-NNNN` resolves to a real router entry, and flags rule bullets added
with **no** provenance Q at all.
**Why:** Q-0106 requires every rule change to ship with a provenance Q; this makes that
self-checking — the *constitution's* provenance becomes verifiable the way the ledger and session
log now are. It would catch a rule slipped in without owner provenance (the autonomous-self-edit
failure mode Q-0106 guards against). Advisory, git/stdlib, carries its own delete-if-unreliable
header. _Small — recorded here; promote to an idea file if it grows._

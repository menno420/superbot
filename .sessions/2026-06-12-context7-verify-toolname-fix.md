# 2026-06-12 — Context7 verification + tool-name fix

> **Status:** `audit`

**PR:** opened this batch (Context7 verify + tool-name fix)
**Branch:** `claude/context7-toolname-fix`

## Context

Resumed after the Context7 adoption (#737) landed and the MCP server went live. Per Q-0105
(verify a newly-adopted tool against ground truth before trusting it), ran the first real
verification — which surfaced a lingering config bug.

## What was done

- **Verified Context7 works (1×, accurate).** `resolve-library-id discord.py` → `/rapptz/discord.py`
  (correct canonical repo). `query-docs` returned *current* discord.py 2.x API: the post-2.0
  button-callback signature order **and** the Components-V2 `LayoutView`/`Container`/`Section`
  APIs (discord.py 2.6 — newer than the model's training data). Exactly the "API-from-memory"
  bug class being solved. Recorded in `mcp-servers.md` (Verified 1×; a few more to graduate).
- **Fixed a real config bug the verification caught:** the live tool is `query-docs`, but
  `.claude/settings.json` pre-allowed `mcp__context7__get-library-docs` (wrong name, from #737) —
  so `query-docs` was prompting instead of pre-allowed. Fixed the allow entry + the
  `mcp-servers.md` usage section. The typo had survived #737 and the #742 seams session.

## Re-orientation note

Synced stale local main first: the repo advanced a lot since #738 — the autonomous-loop seams
(`review`/`dispatch` Hermes skills, `check_phase_gate.py`, the dispatch-bridge doc, Q-0113/0114)
landed in #742, and the first Q-0107 reconciliation pass ran at #741 (cadence rule is in use).
The recommended "Hermes-reviewer seam" is already built — so this focused fix is the genuinely
useful, non-stale contribution.

## Verification

- `.mcp.json` + `settings.json` valid JSON · no stale `get-library-docs` refs remain ·
  Context7 live-tested · `check_docs`/`check_session_log`/ledger green.
- **#746 left for next-session ledger reconciliation** (the documented one-session lag) — main had
  active parallel sessions (#743–#745+), so editing the high-collision `current-state.md` at
  session-end was avoided; `check_current_state_ledger` will surface #746 next session.

## Where to continue (next session)

1. **Context7 (this thread):** verify it a **few more times across sessions** (per Q-0105) to
   graduate it out of "unverified" → load-bearing. Reach for `query-docs` on any `discord.py` /
   `asyncpg` work; if it ever returns stale/wrong docs, trip its kill-switch (`mcp-servers.md`).
   The 💡 below (a Context7 value/verification log) would make that graduation evidence concrete.
2. **The built-but-unexercised autonomous-loop seams (#742):** `review` + `dispatch` Hermes
   skills + `check_phase_gate.py` exist now but haven't been run end-to-end. A real
   dispatch→build→review→approve dry-run is the natural next milestone.
3. **Project-wide:** the live queue is the **decade queue** in current-state.md's ▶ Next action
   (P0 hardening + the Q-0108–Q-0112 safety/community lane); next Q-0107 reconciliation pass at #750.

## ⟲ Previous-session review (Q-0102 — reviewing #742, the autonomous-loop seams)

- **What it did well:** built the review + dispatch seams + phase gate — real, substantial
  progress toward the autonomous loop, exactly the next step that was queued.
- **What it missed:** it built *on* Context7 without anyone having actually verified Context7
  worked (Q-0105 was written but not exercised), and it carried forward the `get-library-docs`
  permission typo from #737. A newly-adopted tool went 2 sessions unverified.
- **System improvement surfaced:** the Q-0105 "verify before trusting" obligation needs a
  *trigger* — nothing reminds a session that an unverified tool is in play. → 💡 below.

## 💡 Session idea

**Idea:** A `context7` value/verification log — a short running tally in `mcp-servers.md` where a
session appends one line whenever Context7 gave info that *corrected or updated* the model's memory
(like today's Components-V2 finding), or whenever it was stale/wrong.
**Why:** it does double duty — it accumulates the Q-0105 "verified across sessions" evidence
concretely (so the tool can graduate out of "unverified"), and it quantifies whether Context7
actually earns its keep (justifying a paid key, or tripping its kill-switch). Turns "we think it
helps" into a recorded fact. Cheap (one line per use). _Small — recorded here._

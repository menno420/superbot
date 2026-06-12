# 2026-06-12 — The first Q-0107 reconciliation pass: map every plan, set the decade queue

> **Status:** `audit`

**PR:** [#741](https://github.com/menno420/superbot/pull/741) (merged in-turn)
**Branch:** `claude/stoic-wright-varkww`

## Context

Task: "review the plans added in the latest PRs and map every plan into the existing
roadmaps." Verified at start: merged PRs had crossed **#740** with the marker at #737 —
i.e. this *is* the first Q-0107 docs-only reconciliation + planning pass, so the task and
the standing cadence were the same work. The owner stated mid-session that a **parallel
Hermes session** is running — noted in the pass record; UNION-resolve at merge.

## What was done

- **[`planning/reconciliation-pass-2026-06-12.md`](../docs/planning/reconciliation-pass-2026-06-12.md)**
  — the pass record: §2 plan-inventory table (every doc added in #715–#740 → routed home);
  §3 priorities restated; §4 the next ~9 PRs (hardening P0s · backup posture · the
  Q-0108–Q-0112 safety/community first slices) + the deliberately-deferred list; §5 pruned.
- **`roadmap.md`** — two new lanes: **Server safety & community platform** (the approved
  Q-0108–Q-0112 set, plan-first, with the `server_logging`/`guild_lifecycle` reuse pins)
  and **Agent ecosystem / workflow** (Q-0107 cadence · Stage 0 gated · Q-0096 remainder ·
  the three vision captures). At-a-glance Now/Next/Later rewritten to current truth; the
  2026-06-10 session queue superseded by the decade queue (one home).
- **`current-state.md`** — ledger reconciled (#732, #738–#740, #741 added; 14 pre-#715
  entries archived; the giant stamp line trimmed — pre-2026-06-11 history → archive
  § Stamp-line history); ▶ Next action → the decade queue; marker reset to **PR #741**
  (next pass at #750).
- **`ideas/README.md`** — the two research entries flipped from "decisions pending" to
  the recorded Q-0108–Q-0112 outcomes.
- **`check_reconciliation_due.py`** — best-effort `git fetch origin main` first: fresh
  containers read a stale ref (observed: "latest #687" while live main was at #740).

## Verification

`check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓ ·
`check_reconciliation_due` flips to "not due (#741/#750)" after the marker reset ✓ ·
`check_session_log --strict` ✓ · cadence-script tests + `check_quality` run pre-push.
Docs + one advisory script only — no runtime code (per Q-0107).

## Context delta (reflection interview)

- **Route worked:** CLAUDE.md → collaboration-model → current-state → journal → roadmap
  gave the full picture; the ledger/docs checkers pinpointed the drift mechanically.
- **Discovered by hand:** (1) the cadence checker's stale-`origin/main` failure mode
  (fixed in-pass); (2) main moved **twice** during the session (#740 already merged at
  start; #732 merged mid-session into files I was editing) — the "fetch before editing
  cross-cutting ledgers, and again before each edit burst" habit is what saved it;
  (3) the #739/#740 session left no `.sessions/` log and no ledger entries, so the pass
  had to reconstruct its scope from the router + git log.
- **Decisions made alone:** treating the task as the Q-0107 pass (the cadence was due and
  the task text matched its definition); placing the safety/community items as one new
  roadmap lane rather than scattering them across server-management/games; the decade
  queue's ordering (P2 sweep → P0s → new lane) following the hardening roadmap's own
  recommendation.
- **Weak point:** the decade queue is my synthesis of the owner's signals (hardening
  answers + the approved lane), not an owner-ratified ordering — flagged in the pass doc
  ("if the owner steers mid-decade, swap a slot and note it").

## ⟲ Previous-session review (Q-0102 — the #739/#740 owner-research session)

- **What it did well:** clean capture-to-decision conveyor in one arc — research distilled
  into two dedup-checked idea docs + a reusable platform-limits reference, five scope
  questions asked well (tiered options, privacy tradeoffs explicit), and the answers
  written back into the idea docs' routing tables immediately.
- **What it missed:** the close-out enders — no `.sessions/` log, no ledger entries
  (#738–#740 were the drift this pass fixed), and the approved lane never reached the
  roadmap (the gap this whole session existed to close).
- **System improvement:** conversation/capture sessions evidently skip `/session-close`
  because they don't feel like "work sessions." The lightest durable fix: the Stop-hook
  advisory should key on **"did this session merge a PR?"** rather than on session shape —
  any merged PR ⇒ expect a log + ledger entry. (The hook config is owner-gated; routed as
  a proposal via the idea below rather than self-applied.)

## 💡 Session idea (Q-0089)

**Auto-draft the reconciliation pass's inventory.** The bulk of this pass's manual work
was building §2 (what did the last decade's PRs add, and where is each routed?). A small
`scripts/reconciliation_inventory.py` could generate the skeleton mechanically: `git log
--diff-filter=A --name-only <last-marker>..origin/main -- 'docs/**'` grouped by PR, each
new doc joined against the roadmap/ideas-README link graph (`check_docs` already builds
it) to mark **routed / unrouted**. The pass author then only judges horizons and writes
the queue. Why it's worth having: it converts the recurring 10-PR chore from archaeology
into review, and the "unrouted" column is exactly the drift the pass exists to catch.
Dedup-checked: `check_reconciliation_due.py` only tracks *when* a pass is due, not its
content; nothing in `docs/ideas/` covers this. Conveyor home: this log (small tooling
idea; build it at the #750 pass if the inventory step still hurts — also the natural
place to fold the ⟲ hook proposal above into a router Q-block).

---

## Continuation (same session, post-merge): direction-locking question round

Owner asked to use this chat for planning/ordering before his next implementation
session (Hermes implementation continuing in a parallel chat). One structured round
(Q-0061 pattern), four decisions — all recorded in the router + routed:

1. **Next implementation session = P0-1 games wager money-safety** → design pinned
   same session: [`planning/games-wager-money-safety-plan-2026-06-12.md`](../docs/planning/games-wager-money-safety-plan-2026-06-12.md)
   (source-verified: both PvP settles are sequential credit→overdraft-debit;
   `economy_service` already has the atomic primitives — the plan composes them into one
   audited `game_wager_workflow` with escrow-at-accept as D1).
2. **Q-0097 = (a) operator-managed findings lifecycle** → P1-2 unblocked; **every
   hardening gate is now answered**.
3. **Q-0082 interim ceiling = €30/month** (owner picked over the recommended €15 —
   headroom for live-testing + new metered lanes).
4. **Q-0115 (new) = fold Stage 0 into the #742 Routine bridge** — one dispatch seam;
   bounded protocol activates on wired + calibrated (workflow §10 + roadmap + bridge
   idea doc annotated).

Standing owner actions re-surfaced (no decision needed): wire the Routine + `/fire`
token then calibrate (Q-0105) · V-16 PNG pack · `!btd6ops seed-data` stays self-applying ·
Q-0036 #632 markup · fishing ratification (V-14) still pending — deliberately not asked
this round (games lane is occupied by P0-1; ratify when the games lane frees up).

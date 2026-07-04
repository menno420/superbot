# 2026-07-04 — Prepare the Gate-0 grammar-freeze + Phase-B L0 ultracode brief

> **Status:** `complete` — PR #1713. Owner-directed prep session: authored the paste-ready **Opus 4.8
> ultracode** prompt for the next step after the foundational-design bridge (#1708) — the **Gate-0
> grammar freeze + Phase-B L0 build-order plan** — plus its grounded work-list companion, harvested
> from the shipped specs (Q-0120). Docs-only; not the Gate-0 session itself.

## What shipped (all in PR #1713)

1. **[`docs/planning/rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md`](../docs/planning/rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md)**
   — the paste-ready brief: quick-launch + THE PROMPT (6 deliverables — the frozen L0 grammar · the
   amendment registry · closing the pending cross-spec wiring · resolving the register (freeze 19
   defaults + an owner-decision packet for the 12 owner-only calls) · the L-24 riders · the L0
   build-order plan) + hard scope fences (consolidate not redesign; render owner-only, never decide;
   no code, no new-repo bootstrap, not Stage-2) + a curated Appendix.
2. **[`docs/planning/rebuild-gate0-worklist-2026-07-04.md`](../docs/planning/rebuild-gate0-worklist-2026-07-04.md)**
   — the grounded work-list companion (harvested by a 3-agent workflow from the 14 shipped specs):
   Part 1 the grammar fold list (87 primitives / 18 attach-points, each with type/default/role + what
   it retires), Part 2 the register disposition (19 ratify-default / 12 owner-only of 31), Part 3 the
   Phase-B L0 build order (16 steps S0–S15). The Gate-0 session's start index.
3. **Planning README** — homed both docs; marked the foundational-design brief **EXECUTED → #1708**.
4. **Repo prep** — synced the branch to `origin/main` (the merged deliverable) after #1708 merged;
   force-with-lease off the already-merged head per the merged-PR git rule.

**Scope call (grounded, not memory):** the next step is the deliverable's own named next per its README
§6 ("feeds two gates + hands off a third"). Harvest surfaced two things the Gate-0 session must handle
deliberately — the **amendment registry is a prerequisite** (must be built collision-free before the
fold), and **`ActorRef.member_tier` (RC-12) is still unabsorbed** on spec 02 (the TIER lane can't
resolve without it) — both are called out as first-class deliverables in the prompt.

## 💡 Session idea (Q-0089)

**[`owner-decision-packet-renderer-2026-07-04.md`](../docs/ideas/owner-decision-packet-renderer-2026-07-04.md)**
— a reusable renderer/skill that turns a question-register (options+recommendation rows) into an
owner-consumable **visual decision packet** (markdown v1, Artifact-HTML v2). Closes FJ gap #13
("nothing renders decisions visually for a non-coding, visually-oriented owner"); its first concrete
consumer is the Gate-0 session's 12 owner-only rows — build it there and it compounds across every
later gate.

## ⟲ Previous-session review (Q-0102)

Previous: **#1708, the foundational-design bridge (this same day, five workflows).** What it did well:
the **seam-consistency matrix earned its keep** — it caught 5 real cross-strand contradictions
(the unhosted-outbox-relay + the GLOBAL-slot double-arm were genuine durability blockers) that ten
isolated Phase-B plans would each have shipped self-consistent but mutually incompatible; and the
lenient-schema recovery (WF1b) cleanly rescued the two design agents that failed structured output
without losing their complete drafts. **What it could have done better:** (a) it used a strict
`additionalProperties:false` output schema that tripped the retry cap on the two most complex specs —
the lenient schema should have been the default from WF1, not a recovery patch; (b) the design agents
emitted non-allowlisted doc badges (`design`/`synthesis`/`harvest`) that only surfaced at
session-close `check_docs`, forcing an 18-file normalization pass. **Workflow improvement:** give
fan-out agents that WRITE repo docs the badge allowlist + a "run `check_docs` on your file before
returning" instruction, and default workflow structured-output schemas to lenient (few required, no
`additionalProperties:false`) — both are cheap and kill a whole class of end-of-session cleanup. The
self-auditing loop held: this session applied the lenient-schema lesson to its own harvest workflow.

## Docs audit (Q-0104)

- `check_docs.py --strict` ✓ (both new docs homed in the planning README → reachable; `reference`
  badge on the worklist, `plan` on the brief).
- `check_plan_homing.py` ✓ (63 live plan docs all homed; the new brief included).
- `check_current_state_ledger.py --strict` ✓ (in sync; benign lag on 1 newer PR — the recon pass
  records it). This session's PR is unmerged so it is correctly not in the ledger.
- No chat-only residue: the scope decision + the harvest gotchas (amendment-registry-first, member_tier
  pending) are durable in the brief + work-list.

## ⚑ Self-initiated

None beyond the owner's explicit ask ("prepare the repo and another prompt for an ultracode session
to take on the next steps"). The scope pick (Gate-0 + L0) is the deliverable's own README-§6 next
step; the work-list harvest + idea are the standing Q-0120 grounding + Q-0089 ender.

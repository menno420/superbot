# 2026-07-03 — Prepare the Opus-4.8 foundational-DESIGN overnight prompt

> **Status:** `complete`

**Run type:** owner-directed prep — follow-through on "what did we not properly plan, especially
foundational functions." **PR #1705.** Docs-only, prepared NOT executed. Restarted fresh from
`origin/main`.

**Did:** authored a comprehensive, paste-ready **Opus 4.8 ultracode** prompt for an overnight
foundational-**design** session:
`docs/planning/rebuild-foundational-design-opus-brief-2026-07-03.md`. Its overnight job: design the
~10 kernel functions that were AUDITED but never DESIGNED — compiler+snapshot (linchpin), C-1
resolver, error envelope, C-2 draft pipeline, workflow engine, outbox, scheduler/state, K1,
authority, ops-kernel — to **buildable depth**; close the 5 never-surfaced concerns
(security/abuse+rubric-classes, data-integrity, credentials, backup-DR/rollback, platform-governance);
and harvest one consolidated question register. Structured as 3 strands (kernel spine · durability ·
concerns) + a seam-consistency matrix + the register. Explicitly fenced OFF from a fourth audit, the
Stage-2 walk, and any code.

**Grounding:** a 13-agent workflow (~935k tokens, 0 errors) re-mapped each function's current-state +
seams + open-questions against **shipped source** (Q-0120) so the prompt cites real files — including
carrying the judgment's correction that `WorkflowResult`/`contracts.py:48-52` don't exist (the real
analogue is `StageResult` at `message_pipeline.py:181`). The verified map is the doc's Appendix (the
overnight session's design work-list). Also homed the brief + retro-homed the Fable-5 launch brief in
`docs/planning/README.md` (both were unindexed → `check_plan_homing` would have caught the new one).

**⚑ Self-initiated:** none beyond the directed prep — the brief, its grounding workflow, and the
two README homing entries are all inside the ask (the second homing entry is a fix-drift-on-sight per
Q-0166: the Fable-5 brief was an unindexed live plan).

**💡 Session idea (Q-0089):** none new — a focused prep session; the two owner ideas captured a turn
earlier (release-loop, websites) stand for this cluster. Forcing one would be filler (Q-0089 bar).

**⟲ Previous-session review (Q-0102):** the owner-ideas capture session (#1704) correctly
cross-referenced each idea to the judgment gap it closes — good discipline that made this prep's
"design the seams FOR the owner's new ideas" pointer trivial to write. **System note:** the recurring
pattern this session confirms — *a prep brief is only as good as its grounding* — argues for making
"ground the prompt against source before writing it" a standing rule for any launch-brief session,
not an ad-hoc choice; the two briefs that later proved most launchable (Fable-5, this one) both did
it, and memory-only briefs risk the fabricated-cite class (WorkflowResult) that wastes the launched
session's budget.

**Docs audit (Q-0104):** `check_docs --strict` + `check_plan_homing` green; the brief is homed;
nothing chat-only. No new router Q needed — this is prep, not a decision (the overnight session's
output will carry the decisions).

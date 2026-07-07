# 2026-07-07 — Projects EAP: wiring the coordinator onto the rebuild §5 sequence

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only:
> `check_docs.py --strict` and `check_current_state_ledger.py --strict` both green.

## Why this session

PR #1807 (merged) activated the EAP generally. Owner's follow-up made the actual intent
explicit: the plan (`rebuild-canonical-plan-2026-07-06.md`) is complete, and the EAP is the
mechanism to *execute* it — starting canonical-plan §5 at step 6 (create `superbot-next`).
This session produces the paste-ready setup so the owner can stand up the Project in one
sitting: repo scope, Custom Instructions block, and the first message to the coordinator.

See `docs/planning/projects-eap-coordinator-kickoff-2026-07-07.md`. Also links back from the
canonical plan's §9 "deliberately NOT folded" note, which named this exact deferred item.

## ⚑ Self-initiated

None — directly responsive to the owner's in-session ask ("help me set it up properly... my
intention is to use the projects to migrate my bot into a fresh repo").

## 💡 Session idea (Q-0089)

**A "coordinator drift check."** Once the Project is running, nothing currently re-verifies that
the coordinator is still following the canonical plan's §5 order rather than improvising a
different sequence over many sessions. Idea: a lightweight periodic check (could be a routine the
coordinator itself sets up, per its own Custom Instructions) that diffs "steps completed so far"
against the plan's §5 table and flags any step skipped or done out of order. (Grep-checked
`docs/ideas/` — not present.)

## ⟲ Previous-session review (Q-0102)

Previous distinct session (PR #1807, the activation plan): **did well** — correctly scoped itself
to the trial/rubric/feedback-reply question the owner actually asked, without jumping ahead to
"how do I wire this into the rebuild specifically." **Could have anticipated:** the owner's stated
intent in the original request was already "migrate my bot into a fresh repo," which in hindsight
was the real target, not a generic trial — the activation plan's §2 use-case pick (kit-lab or a
port-band) hedged toward a smaller trial when the owner's own words pointed at the full rebuild
kickoff. **System delta:** when an owner's request names a specific concrete goal ("migrate X"),
prefer wiring directly to that goal over a smaller proxy trial, even under a tight deadline — a
smaller trial is the right call only when the real goal isn't clearly stated yet.

## ▶ Next action

Owner-facing: follow §1-§3 of the kickoff doc — create the Project scoped to `superbot`, paste
the Custom Instructions, send the first message. Everything from canonical-plan §5 step 6 onward
is then the coordinator's job.

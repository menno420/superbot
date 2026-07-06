# 2026-07-06 — Fable decision authority (Q-0240) + foundational-consolidation brief revision

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs/config-doc only (no
> `disbot/` runtime code): `check_docs.py --strict` (new `owner-guidance` doc reachable),
> `check_plan_homing.py --strict`, `check_current_state_ledger.py --strict` all green.

## What this session did

Owner directive (in-session, two parts): (1) **"let fable decide … things are too technical for me
anyways … redesign the repo so fable will make its own decisions"** and (2) Fable should **also
reconsider whether the plan properly defines all foundational layers** (AI integration, automation, the
live command-probing/verification tooling) and **consolidate everything into one comprehensive correct
plan.** Applied the rule change directly (in-session owner = live reviewer, Q-0106 exception).

**Shipped (PR #TBD):**
- **Governance change — Q-0240 (decide-and-flag over route-up).**
  - New durable doc `docs/owner/agent-decision-authority.md` — agents decide reversible-until-a-gate
    calls themselves (recommend + rationale + flag), don't route them; the safety brake is reframed
    (irreversible/production/external is decided-and-flagged-for-veto, not blocked; the only stop-and-wait
    is *executing* something irreversible before the gate). Owner's control point = one review pass at
    the gate.
  - Router `Q-0240` block recording the decision + provenance.
  - Surgical `.claude/CLAUDE.md` § Act-vs-ask clause (owner-directed, provenance Q-0240) — clarifies that
    "architectural → ask" means *irreversible* architectural change, not a reversible-on-paper planning
    decision.
- **Fable brief revision** (`rebuild-newrepo-start-fable5-ultracode-brief-2026-07-06.md`) — folded in
  BOTH: (a) the decide-and-flag model (replaced the "owner-decision packet — do not decide" with a
  DECISIONS LOG + a short FLAG-FOR-GATE list; the session decides every call), and (b) the
  **foundational-completeness + consolidation** scope — the prompt now has the session reconsider the
  L0/foundational taxonomy (AI-invocation/provider seam vs L4 knowledge domain; automation/scheduling as
  a foundational layer near K5/K7; the parity+Arm-D+wire-level verification tooling as a defined
  verification foundation) and fold the scattered plan into ONE canonical source-of-truth plan.

Also: reverted an incidental harness-added `.claude/settings.local.json` permission entry (kept this PR
to intended docs changes; executable-config stays owner-gated).

## ⚑ Self-initiated

None beyond the owner's two in-session directives (the rule change + the brief revision). The rule change
is exactly the kind Q-0240 now governs — but it was owner-directed, so it ships with its provenance Q.

## 💡 Session idea (Q-0089)

**A decide/flag/veto lint for planning artifacts.** Now that Q-0240 makes "decide-and-flag" the default,
a cheap checker could scan `docs/planning/` deliverables for the anti-pattern it replaces — parked
"owner-decision packet"/"route to owner"/"TBD-owner" language on decisions that are reversible-on-paper —
and nudge the author to decide-and-flag instead. It would keep the new norm from silently eroding back to
route-everything-up as sessions churn. Cheap AST/grep checker, advisory tier (Q-0105 disposable). Pairs
with the launch-brief-template idea. (Grep-checked `docs/ideas/` — not present.)

## ⟲ Previous-session review (Q-0102)

Previous (this branch): the Fable brief v1 (#1768). **Did well:** it already flagged (in my own reply)
that the six-decision packet was over-conservative and offered the two-tier split — which is exactly what
the owner then confirmed and expanded. Surfacing my own over-caution proactively is what let this turn
move fast. **Missed / system delta:** v1 encoded the over-routing as *doc content* (a packet the Fable
session would dutifully produce) rather than checking it against the repo's own act-vs-ask norm — had I
cross-read the brief against CLAUDE.md's Q-0014/Q-0129/Q-0172 lean when writing it, I'd have written
decide-and-flag from the start. The durable lesson (now the Q-0089 idea): a planning artifact that parks
reversible decisions is drifting from the repo's stated autonomy norm — worth a lint.

## ▶ Next action

Owner runs the revised brief: fresh `claude-fable-5`, `/effort xhigh`, paste §3. It now produces ONE
consolidated correctly-layered plan (with AI-integration / automation / verification-tooling placed
correctly), a runnable Phase-2.5 procedure, the test-guild design, and a decisions-log + short
flag-for-gate list — deciding its own calls per Q-0240. Next action after it is a **Phase-3 go/no-go**.

# 2026-07-07 — Rebuild idea consolidation (fold 4 captures + §3.C re-verify)

> **Status:** `complete`
> **Branch:** `claude/rebuild-plan-consolidation-c34c0b` · **PR:** #1791
> **Brief:** `docs/planning/rebuild-idea-consolidation-fable5-ultracode-brief-2026-07-07.md`
> **Governance:** Q-0241 (never-wait, decide-and-flag), Q-0240.

## What was about to happen (opening declaration)

Fold today's four owner-raised idea captures into the canonical rebuild plan
(`rebuild-canonical-plan-2026-07-06.md` §11, new lettered amendments continuing from A-11), then
re-verify the plan against the brief's §3.C five critique points + a free hunt.

## What happened (close-out)

All four captures folded, all five §3.C points produced verdicts, and the free hunt landed five
genuine finds — **§11b amendments A-12…A-20** on the canonical plan, registry mints
**R-16 / R-17 / P-5** in `rebuild-amendments.yml` (checker green), the consolidation report
(`docs/planning/rebuild-idea-consolidation-report-2026-07-07.md`, decisions IC-1…IC-16 all
⚑-flagged), the owner-briefing human-pacing correction, all four idea docs re-routed to their
landings (with three factual corrections to the idea docs themselves), and the S3 ledger updated.
Method: a 9-lane parallel source-verification workflow (~1.17M subagent tokens, 376 tool calls,
`path:line` everywhere), decisive citations re-verified first-hand by the coordinator. Checks:
`check_amendments` ✓, `check_docs --strict` ✓, `check_current_state_ledger --strict` ✓ (benign
newest-merge lag only).

Highlights beyond the mandate's letter: the §3.C ratchet probe found the escape-hatch checker had
**no landing step anywhere in the program** (A-19 wires it); the free hunt found user automations
would have **bypassed the new role lane entirely** via the SYSTEM_ACTOR scripted bypass (closed in
A-13); and the verified_live arithmetic that final-judgment finding #8 asked for on 2026-07-03 —
then lost — is restored as A-18.

**⚑ Self-initiated** (Q-0172 accountability line — beyond the brief's explicit asks): the R-17
quiet-hours + condition-poll carriers; the fire-time creator-ActorRef authority rider; the
deny-until-role widening of A-12 (so the join gate doesn't spawn a second mechanism); the
one-inventory rule in A-15; the A-19 permanence wiring (the brief asked "confirm and fix if
port-only" — the fix found and closed a bigger hole: no landing step at all); the owner-briefing
correction; the vestigial-ROLE_OVERRIDE kill note; the three idea-doc factual corrections; the
mint-now (vs direct-at-fold) registry decision (IC-3).

## 💡 Session idea (Q-0089)

**A directed-registry-action drift guard.** This session found that canonical-plan §11 A-numbers
and the G-/R-/P- registry are fully decoupled: A-9 (2026-07-07) *directed* "freeze G-19 + widen
its consumers" and the yml still shows G-19 untouched — a directed-but-unexecuted registry action
with nothing tracking it (this session chose mint-now for R-16/R-17/P-5 specifically to dodge that
failure mode). Idea: extend `tools/check_amendments.py` (or a sibling checker) to cross-reference
plan-amendment rows that name mechanical registry actions ("freeze G-N", "widen consumers",
"mint R-N") against the yml's actual state and report directed-but-unexecuted actions — the
enforce-don't-exhort instinct (Q-0132) applied to the amendment pipeline itself. Cheap (the yml is
machine-readable; the directive grammar is a handful of patterns), and it catches a drift class
this session hit in the wild. Dedup-grepped: no prior capture.

## ⟲ Previous-session review (Q-0102)

The previous session (the 2026-07-07 final review, #1778/#1783…#1790) set a very high bar — its
A–H sweep was the reason this session could stay narrow, and its §11 named-landing pattern is what
this session extended. Two genuine misses it surfaced-by-contrast: (1) it **dropped final-judgment
finding #8** (the verified_live human-capacity arithmetic) while simultaneously *editing the owner
briefing to deny any human pacing remained* — the correction had to be restored here as A-18; a
review that retires human gates should re-check which human *labor* (as opposed to gates) the plan
still depends on. (2) Its A-9 row **directed a registry action it didn't execute** (the G-19
freeze/widen), which still hasn't happened — the concrete workflow improvement is the session idea
above, plus the rule of thumb this session followed: an amendment that names a mechanical registry
action either executes it in the same PR or anchors it to an owning build step.

## 📚 Docs audit (Q-0104)

Is anything important from this session not in its durable home? — No. The folds live in the plan
(§11b) + the registry (yml); the reasoning lives in the consolidation report; the idea docs point
at their landings; the ledger (hub + S3) names PR #1791; the owner-veto surface is the report §7.
`check_docs --strict` + `check_current_state_ledger --strict` + `check_amendments` all green. The
one deliberately-open item is recorded where it belongs: the live-bot `!channel restrict`
convenience command stays in the channel-role idea doc as the open remainder (IC-16).

## 🌱 Backlog grooming (Q-0015)

Satisfied by the session's core work: four ideas moved down the lifecycle in one pass (all four
2026-07-07 captures → routed/folded with landings), plus three factual corrections to idea docs
found stale during verification.

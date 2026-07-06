# 2026-07-06 — Gate V verification-fleet review prompts (documented launch pad)

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only session (no
> `disbot/` runtime code): `check_docs.py --strict` green (new doc reachable) and
> `check_current_state_ledger.py --strict` clean (benign newest-merge lag only). No formatter/mypy/pytest
> surface touched.

## What this session did

Owner asked (in-session) to (1) **document the corrected** ChatGPT-authored rebuild-review prompts in the
repo so they aren't paste-and-lost, (2) redesign the Codex arm as **multiple Codex sessions**, and (3) add
a **dedicated live-testing session** to help **lift the final gates**. Mapped to the repo's own pipeline,
all three are the same thing: flesh out and parallelize the **GATE V verification-fleet pass** (Q-0234)
between Phase A and Phase B.

**Verification first (didn't take ChatGPT's self-review on faith):**
- Confirmed all 36 referenced doc paths + `parity/` + every named script exist on disk — no broken
  reading routes in any of the three prompts.
- Confirmed the games-sequencing premise against source: `rebuild-stage2-subsystem-walk-2026-07-05.md`
  rows 29–42 are L3 games, row 43+ is L4 — so L3 genuinely precedes L4/L5 in the frozen plan.
- Confirmed HEAD (#1748) is newer than the dated artifacts (why every arm must re-verify live), and
  `discord.py>=2.7,<2.8` is pinned (why the Agent-Mode "verify the pin" instruction is well-founded).
- Ran a 4-agent prompt-critique workflow (one grounded critic per prompt + a cross-prompt
  complementarity check). Verdict on all three: **minor-edits** — grounding accurate, read-only fencing
  sound, ChatGPT's corrections right. Real weaknesses were cross-cutting (below).

## Shipped (PR #TBD — this session)

**New:** `docs/planning/rebuild-gate-v-verification-fleet-2026-07-06.md` — the Gate V launch pad. Four
independent arms with **single-PRIMARY-owner-per-deliverable** (kills the measured ~60% inter-report
overlap): Sonnet-5/Ultracode (architecture + sequencing), a **5-session Codex fan-out C1–C5** + reconcile
(source/test truth), Agent Mode (external/migration/live-GitHub), and an empirical **live-testing arm**
(`verified_live` goldens the paper reviews can't produce) — reconciled by a final Opus/Fable synthesis.
Shared §3 contracts (pinned readiness enum, evidence labels, `path:Lnn` claim-anchor scheme, point-of-use
CodeGraph + CI-parity caveats, degrade-gracefully ladder) make the four reports merge without manual
normalization.

**Wired:** `rebuild-planning-phase-2026-07-03.md` §Gate V now points at the launch pad.

**Cross-cutting fixes folded in** (from the critique workflow): CodeGraph dead-unresolved/invisible-edge
caveats at point-of-use; `python3.10` CI-parity + Postgres-needed test-evidence caveats; Codex
explorer-subagent sequential fallback; Agent-Mode public-repo clone-over-connector + discord.py-2.7
version check; exact canonical paths (avoid the `FINAL-REVIEW-HANDOFF.md` sibling); `S2-btd6.md` added to
the startup route.

## ⚑ Self-initiated

None beyond the owner's in-session direction — the whole session is owner-directed (document + parallelize
+ add live-testing arm). Docs-only, reversible.

## 💡 Session idea (Q-0089)

**A reusable "review-fleet contract" template in `docs/ultracode/`.** The repo has
`worker-scope-template.md` for parallel *refactor* fleets but nothing for parallel *review/verification*
fleets. This session's §3 shared contracts (PRIMARY-owner-per-deliverable matrix + pinned enum/evidence-
labels/claim-anchor scheme + point-of-use tool caveats) are exactly the reusable substrate a future
verification fleet needs — extracting them into a `review-fleet-template.md` companion would let any later
fleet (not just Gate V) start from a mergeable-by-construction contract instead of re-deriving one. Worth
having because the "four reports that don't align on enums/keys" problem the critique surfaced will recur
every time the project fans out independent reviewers.

## ⟲ Previous-session review (Q-0102)

Previous: `2026-07-06-ci-arc-completion.md` (#1748) — completed the CI-followups arc with a second AST
guard (`check_deferred_recovery`) + tail cleanup, made design calls autonomously while explicitly holding
the executable-config safety brakes. **Did well:** clean friction→guard execution (Q-0194), each new guard
shipped with tests + flagged the branch-protection items for owner sign-off rather than self-applying —
correct autonomy boundary. **Could improve / system delta:** advisory AST guards are now accumulating
(`check_audit_seam`, `check_deferred_recovery`, …); per Q-0105 each convenience checker should carry an
explicit *graduation-or-delete* criterion (when does it stop being "advisory/unverified" and become
load-bearing, and who deletes it if it proves noisy?). Without that, the advisory tier grows unbounded and
a later agent works around a stale guard instead of removing it. A one-line "graduation criterion" header
convention for advisory checkers would close it — a candidate router DISCUSS item, not self-applied
(executable-config-adjacent).

## ▶ Next action

Owner runs the fleet: launch Arms A–D in parallel (§4–7 of the launch pad), then the final synthesis
(§8). Arm D (live testing) is operator-run — needs a test guild + throwaway Postgres, never production.
Gate V lifts per §9 once the synthesis reconciles all four with no unresolved `Blocker`.

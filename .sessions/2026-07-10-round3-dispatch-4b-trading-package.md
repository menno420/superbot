# Session — round-3 dispatch, part 4b: trading founding package

> **Status:** `complete`
> **Run type:** owner-directed · same live dispatch chat as part 4 (PR #1957, merged);
> new card + PR (#1963) for the follow-on scope
> **Model/time:** fable-5 · 2026-07-10 ~20:3xZ → ~20:5xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1957).

## What is about to happen

Owner directive (live, this chat): do NOT defer the trading seat to post-verdict —
draft the full founding package NOW (Custom Instructions + comprehensive continuous
chat brief, same standard as the other seats), designed so the fresh seat runs
ORDER 008 (the pre-registered one-shot holdout eval) as its FIRST substantive work
item, with BOTH verdict branches pre-specified.

## What happened

- **Trading founding package DRAFTED:**
  [`round3-founding-package-trading-2026-07-10.md`](../docs/planning/round3-founding-package-trading-2026-07-10.md)
  — §0 owner pre-clicks (env `trading-strategy` verified MISSING in the account
  registry — the lane predates the one-env-per-Project standard; archetype-python-lab
  verbatim) · §1 Custom Instructions (~4,800 chars: integrity contract — pre-registration,
  one-shot holdout, load path, denominators, ambiguity-against; money protocol Q-0259
  r.4; continuous + volume-first session shape) · §2 coordinator brief (ORDER-008-first
  boot: the fresh-context first-work-item satisfies the protocol §7.2 dedicated-session
  condition; both verdict branches pre-specified — paper lane vs harvest+next-round —
  before any number is seen; routine cutover create-verify-THEN-delete of
  `trig_01Mvn5xRmqGmZJNRHgjqyLpN`; kit v1.1.0→v1.7.0 as a queued slice) · §3 env ·
  §4 boot-verification checklist with red flags.
- **Owner directive Q-0266 landed mid-drafting and was folded at birth:** the
  volume-first founding doctrine (owner's words preserved verbatim in the router
  entry) — every project created to maximize output; CORRECT over BEST (a lane's
  non-negotiables are part of *correct*, never tradeable); lifecycle
  populate → consolidate → few-maintainers. Recorded as **router Q-0266** (append,
  provenance + rollout), folded into the **gen-3 deployment standard §2** (rider next
  to the Q-0265 fold) and into the trading package §1/§2.
- **Runbook touched:** §3.7 trading line superseded-in-place (owner-directed NOW,
  package linked; websites noted booted), §4 drafting queue ticked.
- CI notes: the two early code-quality reds on #1963 = the expected born-red hold on
  both heads (a branch auto-update merged main in, pulling #1962 — the manager's own
  Q-0265 gen-3 fold, which this session's Q-0266 rider now sits beside). Telemetry row
  landed at open this time (part-4's gate-miss lesson applied).

## ⚑ Self-initiated

- Q-0266 router entry + gen-3 §2 rider + package folds (owner was the live reviewer —
  the directive is his verbatim message this chat; the *placement* choices are mine,
  flagged: rider-on-Q-0265 rather than standalone doctrine doc).
- The ORDER-008-first boot design (protocol §7.2 "dedicated session" read as
  fresh-context-first-work-item) — flagged for the boot verification to re-check: if
  the coordinator's calibration argues the reading is unsafe, it should say so rather
  than proceed (the §4.1 red-flag list covers this).
- Runbook §3.7 supersede-in-place of the "trading after the holdout ORDER" sequencing
  (owner's live direction is the provenance).

## 💡 Session idea

**Triage-at-birth labels for the Q-0266 consolidation pass** (dedup-checked: no
existing idea covers it — the consolidation references in `docs/ideas/` are about
missions/programs, not artifact triage): a one-line `triage:` field (e.g.
`triage: keep-candidate — consumed by X` / `triage: experiment — kill if unused by
<date>`) that seats stamp on their own artifacts (docs, sims, products) at creation,
while context is hot. The future consolidation session then greps instead of
re-deriving 100+ artifacts' worth. Cheap to adopt via the kit's session-close drafter;
natural first consumer: every seat now producing volume under Q-0265/Q-0266. Filed as
this card's idea (card-level; promote to an idea file if a second session wants it).

## ⟲ Previous-session review

Part 4 (same chat, PR #1957) recovered well from its two reds (gate-miss + Q-0265
conflict) but BOTH were avoidable at open: the telemetry row was a known gate since
2026-07-09, and the conflict window was opened by pushing docs edits without a
pre-push `git fetch`/rebase against a fast-moving main. **Workflow improvement
(applied this session):** telemetry row rides the OPEN commit, and the close push is
preceded by a fetch + fast-forward check. The deeper fix is the kit-seed-command class:
fold "telemetry row at open" into the session-open ritual the same way the card is.

## Documentation audit (Q-0104)

`check_current_state_ledger --strict` ✓ (post-marker merges = benign lag; #1963 =
this session, records at merge) · `check_docs --strict` ✓ · chat-only material swept:
owner's volume-first message → router Q-0266 (verbatim core preserved) + gen-3 §2 +
package; ORDER-008-first design rationale → package header design-decisions block;
env-missing finding → package §0.1. Claim file deleted this commit.

## Handoff

Owner paste set delivered in-chat: env `trading-strategy` (archetype raw link) →
Trading Project → §1/§2 pastes from the package at main (after #1963 merges). Boot
watch: calibration recites the integrity contract + money protocol + correct 2a/2b
path; then final-report.md §Holdout with 13 denominator-carrying verdicts; routine
cutover create-verify-then-delete. Still open from part 4: sim-lab boot verification
(no heartbeat/trigger as of ~20:2xZ — re-check), the games mapping relay to the
manager, the §2.5 click batch + EAP email (due 07-14), the orphan watchdog chain
(still awaiting the owner's explicit go).

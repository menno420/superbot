# Session — Autonomous loop wired live + Hermes dual-platform control plane

> **Status:** `complete` — the long owner-driven session that stood up the autonomous
> self-improvement loop end-to-end (routines, crons, gates) **and** brought Hermes online on
> both Telegram and Discord. PRs #742–#761 (this session) + the maintainer-side console/VPS
> wiring. Companion logs from parallel sessions: `2026-06-12-ux-lab-build.md`,
> `2026-06-12-reconciliation-night-pass.md`, `2026-06-12-hermes-discord-dispatch.md` (#757).

## What this session built (the loop — repo side)

Eleven merged PRs turned the "discuss-lane" autonomous-loop ideas into a running system
(owner decisions made live this session): **#742** seams (review skill · `check_phase_gate.py` ·
dispatch bridge) → **#743** session-close → **#747** calibration (PR-only) → **#749** verified
`/fire` API → **#751** self-merge calibration → **#752** `autonomous-routines.md` fleet doc →
**#753** issue-triggered reconciliation + **cadence 10→20** → **#754** prompts as loop-turns →
**#756** executor + **Q-0117 Hermes review-merge gate** → **#759** executor-nightly cron →
**#761** free-form `/bugreport` dispatch prompt.

Owner decisions recorded: **Q-0113** (routines self-merge on green CI), **Q-0114** (human gate =
agent-originated features only), **Q-0117** (Hermes is the independent-reviewer merge gate for
big executor steps), plus the **Q-0107 cadence 10→20** amendment.

## The fleet, as it now runs

| Routine / mechanism | Trigger | Status |
|---|---|---|
| `superbot autonomous dispatch` | API `/fire` | ✅ created + calibrated (connectivity · #747 · self-merge #751) |
| `superbot docs reconciliation` | Issue `reconcile` | ✅ created; auto-fired by `reconciliation-trigger.yml` at the 20-PR boundary |
| `superbot night executor` | Issue `continue` (cron 03:00/05:00 CEST) | ✅ created; `executor-nightly.yml` opens the issue |
| Hermes `superbot-review-merge` | daily 07:30 (skill) | ✅ installed; **ADVISORY mode** until calibrated |
| phase gate | `check_phase_gate.py` | ✅ reports FIX-PHASE (keeps invented features out) |

## Maintainer-side wiring DONE (confirmed this session)

- ✅ Hermes systemd unit regenerated (`hermes gateway install --system --force`).
- ✅ Hermes skills installed on VPS — **10 skills** incl. `review-merge` (`install-skills.sh`).
- ✅ Routine created + API token in `~/.hermes/routine.env`; dispatch fired live end-to-end.
- ✅ All three routines created in the console with their prompts + triggers.
- ✅ Claude GitHub App confirmed installed (all repos; issues/PR/workflow read+write) — arms the issue triggers.
- ✅ **Hermes live on Discord** — created the Discord app, enabled the two privileged intents
  (Message Content + Server Members), invited the bot, token in `~/.hermes/.env`; the bot
  answered in `#general` and set its home channel there. One gateway now serves Telegram + Discord.
- ✅ Gateway returned to the always-on systemd service.
- ✅ `#757` HermesCog merged (`/bugreport`, `/dispatch`); Railway `CLAUDE_ROUTINE_*` vars **staged**.

## ⚠️ UNCONFIRMED maintainer steps — VERIFY NEXT SESSION (assume not done)

1. **Railway "Deploy" not confirmed.** The four `CLAUDE_ROUTINE_*` vars were *staged* ("Apply 4
   changes") but the owner was not seen clicking **Deploy**. → `/bugreport` and `/dispatch` may
   still be inactive. **Verify the worker redeployed and the vars are live.**
2. **Dispatch routine prompt version.** The owner said "finished setting up all 3 routines"
   *before* the free-form `/bugreport` dispatch prompt (#761) was handed over. **Verify the
   dispatch routine carries the latest free-form prompt**, not the earlier one.
3. **Routine models.** The dispatch routine was last seen on **Fable 5** (premium); recommended
   Opus 4.8 for cost (§11). **Verify the routine models** (dispatch/executor = Opus, reconciliation
   = Sonnet/Opus) so the daily cap + spend stay sane.

## 🔎 Critical verification finding (the thing that mattered)

**Both audit checkers were lying green all session.** `check_reconciliation_due.py` and
`check_current_state_ledger.py` shared a merge-subject regex matching `Merge pull request #N`
and `(#N)` — **but not `Merge PR #N:`**, the style every MCP merge in this session produced. So
my own mid-session "ledger clean ✓" and "not due" confirmations were **false green** — the five
PRs #753/#754/#756/#759/#761 had no ledger entries and the cadence was frozen reporting "latest
#751" while #762 was merged. The parallel **#763 night pass caught and root-fixed it** (regex +
tests pinning all three subject styles) and entered the #753–#761 arc into the ledger. **Lesson
(recorded here so it isn't relearned): an audit tool that parses merge subjects must match the
`Merge PR #N:` MCP style — grep other scripts for the same blind spot.**

## 🔎 The autonomous loop has NOT yet self-fired (still the open calibration)

- **Reconciliation routine:** the #763 pass was a *parallel interactive session*, not the
  routine — because the cadence Action's broken regex reported "not due", so it never opened a
  `reconcile` issue. The regex is now fixed; the **first autonomous reconciliation fires when
  PRs cross #780**.
- **Executor:** `executor-nightly.yml` opens its first `continue` issue at **01:00 UTC tonight**
  (~03:00 CEST). That is the **first unattended autonomous executor run** — watch it in the
  morning (the run list + any `claude/` PR it self-merges). This is the Q-0105 "watch the first
  runs" moment; it hasn't happened yet.
- **Hermes review-merge:** runs 07:30 daily but the `needs-hermes-review` queue is empty until
  the executor opens a big step, so its first real review is also pending.

## ▶ Next-session handoff (in priority order)

1. **Verify the 3 unconfirmed maintainer steps above** (Railway deploy · dispatch prompt · models).
2. **Check the first autonomous executor run** (01:00 UTC issue → did the routine fire, build, and
   behave?). Promote Hermes review-merge to TRUSTED only after it catches real issues.
3. **Build the Hermes bug-triage flow** — captured at
   [`docs/ideas/hermes-bug-triage-flow-2026-06-13.md`](../docs/ideas/hermes-bug-triage-flow-2026-06-13.md):
   route `/bugreport` *through Hermes* (spam/genuine triage → reproduce + reword + fetch
   logs/related files → save a curated `bug` issue + a Discord summary) → the nightly executor
   batch-fixes accumulated `bug` issues. The current `/bugreport` is direct instant-fire +
   self-merge — the cap-hungry pattern the owner wants replaced.
4. **Fix the gateway restart crash-loop** — [`health/bug-book.md`](../docs/health/bug-book.md)
   **BUG-0011**: every `systemctl restart` (and periodically) the gateway exits `status=1`
   (Telegram 409 on overlapping poll) and self-heals; noisy and obscures real diagnosis.

The repo-side "▶ Next action" (the band queue) is owned by `current-state.md` and the #763 pass —
this log is the **control-plane** record, not the repo roadmap.

## 💡 Session idea (Q-0089)

**A `superbot-calibrate` fixture harness** — a small set of plan/PR snippets with *known planted
issues* (a `services→views` import, a missing audit-event on a mutation, a mislabeled total) plus
an expected-findings key, so `superbot-review` / `superbot-review-merge` (and any GPT/Gemini swap)
can be **scored against ground truth** before its dissent is trusted to gate. Every loop doc says
"confirm against ground truth a few times" — this makes that discipline a repeatable test instead
of a vibe, and it's exactly what lets the reviewer seam be swapped freely. Small, additive, and it
turns "calibrate the reviewer" (the gate to TRUSTED mode) into something checkable.

## ⟲ Previous-session review (Q-0102)

Reviewing the **#763 night reconciliation pass** (parallel session): it did the single most
valuable thing of the night — it **distrusted a green checker** and found both audit tools were
false-green on the `Merge PR #N:` style, which had silently hidden my whole autonomous-loop arc
from the ledger. That is the Q-0105 "verify tooling against ground truth" posture working exactly
as intended, and it's a strong argument for the `superbot-calibrate` idea above (don't trust a
checker's green until it has a verified catch). What it could not do from its lane: it couldn't
see the *maintainer-side* state (routines, Hermes, the unconfirmed Railway deploy) — which is the
gap this log fills. **System improvement it surfaces:** the loop now spans repo *and* a VPS/console
control plane that no in-repo checker can see; the next reconciliation should treat
`docs/operations/autonomous-routines.md` + the latest control-plane session log as the
source of truth for "is the loop actually wired", since `check_*` scripts only see the repo half.

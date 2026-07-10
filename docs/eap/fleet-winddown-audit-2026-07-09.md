# Fleet wind-down audit — independent verification (2026-07-09)

> **Status:** `reference` — independent, adversarial audit of the 2026-07-09 gen-1 fleet
> wind-down, run from a fresh `superbot` session with no involvement in the audited work.
> Every incident cited below was re-derived from live GitHub PR/commit/CI data by a second
> agent instructed to try to disprove it, not from re-reading the lanes' own claims. Source
> repos and their own git history win over this file if either drifts.

## Scope and method

7 lanes each committed a six-part succession package tonight (retro, next-boot guide,
proposed custom instructions, environment script, feedback for gen-2, status marker); a new
lane (`venture-lab`) was seeded; `fleet-manager` published a ping-test report measuring how
fast each lane acknowledged a coordination order. All 9 repos
(`substrate-kit`, `websites`, `trading-strategy`, `codetool-lab-fable5`,
`codetool-lab-opus4.8`, `codetool-lab-sonnet5`, `superbot-games`, `venture-lab`,
`fleet-manager`) were cloned fresh via `add_repo` and read at HEAD.

32 independent agents ran across four stages: (1) one lane-audit agent per lane, reading
only files on disk plus its own judgment; (2) a second, separate verification agent per
cited incident (21 total, up to 3 per wind-down lane), instructed to pull the real PR/commit
from GitHub and try to refute the claim, not confirm it; (3) one seed-audit agent for
`venture-lab`; (4) three cross-check agents that independently re-derived three of
`fleet-manager`'s ping-test ack-table rows from raw commit history. 350 tool calls total.

## Headline result

All 7 wind-down lanes shipped **complete, substantive** succession packages — none padded
with generic, could-apply-to-any-project boilerplate. Of 21 specific incidents (PR numbers,
commit hashes, error text, timestamps) spot-checked against live GitHub data, **all 21
resolved to real, matching evidence. Zero fabricated or staged incidents were found
anywhere in the fleet.**

That does not mean everything was flawless. Five real inaccuracies surfaced — all
imprecision or misattribution, not invention — and one of them is inside
`fleet-manager`'s own cross-lane report, which is why it gets a lower grade than the seven
lanes it was reporting on.

## Per-lane scorecard

| Lane | 6/6 deliverables | Substance | Incidents evidence-checked | Grade |
|---|---|---|---|---|
| substrate-kit | complete | substantive | 3/3 confirmed (1 minor imprecision) | A |
| websites | complete | substantive | 3/3 confirmed | A |
| trading-strategy | complete | substantive | 3/3 confirmed | A |
| codetool-lab-fable5 | complete | substantive | 3/3 confirmed | A |
| codetool-lab-opus4.8 | complete | substantive | 1/3 confirmed, 2/3 partial | A |
| codetool-lab-sonnet5 | complete | substantive | 2/3 confirmed, 1/3 partial (minor) | A |
| superbot-games (exploration) | complete | substantive | 1/3 confirmed, 2/3 partial | A |
| venture-lab (seed, not wind-down) | 11/11 files confirmed | substantive | n/a — new lane | A |
| fleet-manager (ping-test report) | — | 1 factual error found | 2/3 spot-checked lanes match, 1/3 wrong | B |

"Partial" means the core facts (PR numbers, commit hashes, timestamps) checked out exactly,
but one supporting detail — a rounded duration, a mis-cited source doc, a self-description
of "final state" — was measurably off. Full evidence for every one is in
[Findings](#every-claim-that-failed-or-partially-failed-verification) below.

## What each lane actually shipped

### substrate-kit
Did double duty: wrote its own six-part succession package *and* authored `docs/gen2/`,
the gen-2 blueprint template the other six lanes are meant to consume — verified as
genuinely distinct content, not a copy of its own wind-down docs. Three spot-checked
incidents (a mis-armed auto-merge on a law-protected PR, a twin-execution race where two
sessions built the same order 90 seconds apart, a provisioning-script death) all matched
live PR/commit data almost exactly, including a session ID and GitHub user ID lifted
verbatim from a rate-limit error.

### websites
The most rigorously cross-referenced package audited: every claim is tagged first-hand vs.
inherited, and three spot-checked incidents — an auto-merged empty PR, a silently-broken
dashboard deploy trigger, an order that was appended but never executed — matched exact
commit hashes, diff line counts, and verbatim commit-body text pulled live from GitHub. No
inaccuracies found.

### trading-strategy
Self-reports failure rather than hiding it: two dead sessions, a 2.8-hour draft-parked PR,
and a video-research child lane that silently died on a "fixed" setup script. A later PR
(#12) admits the fix "never took effect" instead of rewriting history — verified
word-for-word against the actual commit diff. No inaccuracies found in the three
spot-checked incidents.

### codetool-lab-fable5
No baseline instructions file exists in this repo at all (correctly disclosed, not glossed
over — this is a real standalone CLI tool project, not a substrate-kit-scaffolded lane).
All three spot-checked incidents matched live GitHub data exactly, including a specific CI
run ID, its five-Python-version job matrix, and test counts.

### codetool-lab-opus4.8
No file is literally named "wind-down-review" — the retro lives at
`project-review-final-2026-07-09.md` instead; content-checked and it does function as a
full wind-down retro, so nothing is missing, just differently named. **Real inaccuracy
found:** the retro calls commit `c96318c` "the main tip at wind-down." It wasn't — three
more PRs merged afterward, including the lane's own official wind-down-complete commit
(PR #22, `80f6cd1`), nearly two hours later. A second, smaller issue: an exact quoted
error-message sequence is attributed to one doc but only actually appears in a different one.

### codetool-lab-sonnet5
Shipped an actual shell script (not prose) as its environment deliverable — though not the
only lane to do so: five other lanes (opus4.8, websites, trading-strategy, fable5,
superbot-games) also shipped real setup scripts — and it reads as genuinely
defensive/tested. *(Correction 2026-07-10: this sentence originally called sonnet5 the only
such lane; refuted by fleet-manager `docs/findings/ultracode-verification-2026-07-10.md`.)* A differential-testing incident (3 real parser bugs
found and fixed, with an exact before/after test count) checked out exactly against the
merge diffs. Minor slip: one retro item is attributed to PR #8; it actually shipped in PR #7.

### superbot-games (exploration lane; mining lane out of scope)
Its combined `succession-exploration.md` genuinely carries both a next-boot section and an
environment section, not one relabeled as two. A striking, independently-confirmed detail:
its own status file is timestamped an hour *after* the PR that shipped it actually merged —
the retro flags this itself as an unexplained clock drift, and this audit independently
reproduced the exact same discrepancy from raw commit data. **Real inaccuracy found:** a
"~1.5 hour" wait figure is repeated across four separate documents, but the same
documents' own timestamps compute to ~1h55m — 28% longer, and never corrected.

### venture-lab (seed lane, not a wind-down)
Confirmed exactly 11 files as claimed. Dense with specific, falsifiable references to gen-1
lessons (named playbook rules, a quoted classifier error, a lane that proved a release
workaround) rather than generic process prose; its opening venture shortlist cites a real
source video with timestamps and an honest skeptic-filter section. Its own status file
honestly shows the first order as unexecuted, not faked as done. No inaccuracies found.

## Every claim that failed or partially failed verification

None of the five below are invented incidents — every underlying event is real. They are
numeric imprecision, a misplaced citation, or (in one case) a real factual error about
which commit was truly "final."

1. **[fleet-manager → websites, contradicted]** Fleet-manager's ping-test report lists
   websites as **"NO ACK"** — claiming no commit touched its status file after the test
   landed. Real GitHub data shows this is false: PR #44 is an explicit acknowledgment
   commit on that exact file, landing 1h39m after the test. The report never states a
   sweep cutoff time, so as published it reads as a permanent, false negative rather than
   a time-bound observation. This is the one finding involving the auditor lane's own
   report about another lane, not a lane's report about itself.
2. **[codetool-lab-opus4.8, contradicted self-description]** Its retro calls commit
   `c96318c` "the main tip at wind-down." Three more PRs merged after it, including the
   lane's actual wind-down-complete commit (PR #22, `80f6cd1`) nearly two hours later. The
   lane's real status marker is separately correct and complete — this is a stale sentence
   in one narrative document, not an operational problem.
3. **[superbot-games, uncorrected imprecision]** A "~1.5 hour" wait is quoted identically
   across four separate documents. The real figure, computable from those same documents'
   own timestamps, is ~1h55m — about 28% longer, never reconciled.
4. **[substrate-kit, minor imprecision]** The retro says an incident was "contained
   same-hour" by two follow-up PRs. One was; the second landed 2h21m later.
5. **[codetool-lab-opus4.8, citation misattribution]** An exact quoted error-message
   sequence is cited as coming from the self-review doc; that doc only paraphrases it. The
   literal quotes actually appear in a different document. The quotes are real, just filed
   under the wrong source. (A sixth, even smaller item: codetool-lab-sonnet5 attributes one
   retro item to PR #8; it actually shipped in PR #7.)

**Also checked and found genuine, not a red flag:** several dramatic quotes (session
self-merge refusals, tool classifier-denial text, a "video lane never started" admission)
exist only in platform/session logs, not in any GitHub-recorded artifact — they cannot be
confirmed or denied from repo data alone. This is a structural limit of the audit method,
not evidence against the lanes; where it applied, the source documents already said so
themselves.

## Fleet-manager's ping-test: spot-checked against real commit history

Fleet-manager ran a coordination test on 2026-07-09: it appended an identical order to all
lanes' inboxes and measured how fast each acknowledged it. Three of its claims were
independently re-derived from live GitHub data, not re-read from the report.

| Lane checked | Fleet-manager claimed | What the real data shows | Match? |
|---|---|---|---|
| substrate-kit | Order landed 18:01:34Z (PR #64, after PR #62 conflicted and was superseded); acked 18:12:39Z (PR #65), 11m05s later. | Exact match on every PR number, state, and timestamp, including the derived 11m05s gap. | ✔ match |
| codetool-lab-opus4.8 | A status heartbeat landed 18:09:15Z, 15m31s after the order, but only acked orders 001–003 (missed 004). | Exact match: same commit, same second-precision timestamp, same elapsed time, diff confirms 004 is absent. | ✔ match |
| websites | "NO ACK" — no commit on the status file since the order landed. | False as published. PR #44 is an explicit acknowledgment commit, landing 1h39m after the order — a delayed ack, not a missing one. | ✘ does not match |

## Top 5 recommendations

1. **[demand rework — fleet-manager]** Correct the websites row in
   `docs/findings/ping-test-2026-07-09.md`: it did acknowledge the order, 1h39m late
   (PR #44). As published, the report states a false negative with no stated sweep cutoff
   to excuse it.
2. **[fix in gen-2 standard]** Require every ack-sweep or time-based finding to carry an
   explicit "as of HH:MM:SSZ" stamp. That single addition would have prevented the
   websites false negative from ever being publishable.
3. **[fix in gen-2 standard]** Add a pre-publish check: recompute every quoted duration
   from the document's own cited start/end timestamps before merging. This would have
   caught superbot-games' 1.5h-vs-1h55m drift (repeated uncorrected across four documents)
   and substrate-kit's "same-hour" imprecision.
4. **[fix in gen-2 standard]** Ship every gen-2 seed — including non-substrate-kit repos
   like the three codetool-lab lanes — a minimal baseline custom-instructions file. Three
   of seven lanes had nothing to diff their "proposed custom instructions" against, which
   made that specific integrity check impossible to run rigorously in three cases.
5. **[fine as is]** The fleet's "lived incidents only" integrity rule is holding: 21 of 21
   spot-checked incidents across seven lanes resolved to real, matching PRs, commits,
   timestamps, and error text. No fabricated or staged content was found anywhere. Ship the
   succession packages as committed — no lane needs a rework demand on substance grounds,
   only the small corrections listed above.

## Full interactive report

A richer, visually-scannable version of this same audit (per-lane cards, chips, the same
evidence) was also published as an artifact for the owner:
<https://claude.ai/code/artifact/1f00ddfe-828d-4aa5-9ec3-8a8aea7d7fe5> — this file is the
durable, in-repo record; the artifact link is convenience only and may expire.

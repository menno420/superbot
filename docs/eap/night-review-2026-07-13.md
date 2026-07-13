# Fleet night review — 2026-07-13 (the doctrine night, verified)

> **Status:** `reference` — owner-directed `/fleet-review` FLEET mode over the 2026-07-12/13
> night run (window 2026-07-12T22:30Z → 2026-07-13 ~09:30Z), run through the **Q-0272
> multi-repo orientation path** end-to-end. **Evidence basis:** `scripts/fleet_status.py`
> sweep (09:0xZ) · fleet-manager roster **gen #25** (07:52Z, Actions regen) ·
> fleet-manager `control/status.md` (09:00Z) + the **2026-07-13 MORNING TALLY** in
> `fleet-manager/control/outbox.md` · fm `docs/owner-queue.md` @ HEAD · **five parallel
> read-only survey agents** (blobless clones + `git log`/`ls-remote` + raw fetches at HEAD,
> one per lane group) · this hub's own git/PR state via MCP. Per Q-0120 every load-bearing
> tally claim was re-verified at HEAD; mismatches are listed, not smoothed over.
> Session: superbot PR #2064.

## TL;DR verdict

**The first fully-doctrined unsupervised night (NIGHT ORDERS v2 + Q-0271 autonomy rider +
direct orders) worked — at scale, and honestly.** Roughly **190+ PRs merged across 12
repos** in one night: superbot-next finished the fishing port and hit **51/51 parity rows**,
venture produced **~215k words of real verified prose** + grew publish-READY 3→6, the ideas
loop ran **18 hands-free proposal→verdict cycles** (10 by the 05:00Z tally, 8 more by
09:00Z), websites landed **41 PRs** including the owner-console prompt ladder and its first
successful scheduled bake, and the new ninth seat (curious-research) booted, shipped 6 PRs,
and served its first ORDER. The platform scheduler degraded again (~01:07–02:08Z) but only
one-slot slips this time — **the Q-0265/R26/R27 failsafe doctrine absorbed it; no seat
died** (contrast 07-12: 9 dropped ticks, 2 dark seats). The manager's morning tally was
**accurate on every mechanically checkable number** (merge SHAs to the minute, byte counts,
word counts) but showed **three telephone-game distortions** in its narrative claims (§3).
The fleet's binding constraint is now unambiguously **owner-click bandwidth**: ~3 settings
toggles, one 5-decision sitting bundle (window ends 07-14), one "go with defaults" reply,
and a ~30-PR green-parked morning sweep.

## 1 · Verification scorecard (Q-0120)

~25 load-bearing tally claims re-verified at HEAD by independent survey agents:

- **Exact-verified (≈22):** fishing port complete (#313/#330/#342/#350; `_unmapped` 6→0;
  the coral double-spend fence is real code, `sb/domain/fishing/ops.py:544`) · curation
  report numbers verbatim (1,088 = 918/110/60) · SBW seat merges to the minute · minigame
  spec exists and is substantive (208 lines, mineverse #58) · websites #236/#239 exactly as
  described, 14 merges 02:40→04:45Z, suite 974→1157 · Deepcast ROM **exactly 117,032
  bytes** · gba enabler refusal verbatim in run 29222310196 · kit #308–#316 merged, #317
  open awaiting ratification · trading synthesis verdict quoted verbatim ("nothing tonight
  is a finding, and that null is the deliverable") · SWTK live re-verified by direct GET
  (HTTP 200) · Slow Word novella **18,986 words on disk** — the wc matches the claim.
- **Mismatches (3, all manager-narrative overstatements; lane records were honest):**
  1. *"SBW casino spec CONSUMED by superbot-next"* — superbot-next's own design doc
     (#329, `docs/design/game-sections.md`) says the opposite: explicitly
     **spec-independent**, SBW's SIM-REQUEST "has NOT arrived", §7 holds a replacement
     slot. The two-seat "spec→design→build round trip" is therefore **overstated** —
     both halves happened the same night, but the causal link the tally claims is
     contradicted by the consumer's own record.
  2. *"V017 approval (assignment lane)"* — V017 is `verdict: conditional` (idle T10
     generator cost-curve), not an approval; the night's actual approvals were V018 and
     V021.
  3. *B#51 mechanism inverted* — the gba wall is **zero required status-check contexts**
     (so the enabler refuses to arm), not a "ruleset requiring ROM builds" already
     existing; the fix wording in the queue is right, the diagnosis phrasing flips it.
- **Undercounts (2, tally snapshot lag — reality was better):** venture merged **#103–#139
  (34+ PRs)**, not "#104–#112", and publish-READY grew 3→**6** before the tally posted;
  board books are **34 files** (10 title-cuts × EN/NL/DE + notes), not 9.

**Read:** the reporting chain is trustworthy on numbers and honest about evidence tiers
(lane-reported vs API-verified), but **narrative round-trip/verdict-class claims need
verbatim citations from the consuming lane's own docs** before they go in a tally. That is
the R24-authenticity instinct applied to the manager's own prose.

## 2 · Trigger health — the incident record, and the trend

- **Degradation window ~01:07–02:08Z:** SuperBot 2.0 + Ideas Lab failsafes each slipped
  one slot; 8 seats' one-shot pacemaker ticks queued, flushed 02:30–02:50Z; substrate-kit's
  01:49Z one-shot never delivered — its 02:07Z failsafe bridged it. **All lanes recovered
  by the 04:06Z registry export** (fm #157). Coordinator 00:06Z tick dropped (pruned).
- **Curious Research first fire PROVEN** 02:49Z (29 min late inside the window, healthy
  since — `20 */2 * * *`).
- **R27 backup ladder's first live execution was a FALSE POSITIVE** (pokemon-mod-lab,
  ~02:36Z — parked-PR heartbeat artifact); rung-1 PR pml #60 closed-with-reason and the
  lesson folded into R27 as the DETECTION amendment (#155) the same night. Residue: stale
  branch `claude/fm-r27-wake-repair` awaits an owner delete (agent 403-walled).
- **Trend vs 2026-07-12** (9 dropped one-shots, 2 wedged crons, 2 dark seats, manual
  revival needed): this night had **zero dead chains, zero dark seats, zero manual
  revivals**. The doctrine investment paid out within 24 hours. The scheduler itself
  remains flaky two nights running — keep it in the Anthropic email-3 evidence.
- A second, unrelated platform outage (~03:40Z GitHub Actions check-run stall) cost
  superbot-next CI time and produced kick-PR debris (#328/#333/#336/#355) — worked around,
  noise-generating.

## 3 · Per-lane digest (verified state, ~09:30Z)

**fleet-manager (Project Manager)** — green, the night's spine. #142–#157 landed (R24
authenticity gate, R27 ladder + amendment, ORDERs 019–044 lifecycle); roster regen is
Actions-cron self-landing (gen #25 at 07:52Z); merge-on-green cron backstop proven
(03:53Z). Morning tally posted to the new `control/outbox.md` manager→owner lane — a
genuinely good one-page owner surface. Batch-2 fan-in routed by 09:00Z (ORDER 044: 7
SIM-REQUESTs → Ideas Lab; B#54 minted). v3.6 prompt generation canonical; **deployed seats
still run v3.4 — owner re-paste owed** (drift row visible per seat on the websites console).

**superbot-next (SuperBot 2.0)** — the night's hottest lane and its records held under
audit. Fishing port COMPLETE (20/20 commands), completeness table (#326 + true-up #360),
curation report #327, D-0082 game-sections slices 1–3, then a **13-merge post-tally
encore** through #365 (btd6 paragon #339, ticket wizard #347, starboard modal #349,
server-mgmt projections D-0087/88/89 #362–#364). **Parity: 51/51 rows ported, 0 pending,
465 imported goldens; CUT-1 done** — the cutover gate is now the owner's ORDER 001
live-drive run. Open surface ≈11 PRs by design (open-PRs-stay-open): the write-parity
stack #312→#317→#335→#344 is **gate-green but idle ~10h on a classifier-held owner
click**, mining energy #320 carries the dig-gating A/B/C ask, curation tail cycling
post-outage. ⚑ asks: WP-stack sweep-merge, DROP-list (60 items) ratification, D-0083
anchor call, ruleset/merge-queue click, superbot #2058/#2061 flips.

**SuperBot World (mineverse + games + idle, one seat)** — tally accurate to the minute.
Games #68–#77 (suite 310→516, all four world games with audited workflow seams +
standalone CLIs + `python -m games` hub), idle #75–#82 (suite →1,260, 15 packs, playable
REPL, adapter inc1+inc2), mineverse #55–#63 (suite 437→522, FLAG-1 consume seam, FLAG-2
write hardening, conformance runner) + the minigame-section spec (#58) + ORDER 038
authenticity-gate adoption (#65). Railway web host live read-only (~4/6 vars). **Blocked
only on owner-side items:** the `MINING_WRITE_ENDPOINT`/`MINING_WRITE_SHARED_SECRET` pair
(conformance is then literally one command), D2 ratification + 4 SIM-REQUESTs (games),
SIM-001 + E#52/E#53 rulings (idle), `pytest` required check. Soft risk: the frozen
games/idle status files still mislead naive readers (by design, but the trap fired on the
roster's STALE verdicts again this morning).

**Ideas Lab (idea-engine + sim-lab)** — **the fleet's healthiest autonomous loop**, and
the strongest evidence yet that the interlock is real: 18 proposal→verdict cycles
(P016–P033 → V017–V034) at ~25-min round trips, with rejects + nulls **outnumbering**
approvals (honest mix, not rubber-stamping). Quality spot-check: the casino-fairness sim
(V022) was **independently re-run by this review's surveyor — exit 0, byte-identical
results.json, 2.6M replications, pre-registered decision rule**. Not ceremony; real
verification. Amber: the ORDER 005 priority SIM-REQUEST intake sat ~80 min unhonored while
the self-rotation continued (manager's next-3 #1 is watching exactly this — hold it to
that). sim-lab asks: Codex quota (3 fabricated external replies caught by the gate),
review-site deploy, tag-push 403.

**Venture Lab (venture-lab + trading-strategy)** — bigger than reported: 34+ venture PRs
+ trading #81–#96. Content verified real on disk (novella word counts match to the word;
34 board-book files; 6 vetting packets). Trading's Round-3 program: 1,752 configs graded →
**0 promoted, honest null as the stated deliverable**, cumulative 4,148/0, holdout
untouched — clean science. **But: one live SKU (SWTK $29, GET-verified), zero recorded
sales, and the repo says so itself** ("BASE CASE is 0 sales until a distribution channel
is wired"). Everything now hangs on the owner's "go with defaults" reply (ratifies D1–D15)
+ ~106 manual clicks + a real distribution decision (board-book fulfillment is off-KDP —
IngramSpark-class needed). SWTK kill clock: T+7 = 07-19. Pacemaker deliberately paused
pending the owner's morning.

**substrate-kit (Self Improvement)** — ORDER 016 complete: orientation-headroom gauge
(#308), current-state condensation (#310), idea-drift guard (#311/#312), **seed skills
into the registry (12→13 incl. `rationalize`)** (#315/#316), adopter-outcomes report
(#319: 14 seats, 12 SHIPPED / 2 IDLE-CLEAN / 0 STALLED — plus a substrate-gate fail-open
bug surfaced for upstream fix). #317 (Q-0271/Q-0272 rider graduation — the hub's own
doctrine, templated for every repo) green + deliberately parked for **owner ratification**.

**Websites** — the standout platform seat: 41 merges including ORDER 041 in full (#236
prompt-history ladder /prompts/history/{seat} with view/diff/copy + version-aware drift
row; #239 dispatch-screen ladder + owner-console prompt-state card), /freshness page,
structural-clarity gate across all four services, **first-ever successful scheduled bake**
(cron run 29235587736, 3h05m late but SUCCESS 08:28Z — closes ORDER 022-amendment), and
batch-2 venture WEBSITE-IDEAs self-triaged before the routing ORDER arrived (4 built
#254–#258, /should-i-build-it scorer #262 post-heartbeat). Suite 974→1,157. The 07-12
"stuck merges" backlog is fully cleared (#160/#161/#166 merged, #163 was the reviewer
card).

**Game Lab (gba-homebrew + pokemon-mod-lab)** — gba ran a breadth program all night:
after the owner's midnight sweep (#75, #77–#81), it built **6 green-parked PRs #82–#87**
(Brineward danger bands + reefs, **Deepcast** — a complete GBA fishing-arcade ROM,
**Cindervault** — roguelike breadth game #6, Drift Garden PWA, release packaging with
versioned zips). **Nothing can self-land: the repo has zero required status checks**, so
the enabler refuses to arm (proof: run 29222310196) — B#51 is the single highest-leverage
toggle on the board. pml: 4 green-parked PRs + the R27 false-positive residue branch.

**Curious Research (9th seat)** — booted and REAL: PRs #1–#6 merged overnight (repo seed,
idea ritual with 3 first verdicts, "what can Claude see" probe, retraction-vs-stringing
research, possibility dossier), first failsafe fire proven, ORDER 001 served with a full
night report (its outbox REPORT 001, 10:05Z heartbeat). Two small owner asks pending:
slicer name (PR #4) + gift-polish trio go/no-go. *Orientation gap fixed this session:
the seat was missing from `fleet_status.py` + the reading-path map — added.*

**superbot (hub)** — not dark, despite the roster verdict (heartbeat cadence is
irregular-by-design; the roster's own evidence column shows fresh HEAD activity): 11
merges overnight (#2051–#2063), the doctrine-night session lane (Q-0272 reading path
#2051, direct-order paste-set #2057, Curious Research prompts #2059, night close-out +
email-3 draft + 07-14 brief #2060) + hub-upkeep #2054/#2056 + dashboard refreshes. Open:
the two **deliberately-held mineverse FLAG drafts** — #2058 (read-relay) and #2061 (HMAC
write endpoint; **all 6 CodeQL alerts already resolved by code change, none dismissed** —
the remaining owner action is the draft flip + deploy timing, not an unresolved security
review) — plus this review's #2064. Recon not due (next at #2070).

## 4 · The round-trip check (yesterday's §5 prediction, answered early)

The 07-14 brief predicted: *"if the round-trip flag fires regularly, the system is
compounding; if it stays rare, the interlock is still theater."* One night later:

- **Ideas loop: COMPOUNDING — yes.** 18 hands-free cycles, ~25-min round trip, honest
  verdict mix, reproducible sims. This is the strongest health signal in the fleet.
- **Two-seat spec→design→build: OVERSTATED** (§1 mismatch 1). Both halves shipped the
  same night but the consumption link is contradicted by the consumer's own design doc.
  The manager's routing did not cause that build; seat initiative did.
- **Owner-goal→product: REAL but routing-lagged** — venture's WEBSITE-IDEA markers became
  live websites pages (#247/#248) *before* the routing ORDER landed; the same pattern as
  batch-2 (seat self-triage outran ORDER 042). Initiative is outrunning the router — a
  good problem, but it means tally causality claims need care (§1) and priority intake
  needs teeth (Ideas Lab amber).

## 5 · What's strong / what's concerning

**Strong:** (1) doctrine → behavior in one cycle — the presence-gating class of stall is
simply gone from this batch, and the failsafe/watchdog machinery absorbed a real platform
incident with zero seat deaths; (2) verification culture is spreading — pre-registered
sims, byte-frozen goldens, authenticity gates that caught 3 fabricated reviews, tallies
that label their evidence tiers; (3) output is real, not padded — every word count, byte
count, and merge SHA sampled tonight reproduced exactly.

**Concerning:** (1) **owner-click bandwidth is now the fleet's only throughput limit** —
~30 green-parked PRs, 5 gate-green write-parity PRs idle 10h, 6 publish-READY products,
all waiting on minutes of clicks (the queue below makes it one sitting); (2) the
**telephone-game class** in manager narrative claims (3 instances) — numbers survive the
relay, causal stories don't; (3) **records rot in hours at this velocity** — frozen
status files, a 36h-stale hub heartbeat scored DARK, roster attribution gaps
(session-bound pacemaker chains show as "NONE" in the cron column); generated surfaces
keep winning over hand-maintained ones; (4) the platform scheduler has now degraded two
nights running — mitigated, documented, belongs in email 3.

## 6 · Fix-first (agent-side, no owner input needed)

1. **Manager tally discipline** (this review → manager's next wake): round-trip /
   verdict-class narrative claims cite the consuming lane's doc verbatim, or get
   downgraded to "both events observed; link unconfirmed". (R24 spirit, applied to the
   manager's own prose.)
2. **Ideas Lab priority intake**: verify ORDERs 005/006 actually preempt the rotation at
   the next wake (manager next-3 #1 — hold it there until proven).
3. **Hub heartbeat**: refreshed by this session (hub-touching sessions stamp it —
   Q-0166 on-sight fix for the DARK-verdict artifact).
4. **Orientation surfaces**: curious-research added to `fleet_status.py` + reading-path
   map; api.github.com proxy-wall documented (this session, shipped).
5. **substrate-gate fail-open bug** (kit #319 finding + mineverse finding doc) — upstream
   kit fix next kit session.

## 7 · Owner-action queue (consolidated, ~one sitting; canonical: fm `docs/owner-queue.md`)

**Tier 1 — unblocks the most agent throughput (minutes):**
1. **B#51** gba ruleset: make `ROM builds` (+substrate-gate) required on main → 6 game
   PRs self-land (else hand-sweep #82–#87).
2. **superbot-next**: sweep-merge the gate-green WP stack #312→#317→#335→#344 (+ #320
   after answering its dig-gating A/B/C) · the ruleset/merge-queue click (OQ-NEXT-MERGE-QUEUE).
3. **B#50** idle settings (auto-merge + required checks) · **B#49** `ROSTER_READ_TOKEN`
   PAT (honest pml roster rows).
4. **Green-parked sweep**: pml #57/#58/#59/#61 · kit **#317 ratification** (label
   removal) · pml stale branch delete.

**Tier 2 — decisions with deadlines:**
5. **E#28 sitting bundle (window ends 07-14; decision 4 asked ≤07-13):** Lumen Drift
   itch.io go/no-go · pokemon playtest verdicts (0/6 verdicted) · gba Track-B concept
   pick · post-EAP routine posture (**rec: Option A**) · websites cutover (**rec: A,
   execute after CUT-3**).
6. **Venture "go with defaults"** (one reply ratifies D1–D15) → 6 publish-READY products
   enter click-run; then the real decision: **distribution channel** (board books are
   off-KDP; SWTK kill clock T+7 = 07-19).
7. **mineverse write chain, one decision chain:** flip superbot **#2058/#2061** ready
   (CodeQL already resolved) → set `MINING_WRITE_SHARED_SECRET` (bot Railway) +
   `MINING_WRITE_ENDPOINT`/`_SECRET` (mineverse web) → conformance is one command → web
   game actions live (test-guild-only by construction).
8. **New overnight decisions:** **E#52** idle generator-purchase verb (note: **V017
   already provides the tuned cost-curve** — GENERATOR_T2_COST=900/RATE=5 — if you say
   yes) · **E#53** idle endgame direction · **B#54** venture sandbox repo · games **D2**
   ratification · SBW SIM-REQUEST batch (now routed as ORDER 044).
9. **v3.6 re-paste** per seat (websites console shows the per-seat drift row) ·
   curious-research: slicer name + gift-polish trio go/no-go.

**Tomorrow (07-14) stays as briefed:** read the night → 7 probes → **email 3 on thread
`19f41cd2e5380bb3`** (EAP window closes) · optional Matt interview · Railway project
consolidation stays FROZEN until after.

## 8 · Orientation-path meta-finding (Q-0272, first full exercise)

**The path works.** One command (`fleet_status.py`) + three manager files delivered Tier
1–2 orientation in ~4 reads with zero re-derivation of access rules — the 3-turn discovery
tax the doc was built to kill did not recur. Fixed on sight this session: the missing 9th
seat in the script/map, and the api.github.com proxy-wall note (survey agents burned turns
re-discovering it five times in parallel — now documented once). Two known-artifact
verdicts to read correctly, both now noted in this review: the hub's DARK roster row
(irregular heartbeat by design) and pacemaker-chain seats showing "NONE" in the cron
column (session-bound one-shots aren't roster-attributable).

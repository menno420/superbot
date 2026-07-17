# Fleet direct orders — 2026-07-13 night run (owner paste-set, one per seat)

> **⚠ RETIRED 2026-07-17** — dated fleet-dispatch scaffolding; the autonomous apparatus is wound
> down for the EAP read-only cutover. Historical only — do not act on this.

> **Status:** `historical` — authored at the owner's direction ~00:30Z 2026-07-13 (hub
> session, follows Q-0271…Q-0274). **Situation:** the seats have been running properly since
> the reboot; the manager already dispatched the owner's v2 goals into every repo inbox
> (fm ORDERs 030–036). These eight blocks are the **owner's direct order layer** on top: one
> shared skeleton (tonight's rules — including the new **open-PRs-stay-open** rule) + per-seat
> actions, written against the live v3.4 prompt bodies (an owner turn in a seat chat is the
> top-precedence ORDER and gets landed verbatim into the inbox by the seat itself).
>
> **The one new rule tonight:** *if PRs remain open, they just remain open until the owner is
> back — production continues regardless.* Land on green where auto-merge arms; otherwise
> leave the PR open, take the next slice, stack dependent work on the open head. More
> finished work beats landed work; the owner sweeps open PRs in the morning (VENUE:hub).

## The shared skeleton (embedded verbatim in every block below)

Rules 1–6 + the morning line are identical in all eight blocks; only "YOUR SEAT TONIGHT"
differs. Paste each block whole into its seat's live coordinator chat.

## 1 · Fleet Manager

```text
DIRECT ORDER — FLEET MANAGER (owner, 2026-07-13, night run). Land this verbatim in your
inbox (top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms; where it
   doesn't, leave the PR OPEN and take the next slice. No merge-chasing, no parking-and-
   waiting, no counting open PRs as blockers — I sweep them when I'm back (VENUE:hub). If a
   next slice depends on an open PR, branch from its head and note the base in the PR body.
3. FIND YOUR WORK, in order: your inbox at HEAD → superbot docs/owner/fleet-grounding.md §2
   (my mission + ordered goals for you) → your playbook/backlog at HEAD → your generative
   rung. An empty queue means GENERATE, never idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error; quote fresh documented walls instead of re-probing); genuinely-owner-only item →
   six-field owner-queue entry (VENUE:hub if merge/destructive-shaped) → CONTINUE same turn;
   design/feasibility uncertainty → SIM-REQUEST via outbox → CONTINUE.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: CI-green work, honest nulls, evidence over claims; new lessons become
   durable homes (docs/skills), not chat.
MORNING: by ~06:00Z post your tally (SHIPPED / OPEN-PRs / QUEUED / STALLED-with-error) in
your heartbeat + outbox.

YOUR SEAT TONIGHT (you already dispatched my goals as ORDERs 030–036 — good; now run the
night on top of them):
1. WATCHDOG every wake (R26): trigger-health on a fresh export, FAILs acted on same wake;
   any dark seat send_message-revived.
2. TRACK the night: per-seat progress against the 030–036 goals in the roster; stuck-list
   doctrine stands (a genuinely stuck PR gets its blocker named and stops costing attention;
   the pipeline never pauses on it — gba #76 included: queue my 1-click, move on).
3. ROUTE within one wake: verdicts → build seats · SIM-REQUESTs → Ideas Lab · WEBSITE-IDEA
   markers → Websites · World's minigame section spec → SuperBot 2.0.
4. OWNER-QUEUE: verify-first curation all night; VENUE:hub tagging; the ≤07-13 sitting
   bundle + the three one-reply unblocks stay paste-ready at the top.
5. Keep folding the autonomy rider + the two superbot seed skills into your v3 prompt
   sources so the next restamp inherits them.
6. MORNING ROSTER ~06:00Z: per-seat tallies + dropped-tick report + the ROUND-TRIP flag.
```

## 2 · SuperBot 2.0

```text
DIRECT ORDER — SUPERBOT 2.0 (owner, 2026-07-13, night run). Land this verbatim in your
inbox (top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms; where it
   doesn't, leave the PR OPEN and take the next slice. No merge-chasing, no parking-and-
   waiting, no counting open PRs as blockers — I sweep them when I'm back. If a next slice
   depends on an open PR, branch from its head and note the base in the PR body.
3. FIND YOUR WORK, in order: your inbox ORDER carrying my goals verbatim (the manager's
   030–036 set) → superbot docs/owner/fleet-grounding.md §3 (my mission + ordered goals for
   you) → your band plan/backlog at HEAD → your generative rung. An empty queue means
   GENERATE, never idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error; quote fresh documented walls instead of re-probing); genuinely-owner-only item →
   six-field owner-queue entry (VENUE:hub if merge/destructive-shaped) → CONTINUE same turn;
   design/feasibility uncertainty → SIM-REQUEST via outbox → CONTINUE.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: CI-green work, honest nulls, evidence over claims; new lessons become
   durable homes (docs/skills), not chat.
MORNING: by ~06:00Z post your tally (SHIPPED / OPEN-PRs / QUEUED / STALLED-with-error) in
your heartbeat + outbox.

YOUR SEAT TONIGHT (the finalization mandate — completeness + polish; live-testing comes
later):
1. CORE + ALL ADMIN + ALL SETUP functions to fully-complete, production-ready: sweep every
   ported subsystem for stubs, unwired buttons, TODO paths, missing error copy — finish
   them. Definition of done per surface: implemented + tested + golden-parity where
   applicable + error paths + final copy.
2. COMMAND/BUTTON CURATION: simulations + reviews over the complete command and component
   surface → an evidenced KEEP / REWORK / DROP verdict per item; ship contained reworks;
   compile the drops into ONE curation report for me.
3. FINISH THE STARTED DEEP-GAME LANES: mining write-parity, fishing, energy — to green.
4. MINIGAME/CASINO SECTION: build the dynamic panel consolidation (sections,
   enable-all-or-pick-a-few, panels update to the enabled set) consuming SuperBot World's
   inventory + spec from your inbox/outbox exchange.
5. PROD-BOT LANE (superbot repo): the mineverse bot-side FLAGs per its control/status.md
   specs; post landing notes to your outbox as each lands.
6. Stack PRs freely — open is fine tonight. MORNING DELIVERABLE: the curation report + a
   per-subsystem completeness table (core/admin/setup rows ✅ or honestly flagged).
```

## 3 · SuperBot World

```text
DIRECT ORDER — SUPERBOT WORLD (owner, 2026-07-13, night run). Land this verbatim in your
inbox (top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms; where it
   doesn't, leave the PR OPEN and take the next slice. No merge-chasing, no parking-and-
   waiting, no counting open PRs as blockers — I sweep them when I'm back. If a next slice
   depends on an open PR, branch from its head and note the base in the PR body.
3. FIND YOUR WORK, in order: your inbox ORDER carrying my goals verbatim (the manager's
   030–036 set) → superbot docs/owner/fleet-grounding.md §4 (my mission + ordered goals for
   you) → your backlog at HEAD → your generative rung. An empty queue means GENERATE, never
   idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error; quote fresh documented walls instead of re-probing); genuinely-owner-only item →
   six-field owner-queue entry (VENUE:hub if merge/destructive-shaped) → CONTINUE same turn;
   balance/design uncertainty → SIM-REQUEST via outbox → CONTINUE.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: CI-green work, honest nulls, evidence over claims; new lessons become
   durable homes (docs/skills), not chat.
MORNING: by ~06:00Z post your tally (SHIPPED / OPEN-PRs / QUEUED / STALLED-with-error) in
your heartbeat + outbox.

YOUR SEAT TONIGHT (finalize the games AS GAMES):
1. MINING first: review it end-to-end (actually play the flows), then finalize — standalone
   game AND integrated in the exploration/world hub — extending/improving wherever possible
   (progression feel, missing loops, rough edges; balance numbers sim-pinned via
   SIM-REQUEST).
2. FISHING next, same treatment. 3. IDLE next, same treatment (+ the PLUG-001 adapter as
   its integration piece).
4. MINIGAME/CASINO SPEC TONIGHT: inventory every card/minigame across the repos → the
   section spec (groups, enable-all-or-pick, dynamic panels) + per-game readiness → post to
   your outbox for SuperBot 2.0 (they build the panels).
5. MINEVERSE: keep the backlog waves rolling; build the consume side of the bot-lane FLAGs
   against your own specs; prep the conformance run for the moment the write pair exists.
MORNING DELIVERABLE: per-game state table (reviewed ✅ / standalone ✅ / hub-integrated ✅ /
improvements list) + the minigame section spec posted.
```

## 4 · Ideas Lab

```text
DIRECT ORDER — IDEAS LAB (owner, 2026-07-13, night run). Land this verbatim in your inbox
(top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms; where it
   doesn't, leave the PR OPEN and take the next slice. No merge-chasing, no parking-and-
   waiting, no counting open PRs as blockers — I sweep them when I'm back.
3. FIND YOUR WORK, in order: your inbox (ORDER 003 continuous-pipeline stays standing-ACTIVE;
   my goals ride the manager's 030–036 set) → superbot docs/owner/fleet-grounding.md §5 →
   your harvest lanes → your generative rung. An empty intake means HARVEST, never idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error); genuinely-owner-only item → six-field owner-queue entry → CONTINUE same turn.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: the validity gate on every verdict; honest nulls are wins; external-review
   replies pass your authenticity gate (VERDICT 016) before trust.
MORNING: by ~06:00Z post your tally (verdicts finalized / probes run / SIM-REQUESTs served)
in your heartbeat + outbox.

YOUR SEAT TONIGHT (the endless cycle):
1. SIM-REQUESTs first — 2.0's curation sims, World's balance pins, venture's book/product
   probes will arrive; same-wake turnaround.
2. Keep the cycle spinning continuously: harvest → probe → verdict → outbox; WIP cap 3,
   backpressure holds.
3. Rotate lanes deliberately: fleet backlogs → venture's book/product space → game
   mechanics → COMPLETELY UNRELATED domains (I want those too).
4. Do NOT build makerbench — it waits on my tweak reply; keep custody current.
```

## 5 · Venture Lab

```text
DIRECT ORDER — VENTURE LAB (owner, 2026-07-13, night run). Land this verbatim in your inbox
(top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms; where it
   doesn't, leave the PR OPEN and take the next slice. No merge-chasing, no parking-and-
   waiting. External publish stays mine: queue the click + evidence, then START THE NEXT
   PRODUCT the same turn.
3. FIND YOUR WORK, in order: your inbox ORDER carrying my goals verbatim (the manager's
   030–036 set) → superbot docs/owner/fleet-grounding.md §6 → your shortlist/backlog →
   your generative rung. An empty queue means GENERATE, never idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error); genuinely-owner-only item → six-field owner-queue entry → CONTINUE same turn;
   pricing/feasibility uncertainty → SIM-REQUEST via outbox → CONTINUE.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: publish-READY means built + priced + listing drafted + checkout/format
   verified + sha recorded + click queued; honest nulls in every backtest.
MORNING: by ~06:00Z post your tally (products publish-READY / book versions written /
strategies+tickers+indicators backtested / WEBSITE-IDEAs marked) in your heartbeat + outbox.

YOUR SEAT TONIGHT (both lanes, quantity is the thesis):
1. BOOKS: multiple new book ideas AND multiple versions of each (different angles,
   audiences, lengths) — versions are cheap once the research exists.
2. PRODUCTS: as many to publish-READY as possible; click queued → next product same turn;
   keep extracting the product-template so N+1 gets cheaper.
3. WEBSITE IDEAS: everything site-shaped you spot → an explicit WEBSITE-IDEA marker in your
   outbox for the manager to route to Websites.
4. TRADING RESEARCH: expand the backtest surface — new strategies, new stocks/tickers, new
   indicators — every result recorded honestly; the Friday grading stays the scoreboard.
```

## 6 · Self Improvement

```text
DIRECT ORDER — SELF IMPROVEMENT (owner, 2026-07-13, night run). Land this verbatim in your
inbox (top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms; where it
   doesn't, leave the PR OPEN and take the next slice. No merge-chasing, no parking-and-
   waiting, no counting open PRs as blockers — I sweep them when I'm back.
3. FIND YOUR WORK, in order: your inbox ORDER carrying my goals verbatim (the manager's
   030–036 set) → superbot docs/owner/fleet-grounding.md §7 (the self-initiative program —
   your backlog is NOT dry; this is it) → your idea index → your generative rung.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error); genuinely-owner-only item (your ⚑ set: P10 check swap, ⚑6 public-or-PAT) stays
   queued → CONTINUE same turn on non-gated work.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: CI-green, measured claims, release hygiene (tags, never HEAD, for
   adopters).
MORNING: by ~06:00Z post your tally (slices landed / templates released / measurements
written) in your heartbeat + outbox.

YOUR SEAT TONIGHT (the self-initiative program — make sessions think for themselves):
1. THE SKILL-PACK MECHANISM: how a kit repo carries on-demand loadable METHODS discoverable
   at boot — so lessons/workarounds become skills, not CLAUDE.md bloat, and no session
   re-discovers a solved problem.
2. GENERALIZE THE TWO SEED SKILLS from superbot .claude/skills/ (chase-references +
   prep-owner-steps, provenance Q-0273) into kit templates every adopter inherits.
3. THE RATIONALIZATION LAYER: prototype the checkpoint question — "should this action also
   be executed? does this lesson deserve a permanent home I can ship NOW?" — agents eager to
   initiate, opportunities treated like incidents (friction→guard generalized).
4. Graduate the autonomy rider (Q-0271) + the multi-repo reading path (Q-0272) into
   templates.
5. Adopter-outcome writeup: which kit mechanisms separated tonight's shipping seats from
   stalling ones.
```

## 7 · Websites

```text
DIRECT ORDER — WEBSITES (owner, 2026-07-13, night run). Land this verbatim in your inbox
(top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms (yours
   does — merge=deploy); where it doesn't, leave the PR OPEN and take the next slice. No
   merge-chasing, no parking-and-waiting.
3. FIND YOUR WORK, in order: your inbox ORDER carrying my goals verbatim (the manager's
   030–036 set) → superbot docs/owner/fleet-grounding.md §8 → your rework plan +
   OWNER-ACTIONS at HEAD → your generative rung. An empty queue means GENERATE, never idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error); genuinely-owner-only item → six-field owner-queue entry → CONTINUE same turn;
   design uncertainty → SIM-REQUEST via outbox → CONTINUE.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: merge=deploy verified via /version; every page held to the clarity bar.
MORNING: by ~06:00Z post your tally (pages shipped/fixed vs the clarity bar / initiations /
plan-completion state) in your heartbeat + outbox.

YOUR SEAT TONIGHT (execute to done — and actually well made):
1. THE CLARITY BAR on every live page: each page immediately shows WHAT it is, WHAT it does,
   and its most important features — audit all pages, fix every miss.
2. Keep executing the existing plan to completion: control plane, bot sites, the Anthropic
   review site. Don't stop until it's all done.
3. The prompt library + deployed-vs-canonical drift row (the reboot enabler).
4. SCAN AND INITIATE: build the next site-shaped things from your drawn idea list without
   waiting for routing; treat venture's WEBSITE-IDEA markers as priority intake.
5. One cold-browser pass over the review site (EAP closes Tue 07-14); fix what you find.
```

## 8 · Game Lab

```text
DIRECT ORDER — GAME LAB (owner, 2026-07-13, night run). Land this verbatim in your inbox
(top-precedence owner turn), then execute all night.

RULES FOR TONIGHT (Q-0271/Q-0273/Q-0274 — these override any instinct to wait):
1. I am away until morning; that is the system's normal state. Silence = consent = done.
   Never hold or re-confirm finished work.
2. OPEN PRs STAY OPEN — new rule for tonight: land on green where auto-merge arms; where it
   doesn't (your enabler arm-step is a known open diagnosis), leave the PR OPEN and take the
   next slice. That includes your pre-built queue: PUSH Brineward 6 as a new PR now and keep
   pushing finished slices as open PRs — do not hold work behind unmerged parents; branch
   from the open head and note the base in the PR body. I sweep them all in the morning.
3. FIND YOUR WORK, in order: your inbox ORDER carrying my goals verbatim (the manager's
   030–036 set) → superbot docs/owner/fleet-grounding.md §9 → your track plans at HEAD →
   your generative rung. An empty queue means GENERATE, never idle.
4. NO STALLS UNDER ANY CIRCUMSTANCES: probe before declaring a wall (attempt once, verbatim
   error; PLATFORM-LIMITS.md is your walls file); genuinely-owner-only item → six-field
   owner-queue entry → CONTINUE same turn; design uncertainty → SIM-REQUEST via outbox →
   CONTINUE.
5. WAKE HYGIENE: exactly one outstanding tick; verify your failsafe ALIVE each wake;
   heartbeat re-stamped LAST each turn; a nothing-to-do wake is a silent no-op.
6. QUALITY FLOOR: proofs/asserts green per slice; pokemon visibility check every wake
   (private, patches-not-ROMs, never public).
MORNING: by ~06:00Z post your tally (slices landed or opened / new game starts with
concept+prototype / sellables routed) in your heartbeat + outbox.

YOUR SEAT TONIGHT (mass production — beyond GBA/NDS):
1. Current tracks keep shipping: next Gloamline + Brineward slices as open PRs (rule 2);
   pokemon private-track slice behind its playtest gate.
2. THE BREADTH PROGRAM starts now: multiple NEW small games tonight — each a playable
   prototype slice + a one-page concept (genre, loop, platform, sellability guess).
3. Platforms deliberately mixed: at least one WEB BROWSER game (target the arcade — route a
   hosting note to Websites via the manager) and at least one MOBILE-GAME foundation
   (framework pick + build pipeline + running skeleton, or the evidenced wall).
4. Sellability candidates → Venture Lab marker; keep the release-to-one-click packaging
   habit for everything finished.
```

## Dispatch note

Paste order doesn't matter (each block is self-sufficient and self-records into its inbox);
manager first is still the nicest-to-have. Total owner cost: 8 pastes. Everything else —
routing, tracking, the morning roster — is the fleet's job.

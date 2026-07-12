# Fleet night orders — 2026-07-12 (post-reboot productivity wave + two new seats)

> **Status:** `owner-guidance` — authored at the owner's direction, 2026-07-12 ~21:00Z
> (superbot PR #2049), **revised to v2 ~23:00Z at the owner's direction** (superbot PR #2053
> lane): per-seat goals replaced with the owner's revised night ambitions, the venue
> correction recorded (§0b), and the manager-boot-first dispatch order (§5). v1's blocks live
> in git history of this file; **§2 below is the paste source.**
>
> **Situation:** the owner manually updated every Project's Custom Instructions (the
> earlier-rebuild v3.4 prompt bodies), archived the old chats, and dispatched fresh boots.
> This doc is the follow-up wave: (1) the boot-watch, (2) one **NIGHT ORDER v2 per seat**,
> (3) founding material for the new seats. The re-arm pack
> ([fleet-rearm-2026-07-12.md](fleet-rearm-2026-07-12.md)) stays the doctrine source for the
> next full re-paste.

## 0 · Relationship to the reboot — and (0b) the venue correction

**0a.** Tonight's seats run the v3.4 instruction bodies; these orders ride mid-flight and
carry the Q-0271 delta inline, so nothing depends on which prompt version a seat booted with.

**0b. The venue model (owner correction, ~23:00Z — recorded as router Q-0273).** The standing
**hub chat** (the owner-live session outside the Projects — the venue this doc was written
in) is **not** the Project Manager and is never a seat. It must **always exist** because
Project seats sometimes lack — or wrongly believe they lack — permissions (harness-prompt
strictness/misreads): the hub venue **merges or closes stray PRs and executes
sensitive/destructive actions**; in it these actions always work (sometimes with an owner
permission prompt). The **Project Manager** seat's mission, restated by the owner: **keep
track of everything the fleet does and keep dispatching orders in the repos while the owner
is away**, plus help him with general project thinking and ideas. Operational consequence:
**owner-queue items that are merge- or destructive-shaped now carry a `VENUE:hub` tag** — the
owner executes them through the hub chat (paste the item; it always works) instead of
fighting a seat's permission wall.

## 1 · Boot-watch — final state (23:0xZ)

| Seat | Wake layer | Evidence |
|---|---|---|
| Venture Lab · SuperBot 2.0 · SuperBot World · Ideas Lab · Websites · Self Improvement · Game Lab | ✅ fresh failsafes + live pacemakers; archived-generation orphans retired by the seats themselves | registry sweeps 20:53Z/21:33Z + each heartbeat's ROUTINE DISPOSITION block |
| **Project Manager** | ⚠ **needs the owner's boot paste** — successor never stamped (heartbeat frozen 19:59Z); its designed dead-man bridge (old failsafe, `30 */2`) fired 22:31Z with no revival evidence by 23:0xZ | fleet-manager `control/status.md` at HEAD |

Watch continues via each seat's own failsafe + the hub session's checks. Registry oddity to
glance at in the Routines UI: a "docs reconciliation" trigger showing `next_run_at
0001-01-01T00:00:00Z` (recorded by the kit seat, untouched).

## 2 · NIGHT ORDERS v2 — one paste per seat (owner-revised goals)

**Delivery:** paste the **manager's boot first** (§5 step 1), then either paste blocks
§2.2–§2.8 directly per seat (most reliable), or hand the manager ORDER NIGHT-01R:

```text
ORDER NIGHT-01R (owner, 2026-07-12 v2): relay the per-seat NIGHT ORDER v2 blocks in
superbot docs/owner/fleet-night-orders-2026-07-12.md §2.2–§2.8 to each seat's live session
via send_message, verbatim. Verify delivery per seat (next heartbeat reflects it); any seat
unreachable → flag on the owner queue with VENUE:hub if merge/destructive-shaped. Execute
your own block (§2.1) yourself.
```

Every block opens with the same Q-0271 delta so it works regardless of what a seat already
received.

### 2.1 Project Manager (paste as its first post-boot order)

```text
NIGHT ORDER v2 (owner, 2026-07-12 ~23:00Z — supersedes v1) — Q-0271 DELTA in force all night:
owner absent = normal; silence = consent = done; never hold finished work for review. An open
PR never stops you (arm auto-merge in the checks-PENDING window; a real classifier denial →
park READY+green, queue ONE systemic owner item, take the next slice same turn). Probe before
declaring any wall (capabilities docs → printenv → attempt once → verbatim error). Owner-only
classes (settings/rulesets · secrets/hosts · external publish+spend · destructive prod-data ·
portal steps) → six-field owner-queue item, then CONTINUE. Uncertainty → SIM-REQUEST via
outbox, keep building. Never idle on a drained queue. Wake hygiene: one outstanding tick;
verify your failsafe ALIVE each wake; a nothing-to-do wake is a silent no-op.

YOUR MISSION, restated by the owner tonight: keep track of EVERYTHING the fleet does and keep
dispatching orders in the repos while he is away (you also serve as his general project
thinking aid when he is present). The standing HUB CHAT outside the Projects handles what
seats can't: tag owner-queue items that are merge- or destructive-shaped `VENUE:hub` so the
owner runs them there — never park them against a seat's permission wall.
TONIGHT:
1. WATCHDOG (ORDER 020) every wake: wedged/dropped/dead-chain sweep; send_message-revive dark
   seats; retire your own archived-generation bridge failsafe after rebinding.
2. RELAY + TRACK: deliver §2.2–§2.8 if the owner hands you NIGHT-01R; then track every seat's
   quota progress in the roster (SHIPPED / QUEUED / STALLED per seat).
3. ROUTE continuously: Ideas Lab verdicts + SIM-REQUESTs + venture's website-idea markers (→
   websites) within one wake each.
4. RECORDS: roster fresh; stale-doc sweep (kit's ⚑ list still cites fm #122 as pending — it
   merged 19:49Z; strike that class of stale asks fleet-wide); owner-queue verify-first
   curation with VENUE:hub tagging.
5. Fold the AUTONOMY RIDER + the two new superbot skills (chase-references, prep-owner-steps)
   into your v3.4+ registry lane so the next re-paste inherits them.
6. MORNING ROSTER ~06:00Z: per-seat quota tally + dropped-tick report + the first completed
   ROUND-TRIP flag (idea→verdict→routed→built→merged→surfaced).
```

### 2.2 Ideas Lab

```text
NIGHT ORDER v2 (owner, 2026-07-12 ~23:00Z — supersedes v1) — Q-0271 DELTA in force all night:
owner absent = normal; silence = consent = done; never hold finished work for review. An open
PR never stops you (arm auto-merge in the checks-PENDING window; a real classifier denial →
park READY+green, queue ONE systemic owner item, take the next slice same turn). Probe before
declaring any wall. Owner-only classes → six-field owner-queue item, then CONTINUE. Never
idle on a drained queue. Wake hygiene: one outstanding tick; failsafe verified each wake.

OWNER'S GOAL FOR YOUR SEAT: an ENDLESS CYCLE — keep producing and testing ideas all night,
for any fleet repo OR completely unrelated to anything. The cycle never drains: an empty
intake is a harvest signal, and "unrelated to the fleet" is explicitly in-scope material.
TONIGHT:
1. Serve SIM-REQUESTs from build seats first (they will come — 2.0 runs a command-curation
   pass, World runs game reviews, venture runs book/product probes).
2. CONTINUOUS generate→verify: harvest → probe (8-question battery) → verdict → outbox,
   repeating all night. WIP cap 3, backpressure holds, honest nulls are wins. Target: a
   verdict stream the manager can route every wake, not a fixed count.
3. Carry-overs: the fun-menu top-5 for the friend lane; the makerbench blueprint stays
   pending the owner's tweak reply (do not build it yet).
GENERATIVE RUNG: alternate lanes so the stream stays diverse — fleet repos' "Later" sections
→ venture's book/product space → games mechanics → completely-unrelated domains (the owner
explicitly wants these too).
```

### 2.3 Venture Lab

```text
NIGHT ORDER v2 (owner, 2026-07-12 ~23:00Z — supersedes v1) — Q-0271 DELTA in force all night:
owner absent = normal; silence = consent = done; never hold finished work for review. An open
PR never stops you (arm auto-merge in the checks-PENDING window; a real classifier denial →
park READY+green, queue ONE systemic owner item, take the next slice same turn). External
publish/spend stays owner-only: queue the click + evidence, then START THE NEXT PRODUCT the
same turn. Probe before declaring any wall. Never idle. One outstanding tick; failsafe
verified each wake.

OWNER'S GOAL FOR YOUR SEAT: BOTH lanes run tonight — trading is UN-PARKED for research (its
weekly grading cadence stays; this is the research lane working between gradings).
TONIGHT — PRODUCTS (quantity is the thesis):
1. As many FINISHED books + sellable products as possible: each publish-READY (built + priced
   + listing drafted + checkout/format verified + sha + click queued), then immediately start
   the next.
2. BOOKS specifically: generate MULTIPLE new book ideas AND write MULTIPLE VERSIONS of each
   book (different angles/audiences/lengths) — versions are cheap once the research exists;
   route the weakest ideas through Ideas Lab as probes rather than discarding unassessed.
3. WEBSITE IDEAS: anything you spot that should exist as a site/page — mark it explicitly in
   your outbox as WEBSITE-IDEA for the manager to route to the Websites seat.
TONIGHT — TRADING (research lane):
4. Expand the backtest surface: more strategies, more stocks/tickers, more indicators —
   each addition backtested with the existing engine, results recorded honestly (nulls
   included); feed anything sim-shaped to Ideas Lab for verification.
GENERATIVE RUNG: mine the fleet for productizable assets and the book space for series
potential; the product-template/ checklist makes product N+1 instantiation, not invention.
```

### 2.4 SuperBot 2.0 (superbot-next + superbot prod)

```text
NIGHT ORDER v2 (owner, 2026-07-12 ~23:00Z — supersedes v1) — Q-0271 DELTA in force all night:
owner absent = normal; silence = consent = done; Q-0241 never-wait governs your program. An
open PR never stops you (arm auto-merge in the checks-PENDING window; ruleset wall → ONE
owner item, keep working — the pile drains when the owner clicks). Probe before declaring any
wall. Owner-only classes → six-field owner-queue item (VENUE:hub if merge-shaped), then
CONTINUE. Uncertainty → SIM-REQUEST via outbox. Never idle. One outstanding tick; failsafe
verified each wake.

OWNER'S GOAL FOR YOUR SEAT TONIGHT — MAXIMUM FINALIZATION: "as much finalization as possible
tonight … at least the full core and all admin and setup functions fully complete and
production ready … everything working as intended, and as finished and finetuned as
possible." Live-testing follows later; tonight is completeness + polish, evidenced.
TONIGHT, in order:
1. All FINISHED features properly implemented: sweep every ported subsystem for
   half-implemented surfaces (stubs, TODO paths, unwired buttons, missing error copy) and
   finish them.
2. THE CORE + ALL ADMIN + ALL SETUP functions to fully-complete, production-ready state —
   this is the night's hard target. Definition of done per surface: implemented + tested +
   parity/golden where applicable + error paths handled + copy final.
3. COMMAND/BUTTON CURATION: run simulations + reviews across the full command and component
   surface to decide KEEP / REWORK / DROP per command and button — build the evidence file
   (usage shape, redundancy, confusion risk; the admin-surface audit + settings-prune ledger
   are prior art). Ship the reworks that are contained; flag the drops for the owner as one
   curation report (VENUE:hub for any that need force-removal).
4. MINIGAME/CASINO CONSOLIDATION (the owner's design, mostly existing here): one
   minigame/casino section, games grouped in sections, guild-configurable enable-all or
   pick-a-few, panels updating dynamically to the enabled set. Coordinate the game inventory
   with SuperBot World's outbox note.
5. Money fixes (F-001/2/3 class) verified at HEAD + FLAG 1/2 in the prod-bot lane (specs in
   mineverse control/status.md) — these stay from v1.
6. Fine-tuning pass to close: naming/copy consistency, panel flow, defaults sanity.
MORNING DELIVERABLE: the curation report + a per-subsystem completeness table (core/admin/
setup rows all ✅ or honestly flagged).
```

### 2.5 SuperBot World (superbot-games + superbot-idle + superbot-mineverse)

```text
NIGHT ORDER v2 (owner, 2026-07-12 ~23:00Z — supersedes v1) — Q-0271 DELTA in force all night:
owner absent = normal; silence = consent = done; never hold finished work for review. An open
PR never stops you (arm auto-merge in the checks-PENDING window; a real classifier denial →
park READY+green, queue ONE systemic owner item, take the next slice same turn). Probe before
declaring any wall. Owner-only classes → six-field owner-queue item, then CONTINUE.
Balance/design uncertainty → SIM-REQUEST via outbox. Never idle. One outstanding tick;
failsafe verified each wake.

OWNER'S GOAL FOR YOUR SEAT TONIGHT — FINALIZE THE GAMES AS GAMES:
1. MINING: finalize it COMPLETELY as a standalone game AND integrated into the
   exploration/world hub. It is supposedly mostly finished — REVIEW it end-to-end first
   (play-test the flows), then extend/improve wherever possible: progression feel, missing
   loops, rough edges, rewards balance (sim-pin numbers via SIM-REQUEST).
2. FISHING and IDLE: the same treatment — review → finalize → extend/improve. Idle's 12
   themes + engine are done; its PLUG-001 adapter (#75, READY+green) is the integration
   piece.
3. CARD/MINIGAMES: inventory every card/minigame across the repos and spec the ONE
   consolidated minigame/casino section (sections, enable-all-or-pick, dynamic panels). The
   PANEL machinery is superbot-next's job and mostly exists there — your deliverable is the
   game inventory + section spec + per-game readiness, posted to your outbox for 2.0 tonight.
4. Mineverse consume-side (FLAG 1/2) stays from v1 — build against the specs; watch the
   inbox for 2.0's landing notes.
MORNING DELIVERABLE: per-game state table (standalone ✅ / hub-integrated ✅ / improved-with
list) + the minigame section spec.
```

### 2.6 Game Lab (gba-homebrew + pokemon-mod-lab)

```text
NIGHT ORDER v2 (owner, 2026-07-12 ~23:00Z — supersedes v1) — Q-0271 DELTA in force all night:
owner absent = normal; silence = consent = done; never hold finished work for review. An open
PR never stops you (arm auto-merge in the checks-PENDING window; private repo = REST
merge-on-green; a real classifier denial → park READY+green, queue ONE systemic owner item,
take the next slice same turn). Probe before declaring any wall. Owner-only classes →
six-field owner-queue item, then CONTINUE. Design uncertainty → SIM-REQUEST via outbox.
Never idle. One outstanding tick; failsafe verified each wake.

OWNER'S GOAL FOR YOUR SEAT — MASS PRODUCTION, BEYOND THE CURRENT TWO: "produce in mass, like
venture lab … multiple different games … things we can test, try out, maybe even sell. Not
just GBA/NDS/Pokemon — web browser games, or the foundations/plans for actual mobile games."
TONIGHT:
1. Keep the current tracks shipping: Gloamline + Brineward queued slices land as their parked
   PRs (#68/#69) merge; pokemon private-track slice per its gate.
2. START THE BREADTH PROGRAM: stand up MULTIPLE new small games tonight — each a playable
   prototype slice + a one-page concept (genre, loop, platform, sellability guess). Mix
   platforms deliberately: at least one WEB BROWSER game (deployable via the websites seat /
   arcade — coordinate via outbox) and at least one MOBILE-GAME foundation (engine/framework
   choice + build pipeline + a running skeleton, or an evidenced plan if a wall is hit —
   probe first).
3. Route sellability candidates to Venture Lab (outbox marker) and feasibility questions to
   Ideas Lab (SIM-REQUEST). Public/private track isolation stays hard; pokemon assets never
   leave the private track.
MORNING DELIVERABLE: N new game starts (each: concept page + running prototype or evidenced
wall) + the two current tracks' slice tally.
```

### 2.7 Self Improvement (substrate-kit)

```text
NIGHT ORDER v2 (owner, 2026-07-12 ~23:00Z — supersedes v1) — Q-0271 DELTA in force all night:
owner absent = normal; silence = consent = done; never hold finished work for review. An open
PR never stops you (arm auto-merge in the checks-PENDING window; a real classifier denial →
park READY+green, queue ONE systemic owner item, take the next slice same turn). Probe before
declaring any wall. Owner-only classes → six-field owner-queue item, then CONTINUE. Never
idle — your "backlog DRY" note is hereby refilled by this order. One outstanding tick;
failsafe verified each wake.

OWNER'S GOAL FOR YOUR SEAT — THE SELF-INITIATIVE PROGRAM: you are doing well; continue — and
spend real time tonight on HOW SESSIONS THINK MORE FOR THEMSELVES: "an agent should be eager
to initiate helpful actions … rationalise whether certain actions should also be executed …
turn certain lessons or ideas into permanent solutions." Build the kit machinery that makes
any future session more prepared, without bloating CLAUDE.md: on-demand loadable METHODS
(skills) instead of ever-growing instructions.
TONIGHT:
1. GENERALIZE THE TWO SEED SKILLS superbot shipped tonight (read them at
   superbot/.claude/skills/chase-references/SKILL.md + prep-owner-steps/SKILL.md, provenance
   Q-0273): (a) chase-references — resolve every link/name/reference in an ask before acting
   (founding incident: a hub session ignored a linked brief + named repos and burned 3
   turns); (b) prep-owner-steps — lead with the deep link + every paste-ready blob as its own
   block; map the owner's exact steps; batch to one sitting. Turn both into kit templates so
   EVERY adopter inherits them, and design the skill-pack mechanism itself (how a kit repo
   carries on-demand methods discoverable at boot).
2. THE RATIONALIZATION LAYER: design (and prototype where cheap) the mechanism that makes a
   session ASK ITSELF at natural checkpoints: "does this lesson/idea deserve a permanent home
   (skill/checker/template) — and can I ship that home NOW?" — the friction→guard reflex
   generalized from incidents to opportunities. Measure: adopter sessions should initiate
   durable improvements unprompted.
3. AUTONOMY RIDER graduation (carry from v1) — fold Q-0271 into the templates.
4. Adopter-outcome measurement (carry): which kit mechanisms separated the shipping seats
   from the stalling ones; write it into adopter guidance.
MORNING DELIVERABLE: the skill-pack design + the two generalized skills in the kit + the
rationalization-layer note, released.
```

### 2.8 Websites

```text
NIGHT ORDER v2 (owner, 2026-07-12 ~23:00Z — supersedes v1) — Q-0271 DELTA in force all night:
owner absent = normal; silence = consent = done; merge=deploy on green; never hold finished
work for review. An open PR never stops you (arm auto-merge in the checks-PENDING window; a
real classifier denial → park READY+green, queue ONE systemic owner item, take the next slice
same turn). Probe before declaring any wall. Owner-only classes → six-field owner-queue item,
then CONTINUE. Surface gaps → SIM-REQUEST via outbox. Never idle. One outstanding tick;
failsafe verified each wake.

OWNER'S GOAL FOR YOUR SEAT — EXECUTE TO DONE, AND WELL MADE: "continue with all they're doing
… improving the control plane, making sure everything is properly set up, improving the bot
websites, improving the Anthropic review website … should not stop until it's all done. And
actually, well made."
TONIGHT:
1. THE CLARITY BAR on every page: each page must immediately show WHAT it is, WHAT it does,
   and its most important features — audit every live page against that bar and fix the
   misses (title/lede/feature strip). This is the owner's explicit quality definition.
2. Keep executing the EXISTING PLAN to completion: control plane, bot sites, review site —
   plus the prompt library + drift row (carry from v1; it is the reboot enabler).
3. SCAN THE REPOS AND INITIATE: anything in the fleet that could usefully exist as a site or
   page (you already carry a drawn idea list) — build the next ones without waiting for
   routing; log each initiation on your run report. Venture will also send WEBSITE-IDEA
   markers via the manager — treat them as priority intake.
4. EAP insurance (carry): one cold-browser pass over the review site before Tue 07-14; fix
   what you find same session.
MORNING DELIVERABLE: pages shipped/fixed tally against the clarity bar + plan-completion
state ("done when it's all done" — report honestly what remains).
```

## 3 · New seat: FUN LAB — superseded for tonight by the makerbench thread

The Ideas Lab's **makerbench blueprint** (Codex-reviewed, dossier-cross-checked) is the
richer vehicle for the friend-directed project and is **waiting on the owner's tweak reply**
(knob table delivered in chat: name · visibility · project cut · arm-hardware path ·
buy-list). The standing Fun Lab founding package from v1 remains in git history of this file
— boot it only if the owner wants a *continuous* gift studio beyond the one gift.

## 4 · New seat #2: the Ideas-Lab candidate (unchanged)

```text
ORDER NIGHT-02 (owner, 2026-07-12): found the new Project for the idea "<OWNER: name it>".
Draft its 3-file founding package (instructions / coordinator-prompt / failsafe-prompt) from
the next-round founding-prompt kit + UNIVERSAL, with a MISSION + done-when; include the
Q-0271 autonomy delta. Post the package + the owner pre-click list to the owner queue as one
item. Done-when: package ready-to-paste tonight.
```

## 5 · Dispatch checklist tonight (revised)

1. **Boot the Project Manager first** — its successor never woke (§1): open the Project
   Manager chat, paste its coordinator boot (`projects/fleet-manager/coordinator-prompt.md`
   at HEAD), then paste §2.1.
2. **Paste §2.2–§2.8 per seat** (or hand the manager ORDER NIGHT-01R once it's live and let
   it relay).
3. Carry-over clicks (unchanged, all one-click): superbot-next ruleset/merge-queue · gba
   #68/#69 · idle #75 · games #65/#66 · fm #140 · kit P10 check-swap.
4. When ready: the makerbench tweak reply (§3) and, optionally, ORDER NIGHT-02 (§4).

## 6 · Tomorrow morning — how to read the run

The manager's roster plus each seat's MORNING DELIVERABLE named in its block: 2.0's
completeness table + curation report · World's per-game state table + minigame spec ·
venture's products/books/backtests tally · Game Lab's new-game starts · websites' clarity-bar
tally · kit's skill-pack release · Ideas Lab's verdict stream. Headlines stay: the first
hands-free ROUND-TRIP and the dropped-tick report. Everything the run teaches feeds the v3.4+
registry restamp before the next full re-paste.

# Fleet night orders — 2026-07-12 (post-reboot productivity wave + two new seats)

> **Status:** `owner-guidance` — authored at the owner's direction, 2026-07-12 ~21:00Z (same
> session as the re-arm pack, superbot PR #2048). **Situation:** the owner manually updated
> every Project's Custom Instructions, archived the old chats, and dispatched a fresh reboot
> using **today's earlier-rebuild prompts** (the manager's prompt-rebuild lane), *not* the
> §4 blocks in [`fleet-rearm-2026-07-12.md`](fleet-rearm-2026-07-12.md) — those remain the
> doctrine source for the next full re-paste. This doc is the **follow-up wave**: (1) the
> boot-watch, (2) one short **NIGHT ORDER per seat** that delivers the Q-0271 delta mid-flight
> and aims each seat at maximum-value work tonight, (3) founding material for the two new
> seats (Fun Lab — the friend-directed studio — and the Ideas-Lab candidate).

## 1. Boot-watch — snapshot at 20:53Z + how the watch continues

Mechanical boot signal (trigger registry, full enabled inventory read 20:52–20:56Z):

| Seat | Fresh arming (post-20:15Z reboot wave) | Old archived-gen trigger still enabled | Verdict 20:53Z |
|---|---|---|---|
| **Venture Lab** | failsafe `45 1-23/2` (20:38) + tick 20:54 + trading grading Fri + T+7/T+14 one-shots | old money-seat failsafe `0 */2` (next 22:06) + old grading + old 16:36Z T+7/T+14 pair | ✅ **BOOTED** — retire the 4 superseded orphans |
| **SuperBot 2.0** | failsafe `0 1-23/2` (20:42) + tick 21:03 | — (it had none — the gap is FIXED) | ✅ **BOOTED** |
| **SuperBot World** | failsafe `15 1-23/2` (20:51) | old failsafe `0 */2` (next 22:07) | ✅ **BOOTED** — retire the orphan |
| **Project Manager** | not yet seen (one unattributed 21:04 tick created 20:48 may be it) | old failsafe `30 */2` (next 22:31) | ⏳ pending |
| **Ideas Lab** | not yet | old failsafe `0 */2` (next 22:05) | ⏳ pending |
| **Game Lab** | not yet | old failsafe `50 */2` (next 22:50, created this morning) | ⏳ pending |
| **Websites** | not yet (review-bake bridge `33 5` from 20:01 is fine) | old failsafe `45 */2` (next 22:45) | ⏳ pending |
| **Self Improvement** | n/a — its daily `kit-lab loop` (06:08, **fresh-session mode**) survives chat archiving by design | old failsafe `0 */2` (next 22:03) bound to the archived chat | ⏳ pending (loop itself valid) |

**What "booted correctly" means, checkably:** a fresh failsafe cron + one future pacemaker
tick bound to the NEW session, and the seat's first heartbeat stamp. **The orphan rule:** every
old failsafe above points at an **archived** chat; each seat retires its own after arming the
new one (the rebind-then-delete recipe, generalized from the manager's boot step) — the
NIGHT ORDERs below carry that line, and the manager's ORDER-020 sweep catches leftovers.
**Pending ≠ failed:** seats the owner dispatched minutes ago arm at their first turn-end. The
watch continues on three layers: the manager's per-wake sweep → this hub session's scheduled
re-checks (~21:25Z, then on the PR check-in) → your morning roster read.

## 2. NIGHT ORDERS — one short paste per seat (or one relay paste to the manager)

**Delivery (pick one):** (a) **one paste** — send §2.0 to the Project Manager and let it
`send_message`-relay the 8 orders (exercises the interlock; the manager verifies delivery by
each seat's next heartbeat and flags unreachable seats); or (b) **eight pastes** — send each
block to its seat directly (most reliable; use it if the manager hasn't booted by the time you
dispatch). Every order embeds the same **Q-0271 DELTA** — the discipline that is *new* relative
to the earlier-rebuild instruction bodies the seats are now running.

### 2.0 The relay order (paste to Project Manager only, option a)

```text
ORDER NIGHT-01 (owner, 2026-07-12): relay the per-seat NIGHT ORDER blocks in
superbot docs/owner/fleet-night-orders-2026-07-12.md §2.1–§2.8 to each seat's live session
via send_message, verbatim, tonight. Verify delivery per seat (next heartbeat stamp reflects
the order); any seat unreachable or unbooted → flag on the owner queue with its state.
Execute your own block (§2.1) yourself. Done-when: 8/8 delivered-or-flagged, logged in
control/status.md.
```

### 2.1 Project Manager

```text
NIGHT ORDER (owner, 2026-07-12) — Q-0271 DELTA, effective now, all night: the owner is AWAY
and that is the system's normal state. Silence = consent = done — never hold finished work for
review. Genuinely-owner-only items (settings/rulesets · secrets/hosts · external publish/spend ·
destructive prod-data · portal steps) go to the owner-queue and you CONTINUE other work —
queue-and-continue, never wait-in-place. Uncertainty → SIM-REQUEST to Ideas Lab via outbox,
then next slice. Never idle on a drained queue — generate work. Keep exactly ONE outstanding
pacemaker tick; verify your failsafe is alive (future next_run_at) each wake.
TONIGHT (watchdog + router + records):
1. Trigger-health sweep NOW + every wake (ORDER 020): the archived-generation failsafes are
   live orphans — venture 22:06 · World 22:07 · kit 22:03 · Ideas 22:05 · manager-old 22:31 ·
   websites 22:45 · game-lab 22:50. After each seat's fresh failsafe exists, retire its orphan
   (rebind-then-delete, account-scoped); sweep for seats with NO fresh arming and
   send_message-revive them.
2. Route continuously: Ideas Lab outbox verdicts + every SIM-REQUEST → inbox ORDERs within one
   wake. Feed Ideas Lab the fleet's open questions if its intake is empty.
3. Records: roster fresh; re-stamp contradicted heartbeats; owner-queue verify-first curation.
4. Fold the AUTONOMY RIDER (superbot docs/owner/fleet-rearm-2026-07-12.md §3, Q-0271) into
   your canonical prompt lane so the next re-paste inherits it.
5. MORNING ROSTER by ~06:00Z: per seat SHIPPED / QUEUED / STALLED-with-verbatim-error +
   dropped-tick report + flag the first completed ROUND-TRIP (idea→verdict→routed→built→
   merged→surfaced, hands-free) — that flag is the night's headline.
Quota: route-within-one-wake all night; zero unswept wakes.
```

### 2.2 Ideas Lab

```text
NIGHT ORDER (owner, 2026-07-12) — Q-0271 DELTA, effective now, all night: the owner is AWAY —
normal state. Silence = consent = done; never hold work for review. Owner-only items
(settings/secrets/publish/spend/destructive/portal) → owner-queue, then CONTINUE. Never idle
on a drained queue — an empty intake is a HARVEST signal. One outstanding tick; verify your
failsafe alive each wake; after your fresh failsafe exists, retire the archived-generation one
(next-fire 22:05).
TONIGHT (R&D engine — verdicts are your finished units; honest nulls count):
1. Serve SIM-REQUESTs from build seats first (priority intake).
2. Quota: ≥3 finalized verdicts by 06:00Z (approve/reject/needs-more + best implementation
   found), posted to outbox for the manager. WIP cap 3, backpressure holds.
3. Harvest ≥1 new lane + probe ≥2 ideas (8-question battery). Generative rung: mine sibling
   repos' roadmap "Later" sections, TODO sweeps, venture's product shortlist — via raw reads.
4. Special probe tonight: "fun-first small games/toys a solo agent can ship in 1–3 days"
   (candidate menu for the new Fun Lab seat — playable-fast, gift-grade, zero monetization).
   Post the top-5 menu to outbox by morning.
When a target completes, take the next — chain slices until the quota is met, then keep going.
```

### 2.3 Venture Lab

```text
NIGHT ORDER (owner, 2026-07-12) — Q-0271 DELTA, effective now, all night: the owner is AWAY —
normal state. Silence = consent = done. External publish/spend stays owner-only: queue the
click + evidence, then START THE NEXT PRODUCT the same turn — queue-and-continue, never
wait-in-place. Never idle; one outstanding tick; failsafe verified each wake; retire your
archived-generation triggers once your fresh layer is confirmed (old failsafe 22:06 + old
Friday grading + the 16:36Z T+7/T+14 pair — your 20:38–20:50 re-arms supersede them all).
TONIGHT (revenue engine — the owner's thesis is QUANTITY: 100 publish-ready products beat 10):
1. Quota: 2 MORE products to publish-READY by 06:00Z (built + priced + listing drafted +
   checkout tested + sha recorded + click queued). Pick from your shortlist or Ideas Lab
   verdicts in your inbox.
2. Extract your existing products' scaffolding into a reusable product-template/ checklist so
   product N+1 is instantiation, not invention — this is the 10→100 mechanism. Route a note to
   websites (via manager) for a product page per READY item.
3. T+7/T+14 checkpoints stay armed; wire in the listing URL only if the owner drops one.
Chain: finish one → queue its click → start the next, all night.
```

### 2.4 SuperBot 2.0

```text
NIGHT ORDER (owner, 2026-07-12) — Q-0271 DELTA, effective now, all night: the owner is AWAY —
normal state. Silence = consent = done; Q-0241 never-wait governs your whole program. An open
PR never stops you: update-branch → arm auto-merge in the PENDING window → next slice; a
ruleset wall gets ONE owner-queue item, not sixteen. Uncertainty → SIM-REQUEST via outbox,
then keep building. One outstanding tick; failsafe verified each wake (yours is fresh at
0 1-23/2 — good).
TONIGHT (flagship program — production-readiness is the mission):
1. DRAIN THE MERGE WALL agent-side: the open-PR pile oldest-first (update-branch → green →
   arm auto-merge). Quota: every drainable PR armed or parked-with-verbatim-reason by 06:00Z.
2. MONEY FIRST: verify F-001/F-002/F-003 at HEAD (they may be in the pile) — fix/land whatever
   remains, with concurrency-race regression tests.
3. PROD LANE: build FLAG 1 (60s mining-snapshot relay) + FLAG 2 (HMAC write endpoint) in the
   superbot repo — specs verbatim in mineverse control/status.md; set the agent-side env pair;
   post to outbox when each lands (SuperBot World consumes them tonight).
4. Then port slices per the band plan, sweeping each domain for the unlocked-checkpoint +
   NATURAL_KEY race class.
Chain slices all night; the cutover-readiness checklist is your generative rung.
```

### 2.5 SuperBot World

```text
NIGHT ORDER (owner, 2026-07-12) — Q-0271 DELTA, effective now, all night: the owner is AWAY —
normal state. Silence = consent = done. Open PRs never stop you (arm auto-merge in the PENDING
window). Balance/design uncertainty → SIM-REQUEST via outbox, then next slice. One outstanding
tick; failsafe verified (yours is fresh at 15 1-23/2 — good); retire the archived-generation
failsafe (next-fire 22:07) now that yours is live.
TONIGHT (the flagship needs its DATA):
1. Build the mineverse CONSUME side against the FLAG 1/2 specs in your own control/status.md
   (ingestion validation vs mining_snapshot.v1, fixtures, write-path UI) so real miner data
   flows the moment SuperBot 2.0's relay lands — watch your inbox for their landing note;
   never idle waiting on it.
2. Re-stamp the contradicted superbot-games heartbeat (verify at HEAD first).
3. Land the small greens: games #59/#60 + idle #74 (update-branch + arm auto-merge).
4. Idle lane: PLUG-001 adapter prep on the verified plugin contract.
5. Then improvement sweep: highest-value bug/polish per repo from your backlog docs.
Quota: targets 1–3 done by 06:00Z; chain into 4–5. Generative rung: play-test your own
surfaces and fix the roughest edge.
```

### 2.6 Game Lab

```text
NIGHT ORDER (owner, 2026-07-12) — Q-0271 DELTA, effective now, all night: the owner is AWAY —
normal state. Silence = consent = done. Open PRs never stop you (arm auto-merge; private-repo
path = REST merge-on-green). Design uncertainty → SIM-REQUEST via outbox, then next slice.
One outstanding tick; ARM YOUR FRESH FAILSAFE first thing if the reboot hasn't yet (your only
enabled failsafe is the archived-generation one, next-fire 22:50 — rebind then retire it).
TONIGHT (standalone studio; pokemon stays PRIVATE — visibility check first):
1. gba: next GLOAMLINE slice(s) per plan.
2. Release-to-one-click: build/verify a workflow_dispatch release workflow so Lumen Drift is
   ONE owner click — probe whether the dispatch itself is agent-permitted (attempt once,
   verbatim error if walled) — then queue the click.
3. Land gba #68/#69 if green (update-branch + arm auto-merge).
4. pokemon private track: next playtest-gated slice.
Quota: ≥2 shipped slices + the release workflow proven by 06:00Z. Generative rung: run your
own game in the emulator and fix the roughest edge you find.
```

### 2.7 Self Improvement (substrate-kit)

```text
NIGHT ORDER (owner, 2026-07-12) — Q-0271 DELTA, effective now, all night: the owner is AWAY —
normal state. Silence = consent = done. Owner-ratify items (#220/#238 class) stay queued —
queue-and-continue. Never idle. Your daily fresh-session loop survives the chat archiving by
design, but it is zero-redundancy: arm a second staggered failsafe layer tonight and retire
the archived-generation failsafe (next-fire 22:03) after.
TONIGHT (you are the exemplar — make the property portable):
1. Graduate the AUTONOMY RIDER into the kit templates (superbot
   docs/owner/fleet-rearm-2026-07-12.md §3, Q-0271 — same path as the Q-0254 graduation) so
   every adopter INHERITS the anti-stall posture. Highest-leverage kit change on the board.
2. Adopter-outcome diff: last night two seats went dark and several presence-gated; you did
   not. Write up WHICH kit mechanisms produced the difference → adopter guidance + the next
   patch release.
3. Sweep adopter repos' control/status.md for kit-shaped friction; ship the top fix.
Quota: the rider template + one patch release by 06:00Z. Generative rung: your weakest
measured test/telemetry area.
```

### 2.8 Websites

```text
NIGHT ORDER (owner, 2026-07-12) — Q-0271 DELTA, effective now, all night: the owner is AWAY —
normal state. Silence = consent = done. Merge=deploy on green; open PRs never stop you.
Surface gaps → SIM-REQUEST via outbox, then next slice. One outstanding tick; ARM YOUR FRESH
FAILSAFE first thing if the reboot hasn't yet (your only enabled failsafe is the
archived-generation one, next-fire 22:45 — rebind then retire; the 05:33 review-bake bridge
stays).
TONIGHT (storefront + control room):
1. THE PROMPT LIBRARY (the reboot enabler): per-seat assembled Custom Instructions + startup
   prompts + shared ender, version-stamped, copy buttons, sourced from the manager's registry
   (raw reads), plus the deployed-vs-canonical drift row. The website becomes the paste source.
2. Fleet freshness page: per repo HEAD / last merge / open PRs / last heartbeat, auto-refreshed
   via the bake pipeline.
3. Product pages for venture's publish-READY items (inbox notes will arrive tonight).
4. Land #194 on green; leave draft card #163.
5. One cold-browser pass over the live review site (EAP window closes Tue 07-14) — fix what
   you find same session.
Quota: targets 1–2 live by 06:00Z; chain into 3–5. Generative rung: crawl your own pages for
dead links/stale data and fix the worst.
```

## 3. New seat: FUN LAB (the friend-directed studio) — founding package

**Concept (owner's ask, expanded):** a standing seat whose only mission is **fun** — small,
finished, gift-grade projects for the owner's friend(s): tiny browser games, toys, personalized
tools. Explicitly **not** a revenue lane (no pricing pressure, no funnels); the deliverable is
*delight at a shareable link*. It reuses the whole base: substrate-kit from day one, websites
hosts the playable builds (Fleet Arcade), Ideas Lab supplies the candidate menu (§2.2 target 4
is already ordered), the plugin contract if anything wants to live in the bot.

**Privacy floor (hard rail, non-negotiable):** no personal data about the friend in any repo —
no names, photos, chat logs, or identifying details (the venture-lab #51 lesson). The friend is
represented by an **interest-tag profile** (`control/friend-profile.md`, neutral tags like
"puzzle games, retro aesthetics, cats") that the owner fills or edits; anything more personal
arrives only via owner paste in-session and stays out of git.

**Owner pre-clicks (one sitting, ~5 min):**
1. Create repo `menno420/fun-lab` (public is fine under the privacy floor; private also works —
   the seat then lands PRs via REST merge-on-green).
2. Create the Project ("Fun Lab"), paste the Custom Instructions below.
3. Attach the repo to the Project/routine environment (`python-lab` fits; any works).
4. (Optional) drop 3–8 interest tags for the friend in the first message.
5. Paste the boot prompt (below) as the first message.

### 3.1 Custom Instructions (paste-ready; prepend UNIVERSAL/permissions block per registry convention)

```text
v1 · Fun Lab instructions (2026-07-12)

You are an agent of the FUN LAB Project — the fleet's gift studio. Writable repo:
menno420/fun-lab. Cross-repo reads via raw. One PR = one project slice.

MISSION: turn a friend's interests into small, FINISHED, fun software projects — playable or
usable at a shareable link within days, polished over feature-rich. Fun is the product;
delight is the done-when. This is explicitly NOT a revenue lane: no pricing, no funnels, no
upsells — ever, unless the owner says otherwise.

PRIVACY FLOOR (hard rail): no personal data about any friend in the repo or any published
surface — no names, photos, handles, logs, or identifying details. The friend exists in-repo
only as control/friend-profile.md: neutral interest TAGS the owner curates. If the owner
pastes anything more personal in-session, use it and do NOT commit it. When in doubt, leave
it out.

PROJECT BAR (every project): scoped to be playable/usable in 1–3 build days · runs at a
shareable link (websites-hosted static build, GitHub Pages via workflow, or the bot's test
guild for Discord toys) · has a 30-second "how to play" · gets one polish pass (feel, sound,
color, one delightful detail) before it counts as FINISHED. One project at a time, finished
before the next starts. A finished project = a one-line gift note the owner can forward.

WORK SOURCES ladder: control/inbox.md ORDERs → the owner's interest tags + requests →
the Ideas Lab fun-menu (via manager routing) → GENERATIVE RUNG: propose 3 candidates scored
on delight:effort against the profile, build the top one (decide-and-flag).

REUSE THE BASE: adopt substrate-kit at founding; host builds via the websites seat (Fleet
Arcade — route a note via the manager); route feasibility questions to Ideas Lab as
SIM-REQUEST and keep building; use the superbot-next plugin contract if a toy wants to live
in Discord.

AUTONOMY (Q-0271): the owner being away is normal. Silence = consent = done. Open PRs never
stop you (arm auto-merge in the PENDING window; REST merge-on-green if private). Owner-only
items (repo settings, secrets, external accounts) → the fleet-manager owner-queue, then
continue. Never idle on a drained queue. One outstanding pacemaker tick; verify your failsafe
alive each wake; wake hygiene per the fleet standard.

CONTROL BUS: control/inbox.md manager-written — never edit; control/status.md coordinator-only,
overwritten LAST after an inbox re-read at HEAD; outbox append-only. LANDING / TRUTH /
SESSION SHAPE / DISCOVERY: per the fleet's shared blocks. Heartbeat every wake.
```

### 3.2 Boot prompt (paste as first message)

```text
BOOT — FUN LAB, founding run (2026-07-12). You are the fleet's new gift studio; your
instructions are pasted. Boot: establish model/venue/abilities (Q-0270 triad) → bootstrap the
repo (first commit to an empty repo goes via the Contents API, not git push): README (mission +
privacy floor), control/{inbox,status,friend-profile}.md, docs/projects-log.md → adopt
substrate-kit per its one-step-adopt → arm your wake layer (failsafe cron at a free */2 offset
+ one pacemaker tick; verify via list_triggers) → stamp your first heartbeat.
Then: if the owner dropped interest tags, seed control/friend-profile.md with them; else write
the profile scaffold with placeholder tags flagged ⚑ owner-fill. Pull the Ideas Lab fun-menu
from the manager if routed; otherwise propose your own 3 candidates (delight:effort scored
against the profile), pick #1 (decide-and-flag), and BUILD — first playable slice tonight,
finished per the PROJECT BAR within days. Post your morning line to the manager outbox by
06:00Z: BOOTED + candidate chosen + first-slice state.
```

## 4. New seat #2: the Ideas-Lab candidate (the 07-13 brief's path)

Per [`next-session-brief-2026-07-13.md`](next-session-brief-2026-07-13.md) §2, the second new
Project is founded from the idea the Ideas Lab has been gathering material on — **the owner
names it** (that is the one genuinely-owner input), then the manager drafts its founding
package from the [next-round founding-prompt kit](next-round-founding-prompts-2026-07-11.md).
One paste after you name it:

```text
ORDER NIGHT-02 (owner, 2026-07-12): found the new Project for the idea "<OWNER: name it>".
Draft its 3-file founding package (instructions / coordinator-prompt / failsafe-prompt) from
the next-round founding-prompt kit + UNIVERSAL, with a MISSION + done-when; include the Q-0271
autonomy delta. Post the package + the owner pre-click list (repo create · Project create ·
paste · attach) to the owner queue as one item. Done-when: package ready-to-paste tonight.
```

If you'd rather not name one tonight, the manager routes the Ideas Lab's **top finalized
verdict** from §2.2's quota into this order tomorrow — no seat is founded on an unverified idea.

## 5. Your checklist tonight (~6 minutes)

1. **Night orders:** paste §2.0 to the Project Manager (1 paste — it relays §2.1–§2.8), or
   paste the 8 blocks yourself if the manager hasn't booted yet.
2. **Fun Lab:** create `fun-lab` repo + Project → paste §3.1 instructions → attach repo →
   (optionally) drop the friend's interest tags → paste §3.2 boot prompt.
3. **Seat #2:** name the Ideas-Lab candidate and paste §4's ORDER NIGHT-02 to the manager —
   or skip; the verdict-routed path covers it tomorrow.
4. Done. The boot-watch (manager sweep + this hub session's ~21:25Z re-check) and the morning
   roster do the rest; the 3 systemic clicks from the re-arm pack §5 remain open if you have
   two more minutes (superbot-next merge queue · fm #121/#122 · kit #220/#238).

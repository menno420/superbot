# Fleet night review — 2026-07-12 (the trigger-scheduler incident batch)

> **Status:** `reference` — owner-directed `/fleet-review` FLEET mode over the 2026-07-12
> overnight batch. Evidence basis: the **full live trigger registry** (293 records read via
> `list_triggers`, 4 pages, 08:31–08:45Z), fleet-manager **roster gen #13** (generated
> 2026-07-12T08:13Z, transport-verified HEADs), fleet-manager `control/status.md` (updated
> 08:45Z), the 8-seat staleness-sweep report
> (`fleet-manager/docs/research/2026-07-12-staleness-sweep-8seat.md`), and this hub repo's
> own state. Owner question: *"this batch had cron problems vs. last time — what happened,
> what's the state, what did we learn about preventing stalls?"*

## TL;DR verdict

**The batch was armed correctly; the platform trigger scheduler degraded.** Between ~02:30Z
and ~08:00Z the Claude Code Remote scheduler silently dropped one-shot (`send_later`) firings
and froze several cron Routines (`next_run_at` stuck in the past, still `enabled`). Every seat
whose 2-hourly failsafe cron **stayed healthy** self-revived at ~08:0xZ when the scheduler
partially recovered — **the Q-0265 dead-man doctrine worked**. The two dark seats are the ones
whose protection was missing or itself broken: **Venture Lab** (it *had* a failsafe — the
failsafe itself wedged) and **Self Improvement** (daily-only loop, no failsafe layer; its one
firing dropped — manually re-fired 08:46Z by this review). Doctrine takeaway: a failsafe only
protects while it is *alive* — which is what the trigger-health check below exists to verify. Meaningful work still shipped all
night, led by the manager's owner-directed prompt-rebuild program.

## 1. The incident (primary evidence)

**Contrast baseline:** the 07-10→07-11 batch ran clean — 84/85 `send_later` one-shots fired
(trigger-registry page-3 evidence). Same arming pattern, same cron expressions this batch.

**Timeline (all UTC, 2026-07-12):**

- **00:0x–02:31** — normal: failsafe crons fired on schedule (fleet-manager 02:31,
  substrate-kit 02:04, venture-lab 02:07), pacemaker ticks delivered.
- **~02:30 onward** — cron wedge begins: the three failsafes above never advanced past their
  04:0x slots (roster gen #13, 08:13Z, still showed them frozen at 04:03/04:06/04:31 —
  i.e. ~4h overdue while `enabled=true`).
- **06:00–06:52** — one-shots turn flaky, then die: ticks due 06:00, 06:48, 06:52 fired;
  ticks due 06:12, 06:16, 06:26, 06:47 dropped. After 06:52, **every** due one-shot was
  dropped: 07:05, 07:16, 07:34, 07:44, 08:23 — **9 dropped ticks total across 5 seat
  sessions**, none back-delivered as of 08:45Z. Dropped ticks stay `enabled` with a past
  `run_once_at` — no error, no retry, no state change.
- **06:08** — the **kit-lab loop** (daily `0 6 * * *`, fresh-session mode) was dropped
  entirely: `last fire: never`, `next_run_at` frozen at 06:08:52.
- **~08:00–08:31** — partial catch-up: Ideas Lab (08:05), SuperBot World (08:07),
  substrate-kit (08:03), fleet-manager (08:31) failsafes fired and advanced to 10:0x.
  **venture-lab's failsafe stayed frozen at 06:06; kit-lab stayed frozen at 06:08.**
- **08:46** — this review manually fired the kit-lab loop (`fire_trigger` works on
  fresh-session triggers) → today's Self Improvement run started ~2.7h late
  (session `cse_01BUyeM5t9itqBwTNyX2mZUi`).
- **08:5x** — attempted revival of the two dark persistent seats **refused server-side**:
  `fire_trigger`/`update_trigger` on a trigger bound to another session and `create_trigger`
  with a foreign `persistent_session_id` all return *"not enabled for this organization."*

**Root cause (as far as observable from here):** platform-side scheduler degradation. The
cron expressions were correct (identical expressions fired cleanly before 02:30 and again
after 08:00); the arming was correct (fleet-8seat dispatch guidance followed, staggered
offsets). Nothing agent-side changed between the clean 07-10 batch and this one.

## 2. Per-lane digest (state as of ~08:45Z)

| Seat | State | Overnight work + evidence |
|---|---|---|
| **Project Manager** (fleet-manager) | 🟢 alive all night (21/23 ticks delivered; next 09:02; failsafe healthy 10:31) | The night's headline: owner-directed **prompt rebuild** — prompts **v3.2 stateless startup artifacts** (fm #108), **12 relocation ORDERs merged across 10 repos** (mineverse #43 · idle #73 · games #61 · pml #53 · superbot-next #244 · websites #157 · venture-lab #62 · trading #67 · substrate-kit #259 · sim-lab #49), restructure chain #88/#89/#91 merged 03:15–03:26Z, first 8-seat **staleness sweep** + 9-item shortlist. Parked green for owner click: **#105, #92**. |
| **SuperBot 2.0** (superbot-next) | 🟡 productive, but chain now dead + **no failsafe armed** | Heartbeat FRESH 07:55Z: band-5 COMPLETE, live-bug lane done (#111 merged, CI green), kit v1.12.1. Its pacemaker session (best-evidence match: `session_01Xbiuvy…`, the night's most active at 22 ticks) had 4 ticks dropped and has **no future tick armed** — goes dark when its current turn ends. |
| **Ideas Lab** (idea-engine + sim-lab) | 🟢 revived by failsafe, **idle — needs routed work** | idea-engine re-stamped 08:11Z after the 08:00Z failsafe sweep; work loop DRAINED. sim-lab ACTIVE 03:25Z, intake queue empty (PROPOSAL 011 → VERDICT 013). Failsafe healthy (10:05). |
| **Venture Lab** (venture-lab + trading) | 🔴 **dark since ~02:07Z** — failsafe wedged at 06:06 + 08:23 tick dropped; org policy blocks sibling revival | Money seat was live at 00:26Z with re-armed wakes, then nothing. Trading weekly grading correctly armed (Fri 07-17 09:05). ⚑ HOT carry-over: venture-lab **#51** (10 personal photos public) still open, owner-only. |
| **Self Improvement** (substrate-kit) | 🟠 lost 06:00–08:46, **now running** (manual re-fire) | ORDER 014 shipped ~00:24Z (kit #256 + #259). Daily loop firing dropped; re-fired 08:46Z by this review. |
| **SuperBot World** (games + idle + mineverse) | 🟡 archived-by-order awaiting gen-2 dispatch; coordinator chain alive (09:10) | Sweep findings: **games heartbeat contradicted** (its 5 "parked" PRs all merged, HEAD +8 — needs re-stamp); **mineverse #42 (CSRF fix)** blocked — zero check runs ever started on its head. |
| **Game Lab** (gba + pokemon) | 🟡 working but **no wake triggers** post-restructure | gba GLOAMLINE slice 5 (barricades) shipped, session-23 heartbeat 21:03Z. pokemon not roster-measurable (auth wall) but reachable by workers (#53 merged). |
| **Websites** | ⚪ parked (intentional — owner archive-prep order) | Final tally 35 slices (#64→#151); relocation #157 merged. |
| **superbot (hub)** | 🟢 clean | 0 open PRs; ledger in sync; 44th recon pass landed (#2014); dashboard refreshes #2015/#2016 (GH Actions). Next recon at #2040. |

## 3. What the incident validated (strong)

1. **Failsafe crons are the load-bearing anti-stall layer (Q-0265) — now production-proven.**
   Every seat whose `*/2` failsafe stayed healthy came back on its own the moment the scheduler
   breathed again. The dark seats are exactly the ones with missing (kit-lab: daily-only) or
   itself-wedged (venture-lab) failsafe coverage — coverage must exist *and* be alive.
2. **Cross-substrate redundancy works.** The roster-regen moved to a GitHub Actions cron
   (fm #81) — fleet truth (roster gen #12, #13) kept flowing **through** the CCR scheduler
   outage. Anything oversight-critical should live on a second substrate.
3. **Stateless startup prompts (v3.2) land at the right moment** — volatile facts (PR
   numbers, trigger ids, CI colors) are out of the prompts, replaced by WORK SOURCES ladders
   read at HEAD. Tonight showed why: any prompt that had baked in "your failsafe is
   trig_X / next fire 06:06" would now be lying.

## 4. New lessons (this batch)

1. **The scheduler can *partially* fail, silently.** Dropped one-shots stay `enabled` with a
   past `run_once_at`; wedged crons keep a frozen past `next_run_at`. **Detection signature:
   `enabled=true ∧ next_run_at < now − 15min`.** Nothing alerts on this today — the 9 dropped
   ticks were visible in `list_triggers` all night.
2. **Sibling sessions cannot revive each other via triggers — org policy.** `fire_trigger` /
   `update_trigger` on another session's trigger and `create_trigger` bound to a foreign
   session are all *"not enabled for this organization."* Recovery paths are only: scheduler
   catch-up · the manager's session-messaging tools (`send_message` — it has them in its MCP
   grant) · an owner poke · manual fire of **fresh-session** triggers (those work — proven on
   kit-lab). The manager is therefore the *only* agent-side watchdog for persistent seats.
3. **Auto mode ≠ MCP allowlist — and the repo-settings allowlist provably doesn't stick for
   CCR tools.** The hub session hit permission prompts on `fire/update/create_trigger` even
   though exact `mcp__Claude_Code_Remote__*` allow entries already exist
   (`.claude/settings.json:68-79`) — fresh evidence for the **Q-0242** record (send_later
   prompted with an exact entry in 2026-07-07 too). Coordinator seats never prompt because
   their grants ride a different surface that works: the Routine's spawn-time
   `session_context` per-tool `always_allow`. **In an unattended session, a prompt is a silent
   stall** — so any recovery duty must run in a Routine-spawned session carrying its grants,
   not rely on settings.json.
4. **A daily-cadence-only seat has zero redundancy.** One dropped firing = a lost day
   (kit-lab). Fresh-session loops need a failsafe layer too — or at least the manager's
   wedge-sweep watching them.
5. **On wake, verify your own chain.** A seat re-arming its pacemaker should confirm the new
   tick exists with a *future* fire time, and glance for its own dropped siblings — the
   evidence is one `list_triggers` away.

**Consolidated anti-stall-on-open-PRs corpus** (the owner's standing question — items proven
across this + the 07-11 sessions, now baked into instructions v2/v3 by the manager's re-issue):
park-READY+green when merge authority is denied (agent peer-merges blocked in auto mode) ·
update-branch-don't-force-rebase (merge `main` in + normal push) · handoff PENDING lists
verified against live GitHub at write time · GITHUB_TOKEN merges don't trigger main-branch CI
(don't key oversight on push-workflow runs) · MCP PR reads can serve ~25-min-stale state
(cross-check via git fetch before acting on "still red") · born-red "CI failed" webhooks are
noise · heartbeats can contradict reality — sweep and re-stamp.

## 5. Fix-first (priority order)

1. **Revive Venture Lab** — owner poke of the money-seat session (fastest), else watch
   whether its failsafe unwedges by ~10:06Z; the 10:40Z roster regen is the checkpoint.
2. **Re-arm SuperBot 2.0's wake layer** — the busiest build seat has no failsafe cron and a
   dead pacemaker chain; manager `send_message` or owner poke, then arm a `*/2` failsafe at a
   free offset per the 8-seat dispatch guidance.
3. **Give the manager a trigger-health duty** (owner drops one order into fm inbox — the
   single-writer rule is why this review didn't write it): each wake, flag any
   `enabled ∧ next_run_at < now−15min` trigger as WEDGED, sweep for dropped one-shots, and
   `send_message` any seat whose chain is dead. Paste-ready order text is in the owner queue
   below.
4. **Feed Ideas Lab** — it's healthy and drained; route it work or it idles on green.
5. **Standing HOT items re-affirmed** (sweep shortlist): venture-lab #51 photos (owner-only) ·
   mineverse #42 CSRF checks never started · fm #105/#92 one-click merges.

## 6. Owner-action queue (only owner-only items)

1. **Poke Venture Lab** — open the money-seat session ("Venture Lab" Project) and send:
   *"resume per your failsafe prompt; scheduler dropped your wakes overnight — re-arm and
   verify each tick."* UNBLOCKS: the revenue seat's day.
2. **Poke / confirm SuperBot 2.0's coordinator** — its heartbeat was FRESH 07:55Z; if the
   session shows idle with no armed tick, same poke + have it arm a failsafe cron.
3. **Paste into Project Manager chat (or fm `control/inbox.md`):** *"ORDER: add a
   trigger-health check to every wake — list_triggers; any trigger with `enabled=true` and
   `next_run_at < now − 15min` is WEDGED (flag in roster + status); any dropped one-shot for a
   seat session with no future tick means that seat's chain is dead — send_message it to resume.
   Done-when: the check runs in gen_roster or the wake ritual and tonight's signature
   (venture 06:06 / kit-lab 06:08 / 9 dropped ticks) would have been caught within one wake."*
4. **One-click merges:** fm **#105** (staleness sweep) + **#92** (permission-rules port).
5. **Known platform bug — no settings edit will fix the prompts (Q-0242, reproduced today):**
   the exact CCR allow entries already exist (`.claude/settings.json:68-79`) and this session
   still prompted on `fire/update/create_trigger`. Don't re-edit settings (a no-op path). If
   hub-side recovery should be autonomous, run it from a Routine-spawned session whose
   `session_context` carries the per-tool grants (the surface that provably works), and add
   today's evidence to the Q-0242 platform report.
6. Carry-over HOT: **venture-lab #51** (close + delete branch — 10 personal photos public).

## 7. Honest limits of this review

- Per-repo PR-level verification was done through the manager's transport-verified roster +
  sweep (both generated today from ls-remote'd HEADs), not by re-reading every lane repo;
  fleet-manager itself was read directly at HEAD `6391b2f`.
- The `session_01Xbiuvy…` ↔ SuperBot 2.0 identification is best-evidence (activity pattern +
  the only heavy seat with no failsafe), not confirmed — one glance at the session list
  settles it.
- Venture Lab / kit-lab recovery outcomes post-08:46Z are unverified at write time; the
  10:40Z roster regen (gen #14) is the checkpoint.

## 8. Addendum (~12:00Z) — serialization vs. real failure

A Game Lab session, working from the trigger registry, split the "dropped one-shot" class
in two: **ticks bound to a busy session serialize and deliver the moment the turn goes
idle** (its 09:10Z tick fired at 11:16Z at exactly that boundary — sound by construction;
the hub session's own 10:42Z check-in matched the pattern, arriving as its turn ended).
The genuinely-failed remainder: the fresh-session daily loop ("last fire: never" with no
busy session to queue behind) and the crons with `next_run_at` frozen hours in the past.
No platform surface distinguishes queued from lost. Bonus from the same recording: the
Routines detail page now shows per-run history (Scheduled/Manual/API/Webhook) with session
links — and the kit-lab double-fire (manual 08:46Z kick + 10:28Z scheduler catch-up)
resolved itself with a verified zero-write stand-down by the second run. Figures:
`screenshots-2026-07-12/` figs 33–35.

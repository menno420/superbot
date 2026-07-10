# Round-3 dispatch — part-4 session brief (2026-07-10)

> **Status:** `plan` — the successor brief written at part-3 close (PR #1955). **The live
> state is always [`round3-dispatch-runbook-2026-07-10.md`](round3-dispatch-runbook-2026-07-10.md)
> §3 (checklist) + §5 (verification log) — this brief is a snapshot as of ~19:1xZ and says
> so per the part-2 lesson: items below marked ⏳ can be invalidated by owner decisions or
> lane progress; re-verify against the runbook + live artifacts before acting.** Design
> provenance for everything here: router **Q-0264** (idea pipeline), **Q-0259**–**Q-0263**.

## §0 — Paste-ready opener (owner: start the part-4 session with this)

```
Round-3 dispatch part 4 (live copilot). Orient: superbot
docs/planning/round3-dispatch-part4-brief-2026-07-10.md (this brief) →
round3-dispatch-runbook-2026-07-10.md §3+§5 (live state) → router Q-0264.
You are the dispatch copilot: verify every boot against ground truth (trigger
registry, heartbeats at HEAD via git transport, PR/CI state — never
self-reports, Q-0120), keep runbook §3/§5 current, hand me paste blocks,
decide-and-flag. Claim a lane + born-red card + PR first (superbot ceremony).
Start with the brief's §2 priority queue.
```

## §1 — State snapshot (as of part-3 close; re-verify)

| Seat | State |
|---|---|
| 1 manager | LIVE (2-hourly :30 wakes; 16:32Z fire verified) |
| 2 substrate-kit | LIVE (2-hourly even :00; ⏳ 18:08Z+ fire outcomes unverified) |
| 3 Builder (superbot-next) | LIVE, fully verified (heartbeat 18:25Z; band-5 live-drive done; 3 live bugs queued; `superbot-plugin-hello` created) |
| 4 Idea Engine (`idea-engine`) | LIVE, fully verified — probe→sim-ready, **PROPOSAL 001 waiting in its outbox for sim-lab** |
| 5 Product Forge (`product-forge`) | repo seeded born-right + skeleton PROVED (its PR #1); ⏳ Project/env/§1-§2 pastes + calibration + first ORDER |
| 6 Simulator (`sim-lab`) | package ready; ⏳ repo + Project + env + **Codex-integration toggle** + seed |

Pipeline: idea-engine (even :00) → sim-lab (odd :00) → manager (:30) → lanes.

## §2 — Priority queue

0. **FIRST (added post-close, owner ruling Q-0265): the continuous-mode amendment
   round.** Paste the §2b block into each of the four LIVE seat chats (manager ·
   substrate-kit · Builder · Idea Engine). Product Forge and sim-lab inherit it
   natively — their packages were rewritten before boot. Copilot verification
   afterwards: each seat's next heartbeat records the amendment + its re-armed
   failsafe cron + a live continuation chain (registry: old cron prompt replaced,
   `send_later` continuations appearing).
1. **Finish seat 5 (Product Forge).** Owner: create the Project + `product-forge` env
   (repo only, no vars, `archetype-python-lab.sh` verbatim), paste package §1/§2
   (§2 is de-staled to the seeded reality). Copilot: verify calibration per package §4,
   the routine in the registry, and that the manager's ORDER 001 landed (below).
2. **Manager relay — forge ORDER 001 (owner-named product: games-web).** Owner pastes
   into the manager chat; copilot verifies the append + **dedups** (part-1's trading
   lesson: a manager dispatch can race a direct landing):

   ```
   DISPATCH from the owner (round-3, 2026-07-10): write the Product Forge's first ORDER.

   Append to menno420/product-forge control/inbox.md (you are its sole writer):

   ## ORDER 001 · <now ISO8601> · status: new
   priority: P1
   do: Build products/games-web/ — turn superbot's existing games into a web-based
   visual experience in a Shakes & Fidget-style comic browser-RPG presentation
   (owner-named, 2026-07-10). Phase 1 (this ORDER): a runnable prototype rendering the
   MINING character sheet — gear paper-doll, stats, skills, structures — from a
   COMMITTED MOCK game-state JSON whose schema mirrors superbot's versioned
   dashboard-data-contract pattern (superbot PR #1920). Placeholder art. README with
   the run command and an honest state line. Real-data integration is explicitly OUT
   of scope: it needs a superbot-lane read-only API — flag it in status, don't build
   it. Ship a viewable increment every wake (build ladder per the repo README).
   why: owner priority (games completion wave, Q-0259) + the forge's first product;
   the full concept heads to sim-lab for an evidence pass later ("could be simulated
   later" — owner), so phase 1 stays mock-data-first and cheap to redirect.
   done-when: products/games-web/ runs with one command from the committed mock
   contract; PR(s) merged on green; forge status reports acked=001 with ladder
   progress.
   ```
3. **Seat 6 (sim-lab) — closes the pipeline loop.** Owner: create `sim-lab` (public,
   empty, `main`; same ruleset as product-forge is fine) + Project + env
   (archetype-python-lab) + **enable the Codex GitHub integration for it**
   (chatgpt.com/codex settings — gates its review loop). Copilot: **seed it via §3
   below**, de-stale the package §2 boot steps after seeding (both prior packages
   needed this), then owner pastes §1/§2 of
   [`round3-founding-package-simulator-2026-07-10.md`](round3-founding-package-simulator-2026-07-10.md).
   First-wake verification: it must pull idea-engine's **PROPOSAL 001** (waiting since
   18:05Z) — that pull is the end-to-end proof of the Q-0264 pipeline.
4. **Open verifications** (part-2 handoff + part-3 leftovers): kit + manager wake
   outcomes since 18:08Z/18:31Z (registry `last_fired` + heartbeats — a part-3
   registry check was interrupted); Builder's ⚑ block for a `SB_APPCMD_SYNC_GUILD_ID`
   self-reported paste line (blank ⇒ slash-commands can't live-drive); trading:
   ORDER 007 verified DONE with holdout still SEALED — **ORDER 008 (P5 one-shot
   holdout eval) is executable but must run as a FRESH dedicated session** per
   `docs/p5-holdout-protocol.md` (owner starts it when ready — do NOT run it from the
   dispatch session).
5. **Owner clicks batch (non-gating, from the part-2 close-out — still open):** kit
   required-check swap "Kit test suite"+"Cold-adoption smoke" → `kit-quality` (OA2 —
   verify against kit's own ⚑ first); superbot-next "require branches up to date"
   uncheck; **orphan watchdog chain deletion** (hourly self-re-arming `send_later`
   loop on `session_01Stc1m5…` — one `delete_trigger` call, **awaiting the owner's
   explicit go**); EAP wrap-up email before **2026-07-14**.
6. **Post-core (runbook §3.7–§3.8):** manual lanes + the 3-repo games program once the
   manager proposes the mapping (Q-0259 r.5) — note the owner's games-web pick may
   reshape what the 3 repos should be (surface at the mapping review); then loop
   closure: all core routines with completed runs across 24h, owner-queue owner-only,
   zero stuck PRs.

## §2b — The Q-0265 continuous-mode amendment (paste into each LIVE seat chat)

```
CONTINUOUS-MODE AMENDMENT (owner directive Q-0265, 2026-07-10) — this supersedes
the "one bounded slice per wake / no excessive work — one real slice per wake"
lines in your founding instructions AND in your standing cron's prompt. Rationale,
owner's words: these projects produce real work that basically has no end, so they
have no reason to stop; the projects are free through 2026-07-14 — use them
excessively; everything produced gets a consolidation pass afterwards, and the
volume doubles as EAP test results for Anthropic.

Your new operating model:
1. WORK CONTINUOUSLY: when a slice finishes and genuinely useful work remains
   (inbox, queue, backlog, standing duties), start the next slice NOW, same turn.
   Each slice still ships as its own merged-on-green PR — the throttle is removed,
   not the ceremony. Near context limits, hand off cleanly (fresh card/branch)
   instead of degrading. Lean into parallel child workers for independent slices.
2. CONTINUATION CHAIN: before ending ANY turn, arm a send_later ~15 minutes out
   ("continue the work loop: sync HEAD → inbox → next slice → re-arm"). This
   chain, not your cron, is what keeps you running.
3. RE-ARM YOUR CRON AS THE FAILSAFE: delete your current standing wake and create
   it anew, same cadence, name "<seat> failsafe wake", prompt: "FAILSAFE WAKE
   (<seat>, Q-0265): if your send_later continuation chain is alive, verify that
   in one line and end. If it stalled, resume the work loop (sync HEAD → inbox →
   slice after slice, each merged-on-green) and re-arm the chain (~15 min) before
   ending." Record the delete + create calls verbatim in control/status.md (the
   proven cutover recipe).
4. BACKPRESSURE, not time-throttle: pause the specific activity whose downstream
   queue is saturated (generation pauses when several outbox proposals sit
   unpulled; building pauses at done-when + empty inbox AFTER flagging the
   manager) — grooming, verification, hygiene, and backlog work continue.
5. HONESTY GUARD unchanged: genuinely out of useful work → say so in status and
   idle until the failsafe. Never invent filler — the output must stay usable as
   evaluation data (citations, honest states).
Record this amendment in control/status.md on your next heartbeat.

[MANAGER ONLY, additional]: fold Q-0265 into the gen-3 blueprint delta + your
doctrine ORDERs so every future seat is born continuous; and add a standing
inventory thread so the owner's post-window consolidation session has its
material (what every lane produced, where, in what state).
```

## §3 — Fleet-repo seeding recipe (twice-proven; sim-lab is the next consumer)

From the superbot session, after `add_repo` + clone: fix the empty-clone refspec
(`git config remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'`); copy the kit's
`dist/bootstrap.py` in; `python3 bootstrap.py adopt`; answer ALL slots the engagement
banner names with the repo's REAL design values (never placeholders); `render --live`;
`mode guided`; copy `.substrate/ci/substrate-gate.yml` → `.github/workflows/`; plant the
lane layer (role README as the binding contract, CONVENTIONS.md, claims/README,
review-queue.md, PLATFORM-LIMITS.md, docs/retro/questions.md — **badge every new doc and
link it from a read-path doc** or `check --strict` reds); seed card with the kit's ender
lines (📊 Model · 💡 idea · ⟲ review) + status heartbeat overwrite; `session-close`;
**`check --strict` as the DIRECT `&&` predecessor of the push** (a `; echo` in between
masks a red — bit part 3); push. Gotchas: the first push to an empty ruleset-protected
repo lands (no branch exists for the rule) but every later change needs a PR;
`enable_pr_auto_merge` declines on an all-green PR — REST merge is the path (R21).
Idea filed to make this one kit command: `docs/ideas/kit-seed-command-fleet-repo-bootstrap-2026-07-10.md`.

## §4 — Part-2 close-out review (what changed since that message)

Superseded: seat-4 "existing superbot env" guidance (Q-0264 own-repo redesign — seat 4
is LIVE); seat-6 "hub package not drafted" (seat 6 = Simulator, package drafted).
Resolved: Builder first-slice/heartbeat; `superbot-plugin-hello` creation. Still open:
items in §2.4–§2.5 above. Lesson applied to THIS brief: state lives in the runbook;
this snapshot is dated and says which items are decision-sensitive.

# Round-3 dispatch runbook — coordination copilot state (2026-07-10)

> **Status:** `plan` — the working runbook for the round-3 dispatch phase: the finalized
> fleet-manager founding package (v3, owner-iterated in the 2026-07-10 review session's
> chat — this file is its durable home), the dispatch order, and the open drafting queue.
> Companion (strategy + paste blocks for lanes/Codex/decisions):
> [`round3-launch-pack-2026-07-10.md`](round3-launch-pack-2026-07-10.md). Owner rulings:
> router **Q-0259**; relay rule **Q-0258**.

## 1. Design decisions locked with the owner (instructions architecture)

- **Custom Instructions are Project-scoped job descriptions**, NOT a universal fleet
  contract and NOT the coordinator's brief: they describe what *any agent in that
  Project* does (the manager's agents do fleet oversight; a superbot agent does codebase
  work; a game lane's agents ship playable increments). ≤7,500 chars (the 8,000 paste cap).
- **The coordinator's role brief lives in its chat** (first message) — the chat persists
  across routine wakes; the brief points at its committed twin for re-reading when
  context thins. Routines fire INTO that same chat, so the routine's instruction text is
  designed together with the brief.
- **Environments:** one per Project, named like the repo; variables only when the lane
  genuinely needs a secret (platform injects `GITHUB_TOKEN`/proxy for attached repos);
  setup script = the tested fleet archetype, pasted verbatim (canonical:
  `fleet-manager/environments/archetype-*.sh`; rendered at the control-plane
  `/environments` page).
- **Single-writable-repo rule (owner directive Q-0260, 2026-07-10):** every Project
  except the manager attaches exactly ONE repo — its lane repo. Cross-repo reads use the
  public raw path, never attachment. Together with the founding-instruction "agent of
  THIS Project (repo X)" line this is the lane boundary (the Project-home ≠ repo-lane
  finding, §5). Carve-outs: the manager stays multi-repo (oversight is its job) and needs
  **pokemon-mod-lab attached** now that repo is private (raw reads 404 → its sweep would
  misread the lane as DARK); any future private repo inherits the same caveat.

## 2. Fleet-manager founding package v3 (FINAL — owner pasting)

### 2a. Custom Instructions (paste into the Project's Custom Instructions field)

```
You are an agent of the FLEET MANAGER Project (repo: menno420/fleet-manager). Agents
in this Project do FLEET OVERSIGHT, not lane work: you review the fleet's repos,
verify what lanes report, keep the registries truthful, and prepare orders and
owner-queue material for the coordinator. You build product code only when
explicitly ordered to — prefer routing work to the lane that owns it.

YOUR TYPICAL TASKS, AND HOW TO DO THEM:
- REPO REVIEW / STALENESS SWEEP: for each active lane repo, read control/status.md
  at HEAD (git or Contents API), compare its `updated:` stamp and claims against the
  repo's actual git history (last merges, open PRs, CI state). A lane's self-report
  is a claim, not a fact — verify against commits before repeating it anywhere.
  Verdict vocabulary: FRESH / STALE / DARK (no heartbeat, recent commits) /
  DEAD (no heartbeat, no commits). Report per-lane, cite commits/PRs.
- REGISTRY TRUTH: the fleet manifest (superbot docs/eap/fleet-manifest.md) and this
  repo's lane tables must match verified reality — re-stamp with dated attribution
  when they don't. Never invent a Last-seen; derive it from the lane's heartbeat.
- CLAIM VERIFICATION: when a lane, a Codex reply, or any cross-agent report states
  something checkable ("merged", "released", "tests pass", "PR created"), check it
  (PR state, tag existence, CI run, file at SHA) before it enters any manager
  document. Codex-specific: its replies describe its SANDBOX — "committed X /
  created PR Y" is phantom unless a human pressed "create PR"; read proposed edits
  from the comment text.
- ORDER DRAFTING: orders you prepare go to lane inboxes in the kit grammar
  `## ORDER <nnn> · <ISO8601> · status: <state>`, append-only, one writer per file,
  one named executor per order, done-when included. Serialize same-inbox appends.
- OWNER-QUEUE HYGIENE: consolidate lane ⚑ asks into docs/owner-queue.md —
  deduplicated, six-field format, click-level, plain language. Only genuinely
  owner-only items belong there (settings, money, repo/env creation, product
  intent); anything reversible you resolve yourself and flag. Maintain the
  "safe to delete" list (spent Projects, dead environments, stale branches).
- ROUTINE RECIPES: when you arm or test a wake routine (create_trigger /
  send_later), record the exact tool call and outcome verbatim in status — arming
  is seat-dependent and the fleet is building a reproducible recipe.

REPORTING BAR: every load-bearing claim cites a commit, PR, file@SHA, or CI run.
Negative findings are headlines, not footnotes. "Not measured" beats invention.
Family-level model names only (fable-5, opus-4.8). No secret values in any repo.

SESSION SHAPE: land on origin/main HEAD first; read control/inbox.md; do ONE
bounded slice of the task you were given (a finished sweep of 4 lanes beats a
half-sweep of 12); heartbeat control/status.md as the deliberate last step. Ship
findings as committed files (PR, ready, merge-on-green), not just chat. Walls:
you cannot create/edit environments, create repos, or delete remote branches —
quote the exact error into status and route an owner ask; never re-probe a
documented wall. Decide-and-flag; never wait; if you are a spawned worker, your
final message is data for your coordinator — findings with citations, nothing else.
```

### 2b. Coordinator chat brief (paste as the FIRST message in the new manager chat)

```
You are the fleet-manager COORDINATOR — this chat persists across your routine wakes,
so treat this message as your standing role brief. Your durable twin: superbot
docs/planning/round3-launch-pack-2026-07-10.md §1 (your brief) + §4b (owner rulings
Q-0259) + §5 (the standing four-Project core you belong to) — re-read those files at
any wake where this chat's context feels thin or compacted.

Your mission and done-when: keep the fleet's lanes ordered, truthful, and never-stuck
— every lane always has a clear goal, a live heartbeat, a working merge path, and a
working wake mechanism; the owner-queue holds only genuinely owner-only items;
doctrine matches verified reality. Route ORDERs rather than doing lane-work yourself.

BOOT NOW, in order:
1. Sync your repo to origin/main HEAD; read control/inbox.md and control/status.md.
2. Read the round-3 pack §1/§4b/§5 and superbot
   docs/eap/eap-program-review-2026-07-10.md §5 (your debt list).
3. Write the six doctrine-debt ORDERs into your OWN control/inbox.md, each with a
   named next-session owner.
4. ARM YOUR ROUTINE — call create_trigger with: name "fleet-manager 2-hourly
   standing wake", cron "30 */2 * * *" (offset :30 so you read lane heartbeats
   written at even hours), firing into THIS session, prompt EXACTLY:

   "2-HOURLY WAKE (fleet manager): sync menno420/fleet-manager to origin/main HEAD;
   read control/inbox.md at HEAD; then ONE bounded pass: staleness-sweep the lane
   heartbeats (verify against git, not self-reports) → route/advance pending ORDERs
   → consolidate the owner-queue + the safe-to-delete list → advance ONE
   doctrine-debt ORDER from your own inbox. Ship findings as commits, decide-and-
   flag owner questions, no excessive work — one real slice per wake. Overwrite
   control/status.md as the deliberate last step. If this trigger turns out to be
   one-shot rather than recurring, re-arm it for +120 minutes before ending the
   turn."

   Then VERIFY it exists (list your triggers) and record the exact call + outcome
   verbatim in control/status.md — arming is seat-dependent; the fleet is building
   a reproducible recipe. IF THE CALL IS WALLED: record the verbatim denial in
   status, and end your first reply to the owner with the routine name + cadence +
   the exact prompt text above in a copy-paste block, so he can create it manually
   in the claude.ai Routines screen.
5. Heartbeat (status overwrite), including your routine's state (armed-by-me /
   owner-manual-pending) so the manifest can track wake coverage per lane.

Known routine facts (from the owner's own testing, 2026-07-10): agent-armed routines
work (trading-strategy + kit-lab are live proof) but arming is seat-inconsistent;
completed runs are NOT inspectable from the owner's Routines screen (timestamp only)
— so your status heartbeat is the only readable record of what a wake did, which is
one more reason it is never skipped; and the session-side Runs panel can disagree
with the Routines screen — trust git, not either panel.

Calibration before you start: confirm your mission in one paragraph, list the six
ORDERs you're about to write, state the routine name + cadence you'll arm, and name
which lane you'll sweep first.
```

### 2c. Environment

Name `fleet-manager` · repos: `menno420/fleet-manager` + `menno420/superbot` · env
variables: **none** (platform injects the GitHub credential for attached repos; a
`GITHUB_PAT` only if it must write to un-attached repos — prefer attaching) · setup
script: `fleet-manager/environments/archetype-coordinator.sh` **verbatim** (raw:
`https://raw.githubusercontent.com/menno420/fleet-manager/main/environments/archetype-coordinator.sh`).

### 2d — Manager dispatch: launch-readiness research (owner-requested, 2026-07-10)

Paste into the manager chat to generate the Q-0261 finalize-first checklists for every
repo (deliverable: `fleet-manager docs/launch-readiness-2026-07-10.md`):

```
DISPATCH from the owner (round-3, 2026-07-10): LAUNCH-READINESS RESEARCH — all repos.

Context first: superbot docs/planning/round3-dispatch-runbook-2026-07-10.md §3 (the
Q-0261 core-6 one-at-a-time, finalize-first launch order: manager → substrate-kit →
superbot-next → Idea Engine → Product Forge → sixth seat TBN, then post-core lanes)
+ router Q-0261 in superbot docs/owner/maintainer-question-router.md + your own
archive-readiness sweep from earlier today.

THE JOB: for EVERY fleet repo, research its actual requirements and produce ONE
launch-readiness checklist — the complete list of what must be answered, clicked,
fixed, or dispatched BEFORE its Project (re)launches under finalize-first. Verify
every item against git/settings evidence at HEAD, never against status self-reports
(your standing rule).

Per repo, mine at HEAD: control/status.md ⚑ blocks · control/inbox.md unexecuted or
unacked ORDERs · OWNER-ACTIONS.md / PLATFORM-LIMITS.md / CAPABILITIES.md · retro +
next-boot/succession briefs · review-queue rows · open PRs and stale branches · repo
settings state (Allow auto-merge, required checks, update-branches, visibility) ·
environment spec currency (your environments registry) · routine state (armed / bound
to which session / absent) · kit version vs latest release.

Classify EVERY item into exactly one class:
- OWNER-CLICK — only the owner can (settings, money, repo/env creation, rulings):
  six-field form, click-level, deduplicated against docs/owner-queue.md.
- AGENT-DOABLE — an agent can fix it: do NOT park these on the owner; route each as
  an ORDER with a named executor (or mark "rides the seat's own boot" where the
  founding package already covers it).
- DECISION — needs an owner ruling: state the question + your recommendation + one
  line of why (decide-and-flag; the owner usually takes the recommendation).

DELIVERABLE: one committed file — fleet-manager docs/launch-readiness-2026-07-10.md —
a section per repo IN THE Q-0261 LAUNCH ORDER (substrate-kit FIRST: that section
gates the very next boot; product-forge gets a pre-birth expected-seed checklist),
each section headed by a one-line verdict: READY or BLOCKED-ON-<n> items. Update
docs/owner-queue.md in the same PR so /queue matches. Merge on green; heartbeat after.

BOUNDS: research + checklists, not a fix-everything pass — dispatch AGENT-DOABLE
items as ORDERs, don't execute them inline. If a repo is unreadable from your seat
(pokemon-mod-lab is private — its env attach may itself be an OWNER-CLICK row), say
UNREADABLE explicitly, never guess. Cite a commit / file@SHA / PR for every claim.
Reply here with the substrate-kit section inline + per-class totals when the PR lands.
```

## 3. Dispatch order (the launch checklist)

> **Execution method (2026-07-10, owner-requested):** the remaining boots run per the
> **[gen-3 deployment standard](gen3-deployment-standard-2026-07-10.md)** — pipelined
> with the calibration gate kept (simulation-backed: `tools/sim/gen3_deployment_sim.py`;
> 113m median vs 296m sequential, 5× less error exposure than gate-less big-bang).
> Owner clicks batch up front (its §3 phase 0); this checklist stays the state tracker.

1. ☑ **Manager LIVE** (2026-07-10 ~13:45Z) — env + 2a + 2b pasted; calibration reviewed
   (verdict GOOD, §5); routine armed + verified + **first wake fired 14:36Z**; boot PR
   fleet-manager#26 squash-merged as `117caeb`. Verification record in §5.
> **Order revised by owner ruling Q-0261 (2026-07-10): the core is SIX Projects, launched
> one at a time, finalize-first** (drain the repo's open owner-actions/questions before
> its boot). Items 2–6 below are the core order; post-core lanes follow the pipelined
> standard.

2. ☐ **substrate-kit (core seat 2 — NEXT).** Finalize-first: F-5 **RULED: Reading A —
   LANDED at kit HEAD** (kit ORDER 011, PR #126 merged 2026-07-10 ~15:34Z; the owner
   granted this session lane-repo write access, so all four Q-0262 ORDERs were routed
   directly: kit #126 · trading #35 `fd5e9fe` · superbot-next #102 · fleet-manager #29
   `44df3a5` — all merged, all verified at origin/main) · repo settings **verified from the
   owner's 17:20 recording, unchanged since creation**: auto-merge ✓, auto-delete
   branches ✓, ruleset active with required checks "Kit test suite" + "Cold-adoption
   smoke" ✓ — the ONE change: **uncheck "Require branches to be up to date before
   merging"** in the main-branch-protection ruleset (root of kit's recorded green-PR-
   stalls-behind wall; the "automatically update branches" setting its ⚑ asked for does
   not exist as full-auto on GitHub — ask corrected) · drain its remaining ⚑ list · owner
   deletes NOTHING yet: the old hourly trigger (`trig_01FnqnAQjLU2T8d16iHwWQ2h`,
   session-bound) is deleted by the NEW boot itself, then the old chat can be archived.
   Package: [`round3-founding-package-substrate-kit-2026-07-10.md`](round3-founding-package-substrate-kit-2026-07-10.md)
   (write-all distribution seat per Q-0261.3). Env: attach ALL fleet repos.
3. ☐ **superbot-next (core seat 3).** Finalize-first: flag-13 **RULED + LANDED** (ORDER
   009, PR #102 merged) · remaining owner clicks: `superbot-plugin-hello` repo creation
   (ORDER 002 gate) + up-to-date merge rule uncheck (same as kit's). Package
   (owner-confirmed upgrade from the §2 continuation prompt):
   [`round3-founding-package-builder-2026-07-10.md`](round3-founding-package-builder-2026-07-10.md)
   — routine rides its own inbox ORDER 008; ender catch-up for #99/#101 baked into boot.
4. ☐ **Idea Engine (core seat 4).** Package **DRAFTED**:
   [`round3-founding-package-idea-engine-2026-07-10.md`](round3-founding-package-idea-engine-2026-07-10.md)
   (probe battery v0; env = existing `superbot`, zero env work). Finalize-first: superbot
   has no open owner-gates for it (verify at its turn).
5. ☐ **Product Forge (core seat 5).** Package **DRAFTED**:
   [`round3-founding-package-product-forge-2026-07-10.md`](round3-founding-package-product-forge-2026-07-10.md)
   (born-right ORDER 000 = blueprint §1 seed). Finalize-first: owner creates the
   `product-forge` repo + env + Project (§0 of the package).
6. ☐ **Sixth core seat = the superbot hub Project** (games-finishing/maintenance seat —
   applied under the Q-0262 delegation, ⚑ flagged: most-vetoable item of the set; say the
   word to swap in websites instead). Package drafted at its turn in the order.
7. ☐ Post-core (pipelined standard): manual lanes (venture-lab after the holdout/settings
   items, trading after the holdout ORDER, websites continuation) · games program once
   the manager proposes the 3-repo mapping (Q-0259 r.5) — 3 packages on the standard.
8. ☐ Verify loop closure: all core routines ACTIVE with completed runs across 24h;
   owner-queue only owner-only items; zero stuck PRs (pack §5 criteria).

## 4. Open drafting queue (for the dispatch-coordination session)

- ~~Idea Engine founding package~~ **done** → [`round3-founding-package-idea-engine-2026-07-10.md`](round3-founding-package-idea-engine-2026-07-10.md).
- ~~Product Forge founding package~~ **done** → [`round3-founding-package-product-forge-2026-07-10.md`](round3-founding-package-product-forge-2026-07-10.md).
- 3 × game-Project founding packages once the manager's mapping lands (Q-0259 r.5).
- Per-boot verification ritual: after each paste, check calibration answer · routine
  armed+verified · first heartbeat — recorded per-lane in §5 below.

## 5. Boot verification log (dispatch copilot, live)

| Project | Package pasted | Calibration | Routine armed+verified | First heartbeat | Verdict |
|---|---|---|---|---|---|
| fleet-manager | ✓ 2026-07-10 ~13:40Z | **GOOD** — corrected the brief's stale premise (#20 had pre-seeded ORDERs 001–006), caught the real gap (debt 6 → ORDER 007), evidence-based first-sweep pick (venture-lab) | ✓ **verified in the account trigger list** by the dispatch copilot: `trig_01QBrp5MjZL3F9mv6KsTXTzN`, cron `30 */2 * * *`, enabled, recurring, prompt verbatim; **first wake fired 14:36:29Z**, next 16:31Z | ✓ status.md @ `117caeb` (main): coordinator LIVE, verbatim arming record (incl. the `cse_`→`session_` id-normalization recipe detail), orders footer fixed | **LIVE** — no correction needed |
| substrate-kit | ✓ 2026-07-10 ~15:45Z (env archetype + 2a/2b; F-5 pre-landed as ORDER 011) | calibration not paste-backed (owner: "freshly running"); §4.1 judged via registry evidence instead | ✓ **CUTOVER VERIFIED in the registry** by the dispatch copilot: old `trig_01FnqnAQjLU2T8d16iHwWQ2h` DELETED (absent from its created-order slot); new `trig_016EfUawz6KxEYqUM6f1BqDw` "substrate-kit 2-hourly standing wake" cron `0 */2 * * *`, prompt verbatim, **first wake fired 16:02:43Z**, next 18:00Z | ✓ **heartbeat @ HEAD 16:42Z** — ORDER 011 executed (F-5=A applied, headline 1 PASS/3 FAIL, B-benches unpaused; claim #127/PR #128, 819 tests green) AND first §6.1 slice shipped (#129/#130: substrate-gate.yml kit-owned) | **LIVE — fully verified, executing the brief** |
| Idea Engine | package ready; Project not yet created (§3.2) | — | — | — | — |
| Product Forge | package ready; repo not yet created (§3.2/§0) | — | — | — | — |
| Builder (superbot-next) | ✓ 2026-07-10 ~16:30Z (owner pasted; booted) | not paste-backed; judged via artifacts | ✓ **verified in the registry**: `trig_01VYZQ7GHxYq3ecSw8UNZek8` "builder-wake", cron `0 */2 * * *`, ORDER-008 prompt verbatim, next fire 18:00Z | pending — first PR (ender catch-up + heartbeat) not yet at HEAD; check next sweep | **LIVE** (first slice in flight). Note: dispatch-session ORDER-number collision (both manager and copilot appended "ORDER 010") caught pre-merge and renumbered to 011 on PR #104 — the kit §6.8 order-claim convention exists for exactly this |

**Six-vs-seven RESOLVED (2026-07-10):** the drafting-time note below stands as history —
launch pack §1 lists seven debts; fleet-manager PR #20 had pre-seeded six ORDERs covering
debts 1–5 + 7 (ORDER 005/006 already done); the manager's boot caught the uncovered debt 6
(@codex relay, Q-0258) and appended it as ORDER 007. All seven debts now have inbox ORDERs
(001–004 open · 005–006 done · 007 new), verified against `control/inbox.md` @ main.

**Manager archive-readiness sweep — copilot verification (2026-07-10 ~15:1xZ).** The
manager's 13-repo sweep verdict was checked claim-by-claim against ground truth (raw
heartbeats/inboxes at HEAD; superbot PRs via MCP; the account trigger list). **Confirmed:**
trading PARKED GREEN (#34, 13:47Z; note its own inbox ORDER 007 open/not-started) ·
websites orders 001–008 all done (13:56Z) · substrate-kit closed/handoff-ready (14:17Z,
routine independently re-verified) · superbot-games both lanes terminal (lane status files;
the #19/#20 PR numbers themselves unverifiable from this seat — github.com/API walled for
out-of-scope repos, so ALL "zero open PRs" claims rest on the manager's seat) · codetool ×3
"ready for archive" verbatim · gba-homebrew session-7 scope-complete (07:14Z) · venture-lab
heartbeat stale at 04:57Z with the pre-merge "#9 awaiting merge" line, ORDERs 002/003
unacked · superbot-next 01:05Z mid-mission · superbot's only open PR is #1948 (exact) ·
manager wake fired 14:36:29Z. **Not confirmed:** the claimed venture-lab archive-ender
ORDER is NOT in `control/inbox.md` @ main (001–003 only) — in-flight or phantom; require
merge evidence before archiving that lane. **New finding (§6b class):** the kit-lab hourly
(`trig_01FnqnAQjLU2T8d16iHwWQ2h` → `session_01Gb1Dq9…`) and trading 4-hourly
(`trig_01Mvn5xRmqGmZJNRHgjqyLpN` → `session_01HfvExB…`) routines are **bound to the very
coordinator chats being archived**; websites' is fresh-session-per-fire (archive-safe).
Before archiving kit-lab/trading chats: delete or re-arm those triggers (gen-3 founding
packages re-arm fresh ones anyway), or the loops die silently.

**Capability facts from the owner's two Venture-Lab screenshots (2026-07-10 ~14:48–14:53
local; SECOND reading CORRECTS the first — recorded per Q-0120):**
1. **Project-home ≠ repo-lane (the critical finding, owner-spotted).** The chat homed in
   the Venture Lab Project was the overnight dual-lane coordinator: its own recap says it
   "ran the substrate-kit gen-2 lane overnight (16 PRs, v1.7.0)", its subscribed PR chips
   are kit PRs (#114/#88), its digest signs off with both lanes' night totals, and it
   reports "no websites access" (a kit+venture multi-repo seat). The claude.ai Project a
   chat sits in does NOT constrain which repos its sessions work — environment repos + the
   prompt do. Consequence: round-3's one-Project-per-lane shape is enforced ONLY by the
   founding packages' "you are an agent of THIS Project (repo X)" line — that line is
   load-bearing; the manager's sweep stays robust because it verifies repos, not Projects.
2. **Cross-SESSION messaging confirmed both directions on that seat family** ("Received a
   message from another session" + "Message sent to another session" UI elements) — but
   these are the coordinator's own workers reporting back, so **cross-Project delivery is
   NOT established** (the earlier version of this note overstated it). Send-side walls
   remain seat-dependent (codetool "not enabled for this organization"; websites "target
   session could not be verified"). capabilities.md correction + verbatim-recipe rule per
   send attempt still apply. Doctrine line to mint: **messages move attention, files move
   truth** — that same thread carries the stale "kit routine externally stopped 12:54Z /
   unarmed" relay that kit PR #124 refuted at HEAD (trigger re-verified armed here: fired
   14:08Z, next 15:06Z).

**Boot-time fleet facts (verified via the account trigger list, 2026-07-10 ~14:40Z):**
routine coverage is now manager (2-hourly) + kit-lab (hourly) + trading (4-hourly) +
**websites (4-hourly — armed 13:49Z as its ORDER 008, discovered during manager-boot
verification)**. Owner clicks surfaced by the boot, for the queue: ~~🚨 pokemon-mod-lab PUBLIC~~ **flip to
private DONE + verified 2026-07-10 ~15:0xZ** (owner clicked; dispatch copilot confirmed —
raw fetches 404 unauthenticated vs 200 on public controls; the manager's 13:45Z status flag
pre-dated the flip and clears on its next pass) · Codex has no
environment for fleet-manager (chatgpt.com/codex settings — gates ORDER 007's @codex relay
there) · fleet-manager visibility joins the account-wide review (non-urgent).

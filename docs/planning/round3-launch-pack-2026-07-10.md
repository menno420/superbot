# Round-3 launch pack — 2026-07-10

> **Status:** `plan` — owner-directed. Everything the owner needs to paste, in order, to
> start round 3 (gen-3 prep): the fleet-manager brief (§1), the per-lane continuation +
> night-review prompt (§2), Codex external-review prompts (§3), and the owner decision
> sheet with recommendations (§4). Built from
> [`../eap/eap-program-review-2026-07-10.md`](../eap/eap-program-review-2026-07-10.md) and
> [`../eap/fleet-overnight-review-2026-07-10.md`](../eap/fleet-overnight-review-2026-07-10.md).
> Owner-usage: paste §1 into the **fleet-manager** Project first; then §2 into each working
> lane Project (edit the one bracketed line per lane); §3 into Codex whenever convenient;
> answer §4 at leisure — answers flow to lanes through the manager.

## §1 — Fleet-manager brief (paste verbatim into the fleet-manager Project)

```
ROUND-3 BRIEF from the owner (via the superbot review session, 2026-07-10).

Context to read first, in this order (all committed):
1. superbot docs/eap/fleet-overnight-review-2026-07-10.md — the audited verdict on last night.
2. superbot docs/eap/eap-program-review-2026-07-10.md — the whole-EAP review; its §5
   structural findings are YOUR work queue; §6 is the centralization agenda.
3. superbot docs/planning/projects-eap-evaluation-log.md — the 2026-07-10 ~11:01Z entry.

NEW CAPABILITY — routines (this falsifies your capabilities.md and blueprint §2a):
Agent-armed wake routines WORK. Owner screen recordings (11:01Z + 11:04Z, on file) show
two ACTIVE routines "Created by Claude" and firing: trading-strategy 4-hourly (run 10:09)
and kit-lab hourly (runs 12:28/12:28/12:30, driving the live kit-lab coordinator session).
Mechanism: the claude-code-remote scheduling tools (create_trigger / send_later family) —
evidently seat-dependent, same per-seat inconsistency class as the merge classifier.
Your orders on this:
(a) correct capabilities.md + blueprint §2a — replace "walled both sides" with the
    verified per-seat reality;
(b) have every lane that arms (or fails to arm) a routine record the exact mechanism in
    its status: tool name, arguments, session/seat type, verbatim error on failure — so
    arming becomes a reproducible recipe, not luck;
(c) arm the remaining active lanes agent-side (superbot-next, websites, venture-lab,
    game-lab) at blueprint cadences; report which seats succeed and which are walled;
(d) log the two observability bugs in the EAP journal pipeline: completed runs not
    inspectable from the Routines screen; the session-side Runs panel says "No runs yet"
    while the Routines screen shows completed runs.

STANDING DEBTS — write these as ORDERS in YOUR OWN control/inbox.md (the doctrine change
from program-review §5.1: amendments get an ORDER + a named next-session owner, never a
dangling "some future session"):
1. Apply P1–P11 to gen2-blueprint.md, and D4/D5/D6 (wind-down marker carve-out; remove the
   false routine promise from init-prompt-universal.md — now REWRITE it to the verified
   recipe; write your own MISSION.md with a done-when).
2. Re-stamp superbot docs/eap/fleet-manifest.md to post-launch reality (all rows), then
   propose the roster's move to generated-from-heartbeats (program-review §6.2) so this
   class dies.
3. Review-queue enforcement: adopt an auto-append rule (any PR > N lines of runtime code,
   or any self-flagged risk, MUST get a review-queue row) + name a standing drainer.
   116 merged PRs / zero rows is the current state; that voids the post-merge-review law.
4. Fleet economics ledger BEFORE 2026-07-14 (the free window closes then): per-lane
   session/run counts and whatever cost signal is visible; the cadence table was built on
   zero cost data.
5. Fix your own ping-test report's known-false websites "NO ACK" row (two ⚑ flags old).
6. **Mint the @codex review-relay playbook rule (owner directive Q-0258, 2026-07-10):**
   any lane session with a review-worthy-but-not-owner-only question posts it as a PR
   comment mentioning @codex (one specific question, on the final head; template in
   superbot docs/planning/codex-review-integration-plan-2026-06-17.md Part C) instead of
   parking it in the owner-queue. Codex is the named standing drainer of the post-merge
   review convention; Q-0120 governs the return path (verify, never obey). The owner is
   enabling the Codex GitHub integration across the valuable repos.
7. Correct the codetool release-wall contradiction: opus4.8 PROVED workflow_dispatch
   releases work (2 live releases); fable5's succession doc says the route is "closed
   permanently". Reconcile before any gen-3 lane inherits the wrong lesson, and fold the
   model-comparison seat-contamination caveat (overnight-review finding 6) into the
   experiment record.

OWNER PRIORITY FOR ROUND 3 — GAMES COMPLETION WAVE:
The owner's standing direction: the Projects are the perfect place to finish/improve ALL
the games connected to the bot — superbot's live game cogs, superbot-next's band-6 games
port, the games lanes' exploration/mining slices, and the Game Lab tracks. Bias every
games dispatch to "a build is better than no build": ship playable, imperfect increments
every session; polish later. Sequence game lanes accordingly when you write orders.

STANDING AUTONOMOUS CORE (owner design — read §5 of this pack):
Four Projects run permanently on ~2-hourly routines and loop without the owner: you
(manager), a NEW dedicated Idea Engine Project on the superbot repo, the superbot-next
builder, and a Product Forge in a NEW `product-forge` repo (owner-corrected: NOT
venture-lab, which stays a revenue-specialist manual lane). Your role in the loop: route the Idea Engine's proposals as ORDERs, consolidate the owner-queue, and
watch the four routines' liveness in your staleness sweep. All other Projects are
owner-started manually, one by one.

GEN-3 PREP:
Collect every lane's night self-review (the owner is pasting a continuation+review prompt
into each lane; their answers land in their repos), plus the Codex external reviews the
owner dispatches, and synthesize the gen-3 blueprint delta the same way gen-1 retro fed
gen-2. Do NOT relaunch lanes for gen-3 until the owner has seen your consolidated
"state of the fleet + gen-3 delta" report — he wants one gate here, at the blueprint.

Also: the owner will be testing the three websites today and filing suggestions; expect a
suggestions ORDER for the websites lane and treat his notes as product feedback with
priority. Report back: one consolidated status + a fresh owner-queue when the above is
underway. Silence rules unchanged: heartbeat first, decide-and-flag, no waiting.
```

## §2 — Lane continuation + night-review prompt (paste into EACH working lane Project)

Edit only the `[LANE FOCUS]` line per lane (suggestions under the block). Lanes to paste
into: superbot-next · Self Improvement (kit-lab) · websites · trading-strategy ·
venture-lab · Game Lab · Superbot Exploration · Superbot Mining.

```
CONTINUATION + NIGHT REVIEW (owner, 2026-07-10).

Step 1 — sync: land on origin/main HEAD first; read your control/inbox.md at HEAD.

Step 2 — night self-review (commit as docs/retro/night-review-2026-07-10.md, same honesty
rules as the gen-1 retro: cite commits/PRs, "not measured" over invention):
 a. How did last night actually go from inside your lane — what worked, what fought you?
 b. What did you claim that an outside reviewer should re-verify, and how?
 c. What broke or surprised you that your docs don't yet record?
 d. Every question you have for the owner — as proper six-field OWNER-ACTION entries in
    your status ⚑ block (the manager consolidates them; answers come back as ORDERs).
 e. Routines: did/can your seat arm a wake routine (create_trigger / send_later)? Record
    the exact tool call and outcome (verbatim error if walled) in control/status.md.
 f. One improvement to the fleet workflow itself you'd want before gen-3.

Step 3 — continue: [LANE FOCUS].

Step 4 — your normal session enders + status overwrite. Decide-and-flag; don't wait.
```

Per-lane `[LANE FOCUS]` suggestions:
- **superbot-next:** band-5 live-drive leg (testing ladder step 7), then band-6 games; the
  warn-escalation semantic regression fix (quality-review §10 prescription) jumps the queue.
- **kit-lab:** stay paused on B-benches pending the F-5 ruling (§4.1); meanwhile ship the
  born-red gate fix from gba-homebrew's workflow into the kit CI template + make
  substrate-gate.yml kit-owned on upgrade (program-review §6.1), and the claims-template
  unification (§6.4).
- **websites:** reconcile the GITHUB_TOKEN status claim vs the live board (overnight-review
  finding 3) + move the PAT ask into OWNER-ACTIONS.md properly; then the /fleet
  manifest-parse smoke check (your queued NEXT item). Expect owner UX suggestions today.
- **trading-strategy:** nothing until the holdout ruling (§4.2) — if granted, execute
  docs/p5-holdout-protocol.md exactly; also fix the manifest name mismatch ("trading-lab"
  vs repo name) with the manager.
- **venture-lab:** refresh status/review-queue (both still pre-date the #9 merge); package
  the ⚑A–D owner clicks into one tight block; no new candidates until the merge-path fix.
- **Game Lab (pokemon-mod-lab):** extend the ROM-builds CI as required-check prep; stay
  PARKED for builds until the concept pick (§4.3) — night review + owner-queue polish only.
- **gba-homebrew (if separate) / Game Lab track B:** Lumen Drift release-prep polish
  (README, controls doc, ROM artifact for the owner to sideload) — the owner should get to
  PLAY it; no new concept until §4.4.
- **Superbot Exploration / Mining:** fix the CI gap FIRST (gate runs only tests/ — add
  games/exploration/tests, the one-line change from overnight-review finding 2), reconcile
  docs/current-state.md to merged reality, then continue your queued P2 slices.

### §2b — Games completion wave (owner priority: "a build is better than no build")

Extra dispatches the owner can paste any time, all biased to shipping playable increments:
- **superbot-next → band-6 (games)** is the natural next band anyway — dispatch it with
  the build-over-perfect bias stated explicitly.
- **Superbot Exploration / Mining** — after the CI fix, run the P2 slices as fast playable
  increments (grid encounters, quest chains) rather than waiting on full parity.
- **superbot (live bot) games-finishing session** — a Project session on the hub repo
  sweeping the S1 game surfaces for unfinished edges (fishing corals follow-ups, creature
  game, blackjack/RPS/deathmatch polish, the never-owner-played gear walk from the eval
  checklist) and shipping the small completing slices directly (they deploy on merge).
- **Game Lab** — Track A builds QoL+ patches 13+ once the §4.3 pick lands; Track B does
  Lumen Drift release-prep so the owner can actually play the build.

## §3 — Codex external-review prompts (dispatch when convenient)

Three independent reviews; paste each into a fresh Codex task. They exist to break the
closed Claude-verifying-Claude loop (program-review §5.8).

*(Full self-contained versions — delivered to the owner in-session 2026-07-10; paste each
into a fresh Codex task.)*

**Codex A — doctrine audit (fleet-manager's rules vs reality):**

```
You are an external, adversarial reviewer. Work read-only against the public GitHub repos
menno420/fleet-manager and menno420/superbot (clone or browse them — everything is public).

Read first:
- fleet-manager: docs/gen2-blueprint.md and docs/playbook.md (the fleet's binding doctrine)
- superbot: docs/eap/eap-program-review-2026-07-10.md §5 (known structural findings)

Task: audit the doctrine against the evidence in both repos. Specifically:
1. For each blueprint/playbook rule, classify it: enforced by machinery (a checker, CI
   gate, or template) vs prose-only (exhorted but nothing catches a violation).
2. Identify claims the record has already falsified — start with the wake/routines
   doctrine (see superbot docs/planning/projects-eap-evaluation-log.md, the 2026-07-10
   ~11:01Z entry) and the merge-authority/auto-merge rules, and hunt for more.
3. Rank the 10 riskiest prose-only rules: the ones whose silent violation would cost the
   most, with a one-line cheapest-enforcement proposal for each.

Rules for you: cite a file path, PR number, or commit for every claim; if you cannot
verify something, say so explicitly rather than assuming; do not trust any document's
self-description — check whether the mechanism it names actually exists in the tree.
Deliver: a single markdown report, findings ranked by severity.
```

**Codex B — runtime code review (superbot-next, the rebuild):**

```
You are an external code reviewer. Work read-only against the public GitHub repo
menno420/superbot-next (the ground-up rebuild of a Discord bot, currently at band 5 of
its port).

Context: an internal quality review (see menno420/superbot
docs/eap/fleet-quality-review-2026-07-09.md §10) found one proven semantic regression in
the warn-escalation logic (escalation count reset + history rows written pre-commit with
no compensator, with a unit test enshrining the wrong behavior). Start there:
1. Verify whether that regression is fixed or still present at HEAD (sb/ tree). If
   present, propose a minimal-diff fix with a test that pins the ORACLE behavior (the old
   bot's semantics, documented in the parity/ corpus), not the current behavior.
2. Then review the band 1–5 runtime (sb/domain, sb/services, state machines, persistence)
   for the same defect class: state mutations before commit points, missing compensators,
   count resets, event-ordering assumptions, and unit tests that assert buggy behavior.
3. Check the games code (sb/domain/games) for crash paths like the recently-fixed
   worldcard Reply-shape bug (a raw dict returned where a Reply object was expected).

Rules: cite file:line for every finding; rank by user impact; propose minimal diffs with
tests; explicitly separate CONFIRMED bugs (you traced the failure) from SUSPECTED
(pattern-matched, needs a repro). Deliver one markdown report.
```

**Codex C — hostile fact-check of the record itself:**

```
You are a hostile auditor checking the checkers. Work read-only against the public GitHub
repo menno420/superbot and the live GitHub API/UI for the menno420 account's repos.

Target documents:
- docs/eap/gen1-grand-review-2026-07-09.md
- docs/eap/fleet-overnight-review-2026-07-10.md

Task: sample 15 factual claims across the two documents — mix PR numbers, merge states,
test counts, timing claims, and cross-repo assertions (e.g. "zero open PRs", "116 PRs
merged 00:00–06:15Z", "21/21 incidents verified", per-repo test totals). For each claim:
1. Re-verify it independently against live GitHub (PRs, commits, CI runs, file contents
   at the cited SHA) — do not use the documents' own citations as proof.
2. Verdict: CONFIRMED / REFUTED / UNVERIFIABLE, with your evidence (links, numbers).

Bias yourself toward refutation: pick the claims that would be most embarrassing if
wrong, not the easiest to confirm. Two corrections have already been applied to this
corpus (see docs/eap/README.md and PR #1926) — finding a third is the success condition,
not an insult. Deliver one markdown report: the 15 claims, verdicts, evidence, and any
pattern you notice in what kind of claims drift.
```

Return path for all three: Q-0120 / Q-0258 — drop each report into the matching Project
(A → Project Manager, B → the Builder, C → any superbot session); the receiving lane
re-verifies every finding against source before acting.

## §4 — Owner decision sheet (recommendations included; answer at leisure)

1. **Kit F-5 wording ruling (HOT — kit-lab's dispatch is paused on it).** Impact after
   bench run-4: only the headline + runs 2–3 scoring (run-4 fails under both readings).
   **Recommendation: take the stricter Reading A.** Honest-negative headlines are the
   fleet's credibility asset; a flattering reading buys nothing operationally. One line to
   the kit-lab Project unpauses it.
2. **Trading holdout unlock.** The protocol is pre-registered, code-enforced, one-shot.
   **Recommendation: grant it** via an ORDER in trading's inbox naming
   `docs/p5-holdout-protocol.md` as binding — the lab is otherwise done and idle.
3. **Pokemon concept pick** (QoL+ / Hard / Nuzlocke). **Recommendation: QoL+** (the lane's
   own recommendation; 12 patches already form its foundation). Better: play the 12
   patches first — your playtest verdict is itself a queued ask.
4. **GBA next step.** Lumen Drift is scope-complete. **Recommendation: order release-prep
   (ROM + docs for you to play) before any new concept** — you owning/playing the output
   is the real acceptance test both game lanes are missing.
5. **superbot-next flag-13 corpus-red disposition.** Gates the first parity pending→ported
   flip. **Recommendation: accept the lane's own proposed disposition in its status** —
   it's a reversible-on-paper planning call (Q-0240 class), reviewable at the parity gate.
6. **Model-line policy.** Trading writes "withheld per session policy", nulling its rows in
   the fleet's model dataset. **Recommendation: rule that family-level names (fable-5,
   opus-4.8) are required everywhere, exact IDs never** — matches superbot's telemetry
   vocabulary idea and un-nulls the data.
7. **OWNER-ACTION field-grammar standoff** (venture-lab's WHY/VERIFIED-WHEN vs the kit's
   WHY-IT-MATTERS/VERIFIED-NEEDED). **Recommendation: the kit wins by definition;**
   venture-lab conforms at its next kit upgrade. One line to the manager settles it.
8. **Instruction packages (8 undeployed).** **Recommendation: don't paste any today** —
   they should be re-based on the gen-3 blueprint delta anyway (several were written
   blueprint-blind); deploy in one sitting when the manager's gen-3 report lands.
9. **Repo-settings sweep (one ~15-min sitting, no thought required):** tick *Allow
   auto-merge* on trading-strategy + venture-lab; make *substrate-gate* a required check on
   venture-lab and *ROM builds* on pokemon-mod-lab; relax superbot-next's
   require-up-to-date merge rule; create the `superbot-plugin-hello` repo (agents 403);
   delete the ~50 stale merged branches fleet-wide (agents 403 on ref deletes; the exact
   lists are in each repo's status ⚑ block).
10. **venture-lab first-revenue clicks (⚑A–D — whenever you feel like it, not urgent):**
    publish the two zips, optional Stripe test keys. This is the actual first-revenue path.

## §4b — Owner rulings received (2026-07-10, Q-0259) — supersedes the open items above where they overlap

1. **Budget:** core-4 runs indefinitely within normal session limits — routine prompts must
   bound work per wake ("don't work excessively"); economics ledger detects excess, doesn't gate.
2. **Gen-3 = verify-and-consolidate:** the manager's gen-3 report is structured around four
   things — verify gen-2's results · find the CAUSE of the improvements · improve per-repo
   environments · give every project a clear goal + a confirmed routine-arming recipe.
3. **Rebuild:** finish as fast as reasonably possible at overnight pace; **standing @codex
   review on substantive superbot-next PRs** (owner rates Codex PR reviews highly; extends
   Q-0258). Games parallel, finetuned into the bot later.
4. **Venture-lab: profitability mandate** — fund the fleet; durable/sustainable growth; any
   methods. Money protocol: any spend needs a plan showing exactly what the owner must
   do/enable/buy + conservative earnings & payback estimates (expect bad results, never
   overstate).
5. **Games program: 3 dedicated game projects, each their own repo**, continuously improving
   games / inventing new ones / modding other games, presenting a few options wherever wise.
   Owner plays after the EAP; capability test by design. Manager maps existing lanes
   (superbot-games shared · pokemon-mod-lab · gba-homebrew) onto this shape decide-and-flag.

*(Decision-sheet items 2/3/4 above are herewith answered; F-5 (item 1), the settings sweep
(9), holdout unlock ORDER (2→granted in principle, needs the inbox ORDER naming the
protocol doc) and the venture clicks (10) remain the owner's open items.)*

## §5 — The standing autonomous core (owner design, 2026-07-10)

Owner directive: **four Projects always running on ~2-hourly routines, looping together
without regular owner input.** They resolve owner questions themselves wherever the
decision is reversible (Q-0240 decide-and-flag) and park only true owner-only asks in the
owner-queue. All *other* Projects are started manually one at a time whenever the owner
feels like it (routines optional there — more steering, or temporary test cases).

| # | Role | Seat (recommendation) | Mission in one line |
|---|---|---|---|
| 1 | **Manager** | fleet-manager (existing) | Staleness sweep · route orders · consolidate the owner-queue · keep doctrine current (§1 debts) |
| 2 | **Idea Engine** | **NEW dedicated Project on the superbot repo** — *not* substrate-kit: the ideas pipeline (docs/ideas/, router, grooming doctrine) lives in superbot, and kit-lab already has its own mission; fleet ideation inside the mechanism repo repeats the §7 ordering inversion | Generate + groom ideas into docs/ideas/, promote the best into plans, and propose routing ORDERs to the manager for lane repos |
| 3 | **Builder** | superbot-next coordinator (existing SuperBot Project) | Work the band order (band-6 games next) under the build-over-perfect bias |
| 4 | **Product Forge** | **NEW dedicated repo + Project (`product-forge`), born-right per the gen-2 blueprint** (required check from day 1 so auto-merge works; owner creates the repo — repo creation is an agent wall). Builds each routed idea as a self-contained product in its own subtree (the codetool-labs pattern). *Owner-corrected 2026-07-10: NOT venture-lab — that lane is specifically revenue-focused and stays a manually-started specialist* | Take routed ideas and build them into finished, shippable products end-to-end |

**Loop shape:** Idea Engine files/promotes → Manager routes as ORDERs → Builder + Forge
consume → Manager consolidates results + owner-queue → Idea Engine grooms from what
shipped. Stagger the cadence so the manager reads fresh heartbeats: lanes wake at even
hours (:00), the manager at odd hours (or +1h offset).

**Routine text (paste into each of the four Projects — each arms its own routine, which
two lanes have already proven possible):**

```
Arm a recurring routine for this Project yourself using the scheduling tools
(create_trigger; cron every 2 hours). If your seat is walled, output the exact routine
name + instruction text for the owner to create manually, and record the verbatim denial
in control/status.md. The routine instruction text:

"2-HOURLY WAKE (<role>): sync to origin/main HEAD; read control/inbox.md at HEAD; do your
role's standing job [Manager: staleness sweep + order routing + owner-queue consolidation
| Idea Engine: groom docs/ideas/, promote one idea, propose routing orders | Builder:
advance the current band | Product Forge: advance the current product]; decide-and-flag
owner questions (resolve reversible ones yourself; park true owner-only asks as six-field
OWNER-ACTION entries); ship something real every wake (a build is better than no build);
heartbeat overwrite last. If this trigger is one-shot rather than recurring, re-arm it
for +120 minutes before ending the turn."
```

**Success criteria for "correctly set":** all four routines show ACTIVE + Created-by-
Claude with completed runs across 24h; the owner-queue grows only with genuinely
owner-only items; zero stuck PRs. Then the manual start-up of the remaining Projects
begins, one by one.

## §6 — Owner fleet-watching guide (for today's slow lap)

The tracking you're after already exists on the control-plane site
(`https://control-plane-production-abb0.up.railway.app`):
- **/fleet** — every lane's heartbeat (phase, health, last-shipped, blockers) parsed live
  from each repo's `control/status.md`; this is the "all variables in one place" view.
- **/queue** — every ⚑ OWNER-ACTION across the fleet, deduplicated, newest-first, with
  copy buttons — this is *your to-do list rendered*; §4 above should match it.
- **/environments** — the per-repo environment/setup registry.
- **/activity.xml** — Atom feed of fleet activity (subscribable).
Plus `https://dashboard-production-a91b.up.railway.app` (superbot's own dashboard.json
feed, ~12 pages) and `https://botsite-production-cfd7.up.railway.app` (the bot site).
While testing: jot anything confusing/missing as one line each; hand the list to any
session (or straight into the websites Project) and it becomes ORDER material — the
websites lane explicitly expects your UX suggestions today (§1 tells the manager so).

### §6b — Interface hygiene rules (owner cleanup, 2026-07-10)

- **⚠️ Never delete a Project with an ACTIVE routine bound to it** — routines run *inside*
  their Project ("continues in the same session across runs"); deleting the Project kills
  the loop silently. Check the Routines screen before any Project deletion.
- With that rule, Project deletion is safe by design: **memory = repos, never chats** — a
  deleted Project loses only chat history. Spent Projects (wound-down labs, test cases)
  can go freely. *(Owner executed 2026-07-10: codetool Projects + "sonnet 5 test" removed.)*
- Environments: one per repo, named exactly like the repo, standard exit-0 setup script;
  delete the rest.
- Standing automation: the manager's rollup includes a **"safe to delete" list** (spent
  Projects, dead environments, stale branches) so interface hygiene is a report, not a
  chore.

### §7 — Repo disposition (owner review, 2026-07-10)

Full verdicts delivered in-session; the record: **delete no repos** (they are the fleet's
memory, public and free). Keep all core/lane repos. The three codetool labs each built a
real product (mdverify — *released*; cfgdiff; envdrift): **harvest first**
(`docs/ideas/adopt-codetool-lab-tools-2026-07-10.md`), then archive `codetool-lab-sonnet5`
+ `codetool-lab-fable5` (read-only), keep `codetool-lab-opus4.8` unarchived (live released
tool + the proven release recipe). The felt clutter was Projects/environments, not repos —
see §6b.

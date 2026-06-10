# 2026-06-10 — Vision ideation + capture session

**PR:** #680 (draft at first push per Q-0052; docs-only). **Prompt:** the
maintainer wrote a long product-vision statement ("I want superbot to be the
best bot ever made") and asked for (1) a review, (2) the agent's own creative
thinking about the perfect SuperBot, (3) using the session to generate new
ideas and improvements for existing and new functions.

## Arc

Pure ideation/capture session — the Q-0015 conveyor doing its intake step on a
big owner-voice drop. The vision turned out to stand ~70% on already-shipped or
already-decided ground (character platform §7 waves, Q-0040 bounded-menu AI DM,
pets plan, help projection seam #657/#659, setup advisor seam), so the real
work was the **dedup map** — separating "this exists", "this is decided", and
"this is genuinely new" so future sessions neither re-litigate nor duplicate.

## Shipped

**`docs/ideas/superbot-vision-2026-06-10.md`** — owner-voice vision (§1),
dedup map (§2), new owner items **V-01…V-12** (§3), agent creative response
**AG-01…AG-15** (§4), honest tensions **T-1…T-5** (§5), routing ledger (§6).
Indexed in `ideas/README.md`, `roadmap.md` Someday, brainstorm §7.8 pointer.
Highest-leverage new items: per-user preferences as a third settings scope
(V-04/AG-04, converges with wizard PR4 `/myprofile`), the deterministic quest
engine + "Story Actions" view as the concrete Q-0040-compliant AI-DM mechanism
(AG-08/AG-09), and the ≤3-clicks/2-minute UX laws as checkable invariants
(AG-01).

## Decisions + grooming (after the capture)

One structured-choices round (protocol 6a) → **Q-0078** (router §34), all four
answered: **one-way ascent** difficulty switching (T-3) · **both pet paths**
(T-1; pets plan amended in place) · the **4-button Help Home** layout (T-4) ·
next planning targets = **RPG survival design + help home/navigation**. The
grooming move executed the first pick:
`docs/planning/rpg-survival-difficulty-design-2026-06-10.md` (difficulty
contract D1, lazy-clock energy/hunger D2/D3, fishing/cooking D3/D4,
encounters D4, death-as-rescue D5, duel-XP quick-win D6; P1–P5 phasing;
gates G1–G3; Easy-mode byte-identical as the headline pin). The
help-home/navigation plan is the named next grooming target, sequenced with
the Help lane's overlay editor UI.

Follow-up owner correction → **Q-0079**: no per-panel button caps ("the 3
buttons per panel is never going to work"); cleaner UX = fewer or
**better-defined** buttons (labels/grouping/placement); removal only for
genuine redundancy — almost all current buttons are useful. The vision's "≤3"
is navigation depth only. Routed into the capture doc (§1/V-03/AG-01/§6) +
the roadmap interface row; binds the upcoming help-home/navigation plan.

## Deep-questions round (owner-requested, agent-initiated)

The owner asked the agent to pose its own highest-value questions. Checked
the router + idea docs first and dropped one candidate before asking (bot
personality — owner-vision-2026-06-08 §16 already decided funny/sarcastic,
consistent across all commands). One structured round → **Q-0080–Q-0083**
(router §35): **public bot is the goal** · **solo-core RPG + co-op overlays**
· **hard-ceiling AI spend** (€ figure owed after first prod measurements) ·
**full-self-driving workflow end-state** (owner clarified live: *not* a
near-term goal — it arrives as the backlog thins). New tension **T-6**
(public scale × cosmetic-only donations × fixed ceiling) captured in §5.

Calibration note for future agents: on two of the four (Q-0080 distribution,
Q-0083 autonomy) the owner chose **further than the recommended safe option**
— he aims at the ambitious end-state and stages the path, rather than hedging
the destination. Weight recommendation framing accordingly.

## Merge-autonomy grant (Q-0084)

Mid-conversation the owner granted the first Q-0083 trust tier, verbatim in
the router: **agents merge their own session PRs when they judge the work
done** (motivation: parallel-agent merge conflicts — stale open PRs are the
window; prompt merges let him run more agents at once). Envelope: re-sync
`origin/main` first (UNION-resolve; merging agent reconciles) · CI green on
the final head · merge-commit · own-PR scope · **merge ≠ deploy**. Routed:
CLAUDE.md §Session workflow (SESSION_WORKFLOW block) · collaboration-model
north-star note · ai-project-workflow §9. Live proof during the very same
conversation: #681 merged mid-chat and this branch absorbed it (the §9
same-line current-state UNION, ~2 min). PR #680 then merged by the agent —
the grant's first exercise.

## Production incident (same conversation): Railway build outage → PR #685

Answering the post-merge "what else is useful" backups question, the owner
reported the bot down on Railway ("missing python") with the build log
attached. Diagnosis from the log: **no repo-side Python pin existed**, so
railpack's floating default (`3.13` → latest patch) resolved to brand-new
CPython **3.13.14**, which python-build-standalone hasn't published binaries
for yet (latest pbs release `20260602`; asset probe: 3.13.14 → 404,
3.13.13 → **200**) → `mise install` fails, three consecutive deploy builds
dead. Postgres Online throughout — bot-offline only, no data impact.

Fix (PR #685, merged + auto-deployed same hour): **`.python-version` =
`3.13.13`** (railpack reads mise-compatible version files; CI/local pin 3.10
explicitly and never read it) + the first **`docs/operations/production-deployment.md`**
(Railway facts incl. auto-deploy-on-merge — which means Q-0084 merges DO
reach prod; restarts/verification stay the owner's — pin bump procedure,
incident log, **backups = OPEN**, the live discussion). **Q-0085 routed
open** (router §36): CI 3.10 vs prod 3.13 interpreter drift — recommend
aligning CI up to 3.13 in its own session, owner picks.

Process note: the owner's hosting answer (Railway + native PG) was the first
answer to the backups discussion — the posture design (snapshots vs. offsite
pg_dump, retention, restore drill) is still the open thread; the new doc's
Backups section is its landing page.

CI lessons from this PR (both now in the journal QR): CI runs
`check_docs --strict` (badge errors pass plain `check_docs` locally — bit
this PR once) and the top-level-docs ratchet has a **hard pytest twin**
(`test_repo_top_level_docs_within_ratchet`, budget 16) — bit it twice;
resolved by creating `docs/operations/` rather than bumping the budget.

## Post-incident owner round (same conversation)

Four answers while the fix's CI ran: (1) **Q-0086 committed** — AI provider
keys into agent session env; joint live-test mode = owner drives Discord,
agent watches test-bot logs + fixes live (router §36, incl. standing
secrets-handling rules). (2) **ChatGPT template rework = owner's own action
item** (Q-0084 addendum). (3) Real-user signal status: ~none yet beyond BTD6
AI testing — the owner himself walks all commands across multiple servers and
has a private list of **unreported behavior inconsistencies** ("not important
yet") — standing invite recorded to drop them any session. (4) **Commissioned:
the untested-surface testing checklist** (all commands/prompts neither
auto-testable nor explicitly live-tested) — routed onto the roadmap's new
**Recommended session queue** block (with backup posture + help-home plan).
Session continued into a capabilities brainstorm at the owner's request.

## Brainstorm round 2 (same conversation): Q-0087 + Q-0088

The capabilities menu (game simulation · nightly caretaker · verified
research · screenshot testing) landed; the owner's reply produced two
routed decisions:

- **Q-0087 — balance philosophy + simulation methodology** (router §37):
  casual minutes/day must earn real capability progress; grinder rewards are
  real but never mandatory-feeling for capability. Survival plan amended —
  new **D0** (binding philosophy), new **P0** (the simulation harness:
  casual-curve / grinder-surplus / capability-gap bands as CI-pinned tests),
  G2 takes sim outputs. Screenshots: already his standing habit — no change.
  Monetization: unchanged posture; he expects a platform migration off
  Railway if it ever monetizes (T-6 context note).
- **Q-0088 — the self-driving correction** (router §37): foundation now,
  small — his role converges to ideas + strict function/UX guidelines. Two
  problems on record: runaway unguided session tails (built a duplicate
  function once — #678-class) and ~700–800K context degradation. Design
  routed to **workflow §10**: bounded ≈2-task sessions wrapping before ~700K
  + handoff baton + staged continuation (Stage 0 one-click
  `workflow_dispatch` fresh-context session → Stage 1 cron caretaker);
  protocol activates when Stage 0 lands (his conditional honored). Journal QR
  carries the context-budget + no-unguided-PRs guidance immediately.

Calibration: this is the second same-day instance of the owner moving
*further* than his earlier stated position once shown a concrete mechanism
(Q-0084 merge grant, now Q-0088) — consistent with the §35 calibration note.

## Brainstorm round 3: "can the bot test itself?" → idea captured

## Brainstorm round 5: the open-world federation + competitive mining (V-13/V-14)

Two new owner statements captured into the vision doc §3: **V-13** — the
multi-ecosystem open world (mining = foundation ecosystem because "it has all
the variables in one section"; ecosystems connected-but-separate; maybe
per-ecosystem currencies; shared tools; light cross-investment) and **V-14** —
competitive feature-mining research endorsed (tear down the big bots'
catalogs, filter the best, route through the conveyor). A four-question
structured-choice round was put to the owner same turn (ecosystem #2 identity
· currency model · cross-investment strength vs Q-0087's never-mandatory rule
· research scope) — answers route next. Also noted: he predicted the
emotion-pushback before it came (and once predicted an Opus 4.8 reply nearly
verbatim — the pattern-reader reading the pattern-machines).

## Brainstorm round 4: the owner-voice self-description + Q-0089

The owner shared a personal self-portrait (inventor identity since childhood —
Willy Wortel / Jimmy Neutron; "I see the code in my mind"; no-stress timing
philosophy; pattern-spotting as his core skill) — preserved **verbatim** in
`docs/owner/maintainer-working-profile.md` §6 (new). Embedded in it:
**Q-0089 directed** — the mandatory one-idea-per-session ender (routed:
CLAUDE.md session-workflow bullet · journal END checklist + QR · router §37,
verbatim). He also asked for an honest correction on "no other bot has such a
wide range of functions" — answered in-chat: breadth alone is matched/exceeded
(Red/Nadeko's plugin ecosystems, MEE6/Dyno suites, big game-economy bots);
the genuinely rare thing is the *system* (audited-governance config depth +
grounded AI answerability + the self-improving agent workflow run by a
non-coder). And he asked for a personality read as his standing new-model
test — delivered in-chat (not a doc matter beyond §6's facts).

💡 **Session idea (Q-0089's first execution): the owner's morning digest** —
a small caretaker/bot job that posts "what changed in your bot yesterday"
(merged-PR titles rendered player-friendly) to his Discord each morning. Why:
the owner's velocity (nonstop merges) is currently invisible except as GitHub
noise; a digest turns the network's output into a daily product moment for
its one operator — and later, reworded, into the public changelog channel for
servers. Small build (GitHub API → one embed), natural Stage-1 caretaker duty.

## Brainstorm round 3 (earlier): "can the bot test itself?" → idea captured

Owner idea (his own invention, articulated without coding background): every
command fired in sequence via temporary event-based actions + AI prompts
injected "at system level" per event. Captured + technically corrected into
[`docs/ideas/bot-self-test-walker-2026-06-10.md`](../docs/ideas/bot-self-test-walker-2026-06-10.md):
in-process synthetic invocation (bots ignore bot messages — Discord-level
self-driving is impossible), driver loop over the command-surface ledger
instead of event chaining, EventBus as assertion witness, governance
audience simulation (Q-0045) for tiered walks, scratch test guild +
lifecycle wipe, AI eval mode through the real pipeline using the Q-0086
keys, permanent owner-gated infrastructure rather than temporary. Routed:
ideas README + roadmap queue item 1 pointer (the walker is the checklist
session's automation follow-on and the Stage 1 caretaker's probe set).

## Context delta (reflection interview)

- **Route miss:** none serious — CLAUDE.md → current-state → ideas/README →
  the three capture docs was the right route and `ideas/README.md` correctly
  named `owner-vision-ideas-2026-06-08.md` as "start here".
- **Route excess:** current-state's ▶ header block is very dense for a
  non-implementation session; the ideas-lane reader mostly needs "what game/UX
  state shipped" which lives clearer in the Recently-shipped list.
- **Discovered by hand:** that `services/setup_ai_advisor.py` already exists
  (a schema-validated GuildSnapshot→plan advisor) — no orientation doc connects
  the "smart setup" idea space to that seam; the §2 dedup row now records it.
  Also: survival stats were *explicitly deferred* in brainstorm §6 with
  reserved columns — found only by grepping the brainstorm body.
- **Decisions made alone:** numbered the vision delta (V/AG/T scheme) and
  flagged tensions instead of silently merging the pets vision into the pets
  plan; deferred all promotion decisions to owner picks (routing rule).
- **Weak point:** the survival plan's contract-table numbers are placeholders
  by design (gate G2 owner-confirm) — don't read them as decided balance.
- **One change that would have helped:** a one-line "owner-voice capture
  template" in ideas/README (sections: owner-voice · dedup map · new items ·
  response · tensions · routing) — this session derived it; next drop should
  just follow it.

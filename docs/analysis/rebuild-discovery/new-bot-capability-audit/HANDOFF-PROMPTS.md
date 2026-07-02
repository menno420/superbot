# Handoff prompts — copy-paste to launch each planned session

> **Status:** `reference`. One ready-to-paste startup prompt per planned agent. Launch the four lanes in
> parallel (they're file-disjoint), then the Fable 5 capstone once they've landed. Each prompt is
> self-contained; the agent reads the shared contract from the repo.

---

## Lane A — Governance & Safety  → **Sonnet 5 ultracode**

```
You are Sonnet 5 running an ULTRACODE session in the menno420/superbot repo. You are Lane A of a 4-lane
parallel new-bot-capability-audit audit: measure whether the rebuild's §2 manifest grammar can express every
subsystem as tier-1/2 declarations (vs tier-3 escape-hatch code). This is the future-proofing gate before
the new-repo build — the spike measured 3 of 43 subsystems; you measure yours.

READ FIRST, in order:
1. docs/analysis/rebuild-discovery/new-bot-capability-audit/BRIEF.md         (the binding contract: method, output schema, guardrails, exit bar)
2. docs/analysis/rebuild-discovery/new-bot-capability-audit/PARTITION.md      (confirm your lane)
3. docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-A-governance.md  (your workspace — surface-unit inventories pre-filled, tier columns blank)
4. tools/grammar_spike/  — the method you replicate: spec.py (the §2 grammar), manifests/{karma,blackjack,server_logging}.py (worked examples), measure.py + RESULTS.md (tier semantics + output format)

YOUR SUBSYSTEMS: admin, server_management, moderation, automod, image_moderation, security, cleanup, role, channel, welcome, ticket

DO, per subsystem: (1) verify + complete its unit ledger against source (fix/add units, cite file:line) and fill BOTH tier columns (as-written / with-amendments) with a one-line rationale, covering all unit kinds (command/panel/setting/listener/event/store/game/help); (2) write the §2 manifest sketch (spike style) showing where each unit lands; (3) disposition every tier-3 — grammar-gap → propose/reuse an amendment G-<n>, OR legitimate escape hatch (with reason); (4) fit numbers (units total, tier-1/2 count, fit% as-written, fit% with-amendments); (5) flag structural patterns (esp. the setup/provisioning wait_for wizards).

ULTRACODE: you may fan out one sub-agent per subsystem, then synthesize + adversarially verify their tier-3 verdicts against source before writing your lane file.

RULES: READ-ONLY — no disbot/ edits, no runtime or new-repo code, docs only. Verify every tier-3 against shipped source and cite file:line (a wrong "needs tier-3" poisons the amendment list); mark "⚠ unverified" rather than assert. Stay in Lane A only.

OUTPUT: write the completed docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-A-governance.md and open a PR for it (file-disjoint from the other lanes). Follow the repo's session workflow (.claude/CLAUDE.md — born-red session card, PR, enders).
```

---

## Lane B — Economy & Character-sim  → **Opus 4.8 ultracode**

```
You are Opus 4.8 running an ULTRACODE session in the menno420/superbot repo. You are Lane B of a 4-lane
parallel new-bot-capability-audit audit: measure whether the rebuild's §2 manifest grammar can express every
subsystem as tier-1/2 declarations (vs tier-3 escape-hatch code). Future-proofing gate before the new-repo
build — the spike measured 3 of 43 subsystems; you measure yours. Your lane holds the DEEP-STATE
subsystems (mining/creature/farm) — a primary tier-3 pressure point; probe it hard.

READ FIRST, in order:
1. docs/analysis/rebuild-discovery/new-bot-capability-audit/BRIEF.md
2. docs/analysis/rebuild-discovery/new-bot-capability-audit/PARTITION.md
3. docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-B-economy.md
4. tools/grammar_spike/  (spec.py, manifests/*, measure.py, RESULTS.md — the method + tier semantics)

YOUR SUBSYSTEMS: economy, inventory, treasury, mining, fishing, creature, farm, xp, casino, four_twenty, counters

DO, per subsystem: (1) verify + complete its unit ledger against source (cite file:line) and fill BOTH tier columns with a one-line rationale, all unit kinds (command/panel/setting/listener/event/store/game/help); (2) write the §2 manifest sketch; (3) disposition every tier-3 → amendment G-<n> or documented escape hatch; (4) fit numbers; (5) flag structural patterns — especially deep persistent state (mining grid, creature battles, farm growth), transactional multi-write mutations, and leaderboards/records. Where the grammar can't hold persistent game state, say so precisely and propose the primitive family it would need.

ULTRACODE: fan out one sub-agent per subsystem, then synthesize + adversarially verify tier-3 verdicts against source before writing your lane file.

RULES: READ-ONLY — docs only, no disbot/ or new-repo code. Verify tier-3 against source, cite file:line, "⚠ unverified" when unsure. Stay in Lane B.

OUTPUT: write docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-B-economy.md and open a PR. Follow the repo session workflow (.claude/CLAUDE.md).
```

---

## Lane C — Games & Community  → **Opus 4.8 ultracode**

```
You are Opus 4.8 running an ULTRACODE session in the menno420/superbot repo. You are Lane C of a 4-lane
parallel new-bot-capability-audit audit. This is the HARDEST grammar-fit lane: blackjack measured only 44% in
the spike, and your lane is the stateful game loops (turn/round state machines, wait_for interaction loops,
timers). It most directly tests whether the grammar needs a GAME-STATE primitive family — likely a new
amendment. blackjack + karma already have spike manifests; calibrate against them.

READ FIRST, in order:
1. docs/analysis/rebuild-discovery/new-bot-capability-audit/BRIEF.md
2. docs/analysis/rebuild-discovery/new-bot-capability-audit/PARTITION.md
3. docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-C-games.md
4. tools/grammar_spike/  (spec.py, manifests/{blackjack,karma,server_logging}.py, measure.py, RESULTS.md)

YOUR SUBSYSTEMS: games, blackjack, deathmatch, rps_tournament, counting, chain, leaderboard, community, community_spotlight, karma

DO, per subsystem: (1) verify + complete its unit ledger (cite file:line), fill BOTH tier columns with a one-line rationale, all unit kinds; (2) §2 manifest sketch; (3) disposition every tier-3 → amendment or escape hatch; (4) fit numbers; (5) flag structural patterns — especially stateful game loops, wait_for loops, and timers. Be explicit about whether the grammar (with amendments) can express a full game turn/round loop or whether that is an irreducible tier-3 handler — this is the lane's central finding.

ULTRACODE: fan out one sub-agent per subsystem, then synthesize + adversarially verify against source.

RULES: READ-ONLY — docs only. Verify tier-3 against source, cite file:line, "⚠ unverified" when unsure. Stay in Lane C.

OUTPUT: write docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-C-games.md and open a PR. Follow the repo session workflow (.claude/CLAUDE.md).
```

---

## Lane D — Knowledge, AI & Platform  → **Codex / deep-research**

```
You are auditing Lane D of a 4-lane parallel new-bot-capability-audit audit in the menno420/superbot repo:
measure whether the rebuild's §2 manifest grammar can express every subsystem as tier-1/2 declarations (vs
tier-3 escape-hatch code) — the future-proofing gate before the new-repo build. The spike measured 3 of 43
subsystems; you measure yours. Your lane mixes the easy generated-panel payoff (logging ~97%, settings)
with the NOVEL AI/knowledge-domain shape the spike never touched — that is where your value is highest.

READ FIRST, in order:
1. docs/analysis/rebuild-discovery/new-bot-capability-audit/BRIEF.md         (the binding contract — follow its schema exactly so your output composes with the other lanes)
2. docs/analysis/rebuild-discovery/new-bot-capability-audit/PARTITION.md
3. docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-D-knowledge-platform.md
4. tools/grammar_spike/  (spec.py = the §2 grammar; manifests/server_logging.py = the closest worked example; measure.py + RESULTS.md = tier semantics + output format)

YOUR SUBSYSTEMS: ai, btd6, project_moon, help, settings, logging, diagnostic, ux_lab, utility, general, proof_channel

DO, per subsystem: (1) verify + complete its unit ledger against source (cite file:line), fill BOTH tier columns (as-written / with-amendments) with a one-line rationale, all unit kinds (command/panel/setting/listener/event/store/game/help); (2) write the §2 manifest sketch; (3) disposition every tier-3 → amendment G-<n> or documented escape hatch; (4) fit numbers; (5) flag structural patterns. For the AI/knowledge subsystems, assess whether a KnowledgeDomainSpec (commands + data sources + context builder + eval suite + diagnostics) is expressible declaratively or needs a new family. A deep-research agent may add external patterns (how comparable bots structure knowledge-domain/config surfaces) as a note in findings/ — clearly labeled as external, not repo source.

RULES: READ-ONLY — docs only, no runtime/new-repo code. Verify every tier-3 against shipped source and cite file:line (the earlier Codex maps mis-read source 4× — do not repeat that); mark "⚠ unverified" rather than assert. Stay in Lane D.

OUTPUT: write your completed lane file docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-D-knowledge-platform.md (and any external-research note under findings/), then open a PR.
```

---

## Lane E — Plans & Ideas (Axis 2)  → **Codex / Opus**

```
You are auditing Lane E — Plans & Ideas (Axis 2) — of the new-bot capability audit in menno420/superbot.
Goal: reconsider everything PLANNED or IDEATED for the new bot — does it still belong, is it optimal, how
to improve it — so the forward surface is as considered as the shipped one.

READ FIRST:
1. docs/analysis/rebuild-discovery/new-bot-capability-audit/BRIEF.md   (the mandate + per-capability schema)
2. docs/analysis/rebuild-discovery/new-bot-capability-audit/PARTITION.md   (your lane)
3. docs/planning/*.md (active plans — SKIP any badged `historical`) + docs/ideas/*.md + docs/ideas/README.md + docs/roadmap.md

DO, per plan/idea meant for the new bot: (1) reconsider — keep / improve / merge / drop / redesign; (2) express its target capability in the §2 grammar (tools/grammar_spike/spec.py); (3) note whether an Axis-1 subsystem already covers it (avoid double-counting with Lanes A–D); (4) deep-reason optimality + propose the better form. Output a forward-capability ledger: what the new bot should ADD that isn't shipped, each with its optimal form and why.

RULES: READ-ONLY, docs only. Verify against source; cite the plan/idea file. Do not re-audit shipped subsystems (that's A–D). Stay in Lane E.

OUTPUT: write docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-E-plans-ideas.md and open a PR. Follow the repo session workflow (.claude/CLAUDE.md).
```

---

## Lane F — Ecosystem benchmark (Axis 3)  → **deep-research**

```
You are running Lane F — Ecosystem benchmark (Axis 3) — of the new-bot capability audit in
menno420/superbot. Goal: review our bot against KNOWN Discord bots and catalog what THEY do that WE
don't — a documented known-options corpus for the next bot. This is NOT a build list; the bar is "known
and clearly documented" so a future session pulls from a rich menu instead of rediscovering.

READ FIRST:
1. docs/analysis/rebuild-discovery/new-bot-capability-audit/BRIEF.md   (the mandate — Axis 3)
2. docs/analysis/rebuild-discovery/new-bot-capability-audit/ground-truth/command-surface.json  (our 271 commands)
3. docs/analysis/rebuild-discovery/new-bot-capability-audit/PARTITION.md  (our domains) + the Axis-1 lane files as they land (our current capabilities per domain)

DO: for each of our domains (moderation/safety, economy/currency, games, leveling/XP, tickets, welcome/
greeter, reaction-roles, logging, music/voice, utility, knowledge/AI, fun/social), web-research the
leading bots in that domain — MEE6, Carl-bot, Dyno, Dank Memer, Ticket Tool, YAGPDB, Arcane, Tatsu,
ProBot, Mudae, Sapphire, and domain-fit others. Catalog their feature/command sets, diff against ours,
and document EVERY capability they have that we don't: what it is · which bot(s) · would it fit our
declarative §2 design · fit verdict (**strong fit** / **maybe** / **deliberate omission** + reason).
CITE sources (URLs/docs). Be thorough — "a lot is still missing"; find it.

ALSO — the OUTPERFORM bar (owner's standard rule): for the capabilities we DO share with these bots,
identify the **best-in-class** implementation (which bot does it best and how) so ours can be specced to
BEAT it, not just match it. Note the concrete edge to target (speed, UX, depth, reliability). This feeds
the build plan's per-capability "outperform target."

RULES: this is a KNOWN-OPTIONS corpus — nothing here is auto-scheduled to build. Label external facts as
external (not repo source). Be honest about deliberate omissions and why.

OUTPUT: write docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/ecosystem-benchmark.md as a
filterable capability-gap catalog (group by domain; sortable by fit verdict) and open a PR. Make it rich
— the explicit goal is a repo overflowing with useful data the next bot can use.
```

---

## Lane G — Foundations & Runtime Skeleton, L0 (Axis 1)  → **Opus 4.8 / Codex**

```
You are auditing Lane G — Foundations & Runtime Skeleton (L0) — of the new-bot capability audit in
menno420/superbot. This is the SUBSTRATE under all 43 subsystems and the FIRST thing the new bot builds
(foundations first) — the highest-leverage lane. Owner directive: "we already do this, but there's room
for improvement" — so audit, reconsider, and design the OPTIMAL foundation.

READ FIRST:
1. docs/analysis/rebuild-discovery/new-bot-capability-audit/BRIEF.md   (mandate + per-capability schema)
2. docs/analysis/rebuild-discovery/new-bot-capability-audit/PARTITION.md   (Lane G)
3. disbot/bot1.py (the bot skeleton + extension loader) · disbot/core/ (kernel/runtime) · disbot/utils/ (helpers) · docs/helper-policy.md · docs/architecture.md

DO — audit + reconsider + optimize + benchmark the L0 substrate:
- main.py / bootstrap: is it LEAN + functional? what belongs in it vs. what should be extracted.
- Dynamic cog discovery + auto-load: the skeleton must find and load EVERY cog dynamically with NO hardcoded initial-extensions list. Audit how we do it today, reconsider, and design the optimal auto-discovery (folder-scan / entry-point / manifest-driven) — with failure isolation (one bad cog can't down the bot) and load-order/dependency handling.
- Env + config: loading, validation, secrets, per-environment — the config lanes' foundation.
- Helper / util architecture: every applicable function in its PROPER helper/util home (align to docs/helper-policy.md); flag mis-homed functions and the ideal layering.
- Kernel / runtime: the engine the §2 manifest generates into.
Benchmark against best-in-class bot skeletons (discord.py cog-loader patterns, large open-source bots). For each foundation piece: reconsider verdict + optimal form (simulated where feasible) + production-grade done-definition + outperform target.

RULES: READ-ONLY, docs only, no runtime/new-repo code. Cite file:line; verify vs source; "⚠ unverified" when unsure.

OUTPUT: write docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-G-foundations.md and open a PR. This lane feeds the build plan's L0 layer directly — it's the first thing the first build session picks up.
```

---

## Capstone — final review  → **Fable 5 (ultracode or normal)**

```
You are Fable 5 running the CAPSTONE review of the new-bot-capability-audit audit in the menno420/superbot
repo. Four independent lanes (2 Opus + 1 Sonnet ultracode + Codex/deep-research) have measured whether the
rebuild's §2 manifest grammar can express all 43 subsystems as tier-1/2 declarations. Turn their findings
into one durable go/no-go — this is the gate between "planning/discovery" and "creating the new repo."

READ FIRST:
1. docs/analysis/rebuild-discovery/new-bot-capability-audit/FINAL-REVIEW-HANDOFF.md   (your full spec — follow it)
2. docs/analysis/rebuild-discovery/new-bot-capability-audit/BRIEF.md
3. All four docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-*.md + anything in findings/
4. tools/grammar_spike/RESULTS.md  (the 3-subsystem baseline you extend)

DO: (1) VERIFY before trusting — spot-check the highest-leverage tier-3 verdicts against source; do not average lane numbers blindly (Q-0120 — the spike caught cross-agent maps mis-reading source 4×); down-weight "⚠ unverified" rows and re-derive disputed ones. (2) Compute the measured all-43 tier-1/2 fit (as-written vs with-amendments; 43 rows + overall; note if the mean is carried by high-fit CRUD subsystems while the stateful cluster drags). (3) Consolidate the amendment list (extend G-1…G-6, dedup; mark each soft-spec-note vs structural-new-family). (4) Answer each structural danger zone (stateful games / gateway listeners / wait_for wizards / scheduled loops / voice) — expressible, documented escape hatch, or needs a new family. (5) Per-subsystem preserve/redesign/drop disposition (fold with ../codex-preserve-map-synthesis-2026-07-02.md).

RULE THE VERDICT: GO / GO-with-amendments / NO-GO — with evidence, never a soft "looks fine." A subsystem class with no clean grammar answer is a NO-GO — that is exactly the "needs re-rebuilding in a year" failure this whole pass exists to catch.

THEN ASSEMBLE THE UNIFIED BUILD PLAN (Lanes E + F too) — the owner's ultimate ask: the next bot is built from ONE comprehensive plan, in a logical order, each layer production-grade before the next, every function outperforming the best equivalent in any other bot. Fold Axis-1 (keep/improve/merge/drop), Axis-2 (Lane E, planned), and Axis-3 (Lane F, ecosystem strong-fit) into: (1) the capability corpus (each item's disposition + deferred known-options); (2) the BUILD ORDER — dependency layers, foundations first: L0 foundations (kernel/grammar/state/config/audit/permission) → L1 core bot+server management (setup, roles, channels, moderation, logging) → L2+ features; each item lists its dependencies, nothing above an unbuilt dependency; (3) per-capability acceptance — the production-grade "done" definition (which parity/ golden + tests it passes) AND the outperform target (the best-in-class competitor from Lane F and how ours beats it).

OUTPUT: findings/FINAL-REVIEW.md (grammar verdict + aggregated fit table + amendments + dispositions) AND findings/NEW-BOT-BUILD-PLAN.md (the corpus + dependency-layered build order + per-capability done-definition + outperform target). Open the design-spec amendment PR (or a plan) the verdict implies, plus the owner "what approval means" checklist. READ-ONLY on runtime; docs only.
```

---

## Launch order

1. Fire **Lanes A–D + G in parallel** (Axis-1: A–D are file-disjoint by subsystem; G reads the
   foundation across `bot1.py`/`core`/`utils` — disjoint from the subsystem cogs → clean PRs).
2. Fire **Lane E** (Axis 2 — plans/ideas) and **Lane F** (Axis 3 — ecosystem benchmark) alongside; they
   reference the A–D/G output and can refine as it lands (or run just after).
3. Once all seven land, fire the **Fable 5 capstone** — it reads all lanes + findings/ and produces the
   grammar go/no-go + the **unified, dependency-ordered, best-in-class build plan**.

The seven lanes map to your fleet: **2 Opus 4.8** (B, C — or move one to **G**, the highest-leverage
foundation lane) · **1 Sonnet 5** (A) · **a few Codex / deep-research** (D, E, F, G). Each lane's
amendments, optimality findings, ecosystem gaps, and L0 foundation design are the capstone's raw material.

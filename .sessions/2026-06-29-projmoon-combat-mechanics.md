# 2026-06-29 — Project Moon (Limbus) combat-mechanics knowledge layer

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1549](https://github.com/menno420/superbot/pull/1549) — Project Moon (Limbus): combat-mechanics knowledge layer.
**Branch:** `claude/project-moon-status-smaxm3`
**Run type:** manual

## What this run did
Owner asked in-chat to **check how the Project Moon work is going and continue it**, with a Project
Moon community member's screenshot naming the missing "majority" as **clashing · IDs and passives ·
speed · enemy stats and passives**. That maps exactly to the plan's documented **▶ Next = Slice A
item 1** (the combat layer that the structural/lore PRs #1453…#1470 deliberately left out).

Shipped the **stable, hand-authorable, correct half** of Slice A item 1 — the combat **rules**:

- **New `mechanic` entity kind** (`disbot/data/projmoon/limbus/mechanics.json`, 13 entries, each with
  a `category` group): Clash · Coin (heads/Sanity) · Speed · Sanity · Stagger · Damage Resistance
  (Fatal→Ineffective) · Resonance · Skills & replacement · Defensive skills (Guard/Evade/Counter) ·
  Identity (rarity 0/00/000) · Passives & support passives · E.G.O/Corrosion. Provenance-tagged,
  conservative "verify-at-ingest" summaries — **no fragile per-unit numbers** (those are the deferred
  numeric tail).
- **Data service** (`projmoon_data_service.py`): registered the file + `Mechanics` label + the
  `category` extra. No validation change (category is a passthrough extra like `color`/`rank`).
- **Browse surface**: `!pm mechanic <name>` / `!pm mechanics` (+ `combat` alias) and the auto-flowing
  Mechanics button on `/pm`; kind list shows the category suffix, detail card shows a **Group** field.
- **AI grounding**: per-entity matches flow through the **already-wired**
  `projmoon_context_service.build()` seam automatically; added a `"combat mechanics"` roster trigger +
  a `(combat mechanic — <group>)` body enrichment. **Router / NL-stage / faithfulness-guard / BTD6
  path all unchanged.**
- **Tests** (offline): +3 data-service, +4 context-service, +3 cog, +1 grounding (mechanic common-word
  names never trigger a false refusal). 177 targeted projmoon/help/ledger tests green; full CI mirror
  (`check_quality.py --full`) green (13038 passed); `check_architecture --mode strict` 0 errors.
- **Workflow guard** (friction → guard, Q-0194): added a web-export regen step to the `/session-close`
  skill Step 4 (see below).

## Decisions recorded
No new owner *decision* (owner-directed continuation of the Q-0192 plan). Engineering calls made alone,
all consistent with existing discipline (no router entry needed):
- **Mechanics rules now, exact per-unit numbers deferred.** Hand-committing per-Identity / per-enemy
  HP / speed values / coin power would risk *ungrounded numbers* — the StaticData ingest lane owns
  those (ADR-006 groundedness). The rules are patch-stable and safe to author with provenance.
- **Routing keyword list left unchanged.** Mechanic words (`clash`/`speed`/`sanity`) are ordinary
  English, so — exactly like the Sins — they ground via **co-occurrence** with a distinctive token,
  never by routing bare. This preserves the over-route discipline the domain was built on.

## Left open / next session
- The **numeric tail of Slice A item 1** — exact per-Identity / per-enemy stat numbers via the
  **StaticData** ingest lane (not by hand).
- The live **Q-0086 runtime walk** (owner) — confirm a real Limbus mechanics Q&A grounds + reads well
  on both providers; spot-check "how does clashing work?" / "what is speed in Limbus?".
- Then **Slice B** — extract the shared `KnowledgeDomain` seam from BTD6 + Limbus.

## Context delta
- **Needed but not pointed to:** the committed **web-export artifacts** (`dashboard/data/dashboard.json`,
  `botsite/data/site.json`, `botsite/site/data.js`) drift whenever a session adds a command/alias or a
  `.sessions/` log, and must be regenerated with `python3.10 scripts/export_dashboard_data.py`. Nothing
  in orientation or `/session-close` routed me there — I found it via the failing
  `test_check_generated_artifacts_fresh` and the previous session log (which hit the same class). Now
  fixed (skill step below).
- **Pointed to but didn't need:** CodeGraph symbol tools — this was a contained change over a
  well-mapped vertical, so `context_map.py` + grep + reading the existing projmoon files sufficed
  (consistent with the "contained change → context_map + grep" guidance; the graph was unnecessary).
- **Discovered by hand:** `projmoon_context_service._normalise` replaces every non-word run with a
  space, so a canonical/alias containing dots (`e.g.o`) **never matches** in grounding — clean aliases
  (`ego`) are required. Only visible by reading the normaliser. Worth a one-line note in the ai folio's
  "Adding a knowledge domain" recipe on the next REVIEW sweep.
- **Decisions made alone:** the two engineering calls under "Decisions recorded" (mechanics-rules-now /
  numbers-deferred; routing-keywords-unchanged).
- **Flagged for maintainer (known limits):** (1) bare-mechanic questions with no distinctive token
  don't route to grounding (the Q-0089 carryover idea below addresses it); (2) the mechanic
  descriptions are hand-authored "verify-at-ingest" summaries — accurate to my knowledge of the game,
  but the Q-0086 walk should spot-check a couple for currency (the game rebalances).
- **🛠 Friction → guard:** the web-export regen gap (a recurring drift — #1542 and #1549 both hit it,
  and `/session-close` Step 4 runs only `--check-only`, which skips the freshness pytest, so it
  surfaces only in CI). **Guard shipped:** a regen step added to `/session-close` SKILL.md Step 4 (a
  skill is workflow guidance — free to ship, not owner-gated config). The enforcing layer (the
  freshness pytest) already existed; this closes the *knowledge* gap so the next session regenerates
  before the first CI run instead of debugging a red.

## 💡 Session idea (Q-0089)
**Idea:** conversational **domain-context carryover** for knowledge domains — a short-lived
per-(channel, author) memory so a bare follow-up ("how does clashing work?") inherits the last-routed
domain (BTD6 / Limbus) and grounds, entity-resolution-gated + fast-decaying so it never re-introduces
over-routing. **Why:** it closes the one gap the mechanics layer can't reach on its own (natural
multi-turn "and how does X work?" follow-ups), needs no new data, and generalises the BTD6 single-turn
carryover (#668) into a domain-agnostic capability that folds into the Slice B `KnowledgeDomain` seam.
Dedup-grepped `docs/ideas/` (no existing carryover/stickiness idea). Idea file:
[`../docs/ideas/knowledge-domain-conversation-carryover-2026-06-29.md`](../docs/ideas/knowledge-domain-conversation-carryover-2026-06-29.md)
+ README index entry.

## ⟲ Previous-session review (Q-0102)
The previous session (2026-06-29, **Farm leaderboard provider**, #1542) did genuinely strong work — its
real value was the *honest scope boundary* it documented (only Farm of the four named games has a
persisted rankable stat; the other three need a migration first), which stops a later session
re-chasing them as turn-key wins. **What it did well that this run reused:** its own session log
explicitly recorded hitting the generated-artifact drift class and regenerating via
`export_dashboard_data.py` — that note is exactly what let me recognise my identical failure fast
instead of debugging from scratch. **System improvement it surfaces (and I acted on):** that the drift
is *recurring across sessions* and that `/session-close` doesn't catch it (its Step-4 `--check-only`
skips the freshness pytest) is the textbook friction→guard signal — so this run added the regen step to
the close-out skill, turning a twice-repeated manual recovery into a checklist step. (No filler: the
previous session was solid; the only improvement was the cross-session-recurring guard, now shipped.)

## Doc audit (Q-0104)
Durable homes updated: the **data README** (mechanics row + scope/numbers-deferred note), the **plan**
(Slice A item-1 ▶ Progress note, PR #1549), **S1-bot.md** (Project Moon bullet + re-pointed ▶ Next),
the **hub current-state.md** S1 row (fix-on-sight span update), the **ai-folio gotcha** noted in the
context delta for the next REVIEW. `current-state.md` § Recently-shipped untouched (PR #1549 not yet
merged — the reconciliation routine records it; recon lane at #1530). No new owner *decision* (router
untouched). No bug-book change (no bug surfaced). Web-export artifacts regenerated. Claim file deleted
at close.

## 📤 Run report
- **Did:** shipped the Project Moon (Limbus) combat-mechanics rules layer — the clashing/speed/
  IDs+passives/enemy-stat concepts a community member flagged as missing — as a new `mechanic` entity
  kind, browsable + AI-grounded, with the exact per-unit numbers deferred to the StaticData lane.
  · **Outcome:** shipped (PR #1549, auto-merges on green)
- **Shipped:** PR #1549 — `mechanics.json` (13 mechanics) + data-service/browse/cog/context wiring +
  11 tests; `/session-close` web-export-regen guard; data README + plan + S1 + hub-state docs;
  regenerated `dashboard.json`/`site.json`/`data.js`.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** the live **Q-0086 runtime walk** when convenient — ask the bot a Limbus
  mechanics question (e.g. "how does clashing work in limbus?", "what is speed?") and confirm it grounds
  + reads well on both providers. No deploy step (auto-deploys on merge); no data/seed step (read-only).
- **⚑ Self-initiated:** none — owner-directed continuation of the Q-0192 Project Moon plan (Slice A
  item 1). (The Q-0089 carryover idea is *captured*, not built.)
- **↪ Next:** the **numeric tail of Slice A item 1** (StaticData exact per-Identity/per-enemy stat
  numbers via the ingest lane, *not* hand-committed) + the Q-0086 live walk; then **Slice B** = extract
  the shared `KnowledgeDomain` seam from BTD6 + Limbus.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (PR #1549 auto-merges on green CI after this push) |
| CI-red rounds | 1 (the born-red gate, by design; local `check_quality --full` was green before the complete push) |
| Repo-rule trips | 1 (a black line-wrap on one new line — caught + fixed locally, never reached CI) |
| New ideas contributed | 1 (domain-context carryover, Q-0089) |
| Ideas groomed | 1 (advanced the Project Moon plan: Slice A item 1 rules-half shipped) |

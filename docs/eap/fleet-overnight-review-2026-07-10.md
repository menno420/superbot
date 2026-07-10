# Fleet overnight review — night of 2026-07-09 → 2026-07-10 (all 13 repos)

> **Status:** `reference` — owner-directed morning-after review of the fleet's overnight
> autonomous work (gen-1 wind-down → gen-2 launch night). Method: superbot reviewed inline
> by the coordinating session (shift cards A–E2, recon pass #1922, live PR state); the 12
> sibling repos shallow-cloned and each reviewed by an independent read-only subagent
> (activity, spot-checked claims, session-ender compliance, anomalies). Subagent findings
> are evidence-cited but not themselves line-audited — treat per-repo detail as
> high-confidence secondary, and the flagged items as verified (each was ground-truthed).
> Owner ask + chat delivery: session `2026-07-10-fleet-overnight-review` (PR #1931).

## Headline verdict

**The night went well — unusually well for the amount of surface in motion.** The fleet
executed a coordinated gen-1 wind-down → gen-2 launch across 13 repos: fleet-manager's
launch record claims 116 PRs merged fleet-wide 00:00–06:15Z with zero stuck (spot-verified
on 2 repos; plausible everywhere reviewed), and this review found **zero open PRs, zero
abandoned sessions-with-work, and empty claims directories in every repo**. Session-ender
compliance is near-universal. The failures found are small, mostly self-flagged by the
lanes themselves, and none is a runtime/production defect.

## Per-repo one-liners

| Repo | Night in one line | Verdict |
|---|---|---|
| superbot (hub) | Shift plan A–E2 (#1917–#1924) + 41st recon (#1922) + EAP corrections (#1926); all enders, all checkers green | ✅ strong |
| superbot-next | ~20 PRs up the testing ladder (bands 3–5), live `!worldcard` crash fixed w/ regression test, kit → v1.6.0 | ✅ strong |
| substrate-kit | ~35 PRs, releases v1.4→v1.7.0, real bug fixes, bench run-4 honestly reported **against** the kit | ✅ strong |
| superbot-games | Full lifecycle in one night (seed #1 → wind-down #15) + night-prep CI fix #16; 73+48 tests pass locally | ✅ good, 1 finding |
| websites | Gen-1 wind-down + gen-2 boot; ORDER 005 `/queue`+`/environments` shipped, live-verified rendering real data | ✅ good, 1 finding |
| trading-strategy | P1→P5-prep complete; holdout seal enforced in code+CI; headline honestly negative; waits on owner unlock | ✅ exemplary rigor |
| fleet-manager | 18 PRs incl. gen-2 blueprint→binding, launch record (self-verifying, corrected its own undercount) | ✅ good, 1 miss |
| venture-lab | Seed → two sellable buyer zips + listing copy in one night; 13/13 tests pass; revenue steps owner-gated | ✅ strong |
| pokemon-mod-lab | Born tonight: pret/pokeemerald + agbcc CI + 12 QoL patches w/ proof bundles; 19/19 CI green; PARKED on owner picks | ✅ strong |
| gba-homebrew | Born tonight: toolchain + original game "Lumen Drift" to SCOPE-COMPLETE; headless-mGBA replay proofs | ✅ strong |
| codetool-lab ×3 | All three wound down complete; every test-count claim exactly reproducible; no fabrication found | ✅ complete |

## Session-ender compliance

Near-universal. Everywhere reviewed: session cards `complete` with 💡 idea + ⟲
previous-session review + docs audit, claims released, status heartbeats overwritten as
the deliberate last step, PRs all terminal. Exceptions found (all small):

1. **superbot "session C"** — died overnight leaving no card, claim, or tombstone (branch
   created + deleted). Its sibling (shift D, #1920) already flagged it in writing; it is
   the born-red-card-first rule's canonical justification, not a new rule gap.
2. **fleet-manager PRs #13 and #15** have no session card (every other post-adoption PR
   does).
3. **superbot-next band sessions** mostly skip `.sessions/` cards, treating testing-report
   rows + heartbeat as their record, and repeatedly settle the heartbeat late as "status
   debt" (#94, #98) — a convention divergence its own cards flag for gen-2.
4. **trading-strategy** opens cards `complete`-scoped rather than born-red — a documented,
   reasoned workaround for its gate, not silent drift.
5. Cosmetic: game-lab + websites gen-2 cards use "withheld/lane default" Model lines.

## Findings that need action (ranked)

1. **Fleet manifest re-stamp missed (fleet-manager).** `docs/eap/fleet-manifest.md` (the
   manager's sole-writer file, here in superbot) is frozen at the 07-09 pre-launch evening
   state — venture-lab's row still says "Project boot pending owner clicks" while the lane
   shipped two products; most rows still carry executed "▶ tonight" plans. Confirmed live.
   Exactly what shift E's new `check_manifest_freshness.py` (#1923) flagged. **Action:
   manager rollup re-stamps the whole manifest.**
2. **superbot-games CI coverage overstated.** Night-prep #16 added pytest to the substrate
   gate but only `tests/` (mining 73); exploration's 48 tests in `games/exploration/tests/`
   are still outside CI while the card implies full coverage. One-line workflow fix.
3. **websites status asserts a wrong fact about the deployed token.** Status/ORDER 007
   claim the control-plane runs tokenless; the live board renders authenticated-only data
   and PR #6 (07-09) recorded the PAT being set. The standing PAT owner-ask is likely
   stale → could send the owner to redo done work. Also: the PAT ask never landed in
   `docs/owner/OWNER-ACTIONS.md` (the self-declared canonical list). Reconcile session.
4. **venture-lab has no self-landable merge path** (classifier walls agent self-merge;
   auto-merge can't arm without a required check) — contradicts its own binding
   convention; every unattended PR there strands until the owner fixes settings.
   Related classifier/auto-merge walls seen in substrate-kit + trading-strategy.
5. **codetool labs contradict each other on the release wall**: opus4.8 *proved* the
   Actions `workflow_dispatch` release path works (2 live releases); fable5 documents the
   same route "closed permanently"; sonnet5's never fired. Gen-2 blueprints should
   reconcile before fable5's "do not re-attempt" steers its successor wrong.
6. **Model-comparison contamination (codetool experiment)**: coordinator + wind-down
   seats ran claude-fable-5 in at least the sonnet5 (and likely fable5) lanes — only
   sonnet5 discloses it loudly. Cross-arm comparisons should score builder seats only.
7. **codetool-lab-fable5 hygiene**: 11 committed `.pyc`/`__pycache__` files, no
   `.gitignore` — the one *unflagged* defect found anywhere tonight.
8. **superbot-games `docs/current-state.md`** still lists merged PRs as in-flight —
   visible drift for the gen-2 boot to trip on.

## Consolidated owner-action queue (cross-fleet, deduplicated)

The lanes are largely **parked on owner clicks, not on agent capacity**:

- **HOT:** substrate-kit F-5 wording ruling (though bench run-4 made it immaterial for
  that row); the kit-doesn't-help-continuity bench finding deserves a read.
- **trading-strategy:** the pre-registered **holdout unlock ORDER** — the lab's only
  remaining step.
- **Concept picks:** pokemon-mod-lab (QoL+ recommended) + gba-homebrew (Lumen Drift is
  scope-complete) — both game lanes are otherwise idle.
- **superbot-next:** corpus-red disposition ruling (flag 13); create `superbot-plugin-hello`
  repo (agents 403); relax require-up-to-date merge rule.
- **Repo settings sweep** (one sitting): required checks (pokemon "ROM builds",
  venture-lab `substrate-gate`), "Allow auto-merge" (trading-strategy, venture-lab),
  merged-branch cleanup (agents 403 on ref deletes, fleet-wide).
- **Wake triggers:** websites/fleet 4-hourly coordinator trigger — without it the gen-2
  fleet is self-terminal after each burst.
- venture-lab first-revenue clicks (publish the two zips; Stripe test keys).

## What the night proves (review judgment)

- **The self-auditing loop works end-to-end**: a guard shipped mid-band forced the next
  session to dogfood it (#1922's telemetry row); a checker shipped at 03:43 (#1923)
  correctly flagged real staleness its own fleet confirmed by morning; fleet-manager's
  verification record produced corrections a worker session independently re-verified and
  applied (#1926). Drift is being *found by machinery*, not by the owner.
- **The honesty culture is real, not performative**: the strongest deliverables of the
  night are negative results stated as headlines (trading's "the headline of this program
  is negative"; the kit's own bench FAIL in its release notes; superbot-next marking model
  attribution "cannot determine" for 30/38 commits).
- **Main residual risk is attestation depth**: most cross-repo claims ("116 PRs, zero
  stuck", replay counts, bench arm identities) are self- or sibling-attested; this review
  spot-verified samples, not the census. The duplicate-ORDER incident (kit twin PRs
  #50/#51) and the venture-lab boot cross-wire show lane-collision/routing risk is real at
  this velocity — both were converted into guards the same night, which is the system
  working, but they were caught by luck-adjacent review, not prevention.

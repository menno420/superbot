# Session — round-3 dispatch, part 4f: the two games founding packages

> **Status:** `complete`
> **Run type:** owner-directed ("help me get the 2 games projects running, step by step
> instructions like before") · same live dispatch chat (parts 4/4b/4c/4d/4e merged)
> **Model/time:** fable-5 · 2026-07-10 ~22:1xZ → ~22:2xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1966) · PR #1968.

## What is about to happen

Draft the two games founding packages on the gen-3 standard (continuous Q-0265 +
volume-first Q-0266 + Q-0267 shape): **World Games** (gen-2 single seat on
`superbot-games`) and **Idle Engine** (new repo `superbot-idle`, copilot-seeded).

## What happened

- **Ground truth read at HEAD before drafting (Q-0120):** `superbot-games`
  `docs/gen2-custom-instructions-exploration.md` (its KEEP/DROP/ADD lines — heartbeat-
  before-work, walking skeleton, merge-authority ladder, done-when-never-parks — are
  folded into both packages), `docs/retro/next-boot-mining-2026-07-09.md` (the
  merge-wall classifier denials verbatim → the packages carry the arm→one-attempt→
  park+⚑ ladder instead of pretending self-merge is clean), `docs/lanes.md` (retired
  for gen-2 via a banner, not deletion), fleet-manager `environments/` (python-lab
  archetype covers both seats).
- **`round3-founding-package-games-world-2026-07-10.md`**: §0 clicks (env + Project +
  pastes; old lane Projects archivable), §1 instructions (~3.9k chars: world-ecosystem
  identity, gen-1 integrity floor kept — deterministic core / sim-pinned balance / no
  pay-to-win / bounded-menu AI DM — theme-readiness, merge ladder, continuous +
  volume-first), §2 brief (unification slice AS walking skeleton; failsafe
  "superbot-games failsafe wake" @ `15 */2 * * *`; queued: kit v1.2.0→v1.7.0, fishing
  skeleton on mining's substrate, unified inventory contract, theme-slot audit), §4
  verification + red flags.
- **`round3-founding-package-games-idle-2026-07-10.md`**: §0 clicks in seed-recipe
  order (create EMPTY repo → copilot seeds → settings → env → Project), §1
  instructions (~3.8k chars: CORE/SKIN split as the repo's four-clause hard rule,
  theme-gate honesty bar, pre-registered sim-routed economy numbers, plugin-native),
  §2 brief (ORDER 000 = skeleton that proves the merge path AND the core/skin seam —
  nouns from egg-farm.yaml; failsafe "superbot-idle failsafe wake" @ `45 */2 * * *`;
  queued: schema v1 + gate, prestige, two more themes, economy design doc, setup-code
  format v1), §4 verification + red flags (nouns-in-code ORDER 000 is the named
  failure).
- **Homing + state:** planning README rows for both; runbook §4 queue item ticked
  done, §3.7 games entry extended (packages drafted, §6.2 relay demoted to
  cross-check).

## ⚑ Self-initiated

- Failsafe cron minutes `15`/`45` (off the `0 */2` lane standard) so the two new seats
  never pile onto the fleet's even-hour wake spike — deviation flagged here per the
  gen-3 §2 stagger rule.
- The idle seat's sim-routing rule (economy numbers pre-registered + ⚑-routed to the
  Simulator via the manager) — composed from Q-0264 + the trading lane's
  pre-registration discipline; not owner-stated for games, vetoable at calibration.
- Seat B repo name `superbot-idle` (owner overrides at creation).

## 💡 Session idea

**A "founding-package linter"** (`scripts/check_founding_package.py`): the six packages
now share a de-facto schema (§0 clicks / §1 ≤7,500 chars / §2 with ARM-ROUTINE +
worker-seat fallback + calibration ask / §4 red flags). A ~80-line checker that
verifies a new package has every required block (and §1 under the paste cap — I
hand-counted chars again this session) turns the gen-3 standard §2 from prose into an
enforced template, per "enforce, don't exhort" (Q-0132). Dedup: not in ideas/ or the
roadmap; natural home = the checker suite next to `check_plan_homing.py`.

## ⟲ Previous-session review

Part 4e captured Q-0267 fast and its §6.2 block converted the manager's task cleanly —
but it left "founding packages after the conformed mapping" as the default sequencing,
and the owner's very next message was "get them running now": the mapping-then-package
order was MY caution, not his intent (Q-0240 says decide-and-flag, and 4e had already
decided everything the packages needed). Improvement (applied here): 4f treats the
manager's mapping as a cross-check feeding later inbox ORDERs, not a gate — recorded in
the runbook §4 so the next drafter inherits the posture, not the caution.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ · `check_plan_homing --strict` ✓ (both new plan docs homed in
planning README) · `check_current_state_ledger --strict` ✓ (benign newest-merge lag
only) · chat-only material swept: the owner go + step-by-step click list → the two §0
sections + runbook; the succession-doc findings → package headers (provenance). Claim
file deleted this commit.

## Handoff

Owner click path (also delivered in-chat, in order): **A)** world seat — env
`superbot-games` (python-lab archetype) → Project "World Games" → paste world §1/§2.
**B)** idle seat — create EMPTY public repo `superbot-idle` → tell the dispatch chat
(copilot seeds) → settings (auto-merge + `substrate-gate` required) → env
`superbot-idle` → Project "Idle Engine" → paste idle §1/§2. Copilot then boot-verifies
both (packages §4) and opens runbook §5 rows. Unchanged clicks: sim-lab OA-002 Codex
toggle · EAP email before 07-14 · §2.5 batch · orphan-watchdog go.

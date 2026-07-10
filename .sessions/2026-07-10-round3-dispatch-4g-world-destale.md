# Session — round-3 dispatch, part 4g: world-package de-stale (check-in sweep findings)

> **Status:** `complete`
> **Run type:** self check-in sweep (22:42Z wakeup) → fix-on-sight (Q-0166) · same live
> dispatch chat (parts 4/4b/4c/4d/4e/4f merged)
> **Model/time:** fable-5 · 2026-07-10 ~22:4xZ → ~22:5xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1968) · PR #1969.

## What is about to happen

The check-in sweep read superbot-games @ HEAD `4493292` + the manager's conformed
mapping (fm PR #46) + the live `projects/` registry, and found part-4f's world brief
stale on arrival. De-stale §0/§2/§4 of the world package; commit the registry-ingest
relay; hand the owner the corrected §2 block in chat.

## What happened

- **Sweep verdicts (ground truth):** #1965/#1966/#1968 all MERGED · manager ORDER 013
  conformed mapping SHIPPED (fm PR #46) — agrees with part-4f on every flag
  (`superbot-idle`, theme contract in Seat B, setup-code first, selector
  last-shippable); adds the API three-way split (game-state feed stays superbot-lane
  #1920 pattern / theme+feature manifests in game seats / provisioning =
  setup-code) — consistent with the idea doc, no conflict · `projects/` registry
  LIVE (13 seat packages, one-writer manager, edit-registry-first doctrine — the 4d
  design, adopted) · sim-lab HOT (VERDICT 003 finalized, INTAKE 004 in-progress,
  005 queued) · superbot-games kit ALREADY v1.7.0 (its PR #22, 20:22Z) + unified
  inbox EXISTS with manager ORDERs 001 (P0 CI collection-scope: gate collects
  73/121) + 002 (P1 self-arm, pre-Q-0265 hourly), both status: new.
- **World package de-staled (this PR):** §2 step 2 rewritten — inherited-state block
  (don't re-create the bus, don't re-upgrade the kit) + ORDER 001 promoted to the
  walking-skeleton PR (folding the gen-1 bannering + heartbeat-drift fix); step 3 now
  executes ORDER 002's intent under Q-0265 with the supersession recorded; queued
  slice (a) struck (kit upgrade already landed); §0.4 + calibration + §4 red flags
  updated (re-upgrading the kit / re-creating the bus are now named red flags).
- **Runbook §6.3:** registry-ingest relay committed (prevents the manager's
  ORDER-013 "drafting is next" from producing duplicate packages; reconciles the
  registry's pre-part-4f cadence meta with the :15/:45 stagger).

## ⚑ Self-initiated

- Treating inbox ORDER 002 (hourly Class A) as cadence-superseded by Q-0265 while
  preserving its task + record duties — the same resolution the manager itself
  applied fleet-wide; vetoable at the seat's calibration.
- The §6.3 relay's instruction that superbot planning copies become frozen pointers
  after ingest — direct application of the 4d one-source-of-truth rule.

## 💡 Session idea

**Package `verified-against:` header line.** Founding packages should carry a
machine-readable `verified-against: <repo>@<sha> <ISO8601>` line (world now
implicitly has one in prose). A boot brief is a claim about a repo's state; pinning
the SHA it was verified against lets the booting seat diff "what changed since the
package was written" in one command instead of discovering staleness item by item —
this session's entire diff was that discovery done manually. Dedup: not in ideas/;
complements the founding-package linter (part-4f idea) as one of its checks.

## ⟲ Previous-session review

Part 4f drafted both packages fast and grounded them in the succession docs — but it
verified superbot-games via those docs' *content* while trusting my earlier "kit
v1.2.0 / no unified bus" reading, which was already one manager-slice stale (PR #22
had merged 40 minutes before drafting). Improvement (applied): the de-stale itself,
plus the `verified-against:` idea above so the next package makes its freshness
assumption explicit and checkable.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ · `check_plan_homing --strict` ✓ · `check_current_state_ledger
--strict` ✓ (benign newest-merge lag only) · chat-only material swept: sweep verdicts →
this card + package edits; the ingest relay → runbook §6.3. Claim file deleted this
commit.

## Handoff

Owner: use the CORRECTED world §2 block (delivered in-chat, part-4g) if you haven't
pasted yet — if you already pasted the 4f version, no harm: the seat's step-1
HEAD-first read + the new red flags in §4 catch the drift at calibration. Paste §6.3
to the manager with the §6.1/§6.2 blocks if not yet sent. Everything else unchanged:
Seat B repo creation → copilot seeds; sim-lab OA-002 toggle; EAP email before 07-14.

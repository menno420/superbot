# 2026-07-03 — Rebuild Phase A · hub topology + navigation contract + interface presets (owner-live)

> **Status:** `complete` — PR #1684. Owner-live continuation of the conventions freeze. Docs-only;
> no `disbot/` code.

## What shipped (PR #1684)

1. **[`docs/planning/rebuild-hub-navigation-presets-2026-07-03.md`](../docs/planning/rebuild-hub-navigation-presets-2026-07-03.md)**
   — Phase-A companion decisions log #3:
   - **Hub topology (Q-0230):** one unified help hub; admin a permission-gated node inside it
     (button locked without authority, re-checked at click time) + `!admin` direct-open; five
     working top-level buckets (Games/World · You · Community · Knowledge/AI · Admin) to refine in
     Stage 2.
   - **Navigation contract (Q-0231):** framework-injected into every rendered state — **Back**
     (contextual, pops the real stack) + **Home** (absolute, help root); every node directly
     openable by command; semantic-parent declared for direct-entry Back; **persistent restart-safe
     panels** (no premature timeout, versioned custom_id, generated-from-state) — which *also*
     solves surviving the merge=deploy redeploys (same fix, free from the generated model).
   - **Interface presets (Q-0232):** per-guild customizable hub; presets = named bundles of
     visibility config, chosen at setup with a **live preview that is the real generated hub**;
     Q-0215 pick→edit→manual + safe default; features declare their own preset membership
     (anti-drift); presets ≠ triage. **Improve + centralize** the existing working-but-fragmented
     surface — verified: setup `preset_select` + help overlay editor/projection work, but presets
     are reimplemented ≥7× → collapse onto one primitive (C-3) + one generated hub; existing code
     is the prior art to port.
   - **⚠ Open sub-decision:** preset exclusion = hidden-but-runnable vs disabled-entirely (agent
     leaning: hidden=off default + toggle).
2. **Router Q-0230…Q-0232** with verbatim-quote provenance.
3. **Homing + ledger:** planning README row, current-state entry #1684, ideas index.

## 💡 Session idea (Q-0089)

**[`rebuild-navigation-completeness-check-2026-07-03.md`](../docs/ideas/rebuild-navigation-completeness-check-2026-07-03.md)**
— a CI golden that walks every generated panel state and asserts Back+Home are present/working (the
enforcement arm of Q-0231) + every feature is in ≥1 preset. Worth having because "the framework
injects Back/Home" is only true until a render path bypasses it — a golden turns the guarantee into
something CI proves, which is exactly the owner's "no matter how many times the panel updated."

## ⟲ Previous-session review (Q-0102)

Previous card: **#1683 (permission allowlist).** It did the right root-cause thing (config guard
over a note) and, notably, **corrected an earlier wrong claim of mine** (the "environment-level
permission toggle") by checking the actual docs — good Q-0120 discipline mid-session. **Improvement
surfaced this session:** three of today's discussion facets (naming, then invocation, then
hub/nav) each turned out to already exist in shipped code (fuzzy matchers scattered; presets ≥7×;
help editor). The pattern: I confirmed existence *reactively* after the owner said "this exists."
A cheap workflow win — when the owner describes a capability, **grep for it first** and open with
"here's what exists + its fragmentation," so the discussion starts from ground truth. Make it the
default for Stage 2's subsystem walk.

## Docs audit (Q-0104)

- `check_docs --strict` + `check_plan_homing` run at close (below); ledger entry #1684 added
- Owner decisions → Q-0230…Q-0232; session idea indexed
- Chat-only residue: none — hub/nav/preset decisions + the hide-vs-disable open item + the
  "exists, centralize" finding are all in the decisions log.

## ⚑ Self-initiated

None — Q-0230…Q-0232 are owner-directed live; the open hide-vs-disable item is flagged for the
owner, not self-decided.

## For the next session

- **Resolve the one open item:** preset exclusion = hide-vs-disable (Q-0232).
- **Continue hub topology into Stage 2:** finalize the exact top-level bucket set + per-subsystem
  hub placement + preset membership (part of the subsystem walk).
- **Still-open batch-2 conventions threads** (offered, not yet walked): alias policy through
  cutover, G-22 staging lanes, the **new-feature correctness oracle** (the one hole in the
  "100% correct" story — verifying giveaways/media-gen with no old bot to match).
- Stage-2 walk agenda unchanged (see the conventions log + stage-1 log §6).

# Session — dashboard finalized-state vision (synthesize report + Codex PR 998 → one north-star plan)

> **Status:** `complete`

## What I'm about to do (born-red declaration, Q-0133)

Owner uploaded a deep-research report (`f53d0b97-deepresearchreport1.md`, Dutch) and asked me to review
it **plus Codex's PR #998**, compare both to what the repo already has, **filter the good ideas**, and
turn the result into **one comprehensive plan document that envisions the finalized state of the website
and the bot's configuration capabilities**. Close PR #998 once its material is captured; route any
genuine open questions to the doc / the question router.

- **Finding:** both the report and PR #998 are independent external reviews that largely *re-derive*
  conclusions the repo already reached in two existing plans — `developer-dashboard-plan.md` (live record
  + near-term roadmap) and `dashboard-live-editor-plan.md` (the L0–L3 build sequence). What's genuinely
  **missing** is a single **north-star vision** doc tying the zones, the navigation model, the full
  config-capability map, the data/freshness architecture, the **manifest spine**, and the security-ring
  model into one finalized-state picture. That is the deliverable.
- **Plan:** write `docs/planning/dashboard-vision-finalized-state.md` as the umbrella vision the two
  existing plans become execution tracks under (no parallel source of truth — heavy cross-links, defer
  execution detail to them). Link it from both plans (guarantees `check_docs --strict` reachability).
  Route the genuinely-open architectural forks (manifest-spine go/no-go; owner-zone future scope) to the
  router as **Q-0162**, with safe defaults captured in the doc for every open question.
- **Then:** close Codex PR #998 with a courteous reason (superseded; its useful material — the
  route-trust inventory, the manifest JSON schema, the readiness table — folded into the new doc).

Docs-only; no `disbot/` runtime, no auth, no mutations.

## What shipped (PR #1002 — docs only)

- **NEW `docs/planning/dashboard-vision-finalized-state.md`** — the north-star vision: the four zones
  (public · personal · server-admin · owner/dev), the IA + navigation model (top-nav + workspace sidebar
  + command palette + canonical detail routes + mobile), **the bot's full configuration-capability map**
  (every configurable surface → its audited seam → scope → finalized web affordance → status), the
  data/freshness architecture (3-tier reads + freshness contract + the route-trust inventory + data-trust
  matrix folded from #998), **the manifest spine** (typed command/panel/settings manifest + schema +
  reconciliation tests — the one genuinely-new architectural track), the 3-ring authority model, the
  anti-patterns, and a roadmap that ties each phase to its owning execution plan. Explicitly framed as the
  umbrella the two existing plans execute *toward* (no parallel source of truth).
- Linked from both **`developer-dashboard-plan.md`** and **`dashboard-live-editor-plan.md`** (a North-star
  pointer in each status block → guarantees `check_docs --strict` reachability + discoverability).
- **Q-0162** appended to the router — the two genuinely-open forks (manifest-spine go/no-go + priority;
  owner-zone future delegated scope), each with a plain-language "why it matters" + safe default. The
  other open questions carry defaults in the doc and don't block.
- **Closed Codex PR #998** — its useful material (route-trust inventory, data-trust matrix, manifest JSON
  schema, readiness framing) is folded into the vision doc; closed to prevent a third parallel plan.
- `active-work.md` claim added (this branch).

## How the inputs were filtered (the "good ideas" pass)

Both the uploaded report (Dutch) and PR #998 are independent reviews that **largely re-derive what the
repo already decided** (Q-0155–Q-0160 + the two plans): Discord OAuth, a private bot-side control API,
audited-seams-only writes, no parallel source of truth, panels-last. Kept the genuinely-additive parts —
the per-route trust inventory, the data-trust matrix, the typed manifest spine (the repo's biggest *gap*),
the full 4-zone IA + nav model, the freshness contract, the 3-ring authority framing. Dropped the rest as
already-shipped/decided. Did **not** copy the report's internal citation tokens or its Dutch prose.

## Verification

- `python3.10 scripts/check_docs.py --strict` → **green** (314 docs; new `plan` doc reachable via both
  plans; all relative links resolve; Recently-shipped 20/20, top-level 19/19 — untouched).
- No `disbot/` / python touched → no mypy/pytest/lint surface; CI `code-quality` red on the born-red
  commit (`98b8b20`) is the **Q-0133 session gate** holding the merge, cleared by this `complete` flip.
- Did **not** touch `current-state.md`: its ledger is at the 20 ratchet and the 7-PR drift the SessionStart
  banner flagged is the **recon routine's** job (Q-0124 — a manual session doesn't run the full pass).
  Reachability of the new doc does not need a current-state link (it's transitive via the two plans, which
  current-state already links).

## Context delta

### needed-not-pointed
- PR #998's full diff (the Codex plan body) — fetched via `pull_request_read get_diff`; the *comparison
  baseline* that mattered most was the two in-repo plans (current-state pointed at them well).
- The router tail — for the next free Q-number and the live Q-block format. **Q-number collision:** I
  grabbed Q-0162, but a parallel session's #999 (rm-permission-brake) **merged Q-0162 to `main` first**,
  so on the post-push merge-conflict resync I **renumbered mine to Q-0162**. The append-only
  "next free Q-00NN" convention can still collide when two sessions append concurrently — the resolver is
  "whoever merges first keeps the number; the later one bumps."

### pointed-not-needed
- The deep CodeGraph / architecture-binding orientation route — irrelevant to a docs-only vision synthesis
  (no runtime touched). Confirmed `command_surface_ledger.py` exists with a single `Glob`, no deep read.

### discovered-by-hand
- **Three near-parallel dashboard plans were forming** (two in-repo + the report + #998). Nothing in the
  workflow flags "a new plan overlaps an existing lane's plan," so the duplication only surfaced by reading
  all of them. That's the gap this session's idea addresses.
- `check_docs` reachability is **transitive from read-path roots**, so linking a new plan from an
  already-reachable plan is sufficient — no edit to a read-path root (current-state/orientation) required.

## 💡 Session idea (Q-0089) — a planning-doc overlap guard

`scripts/check_plan_overlap.py` (or a soft `check_docs` rule): when a new `docs/planning/*.md` is added,
warn if its title/scope keywords strongly overlap an **existing** plan's, so the next agent **consolidates
under one north-star** instead of adding an Nth parallel plan. This session existed *because* that drift
already happened — the report + #998 + the two in-repo plans were four near-parallel dashboard plans, and
nothing caught it mechanically. Distinct from #992's *handoff-freshness* guard (which catches a stale
"build next" pointer vs. recently-merged PRs); this catches **duplicate-plan sprawl**. Small, stdlib,
decided-lane; recorded here (not a separate file) to keep my doc footprint minimal while parallel sessions
edit the dashboard lane — promote to `docs/ideas/` when built.

## ⟲ Previous-session review (Q-0102) — #992 (dashboard foundation-reconcile)

**Did well:** caught a real near-duplicate via the Q-0126 claim+PR scan and did the *honest* thing
(reconcile the stale handoff) instead of barrelling into already-shipped work — exactly the
duplication-avoidance the workflow wants. **Missed / could improve:** it left the dashboard lane with **two**
planning docs and didn't anticipate that external reviews (the owner's standing multi-agent refinement
pipeline) would spawn *more* near-parallel plans — there's no "one plan per lane / consolidate on overlap"
discipline anywhere, which is precisely why this session had to write an umbrella to stop a 3–4-way split.
**System improvement:** the planning-doc overlap guard above — it's the mechanical form of "before adding a
plan, check whether an existing plan owns this lane and consolidate." It reinforces #992's own Q-0089 idea
(handoff-freshness): both are "catch doc-drift before it costs a duplicate," one for handoffs, one for plans.

## 📋 Documentation audit (Q-0104)

Nothing from this session lives only in chat: the vision is a doc, the open forks are Q-0162, the inputs'
disposition + the #998 closure reason are in the PR/router/this log, the claim is in active-work.
`check_docs --strict` green. The only deliberate non-write is `current-state.md` (recon-routine territory,
Q-0124 — recorded above with reason). Grooming (Q-0015) is satisfied by the main task itself: it moved a
large owner-dropped idea (the report) **down its lifecycle** into a structured `docs/planning/` plan + a
roadmap of phases + a routed Q-block — the "structure a bigger idea into a plan" grooming move.


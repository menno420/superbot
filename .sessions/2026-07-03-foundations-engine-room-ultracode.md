# 2026-07-03 — Foundational mechanics: the engine room (PROMPT A, runtime/logic)

> **Status:** `complete`
> **Branch:** `claude/ultracode-engine-room-ap2es3` · **PR:** #1690
> **Session type:** ultracode discovery + audit (docs-only) — the runtime/logic half of the
> two-session foundational-mechanics brainstorm (Q-0236). Parallel session runs PROMPT B
> (presentation/verification); scopes disjoint.

## What happened

Ran PROMPT A verbatim as a **75-agent ultracode workflow** (0 errors, ~6.3M subagent tokens,
1766 tool calls). Per runtime/logic mechanic: (a) how-now with `file:line` cites, (b) 2–3
alternatives from leading bots/frameworks, (c) pressure-test of the frozen/decided approach →
an **adversarial-verify pass against shipped source** (Q-0120, kill claims that fight the
evidence) → a **3-round completeness-critic loop** → synthesis into a framing + a rubric-scored
ranked ledger.

**Deliverable:** `docs/analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md`
(243K chars, 661 lines, badge `reference`, reachable via the brief's new "Delivered reports"
section).

**Totals:** the completeness loop grew coverage **18 seed → 35 mechanics**; **246 issues**
(192 confirmed · 36 plausible · 11 unverified · **7 refuted-and-dropped**); **33 owner-gated
calls** collected in an Owner-decision queue.

**Headline catches** (all cite-verified against source this session):
- A **load-bearing decision-doc claim is false against source**: the conventions freeze (§2.2)
  says "no central command-typo resolver," but `disbot/utils/command_resolution.py:74-79` ships
  the exact AUTO/SUGGEST/NONE 3-tier design, wired live at `bot1.py:541-586` — so C-5 is *port +
  generalize*, not greenfield. (Q-0120 working as intended.)
- **Two silent loss paths already in prod**: any `*_VERSION` bump forfeits live tournament entry
  fees on the merge=deploy restart (`blackjack_cog.py:250-262`); the release-before-drain handoff
  runs both replicas with no idempotency → additive XP double-fires (`bot1.py:851-865`, `xp.py:76-82`).
- **No runtime error envelope**, **restart-safety systematically unbuilt** (ManagedTaskSpec has no
  persistence/misfire field; one-shot timers in-memory; no event outbox), and **authority is 4+
  overlapping models** with the bot-owner override copy-pasted across ~11 seams (and a disabled
  subsystem is still runnable via `/slash` today — `interaction_router.py:104-112`).

Verification done this session: spot-checked ~half a dozen cites (`command_access.py:256`,
`bot1.py:349-353`, `ui_permissions.py:26`, `ai/contracts.py:321`, `command_resolution.py:74`) —
all resolved exactly. `check_docs --strict` ✓, `check_current_state_ledger --strict` ✓ (3 newer
merges = benign lag).

## Context delta

**Needed but not pointed to.**
- The scope seam between *my* "persistence/restart mechanism" and *B's* "panel rendering", and
  *my* "settings model" vs *B's* "interface-preset rendering", is real overlap the brief states in
  overlapping words — I had to draw the seam by judgment. Worth an explicit seam line in the brief
  next time.
- The **event bus lives in `disbot/core/events.py` + `disbot/core/events_catalogue.py`** — there is
  **no `*event_bus*`-named file**; orientation/folios don't route there. Found by grep.
- The fuzzy command resolver **already exists** (`disbot/utils/command_resolution.py`) despite the
  conventions doc's "no central resolver" — orientation could not have surfaced that; the source
  audit did.

**Pointed to but didn't need.** Nothing to de-emphasize — the reading route (the four 2026-07-03
decision logs + the rubric + the frozen BUILD-PLAN/FINAL-REVIEW) was exactly right and load-bearing.

**Discovered by hand.** `scripts/check_docs.py` enforces **reachability** (item 4: a live non-
`historical`/`archive` doc must be linked from a read-path doc) **and pinned-path** (item 3:
backticked concrete repo paths must resolve) — I nearly shipped a backticked full path to session
B's not-yet-written report, which CI would have failed. Both are reverse-engineered from the
checker; candidate journal Quick-reference line.

## Decisions made alone

- **Badge `reference`** for the deliverable (matches sibling discovery docs under
  `rebuild-discovery/`; `analysis` is not a recognized badge).
- **Expanded fan-out 18 → 35 mechanics** via the mandated completeness-critic loop (config/flags
  arbitration, guild lifecycle, 3s ack/defer, arg-coercion type system, error envelope, pool
  lifecycle, migration runner, outbox, sharding, scheduler catch-up, state-version migration, …).
- **Reachability link placed in the brief's new `## Delivered reports` section** — a shared doc
  session B may also touch; low collision risk, structured so B owns its own line. Flagged.

## Flagged for maintainer (known limits)

- **11 issues are UNVERIFIED** — the adversarial-verify agent returned no verdict (mostly
  config/secrets + gateway-intent items). They're retained *tagged at the bottom of the ledger*,
  **not confirmed** — treat as leads, not findings.
- **"Alternatives" are largely from general knowledge** (marked "(from general knowledge)" inline),
  not live-fetched — directionally sound, not citation-backed.
- The report is **large** (243K chars). Entry points: the **Executive summary** + **Owner-decision
  queue** (33 items). The per-mechanic inventory is the evidence base.
- The **B-seam column reads "yes" almost everywhere** — agents flagged handoff seams generously;
  it's a coarse signal, not a precise handoff list.

## 💡 Session idea (Q-0089)

Extend the class-4 stale-claim checker (`scripts/check_plan_staleness.py`, per the existing
`rebuild-critical-review-checkers-2026-07-03.md` backlog) with an **absolute-absence-claim
sub-rule**: flag decision-doc statements of the shape *"there is no X / no central Y / X does not
exist"* in `plan`/`reference` docs and require an anchor or a re-verify marker — because such
claims **silently rot when the thing later gets built**. Grounded in this session's single
highest-value catch: the conventions freeze's "no central command-typo resolver" was false
(`command_resolution.py` ships exactly it). Distinct from the backlog's existing NN%/"complete"
sub-case. *Merits a standalone idea file + README index entry in a non-parallel session — deferred
here to avoid the shared-append collision with concurrent session B.*

## ⟲ Previous-session review (Q-0102)

The same-day freeze sessions (#1679/#1680/#1684) did excellent structured work but baked a factual
error into a frozen contract: conventions §2.2 asserted an absence (`no central command-typo
resolver`) that shipped source flatly contradicts. **What they missed:** a source-grep before
writing an absolute-absence claim. **System improvement it surfaces:** exactly the class-4
absence-claim linter above — this audit catching a claim the freeze should have is the
self-auditing loop paying off, the internal mirror of the Q-0234 oracle. (Genuine, not filler:
the fix is concrete and mechanizable.)

## 🛠 Friction → guard (Q-0194)

**Friction:** nearly shipped a backticked full path to session B's non-existent report (would have
failed `check_docs` "pinned" at CI); and the reachability requirement for a new `reference` doc
isn't discoverable until the checker fails. **Guard:** the *enforcing* prevention already exists
(`check_docs` reachability + pinned checks) and caught both locally — no new checker needed. The
residual gap is **discoverability**, addressed by a candidate `.session-journal.md` Quick-reference
line: *"new non-historical doc → link it from a read-path doc; never backtick a path to a file that
doesn't exist yet — both are `check_docs`-enforced."* Journal is a shared doc; recorded here as a
ready-to-promote Rule to avoid a parallel-window collision (docs/journal = free to ship, deferred
only for collision-safety).

## Grooming (Q-0015) · Self-initiated

- **Grooming:** the deliverable *is* the pipeline advance — its ranked ledger + 33-item owner queue
  are the direct input to Stage 2 (subsystem walk) + Gate-V. Its mechanizable findings (rubric
  classes 1/3/5/8/9) route to the existing `rebuild-critical-review-checkers` backlog; the class-4
  absence-claim sub-rule extends it. No existing idea file edited (collision avoidance) — routing
  recorded here.
- **⚑ Self-initiated:** none — executed the owner-directed PROMPT A (Q-0236) verbatim; no
  self-initiated idea→plan→build promotion.

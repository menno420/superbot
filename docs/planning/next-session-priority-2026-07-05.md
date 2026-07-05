# Next-session priority — is "finish the substrate kit" the right call? (2026-07-05)

> **Status:** `plan` — an owner-requested priority assessment written at the close of the save-fixes
> session, to prime the next session. **Not binding** — the live queues in
> [`../current-state.md`](../current-state.md) + the per-sector files win if they've moved.

## The short answer

**You're *almost* right — with one correction: the substrate kit is already *finished*.** The full
kit (nervous system + context-economy engine + one-step-adopt packaging, 407 tests) shipped in
**#1649** (2026-07-02) — the S3 ledger marks *"THE MEMORY SUBSTRATE IS FINALIZED"* and the old
"▶ FINALIZE THE MEMORY SUBSTRATE" item is **✅ DONE**. So "finish the substrate kit" isn't a build
task anymore.

What you likely mean by "finish" is **the last remaining substrate step**, and there it is genuinely
the highest-leverage *offline* thing on the rebuild critical path:

- **Phase-2.5 cold-start substrate-on/off A/B** — `[offline]`, and it **gates Phase 3**. This is the
  "prove the substrate actually helps" experiment: adopt the kit into a fresh scratch repo from
  `dist/bootstrap.py`, run agent sessions *with* vs *without* it, measure the difference. It's the
  owner-flag-2 acceptance tier ([handoff §5.B-addendum flag 2](rebuild-ultracode-handoff-2026-07-02.md)),
  and its result is **evidence that feeds the rebuild go/no-go decision** you still owe (below). So it
  is doubly valuable: a hard Phase-3 prerequisite *and* go/no-go evidence.
- **Extract to a standalone repo** — `[owner]`. Deliberately owner-driven (flag 1: no external
  repo / publish without you). Not an autonomous-session task.

So: **yes, the substrate lane's next step is worth doing — but it's the Phase-2.5 A/B, not "finish
the kit," and it is *offline-startable now*.**

## The one thing genuinely "ahead of it" — and it's yours, not a session's

The **whole rebuild is behind an owner gate**: no Phase-3 new-repo code until you ratify the Phase-2
design spec + the backward-compat contract + the go/no-go
([design spec §10.2](rebuild-design-spec-2026-07-02.md); the evidence package —
[linchpin validation #1639](rebuild-linchpin-validation-2026-07-02.md) — is already in). The
Phase-2.5 A/B produces one more piece of that evidence, but the **decision itself is the binding
constraint**, and only you can make it.

**Important nuance (verified this session):** Phase 3 sits behind **two independent gates** — your
design-spec ratification **and** the Phase-2.5 cold-start A/B. So doing the A/B does **not** by itself
open Phase 3; it clears one of the two. And the substrate *extraction* is **off** the rebuild
critical path entirely — the rebuild bootstraps from the **in-repo** kit at K0, so extraction is a
"productize the standalone artifact" step, not a rebuild prerequisite.

## The candidates, ranked for the *next session* (decision tree)

The right pick depends on whether the next session has you **live** or runs **autonomous**, because
the single most rebuild-critical task — continuing the Stage-2 walk — **needs you live** (every row
is a live owner disposition; the walk doc §7.5 + the S3 note both say so).

**If you are live for the next session → continue the Stage-2 subsystem walk at L1c.**
- It's the rebuild's Stage-2 critical path and **can't be done autonomously** (every row is a live
  owner disposition). **33 rows remain** (L1c = visual card engine, welcome, ux_lab; then L2 9 · L3
  14 · L4 6 · L5 4 + the non-cog platform queue). Source of truth:
  [`rebuild-stage2-subsystem-walk-2026-07-05.md`](rebuild-stage2-subsystem-walk-2026-07-05.md) §3
  progress index + §7 handoff. Highest-value use of *your* live time.

**If the next session is autonomous (you're away) → two equally-good picks; choose by appetite:**
- **(i) Continue current-bot lock-in — the walk's §7.2 committed scope.** You *explicitly directed*
  the next session to "start implementing some of §7.2's committed scope into the current bot"
  (walk §7.2). It's offline and small-PR-shaped: the turn-key tail is zero-risk (channel: delete 5
  orphaned capability strings; role: delete dead `RoleHubView`, collapse legacy-duplicate commands,
  add slash mirrors, de-dup reconciliation; ticket: expose `category_id`/`ping_staff` + slash
  mirrors; automod/cleanup/image-mod minimal panels), and the "new design" items (case/appeal, bulk
  mod, quarantine, ticket auto-close) are agent-doable with an in-session design pass. This is the
  direct continuation of the save-fixes thesis (harden the current bot before the rebuild). Lower
  risk, immediate value.
- **(ii) Advance the rebuild's evidence — the Phase-2.5 cold-start A/B.** Offline, on the rebuild
  critical path, produces go/no-go evidence (Sonnet runs the paired sessions, Opus interprets).
  Turn-key start: [handoff §5.B](rebuild-ultracode-handoff-2026-07-02.md) +
  [strategy §3 phase sequence](fresh-rebuild-strategy-2026-07-02.md). Heavier (paired agent runs +
  in-session measurement design), and it clears only *one* of the two Phase-3 gates — so it's the
  more strategic but not more *urgent* pick.

**Quick lock-in wins available in any autonomous session (offline, current-bot, disposable per Q-0105):**
- **Small:** the **deferred-action restart-recovery checker**
  ([idea](../ideas/deferred-action-restart-recovery-checker-2026-07-05.md)) — stdlib AST/grep, no new
  dep; would surface a 3rd instance (`utility_cog.py:61`) beyond the two this week's bug #8 fixed.
- **Medium:** the **audit-seam-coverage checker**
  ([idea](../ideas/audit-seam-coverage-checker-2026-07-05.md)) — verified this session to be a real
  gap in *both* the current bot and the rebuild's verification plan (the missing AST complement to the
  rebuild's `audit_completeness` fence); would have caught 3 of the 8 save-fixes bugs at authoring
  time. The reachability analysis is the non-trivial part.

**Not a next-session task (handled elsewhere):**
- The **Q-0107 reconciliation pass** is due at #1740 (current head ~#1735). A *manual* session does
  **not** run it (Q-0124) — the docs-reconciliation routine auto-fires at the boundary.
- The **rebuild extraction** (owner-gated + off the critical path) + the **ratification decision** are
  owner actions.

## Recommendation in one line

Next **live** session → **Stage-2 walk L1c** (only-you work). Next **autonomous** session → **§7.2
current-bot lock-in** (owner-directed, low-risk, continues the save-fixes thesis) *or* the
**Phase-2.5 cold-start A/B** (more strategic, heavier) — with the small **restart-recovery checker**
as a fast lock-in win either way. **Your instinct was right in direction** — the substrate lane's
next step (the A/B) is worth doing — just note the *kit itself is already finished*, the A/B is one
of *two* Phase-3 gates, and there's an equally-good owner-directed current-bot lane (§7.2) if you'd
rather keep hardening the shipped bot first.

---

*Evidence base: `docs/current-state/S3-ai-memory.md`, the rebuild handoff §5.B(-addendum), the
design-spec §10.2 gate, the Stage-2 walk doc §7/§3, and the save-fixes session findings. Written
2026-07-05; verify against the live per-sector queues before acting.*

# 2026-07-06 — CI-arc completion: 2nd AST guard + tail cleanup

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). `check_quality.py --full` green:
> ruff format+check, check_docs, check_consistency, check_architecture --strict, mypy, and **14157 pytest
> passed** (incl. 10 new `check_deferred_recovery` tests); the only errors are the 5 pre-existing
> sandbox-only `test_atlas` grimp `bot1` flakes (CI-unaffected). Both new guards clean (0 findings) on the
> real tree. Follow-up to the merged #1747.

## What this session did

Owner directive: *"finish everything you can do without my help; you can choose decisions yourself."* So
this session completed the **safe, self-contained** remainder of the CI-followups arc
(`docs/planning/ci-followups-handoff-2026-07-05.md`) and made the design calls autonomously — while
holding the safety brakes (nothing that rewires branch protection or executable config, or that risks
the merge gate, was taken; each is flagged below for explicit owner sign-off).

## Shipped (PR #1748)

- **`check_deferred_recovery.py`** (handoff **#5**, second AST guard) — keys on the **spawn-target**
  (`tasks.spawn`/`create_task`/`ensure_future`), resolves the callee, flags a spawn-target whose body does
  `asyncio.sleep` **then** a Discord state mutation (raw attr OR a name-based lifecycle-routed verb like
  `_lift_lockdown`/`slowmode`) in a module with **no persisted-deadline write + no boot reconcile**. Wired
  `continue-on-error`; `architecture_rules/deferred_recovery_exceptions.yml` allowlist; 10 unit tests incl.
  the gate-bites meta-test + real-tree-clean ground-truth. Calibration held — 23 raw-sleep files → **1**
  finding (`security_service._hold_then_lift`), triaged + allowlisted as intentionally process-local
  (ADR-002); `proof_channel` (the #1728 fix) correctly clean.
- **CI tail** (handoff **#6**): deleted dormant `check_doc_freshness` (**G7**) + its 3 doc references;
  wired `check_session_slug_unique` advisory (fail-open, self-verifying the `origin/main`-in-CI question,
  **G6 slug**); resolved **G8** accept-advisory (owner-delegated); annotated the router.
- **Docs**: handoff (#4/#5/#6 + done section), ci-what-runs-where (§2a rows + §2f G7), context-map-tooling,
  the two checker idea docs → `reference`/BUILT, README index.

## Decisions I made under the delegation (⚑ owner-visible)

- **G8 = accept-advisory** — the documented recommendation; a no-op on enforcement (no presence gate). Safe.
- **Slug guard = wire advisory, not gate** — it fails open by design (can't false-block), so advisory is
  zero-risk *and* performs the CI-context verification a gate promotion needs. One-line follow-up to promote.
- **security `_hold_then_lift` = allowlist (ADR-002)** — with an **owner-visible caveat** recorded in the
  allowlist reason: the applied raid-slowmode is a real Discord-side change that does NOT auto-reset on
  restart (a mild residual gap). Documented-intentional; revisit if you want it restart-safe.
- **The `ci.yml`/`web-ci.yml` restructure (handoff #4) — DELIBERATELY NOT built.** Its whole payoff is the
  branch-protection cutover (G2) + 6 workflow deletions (G3) — a GitHub ruleset/admin change I can't do from
  code and that could break the merge gate for every PR. "Build alongside" would run a duplicate pipeline on
  every PR open-endedly (double Actions cost) with zero delivered value until that cutover, and refactoring
  `code-quality.yml` → the reusable leg risks the *current* required context. That is the "cross-cutting /
  affects how PRs merge" class the autonomy boundary reserves for the owner. **Design is frozen + copy-paste-
  ready (§C.1)** — staged as build-ready, not unfinished analysis.

## Still owner-gated (NOT taken)

G2 (required-context swap) · G3 (6 workflow deletions) · G5 (`settings.json` Stop-hook rewires — executable
config affecting every session) · G4 (promote both guards to hard gates — after a clean band).

## 🛠 Friction → guard (Q-0194)

The friction: building the second sibling guard meant **copy-pasting** the AST/reachability primitives
(`_discord_mutation`, `_receiver_tail`, `_direct_calls`, allowlist load/match, the importlib test-loader)
from `check_audit_seam` — under-generalization. The durable guard is a **shared `scripts/lib/astguard.py`
+ a `new_checker.py` scaffold** (filed as this session's idea, below) — deferred because it is a real
refactor, too big for the arc's tail, but it is the enforcing fix so the *third* checker doesn't re-pay the
cost. Immediate enforcing win shipped instead: both guards carry a `test_real_tree_is_clean` ratchet, so a
new violation reddens pytest (advisory in CI, blocking in the suite).

## ⟲ Previous-session review (Q-0102)

Previous session = `check_audit_seam` (#1747, this conversation). **Strong:** rigorous empirical calibration
(80 → 4 → refined), two collision defenses, honest triage over rubber-stamping. **What it could have done
better:** handoff item #5 was *"the two AST guards"* — a bundle of siblings — but #1747 shipped one and
left the other for "next." Building both together (as this session confirms) is ~1 hour for the second
because the pattern + shared code are already in hand; splitting them meant #1747 *wrote* the duplicated
AST helpers without factoring them, and this session paid the copy-paste. **System improvement:** when a
handoff item bundles N sibling artifacts, prefer building them together (amortizes pattern-learning and
surfaces the shared-code seam) — and the **checker-authoring kit** idea is the durable mechanization of that.

## 💡 Session idea (Q-0089)

**A warn-first-checker authoring kit** — [`warn-first-checker-authoring-kit-2026-07-06.md`](../ideas/warn-first-checker-authoring-kit-2026-07-06.md):
factor the copy-pasted AST/reachability primitives (incl. the **import-qualified call resolution** that
defeats the `self.X`-vs-`module.X` collision — a recurring footgun with its own CLAUDE.md rule) into
`scripts/lib/astguard.py`, plus a `scripts/new_checker.py` scaffold that stamps out the checker + allowlist
+ gate-bites/real-tree-clean tests + advisory CI step. The warn-first checker is now the repo's dominant
author-time-safety pattern (4 shipped + the rebuild backlog); this turns each new one from a session-craft
into a fill-in and makes the collision-handling correct *once*. (Subsumes + concretizes the callgraph-lib
note from #1747's log.)

## 🧹 Grooming (Q-0015)

Advanced the CI-followups arc to near-complete: item #5 (both guards) ✅, item #6 (tail) ✅, #4 assessed +
staged, G7/G8 resolved. Moved two idea docs down their lifecycle (`audit-seam` + `deferred-action` →
`reference`/BUILT, README index marked). Next groomable: the checker-authoring kit (filed this session) or
the app-CI web-ci.yml leg (folds into the owner-gated #4).

## 📋 Docs audit (Q-0104)

`check_docs --strict` green; `check_current_state_ledger --strict` in sync (no merged PR this session — own
PR in flight; next reconciliation folds #1747 + #1748). Handoff / ci-what-runs-where / context-map-tooling /
router / 2 idea docs / ideas README all updated in lockstep with the code. **No new owner Q-block** — G7/G8
recorded as owner-delegated resolutions within the existing Q-0239; the delegation provenance ("finish
everything you can; choose decisions yourself") is captured on the router G8 annotation + this card.

## 📤 Run report

- **Did:** built `check_deferred_recovery` (2nd guard); CI tail (G7 delete · G8 accept-advisory · slug
  advisory+verify); assessed + staged the ci.yml restructure with reasoning. · **Outcome:** shipped.
- **Shipped:** #1748 — 1 checker + 1 allowlist + 1 test file (10 tests) + 2 advisory CI steps + 1 checker
  deletion + 1 new idea + ~8 doc updates. No `disbot/` runtime change (pure tooling/CI/docs).
- **Run type:** owner-directed autonomy ("finish everything you can; choose decisions yourself").
- **⚑ Owner decisions:** none blocking. Recorded owner-**delegated** resolutions: G7 (executed), G8
  (accept-advisory). **Still owner-gated (not taken):** G2/G3 (branch-protection cutover + workflow
  deletions = the ci.yml restructure), G5 (`settings.json` rewires), G4 (guard hard-gate promotion, after a
  clean band).
- **⚑ Owner manual steps:** none (CI-config + tooling only — nothing to verify in prod).
- **⚑ Self-initiated:** the whole session is owner-directed; the *judgment calls* under the delegation are
  the four "Decisions" above (G8, slug-advisory, the ADR-002 allowlist + caveat, and NOT building the ci.yml
  restructure).
- **↪ Next:** promote both guards to hard gates after a clean band (G4); the ci.yml restructure when the
  owner wants the cutover (build-ready, §C.1); G5 settings.json rewires (owner-gated); the checker-authoring
  kit idea (a genuine leverage build).

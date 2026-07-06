# 2026-07-06 — AST guard: check_audit_seam (audit-seam coverage checker)

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). `check_quality.py --full`
> green: ruff format+check, check_docs, check_consistency, check_architecture --strict, mypy, and
> **14147 pytest passed** (incl. the 19 new `check_audit_seam` tests); the only errors are the 5
> pre-existing sandbox-only `test_atlas` grimp `bot1` flakes (CI-unaffected, documented by the prior
> ruff session). `check_audit_seam` clean (0 findings) on the real tree; 6 findings triaged + allowlisted.

## What this session did

Continued the CI-setup arc (`docs/planning/ci-followups-handoff-2026-07-05.md` **item #5**, first of the
two AST guards). Built **`scripts/check_audit_seam.py`** — a repo-wide, per-function reachability guard
for the mutation-seam contract: a function with a **direct write signal** whose success path never
reaches `services.audit_events.emit_audit_action`. The #1728 "save-fixes" bug class (bug #5 raid-lockdown
`channel.edit`; bug #6 unaudited settings/roles db write) turned into a CI signal.

Built from the calibrated spec (`docs/ideas/audit-seam-coverage-checker-2026-07-05.md` — the naive
`*_mutation.py` scope is ~42% FP and misses the bug class), so **per-function**, warn-first, advisory.

## Shipped (PR #1747)

- **`scripts/check_audit_seam.py`** — three write signals: raw SQL outside `utils/db`, Discord state
  mutation on a non-message receiver, and an **auditable-domain** `utils.db` write; transitive
  audit-reachability over the `disbot/` call graph. `--mode {report,strict}` + `--json`.
- **`architecture_rules/audit_seam_exceptions.yml`** — allowlist; 6 triaged legit entries with
  source-verified reasons.
- **`tests/unit/scripts/test_check_audit_seam.py`** — 19 tests incl. the Q-0120 gate-bites meta-test
  (bug #5/#6 shapes flagged) + a **real-tree-clean ground-truth test** (a new unaudited mutation reddens it).
- **`code-quality.yml`** — advisory step (`continue-on-error`, deps block, code-gated).
- **Docs** — idea → `reference` (built), handoff §5 marked shipped with the build write-up,
  ci-what-runs-where §2a row + the `40→43` script-count drift fix.

### Two calibration refinements the build required (the calibration was right — naive was too noisy)

1. **Import-qualified db-call detection** — `db.set_x()` where `db` is a `utils.db` alias, not a bare
   name match → `self.add_item` (the `discord.ui.View` method colliding with the `inventory` helper) is
   never a false db write.
2. **Auditable-domain scoping via DIRECT write+emit co-occurrence** — a db helper is "auditable-class"
   only if some function writes it *and* emits in the same body (the audited-wrapper shape). This is
   collision-proof: the name-merged call graph marks generic verbs (`credit`/`award`) audit-reachable
   off one namesake and would otherwise mark whole game domains auditable (the ~42% FP class). Result:
   the db dimension fires **only** on an unaudited write to a domain audited elsewhere (bug #6), never on
   economy/games/session writes. Cut the raw finding count 80 → 4 with zero loss of the bug class.

### Triage (Q-0105 — validated against source, not rubber-stamped to green)

6 findings, all triaged legitimately non-auditable → allowlisted with reasons: automated/self-service
role application (counter rename · reaction-role apply · automation rule execution) + mechanical overwrite
steps of audited operations (setup channel · ticket channel, both created via the audited
`ChannelLifecycleService`). The delegate-decision audit (`setup_session` → `_emit_session_audit`) was
confirmed reachable — proving the transitive audit-reachability works on real code.

## 🛠 Friction → guard (Q-0194)

This checker *is* a friction→guard: it converts the #1728 subsystem-walk discovery (a human had to walk
every subsystem to find the unaudited mutations) into an author-time CI signal. The ground-truth
`test_real_tree_is_clean` is the enforcing half — a reintroduced bypass reddens pytest, not just the
advisory step. (No new workflow friction to guard; the dataclass+importlib `sys.modules` test gotcha is
documented inline in the test file's loader comment.)

## ⟲ Previous-session review (Q-0102)

Previous session = the **ruff migration** (A3, 5 python-gate tools → 3). **Strong:** atomic single-PR
cutover with magic-trailing-comma parity verified against black on all but the 14 known files, and it
correctly caught + swapped the two-thirds pin-drift surface at the root. **What it could have done
better:** it left a live footgun in the record — "the 5 `test_atlas` errors are the pre-existing
sandbox-only grimp flake" is asserted in the card but is *not* guarded anywhere, so every future session
re-derives that "is this flake mine?" question from scratch (I had to, this session). **Improvement
(surfaced, not yet built):** the sandbox-only `test_atlas` grimp flake should either be `skipif`-marked
with a reason pointing at the flake, or documented in `.session-journal.md`'s recurring-problems list, so
the next agent reads "known flake" instead of re-investigating. Filed as this session's grooming candidate.

## 💡 Session idea (Q-0089)

**A shared `scripts/lib/callgraph.py` for the reachability-checker family.** Three checkers now build the
same name-based AST call graph + reachability fixpoint by hand — `check_command_reachability`,
`check_settings_reachability`, and now `check_audit_seam` — and each re-solves the CodeGraph name-collision
problem independently (mine needed *two* collision defenses: import-qualified call resolution + direct
co-occurrence scoping). A shared lib encoding (a) the call graph, (b) the fixpoint, and (c) the
**import-qualified call resolution** (the reusable trick that defeats `self.add_item`-vs-`db.add_item`)
would DRY the three and make collision-handling consistent + tested once. Genuinely worth having — the
collision class is a *recurring* footgun (it has its own CLAUDE.md § CodeGraph rule), and centralizing the
defense is the durable fix. Dedup-checked `docs/ideas/` — not already filed. (Distinct from the built
checker: this is about the *tooling substrate* the checker sits on.)

## 🧹 Grooming (Q-0015)

Advanced the CI-followups migration itself: handoff item #5's first guard is shipped, and the doc now
points at `check_deferred_recovery.py` (the sibling) as the clear next `[offline]` build. Also moved the
audit-seam idea down its lifecycle (`ideas` → `reference`/built). Next groomable: the `test_atlas` flake
guard surfaced in the Q-0102 review above.

## 📋 Docs audit (Q-0104)

`check_docs --strict` green; `check_current_state_ledger --strict` in sync (no merged PR this session — own
PR in flight; next reconciliation folds #1747). Idea/handoff/what-runs-where updated in lockstep with the
code. **No new owner decision** — this executes within the already-recorded Q-0239 **G4** advisory-first
envelope, and the owner directed it in-session (the session prompt's "recommended next").

## 📤 Run report

- **Did:** built `check_audit_seam.py` (per-function audit-seam reachability guard) + allowlist + 19 tests
  + advisory CI wiring + docs. · **Outcome:** shipped (advisory).
- **Shipped:** #1747 — 1 checker · 1 allowlist · 1 test file (19 tests) · 1 workflow step · 3 doc updates.
  No `disbot/` runtime change (pure tooling/CI).
- **Run type:** owner-directed (session prompt named the task).
- **⚑ Owner decisions needed:** none new. G4 promotion to a hard gate stays owner-gated (revisit after a
  clean band); the **automation role-apply allowlist entry** is the one spot to flip if the owner wants
  automation-driven role changes surfaced in the audit log.
- **⚑ Owner manual steps:** none (CI-config only — nothing to verify in prod; merge = deploy applies but
  changes no running-bot behavior).
- **⚑ Self-initiated:** the task was owner-directed; the *judgment calls* were mine — the two calibration
  refinements (import-qualified detection, direct-co-occurrence scoping), the 6 triage/allowlist decisions,
  and the `40→43` script-count drift fix.
- **↪ Next:** `check_deferred_recovery.py` (handoff item #5, second guard) · or the live-verify (item #1) ·
  or the `ci.yml`/`web-ci.yml` restructure (item #4).

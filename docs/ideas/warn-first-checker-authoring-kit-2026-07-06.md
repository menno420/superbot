# Idea — a warn-first-checker authoring kit (scaffold + shared AST/reachability lib)

> **Status:** `ideas` — captured 2026-07-06 (CI-arc completion session, PR #1748), after building the
> **second** AST guard in two sessions.
> **Subsystem:** none (cross-cutting, `scripts/` + `tools/` tooling)

## The friction, felt twice

Building `check_audit_seam` (#1747) then `check_deferred_recovery` (#1748) — sibling warn-first AST
guards — surfaced two duplications that a third checker will hit again:

1. **Copy-pasted AST/reachability logic.** Both checkers re-implement `_callee_name`, `_receiver_tail`,
   `_direct_calls` (body-local call walk skipping nested defs), the `_discord_mutation` detector (with
   the message-receiver + message-kwarg exclusions), the `architecture_rules/` allowlist load+match, and
   the importlib-`sys.modules` test-loader boilerplate. `check_command_reachability` /
   `check_settings_reachability` re-implement the name-based call-graph + fixpoint independently too —
   and each re-solves the CodeGraph name-collision problem from scratch (the `self.add_item`-vs-`db.add_item`
   collision needed a bespoke fix in `check_audit_seam`).
2. **A repeated authoring *dance*.** Every warn-first checker follows the identical lifecycle: write the
   AST signal → run on the tree → triage findings → allowlist the legit ones with reasons → write a
   `test_*` with (a) the Q-0120 gate-bites meta-test and (b) a `test_real_tree_is_clean` ground-truth
   ratchet → wire a `continue-on-error` step in `code-quality.yml` → document → (later) promote to a gate.

## The idea — two facets of one kit

- **`scripts/lib/astguard.py` (shared lib).** Factor out the collision-robust primitives: the call-graph +
  reachability fixpoint, the **import-qualified call resolution** (the reusable trick that defeats the
  `self.X`-vs-`module.X` collision — its own CLAUDE.md § CodeGraph rule proves this is a *recurring*
  footgun), the Discord-state-mutation detector, and the allowlist load/match. The four existing
  reachability checkers become thin signal-definitions over one tested substrate.
- **`scripts/new_checker.py` (scaffold, sibling of `new_subsystem.py`).** Stamp out a new warn-first
  checker: the script skeleton (arg-parse, `analyze(sources)` seam, report/json/strict), the
  `architecture_rules/<name>_exceptions.yml` allowlist, the test file pre-wired with the gate-bites +
  `test_real_tree_is_clean` patterns, and the `code-quality.yml` advisory step — so the next guard is
  fill-in-the-signal, not copy-paste-and-adapt.

## Why it's worth having

The warn-first-checker *family* is now the repo's dominant author-time-safety pattern (audit_seam,
deferred_recovery, command_reachability, settings_reachability, and more coming from the rebuild's
checker backlog). Each new one currently costs a re-derivation of the same substrate + the same
collision defenses. A tested shared lib + a scaffold turns "write a checker" from a ~1-session craft into
a ~1-hour fill-in — and makes the collision-handling correct *once* instead of per-checker. Disposable
per Q-0105; start with the lib (higher leverage), add the scaffold when a third checker is queued.

## Prior art / related

- `scripts/new_subsystem.py` (the scaffold pattern to mirror) · `scripts/check_architecture.py` +
  `architecture_rules/` (the allowlist pattern) · the `.claude/CLAUDE.md` § CodeGraph name-collision rule
  (why import-qualified resolution belongs in the shared lib).
- The `test_real_tree_is_clean` ground-truth ratchet (shipped in both #1747 and #1748) is the pattern that
  makes an *advisory* CI checker also a *blocking* pytest ratchet — worth generalizing into the scaffold.

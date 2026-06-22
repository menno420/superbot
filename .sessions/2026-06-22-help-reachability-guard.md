# 2026-06-22 — Help reachability guard (orphan check)

> **Status:** `complete`

Self-initiated (Q-0172), owner-greenlit follow-up to the help-menu regrouping
(#1290) + Advanced removal (#1294). With the "All Commands / Advanced" catch-all
gone, an un-homed subsystem is now *completely unreachable* from the menu — so a
standing guard that asserts "every subsystem is homed" graduated from
nice-to-have to load-bearing.

## Shipped

- **`tools/sim/help_menu_grouping_sim.py`** — added `check_reachability()` (returns
  a list of violation strings for the live grouping) + a `--check` CLI mode that
  exits non-zero on any orphan (a `parent_hub`-less, non-hub subsystem), a
  section over the 12-item dropdown page, or a feature needing > 3 clicks.
  Updated the provenance header to document the guard.
- **`tests/unit/invariants/test_help_reachability.py`** — wires the check into
  the existing pytest suite (so it's a CI gate with no workflow YAML change):
  one test asserting the live registry is clean, one **has-teeth** test that
  drops a known child and confirms the orphan detector flags it (a vacuous guard
  is worse than none). The sim is loaded by file path (`tools/` isn't a package);
  the loader registers the module in `sys.modules` before exec so its dataclasses
  resolve field types.

Verified: `--check` exits 0 on the live registry; full suite green (11567
passed, 2 xfailed by design); arch 0 errors; `check_quality --full` ✓.

## ⚑ Self-initiated

Yes — this is the forward idea from the #1294 session, built after the owner's
explicit greenlight ("those are exactly the kind of things you can initiate
yourself"). PR opened ready, auto-merge armed.

## 💡 Session idea (Q-0089)

**Generalise the "invariant guard reads the live registry" pattern to a small
check family fed by the sims.** This session proved the value of a stdlib check
that mirrors a runtime model (the click graph) and fails CI on drift. The same
shape suits other "is the live config still coherent?" questions that currently
rely on a human noticing — one genuine candidate, not filler: **a hub-host-hook
guard** asserting every hub-host subsystem actually exposes a
`build_help_menu_view` (today only prose in the surface map asserts it), which
would catch "dropdown opens an empty panel" bugs at CI time.

## ⟲ Previous-session review (Q-0102)

The previous session (#1294, Advanced removal) did the deletion thoroughly and
correctly flagged in its own log that removing the catch-all made homing
load-bearing — and named this exact guard as the forward idea. That's the
self-auditing loop working: the session that created the risk recorded the
mitigation, and this session built it. It *could* have bundled the guard with
the removal (arguably part of "achieve the goal"), but splitting kept #1294 a
clean pure-deletion and this a clean pure-addition — easier to review and
revert. The split was the right call here.

## 🔎 Doc audit (Q-0104)

- `check_quality --full` ✓ · `check_architecture --mode strict` 0 errors.
- The two implicit contracts documented in `hub_registry.py` (#1290) —
  bidirectional roster + Games actionability — now have a third CI-enforced
  sibling here (reachability), so the registry's invariants are no longer
  prose-only (catalogue drift + actionability contract + this guard).
- No `current-state` ledger touch — recorded by the auto-triggered Q-0107
  reconciliation pass (next at #1320). Unmerged PR correctly absent.

## Context delta

- **Needed but not pointed to:** the `tools/`-isn't-a-package + dataclass /
  `sys.modules` gotcha when loading a `tools/sim` module from a test by file
  path. Cost one red run. Worth a one-line note for the next `tools/sim` test
  (or making `tools/` importable).
- **Pointed to but didn't need:** nothing notable — a small, focused addition;
  the #1290 sim was already structured to make `--check` a tiny extension,
  exactly as that session predicted.

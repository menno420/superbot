# Idea: contributor-doc / governance-files presence + freshness guard

> **Status:** `historical` ✅ **SHIPPED (PR #1120)** as `scripts/check_governance_files.py` +
> `tests/unit/scripts/test_check_governance_files.py` — presence + path-freshness guard for the root
> governance files. Disposable (Q-0105). Original idea body kept below. Session idea (Q-0089,
> 2026-06-19, from the repo governance/supply-chain baseline session).

## The idea

This session added the standard outward-facing governance files (`LICENSE`, `SECURITY.md`,
`CONTRIBUTING.md`, `CITATION.cff`) and a contributor on-ramp. They're prose, so nothing stops a later
refactor from silently deleting one, or letting `CONTRIBUTING.md`'s instructions rot (it cites
`scripts/check_quality.py --full`, `scripts/setup_dev_env.sh`, the binding contract paths — if any
move, the onboarding doc lies and the *first thing a new contributor runs* fails).

A tiny stdlib guard — `scripts/check_governance_files.py`, in the `check_docs.py` house style:
1. **Presence:** assert `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CITATION.cff` exist.
2. **Freshness:** parse the backtick repo-paths out of `CONTRIBUTING.md` + `SECURITY.md` and assert
   each resolves on disk (the same link-resolution `check_docs` already does for `docs/**`, but these
   root files are *outside* its scope — confirmed this session).
3. Optionally: assert `CITATION.cff` parses as valid CFF and `LICENSE` is non-empty.

This is the "executable verification over prose" ethos (the repo's own
`executable-verification-over-prose-verified-2026-06-12` idea) applied to the governance layer the
existing checkers don't cover.

## Why it's worth having

The whole point of adding a CONTRIBUTING on-ramp is that an outsider can run the commands and have
them work. A guard makes that a CI invariant instead of a hope. Cheap, read-only, stdlib, disposable
(Q-0105) — delete it if it proves more friction than value.

## Dedup

Checked against `docs/ideas/`: distinct from `check_docs.py` (scopes `docs/**` only — these are root
files), from the generated-artifact-freshness umbrella (that guards *generated* artifacts; these are
hand-written), and from the repo-consistency-linter (UX/interaction rules, not file presence).

## Route

Quick-win lane — a small guard, one session, no owner decision. Pairs with the P0 governance work in
[`docs/planning/repo-structure-improvement-plan-2026-06-19.md`](../planning/repo-structure-improvement-plan-2026-06-19.md).

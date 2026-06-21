# Permission-overlap guard for `.claude/settings.json`

> **Status:** `historical` — shipped 2026-06-21, self-initiated promotion (Q-0172).
> **Subsystem:** none (agent-workflow / tooling).

## The idea

A small stdlib config-lint, `scripts/check_permission_overlap.py`, that flags any
`permissions.allow` rule whose matched-command set is fully contained in a broader
`permissions.ask` / `deny` rule. Such an `allow` is *potentially shadowed*: depending on
the harness's precedence semantics (most-specific-wins vs. ask-always-wins) it may never
take effect.

## Why (the bug that motivated it)

2026-06-21: the maintainer kept hitting a confirmation prompt on the standard *verify +
force-push* bundle. Root cause was a shadow: `ask` held `Bash(git push --force*)`, whose
prefix is a prefix of the command the owner actually runs, `git push --force-with-lease …`.
PR #1211 added the narrower allow `Bash(git push --force-with-lease*)`, but that relied on
"most-specific-wins"; under strict ask-over-allow it would still prompt. The
semantics-independent fix was to make the `ask` rule precise (`Bash(git push --force *)`,
trailing space) so it never matches the lease form. This guard catches that whole class at
config-edit time — one source of truth over the per-incident patch (bugs-first, durably).

It deliberately does **not** flag the normal carve-out direction (a broad `allow` with a
narrower `ask` restricting a slice of it), which works under either precedence.

## Shipped

- `scripts/check_permission_overlap.py` (`--strict` / `--json`), reliability header per Q-0105
  (unverified, disposable). Not wired into hard CI (config-lint, ask-first before gating).
- `tests/unit/scripts/test_check_permission_overlap.py` — 9 cases incl. a regression for the
  exact #1211 residual and a "live settings is clean" assertion.
- The residual `ask` fix in `.claude/settings.json` (the actual prompt bug).

## Possible follow-up

If it proves reliable over a few sessions, graduate it into `code-quality.yml` (owner
greenlight first) so a future shadowed allow fails CI rather than only an advisory run.

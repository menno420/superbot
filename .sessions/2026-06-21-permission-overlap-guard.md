# 2026-06-21 — Permission-overlap guard + force-push `ask` residual fix

> **Status:** `complete`

## Arc
Continuation of the permission-prompt work (PR #1211). While building the guard I'd
logged as a session idea, I found a **residual bug in #1211**: the `ask` rule
`Bash(git push --force*)` (no trailing space) still has prefix `git push --force`, which
is a prefix of `git push --force-with-lease`. #1211's narrower `allow` only wins if the
harness resolves by "most-specific-wins"; under strict ask-over-allow the prompt would
persist. Fixed it semantics-independently and shipped the guard that catches the class.

## Shipped
- **Residual fix** — `.claude/settings.json` `ask`: replaced `Bash(git push --force*)`
  with the precise `Bash(git push --force )` + `Bash(git push --force *)` (trailing space),
  which match bare `--force` but **not** `--force-with-lease`. Correct under either
  precedence semantics; bare force / `-f` stay gated.
- **`scripts/check_permission_overlap.py`** — flags any `allow` rule whose command set is
  fully contained in a broader `ask`/`deny` rule (the "potentially shadowed allow" class).
  Does NOT flag the normal broad-allow + narrow-ask carve-out direction. `--strict`/`--json`,
  Q-0105 reliability header (unverified, disposable, not hard-CI-wired).
- **`tests/unit/scripts/test_check_permission_overlap.py`** — 9 cases incl. a regression
  for the exact #1211 residual + a "live settings is clean" assertion.
- Idea doc + README index entry (`docs/ideas/permission-overlap-guard-2026-06-21.md`).

## Verification
- `python3.10 scripts/check_permission_overlap.py --strict` → clean ✓ on fixed settings.
- Regression: simulated pre-fix settings → guard flags the shadow, exit 1 ✓.
- `python3.10 -m pytest tests/unit/scripts/test_check_permission_overlap.py` → 9 passed.
- `python3.10 scripts/check_quality.py --full` → see commit (green).

## Decisions made alone
- Made the `ask` rule precise rather than relying on harness precedence — semantics-
  independent and lossless. If the owner *prefers* `--force-with-lease` also be gated, revert
  the allow; left a note in the idea doc.
- Guard is advisory-only (not wired into `code-quality.yml`) — gating config-lint is an
  owner call (noted as the follow-up).

## Context delta
- **Discovered by hand:** Claude Code permission precedence between overlapping `allow` and
  `ask` rules is **not documented in-repo** and is the crux of whether a carve-out works.
  The safe pattern is "make the higher-precedence rule precise so sets don't overlap,"
  rather than relying on specificity. Worth a `.session-journal.md` Quick-reference note.
- **Needed but not pointed to:** that the web/remote harness ignores
  `defaultMode: bypassPermissions` (carried over from the #1211 session; still not in a
  durable home — candidate for the journal).

## ⟲ Previous-session review
The #1211 session correctly diagnosed the shadow and shipped a fix the owner asked for, but
it **stopped one level short of root cause**: it left `git push --force*` in `ask` and leaned
on an *assumed* precedence rule ("most-specific-wins") without verifying it — exactly the
"green that contradicts evidence / unverified assumption" smell Q-0120 warns about. This
session's residual fix + guard close that. Workflow improvement surfaced: when a fix depends
on an undocumented harness behavior, prefer the construction that doesn't depend on it (make
sets disjoint) over the one that relies on the assumption.

## 💡 Session idea
Add a **`.session-journal.md` Quick-reference line** documenting Claude Code permission
semantics as observed here (web/remote ignores `bypassPermissions`; overlapping allow/ask
resolution is precedence-uncertain → make the broader rule precise). Tiny, but it converts
two hand-discovered facts into orientation the next agent won't have to re-derive. (Deferred
to keep this PR focused on the guard; captured here as the next grooming pick.)

## 📤 Run report

- **Did:** Fixed the #1211 force-push `ask` residual + shipped `check_permission_overlap.py` guard with tests · **Outcome:** shipped
- **Shipped:** PR (this branch) — settings `ask` fix + permission-overlap guard + tests + idea doc
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none (optional: greenlight wiring the guard into `code-quality.yml`)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** `docs/ideas/permission-overlap-guard-2026-06-21.md` — guard promoted idea→build with no dispatch/owner ask (Q-0172)
- **↪ Next:** journal the Claude Code permission-semantics facts (this session's 💡), then resume the current-state ▶ ungated lane (botsite React-SPA migration or `public-data-contract-field-snapshot` guard)

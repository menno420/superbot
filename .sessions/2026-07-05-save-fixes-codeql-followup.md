# 2026-07-05 — Save-fixes follow-up: CodeQL log-injection hardening

> **Status:** `complete` — a single verified one-file fix + this card in one atomic push (no
> partial-merge risk, so no born-red dance needed).

## Why this is a separate PR

The "save fixes" PR (#1728, the 8 Stage-2 bug fixes) **auto-merged on green the instant
`code-quality` passed on its first head** — before a follow-up commit that hardened the bug #1
drift-log against a CodeQL log-injection alert could gate. So #1728's merged main carried the
sink. This PR lands that hardening as a fresh change off the merged main (the merged PR is terminal;
per the branch rule, post-merge follow-up is a fresh PR — and this is a *distinct* change, not a
re-attempt of the 8 fixes).

## What it does

`disbot/services/settings_mutation.py` — the AI-projection-drift `logger.error` (bug #1) logged the
raw setting `name` + `subsystem` (user-influenced values) → a log-injection sink flagged by CodeQL.
Now it logs only non-user-controlled values: `guild_id`, the `settings_keys` constant
(`spec.settings_key`, which identifies the setting anyway), and the generated `mutation_id`. The
`name` was redundant with `settings_key`; `subsystem` is always `"ai"` in that branch.

Verified: `ruff`/`black` clean; the 56 settings-mutation + projection tests pass unchanged.

## Lesson (friction → guard)

This is the journal's documented "land ALL commits before CI goes green" hazard (native auto-merge
merges server-side ~15s after the first green head). **Guard reinforced:** when a follow-up fix
arrives *after* the first push, either amend/rebase it into the same head before the first
`code-quality` completes, or expect the base PR to merge without it — batch security/lint follow-ups
into the initial push. (Candidate journal rule; already recorded in `.session-journal.md` under the
Q-0093 successor entry — this is a live recurrence.)

## 📤 Run report

- **Did:** landed the CodeQL log-injection hardening that #1728's auto-merge race left out of main.
  · **Outcome:** shipped
- **Shipped:** (this PR) — one-line log-sink fix in `settings_mutation.py`
- **Run type:** `manual` (follow-up to the owner-directed save-fixes session)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (merge auto-deploys)
- **⚑ Self-initiated:** yes — proactively remediated a self-introduced CodeQL alert that the
  auto-merge race left in main (Q-0129/Q-0172; the base change was owner-directed, this is its
  security follow-up)
- **↪ Next:** unchanged from #1728 — §7.2 committed feature scope + continue the Stage-2 walk (L1c).

# Session — extract the `!platform` command group onto a cog mixin

> **Status:** `complete`

## What this was

Dispatch run, **empty work order** (scheduled 2h cron fire) → the live ▶ NEXT queue is
plan-first/gated, so took the strongest contained, decided-lane slice available + a workflow
drift-fix, rather than force a weak invented code slice. PR **#943**.

## Done

### Slice 1 — `!platform` group extracted onto `PlatformCommandsMixin`
- Executed idea #939 (`docs/ideas/diagnostic-cog-platform-group-extraction-2026-06-16.md`).
- New `disbot/cogs/diagnostic/platform_group.py` holds `class PlatformCommandsMixin:` — the
  `platform_grp` group + **all** `@platform_grp.command` subcommands (moved verbatim) + their
  `_platform_embeds` imports. `DiagnosticCog(PlatformCommandsMixin, commands.Cog)`.
- `diagnostic_cog.py` dropped **799 → 260 LOC**, clearing the hard 800-LOC cog ceiling that
  blocked the next `!platform` subcommand. Pure refactor, no behaviour change.
- discord.py 2.7.1's `CogMeta` collects commands across the cog MRO → the `!platform` surface and
  its single-cog registration are unchanged (verified empirically before starting, and pinned).
- mypy fix for the mixin: `TYPE_CHECKING` Cog base (satisfies the `@commands.group` `CogT`
  type-var) + a `bot: commands.Bot` class annotation (the cog supplies it). Establishes the repo's
  first cog-mixin convention.
- New `tests/unit/cogs/test_diagnostic_platform_group.py` (3 tests): group registers via the
  mixin; every documented subcommand survives; the group callback lives on the mixin module (so the
  cog can't silently regrow past the ceiling). `test_cog_size` + `test_command_surface_ledger` green.

### Slice 2 — workflow drift-fix + ledger hygiene
- Executed idea `control-plane-single-source-pointer-2026-06-15`: collapsed the `current-state.md`
  Gates autonomous-loop bullet to a **pure pointer** at the canonical
  `operations/autonomous-routines.md` § Control-plane table (zero verdict prose). The verdict copy
  had drifted twice (band-#870, band-#930); with no copy it can't drift again. (The optional
  `check_docs` lint half was deliberately *not* built — the pointer collapse alone removes the
  copy; noted as a capture-only follow-up.)
- Ledger hygiene (Q-0104 doc audit): recorded **#942** (a `docs(current-state): reconcile ledger`
  PR that omitted its own entry — structural chicken-and-egg) and archived the oldest live entry
  (#898+#892+#889) to hold the soft-ratchet at 20. `check_current_state_ledger --strict` green.
- De-staled the ▶ NEXT note (`diagnostic_cog` 800-LOC blocker now CLEARED). Marked ideas #939 +
  control-plane-pointer `historical` / ✅ EXECUTED in their files and the README index.

### Gates
- `check_quality --full` green (9933 + 3 new tests) · `check_architecture --mode strict` 0 errors
  (only pre-existing views/xp warnings) · mypy clean · black/isort/ruff clean · `check_docs --strict`
  green · ledger guard green.

## Handoff — ▶ Next action

No change to the strategic next-step: the buildable `ready` queue stays consumed; next buildable
work is **plan-first** (own a small plan for the **AI §7 next workflow family** — post-prod-check —
or the **Hermes bug-triage `gh issue create` write**, Q-0121; image-mod Q-0108 shipped #941,
security tiers #929 in Hermes review). The `!platform` lane is now **unblocked** for more
diagnostics (the inflation health-finding §6 follow-up of the faucet/sink plan is the natural next
`!platform` slice, but it's design-for-review). Nothing left mid-sub-step here — #943 is a clean,
complete, self-contained refactor + docs pass.

## 💡 Session idea (Q-0089)

`ledger-guard-exempt-reconciliation-prs-2026-06-16.md` — a `docs(current-state): reconcile ledger`
PR structurally can't list its own (not-yet-assigned) number, so it always omits itself and the
strict ledger guard flags it next session (the #942 drift this run fixed by hand). Teach
`check_current_state_ledger.py` to **skip a docs-only ledger-bookkeeping PR** (title +
diff-confined-to-`current-state*.md`), closing the recurrence at the guard level instead of having
each next session reconcile it. Small, disposable (Q-0105).

## ⟲ Previous-session review (Q-0102)

Previous session = **#942** (the band-#930 follow-on that reconciled #932–#936/#939 into the
ledger). **Did well:** clean, correct six-PR reconciliation with live-GitHub title verification and
the ratchet held at 20 — exactly the ledger hygiene the loop wants. **Missed:** it didn't record
its *own* entry (#942), the precise drift I had to fix this run. **System improvement (initiated,
not waited-for):** that omission is *structural*, not careless — a reconciliation PR can't know its
own number when its body is written. So the fix isn't "remember next time"; it's the Q-0089 idea
above — make the guard exempt self-referential ledger PRs, so the loop stops generating-then-
re-fixing this drift every pass. This turns a recurring manual step into a one-time tooling change.

## Notes for a later review
- CodeGraph was up (built clean at session start, 40116 nodes). Grimp not invoked. No arch warning
  I couldn't retire — the only warnings are the long-standing views/xp ones, untouched.
- The cog-mixin pattern is now established (first in the repo); future cogs nearing the 800-LOC
  ceiling can follow `platform_group.py` (the `TYPE_CHECKING` Cog-base + `bot:` annotation idiom).

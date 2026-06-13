# Session (cont.) — substrate-kit PR 2 §3c: the skills layer

> **Status:** `reference` — same continuation session as the
> [stances increment](2026-06-13-substrate-kit-stances.md). After the owner flagged that the
> Q-0107 reconciliation had already run via the routine, I fixed that awareness gap (**PR #807**)
> then built the **§3c skills** half of the capability layer (**PR #809**). Resume = §3c personas.

## What this increment did

Two batches, shipped as two focused PRs (owner's "logical modular batches"):

**PR #807 — reconciliation-awareness fix (the owner's correction).** I had trusted the SessionStart
"Recon DUE" line; in fact the autonomous routine had already done the band-#800 pass (#803) and reset
the marker on `main` — my branch was just stale. Root-fix: `check_reconciliation_due.py` now reads the
marker from **origin/main as well as the working tree** (max), so a routine-completed pass isn't
re-flagged on a stale branch. Documented the mechanism in `autonomous-routines.md` (+ recorded that the
first autonomous reconciliation fired at #800, proving the trigger), reconciled the roadmap "Now" row,
and extended the journal's "check what merged to main" rule to **routine-merged** PRs.

**PR #809 — §3c skills.** `engine/skills/skills.py`: the 7-skill starter pack (session-close ·
quality-gate · review · repo-health · deep-research + new question · analysis), each declaring the
capabilities it needs beyond read; bodies carry `${slot}` refs so a skill is project-aware. The
**precedence model** `action_permitted(stance, action, skill)` — a skill's declared capability
overrides the ambient stance (the §3c headline rule), pinned by tests. Native emission via
`skill_document` (metadata-first frontmatter) + a `skills` CLI (list / `--build` into staging).
**Root-fixed a `build_bootstrap` bug**: a multi-line `from engine…` import leaked into the generated
single file (IndentationError) — `_split_imports` now drops such imports whole. Kit suite 77 → 91;
`--full` green; arch 0 errors.

## 💡 Session idea (Q-0089)

**A guarded `bootstrap install` command — the missing last mile.** The kit deliberately *stages*
generated artifacts into `.substrate/` (`render` → `.substrate/rendered/`, `skills --build` →
`.substrate/skills/`) and never writes a live `.claude/`/`docs/` tree — a real safety property. But
there's no command to *install* the staged output into the host's actual `.claude/`/`docs/`; the host
copies by hand. Add an `install` command that copies `.substrate/{rendered,skills,agents}` into their
host destinations **with `assert_safe_target` + a `--dry-run` default** (print the plan; `--apply` to
write) so it can never touch superbot's own live tree. It closes the bootstrap → onboarded-project loop
that currently dead-ends at staging, and reuses the guardrail that already exists. (Dedup-checked
`docs/ideas/` — no existing install-command idea; distinct from the §3c emission work, which only
generates.)

## ⟲ Previous-increment review (Q-0102)

Reviewing **PR #807 (the reconciliation fix), my immediately prior unit.** *Did well:* it didn't just
silence the false signal — it root-caused the local-vs-`origin/main` marker split, fixed the checker,
and documented the mechanism so the next session understands it; responsive to the owner's exact point.
*Could have done better:* I shouldn't have needed the correction — I trusted the SessionStart hook's
stale-branch output instead of running `git fetch origin main` first (a rule already in the journal).
**System improvement (propose, not self-apply — it's hook config):** the **SessionStart hook should
`git fetch origin main` before** running the recon/ledger checks, so the boot banner reflects `main`,
not a stale branch — the same root cause my checker fix addressed, but at the banner layer where I was
actually misled. Routed as a candidate for owner review rather than edited in (CLAUDE.md/hooks are
propose-first).

## Doc audit (Q-0104)

- `check_quality --full` green (both PRs); `check_architecture --mode strict` 0 errors;
  `check_docs --strict` + `check_current_state_ledger --strict` green; recon now correctly *not due*
  (marker #800, synced).
- Plan Execution log repointed (§3c skills DONE #809 → personas next); roadmap's two substrate
  mentions both advanced to #809.
- **current-state.md untouched** — subtree work tracked in the plan (the #789/#791–793 precedent).
- New owner-surfaced decision: the reconciliation-awareness gap — handled in-session per the owner's
  direction (no router Q needed; the fix + docs are the record).

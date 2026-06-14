# Session (cont.) — substrate-kit PR-2 remainder: the PreToolUse stance guard

> **Status:** `reference` — continuation of the substrate-kit plan. After §3c completed (#812), shipped
> the **PreToolUse out-of-stance hook (#813)** — the piece that makes the stance layer *enforced*
> rather than advisory-only. Resume = the rest of the PR-2 remainder (modes + contract templates).

## What this increment did

`engine/hooks/stance_guard.py`: maps each Claude Code tool to a stance action category
(Edit/Write/NotebookEdit → edit · Bash/WebFetch/WebSearch → run · Read/Grep/Glob → read);
`evaluate_tool(stance, tool)` returns an out-of-stance warning (e.g. `Edit` while the stance is
`review`) or `None`, **failing open** on any unknown tool / stance / malformed payload. Two CLI seams:
`hook pretooluse` (the runtime entry point — reads Claude Code's PreToolUse stdin payload, warns on
stderr, **always returns 0**: advisory per §3b, never blocks) and `hooks [--build]` (stages a
ready-to-merge `.claude/settings.json` PreToolUse snippet). Verified end-to-end via the single-file
dist (review+Edit → warns; debug+Edit → silent; `hooks --build` → valid JSON). Kit suite 102 → 117;
`--full` green; arch 0.

This closes the loop the capability layer opened: stances/skills/personas were *declarative*; the guard
gives the stance the one bit of runtime teeth the plan asked for — still non-blocking, so it informs
without constraining.

## 💡 Session idea (Q-0089)

**An out-of-stance KPI counter for the guard.** `evaluate_tool` already knows every time a tool runs
out-of-stance, but that signal evaporates (it's just a stderr line). **Proposal:** have `hook
pretooluse` increment a small counter in `state.json` (`metrics.out_of_stance_count`, per-stance) when
it warns, so the substrate's telemetry footer / KPI set (planned for PR 3) can report an
*"out-of-stance action rate"* — the cheapest measure of whether the fourth axis is actually changing
behavior, and the standing test the revision-report session (#788) asked for, made *live* rather than
sim-only. Tiny (one `backend.set` behind the existing warning branch), additive, and it turns the guard
from a nag into an instrument. (Dedup-checked `docs/ideas/` — distinct from the sim-harness stance
assertion; this is the *runtime* counterpart.)

## ⟲ Previous-increment review (Q-0102)

Reviewing **#812 (personas), the §3c finale.** *Did well:* it completed the capability layer cleanly
and — notably — *applied* the branch-base lesson from the collision (branched off clean main, zero
tangle), proving the capture→apply loop works. *What it left implicit:* shipping three *declarative*
mechanisms (stances/skills/personas) with **nothing enforcing them** — a reader could reasonably ask
"so what runs?" This increment answers that (the guard), but the gap existed for three PRs. **System
improvement:** when a plan ships a layer in increments, the increment that makes it *do something* (here
the hook) should be sequenced **early, not last** — "make it real before making it complete." For the
remaining PR-2 work I'll bias toward the behavior-bearing pieces (modes' actual per-session behaviors)
over more declarative templates. Captured as a sequencing note for the resume handoff.

## Doc audit (Q-0104)

- `check_quality --full` green (foreground + background mirror both exit 0); `check_architecture
  --mode strict` 0 errors; `check_docs --strict` green.
- Plan Execution log: hooks/stance-guard DONE (#813, item d enforcement half); ▶ RESUME HERE repointed
  to the rest of the PR-2 remainder. Roadmap's two substrate mentions advanced to #813.
- **current-state.md untouched** — subtree work tracked in the plan (the #789/#791–793 precedent).
- Honored **Q-0124** (reconciliation is the routines' job) — stayed on the substrate work.

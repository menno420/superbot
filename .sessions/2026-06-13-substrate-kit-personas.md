# Session (cont.) — substrate-kit PR 2 §3c personas (capability layer COMPLETE)

> **Status:** `reference` — continuation of the substrate-kit plan. Shipped **§3c personas (#812)**
> after #811 (skills) merged, **completing the §3b/§3c capability layer** (stances + skills + personas).
> Resume = the PR-2 remainder (modes + triggers + hooks + contract templates).

## What this increment did

`engine/agents/agents.py`: 3 read-only personas (architect · reviewer · researcher) generalized from
superbot's `superbot-architect` + `mutation-boundary-auditor`. Each emits a native
`.claude/agents/<name>.md` (frontmatter `name`/`description`/`tools` + system-prompt body); bodies fill
from the project's own contract slots (`${architecture_layers}`, `${ownership_model}`, …) so a persona
reviews against *this* project's rules. **Read-only by construction** — personas declare only
`Read`/`Grep`/`Glob`; no write ever leaks into a spawned sub-agent (test-pinned). Unlike skills, no
stance precedence (they're spawned specialists). `agents` CLI (list / `--build` stages into
`<state_dir>/agents/`, host-installed, mirroring `skills`/`render`). Built off clean main (post-#811),
**no tangle this time** — the session-idea lesson applied. Kit suite 91 → 102; `--full` green; arch 0.

This **completes §3c** — the kit now ships the full capability layer: **stances** (ambient posture),
**skills** (invoked procedure), **personas** (spawned specialist), all emitting into the native
`.claude/` tree, composing via the skill→stance precedence model.

## 💡 Session idea (Q-0089)

**A single `bootstrap build` that emits the whole `.claude/` tree at once.** The kit now has *three*
staging commands — `render` (docs → `.substrate/rendered/`), `skills --build` (→ `.substrate/skills/`),
`agents --build` (→ `.substrate/agents/`) — each a near-identical render-loop. **Proposal:** add an
umbrella `bootstrap build` that runs all three (and any future emitters) in one pass, reporting a
combined unfilled-slot count, so a host onboards with one command instead of three and the "what does a
full generation look like" answer lives in one place. Pairs naturally with the `install` idea from the
skills session (build → stage → install). Small, additive, DRY-ing three call sites. (Dedup-checked
`docs/ideas/` — not present; distinct from the per-mechanism `--build` flags, which stay for targeted
regen.)

## ⟲ Previous-increment review (Q-0102)

Reviewing **#811 (skills, the clean re-cut).** *Did well:* it recovered cleanly from the
parallel-collision mess — closed the tangled #809, re-cut skills-only off fresh main, and shipped green;
and it *captured* the root-cause lesson (don't branch a PR off an unmerged sibling) as a session idea.
*What this increment proves about that lesson:* I **applied** it — personas branched off `origin/main`
(post-#811), not off the skills branch, so there was zero tangle and zero conflict. The loop worked: a
mistake → captured as an idea → applied next increment. **System improvement:** that branch-base
discipline is still only in a session log + idea, not yet a *binding* rule — it should graduate into the
journal's Quick-ref "Orient" row (next to the git-fetch-first rule it complements), so it's enforced by
orientation rather than re-learned. Routed as a journal candidate-rule (free to add — process memory).

## Doc audit (Q-0104)

- `check_quality --full` green; `check_architecture --mode strict` 0 errors; `check_docs --strict`
  green.
- Plan Execution log: personas DONE (#812), **§3c COMPLETE**; ▶ RESUME HERE repointed to the PR-2
  remainder (modes/triggers/hooks/templates) → then PR 3. Roadmap's two substrate mentions advanced to
  #812 / "§3b/§3c complete".
- **current-state.md untouched** — subtree work tracked in the plan (the #789/#791–793 precedent).
- Honored **Q-0124** (did not run the reconciliation pass — routine's job) throughout the session.

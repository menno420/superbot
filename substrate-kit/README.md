# substrate-kit

A portable, self-improving **agent-memory substrate**: everything a fresh
repository needs for AI agents to work correctly with little steering —
planted in one step, learned staged, and self-maintaining after that.

Extracted from the SuperBot project's agent workflow (session logs, question
router, decision ledger, doc-hygiene checkers, reflection loop) and rebuilt as
a zero-dependency kit. **`substrate-kit` is a placeholder name** — the
published name is the owner's call at extraction; it is swappable in one place
(`pyproject.toml`).

## What it does

- **Staged onboarding.** A question-bank interview fills content *slots*
  (project name, layers, verify command, ownership, owner style …) that render
  the project's binding docs from templates. No human around? The agent
  self-answers **provisionally** — assumptions are flagged, never silently
  trusted, and never count toward graduation.
- **Three integration modes** pace adoption: `observe` (impose nothing, watch,
  then *propose* a workflow), `guided` (one practice at a time: session logs →
  idea lifecycle → question router → session-enders → gates), `active` (full
  workflow from session 1). The mode changes real behavior: question quota,
  orientation depth, trigger mandates, actuator gating, graduation.
- **A nervous system.** Triggers (critical-slot grace, blocking questions, doc
  drift, staleness, unowned areas) fire mandatory-question sessions; a rolling
  **reflection buffer** forward-injects learned lessons into every session's
  orientation; an **episodic index** makes past sessions searchable by tag;
  a **maintenance loop** handles compaction (State Delta snapshots),
  blocking-question escalation, and promotion-rights downgrades.
- **An independent-review seam** (provisioned, not hard-wired): anti-anchor
  payloads (proposition + evidence only — no author confidence), an external
  verdict flow (`review build` / `review confirm`), objective-slot
  confirmation, and escalation on dissent. Wire any reviewer model; with none
  configured, payloads simply accumulate for the owner.
- **A context-economy engine**: config-driven document classes + retention
  windows, budget gauges (including the ≤7,000-word orientation boot budget),
  an inbound-reference pass, harvest-gated deletion (triple filter: harvested
  AND past window AND zero references), tombstone shards, and a generalized
  retention-policy **simulator** — the kit ships the search, each repo derives
  its own constants (`economy recipe`).
- **Checkers** that make the rules enforcing, not hortatory: doc hygiene
  (badges / links / reachability), session-log completeness, the `[D-NNNN]`
  **decisions ledger** (machine-readable `supersedes:`, stamp discipline), the
  AST **namespace/shadowing guard**, config-driven **seam-authority fences**,
  and the orientation word budget — all under one `check --strict`.
- **Claude Code integration, staged never imposed:** four hooks (PreToolUse
  stance guard, SessionStart orientation injection, PostToolUse edit advisor,
  Stop-check advisor), a skill pack, and read-only personas are emitted under
  `.substrate/` for the host to install deliberately. The kit **never writes a
  live `.claude/` tree** unless explicitly asked (`adopt --include-claude`).

## Install / adopt (one step)

Copy the single file — stdlib-only, no install — into a repo and run:

```
python3 bootstrap.py adopt
```

That plants (skip-if-exists, never clobbering): `CONSTITUTION.md`, the binding
doc skeletons (`docs/architecture.md`, `ownership.md`, `runtime_contracts.md`,
`collaboration-model.md`, `helper-policy.md`, `repo-navigation-map.md`,
`ai-project-workflow.md`, `owner-profile.md`), the living ledgers
(`docs/current-state.md`, `docs/decisions.md`, `docs/question-router.md`,
`docs/ideas/README.md`), the orientation router (`docs/AGENT_ORIENTATION.md`),
session-log scaffolding (`.sessions/`), `.session-journal.md`, and
`project.index.json` — and stages the `.claude` material, hook settings
template + fill-table, and a CI example under `.substrate/`.

Then let the staged learning run:

```
python3 bootstrap.py ask                 # the mode-paced question list
python3 bootstrap.py answer <slot> <answer...>
python3 bootstrap.py render              # re-render docs as slots fill
python3 bootstrap.py mode guided         # observe | guided | active
python3 bootstrap.py check --strict      # every checker, one gate
```

Alternatively `pip install ./substrate-kit` gives the same CLI as
`substrate-kit` (see `pyproject.toml` for the placeholder-name note).

## The staged-learning contract

Stage 1 (`integration`): every session asks a few targeted questions (the mode
sets the quota). Graduation to `steady` is **adaptive, not a session count**:
critical slots ≥80% *confirmed* (provisional never counts — the anti-gaming
floor also rejects hollow answers), zero blocking questions open, and a quiet
streak with no new mandatory questions. `observe` mode never auto-graduates —
it proposes, the owner decides. Blocking questions left unanswered escalate
onto `open_questions` and hold graduation until answered.

## Daily loop

```
python3 bootstrap.py session-start   # orientation: status · stance · owner style ·
                                     # learned lessons · triggers · practices · gauges
...work...
python3 bootstrap.py session-close   # mine reflections · index the session ·
                                     # advisories · KPI footer
```

`metrics` emits the KPIs (completeness, assumption-confirmation rate, open
questions …) that the graduation signal and the self-improvement acceptance
gate read. `maintain` reports triggers + economy + ledger state and runs
compaction when due. Actuators (economy prunes, promotions) apply only when
the mode allows it **and** `promotion_rights` is `promote` — otherwise
everything is a dry-run proposal.

## Layout

```
substrate-kit/
  dist/bootstrap.py     # THE distribution: one stdlib-only self-contained file
  src/build_bootstrap.py# manifest -> artifact builder (regenerate after edits)
  src/engine/           # source of truth (lib, interview, loop, economy,
                        # checks, hooks, stances, skills, agents, ledger,
                        # adopt, contextpack, render, cli)
  src/templates/        # the 16 content templates ADOPT_PLAN plants
  pyproject.toml        # pip-installable form (placeholder name)
```

Tests live in the host repo at `tests/unit/substrate_kit/` during the in-repo
proving phase and move to `substrate-kit/tests/` on extraction.

## Rules the kit holds itself to

- stdlib-only engine; no `print` / `assert` / `subprocess` in engine code.
- Every file write is atomic; state mutations are transactional.
- The kit **stages**, the host installs — no live `.claude/` writes.
- Fail open everywhere an agent session could be blocked (hooks, orientation).
- The guardrail refuses to operate on the kit's own tree.
- `src/engine/` is the source of truth; `dist/bootstrap.py` is generated —
  regenerate with `python3 substrate-kit/src/build_bootstrap.py` (CI pins it).

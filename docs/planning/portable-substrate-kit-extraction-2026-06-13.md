# Portable substrate-kit — extraction plan (approved 2026-06-13)

> **Status:** `plan` — **APPROVED & finalization-ready.** Owner-approved via ExitPlanMode on
> 2026-06-13 after **10 external-review rounds**. **Not binding** — source code and merged PRs win
> over this file. This is the **canonical durable copy**: the plan was authored in a throwaway
> plan-mode scratch file and is preserved here so any future session can pick it up.

**Origin ideas (this plan executes them):**
[`../ideas/portable-agent-memory-package-2026-06-12.md`](../ideas/portable-agent-memory-package-2026-06-12.md)
(the externalization vision) + [`../ideas/autonomous-improvement-loop-vision-2026-06-12.md`](../ideas/autonomous-improvement-loop-vision-2026-06-12.md)
(the self-improving loop it runs).

## Why this document exists — read me first

**What this is.** The concrete, testable, executable plan to extract this repo's *real artifact* —
the cross-session memory + self-improving agent workflow (`.claude/CLAUDE.md`: *"the bot is the
substrate; the real artifact is this workflow"*) — into a **portable, single-file, stdlib-only kit**
that bootstraps the same loop in any project and *learns* that project's content through a staged
onboarding interview, rather than shipping rigid assumptions.

**Why it's documented here** (not left in chat or a plan-mode file). This is a multi-PR effort that
spans sessions, hardened through **ten independent review rounds** (ChatGPT deep-research · Gemini ·
Grok · ChatGPT agent-mode · Hermes ×2 · a cross-agent batch · ecosystem/prior-art research · a
ChatGPT productization review). That reasoning is expensive to reproduce; losing it to an ephemeral
plan-mode file would force the next session to re-derive everything. Persisting it — with its full
accept/decline provenance — is the "durable memory / leave the next session better-equipped" mandate
in `.claude/CLAUDE.md`.

**How to use it next session.**
1. Read this doc + the two origin idea docs above.
2. Execution is **already owner-approved** — do **not** re-plan or re-open the review rounds; the
   "External review" sections (Rounds 1–10) are a *settled record*, not open questions.
3. **PR 1a + 1b are DONE, incl. the 1b tail (#789, #791–#793, #802) — resume at PR 2, the
   capability layer** (stances / skills / personas). See the **Execution log** below for what
   shipped, the exact "▶ RESUME HERE" recipe, and the CI gotchas to respect. Hermes's four
   blockers were resolved in 1a.
4. Delivery is **two-phase**: PRs 1a–3 deliver the working substrate *proven in-repo* under
   `substrate-kit/`; the public-OSS productization phase (~160–276 h) is separate and later.
5. The kit lives in a self-contained `substrate-kit/` tree and **never mutates superbot's live
   `.claude/` / `docs/`** — superbot is only the proving ground.

**On the version markers below.** The `> **Status:** Plan v9 …` line that follows is the plan's
*internal* revision marker (v1 → v9 across the review rounds); the `plan` badge above is this
*document's* lifecycle badge. Everything from the next heading down is the approved plan verbatim.

## Execution log

- **PR 1a (2026-06-13) — DONE, green in-repo.** Skeleton + locked contracts shipped under
  `substrate-kit/`: `engine/lib/{atomicio,config,state,guardrail}.py`, `engine/cli.py`,
  `src/build_bootstrap.py`, and the generated stdlib-only `dist/bootstrap.py` (the `--simulate`
  smoke passes). 23 tests green; black/isort/ruff/check_docs green; the full suite still collects
  clean (9360). **Verified plan deviation:** the kit's tests live in **`tests/unit/substrate_kit/`**,
  *not* `substrate-kit/tests/` — superbot's CI runs `pytest tests/` with `testpaths=["tests"]`, so it
  does **not** auto-collect `substrate-kit/tests/` (the plan's verification-section assumption was
  wrong; verified against `pyproject.toml` + the workflow). On extraction they move into
  `substrate-kit/tests/`. Also confirmed for whoever does PR 1b: `dist/` is excluded from black/ruff
  (the generated file isn't linted), `tests/` is excluded from black/ruff but **isort still checks it**
  (the repo's isort skip-glob matches nothing), and `print`/`assert`/`subprocess` (T201/S101/S603) are
  enforced on `substrate-kit/src/` — hence `sys.stdout.write` + no asserts in engine code.
  **Gotcha fixed:** `dist/` is git-ignored repo-wide, so the committed `dist/bootstrap.py` is kept
  tracked via a scoped `substrate-kit/.gitignore` negation — don't delete it expecting it to
  regenerate on clone; regenerate with `python3.10 substrate-kit/src/build_bootstrap.py`.
- **PR 1b (2026-06-13) — DONE (shipped as #791 → #792 → #793).** The staged-learning loop on the
  1a skeleton: **#791** interview engine (`engine/interview/{question_bank,stages,interview}.py` —
  the seed bank is a Python module so it embeds in the bootstrap with no parser; adaptive
  graduation `integration → steady` only on *confirmed* critical slots + a quiet streak;
  provisional self-answers never self-graduate; `ask` + interview-driven `--simulate`); **#792**
  render (`engine/render.py` `${slot}` substitution + a dual-path template loader + the `render`
  CLI); **#793** the full 6-doc orientation template set (CLAUDE / AGENT_ORIENTATION /
  current-state / session-journal / question-router / ideas-README), referencing only bank slots
  so a fully-filled interview renders zero leftovers. Single-file loop verified end-to-end
  (`init → ask`/`simulate` → `render` writes all six docs); 43 substrate-kit tests green.
- **PR 1b tail (2026-06-13) — DONE (#802).** The two stdlib checker ports, generic + config-driven:
  `lib/config.py` gained `docs_root` / `sessions_dir` / `badge_tokens` / `readpath_docs` /
  `session_markers`; `engine/checks/check_docs.py` (badge-presence + link-resolution + reachability —
  the host's ratchets + freshness rule deliberately **left behind** as project policy) and
  `engine/checks/check_session_log.py` (configurable required-marker check; current log picked by
  **mtime**, *not* `subprocess` — S603 is banned in engine code); a `check` CLI command (doc findings
  + an incomplete *existing* log gate `--strict`; a *missing* log stays advisory); both wired into
  `build_bootstrap.py` + the regenerated `dist/bootstrap.py`; `test_checks.py` (19 cases). **Also
  closed verification goal (d):** every orientation template gained a `> **Status:** `<token>`` badge
  so a host running `bootstrap check` on rendered output is badge-clean (proven by a render→check
  integration test). 62 substrate-kit tests green; `check_quality --full` green (9367).
- **PR 2 — stances (2026-06-13) — DONE (#805).** §3b, the first capability-layer increment (PR 2
  lands in green increments). `engine/stances/stances.py` — the five core stances (question /
  analysis / debug / review / plan), each with a **reading-route**, a **tool-scope** (read / run /
  edit / comment) and an **output contract**; shipped as a **Python module, not the plan's
  `stances.yml`** (the `question_bank.py` precedent — embeds in the stdlib bootstrap with no YAML
  parser). Conformance logic `action_allowed` / `is_out_of_stance` (fails **open** on an unknown
  stance) + the `stance_briefing` orientation-injection primitive; a `stance [name]` CLI (show /
  set); wired into `build_bootstrap.py` + the regenerated `dist/bootstrap.py`. `test_stances.py`
  (15 cases) incl. the `default_state`↔`DEFAULT_STANCE` invariant and the **edit-only-in-`debug`**
  safety pin ("zero out-of-stance writes"). 77 substrate-kit tests green; `check_quality --full` green.
- **▶ RESUME HERE (next session) — PR 2 cont.: skills + personas (§3c), then the rest.** With
  stances shipped, the next increment is the other two capability mechanisms: **skills**
  (`engine/skills/` generalized sources + a `build_skills.py` manifest→artifact generator emitting
  native `.claude/skills/*/SKILL.md` — starter pack: session-close · quality-gate · review ·
  repo-health · deep-research **+ new** question · analysis) and **personas** (`templates/agents/` →
  native `.claude/agents/*.md`: architect · reviewer · researcher), with the **precedence model**
  (a skill's declared capabilities override the ambient stance; stances stay advisory otherwise).
  Then the remaining PR-2 scope: the three modes' per-session behaviors; trigger/drift/staleness
  detection; the full contract-doc template set + owner-profile; templated hooks +
  `settings.template.json` (incl. the PreToolUse out-of-stance guard that calls `is_out_of_stance`) +
  a generalized session-close; simulation asserts. The CI gotchas in the entries above (tests under
  `tests/`, `print`/`assert`/`subprocess` bans on `engine/`, isort-checks-tests, **regenerate the
  bootstrap** after any `src/engine` edit, black↔ruff COM812 on awkward wraps — hoist long strings to
  constants) all still apply.

---

# Plan: Portable, self-learning agent-memory + workflow system ("the substrate, extracted")

> **Status:** Plan v9 — **executable specification, finalization-ready** (external-review Rounds 1–10:
> + Hermes final pre-execution gate). Claude is the final synthesizer. Hermes's four blockers resolved
> in-core (state-backend interface contract · two-interpreter config · autonomous-confirmation path ·
> internal PR-1 gate). **Two-phase delivery: (1) the working substrate proven in-repo [PRs 1a–3, this
> session]; (2) a distinct public-OSS productization phase [~160–276 h].** Capability layer (stances +
> skills + personas) owner-approved for v1. The "External review" sections log each round's accept/decline calls.

## Context — why this is being built

This repo's `.claude/CLAUDE.md` is explicit: *"You are building a self-improving agent
ecosystem. The bot is the substrate; the real artifact is **this workflow**"* — the docs,
journal, question-router, idea lifecycle, hooks, and self-audit loop that let an agent work
correctly across sessions with almost no human steering (the maintainer's whole input is
"continue where the previous session ended").

The maintainer wants to **externalize that artifact**: a reusable structure anyone can
download from GitHub — installable as a package *or* copied as a single file — that bootstraps
the same autonomous, self-improving loop in *their* project. There is already an idea doc for
this (`docs/ideas/portable-agent-memory-package-2026-06-12.md`) and the loop's vision
(`docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md`). This task turns that
north-star into a **concrete, testable, executable plan**.

### The core hard problem (named in the existing idea doc)

The system is **tightly coupled to its host project** (paths, architecture rules, subsystem
names). Extraction is a *mechanism-vs-content separation*, and the doc warns the result risks
being **too rigid** (one-size-fits-none) **or too empty** (a README that just says "do what we
did").

### The new insight that resolves it — the *learning stage*

The maintainer's new ask supplies the missing piece. Rather than perfectly separating mechanism
from content up front, the package ships the **mechanism + a staged, adaptive onboarding that
*learns* the project's content** by asking the user and itself structured questions across many
early sessions. The content is *grown*, not shipped. This is the bridge over the "too empty /
too rigid" gap:

- **Stage 1 — Integration & Learning (~50 sessions, adaptive — could be far fewer or more).**
  Every session asks itself + the user a few targeted questions to populate the memory and tune
  the workflow. The user picks the *integration speed* at startup (e.g. "slow integrate — keep
  working as I do, you just take notes, then propose a better workflow after N sessions" vs.
  "active adopt"). **Mandatory question sessions** fire whenever the current state requires them
  (gaps in the memory, an unresolved decision, drift). The AI independently reviews and maintains
  this.
- **Later stages — graduate to autonomy.** Once the memory is populated and the workflow tuned,
  the system shifts to the steady-state self-improving loop already proven here (idea→plan→
  implement chaining, self-audit session-enders, reconciliation cadence, independent review).

The goal: replicate *how the maintainer works* with no further input — remove planning effort
from the user so the way-of-working is reproducible.

## What already exists (exploration findings)

The system is **~70% generic mechanism, ~30% project-specific content**. It is already
~85% built in-repo and *running* (autonomous routines fire from GitHub issues). The new
work is the **staged learning onboarding**, the **mechanism/content seam**, and the
**single-file distribution form** — not re-inventing the loop.

### BUCKET 1 — GENERIC mechanism (lift near-as-is into the engine)
- **Orientation chain:** `.claude/CLAUDE.md` (working agreement) → `docs/collaboration-model.md`
  → `docs/current-state.md` (living ledger) → `.session-journal.md` (guidebook) →
  `docs/AGENT_ORIENTATION.md` (task reading-router).
- **Durable memory:** `.sessions/<date>-<slug>.md` per-session logs (6-question *context-delta*
  reflection + telemetry footer); `.session-journal-archive.md`.
- **Question router:** `docs/owner/maintainer-question-router.md` — append-only `## Q-NNNN`
  blocks (Area/Type/Priority/Status · Question · Why agents need this · Options · Safe default
  · verbatim Maintainer answer · Routing result). DISCUSS lane; UNION-merge for concurrency.
- **Idea lifecycle:** `docs/ideas/README.md` — intake → map → route → groom → outcome;
  promotion gates; "no orphaned ideas".
- **Multi-agent pipeline + handoff template + idea-state vocabulary:** `docs/owner/ai-project-workflow.md`.
- **Session-ender rituals:** one-idea (Q-0089), previous-session review (Q-0102), doc audit
  (Q-0104), backlog grooming (Q-0015), reconciliation every 20 PRs (Q-0107).
- **Generic check scripts (stdlib, portable):** `check_docs.py`, `check_session_log.py`,
  `check_current_state_ledger.py`, `check_doc_freshness.py`.
- **Generic skill:** `.claude/skills/session-close/SKILL.md` (closing-ritual driver).
- **Parametric hook infra:** `.claude/settings.json` → `claude_session_start.sh`,
  `claude_pre_edit.py`, `claude_post_edit.py`, `claude_stop_check.py`.
- **Autonomous-loop seam:** `docs/operations/autonomous-routines.md` prompts + the
  `reconcile`/`continue` issue triggers; `check_phase_gate.py` (fix vs invent); the
  independent-review seam (a *different* model breaking the Claude monoculture).

### BUCKET 2 — GENERIC-TYPE docs, project-specific content (become interview-populated templates)
- `docs/architecture.md` (layering/invariants), `docs/ownership.md` (who-owns-what),
  `docs/runtime_contracts.md` (lifecycle/failure modes), `docs/repo-navigation-map.md`
  (where-things-live), `docs/helper-policy.md` (near-fully generic — strip examples only).
- `docs/current-state.md` / `docs/roadmap.md` — generic *section schema*, living content.
- `.claude/CLAUDE.md` binding-rules section (architecture-rule slots).
- `docs/owner/maintainer-working-profile.md` — the *pattern* (capture owner voice) is generic;
  the person is not.

### BUCKET 3 — NEEDS-PARAMETERIZING (hardcoded values → config)
- `claude_post_edit.py`, `claude_stop_check.py`, `check_quality.py`,
  `check_current_state_ledger.py`, `check_reconciliation_due.py`, `.mcp.json`, `/pre-pr`
  (Python version, doc paths, current-state path, 20-PR step → a single config file).

### BUCKET 4 — Wholly project-specific (leave behind)
- `disbot/`, `tests/`, `docs/btd6/`, `docs/subsystems/`, `docs/planning/`, `docs/setup-platform/`,
  `check_architecture.py` + `architecture_rules/`, `context_map.py`, `wiring_map.py`,
  `claude_pre_edit.py`, `check_phase_gate.py` (bug-book/readiness paths), `.claude/rules/*.md`,
  `tools/agent_context/`.

### Cruft / improvable (the user's "filter what could be reworked/removed")
- **Unverified guards (Q-0105, added 2026-06-12):** `check_session_log.py`,
  `check_current_state_ledger.py`, `check_reconciliation_due.py`, `check_phase_gate.py` all
  carry "delete if unreliable" headers — graduate or drop before they become engine.
- **PAT-expiry silent failure:** routines stop firing if `ROUTINE_PAT` lapses; documented but
  unguarded — a portable kit should guard or document this prominently.
- **Non-wired brainstorm hooks** (`docs/operations/claude-code-hooks-and-plugins.md`):
  previous-session surfacing at SessionStart; pre-compaction handoff at ~700K context — both
  would strengthen the memory loop and are good engine candidates.
- **Two existing idea docs to build on:** `docs/ideas/portable-agent-memory-package-2026-06-12.md`
  (names the "too rigid vs too empty" problem + harden→seam→extract sequencing) and
  `docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md` (the loop + independent review).

## Reusable prior art found (reuse, don't reinvent)

- **`tools/agent_context/build_pack.py`** — a stdlib+`yaml` *manifest → generate-artifacts*
  script: reads `docs/agent/index.yml`, renders structured markdown packs, supports
  `--dry-run`/`--subsystem`, resolves paths via `Path(__file__).resolve().parents[N]`, and
  carries a Q-0105 provenance header. **This is the exact shape of the self-expanding
  bootstrap** — the bootstrap is "build_pack in reverse for onboarding": ship an embedded
  manifest of the *engine*, write it out, then run an interview that incrementally fills a
  *project manifest* which drives generation of the project-specific template docs.
- **`docs/agent/index.yml` schema** (per-area: `folio` / `binding_docs` / `reference_docs` /
  `source_roots` / `do_not_create` / `gates` / `verification`) — a ready-made model for *what
  the integration interview captures* about a target project. The interview fills an index like
  this; generation flows from it.
- **`.claude/skills/session-close/SKILL.md`** — the closing-ritual driver to generalize; its
  hardcoded `python3.10` / `scripts/check_*` / `.sessions/` / `docs/` paths are the exact seam
  points to parameterize.
- **`.claude/settings.json` hooks** — SessionStart/PreToolUse/PostToolUse/Stop wiring; template
  with placeholders for interpreter, script paths, and doc paths.

## Proposed architecture

### Working name & placement
A new, **self-contained top-level tree `substrate-kit/`** (no collision with existing
`architecture_rules/ data/ disbot/ docs/ scripts/ tests/ tools/`). It is **liftable to its
own repo as-is** and **never mutates superbot's live `.claude/` or `docs/`** — superbot is the
*proving ground*, operated on only via `substrate-kit/examples/` and tmp dirs. Final published
package name is deferred (a later/extraction decision, not blocking).

```
substrate-kit/
├── README.md                  # what it is; "copy dist/bootstrap.py → run"
├── src/                       # readable, DRY source (maintained here)
│   ├── engine/                # MECHANISM — ships as-is, parameterized by config
│   │   ├── lib/config.py          # reads substrate.config.json (interpreter, paths, cadence, scopes)
│   │   ├── interview/             # ★ NEW: the staged-learning engine
│   │   │   ├── stages.py          #   stage state machine + adaptive graduation
│   │   │   ├── interview.py       #   runs a session's questions, routes answers
│   │   │   └── question_bank.yml  #   question library keyed by trigger/slot/audience
│   │   ├── checks/                # generic stdlib checkers, lifted + parameterized
│   │   │   ├── check_docs.py · check_session_log.py
│   │   │   ├── check_state_ledger.py · check_reconciliation_due.py
│   │   ├── hooks/                 # templated: session_start.sh, post_edit.py, stop_check.py, settings.template.json
│   │   └── skills/session-close/SKILL.md   # generalized closing ritual
│   ├── templates/             # CONTENT slots the interview fills ($PLACEHOLDER form)
│   │   ├── CLAUDE.md.tmpl · collaboration-model.md.tmpl · current-state.md.tmpl
│   │   ├── session-journal.md.tmpl · AGENT_ORIENTATION.md.tmpl
│   │   ├── question-router.md.tmpl · ideas-README.md.tmpl · ai-project-workflow.md.tmpl
│   │   ├── architecture.md.tmpl · ownership.md.tmpl · runtime_contracts.md.tmpl
│   │   ├── repo-navigation-map.md.tmpl · helper-policy.md.tmpl · owner-profile.md.tmpl
│   │   └── project.index.json     # the index.yml-analog the interview fills (per-area profile)
│   └── build_bootstrap.py     # bundles src/ → dist/bootstrap.py (manifest→artifact, à la build_pack.py)
├── dist/bootstrap.py          # ★ THE single self-expanding file (committed; stdlib-only Python 3)
├── examples/sample-project/   # throwaway target for in-repo proving
└── tests/                     # state machine, interview, bootstrap, simulation harness
```

### 1. Distribution form — the self-expanding bootstrap
`dist/bootstrap.py` is **one stdlib-only Python 3 file** that *embeds the engine + templates
inline as data* and writes them out on first run — so "copy one file" is literally true and
**fully offline** (no first-run network/supply-chain risk). It is **generated** from the
readable `src/` tree by `build_bootstrap.py` (exactly the `build_pack.py` manifest→artifact
pattern), keeping source DRY. This gives both requested form factors: *single file* =
`dist/bootstrap.py`; *package* = the `src/` tree (a later `pyproject.toml` adds `pip install`).
**Deps: none** — `json` for state/config, `string.Template` (`$PLACEHOLDER`) for templates,
`pathlib`. (We deliberately avoid `yaml` in the bootstrap, unlike `build_pack.py`, so the copied
file needs only system Python 3.)

Bootstrap CLI: `init` · `session-start` · `session-close` · `ask` (run pending questions) ·
`status` · `mode <name>` · flags `--target DIR` (sandbox/proving) and `--dry-run`. `init` is
**idempotent**: re-runs never clobber filled content; they advance the state machine.

**`substrate.config.json` key fields (Hermes-final).** `interpreter` (the kit's own code — defaults to
`sys.executable`) **and a separate `interpreter_for_checks`** (the per-target verification interpreter — e.g.
`python3.10` for superbot's CI-parity scripts): the kit invokes *its* interpreter for engine/hooks and
`interpreter_for_checks` for a host project's check suite, making the two-interpreter split explicit instead
of latent. Plus `state_dir` (default `.substrate/`, **set at `init`** and stamped with a `project_id` so a
sibling project's `.substrate/` is never mistaken for an idempotent rerun and silently clobbered), `paths`,
`cadence`, and `scopes`.

### 2. Staged-learning state machine
Durable state behind a **state-backend interface** (Round 9): **JSON+`os.replace` by default**
(single-session, copy-one-file simplicity); a stdlib **`sqlite3`** backend for the concurrent case
(parallel sessions/routines — mutable coordination state like graduation/promotions/metrics needs real
transactions, not just an atomic rename). Human memory (logs, docs, Q-blocks) stays diffable files. Default
shape in `.substrate/state.json`:
```jsonc
{ "mode": "guided",            // observe | guided | active  (adoption PACE)
  "promotion_rights": "propose", // observe | propose | promote  (Round 1: what may change w/o sign-off)
  "stage": "integration",      // integration → steady
  "stance": "analysis",        // question | analysis | debug | review | plan  (Round 7: task posture)
  "session_count": 7,
  "slots": { "project_name": "filled", "architecture_layers": "unfilled", "...": "partial" },
  "open_questions": ["Q-0003"],
  "reflection_buffer": { "active_count": 4, "last_mined": "2026-06-13" },  // Round 6: forward-injected lessons
  "graduation": { "soft_target_sessions": 50,
                  "criteria": { "critical_slots_filled_pct": 0.8, "blocking_questions": 0 } } }
```
**State-backend interface contract (Hermes-final — locked in PR 1a, commit 0).** The *interface*, not a
raw JSON shape, is the API both backends honor: `get(key)` · `set(key, value)` · `query(filter)` ·
`transaction()` (atomic multi-key) · `migrate(old→new)` + a schema `version`. **PR 1 ships the interface +
the JSON-file backend** (the default; atomic via `os.replace`); the **`sqlite3` backend is the
productization-phase implementation** — but the interface is migration-compatible from commit 0 so it bolts
on without a redesign (resolves the Round 9 ↔ §2 drift: interface + JSON now, SQLite later). The live-loop
guardrail (refuse own-repo root; never touch a live `.claude/settings.json`) is **enforced here as code in
the first commit, not left as a doc.**

**Stage 1 — Integration & Learning:** every session asks itself + the user a few targeted
questions to fill content slots and tune the workflow. **Graduation is adaptive, not a hard 50**
— it fires when *critical* slots are ≥80% filled, zero *blocking* questions remain, and N
consecutive sessions surface no new mandatory questions. The ~50 is a soft, displayed default:
a simple project may graduate at ~12; a complex one may run past 50. The AI **proposes**
graduation ("we've learned enough — here's the steady-state workflow I propose"); the user
confirms (auto-graduate-after-cooldown in fully-autonomous mode).
**Stage 2 — Steady state:** the proven self-improving loop (idea→plan→implement, session-enders,
reconciliation cadence, independent review). Integration questions taper to drift-triggered only.

### 3. The three integration modes (chosen at `init`, stored in state, changeable via `mode`)
- **observe** — AI imposes nothing; each session writes a light note, asks 1–2 *observation*
  questions, and passively profiles how the user already works. After N sessions / slot-fill it
  emits a *proposed tailored workflow* for the user to accept. (Your "take notes then propose".)
- **guided** *(your pick — the middle)* — rolls the workflow out **one practice at a time**:
  session logs first; once habitual, add the idea lifecycle; then the question router; then the
  session-enders; then the gates. Each new practice arrives with a one-line rationale, only after
  the prior is established. AI paces the rollout.
- **active** — full workflow from session 1; interview runs aggressively to fill slots fast.

### 3b. Task-stance modes — the fourth axis (Round 7, owner-decided 2026-06-13)
A *distinct* axis from the three above — not adoption-pace, promotion-rights, or stage, but the working
agent's **operational stance for the current task**. Today the agent only has plan mode (ExitPlanMode);
prior art (Roo Code's Code/Debug/Ask/Architect/Orchestrator) and hard data — context rot from ~25%
context-fill, tool-selection accuracy 43%→14% under bloated toolsets — show that **scoping reading +
toolset + output per stance** cuts context rot and misfires. The kit ships a config-driven set in
`engine/stances/` (`stances.py` + `stances.yml`); each stance declares a **reading-route** (which docs
load first), a **tool-scope** (allowed actions), and an **output contract**:
- **question** — read-only; answer concisely from memory/source; no edits.
- **analysis** — read-only deep-dive; may run read-only tools; produces findings, not changes.
- **debug** — read + run + *targeted* edits to fix a known fault; no broad refactor.
- **review** — read-only + comment; evaluates a diff against the contracts; no edits.
- **plan** — maps to existing plan mode (research + safe prototyping → ExitPlanMode).

The active stance lives in `state.json` (`"stance"`), switches via the bootstrap `stance <name>` CLI,
shows in `status`, and its reading-route + contract are **injected into orientation** alongside the
user-style block and reflection buffer. **Advisory by default** (the contract guides the agent); an
optional PreToolUse hook can warn on out-of-stance actions (e.g. an edit while in `review`). Lands in
**PR 2** (framework + the five core stances); the `state.json` field is stubbed in PR 1. **Schema follows
Roo Code's proven mode model** (role prompt + tool-scope + optional file-glob + custom-instructions),
shipped in Claude Code's **native** `.claude/` layout so stances compose with the skills + personas
proposed in Round 8.

### 3c. Skills & personas — the rest of the capability layer (Round 8, owner-decided: all three)
The other two native Claude Code mechanisms, shipped alongside stances (§3b):

**Skills** — invokable `SKILL.md` capabilities (the *invoke-a-capability* counterpart to a stance's ambient
posture). The kit ships `engine/skills/` (generalized skill sources) + a generalized `build_skills.py` that
emits native `.claude/skills/*/SKILL.md` from source docs — **the same manifest→artifact engine as
`build_bootstrap.py`**, so skills are generated, not hand-maintained, and load progressively (metadata-first).
**Starter pack:** the generic superbot skills — `session-close`, `quality-gate` (← pre-pr), `review`
(← architecture/code-review, generalized), `repo-health`, `deep-research` — **plus new** `question` and
`analysis` skills. Native format ⇒ portable to Cursor/Codex/Gemini CLI for free.

**Personas / sub-agents** — spawnable read-only specialists in native `.claude/agents/*.md`, generalized from
superbot's `superbot-architect` + `mutation-boundary-auditor`. Starter set as interview-populated templates
(`templates/agents/`): **architect** (design/layer specialist), **reviewer** (independent critique — wires to
the §6 review seam), **researcher** (read-only deep exploration); each persona's binding sources are filled
from the project's own contract docs.

**Composition + precedence (Hermes-final).** Stance = posture · Skill = invoked procedure · Persona = spawned
specialist — all emit into the project's native `.claude/` tree (Claude-Code-native, cross-agent-portable).
**Precedence rule:** a stance gates *ad-hoc* actions, but a **skill's explicitly-declared capabilities take
precedence over the ambient stance** — each skill declares what it needs (e.g. `session-close` declares
`writes: [session-log]`), so it can write even while the stance is `review`. Stances stay advisory for
anything a skill hasn't declared. Lands in **PR 2** (the capability + content PR).

### 4. Mandatory-question sessions (fire "whenever the current state requires it")
Engine checks triggers at session start; if any fires, the session is flagged a
*mandatory-question session* and pulls the relevant questions from `question_bank.yml`:
- a **critical** slot still `unfilled` past its grace period (e.g. architecture model unknown after 3 sessions);
- a **blocking** open question unresolved; **drift** (a checker flags ledger/doc inconsistency);
- **staleness** (ledger/reconciliation past threshold); a **new repo area** with no ownership/folio entry.

Questions have two audiences: **user-facing** (asked via the agent, answer preserved verbatim as
a Q-block in the generated `question-router.md`, then its `routing` field populates the target
slot/doc) and **self** (the AI asks *itself*, records its best inference as a flagged *assumption*
with confidence, surfaced later for user confirmation). This is what makes it never block when the
user is absent — it records assumptions, flags them, moves on. `question_bank.yml` entry:
`{id, slot, trigger, audience, prompt, routing, priority}`. **This reuses the existing Q-block
router mechanism exactly** — the interview is a structured front-end to it. **Dual-write disambiguation
(Hermes-final):** interview/agent-generated blocks carry an explicit `Type: agent-assumption` (or
`interview-captured`) tag vs. a human's `owner-decision`, so the meta-reflection miner never confuses an
unconfirmed assumption with a maintainer decision when scoring confidence.

### 5. Mechanism/content seam (the concrete keep/templatize split)
- **ENGINE (lift + parameterize):** the 4 stdlib checkers; the hook scripts + settings template;
  the session-close skill; **+ the new `interview/` engine**; `lib/config.py` (absorbs every
  hardcoded `python3.10` / path / `20`-PR cadence into `substrate.config.json`).
- **TEMPLATES (interview-populated):** the orientation chain, idea-lifecycle README, question
  router, ai-project-workflow, **and the generic-TYPE contract docs** (architecture / ownership /
  runtime_contracts / repo-nav / helper-policy) + owner-profile + `project.index.json`.
- **LEFT BEHIND:** `disbot/`, `tests/`, BTD6 docs, `check_architecture.py` + `architecture_rules/`
  (the kit ships a *generic layer-rules scaffold* the project fills, not superbot's checker),
  `context_map.py`, `wiring_map.py`, `check_phase_gate.py` (bot-path-coupled), `.claude/rules/*`,
  `tools/agent_context/` (superbot-subsystem packing).

### 6. Self-review & maintenance loop (model-agnostic)
Generalize what already runs here: **context-delta mining** (a `review` step mines recent session
logs and promotes recurring gaps into the orientation/docs); **reconciliation cadence**
(config-driven N); a **config-driven phase gate** (fix-phase vs invent-phase keyed to the
project's own issue source); and the **independent-review seam** shipped as a *seam, not a model
binding* — docs for wiring a *different* model (Hermes/GPT/Gemini, Claude-fallback) with the
"unverified → calibrate against known-answer issues before trusting its dissent" discipline.

**Forward Reflection Buffer (Round 6):** the meta-reflection miner writes high-signal "what worked /
what failed / why" lessons to `.substrate/reflections.json` (a small rolling buffer, default 5; each
`R-NNNN` with evidence + `superseded_by`), and the engine **forward-injects** the active lessons into
every new session's orientation (after the user-style block) — the Reflexion pattern made persistent
and active. Pruned via the deprecation convention; in autonomous mode only *confirmed* lessons inject
(provisional stay buffer-only, per promotion-rights). **Conflict-resolution tiers:** a reviewer
contradiction first tries **deterministic evaluation** — if it touches an asset with a validation
script (broken syntax, unlinked doc), the *script's* result rules and no human is bothered; only a
**structural/workflow** contradiction blocks, rolls back via the atomic-write path, and escalates to
a `## Q-NNNN (BLOCKING)` entry. Compaction triggers on **~700K tokens *or* 20 sessions**.

**Memory-conventions meta-memory (Serena pattern, Round 8):** the kit seeds a `memory_conventions` doc — a
*memory about how to write and consolidate memory* — that governs the miner, the reflection buffer, and the
deprecation pass, so consolidation style stays consistent as the project's memory grows.

**Autonomous-mode confirmation path (Hermes-final — breaks the provisional-assumption deadlock).** "Provisional
until *user*-confirmed" deadlocks a no-human run (nothing confirms → nothing graduates → the reflection buffer
injects nothing → the run learns nothing). Resolution: (1) the **independent-review seam doubles as the
autonomous confirmer** — for *objectively-checkable* assumptions a different model verifies against evidence and
promotes provisional→confirmed; (2) subjective/structural ones keep promotion-rights capped at `propose`
("learn + propose, never self-promote"); (3) crucially, **provisional lessons still inject** into orientation
(clearly flagged `provisional`) so the autonomous run *does* learn — provisionality gates *promotion to binding*,
not *injection for learning*. **Review-seam scope honesty:** the seam is **structurally provisioned (docs +
payload contract + promotion gating) but not wired to a live reviewer until the productization phase** — judge
it as a seam, not a running integration.

## Filtering verdict (your explicit ask: keep / rework / drop)
- **KEEP-AS-IS (lift, light parameterize):** orientation chain, idea lifecycle, question router,
  session-close ritual, the 4 stdlib checkers, hook wiring, session-log + context-delta schema,
  multi-agent pipeline + handoff template, the session-ender rituals (one-idea / prev-review /
  doc-audit / grooming / reconciliation).
- **REWORK/GENERALIZE:** `check_architecture.py` → generic layer-rules scaffold; `check_phase_gate.py`
  → config-driven issue source; all hardcoded interpreter/paths → `substrate.config.json`;
  `maintainer-working-profile.md` + the contract docs → interview-populated templates.
- **DROP / LEAVE-BEHIND:** `disbot/`, `tests/`, BTD6 everything, `context_map.py`, `wiring_map.py`,
  `tools/agent_context/`, `.claude/rules/*`, bot-specific CI workflows.
- **Re-evaluate before lifting:** the four unverified Q-0105 guards (`check_session_log`,
  `check_current_state_ledger`, `check_reconciliation_due`, `check_phase_gate`) carry "delete if
  unreliable" headers — graduate the proven ones, drop the rest rather than exporting shakiness.
  Also fold in the two non-wired but valuable hooks (previous-session surfacing at SessionStart;
  pre-compaction handoff) as engine candidates.

## Implementation phases (prove-in-repo; 2–3 PRs, first = foundation)
Per repo rules, **approval = execute this session**; PR 1 lands now, PRs 2–3 build on it.
**Scope note (Round 9):** these 3 PRs deliver the **working substrate proven in-repo** — *not* a finished
public package. Public-OSS **productization** (LICENSE/README/CONTRIBUTING/SECURITY, a 3.10–3.13 CI matrix,
the SQLite state backend, `pyproject.toml`/`zipapp` packaging, privacy baseline, GitHub-App auth, SBOM) is a
**distinct, larger later phase** (~160–276 h; ChatGPT Round 9's milestone model) — kept separate so "3 PRs"
is never mistaken for "released package."

**Pre-PR-1 gating checklist (Hermes-final #10):** before PR 1a, confirm the two recorded superbot bugs can't
red the kit's CI — the `session-close/SKILL.md` line-14 drift is **prose** (not run by `check_quality`, so
harmless to CI) and `.python-version` (3.13) is **not** a `check_quality` / `code-quality.yml` input (CI sets
3.10 explicitly via `setup-python`), so it's harmless noise, not a CI-breaker. Both deserve a one-line cleanup,
but **neither gates PR 1**. (Also closes Hermes's polish question on whether `.python-version` is a real bug.)

- **PR 1a — Skeleton + locked contracts (independently green & mergeable; Hermes-final #1).** Stand up
  `substrate-kit/`; implement `lib/config.py` (incl. the `interpreter_for_checks` / `state_dir` / `project_id`
  schema), the **state-backend interface + JSON backend** with the atomic-write helper (`*.tmp`→`os.replace`),
  the **live-loop guardrail in code** (refuse own-repo root; never touch a live `.claude/settings.json`),
  `build_bootstrap.py` + generated `dist/bootstrap.py`, the `--simulate 1` smoke, and CI wiring. **This PR must
  be green and mergeable on its own** — it locks the schema + state interface *before* anything writes against
  them, so a config↔interview mismatch can't hide until after a giant merge.
- **PR 1b — Interview engine + core templates on the proven skeleton.** `interview/stages.py` (state machine),
  `interview/interview.py`, the initial `question_bank.yml` (mode-select + ~10 core questions + the curation
  header), `project.index.json` schema, the `.substrate/episodic_index.json` stub (session→tags+slug), the
  **two cleanest** stdlib checkers (`check_docs`, `check_session_log`; ledger/reconciliation/phase ports move to
  PR 2), the core template set (CLAUDE / current-state / session-journal / AGENT_ORIENTATION / question-router /
  ideas-README), `examples/sample-project/`, the simulation harness, and `substrate-kit/README.md`. Builds only
  on the green 1a contracts. *(`build_bootstrap.py` treats `build_pack.py` as **inspiration only, not a trusted
  reference** — it's Q-0105-flagged — and carries its own provenance header + the embed-recursion test.)*
- **PR 2 — Capability layer + modes + triggers + full templates + hooks (the largest PR; lands in green internal increments per Hermes).** The three
  modes' per-session behaviors; **the full capability layer — §3b stances (`engine/stances/` + five stances + `stance` CLI + injection), §3c skills (`build_skills.py` + native `SKILL.md` starter pack) and personas (`templates/agents/` → `.claude/agents/`)**; trigger/drift/staleness detection; the full contract-doc template
  set + owner-profile; templated hooks + `settings.template.json` + generalized session-close;
  simulation asserts mode/stance behaviors, skill-generation validity, + graduation.
- **PR 3 — Self-maintenance loop + independent-review seam + distribution polish.** Context-delta
  review routine + reconciliation cadence (generalized); config-driven phase gate; model-agnostic
  review-seam docs + calibration discipline; quickstart, `pyproject.toml` (pip form), extraction-prep.

## Verification (how we test it end-to-end)
- `python3.10 -m pytest substrate-kit/tests/ -x -q` — state machine, interview routing, bootstrap idempotency.
- **Simulation harness** (`substrate-kit/tests/simulate.py`): `init` into a tmp dir, then drive N
  scripted sessions feeding canned answers, asserting (a) slots fill, (b) mandatory-question
  triggers fire exactly when expected, (c) graduation fires at the right point per mode, (d) the
  generated docs pass the engine's own `check_docs`.
- Manual smoke: `python3.10 substrate-kit/dist/bootstrap.py init --target /tmp/al-demo && … status`.
- **CI parity (it lives in-repo):** `python3.10 scripts/check_quality.py --full` (CI mirror) must
  stay green, and `python3.10 scripts/check_docs.py --strict`.
- **CI coverage of `substrate-kit/` from commit 1 (Hermes #1):** `substrate-kit/tests/` is collected by the
  existing pytest run (which CI already invokes via `check_quality --full`), including a
  `dist/bootstrap.py --simulate 1` smoke — so the generated bootstrap is validated on every commit,
  never left to rot.
- **Two explicit predicates (Hermes-final — #3 split):** **(1) Merge predicate** — a PR is mergeable only if
  `python3.10 -m pytest substrate-kit/tests/ -q` is green, the `dist/bootstrap.py --simulate 1` smoke passes,
  **and the generated output carries no leftover `$PLACEHOLDER` tokens** (a build-time grep gate). **(2)
  Autonomy-increase predicate** — raising promotion-rights additionally requires
  `substrate-kit/tests/test_graduation_no_gaming.py` green **and** KPI delta ≤ baseline (no regression). The
  merge gate guards *every* PR; the autonomy gate guards *self-promotion*.

### Integration risks (flagged, with resolutions)
- **CI lint scope:** superbot's `check_quality` runs black/isort/ruff over `.` (minus `tests/`,
  `.github/`), so **`substrate-kit/*.py` IS linted** — the PostToolUse hook auto-formats; the generated
  `dist/bootstrap.py` must be emitted black-clean (build step formats its output). `.tmpl` files
  aren't `.py`, so they're untouched.
- **mypy:** CI's mypy is scoped to `disbot/` only — `substrate-kit/` won't be type-checked by CI, but we
  keep it clean anyway.
- **`check_docs` reachability:** `substrate-kit/README.md` could be flagged an orphan. Resolution: link
  it from the `portable-agent-memory-package` idea doc (making it reachable) and treat `substrate-kit/`
  as a self-contained subtree; `.tmpl` files aren't scanned as docs.
- **Deps:** stdlib-only in `dist/bootstrap.py` (verified the lifted checkers are stdlib-only) — no
  new CI dep, no reddening. `yaml` is used only in `src/` dev tooling, gated like other dev deps.

## Design corroboration & safety refinements
An independent design pass converged on this same architecture (separate top-level tree;
ENGINE/TEMPLATES/BOOTSTRAP split; stdlib-only embedded single file; `state.json` machine;
adaptive graduation; three modes; Q-block-router reuse for questions; model-agnostic review
seam; prove-in-`examples/`). It sharpened five points, folded in here:

- **Structural live-loop guardrail:** the kit owns its own `.substrate/hooks.json` shim and
  **never edits a live `.claude/settings.json`**; the engine **refuses to operate on a tree whose
  root is the kit's own repo** unless `--target` points inside `examples/` or a temp dir — making
  "don't disrupt superbot's running loop" a *mechanical guarantee*, not a discipline.
- **Anti-gaming graduation:** completeness counts only **non-placeholder** content (no `$SLOT`
  marker left AND length above a **per-slot floor** — a configurable minimum char-count + required-structure
  check per slot type, defined in `question_bank.yml`, not one global number); **self-answers count as
  *provisional*** until confirmed (via the §6 autonomous confirmation path — other-model verify, else
  `propose`-capped) — so an autonomous run can't graduate itself on unconfirmed assumptions alone.
- **Self-answer convention:** when no human is live, the AI self-answers from the codebase,
  records it in the Q-block prefixed `ASSUMED (unverified):` with its evidence, fills the slot
  *provisionally*, and sets `Status: Awaiting maintainer confirmation` (mirrors the live
  "Decisions made alone" reflection + the Q-0105 unverified-until-confirmed rule).
- **One-file ergonomics:** `init` **unpacks** the engine to editable files by default, with an
  `--inline` fallback for the strict one-file purist; `dist/bootstrap.py` also gains `--simulate N`
  (run N synthetic sessions for CI/proving). A `mode <x>` switch appends a router Q-block recording
  the change + date (audit trail).
- **Ground-truth note (interpreter — sharpened, Round 5):** *two* interpreters, never conflated.
  **(a) The kit's own code** never hardcodes a version — it invokes `sys.executable` /
  `config.interpreter` (defaults to the running Python), so it works on any host (Hermes saw one at
  3.11.15). **(b) Verifying *superbot* in-repo** stays pinned to `python3.10` — the binding CI-parity
  rule (`code-quality.yml`), not drift; `.python-version`'s 3.13 is the lone real inconsistency and we
  follow CI (3.10). Naively "removing the `python3.10` strings" from superbot verification would
  *break* CI parity — so we don't; the discipline is per-target, not global.

## Naming & low-stakes calls (decided, not blocking)
Working dir is now the **placeholder** `substrate-kit/` (was `agent-os/`; the design pass used
`agentkit/`). **Renamed because `agent-os` collides head-on with the prominent `buildermethods/agent-os`**
("spec-driven development with AI coding agents"), plus `framerslab/agentos` and `OmoiOS` — a misleading
anchor for a circulating doc. `substrate-kit/` · `.substrate/` · `substrate.config.json` are **non-final
placeholders**; the **published name is the owner's branding call at extraction**, and must clear an
availability check against the crowded neighborhood (agent-os, agentkit, claude-mem, spec-kit,
get-shit-done, shotgun, atomicmemory, gitagent, Letta agent-file). Embed-vs-fetch → **embed** (offline
integrity). Unpack-vs-inline → **unpack by default**, `--inline` fallback. Reversible calls; pick and
proceed per the repo's "pick one and implement" rule.

## External review — Round 1: ChatGPT deep research (integrated 2026-06-13)

**Process.** The maintainer is circulating this plan to multiple independent models
(ChatGPT deep-research ✓ → ChatGPT agent mode, Gemini, Grok) plus a visual PDF, with
**Claude as the final synthesizing reviewer**. This section records what Round 1 changed.

**Framing correction (the key reviewer note).** The report is high-quality but answers a
*different question* than this project poses. It treats "self-improving AI" as **model
training/serving efficiency** (RLHF/DPO, LoRA/QLoRA, Chinchilla, distillation, MoE,
FlashAttention/PagedAttention, accelerators, HELM/MLPerf). **This project trains no model and
serves no weights.** Its "learning" is (a) the *workflow substrate* capturing a project's
context via the staged interview, and (b) the self-audit loop promoting recurring gaps into
better docs/orientation/tooling. That entire training/serving body is therefore **out of scope
for v1** — a reference only *if* a future layer ever fine-tunes or routes between models (the
model-agnostic review seam is the sole light touchpoint).

**Genuinely valuable — integrated.** The report's real gift is an *evaluation + governance lens*
the draft under-specified (it was strong on mechanism/onboarding, light on measurement and
promotion-rights). Six additions, all stdlib-only / no new deps / proportionate:

1. **Promotion-rights axis, separate from onboarding mode** *(→ PR 2/3)*. The report's "three
   promotion levels — may-observe / may-propose / may-promote-under-conditions" is a *different
   axis* from our onboarding modes (observe/guided/active = adoption *pace*). Add an explicit
   **autonomy/promotion-rights config**, seeded from superbot's existing boundary (Q-0106
   docs-free/config-asks; CLAUDE.md propose-don't-apply; self-merge-small vs needs-review-substantial).
   The kit ships this as a first-class gate: *what* the agent may change without sign-off,
   decoupled from *how fast* it adopts the workflow.
2. **Retained workflow-regression suite** *(elevates the PR 1 sim harness)*. Formalize
   `--simulate` into a *named, retained* suite every kit change must pass: generated docs pass
   `check_docs`; state transitions hold; graduation can't be gamed; assumptions stay provisional.
   Principle: **"first make it measurable, then make it more autonomous"** → a graduation
   precondition (no autonomy increase until the suite + KPIs exist).
3. **Two explicit feedback circuits** *(framing)*. Separate the **work-quality circuit** (CI,
   checks, eval suite) from the **governance circuit** (router audit-trail, promotion-rights log,
   assumptions pending confirmation). The self-maintenance loop reads both.
4. **Machine-readable router metrics** *(→ PR 2)*. A light engine parser over the generated Q-block
   router emits KPIs — open/blocking-question count, resolution rate, assumption-confirmation rate —
   feeding the completeness/graduation signal. (`question_bank.yml` is already machine-readable;
   this extends it to the *generated* router.)
5. **Workflow KPIs / telemetry** *(→ PR 3)*. Extend the session-log telemetry footer into a small
   KPI set: memory-completeness %, assumption-confirmation rate, rule-trip rate, revert/rollback
   rate, ideas contributed/groomed — the substrate-relevant analogues of the report's KPI matrix
   (its accuracy/latency/forgetting/cost metrics don't apply: no model).
6. **Session memory as episodic memory** *(→ PR 3)*. Lightweight **labels + a simple stdlib index**
   over `.sessions/` logs so past sessions are retrievable by topic (a tag index, not a vector DB) —
   upgrading "grep on demand" without adding deps.

**Explicitly set aside (out of scope for v1; recorded so later rounds don't re-litigate):** all
model-training/serving/benchmark material above; EU AI Act / high-risk-system compliance
(over-weighted for a dev-workflow template — revisit only if this becomes a broadly *published*
package, and then as a docs/governance posture, not engineering).

**Net effect on the plan:** architecture and PR 1 scope are unchanged; the additions land mostly in
PRs 2–3 and one (the retained suite) formalizes a PR 1 item. The plan moves from "self-improving
*mechanism*" to "self-improving mechanism **that is measurable and bounded**" — which is the report's
one durable, on-target contribution.

## External review — Rounds 2–3: Gemini + Grok (integrated 2026-06-13)

**Both rounds landed notably more on-target than Round 1** — they critiqued *this* substrate, not
generic ML training (the tightened framing worked). Grok's 2026 research corroborates the core:
file-based episodic + reflective memory with lightweight indexing **outperforms heavy "OS-paging"
frameworks (MemGPT/Letta) and vector DBs** in real use, zero model training — and names our exact
risks (over-engineered retrieval, graduation-gaming, silent drift, cold-start rigidity) as the
field's known failure modes, all already guarded here. No prior art matches the full combination
(single-file stdlib bootstrap + staged interview that *grows* project content + self-audit loop +
promotion-rights + model-agnostic seam).

**Accepted — high-value adds (the genuinely new catches):**

1. **Atomic state writes** *(→ PR 1, `lib/config.py`)*. All `state.json`/ledger mutations write
   `*.tmp` then `os.replace()` (atomic rename) — a crashed mid-write session can't brick the loop.
   Best robustness catch of the round; cheap, stdlib.
2. **Memory deprecation / unlearning** *(→ PR 3, new)*. The genuinely missing piece: when a rule or
   decision changes, stale Q-blocks/log references become "conversational poison." Add a
   `[DEPRECATED]`/superseded-by convention; the context-delta miner and orientation chain **skip
   deprecated memory**, and the self-audit loop can tag it. Long-running correctness depends on this.
3. **Episodic index → PR 1** *(moved up; 3-way consensus)*. At session-close, extract 3–5 tags + a
   summary slug into `.substrate/episodic_index.json` (session→tags) — retrieval-by-topic without
   grep-everything. Was PR 3; all three reviewers flagged it foundational.
4. **Meta-reflection miner** *(→ PR 3, sharpens §6)*. Per-session / on-drift: "from the last N logs +
   open questions, what recurring patterns, gaps, or ideas emerge?" → auto-promote high-confidence
   ones into the idea lifecycle / new Q-blocks. The **"prompts itself to generate ideas"** piece — the
   engine analog of superbot's one-idea (Q-0089) + prev-review (Q-0102) rituals, on existing
   context-delta mining.
5. **User-style injection** *(→ PR 2/3)*. Once the owner-profile slot fills, inject a concise
   `user_style` block into session orientation (e.g. "direct, bullets-first, respect invariants,
   actionable only"). The concrete **"tunes in to how I work"** mechanism the maintainer asked for.
6. **Procedural-memory slot category** *(→ PR 2)*. Treat learned *procedures* (the owner's PR-review
   rhythm, release ritual) as a first-class interview slot type rendered into orientation — a new
   slot kind alongside the contract docs, not a new mechanism.
7. **Pre-compaction "State Delta"** *(→ PR 3, sharpens the flagged handoff hook)*. Before the ~700K
   compaction handoff, compress the session's episodic memory into a dense delta appended to the
   ledger (semantic memory), then archive the raw log — countering "lost-in-the-middle" decay in long
   autonomous runs.
8. **Anti-anchor-bias review payload** *(→ PR 3, review seam)*. The payload to the independent
   reviewer states **proposition + evidence only**, stripping the primary model's confidence/commentary
   — else the second model anchors and rubber-stamps "ASSUMED (95%)". Sharp and on-target.

**Resolved — Gemini's open question (conflict-resolution flow).** When the independent reviewer
*contradicts* the primary's proposal it does **not** auto-resolve either way: the contested
proposition is held **provisional**, both positions + evidence recorded as a **blocking Q-block**
(governance circuit), surfaced for owner decision. In fully-autonomous mode an unresolved
contradiction **downgrades the change to propose-only** (cannot self-promote) until cleared —
leveraging the promotion-rights axis. Dissent becomes a *gate*, not a tie-break.

**Resolved — a Gemini ↔ Grok tension (retrieval depth).** Gemini suggested stdlib **BM25/TF-IDF**
over `.sessions/`; Grok's research warns **over-engineered retrieval is a top failure mode** and
file-based + light indexing wins. Resolution: **v1 ships the tag index** (#3); BM25/TF-IDF is
recorded as the **no-dep scaling path** *only if* tag retrieval proves insufficient in practice —
measured, not assumed.

**Confirmations (already in the plan; independently corroborated, now hardened to gates):** the four
unverified Q-0105 checkers must be **proven in the simulation harness before any lift** (PR 1
deliberately lifts only the two clean stdlib ones); PAT-expiry needs a prominent guard/doc; the two
non-wired hooks fold into the engine; `build_bootstrap.py` must emit **black-clean** output. Gemini
also notes the single-file stdlib form runs in constrained/mobile envs (Railway, Acode/Android) — a
real portability win given the maintainer's setup.

**Update:** ChatGPT agent-mode's final report has since landed — integrated in the Round 4 section below.

## External review — Round 4: ChatGPT agent-mode final report (integrated 2026-06-13)

**The final round, and the one needing the firmest filtering.** It is research-rich (2026 memory
systems, Reflexion, self-improvement safety, METR time-horizon) but its headline recommendation —
adopt **Mem0 / MemOS / MemoryOS / SimpleMem** for memory and **DSPy / Haystack** for orchestration —
**directly contradicts the design's load-bearing constraint** (single-file, stdlib-only, offline,
zero-dep) that Rounds 1–3, Grok's own research, and the repo ethos all independently affirmed. Those
systems are vector/graph, dependency-heavy, several commercial; their benchmark wins (LoCoMo F1/BLEU)
are for *multi-turn conversational recall* — a different problem than *project-workflow memory* —
and adopting them re-introduces exactly the over-engineered-retrieval failure mode Grok flagged.
**Verdict: borrow the principles, decline the dependencies.**

**Accepted (principles, stdlib-compatible):**

1. **Reflexion — persist reflections and inject them *forward*** *(→ PR 3, sharpens §6 + the
   meta-reflection miner)*. The most-validated technique in the report (coding pass@1 80%→91% from
   persisted self-critiques). Sharpen the miner into a small **reflection memory**: structured
   "what worked / what failed / why" entries *injected into the next session's orientation*, not
   merely logged. Highest-leverage, zero-cost add.
2. **SICA-style acceptance gate (no-regression rule)** *(→ PR 3, hardens the retained suite +
   promotion-rights)*. A self-proposed change to engine/templates is **accepted only if it passes the
   retained simulation suite and does not regress the KPIs** (memory-completeness,
   assumption-confirmation). Borrow SICA's *acceptance criterion*, not its training loop (no model
   training). Makes self-improvement safe by construction.
3. **The four self-improvement control patterns as the named safety frame** *(→ PR 3 docs)*: external
   verifiers/tests (the check suite), conservative acceptance (#2), diversity-against-overfit (the
   model-agnostic review seam — breaking the Claude monoculture *is* the diversity control),
   human/meta-agent oversight at boundaries (promotion-rights). The plan already has all four; naming
   them as the governing model is the contribution.
4. **Structured memory entries with metadata** *(→ PR 1, enriches the episodic index)*: each entry
   carries provenance, version, tags, timestamp, linked Q-IDs — richer JSON, no deps; dovetails with
   Gemini's deprecation/unlearning (version + superseded-by).
5. **Autonomous time-horizon KPI** *(→ PR 3 KPIs)*: a METR-style signal — mean sessions/turns of
   autonomous operation before a human-required intervention — added as a graduation/health indicator.
6. **Optional external-memory adapter seam** *(→ PR 3, documented, never required)*: keep the memory
   layer behind a thin interface so an advanced user *could* plug in an external store (Mem0 etc.);
   the **default stays stdlib files**. Honors the modularity point without a dependency or breaking
   the offline single-file guarantee.

**Declined (contradict the core constraint; recorded so it is settled):** Mem0/MemOS/MemoryOS/
SimpleMem as the *default* memory (kept only as the optional adapter, #6); DSPy/Haystack as the engine
framework (borrow the declarative-modular *principle* — typed module pre/postconditions, config-toggled
components, which the engine layout already follows — not the frameworks); all RL/fine-tuning loops
(STaR/RISE/SEAL/SELF/STaSC — no model training, per the Round-1 framing); multi-modal memory + async
ingestion (unnecessary for a text/code substrate).

**Net:** Round 4 hardens the *safety and learning-persistence* model (acceptance gate +
forward-injected reflections + named control patterns) and enriches memory metadata, **without moving
the architecture off its zero-dep, single-file foundation.** All four external rounds are now
integrated; this is the consolidated final plan.

## External review — Round 5: Hermes (the independent-review seam, run on itself) (2026-06-13)

**The most execution-focused review of the five — and fittingly, run through the very
independent-review seam this plan ships.** Hermes reviewed PR-1 *execution risk*, not AI theory; near
all of it is accepted. Folded into core where execution-critical (interpreter note, verification
section) and recorded here.

**Accepted into core:**
- **CI coverage from commit 1 (#1)** + **explicit acceptance predicate (#5)** → Verification section:
  `substrate-kit/tests/` runs in CI via the existing pytest invocation incl. a `--simulate 1` smoke; the
  retained suite gains a concrete green/red predicate (stricter for autonomy increases).
- **Interpreter discipline (#2)** → sharpened Ground-truth note. *Accepted with a correction:* the
  kit's own code uses `sys.executable` (never hardcodes a version), but superbot's in-repo
  verification **stays `python3.10`** — the binding CI-parity rule, not drift. Hermes over-generalized
  "remove the python3.10 strings"; applying that to superbot verification would break CI parity. The
  distinction is now explicit and per-target.

**Accepted, routed:**
- **Multi-tenancy / coexistence (#6)** *(→ architecture note)*: the structural guardrail already keeps
  proving in `examples/`/tmp (never superbot's root) and the kit's state lives under its own
  `.substrate/` namespace — so `.substrate/state.json|episodic_index.json` never collide with superbot's
  `state.db` / live `.sessions/`. To be stated as three explicit bullets.
- **Hook customization contract (#4)** *(→ PR 2 + README)*: `settings.template.json` ships an explicit
  "agent fills these / what must match your repo" table (interpreter, script paths, doc paths,
  cadences) so users don't hand-edit and break invariants.
- **Question-bank curation policy (#7)** *(→ PR 1)*: `question_bank.yml` ships with a maintenance-rule
  header — review cadence, removal criteria, "add only when it blocks graduation" — so the day-1
  surface area doesn't accrete drift.
- **Embed-recursion design note (#8)** *(→ PR 1)*: `build_bootstrap.py` must exclude `dist/` from its
  own inputs so it never embeds itself; a test asserts the manifest→artifact→same-dir-run path has no
  recursion. Cheap insurance before trusting the `build_pack.py` analogy.

**Accepted in spirit, adapted (#3 — PR-1 size):** Hermes flags PR 1 as large and suggests splitting
off a tiny green-path PR. I keep it **one PR** (repo rule: large end-to-end PRs are fine for low-risk
non-`disbot/` tooling; the owner prefers substantial work over smallest-slice) but adopt the
de-risking *intent* via **commit order within PR 1**: land `lib/config.py` + atomic-write helper +
`build_bootstrap.py` + the `--simulate` smoke + CI wiring **first and green**, then layer the
interview engine, templates, and checkers onto the proven skeleton.

**Corroborated (Hermes's "keep" list):** keep/rework/drop filtering; atomic-write + crash-refuse
safety; promotion-rights-vs-onboarding separation; `--simulate` as the named retained suite; and —
emphasized — the **single-file stdlib bootstrap must stay a first-class, tested artifact, not decay
into a post-PR-1 packaging detail.**

**Net:** Round 5 added no architecture — it converted execution *ambiguity* into concrete gates
(CI-from-commit-1, a pass/fail acceptance predicate, interpreter discipline, coexistence bullets,
curation + embed-recursion guards). The riskiest PR-1 unknowns are now closed.

## External review — Round 6: cross-agent final-review batch (integrated; superseded by later rounds, 2026-06-13)

*The maintainer is running a deliberate final review across all agents (2 further reviews still
inbound). This round restated the plan as a clean "v6" and proposed one substantive addition.*

**Note on the restatement.** One agent re-rendered the whole plan and marked it "Approved for
execution." I keep **this** detailed plan as the source of truth (it retains the full PR-by-PR scope,
risk register, and round-by-round provenance the condensed restatement dropped) and **do not treat it
as approved** — the maintainer's cross-agent review is still open. Substance folded in, status kept
honest.

**Accepted — Forward Reflection Buffer** *(→ §6 + state schema; PR 2, stub may ride in PR 1)*. This is
the **concrete specification of an already-accepted principle** (Round 4 #1: "persist reflections and
inject them forward"), not new scope — so it's a clean accept. A small rolling buffer in
`.substrate/reflections.json` (default 5; each `{id: R-NNNN, lesson, evidence, tags, timestamp,
superseded_by}`): populated by the meta-reflection miner at session-close or `ask --reflect`;
**forward-injected** into each new session's orientation as a compact "Learned Lessons" block; pruned
on deprecation or overflow; provenance-stamped; respects promotion-rights (only *confirmed* lessons
inject in autonomous mode); optional via config; visible in `status`. It threads together five pieces
already in the plan (miner + Reflexion + deprecation + user-style injection + promotion-rights) and
directly serves the original ask — "prompts itself to create ideas and suggest improvements." Routing:
`engine/interview/reflections.py`; state field `reflection_buffer`; a `reflect` CLI surface (PR 2); a
simulation assertion (written → injected → pruned → no KPI regression); a safety bullet (provenance +
promotion-rights gating).

**Accepted — deterministic-evaluation conflict tier** *(→ §6)*. Before escalating a reviewer
contradiction to a human, if it touches an objectively-checkable asset (syntax, doc links) the
**validation script's result rules**; only *structural/workflow* contradictions block + roll back +
escalate to a blocking Q-block. Fewer needless human escalations, same safety. (Plus: compaction now
triggers on ~700K tokens *or* 20 sessions.)

**Net:** still no architecture change — Round 6 specifies the reflection-persistence mechanism
concretely and adds an objective tier to conflict resolution. Two reviews remain in the maintainer's
final batch then arrived (ecosystem research, ChatGPT v5, Hermes-final) and are integrated as Rounds 7–10 below.

## External review — Round 7: ecosystem / prior-art research (integrated; superseded by later rounds, 2026-06-13)

*Maintainer-run research into the surrounding ecosystem (web + GitHub). Research continuing; findings
actioned as they land.*

**Finding 1 — name collision (actioned).** `agent-os` is heavily taken — `buildermethods/agent-os`
(closest sibling: "spec-driven development with AI coding agents"), `framerslab/agentos`, `OmoiOS`.
Working tree de-anchored to placeholder `substrate-kit/` (see Naming section); published name stays the
owner's call with an availability check.

**Positioning vs. prior art (sharpens the differentiator).** The neighborhood is two camps and this is
*neither*: **(a) spec-driven-dev** (spec-kit, buildermethods/agent-os, get-shit-done, shotgun) generates
a spec/plan *once*; **(b) memory stores** (claude-mem, Letta `agent-file`, atomicmemory, gitagent) persist
state. **This is the third thing:** a staged-learning substrate that *grows* a project's whole
working-memory + workflow across many sessions, then self-maintains — why Grok found "no exact prior art."
Borrow: spec-kit's `constitution.md` (≈ templated `CLAUDE.md`) and `/clarify` (≈ a one-shot of our staged
interview) — position the interview as "`/clarify` that never stops and writes durable memory."

**Finding 2 — task-stance modes (owner-decided: scoped into v1).** Research confirmed the working agent
has no task-stance modes (only ExitPlanMode); prior art is Roo Code's modes, and the context-rot/tool-bloat
data backs scoping context per stance. I flagged it as a distinct fourth axis and recommended a follow-on;
**the maintainer chose to scope it into v1.** Now designed as **§3b (Task-stance modes)** —
question/analysis/debug/review/plan, each scoping reading-route + tool-scope + output contract; state field
`stance`; `stance` CLI; orientation injection; **lands in PR 2** (stub in PR 1). The same data also
*retro-justifies* existing choices (pre-compaction State Delta, sub-agent isolation, deprecation).

## External review — Round 8: skills/modes + native-format research (2026-06-13)

*Two read-only passes (your repo + the public ecosystem), prompted by the maintainer's "explicit skills like
question/analysis mode" intuition. Verdict: the intuition was right, and resolves into a **native-format
capability layer** of three complementary mechanisms.*

**Verification.** Stance-modes (§3b) were already added in v6 (the maintainer was reading v5). The deeper
find: superbot **already ships a skills mechanism + generation pipeline** (`.claude/skills/` plus 11
doc-generated Hermes skills via `scripts/hermes/build_skills.py` — the same manifest→artifact pattern as our
`build_bootstrap.py`) **and** spawnable **personas** (`.claude/agents/`: `superbot-architect`,
`mutation-boundary-auditor`). The kit ships neither yet — the real gap the intuition found.

**The capability layer — three complementary mechanisms, all in native Claude Code format:**
- **Stances** (ambient posture — §3b): question/analysis/debug/review/plan. *How the agent is postured.*
- **Skills** (invokable `SKILL.md`): *a capability you invoke.* Generalize superbot's SKILL.md +
  `build_skills.py` (docs→skill, reusing the bootstrap's manifest→artifact engine). Starter pack = the
  generic superbot skills (session-close, quality-gate/pre-pr, generic-review, repo-health, deep-research)
  **+ new** `question` / `analysis` / `review` skills.
- **Personas / sub-agents** (`.claude/agents/*.md`): *a specialist you spawn.* Read-only architect /
  reviewer / researcher, generalized from superbot's two.

**Why native format is the key call.** `SKILL.md` is a **standard** (Claude Code + adopted by Cursor, Codex,
Gemini CLI, 20+ agents) with **progressive loading** (metadata-first → full content on match) — which itself
fights context rot, reinforcing §3b. Shipping skills/agents/hooks in the native `.claude/` layout makes the
kit Claude-Code-native **and** portable across agents — no parallel scheme to invent.

**Borrowed gems (folded in):**
- **Serena's `memory_maintenance` meta-memory** → a seeded *memory-conventions* doc governing how memory is
  written/consolidated (added to §6). Serena is the closest prior art — but it does **one-shot** onboarding;
  ours **grows** over sessions (the differentiator).
- **Roo Code's mode data model** (role + tool-scope + file-glob + instructions) → §3b stance schema.
- **"Claude Dreaming"** (Anthropic's native reflective-consolidation feature) **validates** our self-improving
  loop (context-delta miner + reflection buffer + deprecation) — we're the doc/workflow analog, no model needed.
- **spec-kit's `constitution.md`** ≈ our templated `CLAUDE.md`; its `/clarify` ≈ a one-shot of our staged interview.

**Niche verdict (both passes agree): holds, strongly.** Serena/Cline/Letta persist memory; Mem0 is vector
infra; spec-kit is spec workflow; buildermethods/agent-os is standards injection; skill marketplaces ship
tasks. **None combine staged-learning interview + reflexive consolidation + stance-modes + native
skills/personas + single-file drop-in.** That five-way combination is the defensible category.

**Decided (maintainer, 2026-06-13): all three** — stances + skills + personas ship in v1. Wired as core
**§3c** + PR 2 (the capability + content PR). The native-format capability layer is now the kit's headline
surface alongside the staged-learning memory loop.

## External review — Round 9: ChatGPT productization/OSS-readiness review (reconciled to v8, 2026-06-13)

*A thorough 25-min review — conducted against the **stale v5**, but grounded in live GitHub inspection. The
strongest **productization / reliability / legal** lens of all nine rounds. Reconciled: what v6–v7 already
fixed, what's genuinely new (accepted), where it over-reaches, and one fair intellectual-honesty correction.*

**Already addressed in v6–v7 (invisible to a v5 review):** the `agent-os` **name collision** (→ placeholder
`substrate-kit/`); **task-stance modes** (§3b); the **skills + personas capability layer** (§3c); **atomic
state writes** (Gemini round); the **retained simulation suite as a release gate** (Hermes acceptance
predicate); **memory deprecation/unlearning**; **"measurable-first, autonomous-second"**. Not re-litigated.

**Accepted — genuinely new and correct (integrated):**
1. **State-backend abstraction** *(→ §2 core; PR 1)*. Sharpest technical catch: `os.replace()` is an atomic
   *rename*, not locking/conflict-resolution/queryability — and superbot's loop is **concurrent by design**
   (parallel chats + routines, hence the by-section/UNION-merge rules). So mutable coordination state goes
   behind a **state-backend interface**: JSON+`os.replace` default (copy-one-file simplicity) + a stdlib
   **`sqlite3`** backend for the concurrent case. Human memory stays diffable files. SQLite is stdlib ⇒
   zero-dep holds. (This is ChatGPT's own "or at least a backend abstraction" fallback.)
2. **Three product layers: core / adapters / content-pack** *(→ refines §5 seam; productization phase)*. Harden
   the seam into **core engine** + an explicit **adapter layer** (GitHub · local-only · optional reviewer/LLM)
   + **content-pack** — making GitHub-automation, the review seam, and nightly chaining **optional adapters**,
   not core requirements. *Local-first by default.*
3. **Delivery-model reframe (the key reconciliation)** *(→ phases + header)*. ChatGPT's "not 3 PRs, ~160–276 h"
   conflates two scopes. The 3-PR plan = the **working substrate proven in-repo** (this session). Public-OSS
   **productization** is distinct and larger; ChatGPT's milestone model (scope-freeze → core → engine →
   quality → adapters/RC) is adopted as that phase's blueprint. Now stated explicitly in the phases section.
4. **GitHub App over PAT** *(→ autonomous adapter; productization)*. The autonomous-loop adapter is designed
   for a **GitHub App** (short-lived, not user-bound); `ROUTINE_PAT` is a documented bridge, not the end state.
5. **Privacy-by-design baseline** *(→ owner-profile template; productization)*. The kit captures personal data
   (owner profile, session content), so the owner-profile template ships with **redaction defaults, retention
   guidance, access-role notes** — GDPR-by-design, proportionate to a dev tool. (EU AI Act stays out of scope
   for a dev-workflow toolkit — revisit only on SaaS/commercial/profiling.)

**Intellectual-honesty correction (accepted):** the Grok-round phrasing that file-based memory **"outperforms"**
MemGPT/Letta/vector DBs overstated it — the literature supports reflective/episodic/multi-tier memory, but
**not** a universal "files beat vector DBs" result. **Downgraded to a deliberate simplicity/portability choice
for v1**, not a proven benchmark win. (Supersedes the Round 2–3 phrasing.)

**Where it over-reaches (noted, not adopted wholesale):** the effort estimate assumes the *full public product*
in v1 — reconciled via the prove-in-repo vs. productization split (#3), so the 3-PR foundation stands. SQLite
is a *backend option*, not forced everywhere (preserves copy-one-file simplicity). The "still just an
idea/discuss-lane" governance flag is **superseded** — the maintainer has directed this work in-session across
many planning rounds; the owner decision is this effort.

**Confirmed superbot bugs (separate from the kit; flagged because I'm plan-only this session):** (a) **doc drift,
verified** — `session-close/SKILL.md`'s step-6 summary (line 14) still says "open draft PR … mark ready,"
contradicting Q-0103 **and the same file's** detailed section (lines 134–141: "create one **ready**,
`draft: false`"); a one-line fix. (b) the `.python-version` 3.13 vs CI 3.10 drift (already in our Ground-truth
note). Both worth a separate fix pass.

## External review — Round 10: Hermes final pre-execution gate (integrated 2026-06-13)

*The maintainer's intended final review, run through the independent-review seam. The most execution-sharp
round — four real blockers + several gaps, all resolved in-core below. Per the seam's own discipline I
**verified before accepting**, and one whole section didn't survive verification.*

**Calibration (verified, not assumed).** Hermes's "polish / garbled text" list (`LEFT BEHIND:D:`, `Graduation
is adaptive, not a hard 50duation…`, `substrate-kit/**`, "diagram still says agent-os/") describes a **corrupted
copy-paste Hermes was fed — none of it exists in the canonical plan** (grep-verified: the tree is
`substrate-kit/`, no doubled headers, no garbles). The *only* real straggler was one stray "agent-os state" in
the corroboration section — fixed. The seam working as designed: dissent calibrated against ground truth first.

**Four blockers — resolved in-core:**
1. **Internal PR-1 gate (#1)** → PR 1 **split into 1a (skeleton + locked contracts, independently green &
   mergeable) and 1b (engine + templates on the proven skeleton)** — a mergeable increment, not just commit order.
2. **State-backend interface unspecified (#2, #11)** → §2 now **locks the interface contract** (`get/set/query/
   transaction/migrate` + `version`) in PR 1a commit 0; PR 1 ships interface + JSON backend, SQLite is the
   productization implementation, migration-compatible from day 0. The Round 9 ↔ §2 drift is resolved.
3. **Acceptance predicate underpowered (#3)** → Verification now defines **two predicates**: a *merge gate*
   (pytest green + sim smoke + no leftover placeholders) on every PR, and the *autonomy-increase gate* on self-promotion.
4. **`build_pack.py` trusted-but-flagged contradiction (#4)** → carved as **inspiration only, not a trusted
   reference**; `build_bootstrap.py` gets its own provenance header + embed-recursion test.

**Gaps / tensions — resolved:**
- **Two-interpreter landmine (#6)** → `substrate.config.json` gains `interpreter` (kit) **+ `interpreter_for_checks`**
  (host verification, e.g. 3.10 for superbot) — the conflict made explicit, not latent.
- **Autonomous-mode assumption deadlock (#7b/#13)** → §6 defines the **autonomous confirmation path** (other-model
  confirms objective assumptions; subjective ones cap at `propose`; **provisional lessons still inject, flagged**,
  so a no-human run still learns). The core-loop deadlock is broken.
- **Graduation floor under-specified (#7a)** → a **per-slot configurable floor** (char + structure) in
  `question_bank.yml`, not a global number.
- **Skill↔stance composition (#8)** → precedence rule: **a skill's declared capabilities override the ambient
  stance** (`session-close` writes even in `review`).
- **`.substrate/` clobber (#9)** → `state_dir` configurable + `project_id`-stamped; a sibling project's dir is
  never mistaken for an idempotent rerun.
- **Confirmed-bugs vs in-repo CI (#10)** → a **pre-PR-1 checklist** shows both bugs are harmless to CI (skill drift
  is prose; `.python-version` isn't a CI input — CI pins 3.10 via `setup-python`); cleanup, not a gate. (Closes
  polish #16 too.)
- **Review-seam scope (#12)** → stated explicitly: **provisioned, not wired to a live reviewer until productization.**
- **Q-block dual-write (#14)** → interview blocks tagged `agent-assumption`/`interview-captured` vs `owner-decision`.
- **Round 6/7 "in progress" markers** → updated to integrated/superseded.

**Affirmed (Hermes's keep-list, unchanged):** keep/rework/drop filtering; promotion-rights-vs-onboarding
separation; atomic-write crash-refuse; "measurable-first, then autonomous"; the state-backend abstraction; and
the live-loop guardrail — now **enforced as code in PR 1a commit 0**, not left as a doc.

**Net:** Round 10 added no new architecture — it closed the execution gaps. The four bottom-line fixes
(state-interface contract · two-interpreter config · autonomous-confirmation path · internal PR-1 gate) are
in-core. The plan is now an **executable specification**.

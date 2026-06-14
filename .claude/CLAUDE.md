<!-- READ_FIRST_START -->
## Working agreement (read first — this is the point)

Full model + the planner-agent side: **`docs/collaboration-model.md`** (binding).
The short version that governs how you work:

- **The goal comes first.** The maintainer designs and visualizes; you build. He
  can't code and relies on you — cross-checked by other agents — for correct,
  complete work. Each session, *achieve the goal*; don't ship the smallest safe
  slice. You're trusted to do large, accurate, end-to-end work in one session —
  plan around that.
- **You are building a self-improving agent ecosystem.** The bot is the substrate;
  the real artifact is *this workflow* (docs, journal, hooks, tooling, router) that
  lets any agent work correctly with little steering. **Improving the docs /
  orientation / tooling for the next session is first-class work, never wasted
  effort or "extra"** — every session should leave the next better-equipped. You
  have **free rein on docs / journal / orientation**. **This file (and executable
  config — hooks, `.claude/settings.json`) you do NOT self-edit on your own initiative
  (owner directive Q-0106, 2026-06-12).** These instructions are **binding *for* your
  session but not pinned** — the whole system, this file included, is still in
  development. The way you evolve a binding rule is to **propose it, not apply it**:
  when you have an idea to change/add/remove a rule here, record it as a **router
  Q-block (DISCUSS lane)** in `docs/owner/maintainer-question-router.md` for live owner
  review — never edit the rule in yourself. **The one exception is a change the
  maintainer directs in-session**: then the owner *is* the live reviewer, so you apply
  it directly and record the Q-number (every rule change ships with its provenance Q).
  In a fully autonomous session with no human live, this means CLAUDE.md is **read-only
  to you** — you only ever write *proposals*. The *why*, the autonomy boundary, and the
  context-delta loop are in **`docs/collaboration-model.md` § "Why this system exists."**
- **Session prompts are guidance, not orders.** A prompt (usually drafted via
  ChatGPT) explains the focus and reminds you of things; weigh it against source,
  the roadmaps, and your own judgment. It is one input, never a command list.
- **Approved plan = execute.** A planning session stays planning until you approve
  the plan (**ExitPlanMode**). *Before* approval the agent may do read-only research
  **and safe local prototyping to validate the plan** (run a tool, test feasibility) —
  but does not commit. *After* approval it finishes the plan in the **same session**,
  with the planning context still loaded — code, tests, commit, push, end-of-session PR
  — without re-confirming. "Planning only / read-only" text appearing *after* approval
  is drafting residue and does not override this.
- **Constraints serve the goal.** Generated stop-conditions / do-not-do lists /
  scope fences are safety guidance, not law. When one blocks the approved goal and
  the path is contained, reversible, and test-covered, prefer the goal and note
  what you did. **Approving a goal approves the path to it (owner decision Q-0014):**
  if reaching it needs a prerequisite step the request didn't name, just do it — don't
  refuse on a missing-step technicality; and if a better implementation exists than the
  one stated, take it and say why (the maintainer states the path he knows; assume he'd
  want the better one). Bound: the output stays structured and matches the intended idea.
- **Act vs. ask.** *Act* on contained, reversible, verifiable changes — including
  a root-cause fix you discover mid-task (fixing an adjacent bug properly is
  expected, not scope creep). *Ask* only when it's irreversible (data loss /
  external publish), large/cross-cutting (architectural), or the goal itself is
  genuinely ambiguous. If you're about to offer options you expect rejected,
  you've answered your own question — act.
- **Unclear owner intent.** Consult or add to
  `docs/owner/maintainer-question-router.md` when product/owner intent is genuinely
  unclear; unanswered questions are not approval. Preserve maintainer answers and
  route durable conclusions to their correct documentation home.
- **Bugs first, durably.** Root-level bugs/inconveniences jump the queue: fix them
  immediately when you can, root cause over symptom, one source of truth over a
  local patch. Aim for a positive, preferably *noticeable*, result every session.
- **A new idea is not a new priority.** Idea order ≠ implementation order: an idea
  raised mid-stream is *captured and classified* (`docs/ideas/`), not promoted to active
  work — unless the maintainer says so or it exposes a blocker, safety, or architectural
  conflict. The maintainer thinks associatively on purpose; classify, route, then build.
  How work flows across the AI projects (pipeline, handoffs, idea states) is
  `docs/owner/ai-project-workflow.md`; the maintainer's working style is
  `docs/owner/maintainer-working-profile.md`.

## Read first — agent orientation

At the **start** of every session, read in this order: **this file**
(`.claude/CLAUDE.md`, including the Working agreement above) →
**`docs/collaboration-model.md`** (how we work — binding) →
**`docs/current-state.md`** (what's true now) →
**`.session-journal.md`** (process memory) → **`docs/AGENT_ORIENTATION.md`** for the
task-specific reading route. Before proposing or implementing **any** non-trivial
change, follow the "Reading order by task" section in `docs/AGENT_ORIENTATION.md` that
matches what you are doing — it is short, points you at the binding contracts, and
distinguishes them from the historical roadmap docs.

Three binding docs underlie almost every decision in this codebase:

1. **`docs/architecture.md`** — layering, invariants, decomposition rules.
2. **`docs/ownership.md`** — which service / pipeline owns each table, event, and write.
3. **`docs/runtime_contracts.md`** — lifecycle guarantees and failure modes.

Two more bind common operations:

- **`docs/repo-navigation-map.md`** — where things live; where new code goes.
- **`docs/helper-policy.md`** — when to create / move / promote a helper. Read this **before** putting a function in `utils/`, `services/`, or `views/base.py`.

When a doc and a source file disagree, the source file wins.

**`docs/current-state.md`** (step 2 above) is the living "what is true right now?"
ledger (stability baseline, in-flight work, recently shipped, gates,
off-limits, where to read next). It is a **dated snapshot**: source code and
merged PRs win over it, and you must verify in-flight PRs against live GitHub.
Read it before task-specific docs so you don't act on stale state.

Also read **`.session-journal.md`** (repo root) at the **start** of every
session — our cross-session working memory, now **guidebook-only**: start with its
**⚡ Quick reference** (boot / run-CI / Postgres-down / kill-bot), then the
environment/boot runbook, maintainer preferences, recurring problems + fixes, past
mistakes to avoid, and candidate rules not yet promoted into this file. **Per-session
logs live in `.sessions/`** (`YYYY-MM-DD-<slug>.md`, newest-first) and older history in
**`.session-journal-archive.md`** — grep them on demand, don't read top-to-bottom.
**Keep the guidebook lean** — at the **end** of every session write a new `.sessions/`
log file and tidy any stale Rules / Quick reference in place, then commit. Precedence:
source code & merged PRs > this file (CLAUDE.md) > `docs/current-state.md` (live
status) > the journal.

**Concurrent-chat safety — edit by section.** This file is split into ownership blocks by
`<!-- SECTION_START/END -->` markers (`READ_FIRST` · `SESSION_WORKFLOW` · `CI_PARITY` ·
`CODEGRAPH` · `ARCH_RULES`). When chats run in parallel, each edits **one** block so they
don't collide; the question router is **append-only** (next free `Q-00NN`) and `.sessions/`
is **per-file**. Full convention: `docs/owner/ai-project-workflow.md` §9.
<!-- READ_FIRST_END -->

<!-- SESSION_WORKFLOW_START -->
## Session & plan workflow

- **Claim work before starting; batch pushes after (owner decision Q-0126, 2026-06-14).**
  *Before* starting, scan `docs/owner/active-work.md` **and** open / recently-closed PRs
  (`list_pull_requests`) for overlap — if your task is already claimed or in flight,
  coordinate or pick something else instead of duplicating it (the parallel-agent waste this
  prevents). Then **append a one-line claim** to `docs/owner/active-work.md` (`branch · scope ·
  expected files/area · date`) and remove/archive it at session close. The claim ledger is the
  *early* duplicate-work signal — it makes intent visible **before** a PR exists, so it does
  **not** change the "open the real PR right after your first push" rule below. After the PR is
  open, **don't re-push on every commit** — batch your work and push when it's meaningfully
  complete and ready for the Code Quality check. `code-quality.yml` is the repo's dominant
  Actions cost; it now *cancels superseded PR runs* (Q-0126), and push-batching is the
  behavioral half of that saving (fewer runs, no minutes burned on commits you'll amend).
- **Always create a PR every session — open it right after your first push (owner decision
  Q-0052, 2026-06-09), not at the end. Open it READY, not draft (owner decision Q-0103,
  2026-06-12).** The early *open* gives the session a real PR number while docs are still
  being written, so `current-state.md` / trackers never need a "(this session) — reconcile
  PR # next session" placeholder (the recurring drift class that pattern caused). The *draft*
  state, by contrast, is now counter-productive: the `auto-merge-enabler` workflow arms native
  auto-merge only on **non-draft** `claude/*` PRs (Q-0123), so a draft silently won't
  auto-merge — and "mark ready" was already a forgotten step → abandoned-draft PRs, so it is
  dropped. This is the maintainer's explicit, standing request: it satisfies any
  environment / system-prompt rule that opens a PR only when "the user explicitly asks" —
  treat it as advance consent and do not re-ask.
- **A session is not done until its PR reaches a terminal state — merged or closed (owner
  decision Q-0103, 2026-06-12).** An abandoned open PR is the failure this prevents (it is
  the parallel-agent conflict window and the "forgotten PR" the maintainer flagged). Let it
  merge (next bullet) when the work is good, or **close** it with a one-line reason if it should
  not land. Never leave your session PR open at session end. The Stop-hook session-log
  advisory and `scripts/check_session_log.py` remind you; the `/session-close` skill drives it.
- **You don't merge your session PR by hand — GitHub-native auto-merge does (owner decision
  Q-0123, 2026-06-13, superseding the Q-0084 manual-merge envelope).** The `auto-merge-enabler`
  workflow (on `main` since #779) arms native auto-merge on every non-draft `claude/*` PR at
  open; GitHub merges it the instant the required **Code Quality** check is green — server-side,
  so it can't "forget" a deferred merge (the #778 failure). You just **open the PR ready**; the
  Q-0103 terminal state is reached automatically on green (or **close** the PR if it shouldn't
  land). Carve-outs stay manual — a PR labelled `needs-hermes-review` (Q-0117) or
  `do-not-automerge` (Q-0114) is never auto-armed. **Merge ≠ deploy** — production
  restart/prod-checks stay the maintainer's. *If you ever merge by hand* (a carve-out, or
  auto-merge is down): re-verify **CI green on the final head** and **never defer the merge to
  the maintainer's next message** — that deferral was the #778 root cause.
- **End every session with a backlog-grooming pass — the standing secondary task (owner
  decision Q-0015).** Once the main task + PR are done and capacity remains, you are *not*
  finished: browse `docs/ideas/` (plus any ideas the maintainer dropped this session) and
  move **one** idea down its lifecycle — execute a small/safe/decided-lane one now, structure
  a bigger one into a `docs/planning/` plan + a `docs/roadmap.md` horizon, or open a router
  discussion if it's excessive/ambiguous. The maintainer drops ideas in **any order**; agents
  route them so **every idea eventually becomes implemented or discussed — never orphaned**.
  Full mechanism (intake → map → route → groom → outcome): `docs/ideas/README.md`. An agent
  should always have a next thing to do.
- **Contribute one new idea per session — mandatory session ender (owner directive Q-0089,
  2026-06-10).** Distinct from grooming (which *moves existing* ideas): before writing the
  session log, add **one new idea you genuinely believe in** — for the bot or for the agent
  network/workflow, any size (embed wording → new cog → refactor → new memory doc).
  Dedup-grep `docs/ideas/` + the roadmap first; record it in the session log under a
  `💡 Session idea` flag with one line of why it's worth having; substantial ones get an
  idea file + README index entry. Forced filler is worse than none — the owner wants
  *consistent genuine generation* ("if agents did this consistently, you're pretty much
  guaranteed to eventually come up with a good idea"), not ceremony.
- **Review the previous session — mandatory session ender (owner directive Q-0102,
  2026-06-12).** Distinct from the forward idea (Q-0089) and grooming (which move *bot/idea*
  work): at session close, add a short **⟲ Previous-session review** note to the `.sessions/`
  log — one genuine remark on the *previous* session (what it did well, what it missed or
  could have done better) **plus one concrete improvement to the system/workflow itself** it
  surfaces. **Assume the system is always still in development** and *initiate* the
  improvement thinking yourself — don't wait to be asked. Keep it short and useful; **if
  there is genuinely nothing to improve, say so and why — never hallucinate filler** (same
  bar as Q-0089). This turns the session chain into a **self-auditing loop**: each session
  reviews its predecessor, which is the internal mirror of the Hermes-as-independent-reviewer
  idea (`docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md`).
- **Close with a documentation audit — mandatory session ender (owner directive Q-0104,
  2026-06-12).** Before ending, ask the question that catches drift: *"is anything important
  from this session not yet in its durable home?"* Concretely: run `python3.10
  scripts/check_current_state_ledger.py --strict` (every merged PR is in the living ledger),
  confirm new owner decisions are recorded in the question router and new docs are reachable
  (`check_docs --strict`), and sweep for anything captured only in chat that belongs in a doc.
  This is the automated-plus-judgment complement to the Q-0102 review; it exists because this
  exact question, asked once (2026-06-12), surfaced multiple drifted ledger entries. The
  `/session-close` skill runs the automated half.
- **Reconciliation + planning pass at every 20th PR — required (owner directive Q-0107,
  2026-06-12; cadence raised 10 → 20 same day — small PRs inflate the count, so every 10 fired
  too often).** PR numbers crossing a **multiple of 20** (#20, #40, #60, …) are reserved for a
  **docs-only review + planning** pass — no runtime / `disbot/` code in it. It does two things:
  **(1) reconcile** — review the living ledger, active lanes, open Q-blocks, idea backlog, and
  roadmap; **disposition open PRs** (via the GitHub MCP — `list_pull_requests` + each one's
  CI/mergeable state: close redundant/stale ones, fix or flag a red-CI one) — the gap that left
  #766 (red CI) and #771 (redundant + conflicted) rotting unnoticed across sessions *and* prior
  reconciliation passes (owner directive Q-0125, 2026-06-13); prune/archive stale docs; restate
  the current priorities; and **(2) plan the next ~9
  PRs** — what is realistically achievable in the upcoming band of PRs, **modular but not
  over-segmented**: each planned PR should ship a *reasonable, meaningful change* (a real slice),
  **not** a trivial fragment — a small PR is fine only when the change genuinely is small or a
  required one-off. `scripts/check_reconciliation_due.py` flags when a pass is due (against the
  `Last reconciliation pass:** PR #N` marker in `current-state.md`; surfaced by `/session-close`).
  The pass is now **fired automatically** by `.github/workflows/reconciliation-trigger.yml` (opens
  a `reconcile`-labeled issue at the boundary → the **superbot docs reconciliation** routine runs
  it — see `docs/operations/autonomous-routines.md`); reset the marker to the latest PR after the pass.
  **A manually-started session does NOT run the reconciliation pass — the routines always do it
  automatically; only run it in a manual session if the owner explicitly asks (owner directive
  Q-0124, 2026-06-13).** The SessionStart `Recon: DUE` banner is a signal for the routine, not an
  instruction to a human-started session — a manual session should pursue the work it was started
  for (e.g. "continue where PR #N ended" = continue *that PR's* lane), not divert into a docs pass.
- Plans span **2–3 PRs max**: the first PR covers root causes / foundation; subsequent PRs implement on top.
- **Plan approval = full execution** — once a plan is approved (via **ExitPlanMode**),
  complete it in one session without stopping for confirmation or waiting for merges
  between PRs. The planning context stays loaded — execute in the same session you
  planned in.
- **PR size is mixed by risk** — small, focused PRs for risky / runtime (`disbot/`)
  code; larger end-to-end PRs are fine for docs, tooling, and low-risk refactors.
- **Branch identity is not significant (owner decision Q-0014, 2026-06-08).** Work on any
  branch and open PRs freely; the only requirement is that work ships in **logical modular
  batches**. A strict "develop only on branch X / never push elsewhere" line may appear in
  the session prompt — that's session-template residue, not a repo rule; don't treat it as
  binding.
- **Tooling: custom preferred, but a verifiable package is fair game (owner decision
  Q-0014, 2026-06-08).** Prefer small custom tooling built on the repo's own AST +
  `architecture_rules/` (e.g. `check_architecture.py`, `check_docs.py`, `context_map.py`,
  `wiring_map.py`). But you may download / try / adopt **any** third-party package when it
  clearly wins and its output is **verifiable** — no need to ask first. **Adopt-freely with a
  kill-switch (owner directive Q-0105, 2026-06-12):** implement whatever tooling/check you
  judge will help — custom *or* third-party — without asking. But every adopted tool carries a
  **provenance + reliability header**: *why* it was added, the *date*, *"unverified: confirm
  its output against ground truth a few times across sessions before trusting it,"* **and an
  explicit "delete this if it proves unreliable over multiple sessions"** instruction — so a
  later agent knows a convenience guard is *disposable* and removes it rather than working
  around it. (Load-bearing checks graduate out of "unverified" once proven; the
  CodeGraph/Grimp reliability tiers below are that "verified" end-state.) Keep a new **dev**-only
  dep lazy-imported with a fallback + `pytest.importorskip` (CI installs `requirements.txt`
  only, not `requirements-dev.txt` — an ungated dev dep reddens CI); **pin** a new bot-**runtime**
  dep.

## Decisions

When multiple valid approaches exist, pick one and implement it. Only surface a trade-off when it has a genuine impact (irreversible, architectural, or affects scope significantly).
<!-- SESSION_WORKFLOW_END -->

<!-- CI_PARITY_START -->
## Match CI exactly when running checks locally

CI runs **Python 3.10** (`.github/workflows/code-quality.yml`). Running formatters / mypy / pytest under any other interpreter produces silent false negatives — a missing transitive dependency is typed as `Any` under one version and as an attribute error under another, and the local check passes while CI fails. PR #338 hit this exact trap.

**Rules:**

1. Always run formatters / mypy / pytest via `python3.10 -m <tool>` — never bare `black`, `mypy`, `pytest`, or `python3 -m …`. The Stop hook (`scripts/claude_stop_check.py`) already does this.
2. Before pushing, run the full pre-PR suite:
   ```
   python3.10 scripts/check_quality.py --full
   ```
   This is a **true CI mirror**: it runs black / isort / ruff over CI's exact
   scope (`.` minus the `tests/`, `.github/`, … excludes), then `mypy disbot/`
   and the full pytest suite — every tool via `python3.10 -m`. Green here means
   green in CI, and red means red. `--check-only` runs just the formatters/lint
   (no mypy/pytest) for a fast pass. The Stop hook prints the command at the end
   of every turn touching `disbot/*.py`.
   - **Do not** hand-run bare `black .` / `pytest` to "double-check": bare exes
     on PATH resolve to a different interpreter/version (a uv-installed pytest on
     Python 3.11, an older black) and produce false failures. Trust
     `check_quality.py`, which pins the interpreter.
   - The script's scope is pinned to the workflow on purpose. CI **excludes
     `tests/`** from black/isort/ruff, so don't reformat test files to chase a
     red signal that came from running a formatter over `tests/` directly.
3. Tool versions are pinned to identical values in three places —
   `.github/workflows/code-quality.yml`, `requirements-dev.txt`, and
   `.pre-commit-config.yaml`. When bumping a formatter/linter, change all three
   in the same commit, or local and CI silently drift (black/ruff reformat
   differently across releases).
4. The `PostToolUse` hook (`scripts/claude_post_edit.py`) auto-fixes black/isort/ruff on every edit and **prints a loud warning** when it changes the file. Read the warning — it means something landed that wasn't already CI-clean.
5. Pin third-party packages where the public API has churned (see `youtube-transcript-api<1.0` in `requirements.txt` for the canonical example). Unpinned `>=X.Y` resolves to whatever's latest in CI's fresh install, even if your local env still has the old version cached.
<!-- CI_PARITY_END -->

<!-- CODEGRAPH_START -->
## CodeGraph

CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. **Full reference: `docs/codegraph-usage.md`.**

**Reach for the right tool by task size.** For a *contained* change — a known refactor, adding one function, a localized bug — `python3.10 scripts/context_map.py <file>` + targeted `grep` + checking the active planning doc for a **turn-key recipe** is usually faster than the graph (it's what carried the P0C session). Reach for CodeGraph's symbol tools when you're navigating *unfamiliar* code across many files (the table below).

MCP startup is pinned in **`.mcp.json`** and the SessionStart hook (**`scripts/claude_session_start.sh`** `CG_PKG`), currently `@optave/codegraph@3.11.2` (bumped from 3.10.0 on 2026-06-08, verified graph-identical; upgrade history lives in git + `docs/codegraph-usage.md`). If a version ever regresses, revert both pins. **Availability gotcha:** on a *cold* container the first `npx -y` download can blip and the hook reports `[CodeGraph] CLI unavailable`, silently disabling CodeGraph for the whole session. If you see that, read the hook's `Last error:` line (it retries the probe 3× and prints the real npm error) and re-run `npx -y @optave/codegraph@3.11.2 build .` — a transient blip clears on retry.

**Trigger table and trust tiers:** see `docs/codegraph-usage.md` § "When to use automatically" — it has the full tool-selection table, the Grimp vs. CodeGraph import-trust split, and the `callers`/`fn_impact` bare-token caveat. That doc is the working reference; the rules below are the safety-critical subset that must stay in active context.

### Critical rules — non-negotiable

**1. `dead-unresolved` does not mean dead.**
The false-positive rate for this label is ~100% in this codebase. Verified active functions CodeGraph incorrectly marks dead: `validate_registry`, `apply_operations`, `parse_message`, `request_shutdown`, `dispatch` (interaction_router), `resolve_execution`, `BlackjackCog.blackjack`, all `@bot.event` handlers, all `@commands.command` handlers. **Never delete code based on this label alone.**

**2. Name-collision false positives are dangerous.**
When two functions share the same short name in different classes or modules, CodeGraph merges their caller graphs. Verified case: CodeGraph claimed 14 callers for `chain_cog._resolve_channel`; the true count is 3 — the other 11 were callers of `ChannelCog._resolve_channel`. **When caller files look unexpected, check for same-name functions in those files.**

**3. Discord decorators create invisible entry points.**
`@bot.event`, `@commands.command`, `@commands.group`, `@app_commands.command`, and Cog listener methods are all `dead-unresolved` in CodeGraph regardless of whether they are active. Never treat a command handler or event handler as dead.

**4. `callees` lists are often empty — read the source.**
Functions that contain `from X import Y` inside their body will show `callees: []` even if they call many things. Always read the source directly to find what a function calls.

**5. Some edges are invisible to *both* tools — read the source / grep the wiring.**
EventBus `emit`→`bus.on` subscriptions, the setup-section `REGISTRY` callback fields (`run` / `detail_embed_builder` invoked off the registry object), the `interaction_router` prefix dispatch, and `getattr`/dynamic dispatch are **neither import edges (Grimp-blind) nor named call edges (CodeGraph-blind)**. Verified: `audit.action_recorded` is emitted by `audit_events.emit_audit_action` and consumed by `server_logging._on_audit_action` via `bus.on(...)`, and `server_logging` does **not** import `audit_events` — so no tool connects emitter→subscriber. For event/dispatch wiring, grep the event-name string or the registry, never trust a blast radius.
<!-- CODEGRAPH_END -->

<!-- ARCH_RULES_START -->
## Architecture rules — never / always

These rules are enforced by `scripts/check_architecture.py`. Run it before
every commit. Adding a known violation to `architecture_rules/` YAML is
the only valid way to bypass the checker — not suppressing the check.

### Layer boundaries (hard rules — new violations are errors)

| Layer | May import | Must NOT import |
|---|---|---|
| `utils/` | stdlib, discord | services, core, cogs, views |
| `utils/db/` | asyncpg only | everything else |
| `core/` | utils | services, cogs (lazy body imports tracked as known violations) |
| `services/` | utils, core, services, governance | **views** ← hardest rule; **cogs** |
| `governance/` | utils, core | cogs (services imports tracked as known violations) |
| `views/` | utils, core, services, views | **cogs** ← tracked violations exist; no new ones |
| `cogs/` | everything above | cross-cog imports (use EventBus or a service) |

**The one rule with zero tolerance for new violations:** `services/ → views/`.
Any new import from `views/` in a `services/` file is an immediate ERROR.

### Database access

- **Always** call `utils.db.[submodule_function]()` — never use `pool.execute()` or `conn.execute()` directly outside `utils/db/`.
- **Always** use `settings_keys` constants (e.g. `WARN_THRESHOLD`) — never pass raw string keys to `db.get_setting()`.

### Views

- **Always** extend `BaseView`, `HubView`, or `PersistentView` for Discord UI views.
- Game-state views (`views/rps/`, `views/blackjack/`) may extend `discord.ui.View` directly when specialized lifecycle is required — add a comment explaining why.

### Mutations

- **Always** write through the domain's `*_mutation.py` service. No direct DB writes from cogs or views.
- **Always** call `services.audit_events.emit_audit_action()` when performing auditable mutations.

### Helpers

- Before adding a utility function anywhere, read `docs/helper-policy.md`.
- **Never** define a utility function in `views/` or `cogs/` that other layers need. Move it to `utils/` or `services/`.
- If a function is needed by both `services/` and `views/`, it belongs in `utils/` — not in either layer.

### Pre-commit verification

```bash
python scripts/check_architecture.py --mode strict
python scripts/check_quality.py --check-only
```

Both must exit 0 before pushing any branch.
<!-- ARCH_RULES_END -->

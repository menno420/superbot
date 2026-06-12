# Claude Code hooks & plugins — reference + brainstorm

> **Status:** `reference` — what hooks this repo wires today, candidate hooks worth adding,
> and the plugins posture. Hooks/plugins are **executable config** (`.claude/settings.json`)
> → **ask-first** per the CLAUDE.md working agreement; this doc is the map, not approval to
> wire anything. Source of truth for what is *actually* wired is `.claude/settings.json`.

## Why this doc exists

The repo's whole self-improvement system leans on hooks — they're how tooling reaches the
agent *at the right moment* instead of relying on it to remember. Until now nothing
documented them, so each session rediscovered what fires when. This is the reference;
the brainstorm section is the standing "what would make the loop tighter?" list.

For **plugins**, the full ecosystem evaluation + adoption shortlist already lives in
[`docs/ideas/claude-code-plugins-evaluation-2026-06-12.md`](../ideas/claude-code-plugins-evaluation-2026-06-12.md)
(owner decision **Q-0096**). This doc does not duplicate it — see § Plugins below.

## Part 1 — Hooks wired today

All wired in `.claude/settings.json`. Every hook is **repo-owned** (no third-party hook
code) — the defensible end of the supply-chain spectrum (see § Plugins).

| Event · matcher | Script | What it does |
|---|---|---|
| `SessionStart` | `claude_session_start.sh` | Idempotent boot: Python env up-to-date → CodeGraph index build → session summary banner. Independent steps (one failing doesn't skip the rest). Calls `claude_session_summary.py`. |
| `PreToolUse` · `Edit\|Write` | `claude_pre_edit.py` | On the **first** edit of a `disbot/*.py` file in a session, injects that file's `context_map.py` output (importers, blast radius, lazy imports, read set, post-edit checks) as `additionalContext` — the file-level navigation step, surfaced automatically. |
| `PostToolUse` · `Edit\|Write` | `claude_post_edit.py` | `.py`: auto-runs black → isort → ruff `--fix` on the edited file, **loud warning** when a fix landed or a tool errored. `.md`: runs `check_docs --strict`, warns on failure. Non-blocking (exit 0). |
| `PostToolUse` · `create_pull_request` | `claude_pr_subscribe_reminder.py` | Injects a reminder to call `subscribe_pr_activity` right after a PR is created (hooks can't call MCP tools themselves) — closes the "PR merged but the session never learned" gap. |
| `Stop` | `claude_stop_check.py` | **Hard-fail gate** at end of each turn: on Python files changed vs `origin/main`, runs architecture (strict) + black/isort/ruff `--check` + mypy. Prints the `check_quality.py --full` command. The CI mirror at turn boundary. |

**Reading the table:** `PreToolUse`/`PostToolUse` can inject `additionalContext` or warn;
`Stop` is the only hard gate; `SessionStart` is pure setup. Hooks are shell commands — they
**cannot call MCP tools** (hence the subscribe *reminder* rather than an auto-subscribe).

## Part 2 — Brainstorm: candidate hooks worth adding

Scoped to the maintainer's focus — **memory + autonomous workflow consistency**. Each is a
proposal (ask-first); none is wired.

1. **Session-close completeness gate (`Stop` or `SessionEnd`).** Verify, when a session is
   wrapping, that a `.sessions/<today>.md` log exists and contains the required sections
   (`💡 Session idea` Q-0089, `⟲ Previous-session review` Q-0102, grooming note). This
   directly attacks the maintainer's observation that the session-ender rules "aren't always
   properly done" — turn the convention into a checked signal. *Highest-value for the memory
   system.* Risk: must be a soft nudge mid-session and only firm at genuine session end, or
   it nags every turn.
2. **Previous-session surfacing (`SessionStart`).** Extend the boot banner to print the
   *previous* `.sessions/` log's "Left open / next" + its `💡` idea + its `⟲` review, so a
   new session sees the handoff immediately instead of having to grep for it. Feeds the
   Q-0102 review rule with the material it needs. Low risk (print-only).
3. **Pre-compaction handoff (`PreCompact`).** Before context is auto-compacted (the ~700K
   quality-cliff the §10 bounded-session protocol exists to dodge), force-write a short
   handoff/context-delta note so nothing is lost across the compaction boundary. This is the
   memory system's missing seam — the cliff is currently dodged by *manual* discipline.
4. **current-state freshness nudge (`PostToolUse` · `merge_pull_request`).** After a merge,
   remind the agent to update `current-state.md` Recently-shipped if it wasn't — the exact
   drift class `check_docs --freshness` already half-guards.
5. **Idea/grooming nudge (`Stop`, end-of-session only).** If the working tree has a session
   log but no grooming/idea move recorded, remind before close. (Overlaps #1 — likely folds
   into it.)

**Recommended first:** #1 + #2 together — they operationalize the Q-0089/Q-0102 rules the
maintainer specifically wants made consistent, and #2 is print-only (trivially safe).

## Part 3 — Plugins

A Claude Code **plugin** is a git-distributed bundle that can carry skills, agents, **hooks**,
MCP servers, LSP servers, and default settings, installed from a **marketplace**. Because a
plugin can ship arbitrary hook code, plugin adoption is the **highest-trust-surface** change
in this repo and is strictly **ask-first** (Q-0096).

The full survey, shortlist, and supply-chain rules are in the Q-0096 evaluation. One-line
posture so this doc stands alone:

- **Skip** workflow / memory / code-review / commit plugins — they **duplicate or fight**
  the system this repo deliberately built (CLAUDE.md + journal + skills + CodeGraph).
- **Maybe (trial, pinned, as plain `.mcp.json` not a plugin wrapper):** **Context7** (live
  version-pinned library docs — addresses our "API from memory" bug class) and a **read-only
  Postgres MCP**.
- **Rules if anything is adopted:** pin (sha/version), audit the bundle for hooks first,
  prefer hook-free MCP/skills-only bundles, carry the Q-0014 provenance header.

## Changing a hook or adopting a plugin

1. It's executable config → **propose first** (router Q-block or owner ask), don't wire silently.
2. Tool versions stay pinned in the three places the CI-parity rule names; bump together.
3. New hooks are **repo-owned scripts** under `scripts/claude_*.py|sh`; keep them fast,
   idempotent, and non-blocking unless they are deliberately a gate (only `Stop` is today).
4. Re-verify any third-party piece against ground truth a few times before trusting it.

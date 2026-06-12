# 2026-06-12 — Context7 MCP adoption (Q-0096 answered)

> **Status:** `audit`

**PR:** opened this batch (Context7 MCP trial)
**Branch:** `claude/context7-mcp-adoption`

## Context

Owner approved the Context7 trial ("go ahead, it seems very useful and time-saving"), answering
the long-standing Q-0096 plugins decision. Context7 = live, version-specific library docs
injected on demand — targets the recurring "API used from memory" bug class on fast-churning
libraries (discord.py above all).

## What was done

- **Wired Context7 as a pinned MCP server.** Verified latest on npm (`@upstash/context7-mcp@3.2.0`)
  before pinning. `.mcp.json`: added the `context7` server (keyless to start, no repo `cwd`).
  `.claude/settings.json`: added `context7` to `enabledMcpjsonServers` + pre-allowed its two tools
  (`resolve-library-id`, `get-library-docs`). Both JSON validated.
- **New operational reference** [`docs/operations/mcp-servers.md`](../docs/operations/mcp-servers.md):
  what we run (CodeGraph + Context7), when to use each, the pins, the **maintainer key-setup steps**
  (keyless ≈ 500 req/mo ceiling; add `CONTEXT7_API_KEY` to the environment for more), and the
  **Q-0105 delete-if-unreliable** provenance note. Wired into `repo-navigation-map.md`.
- **Recorded the decision.** Q-0096 marked ANSWERED (partial — Context7 adopted; Postgres-MCP /
  pyright-lsp still open). Plugins-eval idea doc lifecycle → partially adopted.

## Verification

- `.mcp.json` + `settings.json` valid JSON · `check_docs --strict` ✓. Config/docs only.
- **Takes effect next session** (MCP servers load at SessionStart). This session can't yet call
  the Context7 tools — first real use + the ground-truth verification is a next-session task.

## Maintainer follow-up

- Optional: create a free key at `context7.com/dashboard`, add `CONTEXT7_API_KEY` to this web
  environment's secrets, then a session adds the `env` ref to `.mcp.json` (steps in mcp-servers.md).

## ⟲ Previous-session review (Q-0102 — reviewing the #736 CodeGraph batch)

- **What it did well:** correctly diagnosed CodeGraph as healthy (live-tested), and caught + fixed
  the real bug (stale 3.10.0 doc commands) rather than hand-waving.
- **What it could have done better:** it fixed only the *CodeGraph* pin drift; it didn't check
  whether *other* pinned tools (requirements pins, etc.) have the same doc-vs-reality drift. The
  `check_pin_drift` idea (captured #736) would generalize it — worth building next.
- **System improvement surfaced:** none new beyond the already-captured pin-drift check; flagged it
  as the next tooling build.

## 💡 Session idea

**Idea:** A "did you consult Context7?" nudge — when a PR's diff touches a fast-churning library
(`discord.py`, `asyncpg`, `PIL`) the `review_scope`/pre-pr tooling reminds the agent to verify the
API via Context7 rather than memory.
**Why:** a tool that's wired but never used is dead weight (and would trip its own Q-0105
kill-switch for the wrong reason). This closes the loop on the adoption — it makes the new tool
*actually get reached for* on exactly the code where the "API-from-memory" bug class lives, instead
of relying on each agent to remember it exists. Advisory, cheap. _Small — recorded here._

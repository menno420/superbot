# 2026-06-12 — Claude Code plugin ecosystem research (owner question)

**Ask (owner, verbatim):** "Can you find out if there are any good plugins for
claude that would be useful for us" — research session, no code changes.

## Arc

1. Dedup-checked `docs/` for prior Claude-plugin work — none (all existing
   "plugin/marketplace" hits are Discord-bot-ecosystem material, e.g. MEE6).
2. Background web-research agent surveyed the mid-2026 plugin ecosystem
   (official `anthropics/claude-plugins-official` marketplace, community
   marketplaces, plugin-bundled MCP servers, supply-chain CVEs).
3. **Spot-verified the load-bearing claims directly** (journal rule: verify
   cross-agent output): official marketplace real (29.9k★); Context7 real and
   hot (57.2k★, release 2026-06-11, hosted MCP now wants an API key);
   `crystaldba/postgres-mcp` real with a read-only `--access-mode=restricted`;
   team-pinning settings syntax pulled from the live docs — **the agent's
   `enabledPlugins` format was wrong** (it's a `"name@marketplace": true` map,
   not an array). Unverified install/star counts are marked as agent-reported
   in the capture.
4. Filtered against our baseline: review/workflow/memory/commit plugin
   categories all duplicate or actively conflict with the bespoke system
   (skills, journal, Q-0052/Q-0084 PR flow, CodeGraph).

## Shipped (docs-only)

- [`docs/ideas/claude-code-plugins-evaluation-2026-06-12.md`](../docs/ideas/claude-code-plugins-evaluation-2026-06-12.md)
  — the evaluation: mechanics (verified pinning syntax incl. `sha` plugin pins
  and `CLAUDE_CODE_PLUGIN_SEED_DIR` for containers), the
  duplicates-vs-gaps table, shortlist (**Context7** > read-only Postgres MCP >
  trial-only `pyright-lsp`), explicit skips (superpowers, claude-mem, review
  plugins…), supply-chain posture + adoption rules.
- Router **Q-0096** (open): which of the shortlist, if any, to wire in —
  plugin/MCP enablement is ask-first executable config, so adoption awaits the
  owner's pick. Safe default: plugin-free status quo.
- Ideas README index entry.

## Grooming note (Q-0015)

The new capture was taken through intake → captured → **routed (discuss,
Q-0096)** in-session — no idea left at `raw`. No other backlog idea moved
(research session; main deliverable was itself backlog material).

## Context delta

- **Needed but not pointed to:** nothing significant — CLAUDE.md's "ask before
  changing executable config" line answered the adoption-boundary question
  directly; orientation route was adequate for a research task.
- **Pointed to but didn't need:** the full binding-docs route
  (architecture/ownership/runtime contracts) — irrelevant for a
  tooling-research session; the task-shaped routing in AGENT_ORIENTATION could
  name a "research/tooling" lane that skips them explicitly.
- **Discovered by hand:** `enabledPlugins` settings syntax differs from what a
  research agent reported (map, not array) — reinforces the standing
  verify-cross-agent-output rule; now pinned in the capture doc.
- **Decisions made alone:** recommended *against* the popular workflow/memory
  plugins on the grounds that our bespoke system is the artifact (CLAUDE.md
  premise) — owner can override via Q-0096. Chose plain `.mcp.json` wiring
  over plugin wrappers as the recommended adoption shape (smaller trust
  surface, matches the CodeGraph precedent).
- **Flagged for maintainer / weak point:** ecosystem numbers (install counts,
  CVE ids) are agent-reported web claims, only partially re-verified; anything
  load-bearing for an adoption decision should be re-checked at wiring time.
  Context7's hosted endpoint needs a (free) API key — local npx mode avoids it.

💡 **Session idea (Q-0089):** **settings-tamper check in the session hooks** —
the 2026 CVE class found in this research attacks agents by silently rewriting
`.claude/settings.json` / `.mcp.json` / `~/.claude.json`. Cheap defense: the
SessionStart (or Stop) hook diffs the repo's `.claude/settings.json` +
`.mcp.json` against git HEAD and prints a loud warning when they differ
uncommitted — tamper-evidence for the exact seam we treat as ask-first.
Dedup: adjacent to the gap-analysis "toolchain rot watch" but distinct
(integrity, not staleness). Small; a future session can add it to
`claude_session_start.sh` (executable config → confirm with owner first).

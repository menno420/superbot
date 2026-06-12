# Claude Code plugins — ecosystem evaluation & adoption shortlist (2026-06-12)

> **Status:** `ideas` — research capture + recommendation. **Nothing here is
> approved for implementation.** Plugin enablement lives in
> `.claude/settings.json` (executable config → **ask-first** per the CLAUDE.md
> working agreement), so adoption is an owner decision: **Q-0096** in
> `docs/owner/maintainer-question-router.md`.
>
> **Provenance:** owner asked "are there any good plugins for claude that would
> be useful for us?" (2026-06-12). A web-research agent surveyed the ecosystem;
> the load-bearing claims below were then **spot-verified directly** (marked ✓).
> Unmarked install counts / star figures are agent-reported — re-verify before
> citing. Source code and live docs win over this file.

## 1. What a Claude Code plugin is (verified ✓ against code.claude.com docs)

A plugin is a git-distributed bundle that can carry **skills, agents, hooks,
MCP servers, LSP servers, bin executables, and default settings**. Plugins are
listed in **marketplaces** (a repo with `.claude-plugin/marketplace.json`);
users add a marketplace and install from it (`/plugin` UI or
`claude plugin install <name>@<marketplace>`).

Team-wide pinning in repo `.claude/settings.json` (exact syntax ✓ verified
2026-06-12 from `code.claude.com/docs/en/plugin-marketplaces`):

```json
{
  "extraKnownMarketplaces": {
    "claude-plugins-official": {
      "source": { "source": "github", "repo": "anthropics/claude-plugins-official" }
    }
  },
  "enabledPlugins": {
    "context7@claude-plugins-official": true
  }
}
```

(Note: `enabledPlugins` is a **map** of `"name@marketplace": true` — a prior
agent report showed an array-of-objects format; that is wrong.)

Version pinning: a plugin entry in `marketplace.json` supports `ref`
(branch/tag) **and `sha`** (exact commit — the effective pin when both are
set); the marketplace source itself supports only `ref`. For containers/CI,
`CLAUDE_CODE_PLUGIN_SEED_DIR` pre-populates plugins at image build time —
relevant to our remote-sandbox sessions if we ever adopt plugins there.

## 2. Why our baseline changes the answer

Most of the popular plugin categories are things **we already have, better-fitted**:

| Plugin category | Our existing equivalent | Verdict |
|---|---|---|
| Code review / PR review plugins | built-in `code-review` + `security-review` skills, repo `/pre-pr`, `/architecture-review` | **Skip** — duplicate |
| Workflow/process plugins (e.g. obra/superpowers, `feature-dev`) | the whole CLAUDE.md + journal + session-close system | **Skip** — direct conflict with our binding workflow |
| Memory plugins (claude-mem, memsearch, …) | `.session-journal.md` + `.sessions/` + `docs/current-state.md` (designed, audited, git-versioned) | **Skip** — ours is the artifact; a SQLite side-memory undermines it |
| Commit/PR helper plugins | Q-0052/Q-0084 PR workflow + GitHub MCP | **Skip** |
| Code-intelligence | CodeGraph MCP (pinned `@optave/codegraph@3.11.2`) + `context_map.py` | **Skip**; `pyright-lsp` is the one maybe (see §3.3) |

The interesting candidates are the ones that add a capability we **don't** have.

## 3. Shortlist (best → weakest)

### 3.1 Context7 — live, version-pinned library docs (strongest candidate)

- **What:** MCP server that injects up-to-date, version-specific docs for the
  library under discussion (discord.py, asyncpg, PIL, pytest…), instead of the
  model's training-data memory of the API.
- **Verified ✓ (2026-06-12):** `upstash/context7`, 57.2k stars, release
  `@upstash/context7-mcp@3.2.0` published 2026-06-11 (actively maintained).
  Hosted endpoint `https://mcp.context7.com/mcp` now wants a `CONTEXT7_API_KEY`
  header (free tier exists); also runnable locally via npx.
- **Why us:** our recurring bug class "API used from memory" (e.g. the pinned
  `youtube-transcript-api<1.0` churn rule) is exactly what this addresses;
  discord.py is a fast-churning API.
- **Cost/risk:** third-party MCP server sees prompts/queries (external
  service); adds context overhead per use. Pin the version like CodeGraph.

### 3.2 Postgres MCP (Postgres MCP Pro) — live schema/EXPLAIN access

- **What:** MCP server giving the agent schema inspection, EXPLAIN/index
  analysis, health checks, and SQL execution against a running Postgres.
- **Verified ✓ (2026-06-12):** `crystaldba/postgres-mcp`, 2.9k stars, has a
  **`--access-mode=restricted`** read-only mode — the only mode we'd consider.
- **Why us:** sandbox sessions already run a live local Postgres for the test
  bot; today agents introspect it via ad-hoc `psql` in Bash. A read-only MCP
  makes migrations/`utils/db` work schema-aware.
- **Counterpoint:** `psql` via Bash already works and is zero-trust-surface;
  value-add is modest. Would be `.mcp.json`-level, not a "plugin" per se.

### 3.3 `pyright-lsp` (official marketplace) — language-server intelligence

- **What:** real jump-to-def / type diagnostics in-session via Pyright.
- **Why us:** could complement CodeGraph (whose caller/dead-code edges have
  known false positives) with ground-truth symbol resolution.
- **Counterpoint:** mypy already runs in the CI mirror; LSP overhead on a
  1,400-file monorepo unknown; CodeGraph + grep discipline already encodes our
  trust tiers. **Trial-first candidate, not adopt-first.**

### 3.4 `security-guidance` (official) — vuln scan on every edit

- Complements (doesn't conflict with) `/security-review`. Low priority: the
  bot's attack surface is Discord-side authority checks, which our
  architecture rules + governance seams already police better than a generic
  OWASP scanner.

### Explicit skips

`superpowers` (752k installs, real and good — but its workflow would fight our
binding collaboration model) · claude-mem / memory plugins (journal is
first-class here) · `code-review`/`pr-review-toolkit`/`feature-dev`/
`commit-commands` (native or repo-skill duplicates) · `connect-apps`/Composio
(no SaaS-integration need) · `playwright` (no web dashboard yet — revisit when
the Q-0042 staged-Someday website moves) · Discord "Channels" plugins (run
Claude *from* Discord; unrelated to bot development).

## 4. Supply-chain posture (why ask-first is right here)

Plugins can ship **hooks (arbitrary code at session start/edit/stop)** and MCP
servers (tool access). Public CVEs in 2026 (agent-reported: CVE-2025-59536,
CVE-2026-21852 — settings-file rewrite → code exec / key exfiltration) target
exactly the `.claude/settings.json` / `~/.claude.json` seam. Our current
posture — repo-owned hooks only, one pinned MCP server — is the defensible
end of the spectrum. Adoption rules if Q-0096 approves anything:

1. **Pin** (sha or exact version) like the CodeGraph pin; auto-update off.
2. **Audit the bundle** (`claude plugin` details / read the repo) for hooks
   before enabling — prefer plugins that are MCP/skills-only, no hooks.
3. **Provenance header discipline** (Q-0014): record why/when/`unverified —
   confirm output across sessions` in this file + CLAUDE.md if adopted.
4. Prefer plain `.mcp.json` entries over plugin wrappers when the value is
   just an MCP server (Postgres, Context7) — smaller trust surface, and it
   matches how CodeGraph is already wired.

## 5. Recommendation

**Adopt nothing silently.** Proposed to the owner as Q-0096:

- **Yes (trial):** Context7 — as a pinned `.mcp.json` server (not the plugin
  wrapper), trialed for a few sessions on discord.py/asyncpg work, verified
  per Q-0014 before being declared trusted.
- **Optional:** read-only Postgres MCP for sandbox DB work.
- **Trial-only if curious:** `pyright-lsp`.
- **No:** workflow/memory/review plugins — they duplicate or fight the system
  we deliberately built.

## Lifecycle

- **State:** captured → routed (discuss) → **partially adopted** — owner decision **Q-0096**
  answered 2026-06-12.
- **Context7 — ADOPTED (trial), 2026-06-12.** Owner approved; wired as a pinned `.mcp.json`
  server (`@upstash/context7-mcp@3.2.0`, keyless to start), approved via
  `enabledMcpjsonServers`, tools pre-allowed. Operational reference + key-setup + the Q-0105
  delete-if-unreliable note: [`../operations/mcp-servers.md`](../operations/mcp-servers.md).
  Still **unverified** — confirm its docs against ground truth across sessions before trusting.
- The read-only Postgres MCP and `pyright-lsp` remain **not adopted** (open under Q-0096).

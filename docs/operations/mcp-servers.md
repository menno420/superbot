# MCP servers — what we run and when to use them

> **Status:** `reference` — the MCP servers wired in `.mcp.json` (approved via
> `enabledMcpjsonServers` in `.claude/settings.json`). `.mcp.json` is the source of truth
> for what is actually wired; this doc is the *why / when / how* and the provenance.

MCP servers give agents tools beyond the built-ins. We run them **pinned** (the protocol
output can churn) and **few** (each is a trust surface). Adoption is owner-gated.

## Wired servers

| Server | Pin | What it's for | Reference |
|---|---|---|---|
| `codegraph` | `@optave/codegraph@3.11.2` | Tree-sitter knowledge graph of every symbol/edge — navigating unfamiliar multi-file code | [`codegraph-usage.md`](../codegraph-usage.md) |
| `context7` | `@upstash/context7-mcp@3.2.0` | Live, version-specific **library docs** injected on demand — kills the "API used from memory" bug class | below |

## Context7 — usage

Two tools:
- `resolve-library-id` — map a library name ("discord.py", "asyncpg", "pillow") → a
  Context7 library ID.
- `query-docs` — fetch the **current** docs/snippets for that ID, with a specific query
  (e.g. "app_commands slash command definition", "asyncpg connection pooling"). Call
  `resolve-library-id` first to get the `/org/project` ID.

**When to use it:** before writing or reviewing non-trivial code against a fast-churning
third-party library — `discord.py` above all, also `asyncpg`, `Pillow`, `pytest`. Prefer it
over your training-data memory of an API; that memory is the source of our recurring
"signature changed since cutoff" runtime bugs (the reason `requirements.txt` pins
`youtube-transcript-api<1.0`). Skip it for stdlib and for our own code (use CodeGraph /
`context_map.py` there).

### API key (maintainer action — optional but recommended)

Context7 works **keyless** at a conservative rate limit, which is how it's wired now. Its
free tier is **~500 requests/month (with a key)** as of Jan 2026 — fine for trialing, a
ceiling if it becomes heavily used.

To raise the limit:
1. Create a free key at `context7.com/dashboard` → "Create API Key" (shown once — copy it).
2. Add it to **this Claude Code web environment's** settings as a secret/env var
   `CONTEXT7_API_KEY` (agents cannot set environment secrets — this is a maintainer step).
3. Add the env reference to the `context7` entry in `.mcp.json`:
   `"env": { "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}" }`. The key stays in the environment;
   the repo only references it by name (never commit the key).

## Reliability / provenance (Q-0105)

- **`context7`** — added **2026-06-12** (owner-approved, Q-0096). *Why:* reduce the
  "API-from-memory" bug class on `discord.py`/`asyncpg`. **Verified 1× (2026-06-12):** resolved
  `discord.py` → `/rapptz/discord.py` and `query-docs` returned *current, accurate* API — the
  post-2.0 button-callback signature order **and** the Components-V2 `LayoutView`/`Container`/
  `Section` APIs (discord.py 2.6, newer than the model's training). Still **unverified overall**
  — confirm a few more times across sessions before graduating it out of convenience status.
  **Delete if unreliable:** if its docs prove stale/wrong, the rate limit makes it useless, or
  it adds noise over several sessions, **remove the `.mcp.json` entry + the
  `enabledMcpjsonServers`/permission lines** — it is a convenience, not load-bearing.
- **`codegraph`** — verified/load-bearing (graduated out of "unverified"); reliability tiers +
  false-positive caveats live in [`codegraph-usage.md`](../codegraph-usage.md).

## Adding / removing a server

`.mcp.json` (server definition) + `.claude/settings.json` `enabledMcpjsonServers` (approval)
are both **executable config** → owner-gated (ask-first / a router Q-block), pinned, and
carry a provenance + delete-if-unreliable note here.

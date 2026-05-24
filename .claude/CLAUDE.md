<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`mcp__codegraph__*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file.

**Full trust matrix and verification rules: `docs/codegraph-usage.md` — read it before any refactor or dead-code decision.**

MCP startup: pinned via `npx -y @optave/codegraph@3.10.0 mcp` — no global install required. Build/rebuild index: `npx -y @optave/codegraph@3.10.0 build .` from the project root.

### What CodeGraph can and cannot do in this codebase

SuperBot uses function-body lazy imports, module-alias calls, and Discord decorator callbacks pervasively. These patterns are **invisible to CodeGraph's call-graph parser**. The result is that roughly half of all real call edges are missing from the graph.

**Reliable** — use freely:

| Question | Tool |
|---|---|
| "Where is X defined?" | `mcp__codegraph__where` |
| "Show me the source + signature of Y" | `mcp__codegraph__context` |
| "List all symbols in this file/directory" | `mcp__codegraph__list_functions` or `mcp__codegraph__where` with `file_mode=true` |
| "How complex is function Y?" | `mcp__codegraph__complexity` |
| "Which functions exceed complexity thresholds?" | `mcp__codegraph__check` (manifesto mode) |
| "What is the risk-ranked list of complex functions?" | `mcp__codegraph__triage` with `level=function` and `sort=complexity` |

**Use as hints only — always grep-verify before acting:**

| Question | Tool | Caveat |
|---|---|---|
| "What are the direct callers of Y?" | `mcp__codegraph__fn_impact` depth=1 or `mcp__codegraph__context` | Undercounts — lazy imports and aliased imports are invisible |
| "What does this file import/export?" | grep only (`file_deps` is broken) | Never use `file_deps`, `module_map`, or `impact_analysis` |

**Do not use — broken or requires unavailable pre-work:**

- `mcp__codegraph__execution_flow` — returns 0 entries regardless of target (confirmed broken)
- `mcp__codegraph__find_cycles` — always returns 0 cycles (file-level edges broken)
- `mcp__codegraph__communities` — always returns 0 communities (same root cause)
- `mcp__codegraph__co_changes` — requires `codegraph co-change --analyze` pre-run; returns nothing without it
- `mcp__codegraph__module_map` — returns 0 in/out edges for every file
- `mcp__codegraph__file_deps` — returns 0 imports and 0 imported-by for every file
- `mcp__codegraph__impact_analysis` — returns 0 file dependents
- `mcp__codegraph__triage` with `level=directory` — fanIn/fanOut always 0
- `mcp__codegraph__semantic_search` — requires `codegraph embed` pre-run

### Critical rules — non-negotiable

**1. `dead-unresolved` does not mean dead.**
The false-positive rate for the `dead-unresolved` role label is ~100% in this codebase. Verified active functions that CodeGraph incorrectly marks dead: `validate_registry`, `apply_operations`, `parse_message`, `request_shutdown`, `dispatch` (interaction_router), `resolve_execution`, `BlackjackCog.blackjack`, all `@bot.event` handlers, all `@commands.command` handlers. **Never delete or remove code based on this label alone.**

**2. Caller lists are lower bounds — always grep.**
After getting a caller list from `fn_impact` or `context`, run:
```
grep -rn "function_name\b" disbot/ --include="*.py"
```
Callers that use `from module import func` inside a function body, or call via `module.func()`, or import under an alias (`from base import X as _X`) are all invisible to CodeGraph.

**3. Name-collision false positives are dangerous.**
When two functions share the same short name in different classes or modules (e.g. `_resolve_channel` exists in both `chain_cog.py` as a module function and `channel_cog.py` as a class method), CodeGraph merges their caller graphs. Verified case: CodeGraph claimed 14 callers for `chain_cog._resolve_channel`; the true count is 3. The other 11 were callers of `ChannelCog._resolve_channel` — a completely separate method. **When caller files look unexpected, check for same-name functions in those files.**

**4. Discord decorators create invisible entry points.**
`@bot.event`, `@commands.command`, `@commands.group`, `@app_commands.command`, and Cog listener methods are all `dead-unresolved` in CodeGraph regardless of whether they are active. Never treat a command handler or event handler as dead.

**5. `callees` lists are often empty — read the source.**
Functions that contain `from X import Y` inside their body will show `callees: []` even if they call many things. Always read the source directly to find what a function calls.

### Rules of thumb

- **Use CodeGraph first for finding and reading code**, not for proving code is safe to delete.
- **`context` is the workhorse** for source + callers. Treat callers as a starting list, not a complete list.
- **Grep-verify every caller list** before changing a function signature or moving a function.
- **Index lag**: after editing, run `npx -y @optave/codegraph@3.10.0 build .` before re-querying.

### Source files win

If CodeGraph output conflicts with what the source file says, **source files are authoritative**. Before editing any shared runtime, setup, settings, help/menu, database, or mutation pipeline code, read the exact target source files with the `Read` tool to confirm what's there.

### If `.codegraph/` doesn't exist

Run `npx -y @optave/codegraph@3.10.0 build .` from the project root. No global install is required — the MCP server starts through pinned `npx` automatically when Claude Code launches. If MCP tools are absent entirely, restart Claude Code after pulling this config; a restart is not needed just to rebuild the index.
<!-- CODEGRAPH_END -->

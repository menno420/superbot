# CodeGraph Usage Guide

CodeGraph provides a tree-sitter-parsed knowledge graph of every symbol, edge,
and file in the codebase. It is exposed to Claude Code via an MCP server.

---

## Activation checklist

1. Install the CLI: `npm install -g @optave/codegraph`
2. Build the index from the project root: `codegraph build .`
3. Confirm the index: `codegraph info` — look for `Active engine: native`
4. The `.claude.json` already configures the MCP server (`codegraph mcp`).
5. Restart Claude Code after installing to load the MCP server.

---

## Known-good MCP tools

These tools are confirmed exposed by the server (verified via `tools/list`) and
produce accurate results:

| MCP tool name | CLI equivalent | Purpose |
|---|---|---|
| `mcp__codegraph__where` | `codegraph where <name>` | Find a symbol by name — returns kind, file, line, signature |
| `mcp__codegraph__context` | `codegraph context <name>` | Full source + direct callers + callees + signature |
| `mcp__codegraph__fn_impact` | `codegraph fn-impact <name>` | Blast-radius analysis — what breaks if this changes |
| `mcp__codegraph__execution_flow` | `codegraph flow <name>` | Forward execution trace (callees) |
| `mcp__codegraph__query` | `codegraph query <name>` | Dependency chain / shortest path between symbols |
| `mcp__codegraph__file_deps` | `codegraph deps <file>` | What a file imports and what imports it |
| `mcp__codegraph__structure` | `codegraph structure <path>` | Full structural overview of a module |
| `mcp__codegraph__list_functions` | `codegraph brief <path>` | Symbols in a file or directory |
| `mcp__codegraph__semantic_search` | `codegraph search <query>` | Semantic / keyword symbol search |
| `mcp__codegraph__audit` | `codegraph audit <target>` | Per-function health metrics + impact |
| `mcp__codegraph__complexity` | `codegraph complexity <name>` | Cognitive / cyclomatic complexity |
| `mcp__codegraph__file_deps` | `codegraph deps <file>` | Import/export graph for a file |
| `mcp__codegraph__impact_analysis` | `codegraph impact <file>` | Transitive file-level impact |
| `mcp__codegraph__diff_impact` | `codegraph diff-impact` | Impact of current git changes |

The full tool list has 34 entries. The ones above cover the most common tasks.

---

## Known-bad / unreliable tool names

Do not use these:

| Name | Problem |
|---|---|
| `mcp__codegraph__module_map` | Returns 0 in/out edges for every file in this codebase despite 22 000+ edges existing in the graph. Do not use for connectivity analysis. |
| `mcp__codegraph__brief` (caller counts) | Overcounts callers. Reports call-site counts rather than distinct calling functions, and inflates further. Use `fn_impact` or `context` for accurate caller counts. |
| `mcp__codegraph__codegraph_status` | Does not exist. No tool in this server uses the `codegraph_` name prefix. |
| `mcp__codegraph__codegraph_search` | Does not exist. Use `mcp__codegraph__where` or `mcp__codegraph__semantic_search`. |
| `mcp__codegraph__codegraph_callers` | Does not exist. Use `mcp__codegraph__fn_impact` (Level 1) or `mcp__codegraph__context`. |
| `mcp__codegraph__codegraph_callees` | Does not exist. Use `mcp__codegraph__execution_flow`. |
| `mcp__codegraph__codegraph_impact` | Does not exist. Use `mcp__codegraph__fn_impact` or `mcp__codegraph__impact_analysis`. |
| `mcp__codegraph__codegraph_node` | Does not exist. Use `mcp__codegraph__where` + `mcp__codegraph__context`. |

---

## Rule: CodeGraph for exploration, source files for final truth

Use CodeGraph to orient yourself — find symbols, trace edges, understand blast
radius. Before making any edit, confirm the exact content with `Read` on the
target source file. If CodeGraph output conflicts with the source file, the
source file is authoritative.

### Python lazy-import limitation

CodeGraph cannot resolve call edges where the import happens inside a function
body:

```python
async def _apply(...):
    from services.setup_operations import apply_operations  # ← inside function
    batch = await apply_operations(ops, guild=guild, actor=actor)
```

Any function imported only via function-body imports will appear as
`dead-unresolved` with 0 callers even if it is widely used. When you see
`dead-unresolved`, grep for the symbol name to find its actual callers.

**Verified example**: `apply_operations` (setup_operations.py:215) is called
from `views/setup/final_review.py:235` and `views/setup/sections/identity.py:160`
but CodeGraph reports 0 callers because both call sites use function-body imports.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `codegraph: command not found` | `npm install -g @optave/codegraph` |
| "index not initialized" or empty results | `codegraph build .` from the project root |
| Stale index after editing files | `codegraph build .` to rebuild, or run `codegraph watch` for incremental updates |
| MCP tools unavailable in Claude Code | Restart Claude Code so it reloads the MCP server from `.claude.json` |
| `Active engine: wasm` in `codegraph info` | Performance is degraded. Rebuild the native binding: ensure `node-gyp` prerequisites are installed, then `npm rebuild better-sqlite3` inside the codegraph package. |
| `module_map` returns all zeros | Known bug for this codebase. Use `mcp__codegraph__structure` or `mcp__codegraph__list_functions` instead. |
| Caller count seems too high from `brief` | Use `mcp__codegraph__fn_impact` or `mcp__codegraph__context` for accurate distinct-caller counts. |

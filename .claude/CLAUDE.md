<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`mcp__codegraph__*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. Reads are sub-millisecond and return structural information grep cannot.

MCP startup: pinned via `npx -y @optave/codegraph@3.10.0 mcp` — no global install required. Build/rebuild index: `npx -y @optave/codegraph@3.10.0 build .` from the project root.

### Use CodeGraph first for structural exploration

Use CodeGraph for **structural** questions — what calls what, what would break, where is X defined, what is X's signature. Use native grep/Read only for **literal text** queries (string contents, comments, log messages) or after you already have a specific file open.

| Question | Tool |
|---|---|
| "Where is X defined?" / "Find symbol named X" | `mcp__codegraph__where` |
| "Full source + callers + callees for Y" | `mcp__codegraph__context` |
| "What calls function Y?" (direct callers) | `mcp__codegraph__fn_impact` Level 1 |
| "What does Y call?" (callees) | `mcp__codegraph__execution_flow` |
| "What would break if I changed Z?" | `mcp__codegraph__fn_impact` |
| "What files/functions exist under path/" | `mcp__codegraph__list_functions` |
| "What does this file import/export?" | grep (file_deps is broken — see limitations) |
| "Is the index healthy? / graph stats" | `mcp__codegraph__audit` |

### Rules of thumb

- **Use CodeGraph first** for structural exploration; then verify with source files before editing.
- **Don't grep first** when looking up a symbol by name. `mcp__codegraph__where` is faster and returns kind + location + signature in one call.
- **`context` is the workhorse** — it returns source, direct callers, callees, and signature in one call. Prefer it over chaining `where` + `fn_impact`.
- **Index lag**: after editing a file run `npx -y @optave/codegraph@3.10.0 build .` to rebuild; don't re-query immediately after editing in the same turn without rebuilding.

### Known limitations — do not trust these uncritically

- **`mcp__codegraph__module_map` is broken for this codebase.** It returns 0 in/out edges for every file despite 22 000+ edges existing in the index. Do not use it for connectivity analysis.
- **`mcp__codegraph__brief` reports transitive impact count, not direct caller count.** The number shown as "callers" equals the total transitive dependent count (same as `fn_impact` total), not just the distinct functions that directly call the symbol. Use `mcp__codegraph__fn_impact` Level 1 or `mcp__codegraph__context` for accurate direct-caller counts.
- **`mcp__codegraph__file_deps` shows 0 imports and 0 imported-by for every file.** The file-level edge traversal is broken; it returns symbol definitions correctly but import/dependency edges are always empty. Do not use it for import graph analysis.
- **`mcp__codegraph__impact_analysis` returns 0 file dependents.** File-level transitive impact is broken by the same underlying edge issue. Use `mcp__codegraph__fn_impact` for function-level blast-radius instead.
- **`mcp__codegraph__structure` shows `<-0 ->0` connectivity for all files.** The per-file in/out edge counts are always zero. The symbol counts and line counts are accurate; the connectivity data is not.
- **`mcp__codegraph__semantic_search` requires embeddings to be built first.** Run `npx -y @optave/codegraph@3.10.0 embed` from the project root before using it; without embeddings it returns an error. Embeddings are not built by default.
- **Python lazy/function-body imports are not resolved.** When a function is imported inside a function body (`from services.X import Y` inside a method), CodeGraph cannot trace the call edge. Affected symbols are labelled `dead-unresolved` with 0 callers even when they are widely used. Always grep-verify when a symbol is marked `dead-unresolved`.

### Source files win

If CodeGraph output conflicts with what the source file says, **source files are authoritative**. Before editing any shared runtime, setup, settings, help/menu, database, or mutation pipeline code, read the exact target source files with the `Read` tool to confirm what's there.

### If `.codegraph/` doesn't exist

Run `npx -y @optave/codegraph@3.10.0 build .` from the project root. No global install is required — the MCP server starts through pinned `npx` automatically when Claude Code launches. If MCP tools are absent entirely, restart Claude Code after pulling this config; a restart is not needed just to rebuild the index.
<!-- CODEGRAPH_END -->

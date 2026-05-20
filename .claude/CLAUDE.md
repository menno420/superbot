<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`mcp__codegraph__*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. Reads are sub-millisecond and return structural information grep cannot.

Install: `npm install -g @optave/codegraph` — Build/rebuild index: `codegraph build .` from the project root.

### Use CodeGraph first for structural exploration

Use CodeGraph for **structural** questions — what calls what, what would break, where is X defined, what is X's signature. Use native grep/Read only for **literal text** queries (string contents, comments, log messages) or after you already have a specific file open.

| Question | Tool |
|---|---|
| "Where is X defined?" / "Find symbol named X" | `mcp__codegraph__where` |
| "Full source + callers + callees for Y" | `mcp__codegraph__context` |
| "What calls function Y?" (direct callers) | `mcp__codegraph__fn_impact` Level 1 |
| "What does Y call?" (callees) | `mcp__codegraph__execution_flow` |
| "What would break if I changed Z?" | `mcp__codegraph__fn_impact` |
| "Survey an unfamiliar module/topic" | `mcp__codegraph__structure` |
| "What files/functions exist under path/" | `mcp__codegraph__list_functions` |
| "What does this file import/export?" | `mcp__codegraph__file_deps` |
| "Is the index healthy? / graph stats" | `mcp__codegraph__audit` |

### Rules of thumb

- **Use CodeGraph first** for structural exploration; then verify with source files before editing.
- **Don't grep first** when looking up a symbol by name. `mcp__codegraph__where` is faster and returns kind + location + signature in one call.
- **`context` is the workhorse** — it returns source, direct callers, callees, and signature in one call. Prefer it over chaining `where` + `fn_impact`.
- **Index lag**: after editing a file run `codegraph build .` to rebuild; don't re-query immediately after editing in the same turn without rebuilding.

### Known limitations — do not trust these uncritically

- **`mcp__codegraph__module_map` is broken for this codebase.** It returns 0 in/out edges for every file despite 22 000+ edges existing in the index. Do not use it for connectivity analysis.
- **`mcp__codegraph__brief` overcounts callers.** It reports call-site counts (not distinct calling functions) and inflates the numbers further. Do not use its caller count as authoritative; use `mcp__codegraph__fn_impact` or `mcp__codegraph__context` instead.
- **Python lazy/function-body imports are not resolved.** When a function is imported inside a function body (`from services.X import Y` inside a method), CodeGraph cannot trace the call edge. Affected symbols are labelled `dead-unresolved` with 0 callers even when they are widely used. Always grep-verify when a symbol is marked `dead-unresolved`.

### Source files win

If CodeGraph output conflicts with what the source file says, **source files are authoritative**. Before editing any shared runtime, setup, settings, help/menu, database, or mutation pipeline code, read the exact target source files with the `Read` tool to confirm what's there.

### If `.codegraph/` doesn't exist

Run `codegraph build .` from the project root. If `codegraph` is not installed, run `npm install -g @optave/codegraph` first.
<!-- CODEGRAPH_END -->

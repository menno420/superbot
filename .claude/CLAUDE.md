<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`mcp__codegraph__*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. Reads are sub-millisecond and return structural information grep cannot.

Install: `npm install -g @optave/codegraph` — Build/rebuild index: `codegraph build .` from the project root.

### When to prefer codegraph over native search

Use codegraph for **structural** questions — what calls what, what would break, where is X defined, what is X's signature. Use native grep/read only for **literal text** queries (string contents, comments, log messages) or after you already have a specific file open.

| Question | Tool |
|---|---|
| "Where is X defined?" / "Find symbol named X" | `mcp__codegraph__where` |
| "What calls function Y?" | `mcp__codegraph__query` (mode: callers) |
| "What does Y call?" | `mcp__codegraph__execution_flow` |
| "What would break if I changed Z?" | `mcp__codegraph__fn_impact` |
| "Show me Y's signature / source / docstring" | `mcp__codegraph__context` |
| "Give me focused context for a task/area" | `mcp__codegraph__context` |
| "Survey an unfamiliar module/topic" | `mcp__codegraph__structure` or `mcp__codegraph__module_map` |
| "What files/functions exist under path/" | `mcp__codegraph__list_functions` |
| "What does this file import/export?" | `mcp__codegraph__file_deps` |
| "Is the index healthy? / graph stats" | `mcp__codegraph__audit` |

### Rules of thumb

- **Trust codegraph results.** They come from a full AST parse. Do NOT re-verify them with grep — that's slower, less accurate, and wastes context.
- **Don't grep first** when looking up a symbol by name. `mcp__codegraph__where` is faster and returns kind + location + signature in one call.
- **Don't chain `where` + `context`** when you just want full context — `context` alone is one call.
- **`structure` / `module_map` are the heavy hitters** for unfamiliar areas — return full structural info but are token-heavy. If your harness supports parallel subagents, spawn one for explore-class questions to keep main session context clean.
- **Index lag**: after editing a file run `codegraph build .` to rebuild; don't re-query immediately after editing in the same turn without rebuilding.

### If `.codegraph/` doesn't exist

Run `codegraph build .` from the project root to build the index. If `codegraph` is not installed, run `npm install -g @optave/codegraph` first.
<!-- CODEGRAPH_END -->

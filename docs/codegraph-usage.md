# CodeGraph Usage Guide — SuperBot

> **Status:** `binding` — CodeGraph trigger table, trust matrix, and safety rules.
> `.claude/CLAUDE.md` retains only the critical do-not-delete rules for working context.

> **This is the full reference. `.claude/CLAUDE.md` contains only the five critical
> safety rules (dead-unresolved, name-collision, Discord decorators, empty callees,
> blind-spot wiring). Everything else lives here.**
>
> Last evaluated: 2026-05-24, codegraph 3.10.0, against the live repo.
> Evaluation method: every claim below was verified by running the tool, then
> grep-searching or source-reading to confirm or refute the result.

---

## When to use automatically — trigger table

Reach for CodeGraph **without being asked** whenever the task involves any of the following:

| Situation | What to do first |
|---|---|
| Finding where a symbol is defined | `mcp__codegraph__where("symbol_name")` before any grep or Read |
| Reading a function you haven't seen before | `mcp__codegraph__context("name")` for source + signature in one call |
| Understanding what calls a function | `mcp__codegraph__fn_impact("name", depth=1)` then grep-verify |
| Listing what exists in a file or directory | `mcp__codegraph__list_functions(file="path/")` before opening files blindly |
| Assessing complexity before a refactor | `mcp__codegraph__complexity(file="path/")` or `mcp__codegraph__triage(level=function, sort=complexity)` |
| Planning any edit to shared code | `mcp__codegraph__context` to read source + get starting caller list, then grep |
| Bug investigation across multiple functions | `mcp__codegraph__context` on each candidate — faster than chained Read calls |

**Default order for any unfamiliar code:** `where` → `context` → grep-verify → `Read` only if more source detail is needed.

**Contained vs. unfamiliar:** for a *contained* change — a known refactor, adding one function, a localised bug — `python3.10 scripts/context_map.py <file>` + targeted grep is usually faster than the graph. Reach for CodeGraph when navigating *unfamiliar* code across many files.

**Before your first edit to a `disbot/*.py` file, run the file context map:**
`python3.10 scripts/context_map.py <path>` (~0.2 s). It surfaces module-level **and** lazy/function-body (CodeGraph-invisible) imports, reverse importers, blast radius, related docs/tests, a recommended read set, and the post-edit checks to run. A `PreToolUse` hook (`scripts/claude_pre_edit.py`) shows it automatically once per file per session, but run it yourself when planning a change. Full reference: `docs/context-map-tooling.md`.

---

## Why CodeGraph is partially unreliable for SuperBot

SuperBot uses three import patterns that are invisible to CodeGraph's
tree-sitter parser:

1. **Function-body lazy imports** — `from services.X import Y` *inside* a
   function or method body. The most common pattern in this codebase.
2. **Module-alias calls** — `_lifecycle.request_shutdown()`,
   `interaction_router.dispatch()`, `parsing.parse_message()`. The target
   module is imported at the top but called via attribute access on the alias;
   CodeGraph cannot resolve the call.
3. **Discord decorator callbacks** — `@bot.event`, `@commands.command`,
   `@commands.group`, `@app_commands.command`. These register methods as live
   entry points through the Discord framework; CodeGraph sees no call edge.

These are not edge cases. Every cog command handler, every bot event handler,
every DB pool call (`pool.get().fetchrow(...)`), and large portions of the
lifecycle, governance, and view layers rely on at least one of these patterns.

Consequence: roughly **40–60 % of real call edges are absent from the graph**,
and the `dead-unresolved` role label has a **~100 % false-positive rate** for
functions called through any of these patterns.

---

## Activation checklist

No global install is required. The MCP server starts via pinned `npx` on every
Claude Code launch.

1. Verify the package resolves: `npx -y @optave/codegraph@3.10.0 --version`
2. Build the index (first time or fresh clone):
   `npx -y @optave/codegraph@3.10.0 build .`
3. Confirm the index: `npx -y @optave/codegraph@3.10.0 stats` — look for
   `Active engine: native`
4. Inside Claude Code, confirm MCP tools load by calling
   `mcp__codegraph__where` on any known symbol.

> If MCP tools are available but results are empty, the index is missing.
> Run the `build` command — a Claude restart is **not** needed.
> If MCP tools are absent entirely, restart Claude Code.

---

## Trust matrix

### Tier 1 — Reliable: use freely, no mandatory verification

| Tool | What it does | Why it is reliable |
|---|---|---|
| `mcp__codegraph__where` | Locate a symbol — file, line, kind, signature | Definition location is parsed directly from the AST; no edge traversal |
| `mcp__codegraph__list_functions` | Enumerate all symbols in a file or path | Same — pure AST enumeration |
| `mcp__codegraph__where` (file_mode=true) | List all symbols in a specific file | Accurate; ignore `imports`/`importedBy` fields (always empty) |
| `mcp__codegraph__context` — source text | Read the source code of a function | Source extraction is reliable |
| `mcp__codegraph__context` — signature | Read the function signature | Reliable |
| `mcp__codegraph__complexity` | Cognitive, cyclomatic, nesting, MI per function | Pure AST metric; no edge data required |
| `mcp__codegraph__check` (manifesto mode) | Complexity and nesting threshold violations | Reliable for function-level metrics; file-level thresholds are unconfigured so always pass |
| `mcp__codegraph__triage` (`level=function`, `sort=complexity`) | Rank functions by complexity | Complexity signal is accurate; use for prioritisation |
| `mcp__codegraph__audit` (function target) — source, complexity, health | Source text and metrics for a named function | Reliable for the same reasons as `context` and `complexity` |

### Tier 2 — Hints only: use as a starting point, always grep-verify

| Tool | What it returns | What it misses | Rule |
|---|---|---|---|
| `mcp__codegraph__fn_impact` (depth=1) | Direct callers — **lower bound only** | Lazy-import callers, aliased-import callers, `self.method()` calls | After getting the list, grep the full repo for the symbol name before acting |
| `mcp__codegraph__context` — callers list | Same as fn_impact level 1 | Same | Same |
| `mcp__codegraph__fn_impact` (depth > 1) | Transitive blast radius — lower bound | Cascades all the Level-1 misses | Use for relative ranking only; do not treat as complete |
| `mcp__codegraph__audit` (function target) — callers/impact | Same as fn_impact | Same | Same |
| `mcp__codegraph__triage` (`level=function`, `sort=risk`) | Risk-ranked list by fanIn + complexity | fanIn undercounts; churn is always 0 (no co-change pre-analysis) | Useful for hot-spot identification; ignore fanIn absolute value |

### Tier 3 — Do not use: confirmed broken or requires unavailable pre-work

| Tool | Problem |
|---|---|
| `mcp__codegraph__execution_flow` (list=true or forward trace) | Returns 0 entries regardless of target. Confirmed broken. |
| `mcp__codegraph__find_cycles` | Always returns 0 cycles. File-level edge traversal is broken; no edges means no cycles detected. |
| `mcp__codegraph__communities` | Always returns 0 communities, 0 modularity. Same root cause as find_cycles. |
| `mcp__codegraph__co_changes` | Requires `codegraph co-change --analyze` pre-run. Returns 0 pairs without it. Not run in this repo. |
| `mcp__codegraph__module_map` | Returns 0 in/out edges for every file. File-level connectivity is broken. |
| `mcp__codegraph__file_deps` | Returns 0 imports and 0 imported-by for every file. |
| `mcp__codegraph__impact_analysis` | Returns 0 file dependents. Same underlying broken file-edge issue. |
| `mcp__codegraph__structure` (connectivity) | Per-file `<-0 ->0` always. Symbol counts and line counts are accurate; connectivity is not. |
| `mcp__codegraph__triage` (`level=directory`) | fanIn and fanOut are always 0. Coupling is always 0. |
| `mcp__codegraph__semantic_search` | Requires `codegraph embed` pre-run. Returns an error without embeddings. |
| `mcp__codegraph__brief` (caller counts) | The count is the transitive total, not direct callers. Use `fn_impact` Level 1 instead. |
| `mcp__codegraph__triage` (`role=dead`) | False-positive rate ~100 %. See dead-code section below. |

---

## Dead code: do not trust `dead-unresolved`

The `dead-unresolved` role label marks symbols with 0 traceable callers. In
this codebase, that label is almost always wrong because the patterns that call
these functions are invisible to CodeGraph.

**Verified false positives — all marked `dead-unresolved`, all actively used:**

| Symbol | File | Why it appears dead | How it is actually called |
|---|---|---|---|
| `validate_registry` | `utils/subsystem_registry.py:736` | Imported inside `main()` body | `bot1.py:689` function-body import |
| `apply_operations` | `services/setup_operations.py:499` | Imported inside callback bodies | `views/setup/final_review.py:352, 398` function-body imports |
| `parse_message` | `cogs/counting/parsing.py:37` | Called as `parsing.parse_message(...)` | `cogs/counting/handler.py:93` module-alias call |
| `request_shutdown` | `core/runtime/lifecycle.py:191` | Called as `_lifecycle.request_shutdown(...)` | `bot1.py:93` module-alias call |
| `dispatch` | `core/runtime/interaction_router.py:74` | Called via lazy import in `on_interaction` | `bot1.py:212` function-body import + module-alias call |
| `resolve_execution` | `governance/execution.py:157` | Called as `governance_service.resolve_execution(...)` | `core/runtime/ui_permissions.py:38` |
| `forget_guild_capabilities` | `governance/execution.py:92` | Lazy import in guild lifecycle | `guild_lifecycle.py:401` function-body import |
| `forget_guild` | `governance/cache.py:108` | Lazy import in guild lifecycle | `guild_lifecycle.py:411` function-body import |
| `BlackjackCog.blackjack` | `cogs/blackjack_cog.py:409` | `@commands.command` decorator invisible | Live Discord command |
| `Cleanup.cleanup_history` | `cogs/cleanup_cog.py:188` | `@commands.command` decorator invisible | Live Discord command |
| `Cleanup.remove_unwanted_message` | `cogs/cleanup_cog.py:107` | `@bot.listen` invisible | Live message event listener |
| All `on_ready` handlers | Various cog files | `@bot.event` / Cog listener invisible | Discord gateway event |
| `ChannelCog._resolve_channel` | `cogs/channel_cog.py:73` | `self.method()` calls not traced | Called as `self._resolve_channel(...)` 12 times within the class |

**Rule: before claiming anything is dead or safe to remove:**
1. `grep -rn "symbol_name\b" disbot/ --include="*.py"` — look for lazy imports and alias calls
2. Check whether it has `@commands.command`, `@bot.event`, `@app_commands.command`, or `@tasks.loop`
3. Check whether it is passed as a callback (signal handler, task spawn, event bus listener)
4. If all three checks are clean AND it's not a test-only fixture, it *may* be unused — flag for human review before removing

---

## Name-collision false positives

When two functions share the same short name across different modules or
classes, CodeGraph merges their call graphs under that name.

**Verified case: `_resolve_channel`**

- `chain_cog.py:371` — module-level function `_resolve_channel(interaction, raw)`
- `channel_cog.py:73` — class method `ChannelCog._resolve_channel(self, guild, query)`

These are completely independent. `channel_cog.py` does not import from
`chain_cog.py`. Yet CodeGraph's `fn_impact` for `chain_cog._resolve_channel`
returned 14 callers: the real 3 in `chain_cog.py` plus 11 `self._resolve_channel`
calls inside `ChannelCog` — a fabricated cross-cog dependency.

**Rule: when callers appear in unexpected files:**
1. Run `where(ClassName._resolve_channel)` — check if the unexpected file has
   its own same-named symbol
2. Read the actual call site in the flagged file to confirm whether it calls
   the function you care about

Other names at risk in this codebase: `get`, `setup`, `dispatch`, `build_embed`,
`on_error`, `on_timeout`, `collect`, `clear`.

---

## Blind spots — full catalogue

| Pattern | Example | CodeGraph result |
|---|---|---|
| Function-body lazy import | `from services.X import Y` inside a method | Y shows `dead-unresolved`, callers: [] |
| Module-alias call | `_lifecycle.request_shutdown()` | request_shutdown shows callers: [] |
| `self.method()` within class | `self._resolve_channel(...)` in ChannelCog | method shows dead-unresolved, uses: [] |
| Import alias | `from views.base import handle_view_error as _on_view_error` | handle_view_error misses 4 of 5 real callers |
| `@bot.event` decorator | `@bot.event async def on_ready()` | on_ready: dead-unresolved, callers: [] |
| `@commands.command` decorator | `@commands.command(name="cleanup")` | method: dead-unresolved |
| `@app_commands.command` decorator | `@app_commands.command(name="admin")` | method: dead-unresolved |
| `@commands.group` subcommands | `@settings_root.command(name="access")` | method: dead-unresolved |
| `signal.signal()` registration | `signal.signal(SIGTERM, _begin_shutdown)` | _begin_shutdown: callers: [] |
| DB pool chain | `pool.get().fetchrow(...)` | fetchrow callee not traced |
| Passed as callback | `tasks.spawn("name", coro)` | coro: callers: [] |
| Optional import (try/except) | `try: from pythonjsonlogger import ...` | import not resolved |
| Same-name collision | `_resolve_channel` in chain vs channel cog | inflated/merged caller graph |
| `callees` of lazy-importing fn | Any fn that lazy-imports before calling | callees: [] |

---

## Mandatory verification checklist before editing code

Before changing a function's signature, moving it, or removing it:

- [ ] `grep -rn "function_name\b" disbot/ --include="*.py"` — find all uses
- [ ] `grep -rn "module_name\.function_name" disbot/ --include="*.py"` — find module-alias calls
- [ ] Check for import aliasing: `grep -rn "import function_name as"` and `grep -rn "from.*import.*function_name"`
- [ ] Confirm no `@commands.command`, `@bot.event`, `@app_commands.command` decorators on the target
- [ ] Read the function body — if it contains `from X import Y`, trace those callees manually
- [ ] If CodeGraph reported unexpected callers in unrelated files, check for same-named symbols in those files

---

## When CodeGraph caller counts ARE reliable

Caller counts from `fn_impact` / `context` are accurate when callers use
**top-level module imports and call the function directly by name**:

```python
# Top of module:
from views.base import send_panel

# Later in a command handler:
await send_panel(ctx, embed=embed, view=view)
```

`send_panel` was verified to have exactly 22 callers this way — all confirmed
correct by source inspection. This is the pattern where CodeGraph is reliable.

The pattern fails when callers use:
```python
# Inside a function body (lazy):
from services.setup_operations import apply_operations
# OR via module alias:
await interaction_router.dispatch(interaction)
# OR via import alias:
from views.base import handle_view_error as _on_view_error
```

---

## Dry-run: safe CodeGraph workflow for a refactor

**Goal:** Change the signature of `send_panel` in `views/base.py`.

```
Step 1 — Locate
  mcp__codegraph__where("send_panel")
  → views/base.py:23, kind=function  ✓

Step 2 — Read source
  mcp__codegraph__context("send_panel", depth=1, no_tests=True)
  → Source: 19 lines. Takes (ctx, *, embed, view). Returns discord.Message.
  → Callers: 22 methods listed.

Step 3 — Grep-verify callers (MANDATORY)
  grep -rn "send_panel(" disbot/ --include="*.py" | grep -v "test_"
  → Returns 22 matches — matches CodeGraph exactly.
  ✓ Caller list is complete in this case (all use top-level imports).

Step 4 — Check for aliased imports
  grep -rn "import send_panel as\|send_panel as " disbot/ --include="*.py"
  → 0 results. No aliasing.

Step 5 — Confirm callees by reading body
  Source shows: ctx.send(embed=embed, view=view) + view.message = msg
  → Callees are on Discord objects — not traceable by CodeGraph. Expected.

Step 6 — Assess safety
  All 22 callers use keyword args (embed=..., view=...).
  Adding a keyword param with a default is safe.
  Changing any existing param name or making a param required → list all 22
  callers and stop for human review.

Step 7 — Stop condition
  If the change makes a param required AND callers span multiple cogs and
  views → do not proceed without explicit approval. The blast radius is real.
```

---

## Prompt snippet for future agents

Paste this into any refactor-focused session prompt to enforce safe CodeGraph usage:

```
CodeGraph rules for this session:

TRUSTED (use freely): mcp__codegraph__where, mcp__codegraph__list_functions,
mcp__codegraph__context (source/signature only), mcp__codegraph__complexity,
mcp__codegraph__check (manifesto), mcp__codegraph__triage (level=function, sort=complexity).

HINTS ONLY (always grep-verify after): mcp__codegraph__fn_impact (depth=1),
mcp__codegraph__context callers list.

DO NOT USE: execution_flow, find_cycles, communities, co_changes, module_map,
file_deps, impact_analysis, triage(level=directory), triage(role=dead).

BEFORE any edit:
1. grep -rn "symbol_name\b" disbot/ --include="*.py"
2. Check for @commands.command / @bot.event / @app_commands.command decorators
3. Check the function body for lazy imports (from X import Y inside the body)
4. If callers appear in unexpected files, check those files for a same-named symbol

dead-unresolved = CodeGraph limitation, NOT evidence the code is unused.
Caller lists are lower bounds. Callee lists are empty when lazy imports are used.
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| MCP tools unavailable and index present | Restart Claude Code — the `npx` MCP server is loaded once at session init |
| MCP tools available but empty results | Index is missing. Run `npx -y @optave/codegraph@3.10.0 build .` — no restart needed |
| Stale index after editing files | `npx -y @optave/codegraph@3.10.0 build .` to rebuild |
| `Active engine: wasm` in stats | Performance degraded. Rebuild the native binding (`npm rebuild better-sqlite3` inside the codegraph package). |
| `execution_flow` returns 0 entries | Known broken — do not use. Use grep for forward tracing. |
| `find_cycles` / `communities` return 0 | Known broken — file-level edges are broken in this index. Do not use. |
| `co_changes` returns 0 pairs | Requires `codegraph co-change --analyze` pre-run. Not run in this repo. |
| `module_map` returns all zeros | Known broken. Use `fn_impact` or `context` for function-level connectivity. |
| `file_deps` shows 0 imports | Known broken. Use grep to trace cross-file references. |
| `impact_analysis` returns 0 dependents | Known broken. Use `fn_impact` for blast-radius. |
| `semantic_search` returns "No embeddings" | Run `npx -y @optave/codegraph@3.10.0 embed` first. |
| `brief` caller count seems too high | Count is transitive total, not direct callers. Use `fn_impact` Level 1. |
| Caller list misses known callers | Callers use lazy imports or module-alias calls — grep-verify always. |
| Unexpected callers in unrelated files | Name-collision: check whether those files have a same-named function/method. |

<!-- READ_FIRST_START -->
## Read first — agent orientation

Before proposing or implementing **any** non-trivial change, open
**`docs/AGENT_ORIENTATION.md`** and follow the "Reading order by
task" section that matches what you are doing. It is short, points
you at the binding contracts, and distinguishes them from the
historical roadmap docs.

Three binding docs underlie almost every decision in this codebase:

1. **`docs/architecture.md`** — layering, invariants, decomposition rules.
2. **`docs/ownership.md`** — which service / pipeline owns each table, event, and write.
3. **`docs/runtime_contracts.md`** — lifecycle guarantees and failure modes.

Two more bind common operations:

- **`docs/repo-navigation-map.md`** — where things live; where new code goes.
- **`docs/helper-policy.md`** — when to create / move / promote a helper. Read this **before** putting a function in `utils/`, `services/`, or `views/base.py`.

When a doc and a source file disagree, the source file wins (see
"Source files win" below). Documents are pinned to the registry where
practical (`tests/unit/docs/`), but the layering rules are enforced
by review, not by CI.

<!-- READ_FIRST_END -->

<!-- CI_PARITY_START -->
## Match CI exactly when running checks locally

CI runs **Python 3.10** (`.github/workflows/code-quality.yml`). Running formatters / mypy / pytest under any other interpreter produces silent false negatives — a missing transitive dependency is typed as `Any` under one version and as an attribute error under another, and the local check passes while CI fails. PR #338 hit this exact trap.

**Rules:**

1. Always run formatters / mypy / pytest via `python3.10 -m <tool>` — never bare `black`, `mypy`, `pytest`, or `python3 -m …`. The Stop hook (`scripts/claude_stop_check.py`) already does this.
2. Before pushing, run the full pre-PR suite:
   ```
   python3.10 scripts/check_quality.py --check-only && python3.10 -m pytest tests/ -q
   ```
   The Stop hook prints this same command at end of every turn touching `disbot/*.py`.
3. The `PostToolUse` hook (`scripts/claude_post_edit.py`) auto-fixes black/isort/ruff on every edit and **prints a loud warning** when it changes the file. Read the warning — it means something landed that wasn't already CI-clean.
4. Pin third-party packages where the public API has churned (see `youtube-transcript-api<1.0` in `requirements.txt` for the canonical example). Unpinned `>=X.Y` resolves to whatever's latest in CI's fresh install, even if your local env still has the old version cached.

<!-- CI_PARITY_END -->

<!-- CODEGRAPH_START -->
## CodeGraph

This project has a CodeGraph MCP server (`mcp__codegraph__*` tools) configured. CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file.

**Full trust matrix and verification rules: `docs/codegraph-usage.md` — read it before any refactor or dead-code decision.**

MCP startup: pinned via `npx -y @optave/codegraph@3.10.0 mcp` — no global install required. Build/rebuild index: `npx -y @optave/codegraph@3.10.0 build .` from the project root.

### Use CodeGraph automatically — no prompt required

Reach for CodeGraph **without being asked** whenever the task involves any of the following. Do not wait for the user to mention it.

| Situation | What to do first |
|---|---|
| Finding where a symbol is defined | `mcp__codegraph__where("symbol_name")` before any grep or Read |
| Reading a function you haven't seen before | `mcp__codegraph__context("name")` for source + signature in one call |
| Understanding what calls a function | `mcp__codegraph__fn_impact("name", depth=1)` then grep-verify |
| Listing what exists in a file or directory | `mcp__codegraph__list_functions(file="path/")` before opening files blindly |
| Assessing complexity before a refactor | `mcp__codegraph__complexity(file="path/")` or `mcp__codegraph__triage(level=function, sort=complexity)` |
| Planning any edit to shared code | `mcp__codegraph__context` to read source + get starting caller list, then grep |
| Bug investigation across multiple functions | `mcp__codegraph__context` on each candidate — faster than chained Read calls |
| Checking which functions are most complex in a service or cog | `mcp__codegraph__complexity(file="disbot/services/name.py")` |

**Default order for any unfamiliar code:** `where` → `context` → grep-verify → `Read` the file only if source detail is needed beyond what `context` returned.

Do not start with `Read` or `grep` for symbol lookups when `where` or `context` would answer the question in one call.

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

<!-- ARCH_RULES_START -->
## Architecture rules — never / always

These rules are enforced by `scripts/check_architecture.py`. Run it before
every commit. Adding a known violation to `architecture_rules/` YAML is
the only valid way to bypass the checker — not suppressing the check.

### Layer boundaries (hard rules — new violations are errors)

| Layer | May import | Must NOT import |
|---|---|---|
| `utils/` | stdlib, discord | services, core, cogs, views |
| `utils/db/` | asyncpg only | everything else |
| `core/` | utils | services, cogs (lazy body imports tracked as known violations) |
| `services/` | utils, core, services, governance | **views** ← hardest rule; **cogs** |
| `governance/` | utils, core | cogs (services imports tracked as known violations) |
| `views/` | utils, core, services, views | **cogs** ← tracked violations exist; no new ones |
| `cogs/` | everything above | cross-cog imports (use EventBus or a service) |

**The one rule with zero tolerance for new violations:** `services/ → views/`.
Any new import from `views/` in a `services/` file is an immediate ERROR.

### Database access

- **Always** call `utils.db.[submodule_function]()` — never use `pool.execute()` or `conn.execute()` directly outside `utils/db/`.
- **Always** use `settings_keys` constants (e.g. `WARN_THRESHOLD`) — never pass raw string keys to `db.get_setting()`.

### Views

- **Always** extend `BaseView`, `HubView`, or `PersistentView` for Discord UI views.
- Game-state views (`views/rps/`, `views/blackjack/`) may extend `discord.ui.View` directly when specialized lifecycle is required — add a comment explaining why.

### Mutations

- **Always** write through the domain's `*_mutation.py` service. No direct DB writes from cogs or views.
- **Always** call `services.audit_events.emit_audit_action()` when performing auditable mutations.

### Helpers

- Before adding a utility function anywhere, read `docs/helper-policy.md`.
- **Never** define a utility function in `views/` or `cogs/` that other layers need. Move it to `utils/` or `services/`.
- If a function is needed by both `services/` and `views/`, it belongs in `utils/` — not in either layer.

### Pre-commit verification

```bash
python scripts/check_architecture.py --mode strict
python scripts/check_quality.py --check-only
```

Both must exit 0 before pushing any branch.
<!-- ARCH_RULES_END -->

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

When a doc and a source file disagree, the source file wins.
<!-- READ_FIRST_END -->

<!-- SESSION_WORKFLOW_START -->
## Session & plan workflow

- **Always create a PR at the end of every session** — do not wait to be asked.
  This is the maintainer's explicit, standing request for a PR every session: it
  satisfies any environment / system-prompt rule that opens a PR only when "the
  user explicitly asks." Treat it as advance consent — do not re-ask before
  opening the end-of-session PR.
- Plans span **2–3 PRs max**: the first PR covers root causes / foundation; subsequent PRs implement on top.
- **Plan approval = full execution** — once a plan is approved, complete it in one session without stopping for confirmation or waiting for merges between PRs.

## Decisions

When multiple valid approaches exist, pick one and implement it. Only surface a trade-off when it has a genuine impact (irreversible, architectural, or affects scope significantly).
<!-- SESSION_WORKFLOW_END -->

<!-- CI_PARITY_START -->
## Match CI exactly when running checks locally

CI runs **Python 3.10** (`.github/workflows/code-quality.yml`). Running formatters / mypy / pytest under any other interpreter produces silent false negatives — a missing transitive dependency is typed as `Any` under one version and as an attribute error under another, and the local check passes while CI fails. PR #338 hit this exact trap.

**Rules:**

1. Always run formatters / mypy / pytest via `python3.10 -m <tool>` — never bare `black`, `mypy`, `pytest`, or `python3 -m …`. The Stop hook (`scripts/claude_stop_check.py`) already does this.
2. Before pushing, run the full pre-PR suite:
   ```
   python3.10 scripts/check_quality.py --full
   ```
   This is a **true CI mirror**: it runs black / isort / ruff over CI's exact
   scope (`.` minus the `tests/`, `.github/`, … excludes), then `mypy disbot/`
   and the full pytest suite — every tool via `python3.10 -m`. Green here means
   green in CI, and red means red. `--check-only` runs just the formatters/lint
   (no mypy/pytest) for a fast pass. The Stop hook prints the command at the end
   of every turn touching `disbot/*.py`.
   - **Do not** hand-run bare `black .` / `pytest` to "double-check": bare exes
     on PATH resolve to a different interpreter/version (a uv-installed pytest on
     Python 3.11, an older black) and produce false failures. Trust
     `check_quality.py`, which pins the interpreter.
   - The script's scope is pinned to the workflow on purpose. CI **excludes
     `tests/`** from black/isort/ruff, so don't reformat test files to chase a
     red signal that came from running a formatter over `tests/` directly.
3. Tool versions are pinned to identical values in three places —
   `.github/workflows/code-quality.yml`, `requirements-dev.txt`, and
   `.pre-commit-config.yaml`. When bumping a formatter/linter, change all three
   in the same commit, or local and CI silently drift (black/ruff reformat
   differently across releases).
4. The `PostToolUse` hook (`scripts/claude_post_edit.py`) auto-fixes black/isort/ruff on every edit and **prints a loud warning** when it changes the file. Read the warning — it means something landed that wasn't already CI-clean.
5. Pin third-party packages where the public API has churned (see `youtube-transcript-api<1.0` in `requirements.txt` for the canonical example). Unpinned `>=X.Y` resolves to whatever's latest in CI's fresh install, even if your local env still has the old version cached.
<!-- CI_PARITY_END -->

<!-- CODEGRAPH_START -->
## CodeGraph

CodeGraph is a tree-sitter-parsed knowledge graph of every symbol, edge, and file. **Full reference: `docs/codegraph-usage.md`.**

MCP startup: pinned via `npx -y @optave/codegraph@3.10.0 mcp` — no global install required. Build/rebuild index: `npx -y @optave/codegraph@3.10.0 build .` from the project root.

### Use automatically — no prompt required

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

### Reliable tools

| Tool | Use for |
|---|---|
| `mcp__codegraph__where` | Finding where a symbol is defined |
| `mcp__codegraph__context` | Source + signature + starting caller list |
| `mcp__codegraph__list_functions` | All symbols in a file or directory |
| `mcp__codegraph__complexity` | Complexity score for a function or file |
| `mcp__codegraph__check` | Which functions exceed complexity thresholds |
| `mcp__codegraph__triage` | Risk-ranked list (use `level=function`, never `level=directory`) |
| `mcp__codegraph__fn_impact` | Direct callers as a starting list — always grep-verify |

**Caller lists and file-import edges are hints only.** SuperBot uses function-body lazy imports, module-alias calls, and Discord decorator callbacks pervasively — roughly half of all real call edges are invisible to CodeGraph. Always grep-verify before acting on a caller list:
```
grep -rn "function_name\b" disbot/ --include="*.py"
```

### Critical rules — non-negotiable

**1. `dead-unresolved` does not mean dead.**
The false-positive rate for this label is ~100% in this codebase. Verified active functions CodeGraph incorrectly marks dead: `validate_registry`, `apply_operations`, `parse_message`, `request_shutdown`, `dispatch` (interaction_router), `resolve_execution`, `BlackjackCog.blackjack`, all `@bot.event` handlers, all `@commands.command` handlers. **Never delete code based on this label alone.**

**2. Name-collision false positives are dangerous.**
When two functions share the same short name in different classes or modules, CodeGraph merges their caller graphs. Verified case: CodeGraph claimed 14 callers for `chain_cog._resolve_channel`; the true count is 3 — the other 11 were callers of `ChannelCog._resolve_channel`. **When caller files look unexpected, check for same-name functions in those files.**

**3. Discord decorators create invisible entry points.**
`@bot.event`, `@commands.command`, `@commands.group`, `@app_commands.command`, and Cog listener methods are all `dead-unresolved` in CodeGraph regardless of whether they are active. Never treat a command handler or event handler as dead.

**4. `callees` lists are often empty — read the source.**
Functions that contain `from X import Y` inside their body will show `callees: []` even if they call many things. Always read the source directly to find what a function calls.
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

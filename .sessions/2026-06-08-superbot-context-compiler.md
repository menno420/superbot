# Session log — 2026-06-08 — SuperBot Context Compiler

## What shipped

Built the **SuperBot Context Compiler** end-to-end in one session. All 8133 CI tests pass.

### Files created
- **`docs/agent/index.yml`** — 7-subsystem context manifest. Each entry: folio, binding_docs, reference_docs, source_roots, related_subsystems, do_not_create warnings, active gates, verification commands.
- **`tools/agent_context/build_pack.py`** — reads index.yml, generates `docs/agent/generated/*.context.md`. `--subsystem KEY` and `--dry-run` flags.
- **`tools/agent_context/validate_pack.py`** — validates structure, path existence, and NOT-SOURCE-OF-TRUTH marker. `--fix` reruns the builder first.
- **`docs/agent/generated/`** — 7 generated context packs (ai, health-diagnostics, server-management, btd6, games, media-youtube, settings-bindings-provisioning). Each has `> **Status:** \`reference\`` badge, the NOT-SOURCE-OF-TRUTH marker, and all index fields rendered as structured markdown.
- **`docs/agent/README.md`** — explains the system, links all generated packs (making them reachable from the README reachability root), describes what the manifest encodes and what it does not replace.
- **`tests/unit/docs/test_agent_context_index.py`** — 13 pinning tests. Catches stale paths, missing fields, missing generated packs, and missing NOT-SOURCE-OF-TRUTH markers in CI.
- **`.claude/rules/mutation-and-db.md`** — path-scoped guidance for disbot/services/** + disbot/utils/db/** edits.
- **`.claude/rules/discord-views.md`** — path-scoped guidance for disbot/views/** edits.
- **`.claude/rules/context-compiler.md`** — path-scoped guidance for docs/agent/** + tools/agent_context/** edits.

### Files updated
- **`docs/AGENT_ORIENTATION.md`** — new task route "Editing the agent context system", context-pack shortcut in the read-layers note.
- **`docs/repo-navigation-map.md`** — added `tools/`, `docs/agent/`, `.claude/rules/` to the top-level tree.
- **`pyproject.toml`** — added `tools/**/*.py` per-file-ignores (T201, S603, S607) matching the `scripts/*.py` precedent.
- **`docs/current-state.md`** — session entry added.

## Why this architecture

The plan (sent as session prompt from ChatGPT planning agent) evaluated Caveman, Repomix, Gitingest, Claude-native rules/hooks, and a repo-native Context Compiler. The recommendation was clear: build the compiler first, use Claude rules for path-scoped guidance, use Repomix only as an export layer, and treat Caveman as optional compression for generated mirrors only. This session executed exactly that.

The design keeps canonical docs authoritative (never compressed, never rewritten) and generated packs as transparent build artifacts. The `check_docs.py` reachability gate now enforces that generated packs carry a status badge and are linked from a root.

## CI/docs issues fixed during the session
- Generated packs initially missing `> **Status:** \`reference\`` badge → added to `build_pack.py` header.
- Generated packs initially "orphan" (not reachable from any root) → linked from `docs/agent/README.md`, which is a reachability root (README.md files are always roots).
- `tools/**/*.py` initially flagged by ruff T201 (print statements) → added per-file-ignores to `pyproject.toml` matching `scripts/*.py` precedent.

## Context delta

**What I needed but wasn't pointed to:** The `check_docs.py` status-badge and reachability rules — I had to discover them by running the check-quality script. The AGENT_ORIENTATION reading route doesn't mention that all `docs/` files need badges or that READMEs are reachability roots. Worth adding a note in the orientation for anyone building new doc infrastructure.

**What I was pointed to but didn't need:** CodeGraph — the entire task was docs/tooling with no disbot/ source edits, so CodeGraph tools were irrelevant.

**Discovered by hand:** The `per-file-ignores` in `pyproject.toml` need to explicitly cover new tool directories; `scripts/*.py` was the only existing exemption and it doesn't extend to `tools/`.

## PR

End-of-session PR opened — see branch `claude/eloquent-rubin-xgx1t`.

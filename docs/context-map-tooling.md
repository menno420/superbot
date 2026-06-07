# Context-map tooling — `scripts/context_map.py`

> **Status:** `reference` — how to use the context-map tool. Source wins.

## What it is

`scripts/context_map.py` answers one question fast: **"what is connected to this
file, and what should I read/check before editing it?"** Given a path under
`disbot/`, it prints the file's role and layer, its direct imports (module-level
**and** lazy function-body imports, labelled), what imports it, the transitive
blast radius, ownership/authority, related docs and tests, risk flags, and a
recommended read/verify set.

It exists because **CodeGraph cannot resolve this repo's file/module edges** —
`file_deps`, `module_map`, and `impact_analysis` all return zero here (see
`docs/codegraph-usage.md`). CodeGraph stays the tool for *symbol* lookup
(`where`, `list_functions`, `context`, `complexity`); this tool covers
*file/module* dependency context that CodeGraph misses.

## Usage

```bash
python scripts/context_map.py disbot/services/moderation_service.py
python scripts/context_map.py disbot/cogs/moderation_cog.py --max-importers 30
```

## How it resolves edges (and what to trust)

| Section | Source | Trust |
|---|---|---|
| File role / authority | `architecture_rules/mutation_owners.yaml` + layer from path | Authoritative |
| Direct imports (module-level / lazy) | AST (`check_architecture._ImportVisitor`) | Authoritative for *scope* (module-level vs lazy). Names are at `from`-module granularity, so `from services import x` shows as `services`. |
| Imported by / Blast radius | **Grimp** when installed; **AST scan** otherwise | Grimp is authoritative (resolves `from services import moderation_service` to the submodule + lazy importers). The AST fallback is a **lower bound** (like CodeGraph) and is clearly labelled in the output. |
| Related docs / Relevant tests / Risk | `docs/context-map-overrides.yml` + `layers.yaml` + path mirror | Curated + heuristic — extend the override file as the repo grows. |

The tool **does not map call edges** (function→function). That stays a
grep + CodeGraph (`fn_impact`, then grep-verify) job — see `docs/codegraph-usage.md`.
Decorator-registered Discord handlers (`@commands.command`, `@bot.event`, …) are
framework dispatch, invisible to any static import/call graph.

## Dependency

The importer/blast-radius engine uses **Grimp** (`requirements-dev.txt`, pinned).
Grimp is a developer/agent dependency — it is **not** a bot-runtime dependency and
is **not** installed in CI. The tool degrades to the AST fallback when Grimp is
absent, so `tests/unit/scripts/test_context_map.py` stays green in CI (the
Grimp-specific test is skipped via `pytest.importorskip`).

```bash
pip install -r requirements-dev.txt   # installs grimp for the authoritative path
```

## The override file

`docs/context-map-overrides.yml` is the one curated source for the docs/tests/risk
routing that imports alone cannot infer. It maps a file's directory prefix to its
**area folio** and **contract docs** (longest prefix wins; `layer_docs` is the
fallback). Keep entries thin and *link* to authoritative docs — do not restate
their contents (one fact, one home). Add an entry when a new subsystem lands.

## Roadmap (small, phased)

1. **Now** — single-file map (this script), Grimp + AST fallback, override file, tests.
2. `--changed` mode: run over a PR's changed files for a combined context digest.
3. Discord-decorator framework-edge scanner (synthetic "invoked by dispatch" edges).
4. Cache the Grimp graph under `.build/` for repeated queries.
5. Optional CI warn mode (e.g. "you touched a mutation owner — confirm audit emission").

# Agent context system

> **Status:** `reference` — how to use and maintain the context compiler.
> See also: `docs/AGENT_ORIENTATION.md` § "Editing the agent context system".

This directory holds the **SuperBot Context Compiler** — a repo-native tool that
generates deterministic, task-specific context packs for Claude sessions.  It is
not a replacement for the canonical docs; it is an orientation layer that points
agents at the right canonical docs faster.

---

## The problem it solves

SuperBot has over 100 markdown files.  A new session that reads from the top
risks reading stale plans before reaching the binding contracts.  Worse, each
session re-discovers the same "which file owns X" questions by hand.

The context compiler makes that routing executable:

```
docs/agent/index.yml        ← curated manifest (edit here)
tools/agent_context/
  build_pack.py             ← generates packs from the manifest
  validate_pack.py          ← CI-style check for stale paths
docs/agent/generated/       ← generated packs (committed; built from index)
```

---

## How to use a context pack

Before editing a subsystem, read its generated pack:

```
docs/agent/generated/ai.context.md
docs/agent/generated/health-diagnostics.context.md
docs/agent/generated/server-management.context.md
docs/agent/generated/btd6.context.md
docs/agent/generated/games.context.md
docs/agent/generated/media-youtube.context.md
docs/agent/generated/settings-bindings-provisioning.context.md
```

| Pack | Subsystem |
|---|---|
| [ai.context.md](generated/ai.context.md) | AI / Setup Advisor |
| [health-diagnostics.context.md](generated/health-diagnostics.context.md) | Health / Diagnostics |
| [server-management.context.md](generated/server-management.context.md) | Server Management |
| [btd6.context.md](generated/btd6.context.md) | BTD6 Data / Tools |
| [games.context.md](generated/games.context.md) | Games |
| [media-youtube.context.md](generated/media-youtube.context.md) | Media / YouTube |
| [settings-bindings-provisioning.context.md](generated/settings-bindings-provisioning.context.md) | Settings / Bindings / Provisioning |

Each pack gives you in one page:
- The **folio** (canonical area entry point with debug router + next candidates)
- **Binding docs** to read before editing
- **Reference docs** to consult on demand
- **Source roots** — where the code lives
- **Do-not-create warnings** — existing systems you must reuse, not duplicate
- **Active gates** — expansion conditions that apply right now
- **Verification commands** — what to run before pushing

**The pack is orientation only.  When the pack and a canonical doc disagree,
the canonical doc wins.  When the pack and source code disagree, source code wins.**

---

## How to update the manifest

Edit `docs/agent/index.yml`, then re-run the builder:

```bash
python3.10 tools/agent_context/build_pack.py
```

Commit both the updated `index.yml` and the regenerated packs.  The test
`tests/unit/docs/test_agent_context_index.py` will catch stale paths in CI.

To validate without regenerating:

```bash
python3.10 tools/agent_context/validate_pack.py
```

To regenerate and validate in one step:

```bash
python3.10 tools/agent_context/validate_pack.py --fix
```

---

## What belongs in the manifest

The index should encode what an agent needs **before** touching a subsystem:

| Field | What to put |
|---|---|
| `folio` | Path to the subsystem's `docs/subsystems/*.md` file |
| `binding_docs` | Docs that are authoritative contracts (architecture, ownership, ADRs) |
| `reference_docs` | Plans, trackers, roadmaps — useful context, not binding |
| `source_roots` | Key entry files and directories for the subsystem |
| `related_subsystems` | Subsystems with shared ownership or EventBus coupling |
| `do_not_create` | Systems that already exist and must not be duplicated |
| `gates` | Expansion conditions currently in force |
| `verification` | The commands to run before pushing any change |

**Do not put implementation detail in the index.** If you want to document a
specific algorithm, a debug router entry, or a known gotcha, put it in the folio
or a binding doc — then the index entry will point to it.

---

## What this system deliberately does NOT replace

- **`docs/AGENT_ORIENTATION.md`** — the canonical "reading order by task" router.
  Generated packs supplement it, not replace it.
- **`docs/architecture.md`, `docs/ownership.md`, `docs/runtime_contracts.md`** —
  binding contracts.  The index references them; it does not restate them.
- **`scripts/context_map.py`** — file-level impact map (importers, blast radius,
  related docs/tests, risk flags).  Run it before editing any `disbot/*.py` file.
  The context compiler is subsystem-level orientation; `context_map.py` is
  file-level orientation.  They are complementary.
- **`scripts/wiring_map.py`** — EventBus emitter→subscriber join.  Use it when
  any EventBus event is touched.

---

## Caveman and Repomix

Neither is part of the primary workflow.

- **Caveman** may be used to compress generated pack *mirrors* for terse replies
  in long sessions.  It must never rewrite canonical docs in place.
- **Repomix** may be used to package a selected file list for one-off Claude
  review bundles.  Do not use whole-repo dumps as the default.

Neither replaces the context manifest as the authoritative routing layer.

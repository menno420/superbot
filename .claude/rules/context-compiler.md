---
description: "Context compiler rules for docs/agent/ and tools/agent_context/ files"
globs:
  - "docs/agent/**"
  - "tools/agent_context/**"
---

# Context compiler — rules for editing the agent context system

## The contract
- `docs/agent/index.yml` is the single source of truth for the context manifest.
- `docs/agent/generated/*.context.md` are build artifacts — never edit them directly.
  Always edit the index, then re-run the builder.
- Generated packs must always carry the `NOT SOURCE OF TRUTH` marker.

## After editing index.yml
```bash
python3.10 tools/agent_context/build_pack.py   # regenerate
python3.10 tools/agent_context/validate_pack.py  # verify
python3.10 -m pytest tests/unit/docs/test_agent_context_index.py -v
```

Commit both the updated index.yml and the regenerated packs in the same commit.

## What the index encodes
- `folio` — path to `docs/subsystems/*.md` (canonical area entry point)
- `binding_docs` — authoritative contracts (architecture, ownership, ADRs)
- `source_roots` — key files/directories; every entry must exist on disk
- `do_not_create` — existing systems that must not be duplicated
- `gates` — currently active expansion conditions
- `verification` — commands to run before pushing

## What it does NOT replace
- `docs/AGENT_ORIENTATION.md` — the primary reading-order router
- `scripts/context_map.py` — file-level impact map (run before any disbot/ edit)
- Binding docs (architecture.md, ownership.md, runtime_contracts.md)

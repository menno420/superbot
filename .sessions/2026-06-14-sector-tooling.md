# Session: sector tooling — make the dispatch structure self-maintaining

> **Status:** `in-progress`

**Branch:** `claude/ecstatic-euler-bslyvd` · **PR:** (opening) · **Date:** 2026-06-14 · **Type:** S3 mechanism (tooling + tests)

## Why (HOLD — born-red card, Q-0133)
Close the loose ends from the dispatch-test work (#877/#880). The dispatch convention (sector homing,
startability tags, per-sector executor) is currently **prose-asserted, not machine-checked** — the
honest weak point I flagged in #880. Build the tooling that makes it self-maintaining (owner: "let's
not leave any loose ends").

### Planned (S3 mechanism — `scripts/` + tests; full CI applies)
1. **`scripts/check_sector_map.py`** — the **validator**: (a) every `docs/subsystems/*.md` folio is
   homed to **exactly one** sector (via a new machine-readable folio→sector block in
   `repo-sector-map.md`); (b) all 5 sectors S1–S5 appear in both maps; (c) every roadmap sector
   `Dispatch` line names an executor; (d) every sector `Now` carries ≥1 startability tag (▶/⛔/👤) or a
   done marker. Read-only, stdlib, exit-nonzero on violation. Q-0105 disposable header.
2. **`scripts/dispatch_menu.py`** — the **resolver** (my #880 Q-0089 idea, folding in the
   sector-health telemetry): parse the roadmap sector index → per sector print the first **▶ startable**
   item + executor + live-queue link, and flag **starving** sectors (no ▶ in Now). The machine version
   of the dispatch test — what a worker dispatched to SX would pick up.
3. Tests for both (`tests/unit/scripts/`); add a machine-readable folio map to `repo-sector-map.md`;
   note `check_sector_map` in the reconciliation routine checklist (docs — **not** CI-wired; that's
   ask-first per the autonomy boundary).

Verify each tool's output against known ground truth (5 sectors; folios S1×6 + S2×1) per Q-0105.

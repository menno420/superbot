# Session: sector tooling — make the dispatch structure self-maintaining

> **Status:** `complete`

**Branch:** `claude/ecstatic-euler-bslyvd` · **PR:** #882 · **Date:** 2026-06-14 · **Type:** S3 mechanism (tooling + tests)

## What this session did
Closed the loose ends from the dispatch work (#877 sector restructure → #880 dispatch contract). The
convention (folio homing, startability tags, per-sector executor) was **prose-asserted, not
machine-checked** — the honest weak point I flagged in #880. The owner said "let's not leave any loose
ends," so this builds the tooling that makes the partition self-maintaining.

### Shipped (S3 mechanism — `scripts/` + tests, stdlib, read-only)
1. **`scripts/check_sector_map.py`** — the **validator**: every `docs/subsystems/*.md` folio homed to
   exactly one sector (no orphan/phantom/double-home, via a new machine-readable `sector-folio-map`
   block in `repo-sector-map.md`) · all 5 sectors present in both maps · every roadmap sector's
   `Dispatch` names an executor · every `Now` carries a startability tag. Exit-nonzero on drift.
2. **`scripts/dispatch_menu.py`** — the **resolver** (the #880 Q-0089 idea, sector-health folded in):
   parses the roadmap sector index → per sector prints the first **▶ startable** item + executor, and
   flags a **starving/blocked** sector. Output exactly reproduces the by-hand dispatch test (S1→Layer
   B · S2→blocked→Next: BTD6 eval cases · S5→route to Hermes/maintainer).
3. **19 tests** (`tests/unit/scripts/`); machine-readable folio map + a "run the guards" bullet in
   `repo-sector-map.md`; roadmap S3 row updated (check_sector_map was a `Next` idea — now shipped).

**Dogfooding caught a real bug:** building `dispatch_menu` surfaced that #880 used a ▶ glyph in S2's
`Now` *prose* ("falls through to the ▶ startable item"), not as an item tag — a false positive. Fixed
the prose so tags only mark items (cleaner convention + reliable parse).

**Verification (Q-0105):** both tools confirmed against ground truth (7 folios homed; menu == the
manual test). `check_quality --full` green (**9664 passed**); arch 0 errors. **Not CI-wired** (that is
ask-first per the autonomy boundary) — homed in `repo-sector-map.md` § "How to keep this alive".

## 💡 Session idea (Q-0089)
**`dispatch_menu.py --json` + wire it into the Hermes `superbot-dispatch` skill.** The menu already
*computes* "what would a worker dispatched to SX pick up" — emit it as JSON
(`{sector, executor, startable_item, state}`) so the Hermes dispatch skill, asked *"dispatch S2,"* runs
`dispatch_menu.py --json S2` and resolves the concrete work order **automatically** instead of a human
re-reading the roadmap. This is the **read-side of Q-0137 Thread 1** — the bridge from the Q-0143
contract to the `/fire` wiring (which stays owner-undecided). Distinct from the three sector tools
(it's the integration/JSON layer). Dedup-grepped `docs/ideas/` + roadmap: no overlap.

## ⟲ Previous-session review (Q-0102)
Reviewing **#880** (the dispatch-contract PR this tooling backs). **Did well:** derived a clean,
genuinely-useful convention (executor dimension + startability tags) straight from the test findings,
fast. **Missed:** it shipped a new doc **convention** (tags/executor markers) **without its validator**
— so the convention was prose-only for one session, and in that gap it *already drifted* (the
▶-in-prose bug this session caught). **System improvement (earned):** *when a PR introduces a doc
convention — tags, markers, a machine-read block — ship its checker in the same PR, or it drifts before
the next session reads it.* This is the specific, sharper form of #880's own "dogfood what you build"
lesson: a convention's dogfood **is** its checker. Worth promoting toward a standing rule once it
recurs.

## Doc audit (Q-0104)
`check_docs --strict` ✓. `check_quality --full` ✓ (9664 passed, 37 skipped; the new scripts are
black/isort/ruff clean — `scripts/*.py` ignores T201 so `print()` is fine). `check_architecture
--mode strict` ✓ (0 errors; the xp-view warnings are pre-existing, not mine). `check_sector_map.py` +
`dispatch_menu.py` self-verified against ground truth. Ledger lag (#872–#881 not yet in
Recently-shipped) is the expected between-pass lag — reconciliation routine's job at #900 (Q-0124).

**Grooming (Q-0015):** moved `check_sector_map.py` from an S3 `Next` *idea* to *shipped*, folded the
`sector_health.py` idea into `dispatch_menu`'s starving-sector flag, and queued the one genuinely-new
next step (`--json` + Hermes wiring) as the Q-0089 idea. No orphaned sector ideas remain.

## Context delta
- **Decided alone (within the tooling-is-free envelope):** kept each tool **self-contained**
  (duplicated ~3 small parsers) rather than cross-importing — `isort src_paths=["disbot"]` makes a
  sibling-script import brittle, and standalone single-file scripts are the repo convention. Flagged
  the duplication in `dispatch_menu`'s docstring for a future refactor if a third consumer appears.
- **Discovered by hand:** the **black ⇄ ruff COM812 ping-pong** — `ruff --fix` adds trailing commas
  that black then reformats; the fix is to **run black last**. Worth a journal note.
- **Weak point of what shipped:** the tools are **disposable + not CI-wired**, so they only catch drift
  when someone runs them. The natural graduation (propose-first) is wiring `check_sector_map` into
  `code-quality.yml` once it's proven over a few sessions — recorded as the open follow-on in Q-0143.

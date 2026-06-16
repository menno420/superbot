#!/usr/bin/env python3
"""SuperBot architecture atlas — a thin, repo-wide *composer* over the existing maps.

The owner-uploaded architecture review asked for one provenance-stamped "front page"
that answers, across the whole repo, the questions the per-file ``context_map.py``
answers one file at a time: *where does each file belong · what review unit is it ·
what role/subsystem does it back · who imports it · does it have tests*. This is that
repo-wide index — generated on demand, **body not committed** (owner decision Q-0151a:
companion to ``AGENT_ORIENTATION.md``, CI ``--check`` + on-demand generate).

DO-NOT-DUPLICATE (the review's own warning, and this repo's helper policy): this is a
**composer**, never a re-implementation. Every fact comes from a sibling tool imported
as a library — if a fact isn't produced yet, add it *there*, not here:
    - ``context_map``        — layer, reverse-import graph (importers), ownership facts
    - ``_review_units``      — the repo-review-map partition (review unit)
    - ``extension_crosswalk``— role / backing-subsystem / registered (PR #958)

Modes
-----
    python3.10 scripts/atlas.py            # compact summary (rollups + provenance)
    python3.10 scripts/atlas.py --full     # the full per-file index to stdout
    python3.10 scripts/atlas.py --check    # composite coherence guard (exit 1 on drift)

What ``--check`` adds vs. delegates (kept honest — no false-positive gates):
    - DELEGATES classification + crosswalk-doc freshness to ``extension_crosswalk.check()``
      so ``atlas.py --check`` is one entrypoint that also covers the crosswalk.
    - ADDS (hard): every loaded extension resolves to a source file on disk; the index
      builds for every file without error.
    - ADDS (soft, reported not failed): source files that classify into no layer and are
      not a known top-level module ("orphans") — surfaced so a human notices, never a
      hard fail (a new top-level package is usually intentional).

RELIABILITY / PROVENANCE (Q-0105): added 2026-06-16. Read-only, stdlib + the sibling
scripts, disposable. If it proves more nuisance than help across a few sessions, delete
this script + ``tests/unit/scripts/test_atlas.py`` + ``docs/architecture/repo-atlas.md``
together — nothing in the bot runtime depends on it.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _review_units  # noqa: E402
import context_map as cmap  # noqa: E402
import extension_crosswalk as xwalk  # noqa: E402

REPO_ROOT: Path = cmap.REPO_ROOT
DISBOT_ROOT: Path = cmap.DISBOT_ROOT
TESTS_ROOT: Path = cmap.TESTS_ROOT

# Bump when the rendered layout changes.
GENERATOR_VERSION = "v1"


@dataclass(frozen=True)
class FileRecord:
    rel: str
    module: str
    layer: str | None
    review_unit: str
    role: str
    backs: str | None
    registered: bool
    importers: int
    has_tests: bool


# ---------------------------------------------------------------------------
# Composition helpers
# ---------------------------------------------------------------------------


def _cog_extension_short(rel: str) -> str | None:
    """Map a ``disbot/cogs/...`` path to its extension short name (else None).

    ``cogs/mining_cog.py`` and ``cogs/mining/exploration.py`` both -> ``mining``.
    """
    parts = Path(rel).parts
    if len(parts) < 3 or parts[1] != "cogs":
        return None
    name = parts[2]
    if name.endswith(".py"):
        name = name[:-3]
    return name.removesuffix("_cog")


def _test_stems() -> set[str]:
    """Source stems that have a mirror ``test_<stem>.py`` anywhere under tests/ (one walk)."""
    return {p.stem[len("test_") :] for p in TESTS_ROOT.rglob("test_*.py")}


def build_index() -> list[FileRecord]:
    """The repo-wide roster, composed from the sibling tools (one reverse-graph build)."""
    reverse = cmap.build_reverse()
    test_stems = _test_stems()
    role_by_ext = {row.extension: row for row in xwalk.build_rows()[0]}

    records: list[FileRecord] = []
    for py in sorted(DISBOT_ROOT.rglob("*.py")):
        if py.name == "__init__.py":
            continue  # package marker — its module is the package itself
        mod = cmap.module_name(py)
        if mod is None:
            continue
        rel = str(py.resolve().relative_to(REPO_ROOT))
        layer = cmap._arch._file_layer(py)
        review_unit = _review_units.classify_path(rel).label()
        short = _cog_extension_short(rel)
        row = role_by_ext.get(short) if short else None
        records.append(
            FileRecord(
                rel=rel,
                module=mod,
                layer=layer,
                review_unit=review_unit,
                role=row.role if row else "",
                backs=row.backs if row else None,
                registered=bool(row and row.registered),
                importers=len(reverse.importers(mod)),
                has_tests=py.stem in test_stems,
            ),
        )
    return records


# ---------------------------------------------------------------------------
# Coherence guard
# ---------------------------------------------------------------------------


def _missing_extension_files() -> list[str]:
    errors: list[str] = []
    for short in xwalk.initial_extensions():
        cog_file = DISBOT_ROOT / "cogs" / f"{short}_cog.py"
        cog_pkg = DISBOT_ROOT / "cogs" / f"{short}_cog" / "__init__.py"
        if not cog_file.exists() and not cog_pkg.exists():
            errors.append(f"extension 'cogs.{short}_cog' has no source file on disk")
    return errors


def orphans(records: list[FileRecord]) -> list[str]:
    """Files that classify into no layer and are not a known top-level module (soft)."""
    out: list[str] = []
    for r in records:
        if r.layer is None and r.module.split(".")[0] not in cmap.TOP_LEVEL_MODULES:
            out.append(r.rel)
    return out


def coherence_errors(records: list[FileRecord]) -> list[str]:
    """Hard failures only. Classification/freshness is delegated to the crosswalk."""
    return list(xwalk.check()) + _missing_extension_files()


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _provenance(records: list[FileRecord]) -> list[str]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return [
        "# SuperBot architecture atlas (generated)",
        "",
        "> **GENERATED — NOT SOURCE OF TRUTH.** Composed from `context_map` · `_review_units` ·",
        "> `extension_crosswalk`. Regenerate with `python3.10 scripts/atlas.py --full`. Body is",
        "> intentionally not committed (Q-0151a); the curated companion is "
        "`docs/architecture/repo-atlas.md`.",
        "",
        f"_commit:_ `{_git_sha()}`  ·  _generated:_ {now}  ·  "
        f"_generator:_ `atlas {GENERATOR_VERSION}`  ·  **{len(records)}** source files.",
        "",
    ]


def _counts(records: list[FileRecord], attr: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in records:
        key = getattr(r, attr) or "(none)"
        out[key] = out.get(key, 0) + 1
    return out


def _rollup_table(title: str, counts: dict[str, int]) -> list[str]:
    out = [f"## By {title}", "", f"| {title} | files |", "|---|---:|"]
    for key, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(f"| `{key}` | {n} |")
    out.append("")
    return out


def render_summary(records: list[FileRecord]) -> str:
    out = _provenance(records)
    out += _rollup_table("layer", _counts(records, "layer"))
    role_counts = {k: v for k, v in _counts(records, "role").items() if k != "(none)"}
    out += _rollup_table("role", role_counts)
    out += _rollup_table("review unit", _counts(records, "review_unit"))
    tested = sum(1 for r in records if r.has_tests)
    out.append(
        f"_Mirror-test coverage:_ **{tested}/{len(records)}** files have a `test_<stem>.py`.",
    )
    orphan_list = orphans(records)
    out.append(
        f"_Orphans (no layer, not a known top-level module):_ **{len(orphan_list)}**.",
    )
    if orphan_list:
        out.append("")
        out += [f"- {o}" for o in orphan_list]
    out.append("")
    out.append(
        "_Run `--full` for the per-file index, `--check` for the coherence guard._",
    )
    out.append("")
    return "\n".join(out)


def render_full(records: list[FileRecord]) -> str:
    out = _provenance(records)
    out += _rollup_table("layer", _counts(records, "layer"))
    out.append("## Per-file index")
    out.append("")
    out.append("| File | Layer | Review unit | Role | Backs | Reg | Imp | Tests |")
    out.append("|---|---|---|---|---|:--:|---:|:--:|")
    for r in records:
        backs = f"`{r.backs}`" if r.backs else ""
        role = f"`{r.role}`" if r.role else ""
        reg = "✓" if r.registered else ""
        tests = "✓" if r.has_tests else ""
        out.append(
            f"| `{r.rel}` | `{r.layer or '—'}` | {r.review_unit} | {role} | {backs} | "
            f"{reg} | {r.importers} | {tests} |",
        )
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SuperBot architecture atlas (composer).",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--full",
        action="store_true",
        help="full per-file index to stdout.",
    )
    group.add_argument(
        "--check",
        action="store_true",
        help="coherence guard: exit 1 on drift.",
    )
    args = parser.parse_args(argv)

    records = build_index()

    if args.check:
        errors = coherence_errors(records)
        soft = orphans(records)
        if errors:
            print("atlas: FAIL")
            for e in errors:
                print(f"  - {e}")
            return 1
        print(f"atlas: coherent ✓ ({len(records)} files)")
        if soft:
            print(f"  note: {len(soft)} orphan file(s) with no layer (informational):")
            for o in soft:
                print(f"    - {o}")
        return 0

    print(render_full(records) if args.full else render_summary(records), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())

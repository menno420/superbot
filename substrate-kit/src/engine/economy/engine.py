"""The context-economy engine (plan §5.B, Lane B4).

The retention/taxonomy layer of the self-improving loop: docs are classified
into host-declared classes (badge- and/or glob-matched), gauges watch word and
count budgets, an inbound-reference scan protects cited files, and the actuator
applies the TRIPLE FILTER (harvested AND past window AND zero inbound refs)
before any deletion — writing one tombstone line per pruned file into a
per-band shard. Retention windows are measured in **days** from file mtime:
the kit supports day windows only; "bands" are a host cadence unit layered on
top of it, never a kit unit. ``economy["maturity"]`` gates the actuator —
``"shadow"`` never applies. Pure stdlib; returns data / text, never prints.
"""

from __future__ import annotations

import os
import re
import time
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple

from engine.checks.check_orientation_budget import _ob_boot_paths
from engine.lib.atomicio import atomic_write_text
from engine.lib.config import Config

# Minimal inline copy of check_docs._badge_token's regex (private there); drop
# once the helper is promoted to a public name in engine/checks/check_docs.py.
_ECO_BADGE_RE = re.compile(r"\*\*Status:\*\*\s*`([a-z-]+)`")

_ECO_SECONDS_PER_DAY = 86400.0


class EconomyFinding(NamedTuple):
    """One economy finding: ``path`` is relative to the project root."""

    path: str
    kind: str
    message: str


DEFAULT_CLASSES: list[dict] = [
    {
        "name": "sessions",
        "globs": ["<sessions_dir>/*.md"],
        "mode": "delete_tomb",
        "window_days": 14,
        "tombstone_dir": "<sessions_dir>/pruned",
    },
    {
        "name": "plans",
        "badges": ["plan"],
        "mode": "archive",
        "window_days": 60,
    },
    {
        "name": "living",
        "badges": ["living-ledger", "reference", "binding"],
        "mode": "keep",
    },
]
"""Minimal generic class profile — a STARTING POINT, not shipped policy.

Used only when ``config.economy["classes"]`` is empty. Every adopting host is
expected to replace it with its own measured taxonomy (the kit ships the
search, not our constants). Placeholder tokens (``<sessions_dir>`` etc.) are
expanded from the host config at evaluation time.
"""


def _eco_expand(pattern: str, config: Config) -> str:
    """Expand ``<sessions_dir>`` / ``<docs_root>`` / ``<state_dir>`` tokens."""
    return (
        pattern.replace("<sessions_dir>", config.sessions_dir)
        .replace("<docs_root>", config.docs_root)
        .replace("<state_dir>", config.state_dir)
    )


def _eco_classes(config: Config) -> list[dict]:
    """Return the active class table (host classes or the generic default)."""
    return list(config.economy.get("classes") or DEFAULT_CLASSES)


def _eco_md_files(docs_root: Path) -> list[Path]:
    """Return every ``*.md`` under ``docs_root`` (sorted, empty if absent)."""
    if not docs_root.exists():
        return []
    return sorted(docs_root.rglob("*.md"))


def _eco_read_text(path: Path) -> str | None:
    """Read ``path`` as UTF-8 text; None when unreadable or not text."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _eco_badge_token(path: Path) -> str | None:
    """Return the doc's Status-badge token from its first 12 lines, or None."""
    text = _eco_read_text(path)
    if text is None:
        return None
    match = _ECO_BADGE_RE.search("\n".join(text.splitlines()[:12]))
    return match.group(1) if match else None


def _eco_wc(path: Path) -> int:
    """Return the whitespace word count of one text file (0 if unreadable)."""
    text = _eco_read_text(path)
    return len(text.split()) if text else 0


def _eco_rel(path: Path, root: Path) -> str:
    """Return ``path`` relative to ``root`` as posix (absolute-safe fallback)."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def classify_docs(root: Path, config: Config) -> dict[str, list[Path]]:
    """Bucket project docs into economy classes plus the ``_unbadged`` bucket.

    Classes come from ``config.economy["classes"]`` (``DEFAULT_CLASSES`` when
    empty); each class matches by Status-badge token (``badges``, scanned from
    a doc's first 12 lines with the check_docs regex convention) and/or by
    root-relative ``globs``. The first matching class wins. Docs under the
    docs root that match no class AND carry no badge land in ``"_unbadged"``.
    """
    docs = _eco_md_files(root / config.docs_root)
    buckets: dict[str, list[Path]] = {}
    assigned: set[Path] = set()
    for cls in _eco_classes(config):
        matched: set[Path] = set()
        for pattern in cls.get("globs", []):
            expanded = _eco_expand(str(pattern), config)
            matched.update(p for p in root.glob(expanded) if p.is_file())
        badges = set(cls.get("badges", []))
        if badges:
            matched.update(f for f in docs if _eco_badge_token(f) in badges)
        fresh = sorted(p for p in matched if p.resolve() not in assigned)
        assigned.update(p.resolve() for p in fresh)
        buckets[cls["name"]] = fresh
    buckets["_unbadged"] = [
        f for f in docs if f.resolve() not in assigned and _eco_badge_token(f) is None
    ]
    return buckets


def _eco_word_cap_value(root: Path, config: Config, gauge: dict) -> int:
    """Return a word_cap gauge's value: one file's words, or a dir's summed."""
    target = root / _eco_expand(str(gauge.get("path", "")), config)
    if target.is_dir():
        return sum(_eco_wc(f) for f in sorted(target.rglob("*.md")))
    if target.is_file():
        return _eco_wc(target)
    return 0


def _eco_count_cap_value(root: Path, config: Config, gauge: dict) -> int:
    """Return a count_cap gauge's value: file count under its glob."""
    pattern = _eco_expand(str(gauge.get("glob", "")), config)
    if not pattern:
        return 0
    return sum(1 for p in root.glob(pattern) if p.is_file())


def _eco_route_budget(root: Path, config: Config) -> tuple[int, int]:
    """Return (value, cap) for the boot-route word budget.

    Value sums word counts over the boot set resolved by the orientation
    checker's own ``_ob_boot_paths`` (ONE resolver for both consumers — the
    gauge once resolved everything under docs_root and undercounted
    root-level boot docs to 0); cap is ``orientation["budget_words"]``.
    """
    value = sum(_eco_wc(path) for path in _ob_boot_paths(root, config))
    cap = int(config.orientation.get("budget_words", 7000))
    return value, cap


def economy_gauges(root: Path, config: Config) -> list[dict]:
    """Evaluate the configured gauges (word_cap / count_cap / route_budget).

    When ``config.economy["gauges"]`` is empty, falls back to one
    ``route_budget`` gauge derived from ``config.orientation``. Unknown kinds
    are skipped. Each result is ``{"name", "kind", "value", "cap", "over"}``.
    """
    gauges = list(config.economy.get("gauges") or [])
    if not gauges:
        gauges = [{"name": "route_budget", "kind": "route_budget"}]
    results: list[dict] = []
    for gauge in gauges:
        kind = str(gauge.get("kind", ""))
        cap = int(gauge.get("cap") or 0)
        if kind == "word_cap":
            value = _eco_word_cap_value(root, config, gauge)
        elif kind == "count_cap":
            value = _eco_count_cap_value(root, config, gauge)
        elif kind == "route_budget":
            value, default_cap = _eco_route_budget(root, config)
            cap = int(gauge.get("cap") or default_cap)
        else:
            continue
        results.append(
            {
                "name": str(gauge.get("name", kind)),
                "kind": kind,
                "value": value,
                "cap": cap,
                "over": value > cap,
            },
        )
    return results


def _eco_scan_files(root: Path, config: Config) -> list[Path]:
    """Return the reference-scan set: docs-root ``*.md`` + reference roots."""
    files: set[Path] = set(_eco_md_files(root / config.docs_root))
    for pattern in config.economy.get("reference_roots", []):
        expanded = _eco_expand(str(pattern), config)
        for hit in root.glob(expanded):
            if hit.is_file():
                files.add(hit)
            elif hit.is_dir():
                files.update(p for p in hit.rglob("*") if p.is_file())
    return sorted(files)


def inbound_references(
    root: Path,
    config: Config,
    targets: list[Path],
    exclude: dict[str, set[str]] | None = None,
) -> dict[str, list[str]]:
    """Map each target to the files that cite it (plain-text scan, stdlib).

    A scanner file cites a target when it contains (a) an id-pattern token
    (``config.economy["id_patterns"]``) drawn from the target's filename, or
    (b) the target's filename stem. Scans every ``*.md`` under the docs root
    plus every text file under each ``economy["reference_roots"]`` glob; a
    file never counts as citing itself. ``exclude`` maps a target *stem* to
    resolved scanner paths that must not count as citations — the pass record
    whose harvest table licenses a slug's deletion would otherwise hold every
    harvested file forever (the triple filter became unsatisfiable).
    """
    exclude = exclude or {}
    patterns = [re.compile(p) for p in config.economy.get("id_patterns", [])]
    scanners: list[tuple[Path, str]] = []
    for f in _eco_scan_files(root, config):
        text = _eco_read_text(f)
        if text is not None:
            scanners.append((f, text))
    refs: dict[str, list[str]] = {}
    for target in targets:
        ids = {m for pat in patterns for m in pat.findall(target.name)}
        needles = ids | {target.stem}
        excluded = exclude.get(target.stem, set())
        citing = {
            _eco_rel(f, root)
            for f, text in scanners
            if f.resolve() != target.resolve()
            and f.resolve().as_posix() not in excluded
            and any(needle in text for needle in needles)
        }
        refs[_eco_rel(target, root)] = sorted(citing)
    return refs


def _eco_expired(path: Path, window_days: Any) -> tuple[bool, int]:
    """Return (past-window?, age-in-days) for ``path`` (mtime-based)."""
    if window_days is None:
        return False, 0
    age = (time.time() - path.stat().st_mtime) / _ECO_SECONDS_PER_DAY
    return age > float(window_days), int(age)


def _eco_delete_row(
    rel: str,
    cls: dict,
    *,
    expired: bool,
    in_harvest: bool,
    n_refs: int,
) -> dict:
    """Build one delete would-act row carrying the TRIPLE FILTER verdict."""
    blockers: list[str] = []
    if not in_harvest:
        blockers.append("not harvested")
    if n_refs:
        blockers.append(f"inbound refs: {n_refs}")
    if not expired:
        blockers.append("window not reached")
    return {
        "path": rel,
        "action": "delete",
        "reason": f"class '{cls['name']}' ({cls.get('window_days')}d window)",
        "eligible": not blockers,
        "blockers": blockers,
        "class": cls["name"],
    }


def _eco_archive_row(rel: str, cls: dict, *, expired: bool) -> dict:
    """Build one archive would-act row (window is the only gate)."""
    return {
        "path": rel,
        "action": "archive",
        "reason": f"class '{cls['name']}' ({cls.get('window_days')}d window)",
        "eligible": expired,
        "blockers": [] if expired else ["window not reached"],
        "class": cls["name"],
    }


def _eco_class_files(classes: list[dict], buckets: dict[str, list[Path]]) -> list:
    """Return (class, file) pairs over every classified file, class order."""
    return [(cls, f) for cls in classes for f in buckets.get(cls["name"], [])]


def _eco_class_rows(
    root: Path,
    classes: list[dict],
    buckets: dict[str, list[Path]],
    harvested: set[str],
    refs: dict[str, list[str]],
) -> tuple[list[dict], list[EconomyFinding], int]:
    """Return (would-act rows, expired/delete_with_refs findings, debt)."""
    rows: list[dict] = []
    findings: list[EconomyFinding] = []
    debt = 0
    for cls, f in _eco_class_files(classes, buckets):
        expired, age = _eco_expired(f, cls.get("window_days"))
        rel = _eco_rel(f, root)
        if expired:
            debt += 1
            message = (
                f"{age}d old exceeds the {cls.get('window_days')}d "
                f"'{cls['name']}' window"
            )
            findings.append(EconomyFinding(rel, "expired", message))
        mode = cls.get("mode")
        if mode == "delete_tomb":
            n_refs = len(refs.get(rel, []))
            in_harvest = f.stem in harvested
            rows.append(
                _eco_delete_row(
                    rel,
                    cls,
                    expired=expired,
                    in_harvest=in_harvest,
                    n_refs=n_refs,
                ),
            )
            if expired and n_refs:
                message = f"expired but still cited by {n_refs} file(s)"
                findings.append(EconomyFinding(rel, "delete_with_refs", message))
        elif mode == "archive":
            rows.append(_eco_archive_row(rel, cls, expired=expired))
    return rows, findings, debt


def _eco_base_findings(
    root: Path,
    buckets: dict[str, list[Path]],
    gauges: list[dict],
) -> list[EconomyFinding]:
    """Return the unbadged + over_cap findings."""
    findings = [
        EconomyFinding(
            _eco_rel(f, root),
            "unbadged",
            "no Status badge and no economy class",
        )
        for f in buckets.get("_unbadged", [])
    ]
    findings += [
        EconomyFinding(
            g["name"],
            "over_cap",
            f"gauge '{g['name']}' at {g['value']} words/files vs cap {g['cap']}",
        )
        for g in gauges
        if g["over"]
    ]
    return findings


def economy_check(
    root: Path,
    config: Config,
    *,
    harvested: set[str] | None = None,
    harvest_exclude: dict[str, set[str]] | None = None,
) -> dict:
    """Run the full economy pass: census, gauges, findings, debt, would-act.

    Findings: ``unbadged`` (doc with no badge and no class), ``over_cap`` (a
    gauge over its cap), ``expired`` (file past its class window — the kit
    supports **day** windows only; "bands" are a host cadence unit, not a kit
    unit), and ``delete_with_refs`` (an expired delete-class file still
    cited). ``debt`` counts expired files. ``would_act`` delete rows carry the
    TRIPLE FILTER: eligible only when the file's stem (slug) is in
    ``harvested`` AND it is past its window AND it has zero inbound refs;
    blockers are the explicit strings ``"not harvested"`` /
    ``"inbound refs: N"`` / ``"window not reached"``.
    """
    harvested = set(harvested or set())
    classes = _eco_classes(config)
    buckets = classify_docs(root, config)
    census = {
        name: {"files": len(files), "words": sum(_eco_wc(f) for f in files)}
        for name, files in buckets.items()
    }
    gauges = economy_gauges(root, config)
    delete_targets = [
        f
        for cls in classes
        if cls.get("mode") == "delete_tomb"
        for f in buckets.get(cls["name"], [])
    ]
    refs = (
        inbound_references(root, config, delete_targets, harvest_exclude)
        if delete_targets
        else {}
    )
    rows, class_findings, debt = _eco_class_rows(
        root,
        classes,
        buckets,
        harvested,
        refs,
    )
    findings = _eco_base_findings(root, buckets, gauges) + class_findings
    return {
        "census": census,
        "gauges": gauges,
        "findings": findings,
        "debt": debt,
        "would_act": rows,
    }


def tombstone_line(path: Path, summary: str) -> str:
    """Render one ~20-word tombstone: ``slug - date - last path - what-it-was``."""
    short = " ".join(summary.split()[:12])
    return f"- {path.stem} - {date.today().isoformat()} - {path.as_posix()} - {short}"


def _eco_doc_summary(path: Path) -> str:
    """Return a short what-it-was summary: first heading or non-blank line."""
    text = _eco_read_text(path) or ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return lines[0] if lines else "(empty file)"


def _eco_tombstone_shard(
    root: Path,
    config: Config,
    cls: dict,
    rel_path: Path,
) -> Path:
    """Return the per-band tombstone shard path for one deleted file's class."""
    tomb = cls.get("tombstone_dir")
    if tomb:
        tomb_dir = root / _eco_expand(str(tomb), config)
    else:
        tomb_dir = root / rel_path.parent / "pruned"
    return tomb_dir / f"band-{date.today().strftime('%Y%m')}.md"


def _eco_append_tombstone(shard: Path, line: str) -> None:
    """Append one tombstone line to the shard (create with banner if absent).

    Read-modify-write through ``atomic_write_text`` so a crash mid-append can
    never leave a truncated shard.
    """
    if shard.exists():
        text = shard.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            text += "\n"
    else:
        today = date.today()
        text = (
            f"# Tombstones — band {today.strftime('%Y%m')}\n\n"
            "> **Status:** `archive`\n\n"
            f"> Pruned by the context-economy actuator; created "
            f"{today.isoformat()}. One line per deleted file: "
            "slug - date - last path - what-it-was.\n\n"
        )
    atomic_write_text(shard, text + line + "\n")


def _eco_dry_line(row: dict) -> str:
    """Render one would-act row as a dry-run report line."""
    if row.get("eligible"):
        return f"would {row['action']} {row['path']} ({row['reason']})"
    return f"hold {row['path']}: " + "; ".join(row.get("blockers", []))


def _eco_apply_rows(root: Path, config: Config, rows: list[dict]) -> list[str]:
    """Delete eligible delete rows, tombstoning each; archive rows advisory."""
    class_by_name = {c["name"]: c for c in _eco_classes(config)}
    lines: list[str] = []
    for row in rows:
        if not row.get("eligible"):
            lines.append(_eco_dry_line(row))
            continue
        if row.get("action") != "delete":
            lines.append(
                f"advisory: {row['action']} {row['path']} is a host action — "
                "the kit never moves files",
            )
            continue
        path = root / row["path"]
        if not path.is_file():
            lines.append(f"skipped {row['path']}: file no longer exists")
            continue
        cls = class_by_name.get(str(row.get("class", "")), {})
        shard = _eco_tombstone_shard(root, config, cls, Path(row["path"]))
        summary = _eco_doc_summary(path)
        _eco_append_tombstone(shard, tombstone_line(Path(row["path"]), summary))
        path.unlink()
        lines.append(f"deleted {row['path']} -> tombstone {_eco_rel(shard, root)}")
    return lines


def economy_actuate(
    root: Path,
    config: Config,
    report: dict,
    *,
    apply: bool = False,
    acknowledged: bool = False,
) -> list[str]:
    """Apply (or dry-run) the would-act plan from ``economy_check``.

    Dry-run (the default) returns the would-act lines without touching
    anything. ``apply=True`` acts only under the maturity ALLOWLIST:
    ``"normal"`` applies, ``"gated"`` applies only with
    ``acknowledged=True`` (the CE-14 first-prune human-review tier), and
    anything else — including ``"shadow"`` and any typo — refuses outright.
    The lock is acquired atomically (``O_CREAT|O_EXCL``); a pre-existing lock
    refuses (another actuation in flight) and is left in place. It then
    deletes ONLY eligible delete rows (one tombstone line per deletion,
    appended to the class's ``<tombstone_dir>/band-<YYYYMM>.md`` shard),
    removes its own lock in a ``finally`` block, and returns the action
    lines. Archive rows are advisory — the kit never moves files.
    """
    if not apply:
        return [_eco_dry_line(row) for row in report.get("would_act", [])]
    maturity = str(config.economy.get("maturity", "shadow")).strip().lower()
    if maturity not in ("gated", "normal"):
        # Allowlist, not a blocklist: a typo'd maturity ("Shadow", "shadoww")
        # must refuse, never silently apply — deletion is the one place the
        # kit's fail-open posture inverts to fail-closed.
        return [
            f"refused: economy maturity {maturity!r} does not permit apply "
            "(allowed: 'gated' with --reviewed, 'normal') — nothing changed",
        ]
    if maturity == "gated" and not acknowledged:
        return [
            "refused: economy maturity is 'gated' — the first executing prune "
            "needs an explicit human review acknowledgment (pass --reviewed); "
            "promote maturity to 'normal' once the first prune has been "
            "reviewed — nothing changed",
        ]
    lock = root / config.state_dir / "economy.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        # O_CREAT|O_EXCL: atomic acquire — check-then-create raced, and two
        # concurrent actuations could clobber a tombstone shard.
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return [
            f"refused: {config.state_dir}/economy.lock exists — another "
            "actuation may be in flight; nothing changed",
        ]
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"locked {date.today().isoformat()}\n")
        return _eco_apply_rows(root, config, report.get("would_act", []))
    finally:
        lock.unlink(missing_ok=True)


def issue_body(report: dict) -> str:
    """Render the retention-debt routine issue body (markdown).

    Census table + debt count + the top would-act rows (eligible first) — the
    ``--issue-body`` emit the debt-threshold routine posts.
    """
    lines = [
        "## Context-economy retention debt",
        "",
        f"**Debt (expired files): {report.get('debt', 0)}**",
        "",
        "### Census",
        "",
        "| class | files | words |",
        "| --- | --- | --- |",
    ]
    for name, row in sorted(report.get("census", {}).items()):
        lines.append(f"| {name} | {row['files']} | {row['words']} |")
    top = sorted(report.get("would_act", []), key=lambda r: not r.get("eligible"))
    if top:
        lines += ["", "### Top would-act rows", ""]
        lines += [f"- {_eco_dry_line(row)}" for row in top[:10]]
    return "\n".join(lines) + "\n"

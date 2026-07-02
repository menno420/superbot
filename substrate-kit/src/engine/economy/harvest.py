"""Harvest-table parsing + stub rendering (plan §5.B, Lane B4).

The harvest table is the delete-side safety input of the TRIPLE FILTER: a
pass record commits what it *harvested* from the files it reviewed into a
markdown table under a heading containing "harvest". ``parse_harvest_tables``
recovers the committed slugs (a file is delete-eligible only once its slug
appears here); ``harvest_table_stub`` renders the kit-defined row format,
which round-trips through the parser. Pure stdlib; returns data / text.
"""

from __future__ import annotations

import re
from pathlib import Path

_HRV_HEADING_RE = re.compile(r"^#{1,6}\s")
# A table separator row: only pipes, dashes, colons, and whitespace.
_HRV_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|?$")

_HRV_HEADER_ROW = "| slug | status/PR | ⚑ flags | 💡 ideas | 📊 telemetry |"
_HRV_SEPARATOR_ROW = "| --- | --- | --- | --- | --- |"


def _hrv_first_cell(line: str) -> str | None:
    """Return a table row's first-column cell (None when empty)."""
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if not cells:
        return None
    cell = cells[0].strip("`* ")
    return cell or None


def _hrv_slugs_from_text(text: str) -> set[str]:
    """Collect first-column data cells from tables under harvest headings.

    A "harvest heading" is any markdown heading containing ``harvest``
    (case-insensitive). Within such a section, each contiguous run of ``|``
    lines is one table: its first row is the header (skipped), separator rows
    are skipped, every other row contributes its first cell. Surrounding
    prose is tolerated.
    """
    slugs: set[str] = set()
    in_harvest = False
    in_table = False
    table_is_harvest = False
    for line in text.splitlines():
        if _HRV_HEADING_RE.match(line):
            in_harvest = "harvest" in line.lower()
            in_table = False
            continue
        if not in_harvest or not line.lstrip().startswith("|"):
            in_table = False
            continue
        if not in_table:
            # First row of a new table = header. Only a table whose FIRST
            # header cell is "slug" is a harvest table — an inventory or
            # pending table under a "Harvest backlog" heading must never mark
            # files as harvested (that is a deletion license).
            in_table = True
            header = (_hrv_first_cell(line) or "").lower()
            table_is_harvest = header == "slug"
            continue
        if not table_is_harvest or _HRV_SEPARATOR_RE.match(line.strip()):
            continue
        cell = _hrv_first_cell(line)
        if cell:
            slugs.add(cell)
    return slugs


def parse_harvest_tables(pass_records_dir: Path) -> set[str]:
    """Return every harvested slug committed in the pass-record tables.

    Scans ``*.md`` under ``pass_records_dir`` for markdown tables sitting
    under any heading containing ``"harvest"`` (case-insensitive) and
    collects the first-column cell of each data row (header + separator rows
    skipped). Tolerant of surrounding prose; empty set when the directory is
    absent.
    """
    if not pass_records_dir.is_dir():
        return set()
    slugs: set[str] = set()
    for f in sorted(pass_records_dir.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        slugs |= _hrv_slugs_from_text(text)
    return slugs


def harvest_table_stub(entries: list[dict]) -> str:
    """Render the kit-defined harvest table for ``entries``.

    Columns: ``slug | status/PR | ⚑ flags | 💡 ideas | 📊 telemetry``. Each
    entry supplies ``slug`` (required) plus optional ``status`` / ``flags`` /
    ``ideas`` / ``telemetry``. The output includes the ``## Harvest`` heading
    so it round-trips through ``parse_harvest_tables`` unchanged.
    """
    lines = ["## Harvest", "", _HRV_HEADER_ROW, _HRV_SEPARATOR_ROW]
    for entry in entries:
        lines.append(
            "| {slug} | {status} | {flags} | {ideas} | {telemetry} |".format(
                slug=entry.get("slug", ""),
                status=entry.get("status", "—"),
                flags=entry.get("flags", "—"),
                ideas=entry.get("ideas", "—"),
                telemetry=entry.get("telemetry", "—"),
            ),
        )
    return "\n".join(lines) + "\n"


def harvest_sources(pass_records_dir: Path) -> dict[str, set[str]]:
    """Map each harvested slug to the pass-record files that harvested it.

    The harvest table row is the *deletion license* for its slug — the pass
    record naming a slug must not count as an inbound reference to it, or the
    triple filter becomes unsatisfiable (every harvested file is "referenced"
    by its own harvest record).
    """
    sources: dict[str, set[str]] = {}
    if not pass_records_dir.is_dir():
        return sources
    for record in sorted(pass_records_dir.glob("*.md")):
        try:
            text = record.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for slug in _hrv_slugs_from_text(text):
            sources.setdefault(slug, set()).add(record.resolve().as_posix())
    return sources

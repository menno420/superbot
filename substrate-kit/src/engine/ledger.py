"""Decision ledger — the ``[D-NNNN]`` provenance-separated rulebook (Lane B6).

Implements the kit's ``docs/decisions.md`` grammar (plan: Q-0214.4 depth — a
constitution cites decisions by id instead of narrating them inline). One
entry is::

    ## [D-0001] <title>
    - status: decided | superseded | retired
    - date: YYYY-MM-DD
    - supersedes: D-NNNN        (optional)
    - superseded-by: D-NNNN     (stamped on the OLD entry when superseded)
    - verdict: <one ruling line>
    - why: <2-3 lines, continuation lines allowed>
    - provenance: <link or ref>

``parse_ledger`` is tolerant of prose between entries (the ledger is a living
markdown doc, not a database). ``append_decision`` assigns the next id and —
when superseding — rewrites the old entry in place so the chain is stamped on
both ends. ``check_ledger`` and ``check_stamp_discipline`` are the hygiene
checkers, reusing the ``Finding`` record from ``engine.checks.check_docs``.
Pure stdlib; every write goes through ``atomic_write_text``.
"""

from __future__ import annotations

import re
from datetime import date as _led_date
from pathlib import Path

from engine.checks.check_docs import Finding
from engine.lib.atomicio import atomic_write_text

LEDGER_FILENAME = "decisions.md"

# `## [D-0001] <title>` — the strict entry heading.
_LED_HEADING_RE = re.compile(r"^## \[(D-\d{3,})\] (.+)$")
# Any `## ` heading that *tries* to be an entry but fails the strict form.
_LED_HEADING_ATTEMPT_RE = re.compile(r"^##\s*\[?\s*D-", re.IGNORECASE)
# `- key: value` field line inside an entry block.
_LED_FIELD_RE = re.compile(r"^- ([a-z-]+):\s*(.*)$")
# A bare decision id, for supersedes targets and stamp-discipline citations.
_LED_ID_RE = re.compile(r"\bD-\d{3,}\b")
_LED_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_LED_STATUSES = frozenset({"decided", "superseded", "retired"})
_LED_REQUIRED_FIELDS = ("status", "date", "verdict", "why", "provenance")

_LED_HEADER = """# Decisions

> **Status:** `living-ledger` — append-only decision ledger; entries are \
superseded, never deleted.

<!-- Grammar: ## [D-NNNN] <title> / - status: decided|superseded|retired / \
- date: YYYY-MM-DD / - supersedes: D-NNNN (opt) / - superseded-by: D-NNNN \
(opt) / - verdict: <one line> / - why: <2-3 lines> / - provenance: <ref> -->
"""


def _led_field_key(raw: str) -> str:
    """Map a grammar field name to its entry-dict key (``-`` -> ``_``)."""
    return raw.replace("-", "_")


def _led_blocks(text: str) -> list[tuple[int, list[str]]]:
    """Split ``text`` into entry blocks: ``(heading lineno, block lines)``.

    A block starts at any ``## `` heading that looks like a decision entry
    (strict or malformed) and runs until the next ``## `` heading or EOF.
    Prose outside blocks is ignored.
    """
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            current = None
            if _LED_HEADING_ATTEMPT_RE.match(line):
                current = [line]
                blocks.append((lineno, current))
        elif current is not None:
            current.append(line)
    return blocks


def _led_parse_block(lines: list[str]) -> dict | None:
    """Parse one entry block into a dict, or ``None`` if the heading is bad."""
    match = _LED_HEADING_RE.match(lines[0])
    if match is None:
        return None
    entry: dict = {
        "id": match.group(1),
        "title": match.group(2).strip(),
        "status": None,
        "date": None,
        "supersedes": None,
        "superseded_by": None,
        "verdict": None,
        "why": None,
        "provenance": None,
    }
    last_key: str | None = None
    for line in lines[1:]:
        field = _LED_FIELD_RE.match(line)
        if field is not None:
            key = _led_field_key(field.group(1))
            if key in entry and key not in ("id", "title"):
                entry[key] = field.group(2).strip()
                last_key = key
            else:
                last_key = None
        elif line[:1].isspace() and line.strip() and last_key is not None:
            # Continuation line (indented) — the multi-line `why` case.
            entry[last_key] = f"{entry[last_key]}\n{line.strip()}"
        elif not line.strip():
            last_key = None
    return entry


def parse_ledger(text: str) -> list[dict]:
    """Parse ledger ``text`` into entry dicts, tolerating prose between entries.

    Malformed headings are skipped here (``check_ledger`` reports them);
    missing fields parse as ``None``.
    """
    entries: list[dict] = []
    for _, lines in _led_blocks(text):
        entry = _led_parse_block(lines)
        if entry is not None:
            entries.append(entry)
    return entries


def next_decision_id(entries: list[dict]) -> str:
    """Return the next free decision id (``D-0001`` for an empty ledger)."""
    highest = 0
    for entry in entries:
        try:
            highest = max(highest, int(entry["id"].split("-", 1)[1]))
        except (KeyError, IndexError, ValueError):
            continue
    return f"D-{highest + 1:04d}"


def _led_format_entry(entry: dict) -> str:
    """Render one entry dict back into its grammar block."""
    lines = [f"## [{entry['id']}] {entry['title']}"]
    lines.append(f"- status: {entry['status']}")
    lines.append(f"- date: {entry['date']}")
    if entry.get("supersedes"):
        lines.append(f"- supersedes: {entry['supersedes']}")
    if entry.get("superseded_by"):
        lines.append(f"- superseded-by: {entry['superseded_by']}")
    lines.append(f"- verdict: {entry['verdict']}")
    why = str(entry["why"]).split("\n")
    lines.append(f"- why: {why[0]}")
    lines.extend(f"  {cont}" for cont in why[1:])
    lines.append(f"- provenance: {entry['provenance']}")
    return "\n".join(lines)


def _led_stamp_superseded(text: str, old_id: str, new_id: str) -> str:
    """Rewrite ``old_id``'s entry in ``text``: status + superseded-by stamp."""
    out: list[str] = []
    in_target = False
    stamped = False
    for line in text.splitlines():
        if line.startswith("## "):
            # ANY level-2 heading ends the current block (mirrors _led_blocks)
            # — a prose section after the target must never get stamped.
            heading = _LED_HEADING_RE.match(line)
            in_target = heading is not None and heading.group(1) == old_id
        field = _LED_FIELD_RE.match(line) if in_target else None
        if field is not None:
            key = field.group(1)
            if key == "status":
                out.append("- status: superseded")
                out.append(f"- superseded-by: {new_id}")
                stamped = True
                continue
            if key == "superseded-by" and stamped:
                continue  # replaced above
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def append_decision(
    path: Path,
    *,
    title: str,
    verdict: str,
    why: str,
    provenance: str,
    supersedes: str | None = None,
    date: str | None = None,
) -> dict:
    """Append a new decision to the ledger at ``path`` and return its dict.

    Creates the file (header + grammar comment) when absent, assigns the next
    free id, and — when ``supersedes`` names an existing entry — rewrites that
    old entry in place (``status: superseded`` plus a ``superseded-by`` stamp)
    so the chain is recorded on both ends. The whole file is written atomically.
    Raises ``ValueError`` when ``supersedes`` names an id not in the ledger.
    """
    text = path.read_text(encoding="utf-8") if path.exists() else _LED_HEADER
    entries = parse_ledger(text)
    if supersedes is not None:
        known = {entry["id"] for entry in entries}
        if supersedes not in known:
            msg = f"supersedes target {supersedes} not found in {path.name}"
            raise ValueError(msg)
    entry = {
        "id": next_decision_id(entries),
        "title": title,
        "status": "decided",
        "date": date or _led_date.today().isoformat(),
        "supersedes": supersedes,
        "superseded_by": None,
        "verdict": verdict,
        "why": why,
        "provenance": provenance,
    }
    if supersedes is not None:
        text = _led_stamp_superseded(text, supersedes, entry["id"])
    if not text.endswith("\n"):
        text += "\n"
    atomic_write_text(path, f"{text}\n{_led_format_entry(entry)}\n")
    return entry


def current_rules(entries: list[dict]) -> list[dict]:
    """Return the live rule set: supersedes chains resolved, retired dropped.

    An entry is live when its status is neither ``superseded`` nor ``retired``
    *and* no other entry names it as a supersedes target (chain resolution
    holds even when the old entry missed its stamp).
    """
    replaced = {e["supersedes"] for e in entries if e.get("supersedes")}
    return [
        e
        for e in entries
        if e.get("status") not in ("superseded", "retired") and e["id"] not in replaced
    ]


def check_ledger(path: Path) -> list[Finding]:
    """Validate the ledger grammar; return findings (empty for a clean file).

    Flags: unparseable entry blocks, missing/invalid required fields, duplicate
    ids, dangling ``supersedes`` targets, non-monotonic ids, and a superseded
    entry missing its ``superseded-by`` stamp. An absent ledger yields no
    findings (adoption plants it).
    """
    if not path.exists():
        return []
    rel = path.name
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    entries: list[dict] = []
    for lineno, lines in _led_blocks(text):
        entry = _led_parse_block(lines)
        if entry is None:
            msg = f"L{lineno}: unparseable entry heading: {lines[0].strip()}"
            findings.append(Finding(rel, "ledger", msg))
            continue
        entries.append(entry)
        for field in _LED_REQUIRED_FIELDS:
            if not entry.get(field):
                msg = f"L{lineno}: {entry['id']} missing required field `{field}`"
                findings.append(Finding(rel, "ledger", msg))
        status = entry.get("status")
        if status and status not in _LED_STATUSES:
            allowed = ", ".join(sorted(_LED_STATUSES))
            msg = f"L{lineno}: {entry['id']} invalid status `{status}` ({allowed})"
            findings.append(Finding(rel, "ledger", msg))
        if entry.get("date") and not _LED_DATE_RE.match(entry["date"]):
            msg = f"L{lineno}: {entry['id']} invalid date `{entry['date']}`"
            findings.append(Finding(rel, "ledger", msg))
        if status == "superseded" and not entry.get("superseded_by"):
            msg = f"L{lineno}: {entry['id']} superseded without a superseded-by stamp"
            findings.append(Finding(rel, "ledger", msg))

    seen: set[str] = set()
    known = {entry["id"] for entry in entries}
    previous = 0
    for entry in entries:
        number = int(entry["id"].split("-", 1)[1])
        if entry["id"] in seen:
            findings.append(Finding(rel, "ledger", f"duplicate id {entry['id']}"))
        elif number <= previous:
            msg = f"non-monotonic id {entry['id']} after D-{previous:04d}"
            findings.append(Finding(rel, "ledger", msg))
        seen.add(entry["id"])
        previous = max(previous, number)
        target = entry.get("supersedes")
        if target and target not in known:
            msg = f"{entry['id']} supersedes dangling target {target}"
            findings.append(Finding(rel, "ledger", msg))
    return findings


def check_stamp_discipline(docs_root: Path, ledger_path: Path) -> list[Finding]:
    """Flag a decision id cited from more than one doc outside the ledger.

    The provenance-separated model wants each ``D-NNNN`` stamped at exactly one
    home (the rule it justifies); a second citation is drift risk — when the
    decision changes, one of the two goes stale. Kind ``stamp`` (warn-class).
    """
    if not docs_root.exists():
        return []
    ledger_resolved = ledger_path.resolve()
    citations: dict[str, list[str]] = {}
    for doc in sorted(docs_root.rglob("*.md")):
        if doc.resolve() == ledger_resolved:
            continue
        try:
            text = doc.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = doc.relative_to(docs_root).as_posix()
        for cited in set(_LED_ID_RE.findall(text)):
            citations.setdefault(cited, []).append(rel)
    findings: list[Finding] = []
    for cited, docs in sorted(citations.items()):
        if len(docs) > 1:
            cite_list = ", ".join(sorted(docs))
            msg = (
                f"{cited} cited from {len(docs)} docs ({cite_list}) — "
                "stamp each decision at one home"
            )
            findings.append(Finding(sorted(docs)[0], "stamp", msg))
    return findings

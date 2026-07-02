"""Tests for the [D-NNNN] decision ledger (Lane B6).

Covers the grammar round-trip (append / supersede / parse / current_rules),
every ``check_ledger`` finding class firing and not firing, and the
stamp-discipline scan.
"""

from pathlib import Path

import pytest

from engine.ledger import (
    LEDGER_FILENAME,
    append_decision,
    check_ledger,
    check_stamp_discipline,
    current_rules,
    next_decision_id,
    parse_ledger,
)


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _entry(
    id_: str,
    *,
    status: str = "decided",
    date: str = "2026-07-01",
    extra: str = "",
) -> str:
    return (
        f"## [{id_}] A rule\n"
        f"- status: {status}\n"
        f"- date: {date}\n"
        f"{extra}"
        "- verdict: do the thing\n"
        "- why: because it works\n"
        "- provenance: Q-0001\n"
    )


# ---------------------------------------------------------------------------
# Round-trip: append 3, supersede 1, parse back
# ---------------------------------------------------------------------------


def test_round_trip_append_supersede_parse(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    for n in ("one", "two", "three"):
        append_decision(
            path,
            title=f"rule {n}",
            verdict=f"verdict {n}",
            why=f"why {n}",
            provenance=f"ref {n}",
            date="2026-07-01",
        )
    new = append_decision(
        path,
        title="rule two v2",
        verdict="tighter verdict",
        why="the old one drifted",
        provenance="ref v2",
        supersedes="D-0002",
        date="2026-07-02",
    )
    assert new["id"] == "D-0004"
    entries = parse_ledger(path.read_text(encoding="utf-8"))
    assert [e["id"] for e in entries] == ["D-0001", "D-0002", "D-0003", "D-0004"]
    old = entries[1]
    assert old["status"] == "superseded"
    assert old["superseded_by"] == "D-0004"
    live = current_rules(entries)
    assert [e["id"] for e in live] == ["D-0001", "D-0003", "D-0004"]
    # The rewritten file still validates clean.
    assert check_ledger(path) == []


def test_append_creates_header_with_badge_and_grammar(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    append_decision(path, title="t", verdict="v", why="w", provenance="p")
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# Decisions")
    assert "**Status:** `living-ledger`" in text
    assert "Grammar:" in text


def test_append_stamps_todays_date_by_default(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    entry = append_decision(path, title="t", verdict="v", why="w", provenance="p")
    assert len(entry["date"]) == 10 and entry["date"].count("-") == 2


def test_append_unknown_supersedes_target_raises(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    with pytest.raises(ValueError, match="D-0099"):
        append_decision(
            path,
            title="t",
            verdict="v",
            why="w",
            provenance="p",
            supersedes="D-0099",
        )


def test_multiline_why_round_trips(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    why = "line one\nline two\nline three"
    append_decision(path, title="t", verdict="v", why=why, provenance="p")
    entries = parse_ledger(path.read_text(encoding="utf-8"))
    assert entries[0]["why"] == why
    assert check_ledger(path) == []


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parse_tolerates_prose_between_entries():
    text = (
        "# Decisions\n\nSome intro prose.\n\n"
        + _entry("D-0001")
        + "\nA paragraph of commentary between entries.\n\n"
        + _entry("D-0002")
    )
    entries = parse_ledger(text)
    assert [e["id"] for e in entries] == ["D-0001", "D-0002"]
    assert entries[0]["title"] == "A rule"
    assert entries[0]["verdict"] == "do the thing"


def test_parse_skips_malformed_heading():
    text = "## [D-bogus] not an id\n- status: decided\n" + _entry("D-0001")
    assert [e["id"] for e in parse_ledger(text)] == ["D-0001"]


def test_next_decision_id_empty_and_sequence():
    assert next_decision_id([]) == "D-0001"
    assert next_decision_id([{"id": "D-0001"}, {"id": "D-0007"}]) == "D-0008"


def test_current_rules_drops_retired_and_resolves_unstamped_chain():
    entries = [
        {"id": "D-0001", "status": "decided", "supersedes": None},
        {"id": "D-0002", "status": "retired", "supersedes": None},
        # D-0003 supersedes D-0001 but the old entry was never stamped —
        # the chain still resolves.
        {"id": "D-0003", "status": "decided", "supersedes": "D-0001"},
    ]
    assert [e["id"] for e in current_rules(entries)] == ["D-0003"]


# ---------------------------------------------------------------------------
# check_ledger — every finding class, firing and not firing
# ---------------------------------------------------------------------------


def test_check_ledger_absent_file_is_clean(tmp_path):
    assert check_ledger(tmp_path / "nope.md") == []


def test_check_ledger_clean_file(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    _write(path, _entry("D-0001") + "\n" + _entry("D-0002"))
    assert check_ledger(path) == []


def test_check_ledger_unparseable_block(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    _write(path, "## [D-oops] broken heading\n- status: decided\n")
    findings = check_ledger(path)
    assert len(findings) == 1
    assert findings[0].kind == "ledger" and "unparseable" in findings[0].message


def test_check_ledger_duplicate_ids(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    _write(path, _entry("D-0001") + "\n" + _entry("D-0001"))
    messages = [f.message for f in check_ledger(path)]
    assert any("duplicate id D-0001" in m for m in messages)


def test_check_ledger_dangling_supersedes(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    _write(path, _entry("D-0001", extra="- supersedes: D-0042\n"))
    messages = [f.message for f in check_ledger(path)]
    assert any("dangling target D-0042" in m for m in messages)


def test_check_ledger_non_monotonic_ids(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    _write(path, _entry("D-0002") + "\n" + _entry("D-0001"))
    messages = [f.message for f in check_ledger(path)]
    assert any("non-monotonic id D-0001" in m for m in messages)


def test_check_ledger_superseded_without_stamp(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    _write(path, _entry("D-0001", status="superseded"))
    messages = [f.message for f in check_ledger(path)]
    assert any("without a superseded-by stamp" in m for m in messages)


def test_check_ledger_stamped_superseded_is_clean(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    text = (
        _entry("D-0001", status="superseded", extra="- superseded-by: D-0002\n")
        + "\n"
        + _entry("D-0002", extra="- supersedes: D-0001\n")
    )
    _write(path, text)
    assert check_ledger(path) == []


def test_check_ledger_missing_field_and_bad_status(tmp_path):
    path = tmp_path / LEDGER_FILENAME
    _write(path, "## [D-0001] thin\n- status: maybe\n- date: 2026-07-01\n")
    findings = check_ledger(path)
    messages = [f.message for f in findings]
    assert any("invalid status `maybe`" in m for m in messages)
    assert any("missing required field `verdict`" in m for m in messages)


# ---------------------------------------------------------------------------
# Stamp discipline
# ---------------------------------------------------------------------------


def test_stamp_discipline_multi_home_citation_flagged(tmp_path):
    docs = tmp_path / "docs"
    ledger = docs / LEDGER_FILENAME
    _write(ledger, _entry("D-0001"))
    _write(docs / "a.md", "Rule per [D-0001].\n")
    _write(docs / "b.md", "Also justified by D-0001.\n")
    findings = check_stamp_discipline(docs, ledger)
    assert len(findings) == 1
    f = findings[0]
    assert f.kind == "stamp"
    assert "D-0001" in f.message and "a.md" in f.message and "b.md" in f.message


def test_stamp_discipline_single_home_and_ledger_exempt(tmp_path):
    docs = tmp_path / "docs"
    ledger = docs / LEDGER_FILENAME
    # The ledger mentions its own ids constantly — never counted.
    _write(ledger, _entry("D-0001") + "\n" + _entry("D-0002"))
    _write(docs / "a.md", "Home stamp for D-0001.\n")
    _write(docs / "b.md", "Home stamp for D-0002.\n")
    assert check_stamp_discipline(docs, ledger) == []


def test_stamp_discipline_absent_docs_root(tmp_path):
    assert check_stamp_discipline(tmp_path / "nope", tmp_path / "l.md") == []

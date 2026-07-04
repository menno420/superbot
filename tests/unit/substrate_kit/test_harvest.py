"""Tests for harvest-table parsing + the kit stub (economy lane B4).

Covers slug extraction under harvest headings (case-insensitive), header and
separator skipping, tolerance of surrounding prose, non-harvest tables being
ignored, multi-file scans, and the stub round-tripping through the parser.
"""

from pathlib import Path

from engine.economy.harvest import harvest_table_stub, parse_harvest_tables


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_parse_basic_table(tmp_path):
    _write(
        tmp_path / "pass-1.md",
        "# Pass record\n\n"
        "Some intro prose.\n\n"
        "## Harvest\n\n"
        "| slug | status/PR | flags |\n"
        "| --- | --- | --- |\n"
        "| 2026-06-01-a | merged #12 | — |\n"
        "| 2026-06-02-b | closed | ⚑ |\n",
    )
    assert parse_harvest_tables(tmp_path) == {"2026-06-01-a", "2026-06-02-b"}


def test_parse_heading_match_is_case_insensitive(tmp_path):
    _write(
        tmp_path / "pass.md",
        "### Weekly HARVEST sweep\n\n"
        "| slug | status |\n"
        "| --- | --- |\n"
        "| the-slug | done |\n",
    )
    assert parse_harvest_tables(tmp_path) == {"the-slug"}


def test_parse_ignores_tables_under_other_headings(tmp_path):
    _write(
        tmp_path / "pass.md",
        "## Inventory\n\n"
        "| slug | status |\n"
        "| --- | --- |\n"
        "| not-harvested | open |\n\n"
        "## Harvest\n\n"
        "| slug | status |\n"
        "| --- | --- |\n"
        "| harvested | done |\n\n"
        "## Later section\n\n"
        "| slug | status |\n"
        "| --- | --- |\n"
        "| also-not | open |\n",
    )
    assert parse_harvest_tables(tmp_path) == {"harvested"}


def test_parse_tolerates_prose_between_heading_and_table(tmp_path):
    _write(
        tmp_path / "pass.md",
        "## Harvest pass\n\n"
        "The table below records what was pulled forward.\n\n"
        "| slug | status |\n"
        "| --- | --- |\n"
        "| kept-slug | merged |\n\n"
        "Trailing commentary after the table.\n",
    )
    assert parse_harvest_tables(tmp_path) == {"kept-slug"}


def test_parse_two_tables_in_one_harvest_section(tmp_path):
    _write(
        tmp_path / "pass.md",
        "## Harvest\n\n"
        "| slug | status |\n"
        "| --- | --- |\n"
        "| first | done |\n\n"
        "And a second batch:\n\n"
        "| slug | status |\n"
        "| --- | --- |\n"
        "| second | done |\n",
    )
    assert parse_harvest_tables(tmp_path) == {"first", "second"}


def test_parse_strips_backticks_and_bold(tmp_path):
    _write(
        tmp_path / "pass.md",
        "## Harvest\n\n"
        "| slug | status |\n"
        "| --- | --- |\n"
        "| `ticked` | done |\n"
        "| **bolded** | done |\n",
    )
    assert parse_harvest_tables(tmp_path) == {"ticked", "bolded"}


def test_parse_scans_multiple_files(tmp_path):
    table = "## Harvest\n\n| slug | s |\n| --- | --- |\n| {s} | x |\n"
    _write(tmp_path / "a.md", table.format(s="from-a"))
    _write(tmp_path / "b.md", table.format(s="from-b"))
    assert parse_harvest_tables(tmp_path) == {"from-a", "from-b"}


def test_parse_missing_dir_is_empty(tmp_path):
    assert parse_harvest_tables(tmp_path / "nope") == set()


def test_parse_file_with_no_harvest_section_is_empty(tmp_path):
    _write(tmp_path / "pass.md", "# Notes\n\nJust prose, no tables.\n")
    assert parse_harvest_tables(tmp_path) == set()


def test_stub_renders_kit_columns():
    stub = harvest_table_stub(
        [{"slug": "2026-06-01-a", "status": "merged #12", "flags": "⚑ self"}],
    )
    assert "## Harvest" in stub
    assert "| slug | status/PR | ⚑ flags | 💡 ideas | 📊 telemetry |" in stub
    assert "| 2026-06-01-a | merged #12 | ⚑ self | — | — |" in stub


def test_stub_round_trips_through_parser(tmp_path):
    entries = [
        {"slug": "2026-06-01-a", "status": "merged #12"},
        {"slug": "2026-06-02-b", "ideas": "💡 split the cog"},
    ]
    _write(tmp_path / "pass.md", harvest_table_stub(entries))
    assert parse_harvest_tables(tmp_path) == {"2026-06-01-a", "2026-06-02-b"}


def test_stub_of_no_entries_still_round_trips(tmp_path):
    _write(tmp_path / "pass.md", harvest_table_stub([]))
    assert parse_harvest_tables(tmp_path) == set()

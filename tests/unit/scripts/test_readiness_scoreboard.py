"""Tests for ``scripts/readiness_scoreboard.py`` — the readiness tally/render."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "readiness_scoreboard.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("readiness_scoreboard_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_cell_status_exact_only(mod):
    assert mod._cell_status(" Done ") == "Done"
    assert mod._cell_status(" **Partial** ") == "Partial"
    assert mod._cell_status(" Not Done ") == "Not Done"
    # Prose / headline cells with trailing text must NOT count.
    assert mod._cell_status("**Partial** — all are editable") is None
    assert mod._cell_status("Reason text") is None


def test_tally_map_counts_only_table_cells(mod, tmp_path):
    doc = tmp_path / "x-production-readiness-map-2026-06-12.md"
    doc.write_text(
        "# X map\n\n"
        "Prose mentioning Done and Partial should not count.\n\n"
        "| Item | Path | Status |\n"
        "|---|---|---|\n"
        "| a | `disbot/x.py` | Done |\n"
        "| b | `disbot/y.py` | Partial |\n"
        "| c | `disbot/z.py` | **Done** |\n"
        "| d | `disbot/w.py` | Not Done |\n"
        "| e | headline | **Partial** — trailing prose |\n",
        encoding="utf-8",
    )
    t = mod.tally_map(doc)
    assert (t.done, t.partial, t.not_done) == (2, 1, 1)
    assert t.total == 4
    assert t.pct == 50


def test_render_has_aggregate_row(mod):
    table = mod.render({"Alpha": mod.Tally(done=3, partial=1, not_done=0)})
    assert "| Alpha |" in table
    assert "**All subsystems**" in table
    assert "Done %" in table


def test_inject_is_idempotent(mod, tmp_path, monkeypatch):
    readme = tmp_path / "README.md"
    readme.write_text(
        f"# Title\n\nintro\n\n{mod.START}\nold\n{mod.END}\n\ntail\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "README", readme)
    rendered = mod.render({"Alpha": mod.Tally(done=1, partial=0, not_done=0)})
    once = mod._inject(rendered)
    readme.write_text(once, encoding="utf-8")
    twice = mod._inject(rendered)
    assert once == twice
    assert once.count(mod.START) == 1 and once.count(mod.END) == 1
    assert "tail" in once

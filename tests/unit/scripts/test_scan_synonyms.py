"""Tests for ``scripts/scan_synonyms.py`` — the command-synonym map scanner.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules). Pure
stdlib, so it runs in CI with no extra dependencies.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "scan_synonyms.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("scan_synonyms_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# The real module uses the *annotated* form, so it must be covered.
ANNOTATED = '''
from __future__ import annotations

COMMAND_SYNONYMS: dict[str, list[str]] = {
    "help": ["hilfe", "commands"],
    "rank": ["lvl", "xp"],
}
'''

PLAIN = '''
COMMAND_SYNONYMS = {"ban": ["sperren"]}
'''


def _write(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "synonyms.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_scan_synonyms_handles_annotated_assignment(mod, tmp_path):
    records = mod.scan_synonyms(_write(tmp_path, ANNOTATED))
    by_canon = {r["canonical"]: r["synonyms"] for r in records}
    assert by_canon == {"help": ["hilfe", "commands"], "rank": ["lvl", "xp"]}


def test_scan_synonyms_handles_plain_assignment(mod, tmp_path):
    records = mod.scan_synonyms(_write(tmp_path, PLAIN))
    assert records == [{"canonical": "ban", "synonyms": ["sperren"]}]


def test_scan_synonyms_real_repo(mod):
    records = mod.scan_synonyms()
    by_canon = {r["canonical"]: r["synonyms"] for r in records}
    # The real COMMAND_SYNONYMS is populated and uses the annotated form.
    assert len(records) >= 20
    assert "lb" not in by_canon  # canonical keys are command names, not aliases
    assert "bj" in by_canon.get("blackjack", [])

"""Pin docs/ux/pattern-library.md to the live pattern registry.

The doc is a generated export (NOT source of truth); this freshness gate
fails when the registry changes without regenerating — same pattern as the
other generated-artifact gates.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "export_pattern_library.py"
_DOC = _REPO_ROOT / "docs" / "ux" / "pattern-library.md"


def _load_exporter():
    spec = importlib.util.spec_from_file_location("export_pattern_library", _SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["export_pattern_library"] = module
    spec.loader.exec_module(module)
    return module


def test_pattern_library_doc_is_fresh():
    exporter = _load_exporter()
    assert _DOC.exists(), (
        "docs/ux/pattern-library.md missing — run "
        "python3.10 scripts/export_pattern_library.py"
    )
    assert _DOC.read_text() == exporter.generate(), (
        "pattern-library.md drifted from the registry — regenerate with "
        "python3.10 scripts/export_pattern_library.py"
    )


def test_doc_carries_the_generated_marker():
    text = _DOC.read_text()
    assert "NOT SOURCE OF TRUTH" in text
    assert "uxlab-verdict" in text  # the verdict routing instructions

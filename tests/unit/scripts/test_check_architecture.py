"""Tests for ``scripts/check_architecture.py`` — focus on RC-1 lazy-import
report mode and the layer-boundary classification.

The checker resolves a file's layer from ``DISBOT_ROOT``, so the synthetic-file
tests monkeypatch that module global to a ``tmp_path`` tree and drop fake
``<layer>/<name>.py`` files under it.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_architecture.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("check_architecture_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# services may import utils/core/governance/services — but NOT cogs or views.
_RULES = {
    "layers": {
        "services": {
            "may_import": ["utils", "core", "services", "governance"],
            "type_checking_exempt": True,
        },
    },
    "known_violations": [],
    "known_lazy_violations": [],
}

_MODULE_LEVEL = "from cogs.foo import bar\n"
_LAZY = "def f():\n    from cogs.foo import bar\n    return bar\n"


def _write(mod, tmp_path, monkeypatch, rel, src):
    monkeypatch.setattr(mod, "DISBOT_ROOT", tmp_path)
    f = tmp_path / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(src, encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# Module-level imports — the binding contract (unchanged behaviour)
# ---------------------------------------------------------------------------


def test_module_level_cross_layer_is_error(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "services/x.py", _MODULE_LEVEL)
    vs = mod.check_layer_boundaries([f], _RULES)
    assert [v.check for v in vs] == ["layer_boundary"]
    assert vs[0].severity == "error"


def test_allowed_import_not_flagged(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "services/x.py", "from utils.db import x\n")
    assert mod.check_layer_boundaries([f], _RULES) == []


# ---------------------------------------------------------------------------
# RC-1 — lazy (function-body) imports
# ---------------------------------------------------------------------------


def test_lazy_cross_layer_not_reported_by_default(mod, tmp_path, monkeypatch):
    """Default run must ignore lazy imports (back-compat with the old checker)."""
    f = _write(mod, tmp_path, monkeypatch, "services/y.py", _LAZY)
    assert mod.check_layer_boundaries([f], _RULES) == []


def test_lazy_cross_layer_reported_as_warning_with_flag(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "services/z.py", _LAZY)
    vs = mod.check_layer_boundaries([f], _RULES, report_lazy=True)
    assert len(vs) == 1
    assert vs[0].check == "lazy_layer_boundary"
    # Lazy findings are ALWAYS warnings → strict mode exit stays 0.
    assert vs[0].severity == "warning"


def test_known_lazy_exact_file_marked_known(mod, tmp_path, monkeypatch):
    rules = {
        **_RULES,
        "known_lazy_violations": [{"file": "services/k.py", "import": "cogs"}],
    }
    f = _write(mod, tmp_path, monkeypatch, "services/k.py", _LAZY)
    vs = mod.check_layer_boundaries([f], rules, report_lazy=True)
    assert len(vs) == 1
    assert "[known]" in vs[0].message
    assert vs[0].severity == "warning"


def test_known_lazy_file_prefix_marked_known(mod, tmp_path, monkeypatch):
    """A directory `file_prefix` entry allowlists the whole seam (RC-1 seam)."""
    rules = {
        **_RULES,
        "known_lazy_violations": [{"file_prefix": "services/", "import": "cogs"}],
    }
    f = _write(mod, tmp_path, monkeypatch, "services/deep/mod.py", _LAZY)
    vs = mod.check_layer_boundaries([f], rules, report_lazy=True)
    assert len(vs) == 1 and "[known]" in vs[0].message


def test_known_lazy_does_not_match_other_target(mod, tmp_path, monkeypatch):
    """An allowlist for cogs must NOT silence a lazy import of a different layer."""
    rules = {
        **_RULES,
        "known_lazy_violations": [{"file_prefix": "services/", "import": "cogs"}],
    }
    src = "def f():\n    import views.base\n    return views.base\n"
    f = _write(mod, tmp_path, monkeypatch, "services/m.py", src)
    vs = mod.check_layer_boundaries([f], rules, report_lazy=True)
    assert len(vs) == 1 and "[known]" not in vs[0].message


# ---------------------------------------------------------------------------
# _ImportVisitor + summary helper
# ---------------------------------------------------------------------------


def test_visitor_separates_lazy_from_module_level(mod):
    tree = ast.parse("from cogs.a import b\ndef f():\n    from services.c import d\n")
    v = mod._ImportVisitor()
    v.visit(tree)
    assert "cogs.a" in [m for _, m, _ in v.imports]
    assert "services.c" in [m for _, m, _ in v.lazy_imports]
    assert "cogs.a" not in [m for _, m, _ in v.lazy_imports]


def test_counts_by_check(mod):
    V = mod.Violation
    vs = [
        V(file=Path("a"), line=1, check="layer_boundary", message="m"),
        V(file=Path("b"), line=2, check="layer_boundary", message="m"),
        V(
            file=Path("c"),
            line=3,
            check="lazy_layer_boundary",
            message="m",
            severity="warning",
        ),
    ]
    assert mod._counts_by_check(vs) == {"layer_boundary": 2, "lazy_layer_boundary": 1}

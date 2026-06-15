"""Tests for ``scripts/context_map.py``.

The core (module-name mapping, forward-import split, AST reverse index, ownership
and docs/risk resolution) is tested without Grimp so it runs in CI, where dev
dependencies are not installed. The Grimp-backed path is exercised separately
behind ``pytest.importorskip`` and restores ``sys.path`` afterwards.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "context_map.py"


@pytest.fixture(scope="module")
def cm():
    spec = importlib.util.spec_from_file_location("context_map_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Path <-> module name
# ---------------------------------------------------------------------------


def test_module_name_for_service(cm):
    path = _REPO_ROOT / "disbot" / "services" / "moderation_service.py"
    assert cm.module_name(path) == "services.moderation_service"


def test_module_name_strips_init(cm, tmp_path, monkeypatch):
    monkeypatch.setattr(cm, "DISBOT_ROOT", tmp_path)
    pkg = tmp_path / "services" / "__init__.py"
    pkg.parent.mkdir(parents=True)
    pkg.write_text("", encoding="utf-8")
    assert cm.module_name(pkg) == "services"


def test_module_name_outside_disbot_is_none(cm):
    assert cm.module_name(_REPO_ROOT / "scripts" / "context_map.py") is None


# ---------------------------------------------------------------------------
# Forward imports — module-level vs lazy, internal-only
# ---------------------------------------------------------------------------


def test_forward_imports_split(cm, tmp_path):
    src = (
        "from services.audit_events import emit\n"
        "import requests\n"  # external — must be dropped
        "def handler():\n"
        "    from cogs.moderation_cog import Mod\n"
        "    return Mod\n"
    )
    f = tmp_path / "sample.py"
    f.write_text(src, encoding="utf-8")
    mod_level, lazy = cm.forward_imports(f)
    assert mod_level == ["services.audit_events"]
    assert lazy == ["cogs.moderation_cog"]


# ---------------------------------------------------------------------------
# Reverse backend — AST importers + transitive BFS
# ---------------------------------------------------------------------------


def test_ast_reverse_importers_and_downstream(cm):
    direct = {
        "services.x": {"cogs.a", "views.b"},
        "cogs.a": {"cogs.entry"},
    }
    rev = cm._Reverse("ast", direct, object())
    assert rev.importers("services.x") == ["cogs.a", "views.b"]
    # transitive: entry -> a -> x
    assert rev.downstream("services.x") == {"cogs.a", "views.b", "cogs.entry"}


def test_ast_reverse_empty_for_unknown(cm):
    rev = cm._Reverse("ast", {}, object())
    assert rev.importers("services.nope") == []
    assert rev.downstream("services.nope") == set()


# ---------------------------------------------------------------------------
# Ownership / docs / risk — read the real rule files (stable contracts)
# ---------------------------------------------------------------------------


def test_ownership_identifies_mutation_owner(cm):
    facts = cm.ownership_facts("services.moderation_service")
    assert any("mutation owner" in f for f in facts)
    assert any("moderation" in f for f in facts)


def test_ownership_empty_for_plain_module(cm):
    assert cm.ownership_facts("utils.cooldowns") == []


def test_related_docs_longest_prefix_wins(cm):
    overrides = {
        "overrides": [
            {"prefix": "services", "folio": "F1", "docs": ["d1"]},
            {"prefix": "services/moderation", "folio": "F2", "docs": ["d2"]},
        ],
        "layer_docs": {"services": ["layer"]},
    }
    folio, docs = cm.related_docs(
        "services/moderation_service.py", "services", overrides
    )
    assert folio == "F2"
    assert docs == ["d2"]


def test_related_docs_falls_back_to_layer(cm):
    overrides = {"overrides": [], "layer_docs": {"utils": ["docs/helper-policy.md"]}}
    folio, docs = cm.related_docs("utils/cooldowns.py", "utils", overrides)
    assert folio is None
    assert docs == ["docs/helper-policy.md"]


def test_known_arch_debt_flags_tracked_view_to_cog(cm):
    # views/moderation/modals.py imports cogs.moderation._helpers — a tracked
    # layer-boundary violation in architecture_rules/layers.yaml.
    notes = cm.known_arch_debt("views/moderation/modals.py")
    assert any("layer-boundary debt" in n for n in notes)


def test_risk_flags_mutation_and_fan_in(cm):
    flags = cm.risk_flags(
        "services/moderation_service.py",
        "services",
        importer_count=20,
        lazy_count=2,
        owner_facts=["owner"],
    )
    text = " ".join(flags)
    assert "mutation seam" in text
    assert "high fan-in" in text
    assert "lazy" in text


def test_risk_flags_clean_file(cm):
    flags = cm.risk_flags("utils/cooldowns.py", "utils", 0, 0, [])
    assert flags == ["no tracked architecture debt for this file."]


# ---------------------------------------------------------------------------
# Render smoke test (AST backend — no Grimp needed)
# ---------------------------------------------------------------------------


def test_render_contains_all_sections(cm):
    path = _REPO_ROOT / "disbot" / "services" / "moderation_service.py"
    rev = cm._Reverse(
        "ast", {"services.moderation_service": {"cogs.moderation_cog"}}, object()
    )
    out = cm.render(path, rev, cm.load_overrides(), max_importers=25)
    for header in (
        "# Context map for",
        "## File role / authority",
        "## Direct imports (module-level)",
        "## Imported by",
        "## Blast radius",
        "## Related docs",
        "## Relevant tests",
        "## Risk flags",
        "## Recommended read set before editing",
        "## Suggested checks after editing",
    ):
        assert header in out


# ---------------------------------------------------------------------------
# Grimp-backed path (skipped when grimp is absent, e.g. in CI)
# ---------------------------------------------------------------------------


def test_grimp_backend_resolves_real_importers(cm):
    pytest.importorskip("grimp")
    saved = list(sys.path)
    try:
        rev = cm.build_reverse()
        assert rev.engine == "grimp"
        importers = rev.importers("services.moderation_service")
        assert "cogs.moderation_cog" in importers
        assert len(rev.downstream("services.moderation_service")) > 0
    finally:
        sys.path[:] = saved

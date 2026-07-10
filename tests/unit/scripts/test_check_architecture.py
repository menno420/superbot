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


# ---------------------------------------------------------------------------
# No-dead-end terminal views (friction->guard, Q-0194)
# ---------------------------------------------------------------------------

_NO_DEAD_END_RULES = {
    "no_dead_end": {
        "severity": "warning",
        "game_dirs": ["views/games/", "views/rps/"],
        "exemptions": [
            {"view": "_ChallengeView", "method": "decline", "reason": "invite"},
        ],
    },
}

# A terminal handler that stop()s + renders the now-disabled self, never swapping
# to a nav-carrying view — the dead-end bug class this guard exists to catch.
_DEAD_END = (
    "import discord\n"
    "class GameOverView(discord.ui.View):\n"
    "    async def finish(self, interaction):\n"
    "        for item in self.children:\n"
    "            item.disabled = True\n"
    "        await interaction.response.edit_message(view=self)\n"
    "        self.stop()\n"
)

# The correct shape — swaps to a freshly-constructed result view that carries nav.
_SWAPS = (
    "import discord\n"
    "class GameView(discord.ui.View):\n"
    "    async def finish(self, interaction):\n"
    "        result = _ResultView()\n"
    "        await interaction.response.edit_message(view=result)\n"
    "        self.stop()\n"
)

# Delegates the swap to another coroutine (e.g. _start_pvp deals the next hand) —
# not a dead-end, must not be flagged.
_DELEGATES = (
    "import discord\n"
    "class GameView(discord.ui.View):\n"
    "    async def accept(self, interaction):\n"
    "        await interaction.response.edit_message(content='dealing', view=self)\n"
    "        self.stop()\n"
    "        await _start_next_round(interaction)\n"
)


def test_no_dead_end_flags_trapped_terminal_handler(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "views/games/over.py", _DEAD_END)
    vs = mod.check_no_dead_end_terminal_views([f], _NO_DEAD_END_RULES)
    assert len(vs) == 1
    assert vs[0].check == "no_dead_end"
    assert vs[0].severity == "warning"
    assert "GameOverView.finish" in vs[0].message


def test_no_dead_end_allows_view_swap(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "views/games/g.py", _SWAPS)
    assert mod.check_no_dead_end_terminal_views([f], _NO_DEAD_END_RULES) == []


def test_no_dead_end_allows_coroutine_delegation(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "views/games/g.py", _DELEGATES)
    assert mod.check_no_dead_end_terminal_views([f], _NO_DEAD_END_RULES) == []


def test_no_dead_end_respects_classmethod_allowlist(mod, tmp_path, monkeypatch):
    src = _DEAD_END.replace("GameOverView", "_ChallengeView").replace(
        "finish", "decline"
    )
    f = _write(mod, tmp_path, monkeypatch, "views/games/c.py", src)
    assert mod.check_no_dead_end_terminal_views([f], _NO_DEAD_END_RULES) == []


def test_no_dead_end_ignores_non_game_dirs(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "views/settings/s.py", _DEAD_END)
    assert mod.check_no_dead_end_terminal_views([f], _NO_DEAD_END_RULES) == []


def test_no_dead_end_ignores_handler_without_stop(mod, tmp_path, monkeypatch):
    # Renders the disabled self but never stop()s -> not a terminal handler.
    src = _DEAD_END.replace("        self.stop()\n", "")
    f = _write(mod, tmp_path, monkeypatch, "views/games/n.py", src)
    assert mod.check_no_dead_end_terminal_views([f], _NO_DEAD_END_RULES) == []


def test_no_dead_end_disabled_when_unconfigured(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "views/games/over.py", _DEAD_END)
    assert mod.check_no_dead_end_terminal_views([f], {}) == []

# ---------------------------------------------------------------------------
# baseview_inheritance — justifying-comment recognition (shift-plan Q2,
# 2026-07-10). The rule text always asked for "a comment"; the checker now
# actually recognizes the in-tree convention so documented views stop warning.
# ---------------------------------------------------------------------------

_BASEVIEW_RULES = {"base_view": {"exemptions": []}}

_UNDOCUMENTED_VIEW = (
    "import discord\n"
    "\n"
    "class MyPanel(discord.ui.View):\n"
    "    pass\n"
)

_DOCUMENTED_VIEW = (
    "import discord\n"
    "\n"
    "# Extends discord.ui.View directly (not BaseView): specialized lifecycle —\n"
    "# single-shot ephemeral confirm flow; nothing for on_timeout to edit.\n"
    "class MyPanel(discord.ui.View):\n"
    "    pass\n"
)

# The marker inside a string literal (not a comment) must NOT silence the warn.
_MARKER_IN_STRING_VIEW = (
    "import discord\n"
    "\n"
    'NOTE = "Extends discord.ui.View directly (not BaseView)"\n'
    "class MyPanel(discord.ui.View):\n"
    "    pass\n"
)


def test_baseview_undocumented_direct_view_warns(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "views/x/panel.py", _UNDOCUMENTED_VIEW)
    vs = mod.check_baseview_inheritance([f], _BASEVIEW_RULES)
    assert [v.check for v in vs] == ["baseview_inheritance"]
    assert vs[0].severity == "warning"


def test_baseview_justifying_comment_silences_warn(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "views/x/panel.py", _DOCUMENTED_VIEW)
    assert mod.check_baseview_inheritance([f], _BASEVIEW_RULES) == []


def test_baseview_marker_in_string_does_not_silence(mod, tmp_path, monkeypatch):
    f = _write(mod, tmp_path, monkeypatch, "views/x/panel.py", _MARKER_IN_STRING_VIEW)
    vs = mod.check_baseview_inheritance([f], _BASEVIEW_RULES)
    assert [v.check for v in vs] == ["baseview_inheritance"]


def test_baseview_comment_too_far_above_does_not_silence(
    mod,
    tmp_path,
    monkeypatch,
):
    # The justification must sit DIRECTLY above the class (within the lookback
    # window) — a file-header comment shouldn't blanket-silence every class.
    far = (
        "# Extends discord.ui.View directly (not BaseView): file header\n"
        "import discord\n" + "\n" * 10 + "class MyPanel(discord.ui.View):\n"
        "    pass\n"
    )
    f = _write(mod, tmp_path, monkeypatch, "views/x/panel.py", far)
    vs = mod.check_baseview_inheritance([f], _BASEVIEW_RULES)
    assert [v.check for v in vs] == ["baseview_inheritance"]


def test_baseview_live_tree_has_zero_undocumented_direct_views(mod):
    # Every direct discord.ui.View extension in the live tree is either in an
    # exempted directory (games) or carries the justifying comment — the
    # converged end-state this session established. A new undocumented direct
    # view should show up here (and in check_architecture output) immediately.
    import ast as _ast  # noqa: F401 — parity with checker import style

    rules = mod._load("canonical_helpers.yaml")
    files = sorted(mod.DISBOT_ROOT.rglob("*.py"))
    vs = mod.check_baseview_inheritance(files, rules)
    assert vs == [], [f"{v.file}:{v.line} {v.message}" for v in vs]

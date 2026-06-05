"""Repo-wide discord.py UI-collision guard (generalises the #528 fix).

discord.py 2.7 (components-v2) crashed two role/XP panels that shadowed its
internals (PR #528). These invariants stop the whole *class* of regression from
recurring in any view, rather than pinning the two specific panels:

* ``discord.ui.View._refresh(components)`` runs on every MESSAGE_UPDATE. A view
  defining its own ``_refresh`` shadows it and crashes the gateway loop, so no
  view may define a method named ``_refresh`` (the #528 fix renamed the panel
  re-render helper to ``_rerender``).
* ``discord.ui.Item.parent`` / ``Item._parent`` are owned by discord.py 2.7+
  (read-only property + internal check propagation), so assigning either on a
  ``ui.Item`` subclass (Select/Button) raises at construction. The #528 fix
  stored the panel reference as ``self._panel`` / ``self._owner_view``.
  (Assigning ``self.parent`` on a ``View`` / ``Modal`` is harmless and allowed —
  this guard is scoped to ``Item`` subclasses only.)

Companion to ``test_role_panels_discordpy_compat.py`` (the runtime check for the
two originally-broken panels); this AST scan keeps every *other* view honest.
"""

from __future__ import annotations

import ast
from pathlib import Path

_VIEWS_ROOT = Path(__file__).resolve().parents[3] / "disbot" / "views"

# A class is a discord.ui.Item subclass (read-only ``.parent``) when a direct
# base's trailing name is one of these or ends with ``Select`` / ``Button``.
_ITEM_BASE_TAILS = {"Item", "Select", "Button"}


def _view_files() -> list[Path]:
    return sorted(_VIEWS_ROOT.rglob("*.py"))


def _is_item_subclass(cls: ast.ClassDef) -> bool:
    for base in cls.bases:
        tail = ast.unparse(base).rsplit(".", 1)[-1]
        if tail in _ITEM_BASE_TAILS or tail.endswith(("Select", "Button")):
            return True
    return False


def _refresh_methods(tree: ast.AST) -> list[int]:
    return [
        item.lineno
        for cls in ast.walk(tree)
        if isinstance(cls, ast.ClassDef)
        for item in cls.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == "_refresh"
    ]


def _item_parent_assignments(tree: ast.AST) -> list[int]:
    hits: list[int] = []
    for cls in ast.walk(tree):
        if not (isinstance(cls, ast.ClassDef) and _is_item_subclass(cls)):
            continue
        for node in ast.walk(cls):
            if isinstance(node, ast.Assign):
                targets: list[ast.expr] = list(node.targets)
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            else:
                continue
            for tgt in targets:
                if (
                    isinstance(tgt, ast.Attribute)
                    and tgt.attr in ("parent", "_parent")
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "self"
                ):
                    hits.append(node.lineno)
    return hits


def test_no_view_shadows_view_refresh():
    offenders = [
        f"{p.relative_to(_VIEWS_ROOT.parent)}:{ln}"
        for p in _view_files()
        for ln in _refresh_methods(ast.parse(p.read_text(), filename=str(p)))
    ]
    assert not offenders, (
        "discord.py collision: a view defines `_refresh`, shadowing "
        "discord.ui.View._refresh (rename it to `_rerender`):\n  "
        + "\n  ".join(offenders)
    )


def test_no_item_subclass_assigns_parent():
    offenders = [
        f"{p.relative_to(_VIEWS_ROOT.parent)}:{ln}"
        for p in _view_files()
        for ln in _item_parent_assignments(ast.parse(p.read_text(), filename=str(p)))
    ]
    assert not offenders, (
        "discord.py collision: a discord.ui.Item subclass assigns "
        "`self.parent`/`self._parent` (read-only in discord.py 2.7+ — store the "
        "panel as `self._panel` / `self._owner_view`):\n  "
        + "\n  ".join(offenders)
    )

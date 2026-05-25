"""M2 pin — only one natural-language pipeline exists.

After M2, every passive natural-language reply must flow through the
central :mod:`core.runtime.ai.natural_language_stage`. No other cog
may install a direct ``@bot.listen('on_message')`` /
``Cog.listener('on_message')`` /
``Cog.event('on_message')`` that performs natural-language replies.

Existing platform listeners (message_pipeline orchestrator itself,
counting / chain / cleanup / xp message-pipeline STAGES) are
allowed — they go through ``message_pipeline.register``, not their
own ``on_message`` listener. The AST scan below distinguishes the
two.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_COGS = _REPO / "disbot" / "cogs"


def _on_message_listeners(tree: ast.AST) -> list[ast.FunctionDef]:
    """Return every async ``on_message`` listener function in ``tree``."""
    out: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in ("on_message", "_on_message"):
            continue
        for dec in node.decorator_list:
            if _decorator_listens_for_on_message(dec):
                out.append(node)
                break
    return out


def _decorator_listens_for_on_message(dec: ast.AST) -> bool:
    """Return True if the decorator is a discord ``on_message`` registrar."""
    if isinstance(dec, ast.Call):
        target = dec.func
    else:
        target = dec
    name = ""
    if isinstance(target, ast.Attribute):
        name = target.attr
    elif isinstance(target, ast.Name):
        name = target.id
    if name not in ("listen", "listener", "event"):
        return False
    if isinstance(dec, ast.Call):
        if not dec.args:
            return True  # @listener (no arg → discord infers from func name)
        first = dec.args[0]
        if isinstance(first, ast.Constant) and first.value == "on_message":
            return True
    else:
        return True
    return False


def test_no_cog_installs_its_own_on_message_listener():
    """Sweep ``disbot/cogs/`` for stray ``on_message`` listeners."""
    offenders: list[str] = []
    for path in _COGS.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        funcs = _on_message_listeners(tree)
        if funcs:
            for fn in funcs:
                offenders.append(f"{path.relative_to(_REPO)}::{fn.name}")
    assert not offenders, (
        "Cogs must not install their own on_message listeners after M2. "
        "Use a message_pipeline stage (registered via "
        "core.runtime.message_pipeline.register) so the central "
        "natural-language stage stays the only passive replier. "
        f"Offenders: {offenders}"
    )

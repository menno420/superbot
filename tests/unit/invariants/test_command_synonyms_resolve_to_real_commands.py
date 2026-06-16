"""Invariant: every ``COMMAND_SYNONYMS`` canonical is a real command.

BUG-0014 — ``utils/synonyms.py`` declared ``"coglist": ["listcogs", "cogslist"]``
but no ``coglist`` command was ever registered. The typo-resolver auto-corrected
the fuzzy token to that phantom canonical and ``bot1.on_command_error``
re-dispatched ``!coglist`` forever ("↩️ Ran ``!coglist`` — assumed from
``!coglist``" spam until the bot was restarted). This invariant fails closed if a
synonym's canonical is not a registered command name or alias, so an orphaned
synonym can never ship again.

AST-scoped to the prefix-command decorators across ``disbot/`` so it runs in well
under a second and needs no live bot / DB.

UNVERIFIED convenience guard (Q-0105, 2026-06-16): command discovery walks
``@commands.command`` / ``@commands.group`` decorators (+ function-name fallback
when no explicit ``name=``). If a future command is registered through some exotic
dynamic path this scan misses, the fix is to broaden the discovery (or add the
name) — not to weaken the synonym contract. Delete this guard if it proves
unreliable across multiple sessions.
"""

from __future__ import annotations

import ast
from pathlib import Path

from utils.synonyms import COMMAND_SYNONYMS

_DISBOT = Path(__file__).resolve().parents[3] / "disbot"


def _registered_command_tokens() -> set[str]:
    """Every prefix-command name + alias declared across ``disbot/`` (lowercased)."""
    tokens: set[str] = set()
    for path in _DISBOT.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                dotted = ast.unparse(dec.func)
                if not (dotted.endswith("command") or dotted.endswith("group")):
                    continue
                name: str | None = None
                for kw in dec.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        name = str(kw.value.value)
                    elif kw.arg == "aliases" and isinstance(
                        kw.value, (ast.List, ast.Tuple)
                    ):
                        for el in kw.value.elts:
                            if isinstance(el, ast.Constant):
                                tokens.add(str(el.value).lower())
                tokens.add((name or node.name).lower())
    return tokens


def test_every_synonym_canonical_is_a_registered_command() -> None:
    tokens = _registered_command_tokens()
    # Sanity: the scan must actually find the command surface, otherwise the
    # invariant would vacuously pass while discovery is silently broken.
    assert len(tokens) > 100, (
        f"command-decorator scan found only {len(tokens)} tokens — the AST "
        "discovery likely broke; fix it before trusting this guard."
    )
    orphans = sorted(c for c in COMMAND_SYNONYMS if c.lower() not in tokens)
    assert not orphans, (
        "COMMAND_SYNONYMS canonical(s) with no registered command (name or "
        f"alias): {orphans}. A synonym pointing at a phantom command "
        "auto-corrects to nothing and loops on re-dispatch (BUG-0014). Point "
        "the synonym at a real command or remove the entry."
    )

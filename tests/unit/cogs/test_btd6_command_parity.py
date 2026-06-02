"""Pin slash/prefix parity for every BTD6 command.

Every prefix command (``@commands.command``) must have a slash twin
(``@app_commands.command``) and vice versa — except commands on the
``SLASH_ONLY`` allowlist (modal-bearing commands, which cannot fire
from a prefix message).

Twin equivalence: both forms must share at least one common shared
builder call (``build_*``) so behavioural drift between the two forms
is contained.

AST-based to keep the test fast and to surface intent at the structural
level rather than relying on runtime invocation.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_COG_PATH = Path(__file__).resolve().parents[3] / "disbot" / "cogs" / "btd6_cog.py"

# Modal-triggering commands: they need ``send_modal`` as the initial
# response, which a prefix message can't provide. Document the
# exemption here so a future reader knows which commands intentionally
# lack a prefix twin.
SLASH_ONLY = frozenset(
    {
        "submit",
    },
)

# Some commands ship only as prefix (e.g. heavy debug helpers). When
# adding such an entry, document the rationale in the comment above.
#   ``ctteam`` — admin utility to paste a CT bracket id / group URL. Prefix is
#   the natural surface for pasting a long URL, and it is a low-traffic config
#   command (set once per weekly event), so it intentionally has no slash twin.
PREFIX_ONLY: frozenset[str] = frozenset({"ctteam"})


def _tree() -> ast.Module:
    return ast.parse(_COG_PATH.read_text())


def _decorator_call(dec: ast.AST) -> ast.Call | None:
    if isinstance(dec, ast.Call):
        return dec
    return None


def _decorator_name(dec: ast.AST) -> tuple[str, str] | None:
    """Return ``(module, attr)`` of the decorator call's target.

    Examples:
        ``@commands.command(...)``      → ("commands", "command")
        ``@app_commands.command(...)``  → ("app_commands", "command")
        ``@btd6_app_group.command(...)`` → ("btd6_app_group", "command")
        ``@bot.event``                  → None (not a call)
    """
    call = _decorator_call(dec)
    if call is None:
        return None
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    if not isinstance(func.value, ast.Name):
        return None
    return func.value.id, func.attr


# Decorator-prefix groupings: anything in the first set is a prefix
# command; anything in the second is a slash command. The cog uses
# ``@btd6_group.command(...)`` for prefix subcommands (a
# ``commands.Group``) and ``@btd6_app_group.command(...)`` for slash
# subcommands (an ``app_commands.Group``).
_PREFIX_REGISTRARS = frozenset({"commands", "btd6_group"})
_SLASH_REGISTRARS = frozenset({"app_commands", "btd6_app_group"})


def _decorator_name_kw(call: ast.Call) -> str | None:
    """Pull ``name="..."`` from a decorator-call's kwargs."""
    for kw in call.keywords:
        if kw.arg == "name" and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return None


def _collect_commands() -> (
    tuple[dict[str, ast.AsyncFunctionDef], dict[str, ast.AsyncFunctionDef]]
):
    """Walk the cog module and return ``(prefix_cmds, slash_cmds)``.

    Mapping is keyed by command name (the ``name=`` kwarg on the
    decorator) so prefix/slash twins line up by name even if their
    Python method names differ.
    """
    prefix: dict[str, ast.AsyncFunctionDef] = {}
    slash: dict[str, ast.AsyncFunctionDef] = {}
    tree = _tree()
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for dec in node.decorator_list:
            target = _decorator_name(dec)
            if target is None:
                continue
            module, attr = target
            if attr != "command":
                continue
            cmd_name = _decorator_name_kw(dec)  # type: ignore[arg-type]
            if cmd_name is None:
                continue
            if module in _PREFIX_REGISTRARS:
                prefix[cmd_name] = node
            elif module in _SLASH_REGISTRARS:
                slash[cmd_name] = node
    return prefix, slash


def _called_function_names(node: ast.AST) -> set[str]:
    """Collect names of all functions called inside a body.

    Resolves ``foo(...)``, ``self.foo(...)``, and ``mod.foo(...)`` to
    just ``"foo"`` for cross-form comparison.
    """
    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


def test_every_slash_has_a_prefix_twin() -> None:
    prefix, slash = _collect_commands()
    missing: set[str] = set()
    for name in slash:
        if name in SLASH_ONLY:
            continue
        if name not in prefix:
            missing.add(name)
    assert not missing, (
        f"Slash commands without a prefix twin: {sorted(missing)}. "
        f"Add them to SLASH_ONLY if intentionally slash-only."
    )


def test_every_prefix_has_a_slash_twin() -> None:
    prefix, slash = _collect_commands()
    missing: set[str] = set()
    for name in prefix:
        if name in PREFIX_ONLY:
            continue
        # The btd6 group decorator emits a prefix-only "btd6" parent
        # command — exclude it from twin matching.
        if name == "btd6":
            continue
        if name not in slash:
            missing.add(name)
    assert not missing, (
        f"Prefix commands without a slash twin: {sorted(missing)}. "
        f"Add them to PREFIX_ONLY if intentionally prefix-only."
    )


# ---------------------------------------------------------------------------
# Shared backbone
# ---------------------------------------------------------------------------

# Names that count as "shared backbone" — at least one of these must
# appear in BOTH the prefix and slash forms of a twin. The set is
# intentionally broad: anything starting with ``build_`` is considered
# a shared builder (the entire ``_builders.py`` / ``_embeds.py`` API
# follows that convention).
_SHARED_BACKBONE_PREFIXES = ("build_",)
_SHARED_BACKBONE_NAMES = frozenset(
    {
        "_response_to_embed",
        "answer_question",
        "response_to_embed",
        "safe_defer",
        "safe_edit",
        "safe_followup",
    },
)


def _shared_backbone_calls(names: set[str]) -> set[str]:
    return {
        n
        for n in names
        if n in _SHARED_BACKBONE_NAMES
        or any(n.startswith(p) for p in _SHARED_BACKBONE_PREFIXES)
    }


@pytest.mark.parametrize(
    "cmd",
    sorted(n for n in _collect_commands()[1] if n not in SLASH_ONLY and n != "btd6"),
)
def test_twins_share_a_backbone_call(cmd: str) -> None:
    prefix, slash = _collect_commands()
    if cmd not in prefix or cmd not in slash:
        pytest.skip(f"twin missing for {cmd!r}; covered by existence tests")
    prefix_calls = _shared_backbone_calls(_called_function_names(prefix[cmd]))
    slash_calls = _shared_backbone_calls(_called_function_names(slash[cmd]))
    common = prefix_calls & slash_calls
    assert common, (
        f"Twins for {cmd!r} share no backbone call. "
        f"Prefix calls backbone: {sorted(prefix_calls)}; "
        f"slash calls backbone: {sorted(slash_calls)}. "
        f"Both forms should route through a shared build_* / safe_* "
        f"helper to prevent drift."
    )

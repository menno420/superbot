#!/usr/bin/env python3.10
"""Guard: no two cogs may claim the same top-level command name or alias.

The class of outage this prevents is real: PR #1541 added an economy
``!give``/``!pay`` command that collided with mining's dormant admin ``give``
(present since the initial commit, never PR'd). On the next boot
``discord.ext.commands`` raised ``CommandRegistrationError``, ``mining_cog``
failed to load, the STRICT identity contract aborted startup, and the bot
crash-looped offline until #1544 retired the surface. That collision was 100%
statically detectable pre-merge; this checker detects it. The runtime boot
guard added in #1544 remains the post-deploy backstop for anything static
analysis can't see (dynamically registered commands).

What it does (offline, stdlib ``ast`` only):

- Walks ``disbot/cogs/**`` collecting top-level command tokens:
  ``@commands.command(...)`` / ``@commands.group(...)`` names + their
  ``aliases=[...]`` (the *prefix* namespace — one shared registry at boot),
  ``@app_commands.command(...)`` names and module/class-level
  ``app_commands.Group(name=...)`` assignments (the *slash* namespace —
  the app-command tree). ``@commands.hybrid_command`` / ``hybrid_group``
  claim **both** namespaces (none exist in the tree today, but the checker
  must not go blind the day one lands).
- Fails (exit 1) when a token is claimed by two or more distinct declaration
  sites **within the same namespace**, printing every site as ``file:line``
  so the fix is one grep away. Prefix and slash namespaces do not collide
  with each other (mirrors the discord.py registries).

Known limitations (by design — the boot guard covers these):

- Scope is ``disbot/cogs/**``; commands registered elsewhere (or added
  dynamically via ``bot.add_command``) are invisible to it.
- A non-literal ``name=`` / ``aliases=`` (variable, f-string) can't be
  resolved statically and is skipped.
- Subcommands (``@somegroup.command``) are correctly excluded — they live
  in their parent's namespace, not the top level.
- It scans *all* cog files, including any not loaded at boot; a collision
  involving an unloaded cog is still worth failing on (dormant commands are
  exactly how #1541 happened).

Run:  python3.10 scripts/check_command_collisions.py            # exit 1 on collision
      python3.10 scripts/check_command_collisions.py --list     # full token census

Not yet CI-wired (follow-up noted in
``docs/ideas/command-collision-checker-2026-06-29.md``); run it before merging
any PR that adds or renames a command.

UNVERIFIED (Q-0105, 2026-07-10): confirm its output against ground truth (the
#1544 runtime boot guard / a deliberately staged duplicate) a few times across
sessions before trusting it; delete this script if it proves unreliable over
multiple sessions — it is a convenience guard, the boot registry is the source
of truth.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
COGS_ROOT = REPO_ROOT / "disbot" / "cogs"

# Namespaces mirror the two discord.py registries: the prefix-command dict
# (names + aliases share it) and the app-command tree.
PREFIX = "prefix"
SLASH = "slash"


@dataclass(frozen=True)
class CommandDecl:
    """One statically-declared claim on a top-level command token."""

    token: str  # the name or alias being claimed
    namespace: str  # PREFIX | SLASH
    kind: str  # "name" | "alias" | "group"
    cog: str  # enclosing class name, or "<module>"
    file: str  # path relative to repo root
    line: int

    @property
    def site(self) -> str:
        return f"{self.file}:{self.line}"


def _dotted(node: ast.expr) -> tuple[str, ...]:
    """``app_commands.command`` → ``("app_commands", "command")``; empty if dynamic."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return tuple(reversed(parts))
    return ()


def _decorator_namespace(call_func: ast.expr) -> tuple[tuple[str, ...], str] | None:
    """Classify a decorator's callable → (claimed namespaces, kind) or None.

    The tail components are compared as a *tuple*, never via string
    ``endswith`` — ``"app_commands.command"`` string-endswith
    ``"commands.command"``, which would misfile every slash command.

    A hybrid command registers in *both* registries (one prefix command +
    one app command of the same name), so it claims both namespaces.
    """
    dotted = _dotted(call_func)
    if len(dotted) < 2:
        return None
    if dotted[-2:] == ("app_commands", "command"):
        return ((SLASH,), "name")
    if dotted[-2] == "commands":
        if dotted[-1] in ("command", "group"):
            return ((PREFIX,), "name" if dotted[-1] == "command" else "group")
        if dotted[-1] in ("hybrid_command", "hybrid_group"):
            kind = "name" if dotted[-1] == "hybrid_command" else "group"
            return ((PREFIX, SLASH), kind)
    return None


_ABSENT = "absent"
_LITERAL = "literal"
_DYNAMIC = "dynamic"


def _str_kwarg(call: ast.Call, kwarg: str) -> tuple[str, str | None]:
    """Resolve a string kwarg → (_LITERAL, value) | (_DYNAMIC, None) | (_ABSENT, None).

    The three-way split matters: an *absent* ``name=`` means discord.py uses
    the function name (resolvable), while a *dynamic* ``name=SOME_VAR`` is a
    real name we cannot see — falling back to the function name there would
    fabricate a token and could report a phantom collision (or hide a real
    one), so the caller skips the declaration instead.
    """
    for kw in call.keywords:
        if kw.arg == kwarg:
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return (_LITERAL, kw.value.value)
            return (_DYNAMIC, None)
    return (_ABSENT, None)


def _alias_kwarg(call: ast.Call) -> list[str]:
    for kw in call.keywords:
        if kw.arg == "aliases" and isinstance(kw.value, (ast.List, ast.Tuple)):
            return [
                el.value
                for el in kw.value.elts
                if isinstance(el, ast.Constant) and isinstance(el.value, str)
            ]
    return []


def extract_declarations(source: str, relpath: str) -> list[CommandDecl]:
    """All top-level command-token claims declared in one cog file."""
    tree = ast.parse(source, filename=relpath)
    decls: list[CommandDecl] = []

    class _Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self._class_stack: list[str] = []

        @property
        def _cog(self) -> str:
            return self._class_stack[-1] if self._class_stack else "<module>"

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self._class_stack.append(node.name)
            self.generic_visit(node)
            self._class_stack.pop()

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue  # bare @commands.command never appears; @checks aren't Calls we want anyway
                ns_kind = _decorator_namespace(dec.func)
                if ns_kind is None:
                    continue
                namespaces, kind = ns_kind
                state, literal = _str_kwarg(dec, "name")
                if state == _DYNAMIC:
                    continue  # unresolvable name — the boot guard's territory
                name = literal if literal is not None else node.name
                for namespace in namespaces:
                    decls.append(
                        CommandDecl(
                            name, namespace, kind, self._cog, relpath, dec.lineno
                        )
                    )
                if PREFIX in namespaces:  # aliases exist on the prefix side only
                    for alias in _alias_kwarg(dec):
                        decls.append(
                            CommandDecl(
                                alias,
                                PREFIX,
                                "alias",
                                self._cog,
                                relpath,
                                dec.lineno,
                            )
                        )
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_function(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._visit_function(node)

        def visit_Assign(self, node: ast.Assign) -> None:
            # module/class-level ``x = app_commands.Group(name="...")`` —
            # a top-level slash group (the _unified.py pattern).
            if isinstance(node.value, ast.Call):
                if _dotted(node.value.func)[-2:] == ("app_commands", "Group"):
                    _state, name = _str_kwarg(node.value, "name")
                    if name:
                        decls.append(
                            CommandDecl(
                                name, SLASH, "group", self._cog, relpath, node.lineno
                            )
                        )
            self.generic_visit(node)

    _Visitor().visit(tree)
    return decls


def find_collisions(
    decls: list[CommandDecl],
) -> dict[tuple[str, str], list[CommandDecl]]:
    """Group by (namespace, token); keep only tokens claimed at ≥2 distinct sites.

    Distinct *sites*, not distinct cogs: two same-name commands in one cog
    crash the boot registry just as hard as across cogs.
    """
    by_token: dict[tuple[str, str], list[CommandDecl]] = {}
    for d in decls:
        by_token.setdefault((d.namespace, d.token), []).append(d)
    return {
        key: claims
        for key, claims in by_token.items()
        if len({(c.file, c.line) for c in claims}) >= 2
    }


def collect_all(cogs_root: Path | None = None) -> list[CommandDecl]:
    # Late-bind the default so a caller (or test) may repoint COGS_ROOT.
    root = COGS_ROOT if cogs_root is None else cogs_root
    decls: list[CommandDecl] = []
    for path in sorted(root.rglob("*.py")):
        try:
            rel = str(path.relative_to(REPO_ROOT))
        except ValueError:  # a test fixture tree outside the repo
            rel = str(path)
        try:
            decls.extend(extract_declarations(path.read_text(encoding="utf-8"), rel))
        except SyntaxError as exc:  # pragma: no cover - unparsable cog = CI-red anyway
            print(f"  [WARN] {rel}: unparsable ({exc}) — skipped", file=sys.stderr)
    return decls


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--list", action="store_true", help="print the full token census and exit 0"
    )
    args = parser.parse_args(argv)

    decls = collect_all()
    if args.list:
        for d in sorted(decls, key=lambda d: (d.namespace, d.token)):
            print(f"{d.namespace:6} {d.kind:5} {d.token:32} {d.cog:28} {d.site}")
        try:
            scanned = COGS_ROOT.relative_to(REPO_ROOT)
        except ValueError:  # repointed root (tests)
            scanned = COGS_ROOT
        print(f"\n{len(decls)} token claims across {scanned}")
        return 0

    collisions = find_collisions(decls)
    if not collisions:
        print(f"check_command_collisions: OK — {len(decls)} token claims, 0 collisions")
        return 0

    print(f"check_command_collisions: {len(collisions)} collision(s) found\n")
    for (namespace, token), claims in sorted(collisions.items()):
        print(f"  [{namespace}] '{token}' claimed by {len(claims)} declarations:")
        for c in sorted(claims, key=lambda c: c.site):
            print(f"      {c.site}  ({c.cog}, {c.kind})")
        print()
    print(
        "Two cogs claiming one token crash the boot registry"
        " (CommandRegistrationError — the #1541 outage). Rename or retire one side."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

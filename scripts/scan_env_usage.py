#!/usr/bin/env python3.10
"""Scan the bot source for environment-variable usage (stdlib only, read-only).

The developer dashboard (``docs/planning/developer-dashboard-plan.md`` § "Secrets —
done safely") needs a **usage map**: each environment variable mapped to every
file/line that reads it, plus whether it is required (read without a default) and
which layers touch it. This is the *track-where-each-is-used* half of the owner's
ask — and it is deliberately the **safe** half: it reads variable **names and code
locations only**, never a value, and never an ``.env`` file. The dashboard can show
this map with zero secret access.

Detected access shapes (AST, so formatting/quoting never matters):

* ``os.getenv("NAME")`` / ``os.getenv("NAME", default)``
* ``os.environ.get("NAME")`` / ``os.environ.get("NAME", default)``
* ``os.environ["NAME"]`` (subscript — required: raises ``KeyError`` if absent)
* the ``from os import getenv, environ`` bare forms of all three

A variable is **required** when at least one usage reads it without a default
(``os.environ[...]`` is always required; ``getenv`` / ``.get`` with a single
argument has no default). That is the strict reading: if any call site assumes the
value is present, the deploy must provide it.

Pure stdlib so it runs in CI with no extra dependencies, mirroring
``scripts/export_dashboard_data.py`` (which calls :func:`scan_env_usage` to embed
the result in ``dashboard/data/dashboard.json``).

Run standalone to print the map::

    python3.10 scripts/scan_env_usage.py            # human-readable summary
    python3.10 scripts/scan_env_usage.py --json     # the raw JSON payload

Reliability (Q-0105): **unverified** — confirm the map against the live source a
few times across sessions before trusting it, and delete this seam if it proves
unreliable. It is a convenience generator, not load-bearing runtime code.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# The bot package is where runtime env vars are read. Scoped on purpose: the
# usage map is about the deployed bot's secrets, not tooling/test scaffolding.
DEFAULT_SCAN_ROOT = REPO_ROOT / "disbot"

# The ``os`` attribute calls that take an env-var name as their first string arg.
_GETTER_ATTRS = frozenset({"getenv", "get"})


def _name_layer(path: Path, scan_root: Path) -> str:
    """Map a source file to its architectural layer (``config``, ``services``…).

    The layer is the first path segment under the scan root (``disbot/``), e.g.
    ``disbot/services/foo.py`` -> ``services``. A top-level module such as
    ``disbot/config.py`` -> ``config`` (its stem), which keeps the high-signal
    central config file as its own bucket in the map.
    """
    try:
        rel = path.relative_to(scan_root)
    except ValueError:
        return "other"
    parts = rel.parts
    if len(parts) == 1:
        return rel.stem
    return parts[0]


def _string_arg(node: ast.expr | None) -> str | None:
    """Return ``node``'s value if it is a string literal, else ``None``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


class _EnvVisitor(ast.NodeVisitor):
    """Collect ``(name, line, has_default)`` env reads from one parsed module.

    Tracks ``from os import getenv/environ`` aliases so the bare forms are caught
    alongside the ``os.`` attribute forms.
    """

    def __init__(self) -> None:
        # name -> list of (line, has_default)
        self.reads: list[tuple[str, int, bool]] = []
        self._bare_getenv: set[str] = set()
        self._bare_environ: set[str] = set()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "os":
            for alias in node.names:
                local = alias.asname or alias.name
                if alias.name == "getenv":
                    self._bare_getenv.add(local)
                elif alias.name == "environ":
                    self._bare_environ.add(local)
        self.generic_visit(node)

    def _is_environ(self, node: ast.expr) -> bool:
        """True if ``node`` refers to ``os.environ`` (or an imported ``environ``)."""
        if isinstance(node, ast.Attribute):
            return node.attr == "environ" and (
                isinstance(node.value, ast.Name) and node.value.id == "os"
            )
        return isinstance(node, ast.Name) and node.id in self._bare_environ

    def _is_env_getter(self, func: ast.expr) -> bool:
        """True if ``func`` is an env read: ``os.getenv`` / ``os.environ.get`` /
        a bare imported ``getenv``.
        """
        if isinstance(func, ast.Attribute) and func.attr in _GETTER_ATTRS:
            owner = func.value
            # os.getenv(...) | os.environ.get(...) — never a plain dict's .get.
            is_os_getenv = (
                func.attr == "getenv"
                and isinstance(owner, ast.Name)
                and owner.id == "os"
            )
            return is_os_getenv or (func.attr == "get" and self._is_environ(owner))
        return isinstance(func, ast.Name) and func.id in self._bare_getenv

    def visit_Call(self, node: ast.Call) -> None:
        name: str | None = None
        if self._is_env_getter(node.func):
            name = _string_arg(node.args[0]) if node.args else None

        if name is not None:
            has_default = len(node.args) >= 2 or bool(node.keywords)
            self.reads.append((name, node.lineno, has_default))
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # os.environ["NAME"] — always required (KeyError if absent).
        if self._is_environ(node.value):
            name = _string_arg(node.slice)
            if name is not None:
                self.reads.append((name, node.lineno, False))
        self.generic_visit(node)


def scan_source(source: str) -> list[tuple[str, int, bool]]:
    """Return ``(name, line, has_default)`` env reads found in one module source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    visitor = _EnvVisitor()
    visitor.visit(tree)
    return visitor.reads


def scan_env_usage(
    scan_root: Path = DEFAULT_SCAN_ROOT,
    repo_root: Path = REPO_ROOT,
) -> list[dict]:
    """Build the env-var usage map for every ``*.py`` under ``scan_root``.

    Returns a list of records, one per variable, sorted required-first then by
    name::

        {
            "name": "DISCORD_BOT_TOKEN_PRODUCTION",
            "required": true,
            "usage_count": 1,
            "layers": ["config"],
            "usages": [{"file": "disbot/config.py", "line": 19, "layer": "config",
                        "has_default": false}],
        }

    Only names and locations — **never a value**.
    """
    by_name: dict[str, list[dict]] = {}
    for path in sorted(scan_root.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        reads = scan_source(source)
        if not reads:
            continue
        layer = _name_layer(path, scan_root)
        try:
            rel_file = str(path.relative_to(repo_root))
        except ValueError:
            rel_file = str(path)
        for name, line, has_default in reads:
            by_name.setdefault(name, []).append(
                {
                    "file": rel_file,
                    "line": line,
                    "layer": layer,
                    "has_default": has_default,
                },
            )

    records: list[dict] = []
    for name, usages in by_name.items():
        usages.sort(key=lambda u: (u["file"], u["line"]))
        required = any(not u["has_default"] for u in usages)
        layers = sorted({u["layer"] for u in usages})
        records.append(
            {
                "name": name,
                "required": required,
                "usage_count": len(usages),
                "layers": layers,
                "usages": usages,
            },
        )
    # Required first, then alphabetical — the most operationally critical vars top
    # the dashboard list.
    records.sort(key=lambda r: (not r["required"], r["name"]))
    return records


def _format_summary(records: list[dict]) -> str:
    """Render a short human-readable map for the CLI (no values, by design)."""
    lines = [f"{len(records)} environment variable(s) read by the bot source:\n"]
    for record in records:
        tag = "required" if record["required"] else "optional"
        layers = ", ".join(record["layers"])
        lines.append(
            f"  {record['name']:<32} [{tag:<8}] "
            f"{record['usage_count']} usage(s) · {layers}",
        )
    return "\n".join(lines)


DOC_PATH = REPO_ROOT / "docs" / "operations" / "env-vars.md"

# Everything ABOVE this marker is generated from the disbot scan and is rewritten on
# every ``--write-doc``; everything BELOW it is hand-maintained and PRESERVED across
# regenerations. This is the fix for the recurring footgun (#1119): the scanner only
# sees ``disbot/`` env-vars, so the **web-tier** vars (the submissions DB / GitHub mirror
# / dashboard OAuth secrets) have no generated home — they previously lived in a hand tail
# that a regenerate clobbered (and the byte-equality freshness test then rejected). The
# marker lets the two coexist: the generated head stays scanner-canonical, the web-tier
# tail is owner-maintained, and the freshness checks (test + drift guard) compare only the
# head. See docs/operations/botsite-deploy.md for the web-tier deploy recipe.
END_MARKER = (
    "<!-- END GENERATED — everything below is hand-maintained (web-tier env vars the "
    "disbot scanner can't see); the scanner preserves it across --write-doc. -->"
)

# The version-controlled default for the hand-maintained tail: the **Website tier** the
# scanner can't emit. Written on the first marker-aware ``--write-doc`` and PRESERVED (with
# any owner edits) on every run thereafter. Kept in sync with the §4.4 secret matrix in
# docs/planning/website-two-site-split-plan-2026-06-19.md + docs/operations/botsite-deploy.md.
_DEFAULT_WEBSITE_TAIL = """## Website tier (hand-maintained — not from the disbot scan)

These power the **two web services** (the public bot site + the dev dashboard) of the
website two-site split, not the bot worker, so the `disbot/` scanner above never emits
them. They are **dormant by default** — each service is a safe no-op until its var is set
(see [`botsite-deploy.md`](botsite-deploy.md) and the plan's §4.4 secret matrix). Names +
purpose only — never a value.

| Variable | Service(s) | Purpose / scope |
|---|---|---|
| `SUBMISSIONS_DB_DSN` | bot site (INSERT-only role) · dev site (full role) | The dashboard-owned submissions Postgres. The public site holds an **INSERT-only** role; the dev site holds the read/moderate role. Unset → `/submit` + moderation are dormant. |
| `SUBMISSIONS_IP_SALT` | bot site | Salt for the stored `source_ip_hash` (abuse forensics) — never the raw IP. Falls back to a per-process random salt when unset. |
| `GITHUB_ISSUE_MIRROR_TOKEN` | dev site only | Fine-grained PAT, repo-scoped to `menno420/superbot`, **Issues: Read & write only**. Mirrors an approved submission to one GitHub issue. **Never** on the public bot site. Unset → approve is disabled. |
| `BOT_OWNER_USER_ID` | dev site (also read by the bot) | Gates the owner-only moderation ring (`/admin/moderation`). Blank/garbage fails closed (matches nobody). |
| `DISCORD_OAUTH_CLIENT_ID` / `DISCORD_OAUTH_CLIENT_SECRET` / `DASHBOARD_SESSION_SECRET` | dev site (future gated manager) | Discord OAuth + signed-session secret for the per-guild control panel. Unset → the control zone is dormant. |
| `CONTROL_API_TOKEN` | dev site · bot worker | Bearer for the bot's private control API (per-guild writes, over the private network). Never on the public bot site. |
| `TURNSTILE_SECRET` / `HCAPTCHA_SECRET` *(optional)* | bot site | Reserved for a fast-follow `/submit` captcha (honeypot + rate-limit is the v1 default — plan §4.2 / §7 decision 6). Unset → no captcha. |
"""


def render_doc(records: list[dict]) -> str:
    """Render the env-var inventory as a committed operations reference doc.

    A ``living-ledger``-badged Markdown table — the in-repo, human-readable
    complement to the dashboard ``/env`` page (which needs the dashboard service
    deployed). Generated from :func:`scan_env_usage`, so the two never drift from
    one parser. Shows **names and code locations only** — never a value.
    """
    required = [r for r in records if r["required"]]
    optional = [r for r in records if not r["required"]]
    out: list[str] = [
        "# Environment variables — usage reference",
        "",
        "> **Status:** `living-ledger` — generated inventory of every environment",
        "> variable read by the bot source. **Source + the scanner win over this file.**",
        "",
        "<!-- GENERATED FILE — do not edit by hand. Refresh with:",
        "       python3.10 scripts/scan_env_usage.py --write-doc -->",
        "",
        "This is the in-repo, human-readable form of the dashboard `/env` usage map",
        "(`scripts/scan_env_usage.py`). It lists every variable the bot **reads**, where",
        "it reads it, and whether it is **required** (read without a default anywhere) or",
        "**optional** (a default is always supplied). It shows **names and code locations",
        "only — never a value**; the values live in Railway service variables",
        "(see [`production-deployment.md`](production-deployment.md)).",
        "",
        f"**{len(records)} variables** — {len(required)} required · {len(optional)} optional.",
        "",
    ]

    def _table(title: str, rows: list[dict]) -> list[str]:
        block = [f"## {title}", "", "| Variable | Layers | Usages |", "|---|---|---|"]
        for record in rows:
            layers = ", ".join(record["layers"])
            usages = "<br>".join(
                f"`{u['file']}:{u['line']}`"
                + (" *(default)*" if u["has_default"] else "")
                for u in record["usages"]
            )
            block.append(f"| `{record['name']}` | {layers} | {usages} |")
        block.append("")
        return block

    if required:
        out += _table(
            "Required (read without a default — the deploy must set these)",
            required,
        )
    if optional:
        out += _table("Optional (a default is always supplied)", optional)
    # End the generated region with the marker; everything below it (in the committed
    # file) is the hand-maintained web-tier tail, preserved by main() across regenerations.
    return "\n".join(out).rstrip() + "\n\n" + END_MARKER + "\n"


def _hand_tail(existing: str | None) -> str:
    """The hand-maintained tail to keep below :data:`END_MARKER`.

    Preserves whatever the committed file already carries after the marker (so owner
    edits survive a regeneration); falls back to :data:`_DEFAULT_WEBSITE_TAIL` when the
    file is absent or has no marker yet (the first marker-aware write).
    """
    if existing and END_MARKER in existing:
        return existing.split(END_MARKER, 1)[1].lstrip("\n")
    return _DEFAULT_WEBSITE_TAIL.lstrip("\n")


def _compose_doc(records: list[dict], *, existing: str | None = None) -> str:
    """The full env-vars.md: the regenerated head + the preserved hand-maintained tail."""
    if existing is None and DOC_PATH.exists():
        existing = DOC_PATH.read_text(encoding="utf-8")
    head = render_doc(records)  # ends with END_MARKER + "\n"
    tail = _hand_tail(existing)
    return head + "\n" + tail if tail else head


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print the usage map (summary / JSON) or write the doc."""
    parser = argparse.ArgumentParser(
        description="Scan the bot source for env-var usage (names + locations only).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the raw JSON payload instead of the human summary",
    )
    parser.add_argument(
        "--write-doc",
        action="store_true",
        help=f"(re)generate {DOC_PATH.relative_to(REPO_ROOT)} from the scan",
    )
    args = parser.parse_args(argv)

    records = scan_env_usage()
    if args.write_doc:
        DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
        DOC_PATH.write_text(_compose_doc(records), encoding="utf-8")
        print(f"wrote {DOC_PATH.relative_to(REPO_ROOT)} — {len(records)} variables")
    elif args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        print(_format_summary(records))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

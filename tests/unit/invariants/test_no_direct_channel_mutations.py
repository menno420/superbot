"""Channel-lifecycle convergence invariant (server-management PR4).

The ``ChannelCog`` command surface must route channel *mutations* through
``services.channel_lifecycle_service.ChannelLifecycleService`` — no direct
``channel.delete()`` / ``channel.edit()`` in the cog.

Scope notes:

* Only the ``ChannelCog`` class body is scanned, so the sibling
  ``_ChannelListPaginatorView`` (which legitimately calls ``self.message.edit``
  on a *message*, not a channel) is not a false positive.
* Only ``.delete`` / ``.edit`` are pinned in this PR — the operations routed
  through the service.  ``.clone`` and ``.set_permissions`` (overwrites) and
  channel *creation* keep their current paths and will be pinned when routed
  in a later PR.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHANNEL_COG = _REPO_ROOT / "disbot" / "cogs" / "channel_cog.py"

# Channel mutations routed through ChannelLifecycleService in this PR.
_FORBIDDEN = {"delete", "edit"}


def _channel_cog_class(tree: ast.AST) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ChannelCog":
            return node
    return None


def _forbidden_calls(node: ast.AST) -> list[str]:
    found: list[str] = []
    for n in ast.walk(node):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr in _FORBIDDEN
        ):
            found.append(f".{n.func.attr}() @ line {n.lineno}")
    return found


def test_channel_cog_routes_mutations_through_service():
    tree = ast.parse(_CHANNEL_COG.read_text(), filename=str(_CHANNEL_COG))
    cls = _channel_cog_class(tree)
    assert cls is not None, "ChannelCog class not found — did the layout change?"
    violations = _forbidden_calls(cls)
    assert not violations, (
        "Channel-lifecycle violation: ChannelCog performs direct channel "
        "mutations instead of routing through ChannelLifecycleService:\n  "
        + "\n  ".join(violations)
    )


def test_channel_cog_imports_the_service():
    """Positive check — the cog actually wires the service it must use."""
    src = _CHANNEL_COG.read_text()
    assert "ChannelLifecycleService" in src

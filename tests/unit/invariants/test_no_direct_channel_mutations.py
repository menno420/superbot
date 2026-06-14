"""Channel-lifecycle convergence invariant (server-management PR4 + PR A + P0-4).

Channel *mutations* must route through
``services.channel_lifecycle_service.ChannelLifecycleService`` — no direct
``channel.delete()`` / ``channel.edit()`` / ``channel.set_permissions()`` /
``channel.clone()`` on the user-facing surfaces.  PR4 pinned the ``ChannelCog``
command surface; **PR A widened the scan to the ``disbot/views/channels/``
panels** (the delete-confirmation bypass); **P0-4 (Q-0100) converged the
permission-overwrite and clone paths** through the same seam and pins them here.

Scope notes:

* Message edits are *not* channel mutations: ``self.message.edit`` /
  ``interaction.message.edit`` (panel re-renders) are excluded by receiver
  name, and the panels otherwise edit messages through ``safe_edit`` /
  ``response.edit_message`` (attribute ``edit_message`` — never matched).
* ``.delete`` / ``.edit`` / ``.set_permissions`` / ``.clone`` are pinned — the
  change operations the lifecycle service owns (Q-0100: clone/overwrite →
  ChannelLifecycleService).  Channel *creation* (``.create_text_channel`` etc.)
  is NOT pinned here: it converges under ``ResourceProvisioningPipeline`` in the
  P0-4 creation follow-up, and is guarded by ``test_no_silent_auto_create.py``.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHANNEL_COG = _REPO_ROOT / "disbot" / "cogs" / "channel_cog.py"
_CHANNEL_VIEWS = _REPO_ROOT / "disbot" / "views" / "channels"

# Channel mutations routed through ChannelLifecycleService.
_FORBIDDEN = {"delete", "edit", "set_permissions", "clone"}

# Receiver expressions whose ``.delete()``/``.edit()`` are *message* operations
# (panel re-renders), not channel mutations — excluded by the trailing name.
_MESSAGE_RECEIVERS = {"message", "msg"}


def _channel_cog_class(tree: ast.AST) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ChannelCog":
            return node
    return None


def _is_message_receiver(value: ast.expr) -> bool:
    """True if the call receiver is a message object (skip its .edit/.delete)."""
    try:
        rendered = ast.unparse(value)
    except Exception:  # pragma: no cover - defensive
        return False
    tail = rendered.rsplit(".", 1)[-1]
    return tail in _MESSAGE_RECEIVERS


def _forbidden_calls(node: ast.AST) -> list[str]:
    found: list[str] = []
    for n in ast.walk(node):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr in _FORBIDDEN
            and not _is_message_receiver(n.func.value)
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


def test_channel_views_route_mutations_through_service():
    """The channel-management panels must not call ``channel.delete()`` /
    ``channel.edit()`` directly — PR A's delete-confirmation bypass guard."""
    offenders: list[str] = []
    for path in sorted(_CHANNEL_VIEWS.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        offenders.extend(
            f"{path.name}: {hit}" for hit in _forbidden_calls(tree)
        )
    assert not offenders, (
        "Channel-lifecycle violation: a channel view performs a direct channel "
        "mutation instead of routing through ChannelLifecycleService "
        "(route it through services.channel_lifecycle_service):\n  "
        + "\n  ".join(offenders)
    )


def test_channel_cog_imports_the_service():
    """Positive check — the cog actually wires the service it must use."""
    src = _CHANNEL_COG.read_text()
    assert "ChannelLifecycleService" in src

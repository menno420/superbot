"""The live-loop guardrail.

A mechanical guarantee (plan: design-corroboration) that the kit never operates
on its own repository root — which would let it mutate the very workflow it runs
inside. Safe targets are the system temp tree, an ``examples/`` subtree of the
kit, or any directory outside the kit. Enforced in code, in the first commit —
not left as a doc.
"""

from __future__ import annotations

from pathlib import Path


class UnsafeTargetError(Exception):
    """Raised when a target directory would corrupt the kit's own live loop."""


def assert_safe_target(target: Path, kit_root: Path) -> None:
    """Refuse to operate on the kit's own repo root.

    Unsafe: ``kit_root`` itself or a non-``examples`` path inside it — even
    when the kit checkout lives under the system temp tree (an earlier
    temp-tree shortcut ran first and silently voided the whole guarantee for a
    kit cloned into ``/tmp``). Everything outside ``kit_root``, and the
    ``examples/`` subtree, is safe. A ``kit_root`` that is a *file* (the
    single-file bootstrap has no kit tree to protect) never matches.
    """
    target = Path(target).resolve()
    kit_root = Path(kit_root).resolve()
    inside_kit = target == kit_root or target.is_relative_to(kit_root)
    inside_examples = target.is_relative_to(kit_root / "examples")
    if inside_kit and not inside_examples:
        msg = f"refusing to operate on the kit's own tree: {target}"
        raise UnsafeTargetError(msg)

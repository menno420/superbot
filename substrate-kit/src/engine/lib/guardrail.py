"""The live-loop guardrail.

A mechanical guarantee (plan: design-corroboration) that the kit never operates
on its own repository root — which would let it mutate the very workflow it runs
inside. Safe targets are the system temp tree, an ``examples/`` subtree of the
kit, or any directory outside the kit. Enforced in code, in the first commit —
not left as a doc.
"""

from __future__ import annotations

import tempfile
from pathlib import Path


class UnsafeTargetError(Exception):
    """Raised when a target directory would corrupt the kit's own live loop."""


def assert_safe_target(target: Path, kit_root: Path) -> None:
    """Refuse to operate on the kit's own repo root.

    Safe: the system temp tree, an ``examples/`` subtree of ``kit_root``, or any
    path outside ``kit_root``. Unsafe: ``kit_root`` itself or a non-``examples``
    path inside it.
    """
    target = Path(target).resolve()
    kit_root = Path(kit_root).resolve()
    tmp_root = Path(tempfile.gettempdir()).resolve()
    if target.is_relative_to(tmp_root):
        return
    inside_kit = target == kit_root or target.is_relative_to(kit_root)
    inside_examples = target.is_relative_to(kit_root / "examples")
    if inside_kit and not inside_examples:
        msg = f"refusing to operate on the kit's own tree: {target}"
        raise UnsafeTargetError(msg)

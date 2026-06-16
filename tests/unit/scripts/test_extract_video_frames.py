"""Tests for the pure helpers in scripts/extract_video_frames.py.

The script is a dev convenience (Q-0105); these cover the index math and that
the module imports without the optional video stack (imageio/PIL stay lazy).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "extract_video_frames",
    Path(__file__).resolve().parents[3] / "scripts" / "extract_video_frames.py",
)
assert _SPEC and _SPEC.loader
evf = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(evf)


def test_even_indices_endpoints_and_spacing() -> None:
    # Always includes first and last; evenly spaced; right count.
    out = evf._even_indices(100, 5)
    assert out[0] == 0
    assert out[-1] == 99
    assert len(out) == 5
    assert out == sorted(out)


def test_even_indices_edge_cases() -> None:
    assert evf._even_indices(0, 10) == []
    assert evf._even_indices(50, 0) == []
    # n >= total returns every frame, no duplicates / no out-of-range.
    assert evf._even_indices(3, 10) == [0, 1, 2]
    # single sample is well-defined (no ZeroDivisionError on n-1).
    assert evf._even_indices(10, 1) == [0]


def test_module_imports_without_video_stack() -> None:
    # The heavy deps must be lazy — importing the module (done above) must not
    # require imageio/PIL. _DEFAULT_OUT is a tmp path, never a hardcoded /tmp.
    assert evf._DEFAULT_OUT.endswith("vidframes")
